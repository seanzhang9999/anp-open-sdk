#!/usr/bin/env python3
"""
详细调试签名问题
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

def debug_signature_process():
    """详细调试签名过程"""
    
    print("=== 详细签名调试 ===")
    
    # 使用固定的私钥和数据
    private_key_bytes = bytes.fromhex("2217f3568c9881ae61de846a2c048efd1778ca67942bffe5678ca4c4620314a7")
    test_data = b"Implementation comparison test data"
    
    # 创建密钥对
    key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, "test-key")
    
    print(f"私钥: {private_key_bytes.hex()}")
    print(f"公钥: {key_pair.public_key.hex()}")
    print(f"测试数据: {test_data}")
    
    # 1. 直接使用 cryptography 生成 DER 签名
    print(f"\n--- 步骤1: 直接生成 DER 签名 ---")
    
    private_key_obj = ec.derive_private_key(
        int.from_bytes(private_key_bytes, byteorder="big"), 
        ec.SECP256K1()
    )
    signature_der = private_key_obj.sign(test_data, ec.ECDSA(hashes.SHA256()))
    print(f"DER 签名长度: {len(signature_der)} bytes")
    print(f"DER 签名: {signature_der.hex()}")
    
    # 2. 将 DER 转换为 R|S
    print(f"\n--- 步骤2: DER 转换为 R|S ---")
    
    r, s = decode_dss_signature(signature_der)
    print(f"r: {r}")
    print(f"s: {s}")
    
    r_bytes = r.to_bytes((r.bit_length() + 7) // 8, byteorder='big')
    s_bytes = s.to_bytes((s.bit_length() + 7) // 8, byteorder='big')
    signature_rs = r_bytes + s_bytes
    
    print(f"r_bytes 长度: {len(r_bytes)}, 内容: {r_bytes.hex()}")
    print(f"s_bytes 长度: {len(s_bytes)}, 内容: {s_bytes.hex()}")
    print(f"R|S 签名长度: {len(signature_rs)} bytes")
    print(f"R|S 签名: {signature_rs.hex()}")
    
    # 3. Base64 编码
    print(f"\n--- 步骤3: Base64 编码 ---")
    
    signature_b64 = base64.b64encode(signature_rs).decode('utf-8')
    print(f"Base64 签名: {signature_b64}")
    
    # 4. 验证过程：Base64 解码
    print(f"\n--- 步骤4: 验证过程 - Base64 解码 ---")
    
    decoded_signature = base64.b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
    print(f"解码后长度: {len(decoded_signature)} bytes")
    print(f"解码后内容: {decoded_signature.hex()}")
    print(f"解码一致性: {signature_rs == decoded_signature}")
    
    # 5. R|S 转换回 DER
    print(f"\n--- 步骤5: R|S 转换回 DER ---")
    
    r_length = len(decoded_signature) // 2
    r_recovered = int.from_bytes(decoded_signature[:r_length], 'big')
    s_recovered = int.from_bytes(decoded_signature[r_length:], 'big')
    
    print(f"恢复的 r: {r_recovered}")
    print(f"恢复的 s: {s_recovered}")
    print(f"r 一致性: {r == r_recovered}")
    print(f"s 一致性: {s == s_recovered}")
    
    signature_der_recovered = encode_dss_signature(r_recovered, s_recovered)
    print(f"恢复的 DER 长度: {len(signature_der_recovered)} bytes")
    print(f"恢复的 DER: {signature_der_recovered.hex()}")
    print(f"DER 一致性: {signature_der == signature_der_recovered}")
    
    # 6. 验证恢复的 DER 签名
    print(f"\n--- 步骤6: 验证恢复的 DER 签名 ---")
    
    # 从公钥字节创建公钥对象
    x = int.from_bytes(key_pair.public_key[1:33], byteorder='big')
    y = int.from_bytes(key_pair.public_key[33:65], byteorder='big')
    public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
    public_key_obj = public_numbers.public_key()
    
    try:
        public_key_obj.verify(signature_der_recovered, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 恢复的 DER 签名验证成功")
        der_verify_success = True
    except Exception as e:
        print(f"✗ 恢复的 DER 签名验证失败: {e}")
        der_verify_success = False
    
    # 7. 测试 PureWBADIDSigner
    print(f"\n--- 步骤7: 测试 PureWBADIDSigner ---")
    
    signer = PureWBADIDSigner()
    
    # 签名
    try:
        signer_signature = signer.sign_payload(test_data, private_key_bytes)
        print(f"✓ PureWBADIDSigner 签名成功: {signer_signature}")
        
        # 解码并检查
        signer_decoded = base64.b64decode(signer_signature + '=' * (-len(signer_signature) % 4))
        print(f"PureWBADIDSigner 解码长度: {len(signer_decoded)} bytes")
        print(f"PureWBADIDSigner 解码内容: {signer_decoded.hex()}")
        print(f"与手动 R|S 一致性: {signature_rs == signer_decoded}")
        
        signer_sign_success = True
    except Exception as e:
        print(f"✗ PureWBADIDSigner 签名失败: {e}")
        signer_sign_success = False
        return False
    
    # 验证
    try:
        is_valid = signer.verify_signature(test_data, signer_signature, key_pair.public_key)
        print(f"PureWBADIDSigner 自验证结果: {is_valid}")
        signer_verify_success = is_valid
    except Exception as e:
        print(f"✗ PureWBADIDSigner 验证异常: {e}")
        import traceback
        traceback.print_exc()
        signer_verify_success = False
    
    # 8. 手动验证 PureWBADIDSigner 的签名
    print(f"\n--- 步骤8: 手动验证 PureWBADIDSigner 签名 ---")
    
    try:
        # 解码
        manual_decoded = base64.b64decode(signer_signature + '=' * (-len(signer_signature) % 4))
        
        # R|S 转 DER
        manual_r_length = len(manual_decoded) // 2
        manual_r = int.from_bytes(manual_decoded[:manual_r_length], 'big')
        manual_s = int.from_bytes(manual_decoded[manual_r_length:], 'big')
        manual_der = encode_dss_signature(manual_r, manual_s)
        
        # 验证
        public_key_obj.verify(manual_der, test_data, ec.ECDSA(hashes.SHA256()))
        print(f"✓ 手动验证 PureWBADIDSigner 签名成功")
        manual_verify_success = True
    except Exception as e:
        print(f"✗ 手动验证 PureWBADIDSigner 签名失败: {e}")
        manual_verify_success = False
    
    # 9. 总结
    print(f"\n--- 总结 ---")
    print(f"DER 恢复验证: {der_verify_success}")
    print(f"PureWBADIDSigner 签名: {signer_sign_success}")
    print(f"PureWBADIDSigner 自验证: {signer_verify_success}")
    print(f"手动验证 PureWBADIDSigner: {manual_verify_success}")
    
    success = all([der_verify_success, signer_sign_success, signer_verify_success, manual_verify_success])
    
    return success

if __name__ == "__main__":
    success = debug_signature_process()
    print(f"\n{'🎉 所有测试通过！' if success else '❌ 存在问题需要修复！'}")
    sys.exit(0 if success else 1)
