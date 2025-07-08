# anp_open_sdk/auth_methods/wba/implementation.py
# 兼容层：提供向后兼容的接口，实际调用protocol层的统一实现

"""
WBA Authentication Implementation - Compatibility Layer

This module provides backward compatibility for existing code while
redirecting all calls to the unified implementation in protocol layer.
"""

import logging
from typing import Dict, Any, Optional, Tuple

# Import from the unified protocol implementation
from anp_open_sdk.protocol.authentication.did_wba import (
    generate_auth_header_two_way,
    verify_auth_header_signature_two_way,
    extract_auth_header_parts_two_way,
    resolve_did_wba_document,
    create_did_wba_document
)
from anp_open_sdk.protocol.crypto import create_secp256k1_signer, create_ed25519_signer
from anp_open_sdk.protocol.verification_methods import create_verification_method

logger = logging.getLogger(__name__)


class PureWBADIDSigner:
    """
    兼容性包装器 - WBA DID签名器
    实际调用protocol层的统一实现
    """
    
    def __init__(self):
        logger.debug("🔑 创建PureWBADIDSigner兼容包装器")
    
    def verify_signature(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """验证签名 - 调用protocol层实现"""
        try:
            logger.debug("🔍 验证签名 (兼容层调用)")
            
            # 根据公钥长度选择合适的签名器
            if len(public_key) == 32:
                signer = create_ed25519_signer()
            else:
                signer = create_secp256k1_signer()
            
            return signer.verify(data, signature, public_key)
        except Exception as e:
            logger.error(f"🔍 签名验证失败: {e}")
            return False


class PureWBAAuthHeaderBuilder:
    """
    兼容性包装器 - WBA认证头构建器
    实际调用protocol层的统一实现
    """
    
    def __init__(self):
        """初始化认证头构建器 - 新架构不需要外部依赖"""
        logger.debug("🔑 创建PureWBAAuthHeaderBuilder兼容包装器")
    
    async def build_auth_header(self, context: Any, credentials: Any) -> Dict[str, Any]:
        """构建认证头 - 调用protocol层实现"""
        try:
            logger.debug("🔑 构建认证头 (兼容层调用)")
            
            # 提取必要参数
            caller_did = getattr(context, 'caller_did', None)
            target_did = getattr(context, 'target_did', None) 
            request_url = getattr(context, 'request_url', 'http://localhost')
            
            if not caller_did:
                raise ValueError("Missing caller_did in context")
            
            # 获取私钥
            private_key_bytes = None
            if hasattr(credentials, 'key_pairs') and credentials.key_pairs:
                key_pair = next(iter(credentials.key_pairs.values()))
                private_key_bytes = key_pair.private_key
            
            if not private_key_bytes:
                raise ValueError("No private key available in credentials")
            
            # 调用protocol层实现
            result = await generate_auth_header_two_way(
                caller_did=caller_did,
                target_did=target_did,
                request_url=request_url,
                private_key_bytes=private_key_bytes
            )
            
            logger.debug("🔑 认证头构建成功 (兼容层)")
            return result
            
        except Exception as e:
            logger.error(f"🔑 构建认证头失败: {e}")
            raise
    
    def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """解析认证头 - 调用protocol层实现"""
        try:
            logger.debug("🔍 解析认证头 (兼容层调用)")
            
            # 导入protocol层的解析函数
            from anp_open_sdk.protocol.authentication.did_wba import DIDWbaAuthHeader
            
            # 创建临时实例来解析
            dummy_header = DIDWbaAuthHeader("dummy")
            parsed = dummy_header.parse_auth_header(auth_header)
            
            logger.debug(f"🔍 认证头解析成功: {parsed}")
            return parsed
            
        except Exception as e:
            logger.error(f"🔍 解析认证头失败: {e}")
            return {}


class PureWBAAuth:
    """
    兼容性包装器 - WBA认证器主类
    实际调用protocol层的统一实现
    """
    
    def __init__(self):
        logger.debug("🔓 创建PureWBAAuth兼容包装器")
        self.signer = PureWBADIDSigner()
        self.header_builder = PureWBAAuthHeaderBuilder()
    
    def extract_dids_from_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """从认证头提取DID - 调用protocol层实现"""
        try:
            logger.debug("🔍 提取DID (兼容层调用)")
            parts = extract_auth_header_parts_two_way(auth_header)
            if parts and len(parts) >= 2:
                return parts[0], parts[1]  # caller_did, target_did
            return None, None
        except Exception as e:
            logger.error(f"🔍 提取DID失败: {e}")
            return None, None
    
    def extract_did_from_auth_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        """从认证头提取DID - 别名方法，用于兼容性"""
        return self.extract_dids_from_header(auth_header)
    
    async def build_auth_header(self, context: Any, credentials: Any) -> Dict[str, Any]:
        """构建认证头 - 委托给header_builder"""
        return await self.header_builder.build_auth_header(context, credentials)
    
    async def verify_signature_from_header(self, auth_header: str, context: Any, expected_sender_did: str) -> Tuple[bool, str]:
        """验证认证头签名 - 调用protocol层实现"""
        try:
            logger.debug("🔍 验证认证头签名 (兼容层调用)")
            
            # 调用protocol层实现
            is_valid, message = await verify_auth_header_signature_two_way(
                auth_header=auth_header,
                expected_caller_did=expected_sender_did
            )
            
            logger.debug(f"🔍 签名验证结果: {is_valid}, {message}")
            return is_valid, message
            
        except Exception as e:
            logger.error(f"🔍 验证认证头签名失败: {e}")
            return False, str(e)


# 创建全局实例供兼容性使用
def create_pure_authenticator(resolver=None) -> PureWBAAuth:
    """创建纯净认证器 - 兼容性函数，接受resolver参数但忽略它"""
    logger.debug("🔓 创建纯净认证器 (兼容层)")
    return PureWBAAuth()


# 为了完全兼容，也提供类的别名
PureWBADIDAuthenticator = PureWBAAuth