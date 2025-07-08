"""
Authentication Manager - SDK Layer

This module handles Authorization header processing and authentication business logic.
It uses Protocol layer for DID method algorithms and Framework layer for I/O operations.

Key responsibilities:
- Authorization header format definition and parsing
- DID method wrapper loading
- Multi-auth method support (DIDWba, Bearer, Token, etc.)
- Two-way authentication logic
- Business rules and policies
"""

import logging
import re
from typing import Dict, Optional, Tuple, Any, List
from abc import ABC, abstractmethod
from enum import Enum

from .schemas import AuthenticationContext, DIDCredentials
from ..protocol.did_methods import get_did_protocol_for_did, get_did_protocol

logger = logging.getLogger(__name__)


# === Framework Layer Interfaces (implemented externally) ===

class DIDResolver(ABC):
    """Abstract DID resolver - implemented by framework layer"""
    
    @abstractmethod
    async def resolve_did_document(self, did: str) -> Optional[Any]:
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


# === SDK Layer Authorization Header Processing ===

class AuthMethod(Enum):
    """Supported authentication methods"""
    DID_WBA = "did_wba"
    DID_KEY = "did_key"
    DID_WEB = "did_web"
    BEARER = "bearer"
    TOKEN = "token"


class AuthenticationResult:
    """Result of authentication operation"""
    def __init__(self, success: bool, message: str, data: Optional[Dict] = None):
        self.success = success
        self.message = message
        self.data = data or {}


class AuthHeaderHandler(ABC):
    """Abstract base class for Authorization header handlers"""
    
    @abstractmethod
    def get_auth_method(self) -> str:
        """Get the authentication method name"""
        pass
    
    @abstractmethod
    def can_handle_header(self, auth_header: str) -> bool:
        """Check if this handler can process the Authorization header"""
        pass
    
    @abstractmethod
    async def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build Authorization header for outgoing request"""
        pass
    
    @abstractmethod
    async def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse Authorization header into structured data"""
        pass
    
    @abstractmethod
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify incoming Authorization header"""
        pass


class DIDAuthHeaderHandler(AuthHeaderHandler):
    """
    Handler for DID-based Authorization headers (DIDWba, DIDKey, DIDWeb, etc.)
    
    Uses Protocol layer for DID method algorithms and Framework layer for I/O.
    """
    
    def __init__(self, did_resolver: DIDResolver = None):
        self.did_resolver = did_resolver
    
    def get_auth_method(self) -> str:
        return "did_based"
    
    def can_handle_header(self, auth_header: str) -> bool:
        """Check if this is a DID-based Authorization header"""
        return (auth_header.startswith("DIDWba ") or 
                auth_header.startswith("DIDKey ") or 
                auth_header.startswith("DIDWeb "))
    
    def _get_did_method_from_header(self, auth_header: str) -> Optional[str]:
        """Extract DID method from Authorization header prefix"""
        if auth_header.startswith("DIDWba "):
            return "wba"
        elif auth_header.startswith("DIDKey "):
            return "key"
        elif auth_header.startswith("DIDWeb "):
            return "web"
        return None
    
    async def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build DID-based Authorization header"""
        try:
            # Get DID method protocol from caller DID
            did_protocol = get_did_protocol_for_did(context.caller_did)
            if not did_protocol:
                raise ValueError(f"Unsupported DID method for: {context.caller_did}")
            
            # Extract verification method fragment from credentials
            verification_method_fragment = self._get_verification_method_fragment(credentials)
            
            # Get private key bytes
            private_key_bytes = credentials.get_private_key_bytes(verification_method_fragment)
            
            # Create signed payload using protocol layer
            context_data = {
                'did': context.caller_did,
                'request_url': context.request_url,
                'target_did': context.target_did if context.use_two_way_auth else None,
                'verification_method_fragment': verification_method_fragment
            }
            
            payload_data = did_protocol.create_signed_payload(context_data, private_key_bytes)
            
            # Build Authorization header based on DID method
            method_name = did_protocol.get_method_name()
            if method_name == "wba":
                return self._build_wba_header(payload_data)
            elif method_name == "key":
                return self._build_key_header(payload_data)
            elif method_name == "web":
                return self._build_web_header(payload_data)
            else:
                raise ValueError(f"Unknown DID method: {method_name}")
                
        except Exception as e:
            logger.error(f"Failed to build DID Authorization header: {e}")
            return {}
    
    def _build_wba_header(self, payload_data: Dict[str, Any]) -> Dict[str, str]:
        """Build WBA Authorization header format"""
        parts = [
            f'DIDWba did="{payload_data["did"]}"',
            f'nonce="{payload_data["nonce"]}"',
            f'timestamp="{payload_data["timestamp"]}"',
        ]
        if payload_data.get("resp_did"):
            parts.append(f'resp_did="{payload_data["resp_did"]}"')
        
        parts.extend([
            f'verification_method="{payload_data["verification_method"]}"',
            f'signature="{payload_data["signature"]}"'
        ])
        
        auth_header_value = ", ".join(parts)
        return {"Authorization": auth_header_value}
    
    def _build_key_header(self, payload_data: Dict[str, Any]) -> Dict[str, str]:
        """Build Key DID Authorization header format (future)"""
        # Placeholder for did:key format
        raise NotImplementedError("DID Key Authorization header not implemented yet")
    
    def _build_web_header(self, payload_data: Dict[str, Any]) -> Dict[str, str]:
        """Build Web DID Authorization header format (future)"""
        # Placeholder for did:web format
        raise NotImplementedError("DID Web Authorization header not implemented yet")
    
    async def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse DID-based Authorization header"""
        method_name = self._get_did_method_from_header(auth_header)
        if not method_name:
            return {}
        
        if method_name == "wba":
            return self._parse_wba_header(auth_header)
        elif method_name == "key":
            return self._parse_key_header(auth_header)
        elif method_name == "web":
            return self._parse_web_header(auth_header)
        else:
            return {}
    
    def _parse_wba_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse WBA Authorization header"""
        if not auth_header.startswith("DIDWba "):
            return {}
        
        value = auth_header.replace("DIDWba ", "", 1)
        try:
            parsed = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', value))
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse WBA auth header: {e}")
            return {}
    
    def _parse_key_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse Key DID Authorization header (future)"""
        # Placeholder
        raise NotImplementedError("DID Key header parsing not implemented yet")
    
    def _parse_web_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse Web DID Authorization header (future)"""
        # Placeholder
        raise NotImplementedError("DID Web header parsing not implemented yet")
    
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify DID-based Authorization header"""
        try:
            # Parse Authorization header
            parsed_data = await self.parse_auth_header(auth_header)
            if not parsed_data:
                return AuthenticationResult(False, "Failed to parse Authorization header")
            
            # Get DID method protocol
            caller_did = parsed_data.get('did')
            if not caller_did:
                return AuthenticationResult(False, "No DID found in Authorization header")
            
            did_protocol = get_did_protocol_for_did(caller_did)
            if not did_protocol:
                return AuthenticationResult(False, f"Unsupported DID method for: {caller_did}")
            
            # Resolve DID document using framework layer
            if not self.did_resolver:
                return AuthenticationResult(False, "DID resolver not configured")
            
            did_doc = await self.did_resolver.resolve_did_document(caller_did)
            if not did_doc:
                return AuthenticationResult(False, f"Failed to resolve DID: {caller_did}")
            
            # Get public key from DID document
            verification_method = parsed_data.get('verification_method')
            public_key_bytes = did_doc.get_public_key_bytes_by_fragment(verification_method)
            if not public_key_bytes:
                return AuthenticationResult(False, f"Public key not found: {verification_method}")
            
            # Add service domain for verification
            from urllib.parse import urlparse
            parsed_url = urlparse(context.request_url)
            service_domain = parsed_url.netloc.split(':')[0]
            parsed_data['service'] = service_domain
            
            # Verify using protocol layer
            is_valid = did_protocol.verify_signed_payload(parsed_data, public_key_bytes)
            
            if is_valid:
                return AuthenticationResult(True, "DID Authorization verification successful")
            else:
                return AuthenticationResult(False, "DID signature verification failed")
                
        except Exception as e:
            logger.error(f"DID Authorization header verification failed: {e}")
            return AuthenticationResult(False, f"Verification error: {e}")
    
    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from Authorization header"""
        try:
            parsed_data = self._parse_any_did_header(auth_header)
            caller_did = parsed_data.get('did')
            target_did = parsed_data.get('resp_did')
            return caller_did, target_did
        except Exception:
            return None, None
    
    def _parse_any_did_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse any DID Authorization header format"""
        if auth_header.startswith("DIDWba "):
            return self._parse_wba_header(auth_header)
        # Add other DID method parsing as needed
        return {}
    
    def _get_verification_method_fragment(self, credentials: DIDCredentials) -> str:
        """Get verification method fragment from credentials"""
        # Get first available key pair
        if credentials.key_pairs:
            first_key_id = next(iter(credentials.key_pairs.keys()))
            return f"#{first_key_id}"
        
        raise ValueError("No key pairs found in credentials")


class BearerTokenHandler(AuthHeaderHandler):
    """Handler for Bearer token Authorization headers"""
    
    def __init__(self, token_storage: TokenStorage = None):
        self.token_storage = token_storage
    
    def get_auth_method(self) -> str:
        return AuthMethod.BEARER.value
    
    def can_handle_header(self, auth_header: str) -> bool:
        return auth_header.startswith("Bearer ")
    
    async def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build Bearer token Authorization header"""
        # Bearer tokens are typically generated by framework layer
        return {"Authorization": "Bearer <token>"}
    
    async def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse Bearer token Authorization header"""
        if not auth_header.startswith("Bearer "):
            return {}
        
        token = auth_header[7:]  # Remove "Bearer "
        return {"token": token, "type": "bearer"}
    
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify Bearer token Authorization header"""
        try:
            if not self.token_storage:
                return AuthenticationResult(False, "Token storage not configured")
            
            parsed_data = await self.parse_auth_header(auth_header)
            token = parsed_data.get("token")
            
            if not token:
                return AuthenticationResult(False, "Invalid Bearer token format")
            
            # Use framework layer for token verification
            token_info = await self.token_storage.get_token(
                context.caller_did, context.target_did
            )
            
            if token_info and token_info.get("token") == token:
                return AuthenticationResult(True, "Bearer token verification successful")
            else:
                return AuthenticationResult(False, "Invalid or expired Bearer token")
                
        except Exception as e:
            logger.error(f"Bearer token verification failed: {e}")
            return AuthenticationResult(False, f"Bearer token verification error: {e}")


class CustomTokenHandler(AuthHeaderHandler):
    """Handler for custom token Authorization headers (extensible)"""
    
    def __init__(self, token_storage: TokenStorage = None):
        self.token_storage = token_storage
    
    def get_auth_method(self) -> str:
        return AuthMethod.TOKEN.value
    
    def can_handle_header(self, auth_header: str) -> bool:
        return auth_header.startswith("Token ") or auth_header.startswith("CustomToken ")
    
    async def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build custom token Authorization header"""
        return {"Authorization": "Token <custom_token>"}
    
    async def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse custom token Authorization header"""
        if auth_header.startswith("Token "):
            token = auth_header[6:]
            return {"token": token, "type": "token"}
        elif auth_header.startswith("CustomToken "):
            token = auth_header[12:]
            return {"token": token, "type": "custom"}
        return {}
    
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify custom token Authorization header"""
        # Placeholder for custom token verification
        return AuthenticationResult(False, "Custom token verification not implemented")


class AuthenticationManager:
    """
    Main authentication manager for the SDK layer.
    
    Handles Authorization header processing using DID method protocols and framework I/O.
    """
    
    def __init__(self, did_resolver: DIDResolver = None, token_storage: TokenStorage = None, 
                 http_transport: HttpTransport = None):
        self.handlers: Dict[str, AuthHeaderHandler] = {}
        self._register_default_handlers(did_resolver, token_storage)
    
    def _register_default_handlers(self, did_resolver: DIDResolver, token_storage: TokenStorage):
        """Register default Authorization header handlers"""
        self.register_handler(DIDAuthHeaderHandler(did_resolver))
        self.register_handler(BearerTokenHandler(token_storage))
        self.register_handler(CustomTokenHandler(token_storage))
    
    def register_handler(self, handler: AuthHeaderHandler):
        """Register a new Authorization header handler"""
        self.handlers[handler.get_auth_method()] = handler
    
    def get_handler_for_header(self, auth_header: str) -> Optional[AuthHeaderHandler]:
        """Get appropriate handler for the Authorization header"""
        for handler in self.handlers.values():
            if handler.can_handle_header(auth_header):
                return handler
        return None
    
    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract DIDs from Authorization header (only for DID-based methods)"""
        handler = self.get_handler_for_header(auth_header)
        
        if isinstance(handler, DIDAuthHeaderHandler):
            return handler.extract_dids_from_header(auth_header)
        
        # Non-DID methods don't contain DIDs in the header
        return None, None
    
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify Authorization header using appropriate handler"""
        handler = self.get_handler_for_header(auth_header)
        if not handler:
            return AuthenticationResult(False, f"No handler found for Authorization header: {auth_header[:20]}...")
        
        return await handler.verify_auth_header(auth_header, context)
    
    async def build_auth_header(self, method: AuthMethod, context: AuthenticationContext, 
                              credentials: DIDCredentials) -> Dict[str, str]:
        """Build Authorization header for specified method"""
        # For DID methods, use the DID handler
        if method in [AuthMethod.DID_WBA, AuthMethod.DID_KEY, AuthMethod.DID_WEB]:
            handler = self.handlers.get("did_based")
        else:
            handler = self.handlers.get(method.value)
        
        if not handler:
            raise ValueError(f"No handler registered for method: {method.value}")
        
        return await handler.build_auth_header(context, credentials)
    
    async def verify_two_way_auth_response(self, response_auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """
        Verify two-way authentication response.
        SDK-layer business logic for validating server responses.
        """
        try:
            # Get handler for response Authorization header
            handler = self.get_handler_for_header(response_auth_header)
            if not handler:
                return AuthenticationResult(False, "No handler found for response Authorization header")
            
            # For DID-based methods, verify server's identity
            if isinstance(handler, DIDAuthHeaderHandler):
                # Extract DIDs from response header
                server_did, client_did = handler.extract_dids_from_header(response_auth_header)
                
                if not server_did or not client_did:
                    return AuthenticationResult(False, "Invalid response Authorization header")
                
                # Verify that the response is addressed to the correct client
                if client_did != context.caller_did:
                    return AuthenticationResult(False, 
                        f"Response DID mismatch: expected {context.caller_did}, got {client_did}")
                
                # Verify that the response is from the expected server
                if server_did != context.target_did:
                    return AuthenticationResult(False, 
                        f"Server DID mismatch: expected {context.target_did}, got {server_did}")
                
                # Create context for server verification (server is now the caller)
                server_context = AuthenticationContext(
                    caller_did=server_did,
                    target_did=client_did,
                    request_url=context.request_url,
                    method=context.method,
                    use_two_way_auth=True,
                    domain=context.domain
                )
                
                # Verify the server's signature
                return await handler.verify_auth_header(response_auth_header, server_context)
            
            # For other auth methods, use standard verification
            return await handler.verify_auth_header(response_auth_header, context)
            
        except Exception as e:
            logger.error(f"Two-way authentication verification failed: {e}")
            return AuthenticationResult(False, f"Two-way auth error: {e}")
    
    def get_supported_methods(self) -> List[str]:
        """Get list of supported authentication methods"""
        return list(self.handlers.keys())


# Factory function
def create_auth_manager(did_resolver: DIDResolver = None, token_storage: TokenStorage = None, 
                       http_transport: HttpTransport = None) -> AuthenticationManager:
    """Create authentication manager with framework layer dependencies"""
    return AuthenticationManager(did_resolver, token_storage, http_transport)