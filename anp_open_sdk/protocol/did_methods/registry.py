"""
Protocol Layer - DID Method Implementations

This module contains pure DID method implementations without any I/O operations.
Each DID method provides cryptographic operations and payload construction logic.

The SDK layer will use these methods and add Authorization header processing.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import jcs

from ..crypto import create_secp256k1_signer, create_ed25519_signer, SignatureEncoder

logger = logging.getLogger(__name__)


class DIDMethodProtocol(ABC):
    """Abstract base class for DID method protocols"""
    
    @abstractmethod
    def get_method_name(self) -> str:
        """Get the DID method name (e.g., 'wba', 'key', 'web')"""
        pass
    
    @abstractmethod
    def create_signed_payload(self, context_data: Dict[str, Any], private_key_bytes: bytes) -> Dict[str, Any]:
        """Create signed payload for this DID method"""
        pass
    
    @abstractmethod
    def verify_signed_payload(self, payload_data: Dict[str, Any], public_key_bytes: bytes) -> bool:
        """Verify signed payload for this DID method"""
        pass
    
    @abstractmethod
    def extract_verification_data(self, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for verification from payload"""
        pass


class WBADIDProtocol(DIDMethodProtocol):
    """
    WBA DID Method Protocol Implementation
    
    Implements the pure WBA signing and verification logic without any I/O.
    """
    
    def __init__(self):
        self.crypto_signer = create_secp256k1_signer()
        self.encoder = SignatureEncoder()
    
    def get_method_name(self) -> str:
        return "wba"
    
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
    
    def create_signed_payload(self, context_data: Dict[str, Any], private_key_bytes: bytes) -> Dict[str, Any]:
        """
        Create WBA signed payload.
        
        Args:
            context_data: Contains 'did', 'request_url', 'target_did' (optional), etc.
            private_key_bytes: Private key for signing
            
        Returns:
            Dict containing all data needed for WBA Authorization header
        """
        try:
            did = context_data['did']
            request_url = context_data['request_url']
            target_did = context_data.get('target_did')
            verification_method_fragment = context_data['verification_method_fragment']
            
            nonce = secrets.token_hex(16)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            service_domain = self._get_domain(request_url)

            # Build canonical data to sign
            data_to_sign = {
                "nonce": nonce,
                "timestamp": timestamp,
                "service": service_domain,
                "did": did,
            }
            if target_did:
                data_to_sign["resp_did"] = target_did

            # Create canonical JSON and hash
            canonical_json = jcs.canonicalize(data_to_sign)
            content_hash = hashlib.sha256(canonical_json).digest()

            # Sign using protocol layer crypto
            signature_der = self.crypto_signer.sign(content_hash, private_key_bytes)
            
            # Convert to R|S format and encode
            signature_rs = self.encoder.der_to_rs_format(signature_der)
            signature_b64 = self.encoder.encode_base64url(signature_rs)

            # Return all data needed for Authorization header
            return {
                "did": did,
                "nonce": nonce,
                "timestamp": timestamp,
                "signature": signature_b64,
                "verification_method": verification_method_fragment,
                "resp_did": target_did,  # May be None
                "service_domain": service_domain,
                "canonical_data": data_to_sign
            }
            
        except Exception as e:
            logger.error(f"WBA payload creation failed: {e}")
            raise
    
    def verify_signed_payload(self, payload_data: Dict[str, Any], public_key_bytes: bytes) -> bool:
        """
        Verify WBA signed payload.
        
        Args:
            payload_data: Contains parsed WBA data (nonce, timestamp, signature, etc.)
            public_key_bytes: Public key for verification
            
        Returns:
            True if signature is valid
        """
        try:
            # Reconstruct the canonical data that was signed
            data_to_verify = {
                "nonce": payload_data['nonce'],
                "timestamp": payload_data['timestamp'],
                "service": payload_data['service'],
                "did": payload_data['did'],
            }
            if 'resp_did' in payload_data and payload_data['resp_did']:
                data_to_verify["resp_did"] = payload_data['resp_did']

            # Create same canonical hash
            canonical_json = jcs.canonicalize(data_to_verify)
            content_hash = hashlib.sha256(canonical_json).digest()

            # Decode signature and convert to DER
            signature_rs = self.encoder.decode_base64url(payload_data['signature'])
            signature_der = self.encoder.rs_to_der_format(signature_rs)

            # Verify using protocol layer crypto
            return self.crypto_signer.verify(content_hash, signature_der, public_key_bytes)
            
        except Exception as e:
            logger.error(f"WBA payload verification failed: {e}")
            return False
    
    def extract_verification_data(self, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data needed for WBA verification"""
        return {
            "did": payload_data.get('did'),
            "verification_method": payload_data.get('verification_method'),
            "signature": payload_data.get('signature'),
            "nonce": payload_data.get('nonce'),
            "timestamp": payload_data.get('timestamp'),
            "service": payload_data.get('service'),
            "resp_did": payload_data.get('resp_did')
        }


class KeyDIDProtocol(DIDMethodProtocol):
    """
    Key DID Method Protocol Implementation (future)
    
    Placeholder for did:key method implementation.
    """
    
    def __init__(self):
        # Could support both secp256k1 and ed25519
        self.secp256k1_signer = create_secp256k1_signer()
        self.ed25519_signer = create_ed25519_signer()
        self.encoder = SignatureEncoder()
    
    def get_method_name(self) -> str:
        return "key"
    
    def create_signed_payload(self, context_data: Dict[str, Any], private_key_bytes: bytes) -> Dict[str, Any]:
        """Create Key DID signed payload"""
        # Placeholder implementation
        raise NotImplementedError("Key DID method not implemented yet")
    
    def verify_signed_payload(self, payload_data: Dict[str, Any], public_key_bytes: bytes) -> bool:
        """Verify Key DID signed payload"""
        # Placeholder implementation
        raise NotImplementedError("Key DID method not implemented yet")
    
    def extract_verification_data(self, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Key DID verification data"""
        # Placeholder implementation
        raise NotImplementedError("Key DID method not implemented yet")


class WebDIDProtocol(DIDMethodProtocol):
    """
    Web DID Method Protocol Implementation (future)
    
    Placeholder for did:web method implementation.
    """
    
    def get_method_name(self) -> str:
        return "web"
    
    def create_signed_payload(self, context_data: Dict[str, Any], private_key_bytes: bytes) -> Dict[str, Any]:
        """Create Web DID signed payload"""
        # Placeholder implementation
        raise NotImplementedError("Web DID method not implemented yet")
    
    def verify_signed_payload(self, payload_data: Dict[str, Any], public_key_bytes: bytes) -> bool:
        """Verify Web DID signed payload"""
        # Placeholder implementation
        raise NotImplementedError("Web DID method not implemented yet")
    
    def extract_verification_data(self, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Web DID verification data"""
        # Placeholder implementation
        raise NotImplementedError("Web DID method not implemented yet")


# Protocol Registry and Factory
class DIDProtocolRegistry:
    """Registry for DID method protocols with configuration support"""
    
    def __init__(self, config_file: Optional[str] = None):
        self._protocols: Dict[str, DIDMethodProtocol] = {}
        self._register_default_protocols()
        
        # Load additional protocols from config if provided
        if config_file:
            self._load_protocols_from_config(config_file)
    
    def _register_default_protocols(self):
        """Register default DID method protocols"""
        self.register_protocol(WBADIDProtocol())
        self.register_protocol(KeyDIDProtocol())
        self.register_protocol(WebDIDProtocol())
    
    def _load_protocols_from_config(self, config_file: str):
        """Load DID method protocols from configuration file"""
        try:
            import yaml
            import importlib
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            did_methods = config.get('did_methods', {})
            
            for method_name, method_config in did_methods.items():
                if method_config.get('enabled', False):
                    self._load_protocol_from_config(method_name, method_config)
                    
        except Exception as e:
            logger.error(f"Failed to load DID protocols from config: {e}")
    
    def _load_protocol_from_config(self, method_name: str, config: Dict[str, Any]):
        """Load a single DID protocol from configuration"""
        try:
            # Support both built-in and external protocols
            module_path = config.get('module')
            class_name = config.get('class')
            
            if module_path and class_name:
                # Load external protocol
                module = importlib.import_module(module_path)
                protocol_class = getattr(module, class_name)
                
                # Pass config parameters to protocol constructor
                protocol_params = config.get('parameters', {})
                protocol = protocol_class(**protocol_params)
                
                self.register_protocol(protocol)
                logger.info(f"Loaded DID method '{method_name}' from {module_path}.{class_name}")
            
        except Exception as e:
            logger.error(f"Failed to load DID method '{method_name}': {e}")
    
    def register_protocol(self, protocol: DIDMethodProtocol):
        """Register a DID method protocol"""
        self._protocols[protocol.get_method_name()] = protocol
    
    def unregister_protocol(self, method_name: str):
        """Unregister a DID method protocol"""
        if method_name in self._protocols:
            del self._protocols[method_name]
    
    def get_protocol(self, method_name: str) -> Optional[DIDMethodProtocol]:
        """Get protocol by method name"""
        return self._protocols.get(method_name)
    
    def get_protocol_for_did(self, did: str) -> Optional[DIDMethodProtocol]:
        """Get protocol for a DID string (e.g., 'did:wba:...' -> WBADIDProtocol)"""
        if not did.startswith("did:"):
            return None
        
        parts = did.split(":")
        if len(parts) < 3:
            return None
        
        method_name = parts[1]
        return self.get_protocol(method_name)
    
    def get_supported_methods(self) -> List[str]:
        """Get list of supported DID methods"""
        return list(self._protocols.keys())
    
    def reload_config(self, config_file: str):
        """Reload configuration and update protocols"""
        # Clear non-default protocols
        default_methods = {'wba', 'key', 'web'}
        for method_name in list(self._protocols.keys()):
            if method_name not in default_methods:
                self.unregister_protocol(method_name)
        
        # Load new config
        self._load_protocols_from_config(config_file)


# Global registry instance
_protocol_registry = None


# Factory functions with configuration support
def initialize_did_protocol_registry(config_file: Optional[str] = None):
    """Initialize the global DID protocol registry with optional config file"""
    global _protocol_registry
    _protocol_registry = DIDProtocolRegistry(config_file)


def get_did_protocol_registry() -> DIDProtocolRegistry:
    """Get the global DID protocol registry"""
    global _protocol_registry
    if _protocol_registry is None:
        _protocol_registry = DIDProtocolRegistry()
    return _protocol_registry


def get_did_protocol(method_name: str) -> Optional[DIDMethodProtocol]:
    """Get DID protocol by method name"""
    registry = get_did_protocol_registry()
    return registry.get_protocol(method_name)


def get_did_protocol_for_did(did: str) -> Optional[DIDMethodProtocol]:
    """Get DID protocol for a specific DID"""
    registry = get_did_protocol_registry()
    return registry.get_protocol_for_did(did)


def register_did_protocol(protocol: DIDMethodProtocol):
    """Register a new DID protocol"""
    registry = get_did_protocol_registry()
    registry.register_protocol(protocol)


def get_supported_did_methods() -> List[str]:
    """Get list of supported DID methods"""
    registry = get_did_protocol_registry()
    return registry.get_supported_methods()


def reload_did_protocol_config(config_file: str):
    """Reload DID protocol configuration"""
    registry = get_did_protocol_registry()
    registry.reload_config(config_file)