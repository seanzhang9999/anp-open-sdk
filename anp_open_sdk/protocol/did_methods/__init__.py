"""
DID Methods Package

This package contains pure DID method implementations without any I/O operations.
All network, file, and storage operations are delegated to the framework layer.
"""

# Import from the registry module
from .registry import (
    DIDMethodProtocol,
    WBADIDProtocol,
    KeyDIDProtocol, 
    WebDIDProtocol,
    DIDProtocolRegistry,
    get_did_protocol,
    get_did_protocol_for_did,
    get_did_protocol_registry,
    initialize_did_protocol_registry,
    reload_did_protocol_config,
    register_did_protocol,
    get_supported_did_methods
)

# Legacy WBA API - using protocol implementations for backward compatibility
from .registry import WBADIDProtocol
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Compatibility aliases
WBADIDSigner = WBADIDProtocol
WBAAuthHeaderBuilder = WBADIDProtocol
WBAAuthHeaderParser = WBADIDProtocol
WBADIDAuthenticator = WBADIDProtocol

def create_wba_authenticator():
    """Create WBA authenticator - compatibility function"""
    return WBADIDProtocol()

# Abstract base classes for framework adapters
class DIDResolver(ABC):
    """Abstract DID resolver interface"""
    
    @abstractmethod
    async def resolve_did_document(self, did: str) -> Optional[Dict[str, Any]]:
        pass

class TokenStorage(ABC):
    """Abstract token storage interface"""
    
    @abstractmethod
    async def store_token(self, did: str, token: str) -> bool:
        pass
    
    @abstractmethod
    async def get_token(self, did: str) -> Optional[str]:
        pass

class HttpTransport(ABC):
    """Abstract HTTP transport interface"""
    
    @abstractmethod
    async def send_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        pass

__all__ = [
    # New protocol API
    'DIDMethodProtocol',
    'WBADIDProtocol',
    'KeyDIDProtocol',
    'WebDIDProtocol', 
    'DIDProtocolRegistry',
    'get_did_protocol',
    'get_did_protocol_for_did',
    'get_did_protocol_registry',
    'initialize_did_protocol_registry',
    'reload_did_protocol_config',
    'register_did_protocol',
    'get_supported_did_methods',
    
    # Legacy WBA API
    'WBADIDSigner',
    'WBAAuthHeaderBuilder',
    'WBAAuthHeaderParser', 
    'WBADIDAuthenticator',
    'create_wba_authenticator',
    
    # Framework adapter interfaces
    'DIDResolver',
    'TokenStorage',
    'HttpTransport'
]