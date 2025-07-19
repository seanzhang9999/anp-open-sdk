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
域名管理器

提供基于Host头的多域名路由和数据路径管理功能
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse

from anp_foundation.config import get_global_config

logger = logging.getLogger(__name__)

class DomainManager:
    """域名管理器 - 处理多域名路由和数据路径分配"""
    
    def __init__(self):
        """初始化域名管理器"""
        self.config = get_global_config()
        self._supported_domains = None
        self._domain_config_cache = {}
        
    @property
    def supported_domains(self) -> Dict[str, int]:
        """获取支持的域名列表"""
        if self._supported_domains is None:
            try:
                hosts_config = self.config.did_config.hosts
                
                # 如果是ConfigNode对象，需要转换为字典
                if hasattr(hosts_config, '_data'):
                    self._supported_domains = hosts_config._data
                elif hasattr(hosts_config, '__dict__'):
                    # 尝试从对象属性构建字典
                    self._supported_domains = {}
                    for attr_name in dir(hosts_config):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(hosts_config, attr_name)
                                if isinstance(attr_value, int):
                                    self._supported_domains[attr_name.replace('_', '.')] = attr_value
                            except:
                                continue
                else:
                    # 假设是普通字典
                    self._supported_domains = hosts_config
                    
            except AttributeError:
                # 如果配置中没有did_config，使用默认值
                logger.warning("配置中未找到did_config.hosts，使用默认域名配置")
                self._supported_domains = {
                    "localhost": 9527,
                    "user.localhost": 9527,
                    "service.localhost": 9527
                }
        return self._supported_domains
    
    def parse_host_header(self, host_header: str) -> Tuple[str, int]:
        """
        解析Host头，提取域名和端口
        
        Args:
            host_header: HTTP Host头的值，如 "user.localhost:9527"
            
        Returns:
            Tuple[str, int]: (域名, 端口)
        """
        if not host_header:
            return self._get_default_host_port()
        
        try:
            # 处理IPv6地址的情况
            if host_header.startswith('['):
                # IPv6格式: [::1]:9527
                if ']:' in host_header:
                    host, port_str = host_header.rsplit(']:', 1)
                    host = host[1:]  # 移除开头的 [
                    port = int(port_str)
                else:
                    host = host_header[1:-1]  # 移除 [ ]
                    port = 80
            else:
                # IPv4或域名格式
                if ':' in host_header:
                    host, port_str = host_header.rsplit(':', 1)
                    try:
                        port = int(port_str)
                    except ValueError:
                        # 端口不是数字，可能是IPv6地址
                        host = host_header
                        port = 80
                else:
                    host = host_header
                    port = 80
            
            return host, port
            
        except Exception as e:
            logger.warning(f"解析Host头失败: {host_header}, 错误: {e}")
            return self._get_default_host_port()
    
    def _get_default_host_port(self) -> Tuple[str, int]:
        """获取默认的主机和端口"""
        try:
            default_host = self.config.did_config.parsing.default_host
            default_port = self.config.did_config.parsing.default_port
            return default_host, default_port
        except AttributeError:
            return "localhost", 9527
    
    def is_supported_domain(self, domain: str, port: int = None) -> bool:
        """
        检查域名是否被支持
        
        Args:
            domain: 域名
            port: 端口（可选）
            
        Returns:
            bool: 是否支持该域名
        """
        try:
            supported = self.supported_domains
            
            # 检查配置对象类型
            if hasattr(supported, '__iter__') and not isinstance(supported, str):
                # 如果是字典类型
                if hasattr(supported, 'get'):
                    if domain in supported:
                        if port is None:
                            return True
                        return supported[domain] == port
                # 如果是列表类型
                else:
                    return domain in supported
            
            # 默认支持localhost相关域名
            return domain in ['localhost', '127.0.0.1', '::1'] or domain.endswith('.localhost')
            
        except Exception as e:
            logger.error(f"检查域名支持时出错: {e}")
            return domain in ['localhost', '127.0.0.1', '::1'] or domain.endswith('.localhost')
    
    def get_data_path_for_domain(self, domain: str, port: int) -> str:
        """
        获取指定域名的数据路径
        
        Args:
            domain: 域名
            port: 端口
            
        Returns:
            str: 数据路径，如 "data_user/user.localhost_9527/"
        """
        # 标准化域名（移除特殊字符）
        safe_domain = domain.replace('.', '_').replace(':', '_')
        return f"data_user/{safe_domain}_{port}"
    
    def get_domain_config(self, domain: str) -> Dict:
        """
        获取域名的配置信息
        
        Args:
            domain: 域名
            
        Returns:
            Dict: 域名配置
        """
        if domain in self._domain_config_cache:
            return self._domain_config_cache[domain]
        
        config = {
            'domain': domain,
            'supported': domain in self.supported_domains,
            'port': self.supported_domains.get(domain, 80),
            'data_path': self.get_data_path_for_domain(domain, self.supported_domains.get(domain, 80))
        }
        
        self._domain_config_cache[domain] = config
        return config
    
    def get_all_data_paths(self, domain: str, port: int) -> Dict[str, Path]:
        """
        获取指定域名的所有数据路径
        
        Args:
            domain: 域名
            port: 端口
            
        Returns:
            Dict[str, Path]: 包含各种数据路径的字典
        """
        try:
            # 使用UnifiedConfig的标准路径解析功能
            from anp_foundation.config.unified_config import UnifiedConfig
            
            # 构建相对于APP_ROOT的数据路径
            data_path_template = f"{{APP_ROOT}}/{self.get_data_path_for_domain(domain, port)}"
            base_path = UnifiedConfig.resolve_path(data_path_template)
            
            # 构建各种路径
            paths = {
                'base_path': base_path,
                'user_did_path': base_path / 'anp_users',
                'user_hosted_path': base_path / 'anp_users_hosted', 
                'agents_cfg_path': base_path / 'agents_config'
            }
            
            return paths
            
        except Exception as e:
            logger.error(f"获取数据路径失败: {e}")
            # 回退策略：使用当前工作目录
            try:
                app_root = UnifiedConfig.get_app_root()
            except RuntimeError:
                app_root = Path.cwd()
                logger.warning("UnifiedConfig未初始化，使用当前工作目录作为app_root")
            
            base_path = app_root / self.get_data_path_for_domain(domain, port)
            return {
                'base_path': base_path,
                'user_did_path': base_path / 'anp_users',
                'user_hosted_path': base_path / 'anp_users_hosted',
                'agents_cfg_path': base_path / 'agents_config'
            }
    
    def ensure_domain_directories(self, domain: str, port: int) -> bool:
        """
        确保域名对应的目录结构存在
        
        Args:
            domain: 域名
            port: 端口
            
        Returns:
            bool: 是否成功创建目录
        """
        try:
            paths = self.get_all_data_paths(domain, port)
            
            for path_name, path in paths.items():
                if path_name != 'base_path':  # base_path会在创建子目录时自动创建
                    path.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"确保目录存在: {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建域名目录失败: {e}")
            return False
    
    def get_host_port_from_request(self, request) -> Tuple[str, int]:
        """
        从HTTP请求中提取主机和端口信息
        
        Args:
            request: HTTP请求对象（FastAPI Request或类似对象）
            
        Returns:
            Tuple[str, int]: (主机, 端口)
        """
        try:
            # 尝试从Host头获取
            host_header = None
            if hasattr(request, 'headers'):
                host_header = request.headers.get('Host')
            elif hasattr(request, 'META'):
                # Django风格
                host_header = request.META.get('HTTP_HOST')
            
            if host_header:
                return self.parse_host_header(host_header)
            
            # 回退到请求URL
            if hasattr(request, 'url'):
                parsed = urlparse(str(request.url))
                host = parsed.hostname or 'localhost'
                port = parsed.port or 80
                return host, port
            
            # 最后的回退
            return self._get_default_host_port()
            
        except Exception as e:
            logger.warning(f"从请求中提取主机端口失败: {e}")
            return self._get_default_host_port()
    
    def validate_domain_access(self, domain: str, port: int) -> Tuple[bool, str]:
        """
        验证域名访问权限
        
        Args:
            domain: 域名
            port: 端口
            
        Returns:
            Tuple[bool, str]: (是否允许访问, 错误信息)
        """
        if not self.is_supported_domain(domain, port):
            return False, f"不支持的域名: {domain}:{port}"
        
        # 检查是否是不安全的域名（仅在非生产环境允许）
        try:
            insecure_patterns = self.config.did_config.insecure_patterns
            allow_insecure = self.config.did_config.parsing.allow_insecure
            
            if not allow_insecure:
                for pattern in insecure_patterns:
                    if self._match_pattern(f"{domain}:{port}", pattern):
                        return False, f"不安全的域名访问被禁止: {domain}:{port}"
        except AttributeError:
            # 配置中没有相关设置，允许访问
            pass
        
        return True, ""
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """
        简单的模式匹配（支持*通配符）
        
        Args:
            text: 要匹配的文本
            pattern: 模式字符串
            
        Returns:
            bool: 是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def get_domain_stats(self) -> Dict:
        """
        获取域名使用统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            supported = self.supported_domains
            
            # 安全地获取域名数量和列表
            if hasattr(supported, '__len__'):
                try:
                    domain_count = len(supported)
                except:
                    domain_count = 0
            else:
                domain_count = 0
            
            if hasattr(supported, 'keys'):
                try:
                    domain_list = list(supported.keys())
                except:
                    domain_list = []
            elif hasattr(supported, '__iter__') and not isinstance(supported, str):
                try:
                    domain_list = list(supported)
                except:
                    domain_list = []
            else:
                domain_list = []
            
            stats = {
                'supported_domains': domain_count,
                'domains': domain_list,
                'cache_size': len(self._domain_config_cache)
            }
            
            # 检查各域名的数据目录状态
            domain_status = {}
            if hasattr(supported, 'items'):
                try:
                    for domain, port in supported.items():
                        paths = self.get_all_data_paths(domain, port)
                        domain_status[f"{domain}:{port}"] = {
                            'base_exists': paths['base_path'].exists(),
                            'users_exists': paths['user_did_path'].exists(),
                            'agents_exists': paths['agents_cfg_path'].exists()
                        }
                except:
                    pass
            
            stats['domain_status'] = domain_status
            return stats
            
        except Exception as e:
            logger.error(f"获取域名统计失败: {e}")
            return {
                'supported_domains': 0,
                'domains': [],
                'cache_size': len(self._domain_config_cache),
                'domain_status': {}
            }


# 全局域名管理器实例
_domain_manager = None

def get_domain_manager() -> DomainManager:
    """
    获取全局域名管理器实例
    
    Returns:
        DomainManager: 域名管理器实例
    """
    global _domain_manager
    if _domain_manager is None:
        _domain_manager = DomainManager()
    return _domain_manager
