#!/usr/bin/env python3
"""
最终调试 - 对比我们的实现和直接cryptography实现
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair, DIDCredentials, DIDDocument
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import secrets
import base64
import base58
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

def test_implementation_comparison():
    """对比我们的实现和直接cryptography实现"""
    
    print("=== 实现对比测试 ===")
    
    # 使用固定的私钥以便重现问题
    private_key_bytes = secrets.token_bytes(32)
    test_data = b"Implementation comparison test data"
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"测试数据: {test_data}")
    
    # 1. 使用我们的DIDKeyPair创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    print(f"\n--- DIDKeyPair信息 ---")
    print(f"公钥长度: {len(key_pair.public_key)} bytes")
    print(f"公钥: {key_pair.public_key.hex()}")
    
    # 2. 直接使用cryptography创建密钥对
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    public_key_obj = private_key_obj.public_key()
    
    from cryptography.hazmat.primitives import serialization
    public_key_bytes_direct = public_key_obj.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    print(f"\n--- 直接cryptography信息 ---")
    print(f"公钥长度: {len(public_key_bytes_direct)} bytes")
    print(f"公钥: {public_key_bytes_direct.hex()}")
    print(f"公钥一致: {key_pair.public_key == public_key_bytes_direct}")
    
    # 3. 使用我们的实现签名
    print(f"\n--- 我们的实现签名 ---")
    try:
        # 创建DID文档和凭证
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
        
        # 使用DIDCredentials签名
        signature_bytes_our = credentials.sign(test_data, "#test-key")
        print(f"✓ DIDCredentials签名成功，长度: {len(signature_bytes_our)} bytes")
        print(f"签名: {signature_bytes_our.hex()}")
        
        # 使用PureWBADIDSigner签名
        signer = PureWBADIDSigner()
        signature_b64_signer = signer.sign_payload(test_data, private_key_bytes)
        signature_bytes_signer = base64.b64decode(signature_b64_signer + '=' * (-len(signature_b64_signer) % 4))
        print(f"✓ PureWBADIDSigner签名成功，长度: {len(signature_bytes_signer)} bytes")
        print(f"签名: {signature_bytes_signer.hex()}")
        print(f"两种签名一致: {signature_bytes_our == signature_bytes_signer}")
        
    except Exception as e:
        print(f"✗ 我们的实现签名失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 直接cryptography签名
    print(f"\n--- 直接cryptography签名 ---")
    signature_der_direct = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    r_direct, s_direct = decode_dss_signature(signature_der_direct)
    r_bytes_direct = r_direct.to_bytes(32, byteorder='big')
    s_bytes_direct = s_direct.to_bytes(32, byteorder='big')
    signature_bytes_direct = r_bytes_direct + s_bytes_direct
    
    print(f"DER签名长度: {len(signature_der_direct)} bytes")
    print(f"R|S签名长度: {len(signature_bytes_direct)} bytes")
    print(f"R|S签名: {signature_bytes_direct.hex()}")
    
    # 5. 验证对比
    print(f"\n--- 验证对比 ---")
    
    # 使用我们的实现验证我们的签名
    signature_b64_our = base64.b64encode(signature_bytes_our).decode('utf-8')
    is_valid_our_our = signer.verify_signature(test_data, signature_b64_our, key_pair.public_key)
    print(f"我们的签名 -> 我们的验证: {is_valid_our_our}")
    
    # 使用我们的实现验证直接cryptography的签名
    signature_b64_direct = base64.b64encode(signature_bytes_direct).decode('utf-8')
    is_valid_direct_our = signer.verify_signature(test_data, signature_b64_direct, key_pair.public_key)
    print(f"直接签名 -> 我们的验证: {is_valid_direct_our}")
    
    # 使用直接cryptography验证我们的签名
    try:
        # 将我们的R|S签名转回DER
        r_our_verify = int.from_bytes(signature_bytes_our[:32], 'big')
        s_our_verify = int.from_bytes(signature_bytes_our[32:], 'big')
        signature_der_our_verify = encode_dss_signature(r_our_verify, s_our_verify)
        
        public_key_obj.verify(signature_der_our_verify, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"我们的签名 -> 直接验证: True")
        is_valid_our_direct = True
    except Exception as e:
        print(f"我们的签名 -> 直接验证: False ({e})")
        is_valid_our_direct = False
    
    # 使用直接cryptography验证直接cryptography的签名
    try:
        public_key_obj.verify(signature_der_direct, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"直接签名 -> 直接验证: True")
        is_valid_direct_direct = True
    except Exception as e:
        print(f"直接签名 -> 直接验证: False ({e})")
        is_valid_direct_direct = False
    
    # 6. 结果分析
    print(f"\n--- 结果分析 ---")
    print(f"公钥一致性: {key_pair.public_key == public_key_bytes_direct}")
    print(f"签名一致性: {signature_bytes_our == signature_bytes_signer}")
    print(f"我们的实现内部一致性: {is_valid_our_our}")
    print(f"与标准库的兼容性: {is_valid_our_direct and is_valid_direct_our}")
    print(f"标准库内部一致性: {is_valid_direct_direct}")
    
    success = (key_pair.public_key == public_key_bytes_direct and 
               signature_bytes_our == signature_bytes_signer and
               is_valid_our_our and 
               is_valid_our_direct and 
               is_valid_direct_our and 
               is_valid_direct_direct)
    
    return success

if __name__ == "__main__":
    success = test_implementation_comparison()
    print(f"\n{'🎉 所有测试通过！' if success else '❌ 存在问题需要修复！'}")
    sys.exit(0 if success else 1)
