"""
Session Management - SDK Layer Extension

This module adds session-based authentication support to the existing auth system.
Sessions can work alongside existing DID and token authentication methods.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
from enum import Enum

from .auth_manager import AuthHeaderHandler, AuthenticationResult, AuthMethod
from .schemas import AuthenticationContext, DIDCredentials

logger = logging.getLogger(__name__)


class SessionStorage(ABC):
    """Abstract session storage - implemented by framework layer"""
    
    @abstractmethod
    async def create_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Create a new session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions, return count of removed sessions"""
        pass


class SessionManager:
    """Session manager for SDK layer"""
    
    def __init__(self, session_storage: SessionStorage, default_expiry_hours: int = 24):
        self.session_storage = session_storage
        self.default_expiry_hours = default_expiry_hours
    
    async def create_session(self, caller_did: str, target_did: str, 
                           auth_method: str = "did", **session_data) -> str:
        """Create a new session after successful authentication"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.default_expiry_hours)
        
        session_info = {
            "session_id": session_id,
            "caller_did": caller_did,
            "target_did": target_did,
            "auth_method": auth_method,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            **session_data
        }
        
        success = await self.session_storage.create_session(session_id, session_info)
        return session_id if success else None
    
    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and update last_used timestamp"""
        session_data = await self.session_storage.get_session(session_id)
        if not session_data:
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            await self.session_storage.delete_session(session_id)
            return None
        
        # Update last_used
        session_data["last_used"] = datetime.now(timezone.utc).isoformat()
        await self.session_storage.update_session(session_id, session_data)
        
        return session_data
    
    async def extend_session(self, session_id: str, hours: int = None) -> bool:
        """Extend session expiration"""
        hours = hours or self.default_expiry_hours
        session_data = await self.session_storage.get_session(session_id)
        if not session_data:
            return False
        
        new_expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        session_data["expires_at"] = new_expires_at.isoformat()
        
        return await self.session_storage.update_session(session_id, session_data)
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke/delete session"""
        return await self.session_storage.delete_session(session_id)


class SessionAuthHandler(AuthHeaderHandler):
    """Handler for session-based Authorization headers"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    def get_auth_method(self) -> str:
        return "session"
    
    def can_handle_header(self, auth_header: str) -> bool:
        return auth_header.startswith("Session ") or auth_header.startswith("SessionID ")
    
    async def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        """Build session Authorization header (typically after login)"""
        # This would typically be called after successful DID authentication
        # to create a session for subsequent requests
        return {"Authorization": "Session <session_id>"}
    
    async def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """Parse session Authorization header"""
        if auth_header.startswith("Session "):
            session_id = auth_header[8:]  # Remove "Session "
            return {"session_id": session_id, "type": "session"}
        elif auth_header.startswith("SessionID "):
            session_id = auth_header[10:]  # Remove "SessionID "
            return {"session_id": session_id, "type": "session"}
        return {}
    
    async def verify_auth_header(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """Verify session Authorization header"""
        try:
            parsed_data = await self.parse_auth_header(auth_header)
            session_id = parsed_data.get("session_id")
            
            if not session_id:
                return AuthenticationResult(False, "Invalid session format")
            
            # Validate session
            session_data = await self.session_manager.validate_session(session_id)
            if not session_data:
                return AuthenticationResult(False, "Invalid or expired session")
            
            # Verify session belongs to the context
            if (context.caller_did and session_data.get("caller_did") != context.caller_did):
                return AuthenticationResult(False, "Session DID mismatch")
            
            if (context.target_did and session_data.get("target_did") != context.target_did):
                return AuthenticationResult(False, "Session target mismatch")
            
            return AuthenticationResult(True, "Session verification successful", {
                "session_data": session_data
            })
            
        except Exception as e:
            logger.error(f"Session verification failed: {e}")
            return AuthenticationResult(False, f"Session verification error: {e}")


# Extended AuthMethod enum - cannot inherit from Enum, so define all values
class ExtendedAuthMethod(Enum):
    """Extended authentication methods including session"""
    DID_WBA = "did_wba"
    DID_KEY = "did_key" 
    DID_WEB = "did_web"
    BEARER = "bearer"
    TOKEN = "token"
    SESSION = "session"


class SessionAwareAuthenticationManager:
    """
    Extended authentication manager with session support.
    
    Provides session-based authentication as an additional layer
    on top of existing DID/token authentication.
    """
    
    def __init__(self, base_auth_manager, session_manager: SessionManager):
        self.base_auth_manager = base_auth_manager
        self.session_manager = session_manager
        
        # Register session handler
        session_handler = SessionAuthHandler(session_manager)
        self.base_auth_manager.register_handler(session_handler)
    
    async def authenticate_and_create_session(self, auth_header: str, context: AuthenticationContext) -> tuple[AuthenticationResult, Optional[str]]:
        """
        Authenticate using DID/token methods and create session on success.
        
        Returns (auth_result, session_id)
        """
        # First authenticate using existing methods (DID/token)
        auth_result = await self.base_auth_manager.verify_auth_header(auth_header, context)
        
        if not auth_result.success:
            return auth_result, None
        
        # Create session after successful authentication
        session_id = await self.session_manager.create_session(
            caller_did=context.caller_did,
            target_did=context.target_did,
            auth_method=self._get_auth_method_from_header(auth_header),
            request_url=context.request_url
        )
        
        return auth_result, session_id
    
    def _get_auth_method_from_header(self, auth_header: str) -> str:
        """Determine auth method from header"""
        if auth_header.startswith("DIDWba "):
            return "did_wba"
        elif auth_header.startswith("Bearer "):
            return "bearer"
        elif auth_header.startswith("Token "):
            return "token"
        else:
            return "unknown"
    
    async def verify_with_session_fallback(self, auth_header: str, context: AuthenticationContext) -> AuthenticationResult:
        """
        Verify using session first, fall back to full authentication.
        
        This is useful for APIs that want to support both session-based
        and per-request authentication.
        """
        # If it's a session header, verify session
        if auth_header.startswith("Session ") or auth_header.startswith("SessionID "):
            return await self.base_auth_manager.verify_auth_header(auth_header, context)
        
        # Otherwise use standard authentication
        return await self.base_auth_manager.verify_auth_header(auth_header, context)


# Example usage patterns:

class SessionBasedAPI:
    """Example of how to use session-aware authentication in an API"""
    
    def __init__(self, session_auth_manager: SessionAwareAuthenticationManager):
        self.auth_manager = session_auth_manager
    
    async def login(self, auth_header: str, context: AuthenticationContext) -> Dict[str, Any]:
        """Login endpoint - authenticate and create session"""
        auth_result, session_id = await self.auth_manager.authenticate_and_create_session(
            auth_header, context
        )
        
        if auth_result.success:
            return {
                "success": True,
                "session_id": session_id,
                "message": "Login successful"
            }
        else:
            return {
                "success": False,
                "message": auth_result.message
            }
    
    async def protected_endpoint(self, auth_header: str, context: AuthenticationContext) -> Dict[str, Any]:
        """Protected endpoint - verify session or full auth"""
        auth_result = await self.auth_manager.verify_with_session_fallback(
            auth_header, context
        )
        
        if auth_result.success:
            return {"success": True, "data": "protected data"}
        else:
            return {"success": False, "message": auth_result.message}
    
    async def logout(self, session_id: str) -> Dict[str, Any]:
        """Logout endpoint - revoke session"""
        success = await self.auth_manager.session_manager.revoke_session(session_id)
        return {
            "success": success,
            "message": "Logout successful" if success else "Logout failed"
        }