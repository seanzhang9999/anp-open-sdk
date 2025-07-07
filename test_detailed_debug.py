#!/usr/bin/env python3
"""
详细调试签名验证问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import secrets
import base64
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_with_detailed_logging():
    """使用详细日志测试签名验证"""
    
    print("=== 详细调试测试 ===")
    
    # 生成测试用的私钥
    private_key_bytes = secrets.token_bytes(32)
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    test_data = b"Detailed debug test data"
    
    print(f"私钥长度: {len(private_key_bytes)} bytes")
    print(f"公钥长度: {len(key_pair.public_key)} bytes")
    print(f"公钥首字节: 0x{key_pair.public_key[0]:02x}")
    
    try:
        signer = PureWBADIDSigner()
        
        # 1. 签名
        print("\n--- 签名阶段 ---")
        signature_b64 = signer.sign_payload(test_data, private_key_bytes)
        print(f"✓ 签名成功: {signature_b64[:50]}...")
        
        # 解码签名查看长度
        signature_bytes = base64.b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
        print(f"签名字节长度: {len(signature_bytes)} bytes")
        
        # 2. 验证 - 手动步骤
        print("\n--- 验证阶段 (手动步骤) ---")
        
        # 检查公钥长度和格式
        print(f"公钥长度检查: {len(key_pair.public_key)} == 65? {len(key_pair.public_key) == 65}")
        print(f"公钥首字节检查: 0x{key_pair.public_key[0]:02x} == 0x04? {key_pair.public_key[0] == 0x04}")
        
        if len(key_pair.public_key) == 65 and key_pair.public_key[0] == 0x04:
            print("✓ 公钥格式正确，进入secp256k1验证分支")
            
            # 手动执行验证逻辑
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
            
            # 创建公钥对象
            x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
            y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            public_key_obj = public_numbers.public_key()
            print("✓ 公钥对象创建成功")
            
            # 将 R|S 格式转换为 DER 格式
            r_length = len(signature_bytes) // 2
            r = int.from_bytes(signature_bytes[:r_length], 'big')
            s = int.from_bytes(signature_bytes[r_length:], 'big')
            signature_der = encode_dss_signature(r, s)
            print(f"✓ 签名转换成功，DER长度: {len(signature_der)} bytes")
            
            # 验证
            try:
                public_key_obj.verify(signature_der, test_data, ec.ECDSA(hashes.SHA256()))
                print("✓ 手动验证成功")
                manual_verify_success = True
            except Exception as e:
                print(f"✗ 手动验证失败: {e}")
                manual_verify_success = False
        else:
            print("✗ 公钥格式不正确")
            manual_verify_success = False
        
        # 3. 使用PureWBADIDSigner验证
        print("\n--- PureWBADIDSigner验证 ---")
        is_valid = signer.verify_signature(test_data, signature_b64, key_pair.public_key)
        print(f"PureWBADIDSigner验证结果: {is_valid}")
        
        # 4. 结果对比
        print(f"\n--- 结果对比 ---")
        print(f"手动验证: {'成功' if manual_verify_success else '失败'}")
        print(f"PureWBADIDSigner验证: {'成功' if is_valid else '失败'}")
        
        if manual_verify_success and is_valid:
            print("🎉 所有验证都成功！")
            return True
        elif manual_verify_success and not is_valid:
            print("❌ 手动验证成功但PureWBADIDSigner失败，可能是实现问题")
            return False
        else:
            print("❌ 验证失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_detailed_logging()
    sys.exit(0 if success else 1)
