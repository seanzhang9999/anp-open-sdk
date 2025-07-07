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

import sys

# 从命令行参数获取根目录
if len(sys.argv) < 2:
    print("Usage: python script.py <root_directory>")
    sys.exit(1)

root_dir = sys.argv[1]
from pathlib import Path

root_dir = Path(root_dir).resolve()

from Crypto.PublicKey import RSA

# 遍历所有 user_* 目录
for user_dir in glob.glob(os.path.join(root_dir, 'user_*')):

    # 获取目录名用于特殊判断
    dir_name = os.path.basename(user_dir)

    
    # 检查文件路径
    jwt_key_public_path = os.path.join(user_dir, 'public_key.pem')
    jwt_key_private_path = os.path.join(user_dir, 'private_key.pem')
    private_key_path = os.path.join(user_dir, 'key-1_private.pem')
    public_key_path = os.path.join(user_dir, 'key-1_public.pem')
    did_doc_path = os.path.join(user_dir, 'did_document.json')



    # 1. 功能1：检查 did_document.json
    if not os.path.isfile(did_doc_path):
        print(f"  缺少 did_document.json")
        user_dir = rename_directory_with_prefix(user_dir, 'nodiddoc')
        continue
    print(f"\n处理目录: {user_dir}")

    # 1. 检查并创建JWT密钥
    if dir_name == "user_hosted_agent-did.com_80_":
        # 特殊处理：只检查并创建固定的 key-1_private.pem
        if not os.path.isfile(private_key_path):
            print(f"  缺少 key-1_private.pem，正在创建固定密钥...")
            try:
                fixed_private_key = """-----BEGIN PRIVATE KEY-----
    MIGEAgEAMBAGByqGSM49AgEGBSuBBAAKBG0wawIBAQQgvt5dMwF4pTOFv1BBD1IV
    ezSrGc0X/aDMesV57FeDvpKhRANCAASQ1x9W59virFSlMLuRPpXnrNIURdvKjedM
    NQXGpplsq7qR6TaCJvIenA0WajVo2+FV22p4qts8+N8kKIkfGX6r
    -----END PRIVATE KEY-----"""

                with open(private_key_path, "w") as f:
                    f.write(fixed_private_key)

                print(f"  固定密钥创建成功")
            except Exception as e:
                print(f"  密钥创建失败: {e}")
                user_dir = rename_directory_with_prefix(user_dir, 'nokey')
                continue
        else:
            print(f"  已存在 key-1_private.pem，跳过创建")
    else:
        # 2. 普通用户：检查并创建JWT密钥
        if not os.path.isfile(jwt_key_private_path):
            print(f"  缺少 JWT密钥，正在创建...")
            try:
                private_key = RSA.generate(2048).export_key()
                public_key = RSA.import_key(private_key).publickey().export_key()

                with open(jwt_key_private_path, "wb") as f:
                    f.write(private_key)
                with open(jwt_key_public_path, "wb") as f:
                    f.write(public_key)

                print(f"  JWT密钥创建成功")
            except Exception as e:
                print(f"  JWT密钥创建失败: {e}")
                user_dir = rename_directory_with_prefix(user_dir, 'nojwtkey')
                continue

        # 3. 检查并创建 key-1_private.pem
        if not os.path.isfile(private_key_path):
            print(f"  缺少 key-1_private.pem，开始生成新密钥对...")

            try:
                private_key, public_key = generate_secp256k1_keypair()

                private_pem = private_key_to_pem(private_key)
                public_pem = public_key_to_pem(public_key)

                with open(private_key_path, 'wb') as f:
                    f.write(private_pem)
                print(f"  已生成 key-1_private.pem")

                with open(public_key_path, 'wb') as f:
                    f.write(public_pem)
                print(f"  已生成 key-1_public.pem")

                jwk = public_key_to_jwk(public_key)
                print(f"  生成的JWK: {jwk}")

                # 更新DID文档
                if os.path.isfile(did_doc_path):
                    if update_did_document_jwk(did_doc_path, jwk):
                        print(f"  ✓ 成功更新DID文档")
                    else:
                        print(f"  ✗ 更新DID文档失败")
                else:
                    print(f"  警告：DID文档不存在，无法更新")

            except Exception as e:
                print(f"  生成密钥对失败: {e}")
                continue
        else:
            print(f"  已存在 key-1_private.pem，跳过生成")

    print(f"  ✓ {user_dir} 处理完成")

print(f"\n所有目录处理完成！")
