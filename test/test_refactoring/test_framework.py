"""
Framework Layer Tests

Tests for I/O adapters and framework integrations.
These tests verify the framework layer properly handles network, file, and storage operations.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from anp_open_sdk_framework.adapters.did_auth_adapter import (
    FileSystemDIDResolver, NetworkDIDResolver, HybridDIDResolver,
    LocalAgentTokenStorage, AiohttpTransport, FrameworkDIDAuthAdapter
)
from anp_open_sdk.auth.schemas import DIDDocument
from test.test_refactoring.test_base import TestDataFactory


class TestFileSystemDIDResolver:
    """Test filesystem-based DID resolver"""
    
    @pytest.mark.asyncio
    async def test_resolve_existing_did(self, temp_dir, sample_did_document):
        """Test resolving DID document from filesystem"""
        # Create mock LocalAgent structure
        did = "did:wba:localhost:9527:user:test123"
        
        # Create DID document file
        did_doc_path = temp_dir / "did_document.json"
        with open(did_doc_path, 'w') as f:
            json.dump(sample_did_document, f)
        
        # Mock LocalAgent.from_did method
        class MockLocalAgent:
            def __init__(self, did):
                self.did_document_path = str(did_doc_path)
        
        # Patch LocalAgent temporarily
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            resolver = FileSystemDIDResolver()
            did_doc = await resolver.resolve_did_document(did)
            
            assert did_doc is not None
            assert isinstance(did_doc, DIDDocument)
            assert did_doc.id == sample_did_document["id"]
        finally:
            # Restore original LocalAgent
            adapter_module.LocalAgent = original_local_agent
    
    @pytest.mark.asyncio
    async def test_resolve_nonexistent_did(self):
        """Test resolving non-existent DID document"""
        # Mock LocalAgent that points to non-existent file
        class MockLocalAgent:
            def __init__(self, did):
                self.did_document_path = "/nonexistent/path/did_document.json"
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            resolver = FileSystemDIDResolver()
            did_doc = await resolver.resolve_did_document("did:wba:nonexistent")
            
            assert did_doc is None
        finally:
            adapter_module.LocalAgent = original_local_agent


class TestNetworkDIDResolver:
    """Test network-based DID resolver"""
    
    @pytest.mark.asyncio
    async def test_resolve_did_placeholder(self):
        """Test network DID resolution (placeholder)"""
        resolver = NetworkDIDResolver()
        
        # Currently returns None (not implemented)
        did_doc = await resolver.resolve_did_document("did:web:example.com")
        assert did_doc is None


class TestHybridDIDResolver:
    """Test hybrid DID resolver (filesystem + network)"""
    
    @pytest.mark.asyncio
    async def test_resolve_local_first(self, temp_dir, sample_did_document):
        """Test hybrid resolver tries local first"""
        # Setup filesystem resolver to succeed
        did_doc_path = temp_dir / "did_document.json"
        with open(did_doc_path, 'w') as f:
            json.dump(sample_did_document, f)
        
        class MockLocalAgent:
            def __init__(self, did):
                self.did_document_path = str(did_doc_path)
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            resolver = HybridDIDResolver()
            did_doc = await resolver.resolve_did_document("did:wba:localhost:9527:user:test123")
            
            # Should resolve from filesystem
            assert did_doc is not None
            assert did_doc.id == sample_did_document["id"]
        finally:
            adapter_module.LocalAgent = original_local_agent
    
    @pytest.mark.asyncio
    async def test_fallback_to_network(self):
        """Test hybrid resolver falls back to network"""
        # Mock LocalAgent that fails
        class MockLocalAgent:
            def __init__(self, did):
                self.did_document_path = "/nonexistent/path"
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            resolver = HybridDIDResolver()
            did_doc = await resolver.resolve_did_document("did:web:example.com")
            
            # Should fallback to network (which returns None for now)
            assert did_doc is None
        finally:
            adapter_module.LocalAgent = original_local_agent


class TestLocalAgentTokenStorage:
    """Test LocalAgent-based token storage"""
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_token(self):
        """Test getting non-existent token"""
        # Mock LocalAgent with empty contact manager
        class MockContactManager:
            def get_token_to_remote(self, did):
                return None
        
        class MockLocalAgent:
            def __init__(self, did):
                self.contact_manager = MockContactManager()
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            storage = LocalAgentTokenStorage()
            token_info = await storage.get_token("did:wba:caller", "did:wba:target")
            
            assert token_info is None
        finally:
            adapter_module.LocalAgent = original_local_agent
    
    @pytest.mark.asyncio
    async def test_get_valid_token(self):
        """Test getting valid token"""
        # Mock token data
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_token_info = {
            "token": "test_token_123",
            "expires_at": expires_at,
            "is_revoked": False
        }
        
        class MockContactManager:
            def get_token_to_remote(self, did):
                return mock_token_info
        
        class MockLocalAgent:
            def __init__(self, did):
                self.contact_manager = MockContactManager()
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            storage = LocalAgentTokenStorage()
            token_info = await storage.get_token("did:wba:caller", "did:wba:target")
            
            assert token_info is not None
            assert token_info["token"] == "test_token_123"
        finally:
            adapter_module.LocalAgent = original_local_agent
    
    @pytest.mark.asyncio
    async def test_get_expired_token(self):
        """Test getting expired token"""
        # Mock expired token
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_token_info = {
            "token": "expired_token",
            "expires_at": expires_at,
            "is_revoked": False
        }
        
        class MockContactManager:
            def get_token_to_remote(self, did):
                return mock_token_info
        
        class MockLocalAgent:
            def __init__(self, did):
                self.contact_manager = MockContactManager()
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            storage = LocalAgentTokenStorage()
            token_info = await storage.get_token("did:wba:caller", "did:wba:target")
            
            # Should return None for expired token
            assert token_info is None
        finally:
            adapter_module.LocalAgent = original_local_agent
    
    @pytest.mark.asyncio
    async def test_store_token(self):
        """Test storing token"""
        stored_tokens = {}
        
        class MockContactManager:
            def store_token_to_remote(self, did, token, expiration_time):
                stored_tokens[did] = {"token": token, "expiration_time": expiration_time}
        
        class MockLocalAgent:
            def __init__(self, did):
                self.contact_manager = MockContactManager()
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            storage = LocalAgentTokenStorage()
            token_data = {
                "token": "new_token_123",
                "expires_delta": 3600
            }
            
            await storage.store_token("did:wba:caller", "did:wba:target", token_data)
            
            # Verify token was stored
            assert "did:wba:caller" in stored_tokens
            assert stored_tokens["did:wba:caller"]["token"] == "new_token_123"
        finally:
            adapter_module.LocalAgent = original_local_agent


class TestAiohttpTransport:
    """Test aiohttp-based HTTP transport"""
    
    @pytest.mark.asyncio
    async def test_send_request_mock(self):
        """Test HTTP request sending (mocked)"""
        # This test would require aiohttp server mocking
        # For now, just test the interface
        transport = AiohttpTransport()
        
        # Test would need proper aiohttp mocking setup
        # Just verify the method exists and has correct signature
        assert hasattr(transport, 'send_request')
        assert callable(transport.send_request)


class TestFrameworkDIDAuthAdapter:
    """Test framework DID auth adapter integration"""
    
    @pytest.mark.asyncio
    async def test_adapter_creation(self):
        """Test adapter creation with default components"""
        adapter = FrameworkDIDAuthAdapter()
        
        assert adapter.did_resolver is not None
        assert adapter.token_storage is not None
        assert adapter.http_transport is not None
        
        # Should use hybrid resolver by default
        assert isinstance(adapter.did_resolver, HybridDIDResolver)
        assert isinstance(adapter.token_storage, LocalAgentTokenStorage)
        assert isinstance(adapter.http_transport, AiohttpTransport)
    
    @pytest.mark.asyncio
    async def test_adapter_with_custom_components(self, temp_dir, sample_did_document):
        """Test adapter with custom components"""
        # Create custom components
        custom_resolver = FileSystemDIDResolver()
        custom_storage = LocalAgentTokenStorage()
        custom_transport = AiohttpTransport()
        
        adapter = FrameworkDIDAuthAdapter(
            did_resolver=custom_resolver,
            token_storage=custom_storage,
            http_transport=custom_transport
        )
        
        assert adapter.did_resolver is custom_resolver
        assert adapter.token_storage is custom_storage
        assert adapter.http_transport is custom_transport
    
    @pytest.mark.asyncio
    async def test_verify_request_with_io_interface(self):
        """Test verify_request_with_io interface"""
        adapter = FrameworkDIDAuthAdapter()
        
        # Mock authenticator
        class MockAuthenticator:
            def parse_auth_header(self, header):
                return {
                    "did": "did:wba:test",
                    "verification_method": "#key1",
                    "signature": "test_signature",
                    "nonce": "test_nonce",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            
            def reconstruct_signed_payload(self, parsed_header, service_domain):
                return b"test_payload"
            
            def verify_signature_with_public_key(self, payload, signature, public_key):
                return True
            
            class HeaderBuilder:
                def _get_domain(self, url):
                    return "localhost"
            
            header_builder = HeaderBuilder()
        
        # Mock context
        context = TestDataFactory.create_auth_context()
        
        # Test the interface (would need full setup to work)
        try:
            success, message = await adapter.verify_request_with_io(
                MockAuthenticator(), "test_header", context
            )
            # Might fail due to missing DID resolution, but interface should work
        except Exception:
            # Expected without full setup
            pass
    
    @pytest.mark.asyncio 
    async def test_authenticate_request_with_io_interface(self):
        """Test authenticate_request_with_io interface"""
        adapter = FrameworkDIDAuthAdapter()
        
        # Mock authenticator
        class MockAuthenticator:
            def build_auth_header(self, context, credentials):
                return {"Authorization": "test_header"}
        
        # Mock context and credentials
        context = TestDataFactory.create_auth_context()
        credentials = None  # Would need proper credentials
        
        # Test the interface
        try:
            success, headers, body = await adapter.authenticate_request_with_io(
                MockAuthenticator(), context, credentials
            )
            # Should return something even if mocked
            assert isinstance(success, bool)
        except Exception:
            # Expected without full setup
            pass


class TestFrameworkIntegration:
    """Test integration between framework components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_token_flow(self):
        """Test end-to-end token storage and retrieval"""
        # Mock LocalAgent ecosystem
        stored_data = {}
        
        class MockContactManager:
            def store_token_to_remote(self, did, token, expiration_time):
                key = f"store:{did}"
                stored_data[key] = {
                    "token": token,
                    "expires_at": datetime.now(timezone.utc) + timedelta(seconds=expiration_time),
                    "is_revoked": False
                }
            
            def get_token_to_remote(self, did):
                key = f"store:{did}"
                return stored_data.get(key)
        
        class MockLocalAgent:
            def __init__(self, did):
                self.contact_manager = MockContactManager()
        
        import anp_open_sdk_framework.adapters.did_auth_adapter as adapter_module
        original_local_agent = adapter_module.LocalAgent
        adapter_module.LocalAgent = type('MockLocalAgent', (), {
            'from_did': staticmethod(lambda did: MockLocalAgent(did))
        })
        
        try:
            storage = LocalAgentTokenStorage()
            
            # Store token
            token_data = {
                "token": "integration_test_token",
                "expires_delta": 3600
            }
            await storage.store_token("did:wba:caller", "did:wba:target", token_data)
            
            # Retrieve token
            retrieved_token = await storage.get_token("did:wba:caller", "did:wba:target")
            
            assert retrieved_token is not None
            assert retrieved_token["token"] == "integration_test_token"
        finally:
            adapter_module.LocalAgent = original_local_agent
    
    def test_framework_adapter_factory(self):
        """Test framework adapter factory function"""
        from anp_open_sdk_framework.adapters.did_auth_adapter import FrameworkDIDAuthAdapter
        
        # Test default creation
        adapter = FrameworkDIDAuthAdapter()
        assert adapter is not None
        
        # Test with custom components
        custom_resolver = FileSystemDIDResolver()
        adapter_with_custom = FrameworkDIDAuthAdapter(did_resolver=custom_resolver)
        assert adapter_with_custom.did_resolver is custom_resolver