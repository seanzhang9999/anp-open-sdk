"""
WBA DID Method Pure Implementation

This module contains the pure WBA DID method implementation without any I/O operations.
Extracted from auth_methods/wba/implementation.py, removing all network and file operations.

The framework layer provides I/O adapters for:
- DID document resolution (network/file)
- Token storage and retrieval  
- HTTP transport
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from abc import ABC, abstractmethod

import jcs

from anp_open_sdk.auth.schemas import AuthenticationContext, DIDCredentials, DIDDocument
from anp_open_sdk.auth.utils import generate_nonce

logger = logging.getLogger(__name__)


# === Pure Interfaces (to be implemented by framework layer) ===

class DIDResolver(ABC):
    """Abstract DID resolver interface - implemented by framework layer"""
    
    @abstractmethod
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        """Resolve DID document - implemented by framework layer with network/file access"""
        pass


class TokenStorage(ABC):
    """Abstract token storage interface - implemented by framework layer"""
    
    @abstractmethod
    async def get_token(self, caller_did: str, target_did: str) -> Optional[Dict[str, Any]]:
        """Get cached token - implemented by framework layer"""
        pass
    
    @abstractmethod  
    async def store_token(self, caller_did: str, target_did: str, token_data: Dict[str, Any]):
        """Store token - implemented by framework layer"""
        pass


class HttpTransport(ABC):
    """Abstract HTTP transport interface - implemented by framework layer"""
    
    @abstractmethod
    async def send_request(self, method: str, url: str, headers: Dict[str, str], 
                          json_data: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        """Send HTTP request - implemented by framework layer"""
        pass


# === Pure WBA Implementation (no I/O operations) ===

class WBADIDSigner:
    """Pure WBA DID signer - no I/O operations"""
    
    def encode_signature(self, signature_bytes: bytes) -> str:
        """
        Encode signature bytes to base64url format.
        Convert from DER format to R|S format if needed.
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
            
            # Try to parse DER format
            try:
                r, s = decode_dss_signature(signature_bytes)
                # Convert to R|S format (32 bytes each)
                r_bytes = r.to_bytes(32, byteorder='big')
                s_bytes = s.to_bytes(32, byteorder='big')
                signature = r_bytes + s_bytes
            except Exception:
                # Assume already in R|S format
                if len(signature_bytes) % 2 != 0:
                    raise ValueError("Invalid R|S signature format: length must be even")
                signature = signature_bytes
            
            # Encode to base64url
            return base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')
            
        except Exception as e:
            logger.error(f"Failed to encode signature: {str(e)}")
            raise ValueError(f"Invalid signature format: {str(e)}")

    def sign_payload(self, payload, private_key_bytes: bytes) -> str:
        """
        Sign payload and return base64url encoded signature.
        Pure cryptographic operation - no I/O.
        """
        try:
            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload
            
            # Use secp256k1 for signing
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
            
            private_key_obj = ec.derive_private_key(
                int.from_bytes(private_key_bytes, byteorder="big"), 
                ec.SECP256K1()
            )
            
            # Generate DER signature
            signature_der = private_key_obj.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
            
            # Parse DER to get R, S
            r, s = decode_dss_signature(signature_der)
            
            # Convert to fixed length R|S format
            r_bytes = r.to_bytes(32, byteorder='big')
            s_bytes = s.to_bytes(32, byteorder='big')
            signature_rs = r_bytes + s_bytes
            
            # Encode to base64url
            return base64.urlsafe_b64encode(signature_rs).rstrip(b'=').decode('ascii')
            
        except Exception as e:
            logger.error(f"Signing failed: {e}")
            raise

    def verify_signature(self, payload, signature: str, public_key_bytes: bytes) -> bool:
        """
        Verify signature - pure cryptographic operation.
        """
        try:
            # Decode base64url signature
            signature_bytes = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))

            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload

            # Determine key type by public key length
            if len(public_key_bytes) == 32:
                # Ed25519 public key (32 bytes)
                from cryptography.hazmat.primitives.asymmetric import ed25519
                public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key_obj.verify(signature_bytes, payload_bytes)
                return True
            elif len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
                # secp256k1 uncompressed public key (65 bytes)
                return self._verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes)
            elif len(public_key_bytes) == 33:
                # secp256k1 compressed public key (33 bytes)
                return self._verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes, compressed=True)
            else:
                logger.error(f"Unsupported public key length: {len(public_key_bytes)} bytes")
                return False

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def _verify_secp256k1_signature(self, signature_bytes: bytes, payload_bytes: bytes, 
                                   public_key_bytes: bytes, compressed: bool = False) -> bool:
        """Verify secp256k1 signature with proper R|S to DER conversion"""
        try:
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

            # Create public key object
            if compressed:
                public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
            else:
                x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
                y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
                public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
                public_key_obj = public_numbers.public_key()

            # Ensure signature is 64 bytes (32 R + 32 S)
            if len(signature_bytes) != 64:
                logger.error(f"Invalid signature length: {len(signature_bytes)}, expected 64")
                return False

            # Extract R and S from fixed length format
            r_bytes = signature_bytes[:32]
            s_bytes = signature_bytes[32:]
            
            # Convert to integers
            r = int.from_bytes(r_bytes, 'big')
            s = int.from_bytes(s_bytes, 'big')
            
            # Validate R and S
            if r == 0 or s == 0:
                logger.error("Invalid signature: R or S is zero")
                return False
            
            # Convert to DER format
            signature_der = encode_dss_signature(r, s)
            
            # Verify signature
            public_key_obj.verify(signature_der, payload_bytes, ec.ECDSA(hashes.SHA256()))
            return True

        except Exception as e:
            logger.error(f"secp256k1 verification failed: {e}")
            return False


class WBAAuthHeaderBuilder:
    """Pure WBA auth header builder - no I/O operations"""
    
    def __init__(self, signer: WBADIDSigner):
        self.signer = signer

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL - pure string operation"""
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
        # Handle both DIDDocument (Pydantic) and dict
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
                # For DIDDocument Pydantic model
                method_dict = next((vm.__dict__ for vm in verification_methods if vm.id == method_id), None)
            else:
                # For dict
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

    def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build authentication header - pure logic, no I/O"""
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

        # Sign using credentials (pure operation)
        signature_der = credentials.sign(content_hash, verification_method_fragment)
        
        # Encode signature
        signature = self.signer.encode_signature(signature_der)

        # Build header parts
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
    """Pure WBA auth header parser - no I/O operations"""

    def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse WBA auth header - pure string operation"""
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

    def extract_did_from_auth_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from auth header - pure string operation"""
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
    Pure WBA DID authenticator - delegates all I/O to framework layer.
    This class contains only pure authentication logic.
    """

    def __init__(self, signer: WBADIDSigner, header_builder: WBAAuthHeaderBuilder, 
                 header_parser: WBAAuthHeaderParser):
        self.signer = signer
        self.header_builder = header_builder
        self.header_parser = header_parser

    def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build authentication header - pure operation"""
        return self.header_builder.build_auth_header(context, credentials)

    def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse authentication header - pure operation"""
        return self.header_parser.parse_auth_header(auth_header)

    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from header - pure operation"""
        return self.header_parser.extract_did_from_auth_header(auth_header)

    def verify_signature_with_public_key(self, payload, signature: str, public_key_bytes: bytes) -> bool:
        """Verify signature with known public key - pure operation"""
        return self.signer.verify_signature(payload, signature, public_key_bytes)

    def reconstruct_signed_payload(self, parsed_header: Dict[str, Any], service_domain: str) -> bytes:
        """Reconstruct the payload that was signed - pure operation"""
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


def create_wba_authenticator() -> WBADIDAuthenticator:
    """Factory function to create WBA authenticator with pure components"""
    signer = WBADIDSigner()
    header_builder = WBAAuthHeaderBuilder(signer)
    header_parser = WBAAuthHeaderParser()
    return WBADIDAuthenticator(signer, header_builder, header_parser)