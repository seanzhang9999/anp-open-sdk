from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization
from datetime import datetime
from anp_open_sdk.auth.utils import multibase_to_bytes

import logging
logger = logging.getLogger(__name__)

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
        
        # DEBUG: 记录签名请求的基本信息
        logger.info(f"🔐 PRIVATE KEY DEBUG - Key ID: {key_id}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Verification method fragment: {verification_method_fragment}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Data to sign length: {len(data_to_sign)}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Data to sign (hex): {data_to_sign.hex()}")
        
        # 获取对应的密钥对
        key_pair = self.get_key_pair(key_id)
        if not key_pair:
            raise ValueError(f"Key pair with ID '{key_id}' not found")
        
        # DEBUG: 记录密钥对信息
        logger.info(f"🔐 PRIVATE KEY DEBUG - Private key length: {len(key_pair.private_key)}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Private key (hex): {key_pair.private_key.hex()}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Public key length: {len(key_pair.public_key)}")
        logger.info(f"🔐 PRIVATE KEY DEBUG - Public key (hex): {key_pair.public_key.hex()}")
        
        # 根据密钥类型进行签名
        try:
            from cryptography.hazmat.primitives.asymmetric import ec, ed25519
            from cryptography.hazmat.primitives import hashes
            
            # 检查私钥长度来判断密钥类型
            # 但是32字节可能是Ed25519或secp256k1，需要根据公钥长度来更准确地判断
            if len(key_pair.private_key) == 32 and len(key_pair.public_key) == 32:
                # Ed25519 私钥 (32 bytes) + Ed25519 公钥 (32 bytes)
                try:
                    private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(key_pair.private_key)
                    logger.info(f"🔐 PRIVATE KEY DEBUG - Using Ed25519 signing")
                    signature_bytes = private_key_obj.sign(data_to_sign)
                    logger.info(f"🔐 PRIVATE KEY DEBUG - Ed25519 signature length: {len(signature_bytes)}")
                    logger.info(f"🔐 PRIVATE KEY DEBUG - Ed25519 signature (hex): {signature_bytes.hex()}")
                    return signature_bytes
                except Exception as ed25519_error:
                    logger.info(f"🔐 PRIVATE KEY DEBUG - Ed25519 failed: {ed25519_error}, trying secp256k1")
                    # 如果Ed25519失败，尝试secp256k1
                    pass
            
            # secp256k1 私钥 (支持32字节私钥 + 33/65字节公钥的组合)
            logger.info(f"🔐 PRIVATE KEY DEBUG - Using secp256k1 signing")
            private_key_obj = ec.derive_private_key(
                int.from_bytes(key_pair.private_key, byteorder="big"), 
                ec.SECP256K1()
            )
            
            # 生成对应的公钥用于验证
            public_key_obj = private_key_obj.public_key()
            from cryptography.hazmat.primitives import serialization
            public_key_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            logger.info(f"🔐 PRIVATE KEY DEBUG - Derived public key length: {len(public_key_bytes)}")
            logger.info(f"🔐 PRIVATE KEY DEBUG - Derived public key (hex): {public_key_bytes.hex()}")
            logger.info(f"🔐 PRIVATE KEY DEBUG - Public key matches stored: {public_key_bytes.hex() == key_pair.public_key.hex()}")

            # 直接返回 DER 格式签名（与原始 agent_connect 保持一致）
            signature_bytes = private_key_obj.sign(data_to_sign, ec.ECDSA(hashes.SHA256()))
            logger.info(f"🔐 PRIVATE KEY DEBUG - secp256k1 signature length: {len(signature_bytes)}")
            logger.info(f"🔐 PRIVATE KEY DEBUG - secp256k1 signature (hex): {signature_bytes.hex()}")
            return signature_bytes
            
        except Exception as e:
            logger.error(f"🔐 PRIVATE KEY DEBUG - Signing failed: {e}")
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
        # Handle both LocalAgent and user_data objects
        if hasattr(user_data, 'private_key_path'):
            private_key_file_path = user_data.private_key_path
            # For LocalAgent, we need to get did_doc from user_data
            if hasattr(user_data, 'user_data') and hasattr(user_data.user_data, 'did_doc'):
                did_doc_data = user_data.user_data.did_doc
            else:
                # Fallback: read from did_document_path
                import json
                with open(user_data.did_document_path, 'r', encoding='utf-8') as f:
                    did_doc_data = json.load(f)
        elif hasattr(user_data, 'did_private_key_file_path'):
            private_key_file_path = user_data.did_private_key_file_path
            did_doc_data = user_data.did_doc
        else:
            raise AttributeError(f"User data object {type(user_data)} does not have private key path attribute")
        
        with open(private_key_file_path, "rb") as key_file:
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
            **did_doc_data,
            raw_document=did_doc_data
        )
        
        # 🔧 FIX: 使用DID文档中存储的公钥，而不是重新生成
        # 从DID文档中获取公钥
        public_key_bytes = None
        try:
            public_key_bytes = did_doc.get_public_key_bytes_by_fragment(f"#{key_id}")
            if public_key_bytes:
                logger.info(f"🔑 使用DID文档中存储的公钥 (长度: {len(public_key_bytes)} bytes)")
                logger.info(f"🔑 存储的公钥 (hex): {public_key_bytes.hex()}")
            else:
                logger.warning(f"🔑 无法从DID文档获取公钥，将从私钥重新生成")
        except Exception as e:
            logger.warning(f"🔑 从DID文档获取公钥失败: {e}，将从私钥重新生成")
        
        # 如果无法从DID文档获取公钥，才从私钥重新生成
        if public_key_bytes is None:
            logger.info(f"🔑 从私钥重新生成公钥")
            # Create key pair using from_private_key_bytes (这会重新生成公钥)
            key_pair = DIDKeyPair.from_private_key_bytes(private_key_bytes, key_id)
            public_key_bytes = key_pair.public_key
            logger.info(f"🔑 重新生成的公钥 (hex): {public_key_bytes.hex()}")
        
        # 直接创建密钥对，使用存储的公钥
        key_pair = DIDKeyPair(
            private_key=private_key_bytes,
            public_key=public_key_bytes,  # 使用DID文档中的公钥
            key_id=key_id
        )
        
        # Get DID from user_data or did_doc_data
        if hasattr(user_data, 'get_did'):
            did = user_data.get_did()
        elif hasattr(user_data, 'id'):
            did = user_data.id
        else:
            did = did_doc_data.get('id')
        
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
