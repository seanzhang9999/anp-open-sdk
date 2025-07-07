#!/usr/bin/env python3
"""
测试签名和验证的兼容性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair, DIDCredentials, DIDDocument
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import secrets
import base64
import base58

def test_signature_compatibility():
    """测试签名和验证的兼容性"""
    
    # 生成测试用的私钥
    private_key_bytes = secrets.token_bytes(32)
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    # 测试数据
    test_data = b"Hello, World! This is a test message for signature verification."
    
    print("=== 签名兼容性测试 ===")
    print(f"私钥长度: {len(private_key_bytes)} bytes")
    print(f"公钥长度: {len(key_pair.public_key)} bytes")
    print(f"测试数据: {test_data}")
    
    # 创建一个简单的DID文档用于测试
    did_doc_dict = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": "did:test:123",
        "verificationMethod": [{
            "id": "did:test:123#test-key",
            "type": "EcdsaSecp256k1VerificationKey2019",
            "controller": "did:test:123",
            "publicKeyMultibase": "z" + base58.b58encode(key_pair.public_key).decode()
        }],
        "authentication": ["did:test:123#test-key"]
    }
    
    did_doc = DIDDocument(**did_doc_dict, raw_document=did_doc_dict)
    credentials = DIDCredentials(did="did:test:123", did_document=did_doc)
    credentials.add_key_pair(key_pair)
    
    # 使用 schemas.py 中的方法签名
    try:
        signature_bytes = credentials.sign(test_data, "#test-key")
        print(f"✓ schemas.py 签名成功，签名长度: {len(signature_bytes)} bytes")
        
        # 将签名转换为base64字符串（模拟传输过程）
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        print(f"✓ Base64签名: {signature_b64[:50]}...")
        
    except Exception as e:
        print(f"✗ schemas.py 签名失败: {e}")
        return False
    
    # 使用 implementation.py 中的方法验证
    try:
        signer = PureWBADIDSigner()
        is_valid = signer.verify_signature(test_data, signature_b64, key_pair.public_key)
        
        if is_valid:
            print("✓ implementation.py 验证成功")
            print("✓ 签名和验证兼容性测试通过！")
            return True
        else:
            print("✗ implementation.py 验证失败")
            return False
            
    except Exception as e:
        print(f"✗ implementation.py 验证异常: {e}")
        return False

def test_pure_signer_compatibility():
    """测试PureWBADIDSigner内部的签名和验证兼容性"""
    
    print("\n=== PureWBADIDSigner 内部兼容性测试 ===")
    
    # 生成测试用的私钥
    private_key_bytes = secrets.token_bytes(32)
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    test_data = b"Internal compatibility test data"
    
    try:
        signer = PureWBADIDSigner()
        
        # 使用PureWBADIDSigner签名
        signature_b64 = signer.sign_payload(test_data, private_key_bytes)
        print(f"✓ PureWBADIDSigner 签名成功: {signature_b64[:50]}...")
        
        # 使用PureWBADIDSigner验证
        is_valid = signer.verify_signature(test_data, signature_b64, key_pair.public_key)
        
        if is_valid:
            print("✓ PureWBADIDSigner 验证成功")
            print("✓ PureWBADIDSigner 内部兼容性测试通过！")
            return True
        else:
            print("✗ PureWBADIDSigner 验证失败")
            return False
            
    except Exception as e:
        print(f"✗ PureWBADIDSigner 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始签名兼容性测试...\n")
    
    # 测试1: schemas.py 和 implementation.py 之间的兼容性
    test1_result = test_signature_compatibility()
    
    # 测试2: PureWBADIDSigner 内部兼容性
    test2_result = test_pure_signer_compatibility()
    
    print(f"\n=== 测试结果 ===")
    print(f"跨模块兼容性测试: {'通过' if test1_result else '失败'}")
    print(f"内部兼容性测试: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！签名验证问题已修复。")
        sys.exit(0)
    else:
        print("❌ 测试失败，需要进一步调试。")
        sys.exit(1)
