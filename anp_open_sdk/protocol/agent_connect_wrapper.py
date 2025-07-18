"""
ANP Open SDK Protocol Wrapper - Centralized Agent Connect Interface

This module provides a centralized interface to manage agent_connect library dependencies,
building on the existing core architecture that separates pure algorithmic logic from 
network/file access operations.

Design Goals:
1. Centralize all agent_connect interactions in one place
2. Leverage existing core/ abstractions (BaseTransport, BaseUserData, etc.)
3. Provide clean interfaces for agent_connect evolution
4. Enable better testing and mocking capabilities
"""

import logging
from typing import Dict, Union, Optional, Any, Tuple
from abc import ABC, abstractmethod

from anp_open_sdk.core.base_transport import RequestContext, ResponseContext

logger = logging.getLogger(__name__)


class AgentConnectCryptoInterface(ABC):
    """
    Abstract interface for agent_connect cryptographic functionality.
    This allows us to control and iterate on agent_connect integration.
    """
    
    @abstractmethod
    def create_verification_method(self, verification_method: Dict) -> Any:
        """Create verification method for signature operations"""
        pass
    
    @abstractmethod
    def get_curve_mapping(self) -> Dict:
        """Get supported curve mappings"""
        pass


class PureAgentConnectCrypto:
    """
    Pure cryptographic operations using agent_connect or fallback implementations.
    This class contains only pure algorithmic logic, no network/file access.
    Leverages the existing auth_methods/wba/implementation.py patterns.
    """
    
    def __init__(self):
        self._agent_connect_available = self._check_agent_connect_availability()
        self._fallback_available = self._check_fallback_availability()
    
    def _check_agent_connect_availability(self) -> bool:
        """Check if agent_connect library is available"""
        try:
            import agent_connect.authentication.verification_methods
            return True
        except ImportError:
            logger.info("agent_connect library not available, using fallback implementation")
            return False
    
    def _check_fallback_availability(self) -> bool:
        """Check if fallback implementation is available"""
        try:
            from anp_open_sdk.protocol.verification_methods import create_verification_method
            return True
        except ImportError:
            logger.warning("Fallback verification methods not available")
            return False
    
    def create_verification_method(self, verification_method: Dict) -> Any:
        """
        Create verification method using agent_connect or fallback.
        Pure algorithmic operation - no network/file access.
        Follows the pattern from auth_methods/wba/implementation.py
        """
        if self._agent_connect_available:
            try:
                from agent_connect.authentication.verification_methods import create_verification_method
                return create_verification_method(verification_method)
            except Exception as e:
                logger.warning(f"agent_connect verification method creation failed: {e}")
                if self._fallback_available:
                    return self._fallback_create_verification_method(verification_method)
                else:
                    raise
        elif self._fallback_available:
            return self._fallback_create_verification_method(verification_method)
        else:
            raise RuntimeError("No verification method implementation available")
    
    def get_curve_mapping(self) -> Dict:
        """
        Get curve mapping from agent_connect or fallback.
        Pure configuration data - no network/file access.
        """
        if self._agent_connect_available:
            try:
                from agent_connect.authentication.verification_methods import CURVE_MAPPING
                return CURVE_MAPPING
            except Exception as e:
                logger.warning(f"agent_connect curve mapping access failed: {e}")
                if self._fallback_available:
                    return self._fallback_curve_mapping()
                else:
                    raise
        elif self._fallback_available:
            return self._fallback_curve_mapping()
        else:
            raise RuntimeError("No curve mapping implementation available")
    
    def _fallback_create_verification_method(self, verification_method: Dict) -> Any:
        """Fallback implementation using our local verification methods"""
        from anp_open_sdk.protocol.verification_methods import create_verification_method
        return create_verification_method(verification_method)
    
    def _fallback_curve_mapping(self) -> Dict:
        """Fallback implementation using our local curve mapping"""
        from anp_open_sdk.protocol.verification_methods import CURVE_MAPPING
        return CURVE_MAPPING


class AgentConnectNetworkOperations:
    """
    Network-related operations that use agent_connect.
    This class isolates all network access operations, working with core/base_transport.py
    """
    
    def __init__(self):
        self._agent_connect_available = self._check_agent_connect_availability()
    
    def _check_agent_connect_availability(self) -> bool:
        """Check if agent_connect library is available"""
        try:
            import agent_connect.authentication
            return True
        except ImportError:
            logger.info("agent_connect library not available for network operations")
            return False
    
    async def resolve_did_document(self, did: str) -> Optional[Dict]:
        """
        Resolve DID document using agent_connect or fallback.
        Network operation - requires external access.
        Integrates with core/base_transport.py patterns.
        """
        if self._agent_connect_available:
            try:
                from agent_connect.authentication import resolve_did_wba_document
                return await resolve_did_wba_document(did)
            except Exception as e:
                logger.warning(f"agent_connect DID resolution failed: {e}")
                return await self._fallback_resolve_did_document(did)
        else:
            return await self._fallback_resolve_did_document(did)
    
    async def _fallback_resolve_did_document(self, did: str) -> Optional[Dict]:
        """Fallback implementation using our local DID resolution"""
        from anp_open_sdk.protocol.authentication.did_wba import resolve_did_wba_document
        return await resolve_did_wba_document(did)


class AgentConnectHotpatchOperations:
    """
    Hotpatch operations that use agent_connect_hotpatch.
    This class provides centralized access to hotpatch functionality.
    """
    
    def __init__(self):
        self._hotpatch_available = self._check_hotpatch_availability()
    
    def _check_hotpatch_availability(self) -> bool:
        """Check if protocol authentication is available"""
        try:
            import anp_open_sdk.protocol.authentication.did_wba
            return True
        except ImportError:
            logger.info("protocol authentication not available")
            return False
    
    async def create_did_wba_document(self, *args, **kwargs) -> Dict[str, Any]:
        """Create DID WBA document using protocol authentication"""
        if self._hotpatch_available:
            try:
                from anp_open_sdk.protocol.authentication.did_wba import create_did_wba_document
                return create_did_wba_document(*args, **kwargs)
            except Exception as e:
                logger.error(f"Protocol create_did_wba_document failed: {e}")
                raise
        else:
            raise RuntimeError("No DID WBA document creation implementation available")
    
    def extract_auth_header_parts_two_way(self, auth_header: str) -> Dict[str, Any]:
        """Extract auth header parts using protocol authentication"""
        if self._hotpatch_available:
            try:
                from anp_open_sdk.protocol.authentication.did_wba import extract_auth_header_parts_two_way
                return extract_auth_header_parts_two_way(auth_header)
            except Exception as e:
                logger.error(f"Protocol extract_auth_header_parts_two_way failed: {e}")
                raise
        else:
            raise RuntimeError("No auth header parsing implementation available")
    
    def verify_auth_header_signature_two_way(self, *args, **kwargs):
        """Verify auth header signature using protocol authentication"""
        if self._hotpatch_available:
            try:
                from anp_open_sdk.protocol.authentication.did_wba import verify_auth_header_signature_two_way
                return verify_auth_header_signature_two_way(*args, **kwargs)
            except Exception as e:
                logger.error(f"Protocol verify_auth_header_signature_two_way failed: {e}")
                raise
        else:
            raise RuntimeError("No auth header signature verification implementation available")
    
    def create_did_wba_auth_header(self, *args, **kwargs):
        """Create DID WBA auth header using protocol authentication"""
        if self._hotpatch_available:
            try:
                from anp_open_sdk.protocol.authentication.did_wba_auth_header import DIDWbaAuthHeader
                return DIDWbaAuthHeader(*args, **kwargs)
            except Exception as e:
                logger.error(f"Protocol DIDWbaAuthHeader creation failed: {e}")
                raise
        else:
            raise RuntimeError("No DID WBA auth header implementation available")


class AgentConnectProtocolWrapper:
    """
    Main protocol wrapper that provides centralized agent_connect interface.
    This class orchestrates pure crypto, network operations, and hotpatch functionality,
    leveraging the existing core/ architecture.
    """
    
    def __init__(self):
        self.crypto = PureAgentConnectCrypto()
        self.network = AgentConnectNetworkOperations()
        self.hotpatch = AgentConnectHotpatchOperations()
        logger.info("AgentConnect Protocol Wrapper initialized with core/ integration including hotpatch")
    
    def create_verification_method(self, verification_method: Dict) -> Any:
        """Create verification method (pure crypto operation)"""
        return self.crypto.create_verification_method(verification_method)
    
    def get_curve_mapping(self) -> Dict:
        """Get curve mapping (pure data operation)"""
        return self.crypto.get_curve_mapping()
    
    async def resolve_did_document(self, did: str) -> Optional[Dict]:
        """Resolve DID document (network operation)"""
        return await self.network.resolve_did_document(did)
    
    async def create_did_wba_document(self, *args, **kwargs) -> Dict[str, Any]:
        """Create DID WBA document (hotpatch operation)"""
        return await self.hotpatch.create_did_wba_document(*args, **kwargs)
    
    def extract_auth_header_parts_two_way(self, auth_header: str) -> Dict[str, Any]:
        """Extract auth header parts (hotpatch operation)"""
        return self.hotpatch.extract_auth_header_parts_two_way(auth_header)
    
    def verify_auth_header_signature_two_way(self, *args, **kwargs):
        """Verify auth header signature (hotpatch operation)"""
        return self.hotpatch.verify_auth_header_signature_two_way(*args, **kwargs)
    
    def create_did_wba_auth_header(self, *args, **kwargs):
        """Create DID WBA auth header (hotpatch operation)"""
        return self.hotpatch.create_did_wba_auth_header(*args, **kwargs)
    
    def get_crypto_interface(self) -> PureAgentConnectCrypto:
        """Get pure crypto interface for advanced operations"""
        return self.crypto
    
    def get_network_interface(self) -> AgentConnectNetworkOperations:
        """Get network interface for advanced operations"""
        return self.network
    
    def get_hotpatch_interface(self) -> AgentConnectHotpatchOperations:
        """Get hotpatch interface for advanced operations"""
        return self.hotpatch
    
    def is_agent_connect_available(self) -> bool:
        """Check if agent_connect is available for operations"""
        return self.crypto._agent_connect_available and self.network._agent_connect_available
    
    def is_hotpatch_available(self) -> bool:
        """Check if hotpatch is available for operations"""
        return self.hotpatch._hotpatch_available
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get detailed status of agent_connect integration"""
        return {
            "crypto_available": self.crypto._agent_connect_available,
            "crypto_fallback_available": self.crypto._fallback_available,
            "network_available": self.network._agent_connect_available,
            "hotpatch_available": self.hotpatch._hotpatch_available,
            "overall_status": "healthy" if self.is_agent_connect_available() else "fallback_mode"
        }


# Global instance for easy access (following singleton pattern used in core/)
_protocol_wrapper = None


def get_protocol_wrapper() -> AgentConnectProtocolWrapper:
    """Get global protocol wrapper instance"""
    global _protocol_wrapper
    if _protocol_wrapper is None:
        _protocol_wrapper = AgentConnectProtocolWrapper()
    return _protocol_wrapper


# Convenience functions for common operations
def create_verification_method(verification_method: Dict) -> Any:
    """Create verification method using centralized protocol wrapper"""
    return get_protocol_wrapper().create_verification_method(verification_method)


def get_curve_mapping() -> Dict:
    """Get curve mapping using centralized protocol wrapper"""
    return get_protocol_wrapper().get_curve_mapping()


async def resolve_did_document(did: str) -> Optional[Dict]:
    """Resolve DID document using centralized protocol wrapper"""
    return await get_protocol_wrapper().resolve_did_document(did)


async def create_did_wba_document(*args, **kwargs) -> Dict[str, Any]:
    """Create DID WBA document using centralized protocol wrapper"""
    return await get_protocol_wrapper().create_did_wba_document(*args, **kwargs)


def extract_auth_header_parts_two_way(auth_header: str) -> Dict[str, Any]:
    """Extract auth header parts using centralized protocol wrapper"""
    return get_protocol_wrapper().extract_auth_header_parts_two_way(auth_header)


def verify_auth_header_signature_two_way(*args, **kwargs):
    """Verify auth header signature using centralized protocol wrapper"""
    return get_protocol_wrapper().verify_auth_header_signature_two_way(*args, **kwargs)


def create_did_wba_auth_header(*args, **kwargs):
    """Create DID WBA auth header using centralized protocol wrapper"""
    return get_protocol_wrapper().create_did_wba_auth_header(*args, **kwargs)


def get_agent_connect_status() -> Dict[str, Any]:
    """Get agent_connect integration status report"""
    return get_protocol_wrapper().get_status_report()


# Legacy compatibility - these will be the main interface points
try:
    CURVE_MAPPING = get_curve_mapping()
except Exception as e:
    logger.warning(f"Failed to initialize CURVE_MAPPING: {e}")
    CURVE_MAPPING = {}