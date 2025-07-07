#!/usr/bin/env python3
"""
专门调试验证逻辑
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

def debug_verify_logic():
    """调试验证逻辑的每一步"""
    
    print("=== 调试验证逻辑 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Implementation comparison test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    # 创建签名
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(signature_der)
    r_bytes = r.to_bytes(32, byteorder='big')
    s_bytes = s.to_bytes(32, byteorder='big')
    signature_bytes = r_bytes + s_bytes
    
    print(f"签名: {signature_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    
    # 手动执行验证逻辑，不捕获异常
    print(f"\n--- 手动验证逻辑 (不捕获异常) ---")
    
    try:
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        signature_bytes_decoded = base64.b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
        
        print(f"1. Base64编解码: ✓")
        print(f"   原始长度: {len(signature_bytes)}, 解码长度: {len(signature_bytes_decoded)}")
        print(f"   数据一致: {signature_bytes == signature_bytes_decoded}")
        
        # 处理payload
        if isinstance(test_data, str):
            payload_bytes = test_data.encode('utf-8')
        else:
            payload_bytes = test_data
        print(f"2. Payload处理: ✓")
        
        # 检查公钥长度
        public_key_bytes = key_pair.public_key
        print(f"3. 公钥长度检查: {len(public_key_bytes)} bytes")
        
        if len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
            print(f"4. 公钥格式检查: ✓ (65字节非压缩格式)")
            
            # 创建公钥对象
            x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
            y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            public_key_obj = public_numbers.public_key()
            print(f"5. 公钥对象创建: ✓")
            
            # 将 R|S 格式转换为 DER 格式
            r_length = len(signature_bytes_decoded) // 2
            r_verify = int.from_bytes(signature_bytes_decoded[:r_length], 'big')
            s_verify = int.from_bytes(signature_bytes_decoded[r_length:], 'big')
            signature_der_verify = encode_dss_signature(r_verify, s_verify)
            print(f"6. 签名格式转换: ✓")
            print(f"   R: {r_verify}")
            print(f"   S: {s_verify}")
            print(f"   DER长度: {len(signature_der_verify)}")
            
            # 验证签名
            print(f"7. 开始验证签名...")
            public_key_obj.verify(signature_der_verify, payload_bytes, ec.ECDSA(hashes.SHA256()))
            print(f"8. 验证成功: ✓")
            
            return True
            
        else:
            print(f"✗ 公钥格式不正确: 长度={len(public_key_bytes)}, 首字节={public_key_bytes[0]:02x}")
            return False
            
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        print(f"异常类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_purewba_verify_with_debug():
    """测试PureWBADIDSigner的验证，添加调试信息"""
    
    print(f"\n=== PureWBADIDSigner验证调试 ===")
    
    # 修改PureWBADIDSigner的verify_signature方法，临时添加调试信息
    from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
    
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Implementation comparison test data"
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    # 创建签名
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(signature_der)
    r_bytes = r.to_bytes(32, byteorder='big')
    s_bytes = s.to_bytes(32, byteorder='big')
    signature_bytes = r_bytes + s_bytes
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
    
    # 创建signer并尝试验证
    signer = PureWBADIDSigner()
    
    # 手动复制verify_signature的逻辑，但添加详细调试
    print("开始手动执行PureWBADIDSigner.verify_signature逻辑...")
    
    try:
        signature_bytes_decoded = base64.b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
        print(f"✓ Base64解码成功")

        # 处理payload，支持字符串和字节类型
        if isinstance(test_data, str):
            payload_bytes = test_data.encode('utf-8')
        else:
            payload_bytes = test_data
        print(f"✓ Payload处理完成")

        # 根据公钥长度判断密钥类型
        public_key_bytes = key_pair.public_key
        if len(public_key_bytes) == 32:
            print("进入Ed25519分支")
        elif len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
            print("✓ 进入secp256k1非压缩公钥分支")
            
            # 从非压缩格式创建公钥对象
            x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
            y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            public_key_obj = public_numbers.public_key()
            print(f"✓ 公钥对象创建成功")

            # 将 R|S 格式转换为 DER 格式
            r_length = len(signature_bytes_decoded) // 2
            r_verify = int.from_bytes(signature_bytes_decoded[:r_length], 'big')
            s_verify = int.from_bytes(signature_bytes_decoded[r_length:], 'big')
            signature_der_verify = encode_dss_signature(r_verify, s_verify)
            print(f"✓ 签名转换完成，DER长度: {len(signature_der_verify)}")

            print("开始调用public_key_obj.verify...")
            public_key_obj.verify(signature_der_verify, payload_bytes, ec.ECDSA(hashes.SHA256()))
            print("✓ 验证成功！")
            return True
        elif len(public_key_bytes) == 33:
            print("进入secp256k1压缩公钥分支")
        else:
            print(f"✗ 不支持的公钥长度: {len(public_key_bytes)} bytes")
            return False

    except Exception as e:
        print(f"✗ 手动验证失败: {e}")
        print(f"异常类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始调试验证逻辑...")
    
    success1 = debug_verify_logic()
    success2 = test_purewba_verify_with_debug()
    
    print(f"\n--- 总结 ---")
    print(f"手动验证逻辑: {'成功' if success1 else '失败'}")
    print(f"PureWBADIDSigner验证: {'成功' if success2 else '失败'}")
    
    sys.exit(0 if success1 and success2 else 1)
