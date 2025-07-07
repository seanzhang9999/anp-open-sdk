#!/usr/bin/env python3
"""
使用完全相同的数据测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair, DIDCredentials, DIDDocument
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import base64
import base58

def test_exact_same_data():
    """使用完全相同的数据进行测试"""
    
    print("=== 使用完全相同的数据测试 ===")
    
    # 使用之前测试中的确切数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Implementation comparison test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
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
    
    # 1. 使用DIDCredentials签名
    print(f"\n--- DIDCredentials签名 ---")
    try:
        signature_bytes_credentials = credentials.sign(test_data, "#test-key")
        print(f"✓ 签名成功: {signature_bytes_credentials.hex()}")
        signature_b64_credentials = base64.b64encode(signature_bytes_credentials).decode('utf-8')
        print(f"✓ Base64: {signature_b64_credentials}")
    except Exception as e:
        print(f"✗ 签名失败: {e}")
        return False
    
    # 2. 使用PureWBADIDSigner签名
    print(f"\n--- PureWBADIDSigner签名 ---")
    try:
        signer = PureWBADIDSigner()
        signature_b64_signer = signer.sign_payload(test_data, private_key_bytes)
        signature_bytes_signer = base64.b64decode(signature_b64_signer + '=' * (-len(signature_b64_signer) % 4))
        print(f"✓ 签名成功: {signature_bytes_signer.hex()}")
        print(f"✓ Base64: {signature_b64_signer}")
        print(f"✓ 两种签名一致: {signature_bytes_credentials == signature_bytes_signer}")
    except Exception as e:
        print(f"✗ 签名失败: {e}")
        return False
    
    # 3. 验证测试
    print(f"\n--- 验证测试 ---")
    
    # 测试1: 使用PureWBADIDSigner验证DIDCredentials的签名
    print("测试1: PureWBADIDSigner验证DIDCredentials签名")
    try:
        result1 = signer.verify_signature(test_data, signature_b64_credentials, key_pair.public_key)
        print(f"结果: {result1}")
    except Exception as e:
        print(f"异常: {e}")
        result1 = False
    
    # 测试2: 使用PureWBADIDSigner验证PureWBADIDSigner的签名
    print("测试2: PureWBADIDSigner验证PureWBADIDSigner签名")
    try:
        result2 = signer.verify_signature(test_data, signature_b64_signer, key_pair.public_key)
        print(f"结果: {result2}")
    except Exception as e:
        print(f"异常: {e}")
        result2 = False
    
    # 测试3: 手动验证DIDCredentials的签名
    print("测试3: 手动验证DIDCredentials签名")
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
        
        signature_bytes_decoded = base64.b64decode(signature_b64_credentials + '=' * (-len(signature_b64_credentials) % 4))
        
        # 创建公钥对象
        x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
        y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
        public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
        public_key_obj = public_numbers.public_key()
        
        # 转换签名格式
        r_length = len(signature_bytes_decoded) // 2
        r = int.from_bytes(signature_bytes_decoded[:r_length], 'big')
        s = int.from_bytes(signature_bytes_decoded[r_length:], 'big')
        signature_der = encode_dss_signature(r, s)
        
        # 验证
        public_key_obj.verify(signature_der, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"结果: True")
        result3 = True
    except Exception as e:
        print(f"结果: False ({e})")
        result3 = False
    
    # 4. 结果总结
    print(f"\n--- 结果总结 ---")
    print(f"测试1 (PureWBADIDSigner验证DIDCredentials签名): {result1}")
    print(f"测试2 (PureWBADIDSigner验证PureWBADIDSigner签名): {result2}")
    print(f"测试3 (手动验证DIDCredentials签名): {result3}")
    
    # 如果手动验证成功但PureWBADIDSigner验证失败，说明PureWBADIDSigner有问题
    if result3 and not result1:
        print(f"\n⚠️  关键发现：手动验证成功但PureWBADIDSigner验证失败！")
        print(f"这说明PureWBADIDSigner.verify_signature方法存在问题。")
        
        # 让我们直接调用verify_signature并捕获详细异常
        print(f"\n--- 详细异常调试 ---")
        try:
            # 临时修改异常处理，让异常抛出而不是被捕获
            import logging
            logging.basicConfig(level=logging.DEBUG)
            
            # 直接调用，不让异常被捕获
            print("直接调用verify_signature...")
            result_direct = signer.verify_signature(test_data, signature_b64_credentials, key_pair.public_key)
            print(f"直接调用结果: {result_direct}")
            
        except Exception as e:
            print(f"直接调用异常: {e}")
            import traceback
            traceback.print_exc()
    
    success = result1 and result2 and result3
    return success

if __name__ == "__main__":
    success = test_exact_same_data()
    print(f"\n{'🎉 所有测试通过！' if success else '❌ 存在问题需要修复！'}")
    sys.exit(0 if success else 1)
