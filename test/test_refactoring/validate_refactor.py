#!/usr/bin/env python3
"""
Simple Test Runner for Basic Validation

This script runs basic tests to validate the refactored architecture works.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_protocol_layer():
    """Test basic protocol layer functionality"""
    print("Testing Protocol Layer...")
    
    try:
        # Test crypto operations
        from anp_open_sdk.protocol.crypto import create_secp256k1_signer, SignatureEncoder
        
        signer = create_secp256k1_signer()
        encoder = SignatureEncoder()
        
        # Test basic signing
        test_payload = b"test message"
        test_private_key = bytes.fromhex("1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        
        signature_der = signer.sign(test_payload, test_private_key)
        print(f"✅ Crypto signing works (signature length: {len(signature_der)})")
        
        # Test DID methods registry
        from anp_open_sdk.protocol.did_methods import get_did_protocol, initialize_did_protocol_registry
        
        initialize_did_protocol_registry()
        wba_protocol = get_did_protocol("wba")
        
        if wba_protocol and wba_protocol.get_method_name() == "wba":
            print("✅ DID methods registry works")
        else:
            print("❌ DID methods registry failed")
            return False
            
    except Exception as e:
        print(f"❌ Protocol layer test failed: {e}")
        return False
    
    return True


def test_sdk_layer():
    """Test basic SDK layer functionality"""
    print("Testing SDK Layer...")
    
    try:
        # Test auth manager creation
        from anp_open_sdk.auth.auth_manager import create_auth_manager, AuthMethod
        
        auth_manager = create_auth_manager()
        supported_methods = auth_manager.get_supported_methods()
        
        if len(supported_methods) > 0:
            print(f"✅ Auth manager works (methods: {supported_methods})")
        else:
            print("❌ Auth manager has no methods")
            return False
        
        # Test header detection
        bearer_handler = auth_manager.get_handler_for_header("Bearer token123")
        did_handler = auth_manager.get_handler_for_header("DIDWba did=\"test\"")
        
        if bearer_handler and did_handler:
            print("✅ Authorization header detection works")
        else:
            print("❌ Authorization header detection failed")
            return False
            
    except Exception as e:
        print(f"❌ SDK layer test failed: {e}")
        return False
    
    return True


def test_framework_layer():
    """Test basic framework layer functionality"""
    print("Testing Framework Layer...")
    
    try:
        # Test adapter creation
        from anp_open_sdk_framework.adapters.did_auth_adapter import FrameworkDIDAuthAdapter
        
        adapter = FrameworkDIDAuthAdapter()
        
        if adapter.did_resolver and adapter.token_storage and adapter.http_transport:
            print("✅ Framework adapter creation works")
        else:
            print("❌ Framework adapter missing components")
            return False
            
    except Exception as e:
        print(f"❌ Framework layer test failed: {e}")
        return False
    
    return True


def test_integration():
    """Test basic integration between layers"""
    print("Testing Layer Integration...")
    
    try:
        # Test that SDK can use protocol layer
        from anp_open_sdk.auth.auth_manager import get_did_protocol_for_did
        from anp_open_sdk.protocol.did_methods import initialize_did_protocol_registry
        
        initialize_did_protocol_registry()
        protocol = get_did_protocol_for_did("did:wba:localhost:9527:user:test")
        
        if protocol and protocol.get_method_name() == "wba":
            print("✅ SDK to Protocol layer integration works")
        else:
            print("❌ SDK to Protocol layer integration failed")
            return False
        
        # Test that framework components can be injected into SDK
        from anp_open_sdk.auth.auth_manager import create_auth_manager
        from anp_open_sdk_framework.adapters.did_auth_adapter import LocalAgentTokenStorage
        
        storage = LocalAgentTokenStorage()
        manager = create_auth_manager(token_storage=storage)
        
        # Check that the storage was injected
        bearer_handler = manager.get_handler_for_header("Bearer test")
        if hasattr(bearer_handler, 'token_storage') and bearer_handler.token_storage is storage:
            print("✅ Framework to SDK injection works")
        else:
            print("❌ Framework to SDK injection failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    return True


def main():
    """Run all basic validation tests"""
    print("=" * 60)
    print("ANP SDK Refactoring - Basic Validation Tests")
    print("=" * 60)
    
    tests = [
        test_protocol_layer,
        test_sdk_layer, 
        test_framework_layer,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            print()
    
    print("=" * 60)
    print(f"Basic Validation Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All basic validation tests passed!")
        print("The refactored architecture appears to be working correctly.")
        return 0
    else:
        print("⚠️  Some basic validation tests failed.")
        print("Please check the implementation before running full tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())