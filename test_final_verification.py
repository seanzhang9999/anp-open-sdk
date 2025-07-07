#!/usr/bin/env python3
"""
最终验证测试 - 使用相同的签名进行验证
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

def test_final_verification():
    """最终验证测试"""
    
    print("=== 最终验证测试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Final verification test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 创建签名器
    signer = PureWBADIDSigner()
    
    # 方法1：使用 encode_signature 方法（已知可以工作）
    print(f"\n--- 方法1: 使用 encode_signature ---")
    
    # 直接生成 DER 签名
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    print(f"DER 签名: {signature_der.hex()}")
    
    # 使用 encode_signature 编码
    encoded_signature = signer.encode_signature(signature_der)
    print(f"编码签名: {encoded_signature}")
    
    # 验证编码的签名
    verify_result_1 = signer.verify_signature(test_data, encoded_signature, key_pair.public_key)
    print(f"验证结果: {verify_result_1}")
    
    # 方法2：修复 sign_payload 使其使用相同的逻辑
    print(f"\n--- 方法2: 直接测试 sign_payload 和 verify_signature 的一致性 ---")
    
    # 多次测试以确保一致性
    success_count = 0
    total_tests = 5
    
    for i in range(total_tests):
        print(f"\n测试 {i+1}:")
        
        # 使用 sign_payload 签名
        signature = signer.sign_payload(test_data, private_key_bytes)
        print(f"签名: {signature}")
        
        # 验证签名
        is_valid = signer.verify_signature(test_data, signature, key_pair.public_key)
        print(f"验证结果: {is_valid}")
        
        if is_valid:
            success_count += 1
            print(f"✓ 测试 {i+1} 成功")
        else:
            print(f"✗ 测试 {i+1} 失败")
    
    print(f"\n--- 总结 ---")
    print(f"encode_signature 方法: {'✓ 正常' if verify_result_1 else '✗ 异常'}")
    print(f"sign_payload 一致性: {success_count}/{total_tests} 成功")
    
    # 如果所有测试都成功，说明修复有效
    all_success = verify_result_1 and success_count == total_tests
    
    if all_success:
        print(f"🎉 所有测试通过！PureWBADIDSigner 工作正常！")
        
        # 额外测试：验证错误的签名会被拒绝
        print(f"\n--- 额外测试: 错误签名验证 ---")
        wrong_signature = "invalid_signature_test"
        wrong_result = signer.verify_signature(test_data, wrong_signature, key_pair.public_key)
        print(f"错误签名验证结果: {wrong_result} (应该是 False)")
        
        if not wrong_result:
            print(f"✓ 错误签名正确被拒绝")
            return True
        else:
            print(f"✗ 错误签名未被拒绝")
            return False
    else:
        print(f"❌ 测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = test_final_verification()
    sys.exit(0 if success else 1)
