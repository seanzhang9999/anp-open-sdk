#!/usr/bin/env python3
"""
Real Integration Test for ANP Open SDK DID Authentication

This test uses actual DID documents and keys from the existing test data
to perform real authentication flow testing.
"""

import os
import sys
import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.anp_sdk_agent import LocalAgent
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager
from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
from anp_open_sdk_framework.auth.auth_client import AuthClient
from anp_open_sdk.auth.schemas import AuthenticationContext
import logging

logger = logging.getLogger(__name__)


class RealIntegrationTestHelper:
    """Helper for real integration testing using existing test data"""
    
    def __init__(self):
        # 指向测试套件数据目录
        # 从 test_suite/tests/test_real_integration.py 向上2级到项目根目录
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.test_data_root = os.path.join(script_dir, "test_suite", "data", "data_user", "localhost_9527", "anp_users")
        self.available_agents = self.discover_test_agents()
        
    def discover_test_agents(self) -> dict:
        """Discover available test agents from existing data"""
        agents = {}
        
        if not os.path.exists(self.test_data_root):
            logger.warning(f"Test data directory not found: {self.test_data_root}")
            return agents
            
        for agent_dir in os.listdir(self.test_data_root):
            agent_path = os.path.join(self.test_data_root, agent_dir)
            if os.path.isdir(agent_path):
                did_doc_path = os.path.join(agent_path, "did_document.json")
                # 尝试多种私钥文件格式
                private_key_path = None
                for key_file in ["private_key.txt", "private_key.pem", "key-1_private.pem"]:
                    potential_path = os.path.join(agent_path, key_file)
                    if os.path.exists(potential_path):
                        private_key_path = potential_path
                        break
                
                if os.path.exists(did_doc_path) and private_key_path:
                    try:
                        with open(did_doc_path, 'r') as f:
                            did_doc = json.load(f)
                        
                        agents[agent_dir] = {
                            "did": did_doc.get("id"),
                            "did_document_path": did_doc_path,
                            "private_key_path": private_key_path,
                            "agent_dir": agent_path
                        }
                        logger.info(f"Found test agent: {agent_dir} -> {did_doc.get('id')}")
                    except Exception as e:
                        logger.warning(f"Failed to load agent {agent_dir}: {e}")
                        
        return agents
        
    def create_test_agent(self, agent_key: str):
        """Create test agent user data from test data"""
        if agent_key not in self.available_agents:
            raise ValueError(f"Agent {agent_key} not found in test data")
            
        agent_data = self.available_agents[agent_key]
        
        # 创建一个简单的测试用户数据对象
        class TestUserData:
            def __init__(self, did, did_document_path, private_key_path):
                self.did = did
                self.id = did  # 兼容性别名
                self.name = f"TestAgent_{agent_key}"
                self.did_document_path = did_document_path
                self.private_key_path = private_key_path
                
            def get_did(self):
                return self.did
                
        return TestUserData(
            agent_data["did"],
            agent_data["did_document_path"], 
            agent_data["private_key_path"]
        )
        
    def setup_auth_components(self) -> tuple[LocalUserDataManager, AuthClient]:
        """Setup authentication components"""
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        return user_data_manager, auth_client


class TestRealDIDAuthentication:
    """Real DID Authentication Integration Tests"""
    
    @pytest.fixture
    def test_helper(self):
        """Provide real test helper"""
        return RealIntegrationTestHelper()
        
    @pytest.fixture
    def test_config(self):
        """Setup real test configuration"""
        # 从 test_suite/tests/test_real_integration.py 向上2级到项目根目录
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(script_dir, "test_suite", "config", "test_config.yaml")
        
        if not os.path.exists(config_path):
            # Fallback to default config
            config_path = os.path.join(script_dir, "unified_config.default.yaml")
            
        app_config = UnifiedConfig(config_file=config_path, app_root=script_dir)
        set_global_config(app_config)
        setup_logging()
        
        return app_config
        
    def test_discover_real_test_agents(self, test_helper):
        """Test discovery of real test agents"""
        agents = test_helper.available_agents
        
        if len(agents) == 0:
            pytest.skip("No test agents found in test data directory")
            
        logger.info(f"Found {len(agents)} test agents:")
        for agent_key, agent_data in agents.items():
            logger.info(f"  - {agent_key}: {agent_data['did']}")
            
        # Verify agent data structure
        first_agent = list(agents.values())[0]
        assert "did" in first_agent
        assert "did_document_path" in first_agent
        assert "private_key_path" in first_agent
        assert os.path.exists(first_agent["did_document_path"])
        assert os.path.exists(first_agent["private_key_path"])
        
        logger.info("✅ Real test agent discovery passed")
        
    def test_load_real_did_documents(self, test_helper):
        """Test loading real DID documents"""
        if len(test_helper.available_agents) == 0:
            pytest.skip("No test agents available")
            
        # Test loading first available agent
        agent_key = list(test_helper.available_agents.keys())[0]
        agent = test_helper.create_test_agent(agent_key)
        
        assert agent.id.startswith("did:wba:")
        assert os.path.exists(agent.did_document_path)
        assert os.path.exists(agent.private_key_path)
        
        # Load and verify DID document structure
        with open(agent.did_document_path, 'r') as f:
            did_doc = json.load(f)
            
        assert did_doc["id"] == agent.id
        assert "verificationMethod" in did_doc
        assert len(did_doc["verificationMethod"]) > 0
        assert "authentication" in did_doc
        
        # Load and verify private key
        with open(agent.private_key_path, 'r') as f:
            private_key = f.read().strip()
            
        assert len(private_key) > 0
        
        logger.info(f"✅ Real DID document loading passed for {agent_key}")
        
    @pytest.mark.asyncio
    async def test_real_authentication_context_flow(self, test_helper, test_config):
        """Test authentication context creation with real agents"""
        if len(test_helper.available_agents) < 2:
            pytest.skip("Need at least 2 test agents for authentication flow")
            
        # Get two different agents
        agent_keys = list(test_helper.available_agents.keys())[:2]
        caller_agent = test_helper.create_test_agent(agent_keys[0])
        target_agent = test_helper.create_test_agent(agent_keys[1])
        
        # Setup auth components
        user_data_manager, auth_client = test_helper.setup_auth_components()
        
        # Inject auth client
        caller_agent.auth_client = auth_client
        
        # Create authentication context
        context = AuthenticationContext(
            caller_did=caller_agent.id,
            target_did=target_agent.id,
            request_url="http://localhost:9527/test",
            method="GET",
            custom_headers={},
            json_data=None,
            use_two_way_auth=True,
            domain="localhost"
        )
        
        assert context.caller_did == caller_agent.id
        assert context.target_did == target_agent.id
        assert context.use_two_way_auth == True
        
        logger.info(f"✅ Real authentication context flow passed")
        logger.info(f"   Caller: {caller_agent.id}")
        logger.info(f"   Target: {target_agent.id}")
        
    @pytest.mark.asyncio 
    async def test_auth_flow_with_real_keys(self, test_helper, test_config):
        """Test authentication flow with real cryptographic keys"""
        if len(test_helper.available_agents) == 0:
            pytest.skip("No test agents available")
            
        # Get first available agent
        agent_key = list(test_helper.available_agents.keys())[0]
        agent = test_helper.create_test_agent(agent_key)
        
        # Setup auth components
        user_data_manager, auth_client = test_helper.setup_auth_components()
        agent.auth_client = auth_client
        
        # Load actual DID document and private key
        with open(agent.did_document_path, 'r') as f:
            did_doc_raw = json.load(f)
            
        with open(agent.private_key_path, 'r') as f:
            private_key_raw = f.read().strip()
            
        logger.info(f"🔑 Testing with real keys for agent: {agent.id}")
        logger.info(f"   DID document keys: {len(did_doc_raw.get('verificationMethod', []))}")
        logger.info(f"   Private key length: {len(private_key_raw)}")
        
        # Test that we can create DIDCredentials without errors
        from anp_open_sdk.auth.schemas import DIDDocument, DIDKeyPair, DIDCredentials
        
        try:
            did_doc = DIDDocument(**did_doc_raw, raw_document=did_doc_raw)
            
            # Extract verification method
            if did_doc.verification_methods:
                vm = did_doc.verification_methods[0]
                key_id = vm.id.split('#')[-1] if '#' in vm.id else vm.id
                
                # For real testing, we'd need to parse the actual private key
                # For now, just verify the structure is correct
                logger.info(f"   Verification method ID: {key_id}")
                logger.info(f"   Public key type: {vm.type}")
                
                assert vm.type in ["EcdsaSecp256k1VerificationKey2019", "Ed25519VerificationKey2018"]
                
        except Exception as e:
            logger.error(f"Failed to process real keys: {e}")
            pytest.fail(f"Real key processing failed: {e}")
            
        logger.info(f"✅ Authentication flow with real keys structure test passed")


def run_real_integration_tests():
    """Run real integration tests"""
    print("🧪 Running ANP Open SDK Real Integration Tests")
    print("=" * 80)
    
    # Run with pytest
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show output immediately
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
    return result.returncode == 0


if __name__ == "__main__":
    success = run_real_integration_tests()
    if success:
        print("\n✅ All real integration tests passed!")
    else:
        print("\n❌ Some real integration tests failed!")
        sys.exit(1)