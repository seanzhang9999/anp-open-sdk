#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DID 密钥一致性检查和修复脚本

检查所有 user_* 目录中的：
1. key-1_private.pem 和 key-1_public.pem 是否匹配 (DID认证用)
2. private_key.pem 和 public_key.pem 是否匹配 (JWT用)
3. DID 文档中的公钥是否与实际密钥文件匹配
4. 自动修复不一致的 DID 文档
"""

import os
import glob
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives import serialization

def load_private_key_from_file(private_key_path):
    """从PEM文件加载私钥"""
    try:
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        return private_key
    except Exception as e:
        print(f"❌ 无法加载私钥 {private_key_path}: {e}")
        return None

def load_public_key_from_file(public_key_path):
    """从PEM文件加载公钥"""
    try:
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        return public_key
    except Exception as e:
        print(f"❌ 无法加载公钥 {public_key_path}: {e}")
        return None

def get_public_key_from_private(private_key):
    """从私钥生成公钥"""
    try:
        return private_key.public_key()
    except Exception as e:
        print(f"❌ 无法从私钥生成公钥: {e}")
        return None

def public_keys_match(pub_key1, pub_key2):
    """比较两个公钥是否相同"""
    try:
        # 处理不同类型的公钥
        if isinstance(pub_key1, ec.EllipticCurvePublicKey) and isinstance(pub_key2, ec.EllipticCurvePublicKey):
            pub1_bytes = pub_key1.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            pub2_bytes = pub_key2.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
        elif isinstance(pub_key1, rsa.RSAPublicKey) and isinstance(pub_key2, rsa.RSAPublicKey):
            pub1_bytes = pub_key1.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            pub2_bytes = pub_key2.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        else:
            print(f"❌ 不同类型的公钥无法比较: {type(pub_key1)} vs {type(pub_key2)}")
            return False
        
        return pub1_bytes == pub2_bytes
    except Exception as e:
        print(f"❌ 无法比较公钥: {e}")
        return False

def get_jwk_coordinates_from_public_key(public_key):
    """从公钥获取JWK格式的x,y坐标"""
    try:
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_numbers = public_key.public_numbers()
            x_bytes = public_numbers.x.to_bytes(32, byteorder='big')
            y_bytes = public_numbers.y.to_bytes(32, byteorder='big')
            
            x_b64 = base64.urlsafe_b64encode(x_bytes).rstrip(b'=').decode('ascii')
            y_b64 = base64.urlsafe_b64encode(y_bytes).rstrip(b'=').decode('ascii')
            
            return x_b64, y_b64
        else:
            print(f"❌ 不支持的公钥类型: {type(public_key)}")
            return None, None
    except Exception as e:
        print(f"❌ 无法获取JWK坐标: {e}")
        return None, None

def get_public_key_hex(public_key):
    """获取公钥的十六进制表示"""
    try:
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            return pub_bytes.hex()
        elif isinstance(public_key, rsa.RSAPublicKey):
            pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pub_bytes.hex()[:128] + "..." if len(pub_bytes.hex()) > 128 else pub_bytes.hex()
        else:
            return "Unknown key type"
    except Exception as e:
        print(f"❌ 无法获取公钥十六进制: {e}")
        return None

def get_key_info(key):
    """获取密钥的详细信息"""
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return f"EC Private Key ({key.curve.name})"
    elif isinstance(key, ec.EllipticCurvePublicKey):
        return f"EC Public Key ({key.curve.name})"
    elif isinstance(key, rsa.RSAPrivateKey):
        return f"RSA Private Key ({key.key_size} bits)"
    elif isinstance(key, rsa.RSAPublicKey):
        return f"RSA Public Key ({key.key_size} bits)"
    else:
        return f"Unknown Key Type: {type(key)}"

def load_did_document(did_doc_path):
    """加载DID文档"""
    try:
        with open(did_doc_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载DID文档 {did_doc_path}: {e}")
        return None

def get_jwk_from_did_document(did_doc):
    """从DID文档中提取JWK"""
    try:
        if 'verificationMethod' in did_doc:
            for vm in did_doc['verificationMethod']:
                if 'publicKeyJwk' in vm:
                    jwk = vm['publicKeyJwk']
                    return jwk.get('x'), jwk.get('y')
        return None, None
    except Exception as e:
        print(f"❌ 无法从DID文档提取JWK: {e}")
        return None, None

def update_did_document_jwk(did_doc_path, x_b64, y_b64):
    """更新DID文档中的JWK坐标"""
    try:
        did_doc = load_did_document(did_doc_path)
        if not did_doc:
            return False
        
        updated = False
        if 'verificationMethod' in did_doc:
            for vm in did_doc['verificationMethod']:
                if 'publicKeyJwk' in vm:
                    vm['publicKeyJwk']['x'] = x_b64
                    vm['publicKeyJwk']['y'] = y_b64
                    updated = True
        
        if updated:
            with open(did_doc_path, 'w', encoding='utf-8') as f:
                json.dump(did_doc, f, indent=4, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        print(f"❌ 无法更新DID文档 {did_doc_path}: {e}")
        return False

def check_user_directory(user_dir_path):
    """检查单个用户目录的密钥一致性"""
    user_dir = Path(user_dir_path)
    user_name = user_dir.name
    
    print(f"\n🔍 检查用户目录: {user_name}")
    
    # 文件路径
    did_private_key_path = user_dir / "key-1_private.pem"
    did_public_key_path = user_dir / "key-1_public.pem"
    jwt_private_key_path = user_dir / "private_key.pem"
    jwt_public_key_path = user_dir / "public_key.pem"
    did_doc_path = user_dir / "did_document.json"
    
    # 检查文件是否存在
    files_status = {
        "key-1_private.pem": did_private_key_path.exists(),
        "key-1_public.pem": did_public_key_path.exists(),
        "private_key.pem": jwt_private_key_path.exists(),
        "public_key.pem": jwt_public_key_path.exists(),
        "did_document.json": did_doc_path.exists()
    }
    
    missing_files = [name for name, exists in files_status.items() if not exists]
    if missing_files:
        print(f"⚠️  缺少文件: {', '.join(missing_files)}")
        if len(missing_files) > 2:  # 如果缺少太多文件，跳过
            return False
    
    success = True
    
    # 1. 检查 DID 密钥对 (key-1_private.pem & key-1_public.pem)
    if files_status["key-1_private.pem"] and files_status["key-1_public.pem"]:
        print("📋 检查 DID 密钥对 (key-1_*.pem):")
        
        did_private_key = load_private_key_from_file(did_private_key_path)
        did_public_key_from_file = load_public_key_from_file(did_public_key_path)
        
        if did_private_key and did_public_key_from_file:
            print(f"   私钥: {get_key_info(did_private_key)}")
            print(f"   公钥: {get_key_info(did_public_key_from_file)}")
            
            did_public_key_from_private = get_public_key_from_private(did_private_key)
            if did_public_key_from_private:
                if public_keys_match(did_public_key_from_private, did_public_key_from_file):
                    print("   ✅ DID 私钥和公钥文件匹配")
                else:
                    print("   ❌ DID 私钥和公钥文件不匹配")
                    success = False
            else:
                success = False
        else:
            success = False
    else:
        print("⚠️  DID 密钥文件不完整，跳过 DID 密钥检查")
    
    # 2. 检查 JWT 密钥对 (private_key.pem & public_key.pem)
    if files_status["private_key.pem"] and files_status["public_key.pem"]:
        print("📋 检查 JWT 密钥对 (private_key.pem & public_key.pem):")
        
        jwt_private_key = load_private_key_from_file(jwt_private_key_path)
        jwt_public_key_from_file = load_public_key_from_file(jwt_public_key_path)
        
        if jwt_private_key and jwt_public_key_from_file:
            print(f"   私钥: {get_key_info(jwt_private_key)}")
            print(f"   公钥: {get_key_info(jwt_public_key_from_file)}")
            
            jwt_public_key_from_private = get_public_key_from_private(jwt_private_key)
            if jwt_public_key_from_private:
                if public_keys_match(jwt_public_key_from_private, jwt_public_key_from_file):
                    print("   ✅ JWT 私钥和公钥文件匹配")
                else:
                    print("   ❌ JWT 私钥和公钥文件不匹配")
                    success = False
            else:
                success = False
        else:
            success = False
    else:
        print("⚠️  JWT 密钥文件不完整，跳过 JWT 密钥检查")
    
    # 3. 检查 DID 文档中的公钥
    if files_status["key-1_private.pem"] and files_status["did_document.json"]:
        print("📋 检查 DID 文档中的公钥:")
        
        did_private_key = load_private_key_from_file(did_private_key_path)
        if did_private_key:
            did_public_key_from_private = get_public_key_from_private(did_private_key)
            if did_public_key_from_private and isinstance(did_public_key_from_private, ec.EllipticCurvePublicKey):
                # 获取正确的JWK坐标
                x_correct, y_correct = get_jwk_coordinates_from_public_key(did_public_key_from_private)
                if x_correct and y_correct:
                    # 检查DID文档中的JWK
                    did_doc = load_did_document(did_doc_path)
                    if did_doc:
                        x_in_doc, y_in_doc = get_jwk_from_did_document(did_doc)
                        
                        if x_in_doc == x_correct and y_in_doc == y_correct:
                            print("   ✅ DID文档中的公钥与密钥文件匹配")
                            pub_hex = get_public_key_hex(did_public_key_from_private)
                            print(f"   📋 公钥 (hex): {pub_hex}")
                        else:
                            print("   ❌ DID文档中的公钥与密钥文件不匹配")
                            print(f"      DID文档中: x={x_in_doc}, y={y_in_doc}")
                            print(f"      应该是:    x={x_correct}, y={y_correct}")
                            
                            # 自动修复
                            print("   🔧 正在修复DID文档...")
                            if update_did_document_jwk(did_doc_path, x_correct, y_correct):
                                print("   ✅ DID文档已修复")
                                pub_hex = get_public_key_hex(did_public_key_from_private)
                                print(f"   📋 公钥 (hex): {pub_hex}")
                            else:
                                print("   ❌ DID文档修复失败")
                                success = False
                    else:
                        success = False
                else:
                    success = False
            else:
                print("   ⚠️  DID 私钥不是 EC 密钥，跳过 DID 文档检查")
        else:
            success = False
    else:
        print("⚠️  缺少 DID 私钥或 DID 文档，跳过 DID 文档检查")
    
    return success

def main():
    """主函数"""
    print("🚀 开始完整密钥一致性检查...")
    print("检查项目:")
    print("  1. DID 密钥对 (key-1_private.pem & key-1_public.pem)")
    print("  2. JWT 密钥对 (private_key.pem & public_key.pem)")
    print("  3. DID 文档中的公钥一致性")
    
    # 查找所有用户目录
    user_dirs = []
    
    # 在多个可能的位置查找用户目录
    search_paths = [
        "demo_anp_open_sdk_framework/data_user/localhost_9527/anp_users",
        "demo_anp_open_sdk/data_user/localhost_9527/anp_users", 
        "demo_anp_user_service/anp_user_service/data_user/localhost_9527/anp_users",
        "test/data_user/localhost_9527/anp_users"
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            pattern = os.path.join(search_path, "user_*")
            user_dirs.extend(glob.glob(pattern))
    
    if not user_dirs:
        print("❌ 未找到任何用户目录")
        return
    
    print(f"📂 找到 {len(user_dirs)} 个用户目录")
    
    # 检查每个用户目录
    success_count = 0
    total_count = len(user_dirs)
    
    for user_dir in sorted(user_dirs):
        if check_user_directory(user_dir):
            success_count += 1
    
    # 总结
    print(f"\n📊 检查完成:")
    print(f"   总计: {total_count} 个用户目录")
    print(f"   成功: {success_count} 个")
    print(f"   失败: {total_count - success_count} 个")
    
    if success_count == total_count:
        print("🎉 所有用户目录的密钥一致性检查通过！")
    else:
        print("⚠️  部分用户目录存在问题，请检查上述输出")

if __name__ == "__main__":
    main()