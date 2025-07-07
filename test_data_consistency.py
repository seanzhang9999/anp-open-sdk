#!/usr/bin/env python3
"""
测试签名和验证数据一致性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
import secrets
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

def test_direct_cryptography():
    """直接使用cryptography库测试签名验证"""
    
    print("=== 直接使用cryptography库测试 ===")
    
    # 生成测试用的私钥
    private_key_bytes = secrets.token_bytes(32)
    
    test_data = b"Direct cryptography test data"
    
    print(f"私钥长度: {len(private_key_bytes)} bytes")
    print(f"测试数据: {test_data}")
    
    try:
        # 1. 创建私钥对象
        private_key_obj = ec.derive_private_key(
            int.from_bytes(private_key_bytes, byteorder="big"), 
            ec.SECP256K1()
        )
        public_key_obj = private_key_obj.public_key()
        
        # 2. 获取公钥字节
        from cryptography.hazmat.primitives import serialization
        public_key_bytes = public_key_obj.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        print(f"公钥长度: {len(public_key_bytes)} bytes")
        print(f"公钥首字节: 0x{public_key_bytes[0]:02x}")
        
        # 3. 直接签名和验证（DER格式）
        print("\n--- 直接DER格式签名验证 ---")
        signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
        print(f"DER签名长度: {len(signature_der)} bytes")
        
        try:
            public_key_obj.verify(signature_der, test_data, ec.ECDSA(hashes.SHA256()))
            print("✓ 直接DER验证成功")
            der_success = True
        except Exception as e:
            print(f"✗ 直接DER验证失败: {e}")
            der_success = False
        
        # 4. 转换为R|S格式再转回DER验证
        print("\n--- R|S格式转换测试 ---")
        r, s = decode_dss_signature(signature_der)
        print(f"r: {r}")
        print(f"s: {s}")
        
        # 转换为固定长度字节
        r_bytes = r.to_bytes(32, byteorder='big')
        s_bytes = s.to_bytes(32, byteorder='big')
        rs_signature = r_bytes + s_bytes
        
        print(f"R|S签名长度: {len(rs_signature)} bytes")
        
        # 转回DER格式
        r_from_bytes = int.from_bytes(rs_signature[:32], 'big')
        s_from_bytes = int.from_bytes(rs_signature[32:], 'big')
        signature_der_reconstructed = encode_dss_signature(r_from_bytes, s_from_bytes)
        
        print(f"重构DER签名长度: {len(signature_der_reconstructed)} bytes")
        print(f"原始DER == 重构DER: {signature_der == signature_der_reconstructed}")
        
        try:
            public_key_obj.verify(signature_der_reconstructed, test_data, ec.ECDSA(hashes.SHA256()))
            print("✓ 重构DER验证成功")
            reconstructed_success = True
        except Exception as e:
            print(f"✗ 重构DER验证失败: {e}")
            reconstructed_success = False
        
        # 5. 测试我们的实现流程
        print("\n--- 测试我们的实现流程 ---")
        
        # 模拟我们的签名流程
        signature_der_our = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
        r_our, s_our = decode_dss_signature(signature_der_our)
        r_bytes_our = r_our.to_bytes(32, byteorder='big')
        s_bytes_our = s_our.to_bytes(32, byteorder='big')
        rs_signature_our = r_bytes_our + s_bytes_our
        
        # Base64编码（模拟传输）
        signature_b64_our = base64.b64encode(rs_signature_our).decode('utf-8')
        print(f"Base64签名: {signature_b64_our[:50]}...")
        
        # 模拟我们的验证流程
        signature_bytes_decoded = base64.b64decode(signature_b64_our + '=' * (-len(signature_b64_our) % 4))
        print(f"解码签名长度: {len(signature_bytes_decoded)} bytes")
        
        # 从公钥字节重新创建公钥对象（模拟验证时的情况）
        x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
        y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
        public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
        public_key_obj_reconstructed = public_numbers.public_key()
        
        # 将R|S转回DER
        r_length = len(signature_bytes_decoded) // 2
        r_verify = int.from_bytes(signature_bytes_decoded[:r_length], 'big')
        s_verify = int.from_bytes(signature_bytes_decoded[r_length:], 'big')
        signature_der_verify = encode_dss_signature(r_verify, s_verify)
        
        try:
            public_key_obj_reconstructed.verify(signature_der_verify, test_data, ec.ECDSA(hashes.SHA256()))
            print("✓ 完整流程验证成功")
            full_flow_success = True
        except Exception as e:
            print(f"✗ 完整流程验证失败: {e}")
            full_flow_success = False
        
        # 6. 结果总结
        print(f"\n--- 结果总结 ---")
        print(f"直接DER验证: {'成功' if der_success else '失败'}")
        print(f"重构DER验证: {'成功' if reconstructed_success else '失败'}")
        print(f"完整流程验证: {'成功' if full_flow_success else '失败'}")
        
        return der_success and reconstructed_success and full_flow_success
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_cryptography()
    print(f"\n{'🎉 测试成功！' if success else '❌ 测试失败！'}")
    sys.exit(0 if success else 1)
