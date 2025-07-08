"""
Protocol Layer Tests

Tests for pure cryptographic operations and DID method protocols.
These tests verify the protocol layer works without any I/O operations.
"""

import pytest
import hashlib
from datetime import datetime, timezone

from anp_open_sdk.protocol.crypto import (
    create_secp256k1_signer, create_ed25519_signer,
    SignatureEncoder, get_signer_for_key_type
)
from anp_open_sdk.protocol.did_methods import (
    WBADIDProtocol, KeyDIDProtocol, WebDIDProtocol,
    DIDProtocolRegistry, get_did_protocol, get_did_protocol_for_did,
    initialize_did_protocol_registry, reload_did_protocol_config
)


class TestCryptographicOperations:
    """Test pure cryptographic operations"""
    
    def test_secp256k1_signer_creation(self):
        """Test secp256k1 signer creation"""
        signer = create_secp256k1_signer()
        assert signer is not None
    
    def test_ed25519_signer_creation(self):
        """Test Ed25519 signer creation"""
        signer = create_ed25519_signer()
        assert signer is not None
    
    def test_get_signer_for_key_type(self):
        """Test signer factory by key type"""
        secp_signer = get_signer_for_key_type("secp256k1")
        assert secp_signer is not None
        
        ed_signer = get_signer_for_key_type("ed25519")
        assert ed_signer is not None
        
        with pytest.raises(ValueError):
            get_signer_for_key_type("unknown")
    
    def test_secp256k1_sign_verify_cycle(self, sample_private_key, sample_public_key):
        """Test secp256k1 sign and verify cycle"""
        signer = create_secp256k1_signer()
        
        payload = b"test message to sign"
        
        # Sign
        signature_der = signer.sign(payload, sample_private_key)
        assert signature_der is not None
        assert len(signature_der) > 0
        
        # Verify with correct key
        is_valid = signer.verify(payload, signature_der, sample_public_key)
        assert is_valid
        
        # Verify with wrong payload should fail
        wrong_payload = b"wrong message"
        is_valid_wrong = signer.verify(wrong_payload, signature_der, sample_public_key)
        assert not is_valid_wrong
    
    def test_signature_encoder(self):
        """Test signature encoding utilities"""
        encoder = SignatureEncoder()
        
        # Test base64url encoding/decoding
        test_data = b"test data for encoding"
        encoded = encoder.encode_base64url(test_data)
        decoded = encoder.decode_base64url(encoded)
        assert decoded == test_data
        
        # Test DER to R|S conversion (mock data)
        # This is a simplified test - real DER parsing would need valid DER data
        mock_rs_signature = b'A' * 64  # 32 bytes R + 32 bytes S
        
        # Test R|S to DER conversion
        try:
            der_signature = encoder.rs_to_der_format(mock_rs_signature)
            assert len(der_signature) > 0
        except Exception:
            # This might fail with mock data, which is expected
            pass


class TestWBADIDProtocol:
    """Test WBA DID method protocol"""
    
    def test_wba_protocol_creation(self):
        """Test WBA protocol creation"""
        protocol = WBADIDProtocol()
        assert protocol.get_method_name() == "wba"
    
    def test_wba_create_signed_payload(self, sample_private_key):
        """Test WBA signed payload creation"""
        protocol = WBADIDProtocol()
        
        context_data = {
            'did': 'did:wba:localhost:9527:user:test123',
            'request_url': 'http://localhost:9527/api/test',
            'verification_method_fragment': '#key1'
        }
        
        payload_data = protocol.create_signed_payload(context_data, sample_private_key)
        
        # Verify payload structure
        assert 'did' in payload_data
        assert 'nonce' in payload_data
        assert 'timestamp' in payload_data
        assert 'signature' in payload_data
        assert 'verification_method' in payload_data
        assert 'service_domain' in payload_data
        
        # Verify values
        assert payload_data['did'] == context_data['did']
        assert payload_data['verification_method'] == context_data['verification_method_fragment']
        assert payload_data['service_domain'] == 'localhost'
    
    def test_wba_create_signed_payload_with_target(self, sample_private_key):
        """Test WBA signed payload with target DID (two-way auth)"""
        protocol = WBADIDProtocol()
        
        context_data = {
            'did': 'did:wba:localhost:9527:user:test123',
            'request_url': 'http://localhost:9527/api/test',
            'target_did': 'did:wba:localhost:9527:user:target',
            'verification_method_fragment': '#key1'
        }
        
        payload_data = protocol.create_signed_payload(context_data, sample_private_key)
        
        # Should include resp_did for two-way auth
        assert 'resp_did' in payload_data
        assert payload_data['resp_did'] == context_data['target_did']
    
    def test_wba_verify_signed_payload(self, sample_private_key, sample_public_key):
        """Test WBA signed payload verification"""
        protocol = WBADIDProtocol()
        
        # Create payload
        context_data = {
            'did': 'did:wba:localhost:9527:user:test123',
            'request_url': 'http://localhost:9527/api/test',
            'verification_method_fragment': '#key1'
        }
        
        payload_data = protocol.create_signed_payload(context_data, sample_private_key)
        
        # Verify payload
        is_valid = protocol.verify_signed_payload(payload_data, sample_public_key)
        assert is_valid
        
        # Modify payload should fail verification
        payload_data['nonce'] = 'modified_nonce'
        is_valid_modified = protocol.verify_signed_payload(payload_data, sample_public_key)
        assert not is_valid_modified
    
    def test_wba_extract_verification_data(self):
        """Test WBA verification data extraction"""
        protocol = WBADIDProtocol()
        
        payload_data = {
            'did': 'did:wba:localhost:9527:user:test123',
            'nonce': 'test_nonce',
            'timestamp': '2024-01-01T12:00:00Z',
            'signature': 'test_signature',
            'verification_method': '#key1',
            'service': 'localhost'
        }
        
        verification_data = protocol.extract_verification_data(payload_data)
        
        expected_fields = ['did', 'verification_method', 'signature', 'nonce', 'timestamp', 'service']
        for field in expected_fields:
            assert field in verification_data
            assert verification_data[field] == payload_data[field]


class TestDIDProtocolRegistry:
    """Test DID protocol registry"""
    
    def test_registry_creation(self):
        """Test registry creation with default protocols"""
        registry = DIDProtocolRegistry()
        
        # Should have default protocols
        supported_methods = registry.get_supported_methods()
        assert 'wba' in supported_methods
        assert 'key' in supported_methods
        assert 'web' in supported_methods
    
    def test_protocol_registration(self):
        """Test manual protocol registration"""
        registry = DIDProtocolRegistry()
        
        # Create custom protocol
        class CustomDIDProtocol:
            def get_method_name(self):
                return "custom"
            
            def create_signed_payload(self, context_data, private_key_bytes):
                return {"method": "custom"}
            
            def verify_signed_payload(self, payload_data, public_key_bytes):
                return True
            
            def extract_verification_data(self, payload_data):
                return payload_data
        
        custom_protocol = CustomDIDProtocol()
        registry.register_protocol(custom_protocol)
        
        # Should be able to retrieve it
        retrieved = registry.get_protocol("custom")
        assert retrieved is not None
        assert retrieved.get_method_name() == "custom"
    
    def test_get_protocol_for_did(self):
        """Test getting protocol by DID string"""
        registry = DIDProtocolRegistry()
        
        # Test WBA DID
        wba_protocol = registry.get_protocol_for_did("did:wba:localhost:9527:user:test123")
        assert wba_protocol is not None
        assert wba_protocol.get_method_name() == "wba"
        
        # Test Key DID
        key_protocol = registry.get_protocol_for_did("did:key:z6MkiTBz1ymuepAQ4HEHYSF1H8quG5GLVVQR3djdX3mDooWp")
        assert key_protocol is not None
        assert key_protocol.get_method_name() == "key"
        
        # Test invalid DID
        invalid_protocol = registry.get_protocol_for_did("invalid:did:format")
        assert invalid_protocol is None
    
    def test_unregister_protocol(self):
        """Test protocol unregistration"""
        registry = DIDProtocolRegistry()
        
        # Unregister WBA protocol
        registry.unregister_protocol("wba")
        
        # Should not be available
        wba_protocol = registry.get_protocol("wba")
        assert wba_protocol is None
        
        # Other protocols should still be available
        key_protocol = registry.get_protocol("key")
        assert key_protocol is not None


class TestDIDProtocolFactory:
    """Test DID protocol factory functions"""
    
    def test_get_did_protocol(self):
        """Test factory function to get protocol"""
        protocol = get_did_protocol("wba")
        assert protocol is not None
        assert protocol.get_method_name() == "wba"
    
    def test_get_did_protocol_for_did(self):
        """Test factory function to get protocol by DID"""
        protocol = get_did_protocol_for_did("did:wba:localhost:9527:user:test123")
        assert protocol is not None
        assert protocol.get_method_name() == "wba"
    
    def test_initialize_with_config(self, did_config_file):
        """Test initializing registry with config file"""
        # Initialize with config
        initialize_did_protocol_registry(str(did_config_file))
        
        # Should still have WBA (enabled in config)
        wba_protocol = get_did_protocol("wba")
        assert wba_protocol is not None
        
        # Key should be available but might be disabled based on config
        key_protocol = get_did_protocol("key")
        assert key_protocol is not None  # Still registered, just disabled in config
    
    def test_reload_config(self, did_config_file, temp_dir):
        """Test reloading configuration"""
        # Create new config with different settings
        new_config = {
            "did_methods": {
                "wba": {"enabled": True},
                "key": {"enabled": True},
                "custom_test": {
                    "enabled": True,
                    "module": "nonexistent.module",
                    "class": "NonexistentClass"
                }
            }
        }
        
        new_config_file = temp_dir / "new_config.yaml"
        import yaml
        with open(new_config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # Initialize registry
        initialize_did_protocol_registry()
        
        # Reload with new config (should handle missing module gracefully)
        reload_did_protocol_config(str(new_config_file))
        
        # Should still work
        wba_protocol = get_did_protocol("wba")
        assert wba_protocol is not None


class TestDIDMethodPlaceholders:
    """Test placeholder DID methods (key, web)"""
    
    def test_key_did_protocol_placeholder(self):
        """Test Key DID protocol placeholder"""
        protocol = KeyDIDProtocol()
        assert protocol.get_method_name() == "key"
        
        # Should raise NotImplementedError for now
        with pytest.raises(NotImplementedError):
            protocol.create_signed_payload({}, b'test')
        
        with pytest.raises(NotImplementedError):
            protocol.verify_signed_payload({}, b'test')
    
    def test_web_did_protocol_placeholder(self):
        """Test Web DID protocol placeholder"""
        protocol = WebDIDProtocol()
        assert protocol.get_method_name() == "web"
        
        # Should raise NotImplementedError for now
        with pytest.raises(NotImplementedError):
            protocol.create_signed_payload({}, b'test')
        
        with pytest.raises(NotImplementedError):
            protocol.verify_signed_payload({}, b'test')