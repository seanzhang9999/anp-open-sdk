#!/usr/bin/env python3
"""
调试签名验证问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import secrets
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

def debug_signature_formats():
    """调试不同签名格式"""
    
    print("=== 调试签名格式 ===")
    
    # 生成测试用的私钥
    private_key_bytes = secrets.token_bytes(32)
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    test_data = b"Debug test data"
    
    print(f"私钥长度: {len(private_key_bytes)} bytes")
    print(f"公钥长度: {len(key_pair.public_key)} bytes")
    print(f"公钥格式: {key_pair.public_key[:5].hex()}... (前5字节)")
    
    # 创建私钥对象
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    
    # 1. 原始DER格式签名
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    print(f"\n1. DER格式签名长度: {len(signature_der)} bytes")
    print(f"   DER签名: {signature_der[:10].hex()}...")
    
    # 2. 转换为R|S格式
    r, s = decode_dss_signature(signature_der)
    print(f"\n2. 解码后的 r: {r}")
    print(f"   解码后的 s: {s}")
    
    # 转换为固定长度字节
    r_bytes = r.to_bytes(32, byteorder='big')
    s_bytes = s.to_bytes(32, byteorder='big')
    rs_signature = r_bytes + s_bytes
    
    print(f"\n3. R|S格式签名长度: {len(rs_signature)} bytes")
    print(f"   R部分: {r_bytes[:5].hex()}...")
    print(f"   S部分: {s_bytes[:5].hex()}...")
    
    # 3. 验证DER格式
    try:
        # 从公钥字节创建公钥对象
        x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
        y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
        public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
        public_key_obj = public_numbers.public_key()
        
        public_key_obj.verify(signature_der, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"\n4. ✓ DER格式验证成功")
    except Exception as e:
        print(f"\n4. ✗ DER格式验证失败: {e}")
    
    # 4. 验证R|S转回DER格式
    try:
        # 将R|S转回DER格式
        r_from_bytes = int.from_bytes(rs_signature[:32], 'big')
        s_from_bytes = int.from_bytes(rs_signature[32:], 'big')
        signature_der_reconstructed = encode_dss_signature(r_from_bytes, s_from_bytes)
        
        public_key_obj.verify(signature_der_reconstructed, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"5. ✓ R|S转DER格式验证成功")
        
        # 检查重构的DER是否与原始DER相同
        if signature_der == signature_der_reconstructed:
            print(f"6. ✓ 重构的DER与原始DER完全相同")
        else:
            print(f"6. ⚠ 重构的DER与原始DER不同")
            print(f"   原始: {signature_der.hex()}")
            print(f"   重构: {signature_der_reconstructed.hex()}")
            
    except Exception as e:
        print(f"5. ✗ R|S转DER格式验证失败: {e}")
    
    # 5. 测试PureWBADIDSigner的验证逻辑
    print(f"\n=== 测试PureWBADIDSigner验证逻辑 ===")
    
    try:
        signer = PureWBADIDSigner()
        
        # 使用R|S格式签名进行验证
        rs_signature_b64 = base64.b64encode(rs_signature).decode('utf-8')
        print(f"R|S签名Base64: {rs_signature_b64[:50]}...")
        
        # 手动执行验证逻辑
        signature_bytes = base64.b64decode(rs_signature_b64 + '=' * (-len(rs_signature_b64) % 4))
        print(f"解码后签名长度: {len(signature_bytes)} bytes")
        
        # 检查公钥长度判断
        if len(key_pair.public_key) == 65 and key_pair.public_key[0] == 0x04:
            print("✓ 公钥识别为65字节非压缩格式")
            
            # 将 R|S 格式转换为 DER 格式
            r_length = len(signature_bytes) // 2
            r_verify = int.from_bytes(signature_bytes[:r_length], 'big')
            s_verify = int.from_bytes(signature_bytes[r_length:], 'big')
            signature_der_verify = encode_dss_signature(r_verify, s_verify)
            
            print(f"验证用DER签名长度: {len(signature_der_verify)} bytes")
            
            # 创建公钥对象进行验证
            x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
            y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            public_key_obj = public_numbers.public_key()
            
            public_key_obj.verify(signature_der_verify, test_data, ec.ECDSA(hashes.SHA256()))
            print("✓ 手动验证逻辑成功")
            
        else:
            print(f"✗ 公钥格式不匹配: 长度={len(key_pair.public_key)}, 首字节={key_pair.public_key[0]:02x}")
            
    except Exception as e:
        print(f"✗ 手动验证逻辑失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_signature_formats()
