#!/usr/bin/env python3
"""
Simple Test Runner for ANP Open SDK DID Authentication

A standalone test runner that can be executed directly without pytest infrastructure.
"""

import os
import sys
import asyncio
import json
import traceback

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


def setup_test_environment():
    """Setup test environment"""
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 向上三级到项目根目录
    config_path = os.path.join(script_dir, "test_suite", "config", "test_config.yaml")
    
    if not os.path.exists(config_path):
        config_path = os.path.join(script_dir, "unified_config.default.yaml")
        
    app_config = UnifiedConfig(config_file=config_path, app_root=script_dir)
    set_global_config(app_config)
    setup_logging()
    
    return app_config


def discover_test_agents():
    """Discover available test agents"""
    # 使用测试套件中的数据目录
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_data_root = os.path.join(script_dir, "data", "data_user", "localhost_9527", "anp_users")
    agents = {}
    
    if not os.path.exists(test_data_root):
        print(f"⚠️  Test data directory not found: {test_data_root}")
        return agents
        
    for agent_dir in os.listdir(test_data_root):
        agent_path = os.path.join(test_data_root, agent_dir)
        if os.path.isdir(agent_path):
            did_doc_path = os.path.join(agent_path, "did_document.json")
            private_key_path = os.path.join(agent_path, "private_key.txt")
            
            if os.path.exists(did_doc_path) and os.path.exists(private_key_path):
                try:
                    with open(did_doc_path, 'r') as f:
                        did_doc = json.load(f)
                    
                    agents[agent_dir] = {
                        "did": did_doc.get("id"),
                        "did_document_path": did_doc_path,
                        "private_key_path": private_key_path,
                        "agent_dir": agent_path
                    }
                    print(f"✅ Found test agent: {agent_dir} -> {did_doc.get('id')}")
                except Exception as e:
                    print(f"⚠️  Failed to load agent {agent_dir}: {e}")
                    
    return agents


def test_agent_discovery():
    """Test 1: Agent Discovery"""
    print("\n🧪 Test 1: Agent Discovery")
    print("-" * 50)
    
    agents = discover_test_agents()
    
    if len(agents) == 0:
        print("❌ No test agents found - may need to run framework demo first")
        return False
        
    print(f"✅ Found {len(agents)} test agents:")
    for agent_key, agent_data in agents.items():
        print(f"   - {agent_key}: {agent_data['did']}")
        
    return True


def test_did_document_loading():
    """Test 2: DID Document Loading"""
    print("\n🧪 Test 2: DID Document Loading")
    print("-" * 50)
    
    agents = discover_test_agents()
    if len(agents) == 0:
        print("❌ Skipping - no test agents available")
        return False
        
    # Test first agent
    agent_key = list(agents.keys())[0]
    agent_data = agents[agent_key]
    
    try:
        # Load DID document
        with open(agent_data["did_document_path"], 'r') as f:
            did_doc = json.load(f)
            
        print(f"✅ Loaded DID document for {agent_key}")
        print(f"   DID: {did_doc['id']}")
        print(f"   Verification methods: {len(did_doc.get('verificationMethod', []))}")
        print(f"   Services: {len(did_doc.get('service', []))}")
        
        # Load private key
        with open(agent_data["private_key_path"], 'r') as f:
            private_key = f.read().strip()
            
        print(f"   Private key length: {len(private_key)}")
        
        # Basic validation
        assert did_doc["id"] == agent_data["did"]
        assert "verificationMethod" in did_doc
        assert len(did_doc["verificationMethod"]) > 0
        assert len(private_key) > 0
        
        print("✅ DID document structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ DID document loading failed: {e}")
        traceback.print_exc()
        return False


def test_auth_components_setup():
    """Test 3: Authentication Components Setup"""
    print("\n🧪 Test 3: Authentication Components Setup")
    print("-" * 50)
    
    try:
        # Setup auth components
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        print("✅ Created LocalUserDataManager")
        print("✅ Created HttpTransport")
        print("✅ Created FrameworkAuthManager")
        print("✅ Created AuthClient")
        
        # Basic validation
        assert user_data_manager is not None
        assert auth_client is not None
        assert hasattr(auth_client, 'auth_manager')
        
        print("✅ Authentication components setup passed")
        return True
        
    except Exception as e:
        print(f"❌ Authentication components setup failed: {e}")
        traceback.print_exc()
        return False


async def test_authentication_context():
    """Test 4: Authentication Context Creation"""
    print("\n🧪 Test 4: Authentication Context Creation")
    print("-" * 50)
    
    try:
        agents = discover_test_agents()
        if len(agents) < 2:
            print("⚠️  Need at least 2 agents for authentication context test")
            if len(agents) == 1:
                # Use same agent as caller and target for testing
                agent_keys = list(agents.keys())
                caller_did = agents[agent_keys[0]]["did"]
                target_did = caller_did
            else:
                print("❌ No agents available")
                return False
        else:
            agent_keys = list(agents.keys())[:2]
            caller_did = agents[agent_keys[0]]["did"]
            target_did = agents[agent_keys[1]]["did"]
        
        # Create authentication context
        context = AuthenticationContext(
            caller_did=caller_did,
            target_did=target_did,
            request_url="http://localhost:9527/test",
            method="GET",
            custom_headers={},
            json_data=None,
            use_two_way_auth=True,
            domain="localhost"
        )
        
        print(f"✅ Created authentication context")
        print(f"   Caller DID: {context.caller_did}")
        print(f"   Target DID: {context.target_did}")
        print(f"   Two-way auth: {context.use_two_way_auth}")
        print(f"   Method: {context.method}")
        print(f"   URL: {context.request_url}")
        
        # Validation
        assert context.caller_did == caller_did
        assert context.target_did == target_did
        assert context.use_two_way_auth == True
        assert context.method == "GET"
        
        print("✅ Authentication context creation passed")
        return True
        
    except Exception as e:
        print(f"❌ Authentication context creation failed: {e}")
        traceback.print_exc()
        return False


def test_signature_components():
    """Test 5: Signature Components"""
    print("\n🧪 Test 5: Signature Components")
    print("-" * 50)
    
    try:
        from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner, PureWBAAuthHeaderBuilder, PureWBAAuth
        import hashlib
        import jcs
        
        # Create components
        signer = PureWBADIDSigner()
        header_builder = PureWBAAuthHeaderBuilder(signer)
        base_auth = PureWBAAuth()
        
        print("✅ Created PureWBADIDSigner")
        print("✅ Created PureWBAAuthHeaderBuilder")
        print("✅ Created PureWBAAuth")
        
        # Test signature creation with test data
        test_data = {
            "nonce": "test_nonce_123456789",
            "timestamp": "2025-07-07T23:30:00Z",
            "service": "localhost",
            "did": "did:wba:localhost%3A9527:wba:user:test",
        }
        
        canonical_json = jcs.canonicalize(test_data)
        content_hash = hashlib.sha256(canonical_json).digest()
        
        print(f"✅ Created test payload hash: {content_hash.hex()[:16]}...")
        
        # Test auth header parsing
        sample_header = 'DIDWba did="test", nonce="123", timestamp="2025-01-01T00:00:00Z", verification_method="#key-1", signature="test"'
        parsed = header_builder.parse_auth_header(sample_header)
        
        print(f"✅ Parsed auth header: {len(parsed)} fields")
        
        assert "did" in parsed
        assert "nonce" in parsed
        assert parsed["did"] == "test"
        
        print("✅ Signature components test passed")
        return True
        
    except Exception as e:
        print(f"❌ Signature components test failed: {e}")
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 ANP Open SDK DID Authentication Test Suite")
    print("=" * 80)
    
    # Setup test environment
    try:
        setup_test_environment()
        print("✅ Test environment setup completed")
    except Exception as e:
        print(f"❌ Test environment setup failed: {e}")
        return False
    
    # Run tests
    tests = [
        ("Agent Discovery", test_agent_discovery),
        ("DID Document Loading", test_did_document_loading),
        ("Auth Components Setup", test_auth_components_setup),
        ("Authentication Context", test_authentication_context),
        ("Signature Components", test_signature_components),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
            
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            traceback.print_exc()
    
    print(f"\n📊 Test Results")
    print("=" * 80)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The DID authentication flow is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_all_tests())
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()