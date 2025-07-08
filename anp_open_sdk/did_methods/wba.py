"""
WBA DID Method Implementation - SDK Layer

This module implements the WBA DID method including:
- Authorization header format and parsing
- DID-specific authentication logic
- Business rules for WBA authentication

Uses Protocol layer for cryptographic operations and Framework layer for I/O.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from abc import ABC, abstractmethod

import jcs

from ..auth.schemas import AuthenticationContext, DIDCredentials, DIDDocument
from ..protocol.crypto import create_secp256k1_signer, SignatureEncoder

logger = logging.getLogger(__name__)


# === Abstract interfaces for Framework layer ===

class DIDResolver(ABC):
    """Abstract DID resolver - implemented by framework layer"""
    
    @abstractmethod
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        """Resolve DID document"""
        pass


class TokenStorage(ABC):
    """Abstract token storage - implemented by framework layer"""
    
    @abstractmethod
    async def get_token(self, caller_did: str, target_did: str) -> Optional[Dict[str, Any]]:
        """Get cached token"""
        pass
    
    @abstractmethod  
    async def store_token(self, caller_did: str, target_did: str, token_data: Dict[str, Any]):
        """Store token"""
        pass


class HttpTransport(ABC):
    """Abstract HTTP transport - implemented by framework layer"""
    
    @abstractmethod
    async def send_request(self, method: str, url: str, headers: Dict[str, str], 
                          json_data: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        """Send HTTP request"""
        pass


# === WBA DID Method Implementation ===

class WBAAuthHeaderBuilder:
    """WBA Authorization header builder"""
    
    def __init__(self):
        self.crypto_signer = create_secp256k1_signer()
        self.encoder = SignatureEncoder()

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from starlette.requests import Request
        except ImportError:
            Request = None

        if Request and isinstance(url, Request):
            url_str = str(getattr(url, "base_url", None) or getattr(url, "url", None))
        else:
            url_str = str(url)

        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.split(':')[0]
        return domain

    def _select_authentication_method(self, did_document) -> Tuple[Dict, str]:
        """Select first authentication method from DID document"""
        if hasattr(did_document, 'authentication'):
            authentication_methods = did_document.authentication
            verification_methods = did_document.verification_methods
        else:
            authentication_methods = did_document.get("authentication")
            verification_methods = did_document.get("verificationMethod", [])
            
        if not authentication_methods or not isinstance(authentication_methods, list):
            raise ValueError("DID document is missing or has an invalid 'authentication' field.")

        first_method_ref = authentication_methods[0]

        if isinstance(first_method_ref, str):
            method_id = first_method_ref
            if hasattr(did_document, 'verification_methods'):
                method_dict = next((vm.__dict__ for vm in verification_methods if vm.id == method_id), None)
            else:
                method_dict = next((vm for vm in verification_methods if vm.get("id") == method_id), None)
            if not method_dict:
                raise ValueError(f"Verification method '{method_id}' not found in 'verificationMethod' array.")
        elif isinstance(first_method_ref, dict):
            method_dict = first_method_ref
            method_id = method_dict.get("id")
            if not method_id:
                raise ValueError("Embedded authentication method is missing 'id'.")
        else:
            raise ValueError("Invalid format for authentication method reference.")

        fragment = urlparse(method_id).fragment
        if not fragment:
            raise ValueError(f"Could not extract fragment from verification method ID: {method_id}")

        return method_dict, f"#{fragment}"

    def build_authorization_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build WBA Authorization header"""
        did_document = credentials.did_document
        did = credentials.did

        _method_dict, verification_method_fragment = self._select_authentication_method(did_document)

        nonce = secrets.token_hex(16)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        service_domain = self._get_domain(context.request_url)

        data_to_sign = {
            "nonce": nonce,
            "timestamp": timestamp,
            "service": service_domain,
            "did": did,
        }
        if context.use_two_way_auth:
            data_to_sign["resp_did"] = context.target_did

        canonical_json = jcs.canonicalize(data_to_sign)
        content_hash = hashlib.sha256(canonical_json).digest()

        # Sign using credentials (gets DER format)
        signature_der = credentials.sign(content_hash, verification_method_fragment)
        
        # Convert DER to R|S format and encode as base64url
        signature_rs = self.encoder.der_to_rs_format(signature_der)
        signature = self.encoder.encode_base64url(signature_rs)

        # Build Authorization header parts
        parts = [
            f'DIDWba did="{did}"',
            f'nonce="{nonce}"',
            f'timestamp="{timestamp}"',
        ]
        if context.use_two_way_auth:
            parts.append(f'resp_did="{context.target_did}"')

        parts.extend([f'verification_method="{verification_method_fragment}"', f'signature="{signature}"'])

        auth_header_value = ", ".join(parts)
        return {"Authorization": auth_header_value}


class WBAAuthHeaderParser:
    """WBA Authorization header parser"""

    def parse_authorization_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse WBA Authorization header"""
        if not auth_header or not auth_header.startswith("DIDWba "):
            return {}

        value = auth_header.replace("DIDWba ", "", 1)
        import re
        try:
            parsed = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', value))
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse auth header '{auth_header}': {e}")
            return {}

    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from Authorization header"""
        if not auth_header or not auth_header.startswith("DIDWba "):
            return None, None

        import re
        try:
            value_str = auth_header.replace("DIDWba ", "", 1)
            parsed = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', value_str))
            caller_did = parsed.get('did')
            target_did = parsed.get('resp_did')
            return caller_did, target_did
        except Exception:
            return None, None


class WBADIDAuthenticator:
    """
    WBA DID Method Authenticator - SDK Layer
    
    Handles WBA-specific authentication logic including Authorization header processing.
    Uses Protocol layer for crypto operations and Framework layer for I/O.
    """

    def __init__(self, did_resolver: DIDResolver = None, token_storage: TokenStorage = None, 
                 http_transport: HttpTransport = None):
        self.header_builder = WBAAuthHeaderBuilder()
        self.header_parser = WBAAuthHeaderParser()
        self.crypto_signer = create_secp256k1_signer()
        self.encoder = SignatureEncoder()
        
        # Framework layer dependencies (injected)
        self.did_resolver = did_resolver
        self.token_storage = token_storage
        self.http_transport = http_transport

    def get_method_name(self) -> str:
        """Get DID method name"""
        return "wba"

    def can_handle_auth_header(self, auth_header: str) -> bool:
        """Check if this authenticator can handle the Authorization header"""
        return auth_header.startswith("DIDWba ")

    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from Authorization header"""
        return self.header_parser.extract_dids_from_header(auth_header)

    async def build_auth_request(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build authorization header for outgoing request"""
        return self.header_builder.build_authorization_header(context, credentials)

    async def verify_auth_request(self, auth_header: str, context: AuthenticationContext) -> Tuple[bool, str]:
        """
        Verify incoming authorization header (server-side).
        Uses framework layer for DID resolution.
        """
        try:
            # Parse Authorization header
            parsed_header = self.header_parser.parse_authorization_header(auth_header)
            if not parsed_header:
                return False, "Invalid or unparsable auth header."

            # Validate required fields
            required_fields = {"did", "nonce", "timestamp", "verification_method", "signature"}
            if not required_fields.issubset(parsed_header.keys()):
                return False, "Auth header is missing required fields."

            # Resolve DID document using framework layer
            if not self.did_resolver:
                return False, "DID resolver not configured"
                
            did_doc = await self.did_resolver.resolve_did_document(parsed_header['did'])
            if not did_doc:
                return False, f"Failed to resolve DID document for {parsed_header['did']}."

            # Get public key from DID document
            public_key_bytes = did_doc.get_public_key_bytes_by_fragment(parsed_header['verification_method'])
            if not public_key_bytes:
                return False, f"Public key not found for {parsed_header['verification_method']}."

            # Reconstruct signed payload
            service_domain = self.header_builder._get_domain(context.request_url)
            payload_to_verify = self._reconstruct_signed_payload(parsed_header, service_domain)

            # Verify signature using protocol layer
            signature_rs = self.encoder.decode_base64url(parsed_header['signature'])
            signature_der = self.encoder.rs_to_der_format(signature_rs)
            is_valid = self.crypto_signer.verify(payload_to_verify, signature_der, public_key_bytes)

            if is_valid:
                return True, "Request verification successful."
            else:
                return False, "Signature verification failed."

        except Exception as e:
            logger.error(f"Request verification failed: {e}")
            return False, f"Exception during verification: {e}"

    def _reconstruct_signed_payload(self, parsed_header: Dict[str, Any], service_domain: str) -> bytes:
        """Reconstruct the payload that was signed"""
        data_to_sign = {
            "nonce": parsed_header['nonce'],
            "timestamp": parsed_header['timestamp'],
            "service": service_domain,
            "did": parsed_header['did'],
        }
        if 'resp_did' in parsed_header:
            data_to_sign["resp_did"] = parsed_header['resp_did']

        canonical_json_bytes = jcs.canonicalize(data_to_sign)
        return hashlib.sha256(canonical_json_bytes).digest()

    async def send_authenticated_request(self, context: AuthenticationContext, credentials: DIDCredentials) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Send authenticated HTTP request using framework layer.
        """
        try:
            if not self.http_transport:
                return False, "HTTP transport not configured", {}

            # Build authorization header
            auth_headers = await self.build_auth_request(context, credentials)

            # Send HTTP request using framework layer
            status, response_headers, response_body = await self.http_transport.send_request(
                method=getattr(context, 'method', 'GET').upper(),
                url=context.request_url,
                headers={**getattr(context, 'custom_headers', {}), **auth_headers},
                json_data=getattr(context, 'json_data', None)
            )

            is_success = 200 <= status < 300
            return is_success, str(response_headers), response_body

        except Exception as e:
            logger.error(f"Authenticated request failed: {e}")
            return False, "", {"error": str(e)}


# Factory function
def create_wba_authenticator(did_resolver: DIDResolver = None, token_storage: TokenStorage = None, 
                           http_transport: HttpTransport = None) -> WBADIDAuthenticator:
    """Create WBA DID authenticator with optional framework dependencies"""
    return WBADIDAuthenticator(did_resolver, token_storage, http_transport)