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
URL分析器

提供URL模式匹配和DID推断功能，用于从HTTP请求URL中智能推断resp_did
"""

import logging
import re
from typing import Dict, Optional, Tuple
from urllib.parse import unquote

from anp_sdk.domain import get_domain_manager
from .did_format_manager import get_did_format_manager

logger = logging.getLogger(__name__)

class UrlAnalyzer:
    """URL分析器 - 从URL中推断DID和相关信息"""
    
    def __init__(self):
        """初始化URL分析器"""
        self.domain_manager = get_domain_manager()
        self.did_manager = get_did_format_manager()
        self._pattern_cache = {}
        
    def infer_resp_did_from_url(self, request) -> Optional[str]:
        """
        从HTTP请求URL中推断resp_did
        
        Args:
            request: HTTP请求对象（FastAPI Request或类似对象）
            
        Returns:
            Optional[str]: 推断出的resp_did，如果无法推断则返回None
        """
        try:
            # 获取URL路径和域名信息
            path = self._get_path_from_request(request)
            host, port = self.domain_manager.get_host_port_from_request(request)
            
            if not path:
                logger.debug("无法从请求中获取URL路径")
                return None
            
            # 解析URL模式
            pattern_info = self.parse_url_pattern(path)
            if not pattern_info:
                logger.debug(f"无法识别URL模式: {path}")
                return None
            
            # 根据模式类型推断DID
            did = self._infer_did_from_pattern(pattern_info, host, port)
            
            if did:
                # 验证推断出的DID
                if self.validate_inferred_did(did):
                    logger.debug(f"成功从URL推断resp_did: {path} -> {did}")
                    return did
                else:
                    logger.warning(f"推断出的DID验证失败: {did}")
            
            return None
            
        except Exception as e:
            logger.warning(f"URL推断resp_did失败: {e}")
            return None
    
    def parse_url_pattern(self, path: str) -> Optional[Dict[str, str]]:
        """
        解析URL路径，识别模式类型
        
        Args:
            path: URL路径，如 "/wba/user/3ea884878ea5fbb1/did.json"
            
        Returns:
            Optional[Dict[str, str]]: 模式信息字典，包含pattern_type, user_type, user_info等
        """
        if not path:
            return None
        
        # 缓存检查
        if path in self._pattern_cache:
            return self._pattern_cache[path]
        
        result = None
        
        # 模式1: /wba/user/{user_id_or_did}/{file}
        if path.startswith("/wba/user/"):
            result = self._parse_wba_user_pattern(path)
        
        # 模式2: /wba/hostuser/{user_id}/{file}
        elif path.startswith("/wba/hostuser/"):
            result = self._parse_wba_hostuser_pattern(path)
        
        # 模式3: /agent/api/{did}/{endpoint} (如果存在)
        elif path.startswith("/agent/api/"):
            result = self._parse_agent_api_pattern(path)
        
        # 模式4: /wba/tests/{test_name}/{file} (测试用户)
        elif path.startswith("/wba/tests/"):
            result = self._parse_wba_test_pattern(path)
        
        # 缓存结果
        if result:
            self._pattern_cache[path] = result
        
        return result
    
    def _parse_wba_user_pattern(self, path: str) -> Optional[Dict[str, str]]:
        """解析 /wba/user/ 模式"""
        # 匹配: /wba/user/{user_info}/{file}
        pattern = r"^/wba/user/([^/]+)/(.+)$"
        match = re.match(pattern, path)
        
        if not match:
            return None
        
        user_info, file_part = match.groups()
        
        # 判断user_info的类型
        if self._is_encoded_did(user_info):
            # 已编码的完整DID
            return {
                'pattern_type': 'wba_user_encoded_did',
                'user_type': 'user',
                'user_info': user_info,
                'file_part': file_part,
                'info_type': 'encoded_did'
            }
        elif self._is_user_id(user_info):
            # 16位hex的user_id
            return {
                'pattern_type': 'wba_user_id',
                'user_type': 'user',
                'user_info': user_info,
                'file_part': file_part,
                'info_type': 'user_id'
            }
        
        return None
    
    def _parse_wba_hostuser_pattern(self, path: str) -> Optional[Dict[str, str]]:
        """解析 /wba/hostuser/ 模式"""
        # 匹配: /wba/hostuser/{user_id}/{file}
        pattern = r"^/wba/hostuser/([^/]+)/(.+)$"
        match = re.match(pattern, path)
        
        if not match:
            return None
        
        user_id, file_part = match.groups()
        
        # hostuser通常只接受user_id格式
        if self._is_user_id(user_id):
            return {
                'pattern_type': 'wba_hostuser',
                'user_type': 'hostuser',
                'user_info': user_id,
                'file_part': file_part,
                'info_type': 'user_id'
            }
        
        return None
    
    def _parse_wba_test_pattern(self, path: str) -> Optional[Dict[str, str]]:
        """解析 /wba/tests/ 模式"""
        # 匹配: /wba/tests/{test_name}/{file}
        pattern = r"^/wba/tests/([^/]+)/(.+)$"
        match = re.match(pattern, path)
        
        if not match:
            return None
        
        test_name, file_part = match.groups()
        
        return {
            'pattern_type': 'wba_test',
            'user_type': 'tests',
            'user_info': test_name,
            'file_part': file_part,
            'info_type': 'test_name'
        }
    
    def _parse_agent_api_pattern(self, path: str) -> Optional[Dict[str, str]]:
        """解析 /agent/api/ 模式"""
        # 匹配: /agent/api/{did}/{endpoint}
        pattern = r"^/agent/api/([^/]+)(/.*)?$"
        match = re.match(pattern, path)
        
        if not match:
            return None
        
        did_part, endpoint = match.groups()
        
        if self._is_encoded_did(did_part):
            return {
                'pattern_type': 'agent_api',
                'user_type': 'unknown',  # 需要从DID中解析
                'user_info': did_part,
                'file_part': endpoint or '',
                'info_type': 'encoded_did'
            }
        
        return None
    
    def _infer_did_from_pattern(self, pattern_info: Dict[str, str], host: str, port: int) -> Optional[str]:
        """
        根据模式信息推断DID
        
        Args:
            pattern_info: 模式信息
            host: 主机名
            port: 端口
            
        Returns:
            Optional[str]: 推断出的DID
        """
        info_type = pattern_info.get('info_type')
        user_info = pattern_info.get('user_info')
        user_type = pattern_info.get('user_type')
        
        # 检查必需的字段
        if not user_info:
            logger.warning("模式信息中缺少user_info")
            return None
        
        if info_type == 'encoded_did':
            # 已编码的DID，直接解码
            try:
                decoded_did = unquote(user_info)
                # 验证解码后的DID格式
                if decoded_did.startswith('did:'):
                    return decoded_did
            except Exception as e:
                logger.warning(f"解码DID失败: {user_info}, 错误: {e}")
                return None
        
        elif info_type == 'user_id':
            # user_id，需要构造完整DID
            if not user_type:
                logger.warning("模式信息中缺少user_type")
                return None
            try:
                return self.did_manager.format_did(host, port, user_type, user_info)
            except Exception as e:
                logger.warning(f"构造DID失败: {user_type}:{user_info}, 错误: {e}")
                return None
        
        elif info_type == 'test_name':
            # 测试用户名，构造测试DID
            try:
                return self.did_manager.format_did(host, port, 'tests', user_info)
            except Exception as e:
                logger.warning(f"构造测试DID失败: {user_info}, 错误: {e}")
                return None
        
        return None
    
    def _is_encoded_did(self, text: str) -> bool:
        """检查文本是否是编码的DID"""
        if not text:
            return False
        
        # 检查是否包含DID的编码特征
        # did: -> did%3A
        # : -> %3A
        return ('did%3A' in text.lower() or 
                text.lower().startswith('did:') or
                '%3A' in text)
    
    def _is_user_id(self, text: str) -> bool:
        """检查文本是否是16位hex的user_id"""
        if not text or len(text) != 16:
            return False
        
        # 检查是否全部是hex字符
        try:
            int(text, 16)
            return True
        except ValueError:
            return False
    
    def validate_inferred_did(self, did: str) -> bool:
        """
        验证推断出的DID是否有效
        
        Args:
            did: 推断出的DID
            
        Returns:
            bool: 是否有效
        """
        if not did:
            return False
        
        try:
            # 使用DID格式管理器验证
            valid, error_msg = self.did_manager.validate_did_format(did)
            if not valid:
                logger.debug(f"DID格式验证失败: {did}, 错误: {error_msg}")
                return False
            
            # 解析DID获取域名信息
            parsed = self.did_manager.parse_did(did)
            if not parsed:
                logger.debug(f"DID解析失败: {did}")
                return False
            
            # 验证域名支持
            host = parsed['host']
            port = int(parsed['port'])
            if not self.domain_manager.is_supported_domain(host, port):
                logger.debug(f"DID中的域名不受支持: {host}:{port}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"验证DID时出错: {did}, 错误: {e}")
            return False
    
    def _get_path_from_request(self, request) -> Optional[str]:
        """从请求对象中获取URL路径"""
        try:
            if hasattr(request, 'url') and hasattr(request.url, 'path'):
                return request.url.path
            elif hasattr(request, 'path'):
                return request.path
            elif hasattr(request, 'path_info'):
                # WSGI风格
                return request.path_info
            else:
                logger.warning("无法从请求对象中获取URL路径")
                return None
        except Exception as e:
            logger.warning(f"获取请求路径时出错: {e}")
            return None
    
    def extract_user_info_from_path(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从路径中提取用户类型和用户信息
        
        Args:
            path: URL路径
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (用户类型, 用户信息)
        """
        pattern_info = self.parse_url_pattern(path)
        if not pattern_info:
            return None, None
        
        return pattern_info.get('user_type'), pattern_info.get('user_info')
    
    def get_supported_patterns(self) -> Dict[str, str]:
        """
        获取支持的URL模式列表
        
        Returns:
            Dict[str, str]: 模式名称到描述的映射
        """
        return {
            'wba_user_id': '/wba/user/{16位hex用户ID}/{文件名} - 通过用户ID访问',
            'wba_user_encoded_did': '/wba/user/{编码的DID}/{文件名} - 通过完整DID访问',
            'wba_hostuser': '/wba/hostuser/{用户ID}/{文件名} - 访问托管用户',
            'wba_test': '/wba/tests/{测试名称}/{文件名} - 访问测试用户',
            'agent_api': '/agent/api/{编码的DID}/{端点} - Agent API访问'
        }
    
    def get_analysis_stats(self) -> Dict:
        """
        获取URL分析统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'supported_patterns': len(self.get_supported_patterns()),
            'cache_size': len(self._pattern_cache),
            'patterns': list(self.get_supported_patterns().keys())
        }


# 全局URL分析器实例
_url_analyzer = None

def get_url_analyzer() -> UrlAnalyzer:
    """
    获取全局URL分析器实例
    
    Returns:
        UrlAnalyzer: URL分析器实例
    """
    global _url_analyzer
    if _url_analyzer is None:
        _url_analyzer = UrlAnalyzer()
    return _url_analyzer
