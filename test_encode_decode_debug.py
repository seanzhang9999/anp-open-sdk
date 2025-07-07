#!/usr/bin/env python3
"""
调试 PureWBADIDSigner 的编码和解码过程
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

def debug_encode_decode():
    """调试编码和解码过程"""
    
    print("=== PureWBADIDSigner 编码解码调试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Encode decode debug test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 创建签名器
    signer = PureWBADIDSigner()
    
    # 步骤1：使用 PureWBADIDSigner 签名
    print(f"\n--- 步骤1: PureWBADIDSigner 签名 ---")
    
    signature_b64url = signer.sign_payload(test_data, private_key_bytes)
    print(f"签名结果: {signature_b64url}")
    
    # 步骤2：手动解码签名
    print(f"\n--- 步骤2: 手动解码签名 ---")
    
    signature_decoded = base64.urlsafe_b64decode(signature_b64url + '=' * (-len(signature_b64url) % 4))
    print(f"解码长度: {len(signature_decoded)} bytes")
    print(f"解码内容: {signature_decoded.hex()}")
    
    # 步骤3：手动验证签名
    print(f"\n--- 步骤3: 手动验证签名 ---")
    
    # 从 R|S 格式恢复 DER
    r_length = len(signature_decoded) // 2
    r = int.from_bytes(signature_decoded[:r_length], 'big')
    s = int.from_bytes(signature_decoded[r_length:], 'big')
    
    print(f"r: {r}")
    print(f"s: {s}")
    
    signature_der_recovered = encode_dss_signature(r, s)
    print(f"恢复的 DER 长度: {len(signature_der_recovered)} bytes")
    print(f"恢复的 DER: {signature_der_recovered.hex()}")
    
    # 创建公钥对象并验证
    x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
    y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
    public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
    public_key_obj = public_numbers.public_key()
    
    try:
        public_key_obj.verify(signature_der_recovered, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 手动验证成功")
        manual_verify_success = True
    except Exception as e:
        print(f"✗ 手动验证失败: {e}")
        manual_verify_success = False
    
    # 步骤4：使用 PureWBADIDSigner 验证
    print(f"\n--- 步骤4: PureWBADIDSigner 验证 ---")
    
    try:
        signer_verify_result = signer.verify_signature(test_data, signature_b64url, key_pair.public_key)
        print(f"PureWBADIDSigner 验证结果: {signer_verify_result}")
    except Exception as e:
        print(f"✗ PureWBADIDSigner 验证异常: {e}")
        import traceback
        traceback.print_exc()
        signer_verify_result = False
    
    # 步骤5：对比 encode_signature 方法
    print(f"\n--- 步骤5: 测试 encode_signature 方法 ---")
    
    # 直接生成 DER 签名
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der_direct = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    print(f"直接 DER 签名: {signature_der_direct.hex()}")
    
    # 使用 encode_signature 编码
    encoded_signature = signer.encode_signature(signature_der_direct)
    print(f"encode_signature 结果: {encoded_signature}")
    
    # 对比两种方法的结果
    print(f"签名方法一致性: {signature_b64url == encoded_signature}")
    
    # 步骤6：验证 encode_signature 的结果
    print(f"\n--- 步骤6: 验证 encode_signature 的结果 ---")
    
    try:
        encode_verify_result = signer.verify_signature(test_data, encoded_signature, key_pair.public_key)
        print(f"encode_signature 验证结果: {encode_verify_result}")
    except Exception as e:
        print(f"✗ encode_signature 验证异常: {e}")
        encode_verify_result = False
    
    # 总结
    print(f"\n--- 总结 ---")
    print(f"手动验证: {manual_verify_success}")
    print(f"PureWBADIDSigner 验证: {signer_verify_result}")
    print(f"encode_signature 验证: {encode_verify_result}")
    
    success = manual_verify_success and signer_verify_result and encode_verify_result
    return success

if __name__ == "__main__":
    success = debug_encode_decode()
    print(f"\n{'🎉 编码解码正常！' if success else '❌ 编码解码有问题！'}")
    sys.exit(0 if success else 1)
