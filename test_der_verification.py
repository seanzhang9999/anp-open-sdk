#!/usr/bin/env python3
"""
测试 DER 格式签名验证
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

def test_der_verification():
    """测试 DER 格式签名的生成和验证"""
    
    print("=== DER 格式签名验证测试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Implementation comparison test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 1. 直接使用 cryptography 生成和验证 DER 签名
    print(f"\n--- 直接 cryptography DER 签名验证 ---")
    
    # 生成签名
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    print(f"DER 签名长度: {len(signature_der)} bytes")
    print(f"DER 签名: {signature_der.hex()}")
    
    # 验证签名
    try:
        # 从公钥字节创建公钥对象
        x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
        y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
        public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
        public_key_obj = public_numbers.public_key()
        
        # 验证
        public_key_obj.verify(signature_der, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 直接验证成功")
        direct_success = True
    except Exception as e:
        print(f"✗ 直接验证失败: {e}")
        direct_success = False
    
    # 2. 测试 Base64 编解码
    print(f"\n--- Base64 编解码测试 ---")
    
    signature_b64 = base64.b64encode(signature_der).decode('utf-8')
    print(f"Base64 签名: {signature_b64}")
    
    signature_decoded = base64.b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
    print(f"解码后长度: {len(signature_decoded)} bytes")
    print(f"解码一致性: {signature_der == signature_decoded}")
    
    # 验证解码后的签名
    try:
        public_key_obj.verify(signature_decoded, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 解码后验证成功")
        decode_success = True
    except Exception as e:
        print(f"✗ 解码后验证失败: {e}")
        decode_success = False
    
    # 3. 测试我们的 PureWBADIDSigner
    print(f"\n--- PureWBADIDSigner 测试 ---")
    
    from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
    
    signer = PureWBADIDSigner()
    
    # 签名
    try:
        signature_b64_signer = signer.sign_payload(test_data, private_key_bytes)
        print(f"✓ PureWBADIDSigner 签名成功")
        print(f"签名: {signature_b64_signer}")
        
        # 检查签名是否与直接方法一致
        signature_bytes_signer = base64.b64decode(signature_b64_signer + '=' * (-len(signature_b64_signer) % 4))
        print(f"签名长度: {len(signature_bytes_signer)} bytes")
        
        signer_sign_success = True
    except Exception as e:
        print(f"✗ PureWBADIDSigner 签名失败: {e}")
        signer_sign_success = False
        return False
    
    # 验证
    try:
        is_valid = signer.verify_signature(test_data, signature_b64_signer, key_pair.public_key)
        print(f"PureWBADIDSigner 验证结果: {is_valid}")
        signer_verify_success = is_valid
    except Exception as e:
        print(f"✗ PureWBADIDSigner 验证异常: {e}")
        import traceback
        traceback.print_exc()
        signer_verify_success = False
    
    # 4. 交叉验证
    print(f"\n--- 交叉验证 ---")
    
    # 用直接方法验证 PureWBADIDSigner 的签名
    try:
        public_key_obj.verify(signature_bytes_signer, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 直接方法验证 PureWBADIDSigner 签名: 成功")
        cross_verify_1 = True
    except Exception as e:
        print(f"✗ 直接方法验证 PureWBADIDSigner 签名: 失败 ({e})")
        cross_verify_1 = False
    
    # 用 PureWBADIDSigner 验证直接方法的签名
    try:
        is_valid = signer.verify_signature(test_data, signature_b64, key_pair.public_key)
        print(f"PureWBADIDSigner 验证直接签名: {'成功' if is_valid else '失败'}")
        cross_verify_2 = is_valid
    except Exception as e:
        print(f"✗ PureWBADIDSigner 验证直接签名异常: {e}")
        cross_verify_2 = False
    
    # 5. 总结
    print(f"\n--- 总结 ---")
    print(f"直接 cryptography 验证: {direct_success}")
    print(f"Base64 编解码验证: {decode_success}")
    print(f"PureWBADIDSigner 签名: {signer_sign_success}")
    print(f"PureWBADIDSigner 验证: {signer_verify_success}")
    print(f"交叉验证1 (直接->PureWBA): {cross_verify_1}")
    print(f"交叉验证2 (PureWBA->直接): {cross_verify_2}")
    
    success = all([
        direct_success, decode_success, signer_sign_success, 
        signer_verify_success, cross_verify_1, cross_verify_2
    ])
    
    return success

if __name__ == "__main__":
    success = test_der_verification()
    print(f"\n{'🎉 所有测试通过！' if success else '❌ 存在问题需要修复！'}")
    sys.exit(0 if success else 1)
