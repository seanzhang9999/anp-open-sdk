#!/usr/bin/env python3
"""
测试 PureWBADIDSigner 的自验证能力
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner

def test_signer_self_verification():
    """测试签名器的自验证能力"""
    
    print("=== PureWBADIDSigner 自验证测试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Self verification test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 创建签名器
    signer = PureWBADIDSigner()
    
    # 进行多次签名和验证测试
    for i in range(3):
        print(f"\n--- 测试轮次 {i+1} ---")
        
        try:
            # 签名
            signature = signer.sign_payload(test_data, private_key_bytes)
            print(f"✓ 签名成功: {signature}")
            
            # 验证
            is_valid = signer.verify_signature(test_data, signature, key_pair.public_key)
            print(f"验证结果: {is_valid}")
            
            if not is_valid:
                print(f"❌ 第 {i+1} 轮验证失败！")
                return False
            else:
                print(f"✓ 第 {i+1} 轮验证成功！")
                
        except Exception as e:
            print(f"❌ 第 {i+1} 轮出现异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 测试不同数据的签名验证
    print(f"\n--- 测试不同数据 ---")
    
    different_data = b"Different test data"
    try:
        signature1 = signer.sign_payload(test_data, private_key_bytes)
        signature2 = signer.sign_payload(different_data, private_key_bytes)
        
        print(f"原始数据签名: {signature1}")
        print(f"不同数据签名: {signature2}")
        
        # 正确验证
        valid1 = signer.verify_signature(test_data, signature1, key_pair.public_key)
        valid2 = signer.verify_signature(different_data, signature2, key_pair.public_key)
        
        # 错误验证（交叉验证）
        invalid1 = signer.verify_signature(test_data, signature2, key_pair.public_key)
        invalid2 = signer.verify_signature(different_data, signature1, key_pair.public_key)
        
        print(f"正确验证1: {valid1}")
        print(f"正确验证2: {valid2}")
        print(f"错误验证1: {invalid1}")
        print(f"错误验证2: {invalid2}")
        
        if valid1 and valid2 and not invalid1 and not invalid2:
            print("✓ 不同数据测试通过！")
            return True
        else:
            print("❌ 不同数据测试失败！")
            return False
            
    except Exception as e:
        print(f"❌ 不同数据测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_signer_self_verification()
    print(f"\n{'🎉 PureWBADIDSigner 自验证正常！' if success else '❌ PureWBADIDSigner 自验证有问题！'}")
    sys.exit(0 if success else 1)
