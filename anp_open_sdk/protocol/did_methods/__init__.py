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

# Keep old WBA imports for backward compatibility
from .wba import (
    WBADIDSigner,
    WBAAuthHeaderBuilder, 
    WBAAuthHeaderParser,
    WBADIDAuthenticator,
    create_wba_authenticator
)

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
    'create_wba_authenticator'
]