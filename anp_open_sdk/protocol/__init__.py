"""
ANP Open SDK Protocol Wrapper Package

This package provides protocol-level implementations to centralize agent_connect interactions
and separate pure algorithmic logic from network/file access operations.
"""

# Primary interface - centralized agent_connect wrapper
from .agent_connect_wrapper import (
    get_protocol_wrapper,
    create_verification_method,
    get_curve_mapping,
    resolve_did_document,
    
    # Hotpatch operations
    create_did_wba_document,
    extract_auth_header_parts_two_way,
    verify_auth_header_signature_two_way,
    create_did_wba_auth_header,
    
    # Status monitoring
    get_agent_connect_status,
    
    CURVE_MAPPING,
    AgentConnectProtocolWrapper,
    PureAgentConnectCrypto,
    AgentConnectNetworkOperations,
    AgentConnectHotpatchOperations
)

# Fallback implementations
from .verification_methods import (
    BaseVerificationMethod,
    EcdsaSecp256k1VerificationKey2019,
    Ed25519VerificationKey2020,
    JsonWebKey2020
)

__all__ = [
    # Main interface
    'get_protocol_wrapper',
    'create_verification_method',
    'get_curve_mapping', 
    'resolve_did_document',
    
    # Hotpatch operations
    'create_did_wba_document',
    'extract_auth_header_parts_two_way',
    'verify_auth_header_signature_two_way',
    'create_did_wba_auth_header',
    
    # Status monitoring
    'get_agent_connect_status',
    'CURVE_MAPPING',
    
    # Advanced interfaces
    'AgentConnectProtocolWrapper',
    'PureAgentConnectCrypto',
    'AgentConnectNetworkOperations',
    'AgentConnectHotpatchOperations',
    
    # Fallback implementations
    'BaseVerificationMethod',
    'EcdsaSecp256k1VerificationKey2019',
    'Ed25519VerificationKey2020',
    'JsonWebKey2020'
]