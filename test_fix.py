#!/usr/bin/env python3
"""
测试修复是否生效的脚本
"""

def test_didcredentials_sign():
    """测试DIDCredentials的sign方法"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from anp_open_sdk.auth.schemas import DIDCredentials, DIDDocument, DIDKeyPair
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    
    # 创建测试用的secp256k1密钥对
    private_key_obj = ec.generate_private_key(ec.SECP256K1())
    private_key_bytes = private_key_obj.private_numbers().private_value.to_bytes(32, byteorder="big")
    public_key_bytes = private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # 创建DIDKeyPair
    key_pair = DIDKeyPair(
        private_key=private_key_bytes,
        public_key=public_key_bytes,
        key_id="key-1"
    )
    
    # 创建简单的DID文档
    did_doc_dict = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": "did:test:123",
        "verificationMethod": [
            {
                "id": "did:test:123#key-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": "did:test:123",
                "publicKeyMultibase": "z123"
            }
        ],
        "authentication": ["did:test:123#key-1"]
    }
    
    did_doc = DIDDocument(**did_doc_dict)
    
    # 创建DIDCredentials
    credentials = DIDCredentials(
        did="did:test:123",
        did_document=did_doc
    )
    credentials.add_key_pair(key_pair)
    
    # 测试sign方法
    test_data = b"Hello, World!"
    try:
        signature = credentials.sign(test_data, "#key-1")
        print(f"✅ DIDCredentials.sign 方法工作正常")
        print(f"   签名长度: {len(signature)} 字节")
        return True
    except Exception as e:
        print(f"❌ DIDCredentials.sign 方法失败: {e}")
        return False

def test_diddocument_access():
    """测试DIDDocument属性访问"""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from anp_open_sdk.auth.schemas import DIDDocument
    
    # 创建测试DID文档
    did_doc_dict = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": "did:test:123",
        "verificationMethod": [
            {
                "id": "did:test:123#key-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": "did:test:123",
                "publicKeyMultibase": "z123"
            }
        ],
        "authentication": ["did:test:123#key-1"]
    }
    
    did_doc = DIDDocument(**did_doc_dict)
    
    try:
        # 测试属性访问（而不是get方法）
        auth_methods = did_doc.authentication
        print(f"✅ DIDDocument.authentication 属性访问正常: {auth_methods}")
        
        verification_methods = did_doc.verification_methods
        print(f"✅ DIDDocument.verification_methods 属性访问正常: {len(verification_methods)} 个")
        return True
    except Exception as e:
        print(f"❌ DIDDocument 属性访问失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 测试修复是否生效")
    print("=" * 50)
    
    success1 = test_diddocument_access()
    success2 = test_didcredentials_sign()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有修复都工作正常!")
    else:
        print("❌ 还有问题需要修复")