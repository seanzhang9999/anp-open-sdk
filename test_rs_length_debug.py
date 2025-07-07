#!/usr/bin/env python3
"""
调试 R|S 长度问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth.schemas import DIDKeyPair
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature, encode_dss_signature

def debug_rs_length():
    """调试 R|S 长度问题"""
    
    print("=== R|S 长度调试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"RS length debug test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 创建私钥对象
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    
    # 进行多次签名，观察 R|S 长度变化
    for i in range(5):
        print(f"\n--- 签名 {i+1} ---")
        
        # 生成 DER 签名
        signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
        print(f"DER 签名长度: {len(signature_der)} bytes")
        print(f"DER 签名: {signature_der.hex()}")
        
        # 解析 DER 得到 R, S
        r, s = decode_dss_signature(signature_der)
        print(f"r: {r}")
        print(f"s: {s}")
        
        # 转换为字节（使用固定长度）
        r_bytes_fixed = r.to_bytes(32, byteorder='big')
        s_bytes_fixed = s.to_bytes(32, byteorder='big')
        signature_rs_fixed = r_bytes_fixed + s_bytes_fixed
        
        print(f"r_bytes (32字节): {r_bytes_fixed.hex()}")
        print(f"s_bytes (32字节): {s_bytes_fixed.hex()}")
        print(f"R|S (64字节): {signature_rs_fixed.hex()}")
        
        # 转换为字节（使用变长）
        r_bytes_var = r.to_bytes((r.bit_length() + 7) // 8, byteorder='big')
        s_bytes_var = s.to_bytes((s.bit_length() + 7) // 8, byteorder='big')
        signature_rs_var = r_bytes_var + s_bytes_var
        
        print(f"r_bytes (变长{len(r_bytes_var)}字节): {r_bytes_var.hex()}")
        print(f"s_bytes (变长{len(s_bytes_var)}字节): {s_bytes_var.hex()}")
        print(f"R|S (变长{len(signature_rs_var)}字节): {signature_rs_var.hex()}")
        
        # 测试验证（固定长度）
        print(f"\n--- 验证测试（固定长度） ---")
        
        # 从固定长度 R|S 恢复 DER
        r_recovered_fixed = int.from_bytes(signature_rs_fixed[:32], 'big')
        s_recovered_fixed = int.from_bytes(signature_rs_fixed[32:], 'big')
        signature_der_recovered_fixed = encode_dss_signature(r_recovered_fixed, s_recovered_fixed)
        
        print(f"恢复的 r: {r_recovered_fixed}")
        print(f"恢复的 s: {s_recovered_fixed}")
        print(f"r 一致性: {r == r_recovered_fixed}")
        print(f"s 一致性: {s == s_recovered_fixed}")
        print(f"DER 一致性: {signature_der == signature_der_recovered_fixed}")
        
        # 验证恢复的签名
        public_key_obj = private_key_obj.public_key()
        try:
            public_key_obj.verify(signature_der_recovered_fixed, test_data, ec.ECDSA(hashes.SHA256()))
            print(f"✓ 固定长度验证成功")
        except Exception as e:
            print(f"✗ 固定长度验证失败: {e}")
        
        # 测试验证（变长）
        print(f"\n--- 验证测试（变长） ---")
        
        # 从变长 R|S 恢复 DER（这里需要知道分割点）
        if len(signature_rs_var) % 2 == 0:
            mid_point = len(signature_rs_var) // 2
            r_recovered_var = int.from_bytes(signature_rs_var[:mid_point], 'big')
            s_recovered_var = int.from_bytes(signature_rs_var[mid_point:], 'big')
            
            print(f"恢复的 r: {r_recovered_var}")
            print(f"恢复的 s: {s_recovered_var}")
            print(f"r 一致性: {r == r_recovered_var}")
            print(f"s 一致性: {s == s_recovered_var}")
            
            if r == r_recovered_var and s == s_recovered_var:
                signature_der_recovered_var = encode_dss_signature(r_recovered_var, s_recovered_var)
                try:
                    public_key_obj.verify(signature_der_recovered_var, test_data, ec.ECDSA(hashes.SHA256()))
                    print(f"✓ 变长验证成功")
                except Exception as e:
                    print(f"✗ 变长验证失败: {e}")
            else:
                print(f"✗ 变长 R|S 恢复失败")
        else:
            print(f"✗ 变长 R|S 长度为奇数，无法平分")
        
        print(f"=" * 50)

if __name__ == "__main__":
    debug_rs_length()
