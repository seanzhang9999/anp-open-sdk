#!/usr/bin/env python3
"""
调试签名缓存问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anp_open_sdk'))

from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
import base64

def test_signature_cache():
    """测试签名缓存问题"""
    
    print("=== 签名缓存调试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Cache debug test data"
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"测试数据: {test_data}")
    
    # 创建签名器
    signer = PureWBADIDSigner()
    
    # 多次调用 sign_payload，检查是否有缓存
    signatures = []
    for i in range(5):
        print(f"\n--- 签名 {i+1} ---")
        
        signature = signer.sign_payload(test_data, private_key_bytes)
        print(f"签名: {signature}")
        
        # 解码签名查看内容
        signature_decoded = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
        print(f"解码长度: {len(signature_decoded)} bytes")
        print(f"解码内容: {signature_decoded.hex()}")
        
        signatures.append(signature)
    
    # 检查签名是否相同
    print(f"\n--- 签名比较 ---")
    all_same = all(sig == signatures[0] for sig in signatures)
    print(f"所有签名相同: {all_same}")
    
    if all_same:
        print("❌ 发现缓存问题！ECDSA 签名不应该相同")
        
        # 检查是否是 Ed25519 路径的问题
        print(f"\n--- 检查 Ed25519 路径 ---")
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            ed25519_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            print("✓ Ed25519 私钥创建成功 - 这可能是问题所在！")
            
            # 测试 Ed25519 签名
            ed25519_sig1 = ed25519_key.sign(test_data)
            ed25519_sig2 = ed25519_key.sign(test_data)
            print(f"Ed25519 签名1: {ed25519_sig1.hex()}")
            print(f"Ed25519 签名2: {ed25519_sig2.hex()}")
            print(f"Ed25519 签名相同: {ed25519_sig1 == ed25519_sig2}")
            
        except Exception as e:
            print(f"✗ Ed25519 私钥创建失败: {e}")
    else:
        print("✓ 签名正常，每次都不同")
    
    return not all_same

if __name__ == "__main__":
    success = test_signature_cache()
    print(f"\n{'🎉 签名正常！' if success else '❌ 发现缓存问题！'}")
    sys.exit(0 if success else 1)
