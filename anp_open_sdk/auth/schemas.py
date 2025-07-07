from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization
from datetime import datetime
from anp_open_sdk.auth.utils import multibase_to_bytes


class VerificationMethod(BaseModel):
    id: str
    type: str
    controller: str
    public_key_multibase: Optional[str] = Field(None, alias="publicKeyMultibase")

    class Config:
        validate_by_name = True
        extra = "allow"


class DIDKeyPair(BaseModel):
    """DID密钥对内存对象 (支持 secp256k1)"""
    private_key: bytes = Field(..., description="私钥字节")
    public_key: bytes = Field(..., description="公钥字节")
    key_id: str = Field(..., description="密钥ID")

    class Config:
        arbitrary_types_allowed = True
    @classmethod
    def from_private_key_bytes(cls, private_key_bytes: bytes, key_id: str = "key-1"):
        """从 secp256k1 私钥字节创建密钥对"""
        private_key_obj = ec.derive_private_key(
            int.from_bytes(private_key_bytes, byteorder="big"), ec.SECP256K1()
        )
        public_key_obj = private_key_obj.public_key()
        public_key_bytes = public_key_obj.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        return cls(
            private_key=private_key_bytes,
            public_key=public_key_bytes,
            key_id=key_id
            )
    @classmethod
    def from_file_path(cls, private_key_path: str, key_id: str = "key-1"):
        """从PEM/PKCS8 secp256k1私钥文件创建密钥对"""
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
        )
            if not isinstance(private_key, ec.EllipticCurvePrivateKey):
                raise ValueError("Loaded private key is not an EC key")
            if private_key.curve.name != "secp256k1":
                raise ValueError("Private key is not secp256k1 curve")
            private_key_bytes = private_key.private_numbers().private_value.to_bytes(32, byteorder="big")
            public_key_bytes = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
                )
        return cls(
            private_key=private_key_bytes,
            public_key=public_key_bytes,
            key_id=key_id
                )
        

class DIDDocument(BaseModel):
    context: List[Any] = Field(..., alias="@context")
    id: str
    verification_methods: List[VerificationMethod] = Field(..., alias="verificationMethod")
    authentication: List[Any]
    service: Optional[List[Dict[str, Any]]] = None
    raw_document: Optional[Dict[str, Any]] = None

    class Config:
        validate_by_name = True
        extra = "allow"

    def get_public_key_bytes_by_fragment(self, fragment: str) -> Optional[bytes]:
        """
        根据ID片段 (e.g., '#keys-1') 查找验证方法并返回其公钥字节。
        """
        if not fragment.startswith('#'):
            return None

        for vm in self.verification_methods:
            if vm.id.endswith(fragment):
                public_key_multibase = vm.public_key_multibase
                if public_key_multibase:
                    return multibase_to_bytes(public_key_multibase)

                jwk = getattr(vm, 'public_key_jwk', None) or getattr(vm, 'publicKeyJwk', None)
                if jwk and jwk.get('kty') == 'EC' and jwk.get('crv') == 'secp256k1':
                    import base64
                    x = jwk.get('x')
                    y = jwk.get('y')
                    if x and y:
                        x_bytes = base64.urlsafe_b64decode(x + '=' * (-len(x) % 4))
                        y_bytes = base64.urlsafe_b64decode(y + '=' * (-len(y) % 4))
                        return b'\x04' + x_bytes + y_bytes
        return None

    @classmethod
    def from_file_path(cls, did_document_path: str):
        """从文件路径加载（向后兼容）"""
        import json
        with open(did_document_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        return cls(
            **doc,
            raw_document=doc
        )

    def get_verification_method(self, key_id: str) -> Optional[VerificationMethod]:
        """获取指定的验证方法"""
        for vm in self.verification_methods:
            if vm.id.endswith(f"#{key_id}"):
                return vm
        return None


class DIDCredentials(BaseModel):
    """DID凭证集合"""
    did: str
    did_document: DIDDocument
    key_pairs: Dict[str, DIDKeyPair] = Field(default_factory=dict)

    def get_key_pair(self, key_id: str = "key-1") -> Optional[DIDKeyPair]:
        """获取指定的密钥对"""
        return self.key_pairs.get(key_id)

    def add_key_pair(self, key_pair: DIDKeyPair):
        """添加密钥对"""
        self.key_pairs[key_pair.key_id] = key_pair

    def sign(self, data_to_sign: bytes, verification_method_fragment: str) -> bytes:
        """
        使用指定的验证方法签名数据
        
        Args:
            data_to_sign: 要签名的数据（字节）
            verification_method_fragment: 验证方法片段（如 "#key-1"）
            
        Returns:
            签名字节
        """
        # 提取密钥ID（去掉 # 前缀）
        key_id = verification_method_fragment.lstrip('#')
        
        # 获取对应的密钥对
        key_pair = self.get_key_pair(key_id)
        if not key_pair:
            raise ValueError(f"Key pair with ID '{key_id}' not found")
        
        # 根据密钥类型进行签名
        try:
            from cryptography.hazmat.primitives.asymmetric import ec, ed25519
            from cryptography.hazmat.primitives import hashes
            
            # 检查私钥长度来判断密钥类型
            if len(key_pair.private_key) == 32:
                # Ed25519 私钥
                try:
                    private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(key_pair.private_key)
                    return private_key_obj.sign(data_to_sign)
                except:
                    # 如果Ed25519失败，尝试secp256k1
                    pass
            
            # secp256k1 私钥
            private_key_obj = ec.derive_private_key(
                int.from_bytes(key_pair.private_key, byteorder="big"), 
                ec.SECP256K1()
            )
            return private_key_obj.sign(data_to_sign, ec.ECDSA(hashes.SHA256()))
            
        except Exception as e:
            raise ValueError(f"Failed to sign data with key '{key_id}': {e}")

    @classmethod
    def from_paths(cls, did_document_path: str, private_key_path: str, key_id: str = "key-1"):
        """从文件路径创建（向后兼容）"""
        did_doc = DIDDocument.from_file_path(did_document_path)
        key_pair = DIDKeyPair.from_file_path(private_key_path, key_id)
        # Extract DID from the document
        did = did_doc.id
        credentials = cls(did=did, did_document=did_doc)
        credentials.add_key_pair(key_pair)
        return credentials

    @classmethod
    def from_memory(cls, user_data: Any, key_id_attr: str = 'key_id') -> "DIDCredentials":
        """
        从内存中的用户数据对象创建DID凭证。
        期望 user_data 对象具有 'did_doc' (dict) 和 'private_key' (PEM string) 属性。
        """
        if not all(hasattr(user_data, attr) for attr in ['did_doc', 'private_key']):
            raise ValueError("传入的对象缺少必要的属性 (did_doc, private_key)。")

        private_key_pem = user_data.private_key.encode('utf-8')
        try:
            private_key_obj = serialization.load_pem_private_key(private_key_pem, password=None)
            public_key_obj = private_key_obj.public_key()
        except Exception as e:
            raise ValueError(f"无法从PEM加载私钥: {e}") from e

        if isinstance(private_key_obj, ec.EllipticCurvePrivateKey):
            private_key_bytes = private_key_obj.private_numbers().private_value.to_bytes(32, byteorder="big")
            public_key_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
        elif isinstance(private_key_obj, ed25519.Ed25519PrivateKey):
            private_key_bytes = private_key_obj.private_bytes(
                encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_key_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
            )
        else:
            raise TypeError(f"不支持的私钥类型: {type(private_key_obj)}")

        did_document_dict = user_data.did_doc
        did_doc = DIDDocument(
            **did_document_dict,
            raw_document=did_document_dict
        )
        if not did_doc.id:
            raise ValueError("DID document dictionary must contain a non-empty 'id' field.")

        key_id = getattr(user_data, key_id_attr, 'key-1') or 'key-1'
        key_pair = DIDKeyPair(private_key=private_key_bytes, public_key=public_key_bytes, key_id=key_id)

        # Extract DID from the document
        did = did_doc.id
        credentials = cls(did=did, did_document=did_doc)
        credentials.add_key_pair(key_pair)
        return credentials

    @classmethod
    def from_memory_data(cls, did_document_dict: Dict[str, Any], private_key_bytes: bytes, key_id: str = "key-1"):
        """从内存数据创建DID凭证"""
        did_doc = DIDDocument(
            **did_document_dict,
            raw_document=did_document_dict
        )
        key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, key_id)
        # Extract DID from the document
        did = did_doc.id
        credentials = cls(did=did, did_document=did_doc)
        credentials.add_key_pair(key_pair)
        return credentials

    @classmethod
    def from_user_data(cls, user_data):
        """从用户数据对象创建DID凭证"""
        with open(user_data.did_private_key_file_path, "rb") as key_file:
            private_key_pem = key_file.read()
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        if isinstance(private_key, ec.EllipticCurvePrivateKey):
            private_key_bytes = private_key.private_numbers().private_value.to_bytes(32, byteorder="big")
        else:
            try:
                private_key_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            except Exception:
                private_key_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
        key_id = getattr(user_data, 'key_id', 'key-1')
        if not key_id:
            key_id = 'key-1'
        
        # Create DIDDocument first
        did_doc = DIDDocument(
            **user_data.did_doc,
            raw_document=user_data.did_doc
        )
        
        # Create key pair
        key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, key_id)
        
        # Get DID from user_data or did_doc
        did = user_data.get_did() if hasattr(user_data, 'get_did') else user_data.did_doc.get('id')
        
        # Create credentials with the DID
        credentials = cls(did=did, did_document=did_doc)
        credentials.add_key_pair(key_pair)
        return credentials


class AuthenticationContext(BaseModel):
    """认证上下文"""
    caller_did: str
    target_did: str
    request_url: str
    method: str = "GET"
    timestamp: Optional[datetime] = None
    nonce: Optional[str] = None
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    json_data: Optional[Dict[str, Any]] = None
    use_two_way_auth: bool = True
    domain: Optional[str] = None  # 新增 domain 字段
