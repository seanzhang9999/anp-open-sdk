"""
Test Suite for ANP SDK Refactoring

This test suite ensures that the layered architecture refactoring works correctly.

Test Structure:
- test_protocol/: Protocol layer tests (crypto, DID methods)
- test_sdk/: SDK layer tests (auth manager, Authorization headers)
- test_framework/: Framework layer tests (I/O adapters)
- test_integration/: End-to-end integration tests
- test_session/: Session management tests
- test_config/: Configuration loading tests
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import json
import yaml

# Test fixtures and utilities
@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_did_document():
    """Sample DID document for testing"""
    return {
        "id": "did:wba:localhost:9527:user:test123",
        "verificationMethod": [
            {
                "id": "did:wba:localhost:9527:user:test123#key1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": "did:wba:localhost:9527:user:test123",
                "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G"
            }
        ],
        "authentication": [
            "did:wba:localhost:9527:user:test123#key1"
        ]
    }

@pytest.fixture
def sample_private_key():
    """Sample private key for testing (32 bytes for secp256k1)"""
    # Valid secp256k1 private key for testing (not for production use)
    return bytes.fromhex("1111111111111111111111111111111111111111111111111111111111111111")

@pytest.fixture 
def sample_public_key():
    """Sample public key for testing (calculated from private key)"""
    # Generate the corresponding public key from the private key
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    
    private_key_bytes = bytes.fromhex("1111111111111111111111111111111111111111111111111111111111111111")
    private_key_int = int.from_bytes(private_key_bytes, 'big')
    private_key = ec.derive_private_key(private_key_int, ec.SECP256K1())
    
    public_key = private_key.public_key()
    
    # Get uncompressed public key bytes (65 bytes: 0x04 + 32 bytes x + 32 bytes y)
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    return public_key_bytes

@pytest.fixture
def did_config_file(temp_dir):
    """Create DID methods config file for testing"""
    config = {
        "did_methods": {
            "wba": {
                "enabled": True,
                "description": "Test WBA method"
            },
            "key": {
                "enabled": False,
                "description": "Test Key method"
            }
        },
        "session": {
            "enabled": True,
            "default_expiry_hours": 24
        }
    }
    
    config_file = temp_dir / "test_did_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Test data utilities
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_auth_context(caller_did: str = "did:wba:localhost:9527:user:test123",
                          target_did: str = "did:wba:localhost:9527:user:target",
                          request_url: str = "http://localhost:9527/api/test",
                          use_two_way_auth: bool = False):
        """Create authentication context for testing"""
        from anp_open_sdk.auth.schemas import AuthenticationContext
        
        return AuthenticationContext(
            caller_did=caller_did,
            target_did=target_did if use_two_way_auth else None,
            request_url=request_url,
            method="POST",
            use_two_way_auth=use_two_way_auth,
            domain="localhost"
        )
    
    @staticmethod
    def create_did_credentials(did: str, did_document: Dict[str, Any], private_key_bytes: bytes):
        """Create DID credentials for testing"""
        from anp_open_sdk.auth.schemas import DIDCredentials, DIDDocument, DIDKeyPair
        
        # Create DID document
        did_doc = DIDDocument(**did_document, raw_document=did_document)
        
        # Create key pair
        key_pair = DIDKeyPair(
            key_id="key1",
            private_key_bytes=private_key_bytes,
            key_type="secp256k1"
        )
        
        return DIDCredentials(
            did=did,
            did_document=did_doc,
            key_pairs={"key1": key_pair}
        )

# Mock classes for testing
class MockDIDResolver:
    """Mock DID resolver for testing"""
    
    def __init__(self, did_documents: Dict[str, Dict[str, Any]] = None):
        self.did_documents = did_documents or {}
    
    async def resolve_did_document(self, did: str):
        """Mock DID document resolution"""
        if did in self.did_documents:
            from anp_open_sdk.auth.schemas import DIDDocument
            raw_doc = self.did_documents[did]
            return DIDDocument(**raw_doc, raw_document=raw_doc)
        return None

class MockTokenStorage:
    """Mock token storage for testing"""
    
    def __init__(self):
        self.tokens = {}
    
    async def get_token(self, caller_did: str, target_did: str):
        """Mock token retrieval"""
        key = f"{caller_did}:{target_did}"
        return self.tokens.get(key)
    
    async def store_token(self, caller_did: str, target_did: str, token_data: Dict[str, Any]):
        """Mock token storage"""
        key = f"{caller_did}:{target_did}"
        self.tokens[key] = token_data

class MockHttpTransport:
    """Mock HTTP transport for testing"""
    
    def __init__(self, responses: Dict[str, Any] = None):
        self.responses = responses or {}
        self.requests = []
    
    async def send_request(self, method: str, url: str, headers: Dict[str, str], 
                          json_data: Dict[str, Any] = None):
        """Mock HTTP request"""
        self.requests.append({
            "method": method,
            "url": url, 
            "headers": headers,
            "json_data": json_data
        })
        
        # Return mock response
        response_key = f"{method}:{url}"
        if response_key in self.responses:
            response = self.responses[response_key]
            return response.get("status", 200), response.get("headers", {}), response.get("body", {})
        else:
            return 200, {}, {"success": True}

class MockSessionStorage:
    """Mock session storage for testing"""
    
    def __init__(self):
        self.sessions = {}
    
    async def create_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Mock session creation"""
        self.sessions[session_id] = session_data
        return True
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Mock session retrieval"""
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Mock session update"""
        if session_id in self.sessions:
            self.sessions[session_id] = session_data
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Mock session deletion"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Mock session cleanup"""
        return 0

# Test utilities
def assert_signature_valid(payload: bytes, signature: str, public_key_bytes: bytes):
    """Utility to verify signature in tests"""
    from anp_open_sdk.protocol.crypto import create_secp256k1_signer, SignatureEncoder
    
    signer = create_secp256k1_signer()
    encoder = SignatureEncoder()
    
    # Decode signature and convert to DER
    signature_rs = encoder.decode_base64url(signature)
    signature_der = encoder.rs_to_der_format(signature_rs)
    
    return signer.verify(payload, signature_der, public_key_bytes)

def create_test_wba_header(did: str, private_key_bytes: bytes, request_url: str = "http://localhost:9527/test",
                          target_did: str = None) -> str:
    """Create valid WBA Authorization header for testing"""
    import hashlib
    import secrets
    from datetime import datetime, timezone
    import jcs
    from anp_open_sdk.protocol.crypto import create_secp256k1_signer, SignatureEncoder
    
    # Build payload
    nonce = secrets.token_hex(16)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    data_to_sign = {
        "nonce": nonce,
        "timestamp": timestamp,
        "service": "localhost",
        "did": did,
    }
    if target_did:
        data_to_sign["resp_did"] = target_did
    
    # Create signature
    canonical_json = jcs.canonicalize(data_to_sign)
    content_hash = hashlib.sha256(canonical_json).digest()
    
    signer = create_secp256k1_signer()
    encoder = SignatureEncoder()
    
    signature_der = signer.sign(content_hash, private_key_bytes)
    signature_rs = encoder.der_to_rs_format(signature_der)
    signature = encoder.encode_base64url(signature_rs)
    
    # Build header
    parts = [
        f'DIDWba did="{did}"',
        f'nonce="{nonce}"',
        f'timestamp="{timestamp}"',
    ]
    if target_did:
        parts.append(f'resp_did="{target_did}"')
    
    parts.extend([
        'verification_method="#key1"',
        f'signature="{signature}"'
    ])
    
    return ", ".join(parts)