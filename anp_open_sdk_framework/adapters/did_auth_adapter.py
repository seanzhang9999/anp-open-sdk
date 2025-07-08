"""
Framework Layer I/O Adapters

This module implements the I/O operations that the protocol layer delegates to the framework.
It provides concrete implementations for network, file, and storage operations.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

import aiohttp

from anp_open_sdk.auth.schemas import DIDDocument
from anp_open_sdk.protocol.did_methods.wba import DIDResolver, TokenStorage, HttpTransport
from anp_open_sdk.anp_sdk_agent import LocalAgent

logger = logging.getLogger(__name__)


class FileSystemDIDResolver(DIDResolver):
    """DID resolver that reads from local file system"""
    
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        """Resolve DID document from local file system"""
        try:
            agent = LocalAgent.from_did(did)
            did_doc_path = Path(agent.did_document_path)
            if did_doc_path.exists():
                with open(did_doc_path, 'r') as f:
                    raw_doc = json.load(f)
                return DIDDocument(
                    **raw_doc,
                    raw_document=raw_doc
                )
        except Exception as e:
            logger.error(f"Failed to resolve DID from filesystem: {did}, error: {e}")
            return None


class NetworkDIDResolver(DIDResolver):
    """DID resolver that uses network requests"""
    
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        """Resolve DID document from network"""
        try:
            # Implementation would depend on the DID method
            # For WBA, this might resolve from a DID registry
            logger.info(f"Network DID resolution for {did} - not implemented yet")
            return None
        except Exception as e:
            logger.error(f"Failed to resolve DID from network: {did}, error: {e}")
            return None


class HybridDIDResolver(DIDResolver):
    """DID resolver that tries local first, then network"""
    
    def __init__(self):
        self.filesystem_resolver = FileSystemDIDResolver()
        self.network_resolver = NetworkDIDResolver()
    
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        """Try local first, then network"""
        # Try local first
        result = await self.filesystem_resolver.resolve_did_document(did)
        if result:
            return result
        
        # Fall back to network
        return await self.network_resolver.resolve_did_document(did)


class LocalAgentTokenStorage(TokenStorage):
    """Token storage using LocalAgent contact manager"""
    
    async def get_token(self, caller_did: str, target_did: str) -> Optional[Dict[str, Any]]:
        """Get cached token from LocalAgent storage"""
        try:
            target_agent = LocalAgent.from_did(target_did)
            token_info = target_agent.contact_manager.get_token_to_remote(caller_did)
            
            if token_info:
                # Handle timezone-naive datetime
                if isinstance(token_info["expires_at"], str):
                    expires_at_dt = datetime.fromisoformat(token_info["expires_at"])
                else:
                    expires_at_dt = token_info["expires_at"]
                    
                if expires_at_dt.tzinfo is None:
                    expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
                    
                token_info["expires_at"] = expires_at_dt
                
                # Check if token is still valid
                if not token_info.get("is_revoked", False) and datetime.now(timezone.utc) < expires_at_dt:
                    return token_info
                    
            return None
        except Exception as e:
            logger.error(f"Failed to get token from storage: {e}")
            return None
    
    async def store_token(self, caller_did: str, target_did: str, token_data: Dict[str, Any]):
        """Store token in LocalAgent storage"""
        try:
            target_agent = LocalAgent.from_did(target_did)
            expiration_time = token_data.get("expires_delta", 3600)  # Default 1 hour
            target_agent.contact_manager.store_token_to_remote(
                caller_did, 
                token_data["token"], 
                expiration_time
            )
        except Exception as e:
            logger.error(f"Failed to store token: {e}")


class AiohttpTransport(HttpTransport):
    """HTTP transport using aiohttp"""
    
    async def send_request(self, method: str, url: str, headers: Dict[str, str], 
                          json_data: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        """Send HTTP request using aiohttp"""
        try:
            async with aiohttp.ClientSession() as session:
                request_kwargs = {'headers': headers}
                if method.upper() in ["POST", "PUT", "PATCH"] and json_data is not None:
                    request_kwargs['json'] = json_data

                async with session.request(method, url, **request_kwargs) as response:
                    status = response.status
                    response_headers = dict(response.headers)

                    try:
                        response_body = await response.json()
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        response_body = {"text": await response.text()}

                    return status, response_headers, response_body

        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            return 500, {}, {"error": str(e)}


class FrameworkDIDAuthAdapter:
    """
    Adapter that connects pure protocol layer with framework I/O operations.
    This bridges the gap between pure logic and I/O implementations.
    """
    
    def __init__(self, 
                 did_resolver: DIDResolver = None,
                 token_storage: TokenStorage = None,
                 http_transport: HttpTransport = None):
        self.did_resolver = did_resolver or HybridDIDResolver()
        self.token_storage = token_storage or LocalAgentTokenStorage()
        self.http_transport = http_transport or AiohttpTransport()
    
    async def authenticate_request_with_io(self, authenticator, context, credentials):
        """
        Perform authentication request with I/O operations.
        Uses pure authenticator logic + framework I/O adapters.
        """
        try:
            # 1. Build auth header (pure operation)
            auth_headers = authenticator.build_auth_header(context, credentials)

            # 2. Send HTTP request (I/O operation via framework)
            status, response_headers, response_body = await self.http_transport.send_request(
                method=getattr(context, 'method', 'GET').upper(),
                url=context.request_url,
                headers={**getattr(context, 'custom_headers', {}), **auth_headers},
                json_data=getattr(context, 'json_data', None)
            )

            is_success = 200 <= status < 300
            return is_success, json.dumps(response_headers), response_body

        except Exception as e:
            logger.error(f"Authentication request with I/O failed: {e}")
            return False, "", {"error": str(e)}
    
    async def verify_request_with_io(self, authenticator, auth_header: str, context):
        """
        Verify authentication request with I/O operations.
        Uses pure authenticator logic + framework I/O adapters.
        """
        try:
            # 1. Parse auth header (pure operation)
            parsed_header = authenticator.parse_auth_header(auth_header)
            if not parsed_header:
                return False, "Invalid or unparsable auth header."

            # Validate required fields
            required_fields = {"did", "nonce", "timestamp", "verification_method", "signature"}
            if not required_fields.issubset(parsed_header.keys()):
                return False, "Auth header is missing required fields."

            # 2. Resolve DID document (I/O operation via framework)
            did_doc = await self.did_resolver.resolve_did_document(parsed_header['did'])
            if not did_doc:
                return False, f"Failed to resolve DID document for {parsed_header['did']}."

            # 3. Get public key (pure operation)
            public_key_bytes = did_doc.get_public_key_bytes_by_fragment(parsed_header['verification_method'])
            if not public_key_bytes:
                return False, f"Public key not found for {parsed_header['verification_method']}."

            # 4. Reconstruct signed payload (pure operation)
            service_domain = authenticator.header_builder._get_domain(context.request_url)
            payload_to_verify = authenticator.reconstruct_signed_payload(parsed_header, service_domain)

            # 5. Verify signature (pure operation)
            is_valid = authenticator.verify_signature_with_public_key(
                payload_to_verify, 
                parsed_header['signature'], 
                public_key_bytes
            )

            if is_valid:
                return True, "Request verification successful."
            else:
                return False, "Signature verification failed."

        except Exception as e:
            logger.error(f"Request verification with I/O failed: {e}")
            return False, f"Exception during verification: {e}"