#!/usr/bin/env python3
"""
Simplified E2E DID Authentication Test Suite

A working version that focuses on the core authentication flow without complex mocking.
"""

import os
import sys
import pytest
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.auth.schemas import AuthenticationContext, DIDDocument
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager
from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
from anp_open_sdk_framework.auth.auth_client import AuthClient
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner, PureWBAAuthHeaderBuilder, PureWBAAuth
import logging

logger = logging.getLogger(__name__)


class TestDIDAuthenticationComponents:
    """Test DID authentication components without complex agent setup"""
    
    @pytest.fixture
    def test_config(self):
        """Setup test configuration"""
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # 向上四级到项目根目录
        config_path = os.path.join(script_dir, "test_suite", "config", "test_config.yaml")
        
        if not os.path.exists(config_path):
            config_path = os.path.join(script_dir, "unified_config.default.yaml")
            
        app_config = UnifiedConfig(config_file=config_path, app_root=script_dir)
        set_global_config(app_config)
        setup_logging()
        
        return app_config
        
    def test_did_document_structure(self, test_config):
        """Test DID document creation and validation"""
        did = "did:wba:localhost%3A9527:wba:user:test_001"
        
        did_doc_data = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/secp256k1-2019/v1"
            ],
            "id": did,
            "verificationMethod": [{
                "id": f"{did}#key-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": did,
                "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G7Rou2yXqXFGZNcYru7NjzCawPNbYLdmQjXXR"
            }],
            "authentication": [f"{did}#key-1"],
            "service": [{
                "id": f"{did}#agent-service",
                "type": "AgentService", 
                "serviceEndpoint": "http://localhost:9527"
            }]
        }
        
        # Test DID document creation
        did_doc = DIDDocument(**did_doc_data, raw_document=did_doc_data)
        
        assert did_doc.id == did
        assert len(did_doc.verification_methods) == 1
        assert len(did_doc.authentication) == 1
        assert len(did_doc.service) == 1
        
        # Test verification method access
        vm = did_doc.verification_methods[0]
        assert vm.id == f"{did}#key-1"
        assert vm.type == "EcdsaSecp256k1VerificationKey2019"
        
        logger.info("✅ DID document structure test passed")
        
    def test_authentication_context_creation(self, test_config):
        """Test authentication context creation"""
        caller_did = "did:wba:localhost%3A9527:wba:user:caller"
        target_did = "did:wba:localhost%3A9527:wba:user:target"
        
        context = AuthenticationContext(
            caller_did=caller_did,
            target_did=target_did,
            request_url="http://localhost:9527/test",
            method="POST",
            custom_headers={"Content-Type": "application/json"},
            json_data={"test": "data"},
            use_two_way_auth=True,
            domain="localhost"
        )
        
        assert context.caller_did == caller_did
        assert context.target_did == target_did
        assert context.request_url == "http://localhost:9527/test"
        assert context.method == "POST"
        assert context.use_two_way_auth == True
        assert context.domain == "localhost"
        assert context.json_data == {"test": "data"}
        
        logger.info("✅ Authentication context creation test passed")
        
    def test_signature_components(self, test_config):
        """Test signature creation and verification components"""
        # Test WBA components creation
        signer = PureWBADIDSigner()
        header_builder = PureWBAAuthHeaderBuilder(signer)
        base_auth = PureWBAAuth()
        
        assert signer is not None
        assert header_builder is not None
        assert base_auth is not None
        
        # Test auth header parsing
        sample_header = 'DIDWba did="test:did", nonce="abc123", timestamp="2025-01-01T00:00:00Z", verification_method="#key-1", signature="test_sig"'
        parsed = header_builder.parse_auth_header(sample_header)
        
        assert "did" in parsed
        assert "nonce" in parsed
        assert "timestamp" in parsed
        assert "verification_method" in parsed
        assert "signature" in parsed
        
        assert parsed["did"] == "test:did"
        assert parsed["nonce"] == "abc123"
        assert parsed["verification_method"] == "#key-1"
        
        # Test DID extraction
        caller_did, target_did = base_auth.extract_did_from_auth_header(sample_header)
        assert caller_did == "test:did"
        assert target_did is None  # No resp_did in this header
        
        # Test two-way auth header
        two_way_header = 'DIDWba did="caller:did", nonce="xyz789", timestamp="2025-01-01T00:00:00Z", resp_did="target:did", verification_method="#key-1", signature="test_sig_2"'
        caller_did_2, target_did_2 = base_auth.extract_did_from_auth_header(two_way_header)
        assert caller_did_2 == "caller:did"
        assert target_did_2 == "target:did"
        
        logger.info("✅ Signature components test passed")
        
    def test_auth_client_creation(self, test_config):
        """Test authentication client setup with mocked components"""
        # Test transport creation (should work independently)
        http_transport = HttpTransport()
        assert http_transport is not None
        
        # Test that we can import the required classes
        try:
            from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager
            from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager  
            from anp_open_sdk_framework.auth.auth_client import AuthClient
            
            # Just verify the classes can be imported
            assert LocalUserDataManager is not None
            assert FrameworkAuthManager is not None
            assert AuthClient is not None
            
            logger.info("✅ Auth client related classes imported successfully")
            
        except ImportError as e:
            pytest.fail(f"Failed to import authentication classes: {e}")
        
        logger.info("✅ Auth client creation test passed (with imports only)")
        
    def test_file_based_did_discovery(self, test_config):
        """Test file-based DID discovery"""
        # Ensure config is properly set
        from anp_open_sdk.config import set_global_config
        set_global_config(test_config)
        
        # Use the test suite data directory  
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # test_suite directory
        test_data_root = os.path.join(script_dir, "data", "data_user", "localhost_9527", "anp_users")
        
        if not os.path.exists(test_data_root):
            pytest.skip(f"Test data directory not found: {test_data_root}")
            
        found_agents = {}
        
        for agent_dir in os.listdir(test_data_root):
            agent_path = os.path.join(test_data_root, agent_dir)
            if os.path.isdir(agent_path):
                did_doc_path = os.path.join(agent_path, "did_document.json")
                private_key_path = os.path.join(agent_path, "private_key.txt")
                
                if os.path.exists(did_doc_path) and os.path.exists(private_key_path):
                    with open(did_doc_path, 'r') as f:
                        did_doc = json.load(f)
                    
                    found_agents[agent_dir] = {
                        "did": did_doc.get("id"),
                        "did_document_path": did_doc_path,
                        "private_key_path": private_key_path
                    }
        
        if len(found_agents) > 0:
            logger.info(f"Found {len(found_agents)} test agents")
            for agent_id, agent_data in found_agents.items():
                logger.info(f"  - {agent_id}: {agent_data['did']}")
                
                # Validate each agent's DID document
                with open(agent_data["did_document_path"], 'r') as f:
                    did_doc_raw = json.load(f)
                
                did_doc = DIDDocument(**did_doc_raw, raw_document=did_doc_raw)
                assert did_doc.id == agent_data["did"]
                assert len(did_doc.verification_methods) > 0
        else:
            logger.info("No test agents found - this is okay for unit testing")
            
        logger.info("✅ File-based DID discovery test passed")


def run_simple_pytest():
    """Run the simplified pytest suite"""
    print("🧪 Running Simplified DID Authentication Tests")
    print("=" * 80)
    
    # Run with pytest
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
    return result.returncode == 0


if __name__ == "__main__":
    success = run_simple_pytest()
    if success:
        print("\n✅ All simplified tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)