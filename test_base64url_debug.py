#!/usr/bin/env python3
"""
调试 base64url 编码/解码问题
"""

import base64

def test_base64url_encoding():
    """测试 base64url 编码/解码"""
    
    print("=== Base64url 编码/解码测试 ===")
    
    # 测试数据：64 字节的 R|S 签名
    test_data = bytes.fromhex("30f1cb245e50228717f64f1f528be7c48ba898a2a1f32151f28e18280aa465431743b5158b87be6eab201d04f37fa4fa47880f502048120208f1d48aad3fa1f0")
    
    print(f"原始数据长度: {len(test_data)} bytes")
    print(f"原始数据: {test_data.hex()}")
    
    # 方法1：标准 base64 编码
    print(f"\n--- 方法1: 标准 base64 ---")
    b64_standard = base64.b64encode(test_data).decode('ascii')
    print(f"标准 base64: {b64_standard}")
    
    decoded_standard = base64.b64decode(b64_standard)
    print(f"解码长度: {len(decoded_standard)} bytes")
    print(f"解码一致性: {test_data == decoded_standard}")
    
    # 方法2：base64url 编码（不去除填充）
    print(f"\n--- 方法2: base64url (保留填充) ---")
    b64url_with_padding = base64.urlsafe_b64encode(test_data).decode('ascii')
    print(f"base64url (带填充): {b64url_with_padding}")
    
    decoded_with_padding = base64.urlsafe_b64decode(b64url_with_padding)
    print(f"解码长度: {len(decoded_with_padding)} bytes")
    print(f"解码一致性: {test_data == decoded_with_padding}")
    
    # 方法3：base64url 编码（去除填充）
    print(f"\n--- 方法3: base64url (去除填充) ---")
    b64url_no_padding = base64.urlsafe_b64encode(test_data).rstrip(b'=').decode('ascii')
    print(f"base64url (无填充): {b64url_no_padding}")
    
    # 解码时添加填充
    padding_needed = 4 - (len(b64url_no_padding) % 4)
    if padding_needed != 4:
        b64url_with_added_padding = b64url_no_padding + '=' * padding_needed
    else:
        b64url_with_added_padding = b64url_no_padding
    
    print(f"添加填充后: {b64url_with_added_padding}")
    
    decoded_no_padding = base64.urlsafe_b64decode(b64url_with_added_padding)
    print(f"解码长度: {len(decoded_no_padding)} bytes")
    print(f"解码一致性: {test_data == decoded_no_padding}")
    
    # 方法4：使用当前 PureWBADIDSigner 的方法
    print(f"\n--- 方法4: PureWBADIDSigner 方法 ---")
    signature_encoded = base64.urlsafe_b64encode(test_data).rstrip(b'=').decode('ascii')
    print(f"编码结果: {signature_encoded}")
    
    # 解码（模拟 verify_signature 中的逻辑）
    signature_decoded = base64.urlsafe_b64decode(signature_encoded + '=' * (-len(signature_encoded) % 4))
    print(f"解码长度: {len(signature_decoded)} bytes")
    print(f"解码一致性: {test_data == signature_decoded}")
    
    # 检查填充计算
    padding_calc = -len(signature_encoded) % 4
    print(f"填充计算: -{len(signature_encoded)} % 4 = {padding_calc}")
    print(f"添加的填充: {'=' * padding_calc}")
    
    return test_data == signature_decoded

if __name__ == "__main__":
    success = test_base64url_encoding()
    print(f"\n{'🎉 Base64url 编码/解码正常！' if success else '❌ Base64url 编码/解码有问题！'}")
