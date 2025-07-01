import os
import glob
import json
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_secp256k1_keypair():
    """生成secp256k1密钥对"""
    # 生成私钥
    private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
    
    # 获取公钥
    public_key = private_key.public_key()
    
    return private_key, public_key

def private_key_to_pem(private_key):
    """将私钥转换为PEM格式"""
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def public_key_to_pem(public_key):
    """将公钥转换为PEM格式"""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def public_key_to_jwk(public_key):
    """将公钥转换为JWK格式"""
    # 获取椭圆曲线点坐标
    public_numbers = public_key.public_numbers()
    x_coord = public_numbers.x
    y_coord = public_numbers.y
    
    # 转换为32字节的字节数组
    x_bytes = x_coord.to_bytes(32, 'big')
    y_bytes = y_coord.to_bytes(32, 'big')
    
    # 转换为Base64URL编码（无填充）
    x_b64url = base64.urlsafe_b64encode(x_bytes).decode().rstrip('=')
    y_b64url = base64.urlsafe_b64encode(y_bytes).decode().rstrip('=')
    
    # 生成kid（密钥ID）
    # 使用公钥的SHA-256哈希作为kid
    public_key_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(public_key_der)
    kid = base64.urlsafe_b64encode(digest.finalize()).decode().rstrip('=')
    
    return {
        "kty": "EC",
        "crv": "secp256k1",
        "x": x_b64url,
        "y": y_b64url,
        "kid": kid
    }

def update_did_document_jwk(did_doc_path, new_jwk):
    """更新DID文档中的publicKeyJwk"""
    try:
        with open(did_doc_path, 'r', encoding='utf-8') as f:
            did_doc = json.load(f)
        
        # 更新verificationMethod中的publicKeyJwk
        if 'verificationMethod' in did_doc:
            for vm in did_doc['verificationMethod']:
                if 'publicKeyJwk' in vm:
                    vm['publicKeyJwk'] = new_jwk
                    print(f"  已更新 {vm['id']} 的 publicKeyJwk")
        
        # 写回文件
        with open(did_doc_path, 'w', encoding='utf-8') as f:
            json.dump(did_doc, f, indent=4, ensure_ascii=False)
        
        print(f"  DID文档已更新: {did_doc_path}")
        return True
        
    except Exception as e:
        print(f"  更新DID文档失败: {e}")
        return False

def rename_directory_with_prefix(user_dir, prefix):
    """重命名目录，添加前缀"""
    parent = os.path.dirname(user_dir)
    basename = os.path.basename(user_dir)
    new_dir = os.path.join(parent, f"{prefix}_{basename}")
    
    # 避免已存在同名目录
    if not os.path.exists(new_dir):
        print(f"重命名 {user_dir} -> {new_dir}")
        os.rename(user_dir, new_dir)
        return new_dir
    else:
        print(f"目标目录 {new_dir} 已存在，跳过重命名。")
        return user_dir

# 设置根目录
root_dir = os.path.join('data_user', 'localhost_9527', 'anp_users')

# 遍历所有 user_* 目录
for user_dir in glob.glob(os.path.join(root_dir, 'user_*')):











    print(f"\n处理目录: {user_dir}")
    
    # 检查文件路径
    key_private_path = os.path.join(user_dir, 'key-1_private.pem')
    private_key_path = os.path.join(user_dir, 'private_key.pem')
    public_key_path = os.path.join(user_dir, 'public_key.pem')
    did_doc_path = os.path.join(user_dir, 'did_document.json')
    
    # 1. 原有功能：检查 key-1_private.pem
    if not os.path.isfile(key_private_path):
        print(f"  缺少 key-1_private.pem")
        user_dir = rename_directory_with_prefix(user_dir, 'nojwtkey')
        continue
    
    # 2. 新功能1：检查 did_document.json
    if not os.path.isfile(did_doc_path):
        print(f"  缺少 did_document.json")
        user_dir = rename_directory_with_prefix(user_dir, 'nodiddoc')
        continue
    
    # 3. 新功能2：检查 private_key.pem，如果没有则生成密钥对并更新DID文档
    if not os.path.isfile(private_key_path):
        print(f"  缺少 private_key.pem，开始生成新密钥对...")
        
        try:
            # 生成密钥对
            private_key, public_key = generate_secp256k1_keypair()
            
            # 转换为PEM格式
            private_pem = private_key_to_pem(private_key)
            public_pem = public_key_to_pem(public_key)
            
            # 保存私钥
            with open(private_key_path, 'wb') as f:
                f.write(private_pem)
            print(f"  已生成 private_key.pem")
            
            # 保存公钥
            with open(public_key_path, 'wb') as f:
                f.write(public_pem)
            print(f"  已生成 public_key.pem")
            
            # 转换为JWK格式
            jwk = public_key_to_jwk(public_key)
            print(f"  生成的JWK: {jwk}")
            
            # 更新DID文档
            if update_did_document_jwk(did_doc_path, jwk):
                print(f"  ✓ 成功更新DID文档中的publicKeyJwk")
            else:
                print(f"  ✗ 更新DID文档失败")
                
        except Exception as e:
            print(f"  生成密钥对失败: {e}")
            continue
    else:

        print(f"  已存在 private_key.pem，跳过生成")
    
    print(f"  ✓ {user_dir} 处理完成")

print(f"\n所有目录处理完成！")
