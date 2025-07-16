# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
DID格式管理器

提供DID格式化、解析、验证和身份管理功能
"""

import logging
import re
import secrets
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from ..config import get_global_config
from anp_sdk.domain import get_domain_manager

logger = logging.getLogger(__name__)

class DidFormatManager:
    """DID格式管理器 - 处理DID格式化、解析和验证"""
    
    def __init__(self):
        """初始化DID格式管理器"""
        self.config = get_global_config()
        self.domain_manager = get_domain_manager()
        self._format_cache = {}
        
    def create_agent_identity(self, name: str, description: str, 
                            host: str, port: int, user_type: str = "user") -> Dict[str, str]:
        """
        创建Agent身份信息
        
        Args:
            name: Agent名称
            description: Agent描述
            host: 主机名
            port: 端口
            user_type: 用户类型
            
        Returns:
            Dict[str, str]: 包含完整身份信息的字典
        """
        try:
            # 验证用户类型是否可创建
            if not self.can_create_user_type(user_type):
                raise ValueError(f"不允许创建用户类型: {user_type}")
            
            # 生成唯一ID
            unique_id = self._generate_unique_id()
            
            # 格式化DID
            did = self.format_did(host, port, user_type, unique_id)
            
            # 构建身份信息
            identity = {
                'name': name,
                'description': description,
                'unique_id': unique_id,
                'did': did,
                'type': user_type,
                'host': host,
                'port': str(port)
            }
            
            # 验证身份信息
            valid, error_msg = self.validate_agent_identity(identity)
            if not valid:
                raise ValueError(f"身份验证失败: {error_msg}")
            
            logger.info(f"创建Agent身份成功: {name} -> {did}")
            return identity
            
        except Exception as e:
            logger.error(f"创建Agent身份失败: {e}")
            raise
    
    def format_did(self, host: str, port: int, user_type: str, unique_id: str) -> str:
        """
        格式化DID（智能处理端口编码）
        
        Args:
            host: 主机名
            port: 端口
            user_type: 用户类型
            unique_id: 唯一标识符
            
        Returns:
            str: 格式化的DID字符串
        """
        try:
            method = self._get_method()
            
            # 智能处理端口编码：标准端口不编码，非标准端口使用%3A编码
            if self._is_standard_port(port):
                # 标准端口（80, 443）不需要编码，直接使用主机名
                host_part = host
            else:
                # 非标准端口使用%3A编码
                host_part = f"{host}%3A{port}"
            
            # 直接构建DID，避免模板中的端口参数导致双重编码
            did = f"did:{method}:{host_part}:{method}:{user_type}:{unique_id}"
            
            return did
            
        except Exception as e:
            logger.error(f"格式化DID失败: {e}")
            raise
    
    def parse_did(self, did: str) -> Optional[Dict[str, str]]:
        """
        解析DID字符串（支持%3A编码）
        
        Args:
            did: DID字符串
            
        Returns:
            Optional[Dict[str, str]]: 解析结果，包含各个组件
        """
        if not did:
            return None
        
        try:
            # 标准DID格式：did:wba:host%3Aport:wba:user_type:user_id
            pattern = r"did:(\w+):([^:]+):(\w+):(\w+):(.+)"
            match = re.match(pattern, did)
            
            if not match:
                logger.warning(f"DID格式不匹配: {did}")
                return None
            
            method1, host_port, method2, user_type, user_id = match.groups()
            
            # 验证方法名一致性
            if method1 != method2:
                logger.warning(f"DID方法名不一致: {method1} != {method2}")
                return None
            
            # 解析主机和端口（处理%3A编码）
            host, port = self._parse_host_port(host_port)
            
            result = {
                'method': method1,
                'host': host,
                'port': str(port),
                'user_type': user_type,
                'user_id': user_id,
                'original_did': did
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析DID失败: {did}, 错误: {e}")
            return None
    
    def _parse_host_port(self, host_port: str) -> Tuple[str, int]:
        """
        解析主机端口字符串（支持%3A编码）
        
        Args:
            host_port: 主机端口字符串，如 "localhost%3A9527"
            
        Returns:
            Tuple[str, int]: (主机, 端口)
        """
        try:
            # 处理%3A编码
            if '%3A' in host_port:
                host, port_str = host_port.split('%3A', 1)
                port = int(port_str)
                return host, port
            
            # 处理标准冒号分隔（向后兼容）
            if ':' in host_port:
                host, port_str = host_port.rsplit(':', 1)
                port = int(port_str)
                return host, port
            
            # 没有端口信息，使用默认端口
            return host_port, 80
            
        except ValueError as e:
            logger.warning(f"解析主机端口失败: {host_port}, 错误: {e}")
            return host_port, 80
    
    def normalize_did(self, did: str) -> str:
        """
        标准化DID格式（确保使用%3A编码）
        
        Args:
            did: 原始DID字符串
            
        Returns:
            str: 标准化的DID字符串
        """
        parsed = self.parse_did(did)
        if not parsed:
            return did
        
        # 重新格式化为标准格式
        return self.format_did(
            parsed['host'],
            int(parsed['port']),
            parsed['user_type'],
            parsed['user_id']
        )
    
    def can_create_user_type(self, user_type: str) -> bool:
        """
        检查用户类型是否可以创建
        
        Args:
            user_type: 用户类型
            
        Returns:
            bool: 是否可以创建
        """
        try:
            creatable_types = self.config.did_config.creatable_user_types
            return user_type in creatable_types
        except AttributeError:
            # 配置中没有相关设置，默认只允许创建user类型
            return user_type == "user"
    
    def get_host_port_from_request(self, request) -> Tuple[str, int]:
        """
        从请求中获取主机和端口
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Tuple[str, int]: (主机, 端口)
        """
        return self.domain_manager.get_host_port_from_request(request)
    
    def get_data_paths(self, host: str, port: int) -> Dict[str, Path]:
        """
        获取指定主机端口的数据路径
        
        Args:
            host: 主机名
            port: 端口
            
        Returns:
            Dict[str, Path]: 数据路径字典
        """
        return self.domain_manager.get_all_data_paths(host, port)
    
    def validate_agent_identity(self, agent_identity: Dict) -> Tuple[bool, str]:
        """
        验证Agent身份信息
        
        Args:
            agent_identity: Agent身份信息字典
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查必需字段
            required_fields = ['name', 'unique_id', 'did', 'type', 'host', 'port']
            for field in required_fields:
                if field not in agent_identity:
                    return False, f"缺少必需字段: {field}"
                if not agent_identity[field]:
                    return False, f"字段不能为空: {field}"
            
            # 验证DID格式
            did = agent_identity['did']
            parsed = self.parse_did(did)
            if not parsed:
                return False, f"DID格式无效: {did}"
            
            # 验证DID组件一致性
            if parsed['host'] != agent_identity['host']:
                return False, f"DID中的主机与身份信息不一致"
            
            if parsed['port'] != str(agent_identity['port']):
                return False, f"DID中的端口与身份信息不一致"
            
            if parsed['user_type'] != agent_identity['type']:
                return False, f"DID中的用户类型与身份信息不一致"
            
            if parsed['user_id'] != agent_identity['unique_id']:
                return False, f"DID中的用户ID与身份信息不一致"
            
            # 验证域名支持
            host = agent_identity['host']
            port = int(agent_identity['port'])
            valid_domain, domain_error = self.domain_manager.validate_domain_access(host, port)
            if not valid_domain:
                return False, f"域名验证失败: {domain_error}"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证过程中发生错误: {e}"
    
    def _generate_unique_id(self, length: int = 16) -> str:
        """
        生成唯一标识符
        
        Args:
            length: 标识符长度
            
        Returns:
            str: 唯一标识符
        """
        return secrets.token_hex(length // 2)
    
    def _get_format_template(self) -> str:
        """获取DID格式模板"""
        try:
            return self.config.did_config.format_template
        except AttributeError:
            return "did:{method}:{host}:{method}:{user_type}:{user_id}"
    
    def _get_method(self) -> str:
        """获取DID方法名"""
        try:
            return self.config.did_config.method
        except AttributeError:
            return "wba"
    
    def _is_standard_port(self, port: int) -> bool:
        """
        检查是否为标准端口（80, 443）
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否为标准端口
        """
        return port in [80, 443]
    
    def get_supported_user_types(self) -> List[str]:
        """
        获取支持的用户类型列表
        
        Returns:
            List[str]: 用户类型列表
        """
        try:
            user_types = self.config.did_config.user_types
            if hasattr(user_types, 'user'):
                return [user_types.user, user_types.hostuser, user_types.test]
            elif hasattr(user_types, 'values'):
                # 如果是字典格式
                return list(user_types.values())
            elif hasattr(user_types, '__iter__') and not isinstance(user_types, str):
                # 如果是可迭代对象（如ConfigNode）
                try:
                    return list(user_types)
                except:
                    # 如果转换失败，尝试获取属性
                    result = []
                    for attr in ['user', 'hostuser', 'tests']:
                        if hasattr(user_types, attr):
                            result.append(getattr(user_types, attr))
                    return result if result else ["user", "hostuser", "tests"]
            else:
                return ["user", "hostuser", "tests"]
        except AttributeError:
            return ["user", "hostuser", "tests"]
    
    def get_creatable_user_types(self) -> List[str]:
        """
        获取可创建的用户类型列表
        
        Returns:
            List[str]: 可创建的用户类型列表
        """
        try:
            return list(self.config.did_config.creatable_user_types)
        except AttributeError:
            return ["user"]
    
    def validate_did_format(self, did: str) -> Tuple[bool, str]:
        """
        验证DID格式是否正确
        
        Args:
            did: DID字符串
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not did:
            return False, "DID不能为空"
        
        parsed = self.parse_did(did)
        if not parsed:
            return False, "DID格式无效"
        
        # 检查方法名
        expected_method = self._get_method()
        if parsed['method'] != expected_method:
            return False, f"DID方法名错误，期望: {expected_method}, 实际: {parsed['method']}"
        
        # 检查用户类型
        supported_types = self.get_supported_user_types()
        if parsed['user_type'] not in supported_types:
            return False, f"不支持的用户类型: {parsed['user_type']}"
        
        # 检查域名支持
        host = parsed['host']
        port = int(parsed['port'])
        if not self.domain_manager.is_supported_domain(host, port):
            return False, f"不支持的域名: {host}:{port}"
        
        return True, ""
    
    def get_did_stats(self) -> Dict:
        """
        获取DID使用统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {
            'format_template': self._get_format_template(),
            'method': self._get_method(),
            'supported_user_types': self.get_supported_user_types(),
            'creatable_user_types': self.get_creatable_user_types(),
            'cache_size': len(self._format_cache)
        }
        
        # 添加域名统计
        domain_stats = self.domain_manager.get_domain_stats()
        stats.update(domain_stats)
        
        return stats


# 全局DID格式管理器实例
_did_format_manager = None

def get_did_format_manager() -> DidFormatManager:
    """
    获取全局DID格式管理器实例
    
    Returns:
        DidFormatManager: DID格式管理器实例
    """
    global _did_format_manager
    if _did_format_manager is None:
        _did_format_manager = DidFormatManager()
    return _did_format_manager
