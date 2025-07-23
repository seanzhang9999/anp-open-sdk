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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANP用户工具

这个程序提供了ANP用户管理的基本功能：
1. 创建新用户 (-n)
2. 列出所有用户 (-l)
3. 按服务器信息排序显示用户 (-s)
"""

import json
import logging
import os
import secrets
import shutil
from datetime import datetime

import yaml
from Crypto.PublicKey import RSA
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from anp_foundation.did.did_tool import create_jwt, verify_jwt, parse_wba_did_host_port

logger = logging.getLogger(__name__)
from typing import Dict, List, Optional, Any, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa


from anp_foundation.config import get_global_config, UnifiedConfig


class LocalUserData():
    def __init__(self, folder_name: str, agent_cfg: Dict[str, Any], did_doc: Dict[str, Any], did_doc_path, password_paths: Dict[str, str], user_folder_path):
        self.folder_name = folder_name
        self.agent_cfg = agent_cfg
        self.did_document = did_doc
        self.password_paths = password_paths
        self.did = did_doc.get("id")
        self.name = agent_cfg.get("name")
        self.unique_id = agent_cfg.get("unique_id")
        self.user_dir = user_folder_path
        self._did_doc_path = did_doc_path

        self._did_private_key_file_path = password_paths.get("did_private_key_file_path")
        self.did_public_key_file_path = password_paths.get("did_public_key_file_path")
        self.jwt_private_key_file_path = password_paths.get("jwt_private_key_file_path")
        self.jwt_public_key_file_path = password_paths.get("jwt_public_key_file_path")
        self.key_id = did_doc.get('key_id') or did_doc.get('publicKey', [{}])[0].get('id') if did_doc.get('publicKey') else None

        self.token_to_remote_dict = {}
        self.token_from_remote_dict = {}
        self.contacts = {}


        # [新] 托管DID相关属性
        self.is_hosted_did: bool = folder_name.startswith('user_hosted_')
        self.parent_did: Optional[str] = agent_cfg.get('hosted_config', {}).get('parent_did') if self.is_hosted_did else None
        self.hosted_info: Optional[Dict[str, Any]] = self._parse_hosted_info_from_name(folder_name) if self.is_hosted_did else None


        # --- 新增代码：用于持有内存中的密钥对象 ---
        self.did_private_key: Optional[ec.EllipticCurvePrivateKey] = None
        self.jwt_private_key: Optional[rsa.RSAPrivateKey] = None
        self.jwt_public_key: Optional[rsa.RSAPublicKey] = None

        # --- 新增代码：在初始化时，自动调用加载方法 ---
        self._load_keys_to_memory()

    def _load_keys_to_memory(self):
        """
        [新增] 这是一个内部辅助方法，在对象初始化时被调用。
        它会根据已有的文件路径，尝试将密钥文件加载为内存对象。
        """
        # 在方法内部导入以避免循环依赖问题

        try:
            # 加载 DID 私钥
            if self.did_private_key_file_path and os.path.exists(self.did_private_key_file_path):
                self.did_private_key = load_private_key(self.did_private_key_file_path)

            # 加载 JWT 私钥
            if self.jwt_private_key_file_path and os.path.exists(self.jwt_private_key_file_path):
                self.jwt_private_key = load_private_key(self.jwt_private_key_file_path)

            # 加载 JWT 公钥
            if self.jwt_public_key_file_path and os.path.exists(self.jwt_public_key_file_path):
                with open(self.jwt_public_key_file_path, "rb") as f:
                    self.jwt_public_key = serialization.load_pem_public_key(f.read())
        except Exception as e:
            # 如果加载失败，只记录错误，不中断整个程序
            logger.error(f"为用户 {self.name} 加载密钥到内存时失败: {e}")


    def _parse_hosted_info_from_name(self, folder_name: str) -> Optional[Dict[str, Any]]:
        """[新增] 从目录名解析托管信息。"""
        if folder_name.startswith('user_hosted_'):
            parts = folder_name[12:].rsplit('_', 2)
            if len(parts) >= 2:
                if len(parts) == 3:
                    host, port, did_suffix = parts
                    return {'host': host, 'port': port, 'did_suffix': did_suffix}
                else:
                    host, port = parts
                    return {'host': host, 'port': port}
        return None
    @property
    def did_private_key_file_path(self) -> str:
        return self._did_private_key_file_path
    @property
    def did_doc_path(self) -> str:
        return self._did_doc_path

    def get_did(self) -> str:
        return self.did

    def get_private_key_path(self) -> str:
        return self.did_private_key_file_path

    def get_public_key_path(self) -> str:
        return self.did_public_key_file_path

    def get_token_to_remote(self, remote_did: str) -> Optional[Dict[str, Any]]:
        return self.token_to_remote_dict.get(remote_did)

    def store_token_to_remote(self, remote_did: str, token: str, expires_delta: int):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expires_delta)
        self.token_to_remote_dict[remote_did] = {
            "token": token,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_revoked": False,
            "req_did": remote_did
        }
    def get_token_from_remote(self, remote_did: str) -> Optional[Dict[str, Any]]:
        return self.token_from_remote_dict.get(remote_did)

    def store_token_from_remote(self, remote_did: str, token: str):
        from datetime import datetime
        now = datetime.now()
        self.token_from_remote_dict[remote_did] = {
            "token": token,
            "created_at": now.isoformat(),
            "req_did": remote_did
        }

    def add_contact(self, contact: Dict[str, Any]):
        did = contact.get("did")
        if did:
            self.contacts[did] = contact

    def get_contact(self, remote_did: str) -> Optional[Dict[str, Any]]:
        return self.contacts.get(remote_did)

    def list_contacts(self) -> List[Dict[str, Any]]:
        return list(self.contacts.values())



class LocalUserDataManager():
    _instance = None
    def __new__(cls, user_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, user_dir: Optional[str] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        config = get_global_config()
        self._user_dir = user_dir or config.anp_sdk.user_did_path

        # 提供多种索引方式，提高查询效率
        self.users_by_did: Dict[str, LocalUserData] = {}
        self.users_by_name: Dict[str, LocalUserData] = {}
        self.users: Dict[str, LocalUserData] = {}
        self.load_all_users()
        self._initialized = True
        self.users_by_host_port = {}  # 格式: {(host, port): {name: user_data}}


    def load_all_users(self):
        """
        [重构] 扫描用户目录，实例化LocalUserData，并建立索引。
        此方法将不再关心文件内容的具体解析。
        """
        if not os.path.isdir(self._user_dir):
            logger.warning(f"用户目录不存在: {self._user_dir}")
            return

        # 新增：用于记录冲突的用户
        self.conflicting_users = []
        # 清空现有索引
        self.users_by_did.clear()
        self.users_by_name.clear()
        self.users.clear()
        self.users_by_host_port = {}  # 新增：清空域名端口索引

        logger.info(f"开始从 {self._user_dir} 加载所有用户数据...")
        for entry in os.scandir(self._user_dir):
            if not entry.is_dir() or not (entry.name.startswith('user_') or entry.name.startswith('user_hosted_')):
                continue

            user_folder_path = entry.path
            folder_name = entry.name
            try:
                # --- 1. 准备构造 LocalUserData 所需的参数 ---
                cfg_path = os.path.join(user_folder_path, 'agent_cfg.yaml')
                did_doc_path = os.path.join(user_folder_path, 'did_document.json')

                if not (os.path.exists(cfg_path) and os.path.exists(did_doc_path)):
                    logger.warning(f"跳过不完整的用户目录 (缺少cfg或did_doc): {folder_name}")
                    continue

                with open(cfg_path, 'r', encoding='utf-8') as f:
                    agent_cfg = yaml.safe_load(f)

                with open(did_doc_path, 'r', encoding='utf-8') as f:
                    did_doc = json.load(f)

                # 确定 key_id 来构建密钥路径
                key_id = self.parse_key_id_from_did_doc(did_doc)

                if not key_id:
                    logger.warning(f"无法在 {folder_name} 的DID文档中确定key_id")
                    key_id = get_global_config().anp_sdk.user_did_key_id  # 使用默认值作为后备

                password_paths = {
                    "did_private_key_file_path": os.path.join(user_folder_path, f"{key_id}_private.pem"),
                    "did_public_key_file_path": os.path.join(user_folder_path, f"{key_id}_public.pem"),
                    "jwt_private_key_file_path": os.path.join(user_folder_path, 'private_key.pem'),
                    "jwt_public_key_file_path": os.path.join(user_folder_path, 'public_key.pem')
                }

                # --- 2. 实例化 LocalUserData ---
                # 所有文件加载和解析的复杂性都已封装在 LocalUserData 的 __init__ 中
                user_data = LocalUserData(folder_name, agent_cfg, did_doc, did_doc_path, password_paths,
                                          user_folder_path)
                # --- 3. 建立索引 ---
                if user_data.did:
                    # 提取域名和端口
                    from anp_foundation.did.did_tool import parse_wba_did_host_port
                    host, port = parse_wba_did_host_port(user_data.did)
                    
                    if host and port and user_data.name:
                        # 按域名端口分组
                        host_port_key = (host, port)
                        if host_port_key not in self.users_by_host_port:
                            self.users_by_host_port[host_port_key] = {}
                        
                        # 检查同一域名端口下是否有重名
                        if user_data.name in self.users_by_host_port[host_port_key]:
                            existing_user = self.users_by_host_port[host_port_key][user_data.name]
                            logger.error(f"用户名冲突: 域名端口 {host}:{port} 下已存在同名用户 '{user_data.name}'")
                            logger.error(f"冲突用户 DID: {existing_user.did} 和 {user_data.did}")
                            
                            # 记录冲突
                            self.conflicting_users.append({
                                'name': user_data.name,
                                'host': host,
                                'port': port,
                                'users': [existing_user.did, user_data.did]
                            })
                            
                            # 标记为有冲突
                            user_data.has_name_conflict = True
                            existing_user.has_name_conflict = True
                        
                        # 添加到域名端口索引
                        self.users_by_host_port[host_port_key][user_data.name] = user_data
                    
                    # 添加到DID索引
                    self.users_by_did[user_data.did] = user_data
                    
                    # 添加到名称索引
                    if user_data.name:
                        self.users_by_name[user_data.name] = user_data
                else:
                    logger.warning(f"用户 {folder_name} 加载成功但缺少DID，无法索引。")

            except Exception as e:
                logger.error(f"加载用户数据失败 ({folder_name}): {e}", exc_info=True)

         # 如果有冲突，输出汇总信息
        if self.conflicting_users:
            logger.warning(f"发现 {len(self.conflicting_users)} 个用户名冲突，请检查并解决")
            for conflict in self.conflicting_users:
                logger.warning(f"  - 域名端口 {conflict['host']}:{conflict['port']} 下的用户名 '{conflict['name']}' 有冲突")
        

        logger.info(f"加载完成，共 {len(self.users_by_did)} 个用户数据进入内存。")

        

    def parse_key_id_from_did_doc(self, did_doc):
        key_id = did_doc.get('key_id') or (
            did_doc.get('verificationMethod', [{}])[0].get('id', '').split('#')[-1] if did_doc.get(
                'verificationMethod') else None)
        if not key_id:
            # 兼容旧版 publicKey 写法
            key_id = did_doc.get('publicKey', [{}])[0].get('id').split('#')[-1] if did_doc.get(
                'publicKey') else None
        return key_id

    def is_username_taken(self, name: str, host: str, port: int) -> bool:
        """检查指定域名端口下用户名是否已被使用"""
        host_port_key = (host, port)
        if host_port_key in self.users_by_host_port:
            return name in self.users_by_host_port[host_port_key]
        return False
    def create_hosted_user(self, parent_user_data: 'LocalUserData', host: str, port: str, did_document: dict) -> Tuple[bool, Optional['LocalUserData']]:
        """
        [新] 创建一个托管用户，并将其持久化到文件系统，然后加载到内存。
        """
        from pathlib import Path
        import re

        try:
            did_id = did_document.get('id', '')
            pattern = r"did:wba:[^:]+:[^:]+:[^:]+:([a-zA-Z0-9]{16})"
            match = re.search(pattern, did_id)
            did_suffix = match.group(1) if match else "unknown_id"

            original_user_dir = Path(parent_user_data.user_dir)
            parent_dir = original_user_dir.parent
            clean_host = host.replace(".", "_").replace(":", "_")
            hosted_dir_name = f"user_hosted_{clean_host}_{port}_{did_suffix}"
            hosted_dir_path = parent_dir / hosted_dir_name

            # --- 文件系统操作 ---
            hosted_dir_path.mkdir(parents=True, exist_ok=True)
            key_files = ['key-1_private.pem', 'key-1_public.pem', 'private_key.pem', 'public_key.pem']

            for key_file in key_files:
                src_path = original_user_dir / key_file
                if src_path.exists():
                    shutil.copy2(src_path, hosted_dir_path / key_file)

            did_doc_path = hosted_dir_path / 'did_document.json'
            with open(did_doc_path, 'w', encoding='utf-8') as f:
                json.dump(did_document, f, ensure_ascii=False, indent=2)

            agent_cfg = {
                'did': did_id,
                'unique_id': did_suffix,
                'name': f"hosted_{parent_user_data.name}_{host}_{port}",
                'hosted_config': {
                    'parent_did': parent_user_data.did,
                    'host': host,
                    'port': int(port),
                    'created_at': datetime.now().isoformat(),
                    'purpose': f"对外托管服务 - {host}:{port}"
                }
            }
            config_path = hosted_dir_path / 'agent_cfg.yaml'
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(agent_cfg, f, default_flow_style=False, allow_unicode=True)
            # --- 文件操作结束 ---

            # --- 动态加载新用户到内存 ---
            key_id = self.parse_key_id_from_did_doc(did_document)
            password_paths = {
                "did_private_key_file_path": str(hosted_dir_path / f"{key_id}_private.pem"),
                "did_public_key_file_path": str(hosted_dir_path / f"{key_id}_public.pem"),
                "jwt_private_key_file_path": str(hosted_dir_path / 'private_key.pem'),
                "jwt_public_key_file_path": str(hosted_dir_path / 'public_key.pem')
            }
            new_user_data = LocalUserData(
                hosted_dir_name, agent_cfg, did_document, str(did_doc_path), password_paths, str(hosted_dir_path)
            )
            self.users_by_did[new_user_data.did] = new_user_data
            if new_user_data.name:
                self.users_by_name[new_user_data.name] = new_user_data
            # --- 动态加载结束 ---

            logger.debug(f"托管DID创建并加载到内存成功: {hosted_dir_name}")
            return True, new_user_data

        except Exception as e:
            logger.error(f"创建托管DID文件夹失败: {e}")
            return False, None

    def get_user_data(self, did: str) -> Optional[LocalUserData]:
        """通过 DID 从内存中快速获取用户数据"""
        return self.users_by_did.get(did)

    def get_all_users(self) -> List[LocalUserData]:
        """获取所有已加载的用户数据列表"""
        return list(self.users_by_did.values())

    def get_user_data_by_name(self, name: str) -> Optional[LocalUserData]:
        """通过用户名称从内存中快速获取用户数据"""
        return self.users_by_name.get(name)

    def reload_all_users(self):
        """重新加载所有用户数据"""
        logger.info("重新加载所有用户数据...")

        # 清空现有索引
        self.users_by_did.clear()
        self.users_by_name.clear()
        self.users.clear()

        # 重新加载
        self.load_all_users()

        logger.info(f"重新加载完成，当前共有 {len(self.users_by_did)} 个用户")

    def add_user_to_memory(self, user_data: LocalUserData):
        """将新用户添加到内存索引中"""
        if user_data.did:
             # 添加到DID索引
            self.users_by_did[user_data.did] = user_data
        logger.debug(f"用户 {user_data.did} 已添加到内存索引")

        # 添加到域名端口索引
        from anp_foundation.did.did_tool import parse_wba_did_host_port
        host, port = parse_wba_did_host_port(user_data.did)
        if host and port and user_data.name:
            host_port_key = (host, port)
            if host_port_key not in self.users_by_host_port:
                self.users_by_host_port[host_port_key] = {}
            
            # 检查是否有冲突
            if user_data.name in self.users_by_host_port[host_port_key]:
                existing_user = self.users_by_host_port[host_port_key][user_data.name]
                logger.error(f"用户名冲突: 域名端口 {host}:{port} 下已存在同名用户 '{user_data.name}'")
                logger.error(f"冲突用户 DID: {existing_user.did} 和 {user_data.did}")
                
                # 标记为有冲突
                user_data.has_name_conflict = True
                existing_user.has_name_conflict = True
                
                # 记录冲突
                if not hasattr(self, 'conflicting_users'):
                    self.conflicting_users = []
                
                self.conflicting_users.append({
                    'name': user_data.name,
                    'host': host,
                    'port': port,
                    'users': [existing_user.did, user_data.did]
                })
            
            # 添加到域名端口索引
            self.users_by_host_port[host_port_key][user_data.name] = user_data

        # 添加到名称索引
        if user_data.name:
            self.users_by_name[user_data.name] = user_data
            logger.debug(f"用户名 {user_data.name} 已添加到内存索引")

    def remove_user_from_memory(self, did: str):
        """从内存索引中移除用户"""
        user_data = self.users_by_did.get(did)
        if user_data:
            # 从 DID 索引中移除
            self.users_by_did.pop(did, None)

        # 从域名端口索引中移除
        from anp_foundation.did.did_tool import parse_wba_did_host_port
        host, port = parse_wba_did_host_port(user_data.did)
        if host and port and user_data.name:
            host_port_key = (host, port)
            if host_port_key in self.users_by_host_port:
                self.users_by_host_port[host_port_key].pop(user_data.name, None)    
        # 从名称索引中移除
        if user_data.name:
            self.users_by_name.pop(user_data.name, None)

        logger.debug(f"用户 {did} 已从内存索引中移除")

    def load_single_user(self, user_folder_path: str) -> Optional[LocalUserData]:
        """加载单个用户到内存"""
        folder_name = os.path.basename(user_folder_path)

        try:
            # 检查必要文件
            cfg_path = os.path.join(user_folder_path, 'agent_cfg.yaml')
            did_doc_path = os.path.join(user_folder_path, 'did_document.json')

            if not (os.path.exists(cfg_path) and os.path.exists(did_doc_path)):
                logger.warning(f"用户目录不完整: {folder_name}")
                return None

            # 加载配置文件
            with open(cfg_path, 'r', encoding='utf-8') as f:
                agent_cfg = yaml.safe_load(f)

            with open(did_doc_path, 'r', encoding='utf-8') as f:
                did_doc = json.load(f)

            # 构建密钥路径
            key_id = self.parse_key_id_from_did_doc(did_doc)
            if not key_id:
                key_id = get_global_config().anp_sdk.user_did_key_id

            password_paths = {
                "did_private_key_file_path": os.path.join(user_folder_path, f"{key_id}_private.pem"),
                "did_public_key_file_path": os.path.join(user_folder_path, f"{key_id}_public.pem"),
                "jwt_private_key_file_path": os.path.join(user_folder_path, 'private_key.pem'),
                "jwt_public_key_file_path": os.path.join(user_folder_path, 'public_key.pem')
            }

            # 创建用户数据对象
            user_data = LocalUserData(
                folder_name, agent_cfg, did_doc, did_doc_path,
                password_paths, user_folder_path
            )

            # 添加到内存索引
            self.add_user_to_memory(user_data)

            logger.info(f"成功加载用户: {user_data.did}")
            return user_data

        except Exception as e:
            logger.error(f"加载单个用户失败 ({folder_name}): {e}", exc_info=True)
            return None

    def refresh_user(self, did: str) -> Optional[LocalUserData]:
        """刷新指定用户的数据"""
        user_data = self.users_by_did.get(did)
        if not user_data:
            logger.warning(f"用户 {did} 不在内存中，无法刷新")
            return None

        # 重新加载用户数据
        return self.load_single_user(user_data.user_dir)

    def scan_and_load_new_users(self):
        """扫描用户目录，加载新用户"""
        if not os.path.isdir(self._user_dir):
            return

        current_dids = set(self.users_by_did.keys())
        found_dids = set()

        for entry in os.scandir(self._user_dir):
            if not entry.is_dir() or not (entry.name.startswith('user_') or entry.name.startswith('user_hosted_')):
                continue

            try:
                did_doc_path = os.path.join(entry.path, 'did_document.json')
                if os.path.exists(did_doc_path):
                    with open(did_doc_path, 'r', encoding='utf-8') as f:
                        did_doc = json.load(f)

                    did = did_doc.get('id')
                    if did:
                        found_dids.add(did)

                        # 如果是新用户，加载到内存
                        if did not in current_dids:
                            logger.info(f"发现新用户: {did}")
                            self.load_single_user(entry.path)

            except Exception as e:
                logger.error(f"扫描用户目录时出错 ({entry.name}): {e}")

        # 检查是否有用户被删除
        deleted_dids = current_dids - found_dids
        for did in deleted_dids:
            logger.info(f"用户已被删除: {did}")
            self.remove_user_from_memory(did)
    @property
    def user_dir(self):
        return self._user_dir
    

    def get_conflicting_users(self) -> List[Dict[str, Any]]:
        """获取所有存在用户名冲突的用户信息"""
        return self.conflicting_users


    def resolve_username_conflict(self, did: str, new_name: str) -> bool:
        """
        解决用户名冲突
        
        Args:
            did: 需要更新名称的用户DID
            new_name: 新的用户名
            
        Returns:
            bool: 是否成功解决冲突
        """
        user_data = self.users_by_did.get(did)
        if not user_data:
            logger.error(f"找不到DID为 {did} 的用户")
            return False
            
        host, port = parse_wba_did_host_port(user_data.did)
        if not (host and port):
            logger.error(f"无法从DID {did} 解析出域名和端口")
            return False
            
        # 检查新名称是否可用
        if self.is_username_taken(new_name, host, port):
            logger.error(f"新用户名 '{new_name}' 在域名端口 {host}:{port} 下已存在")
            return False
            
        # 更新内存中的索引
        old_name = user_data.name
        host_port_key = (host, port)
        
        if host_port_key in self.users_by_host_port and old_name in self.users_by_host_port[host_port_key]:
            del self.users_by_host_port[host_port_key][old_name]
            self.users_by_host_port[host_port_key][new_name] = user_data
            
        if old_name in self.users_by_name:
            del self.users_by_name[old_name]
        self.users_by_name[new_name] = user_data
        
        # 更新用户数据
        user_data.name = new_name
        if hasattr(user_data, 'has_name_conflict'):
            delattr(user_data, 'has_name_conflict')
            
        # 更新配置文件
        try:
            cfg_path = os.path.join(user_data.user_dir, 'agent_cfg.yaml')
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                
                cfg['name'] = new_name
                
                with open(cfg_path, 'w', encoding='utf-8') as f:
                    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
                    
                logger.info(f"已将用户 {did} 的名称从 '{old_name}' 更新为 '{new_name}'")
                return True
        except Exception as e:
            logger.error(f"更新用户名失败: {e}")
            return False
# --- [新] 懒加载实现 ---
_user_data_manager_instance: Optional[LocalUserDataManager] = None
def get_user_data_manager() -> LocalUserDataManager:
    """
    获取 LocalUserDataManager 的全局单例。
    在首次调用时，会创建该实例。
    """
    global _user_data_manager_instance
    if _user_data_manager_instance is None:
        _user_data_manager_instance = LocalUserDataManager()
    return _user_data_manager_instance


def load_private_key(private_key_path: str, password: Optional[bytes] = None):
    """加载私钥"""
    try:
        with open(private_key_path, "rb") as f:
            private_key_data = f.read()
        return load_pem_private_key(private_key_data, password=password)
    except Exception as e:
        logger.error(f"加载私钥时出错: {str(e)}")
        return None
def refresh_user_data_manager():
    """刷新用户数据管理器 - 便捷函数"""
    manager = get_user_data_manager()
    manager.scan_and_load_new_users()
def reload_user_data_manager():
    """重新加载用户数据管理器 - 便捷函数"""
    manager = get_user_data_manager()
    manager.reload_all_users()
def force_reload_user_data_manager():
    """强制重新创建用户数据管理器实例"""
    global _user_data_manager_instance
    _user_data_manager_instance = None
    return get_user_data_manager()
def create_did_user(user_iput: dict, *, did_hex: bool = True, did_check_unique: bool = True):
    from agent_connect.authentication.did_wba import create_did_wba_document
    import json
    import os
    from datetime import datetime
    import re
    import urllib.parse



    required_fields = ['name', 'host', 'port', 'dir', 'type']
    if not all(field in user_iput for field in required_fields):
        logger.error("缺少必需的参数字段")
        return None
    config=get_global_config()

    userdid_filepath = config.anp_sdk.user_did_path
    userdid_filepath = UnifiedConfig.resolve_path(userdid_filepath)


    def get_existing_usernames(userdid_filepath):
        if not os.path.exists(userdid_filepath):
            return []
        usernames = []
        for d in os.listdir(userdid_filepath):
            if os.path.isdir(os.path.join(userdid_filepath, d)):
                cfg_path = os.path.join(userdid_filepath, d, 'agent_cfg.yaml')
                if os.path.exists(cfg_path):
                    with open(cfg_path, 'r') as f:
                        try:
                            cfg = yaml.safe_load(f)
                            if cfg and 'name' in cfg:
                                usernames.append(cfg['name'])
                        except:
                            pass
        return usernames

    base_name = user_iput['name']
    existing_names = get_existing_usernames(userdid_filepath)

    if base_name in existing_names:
        date_suffix = datetime.now().strftime('%Y%m%d')
        new_name = f"{base_name}_{date_suffix}"
        if new_name in existing_names:
            pattern = f"{re.escape(new_name)}_?(\\d+)?"
            matches = [re.match(pattern, name) for name in existing_names]
            numbers = [int(m.group(1)) if m and m.group(1) else 0 for m in matches if m]
            next_number = max(numbers + [0]) + 1
            new_name = f"{new_name}_{next_number}"
        user_iput['name'] = new_name
        logger.debug(f"用户名 {base_name} 已存在，使用新名称：{new_name}")

    # 在这里添加域名端口下用户名唯一性检查
    user_data_manager = get_user_data_manager()
    if user_data_manager.is_username_taken(user_iput['name'], user_iput['host'], int(user_iput['port'])):
        logger.error(f"用户名 '{user_iput['name']}' 在域名端口 {user_iput['host']}:{user_iput['port']} 下已存在")
        return None
    
    userdid_hostname = user_iput['host']
    userdid_port = int(user_iput['port'])
    unique_id = secrets.token_hex(8) if did_hex else None


    if userdid_port not in (80, 443):
        userdid_host_port = f"{userdid_hostname}%3A{userdid_port}"
    did_parts = ['did', 'wba', userdid_host_port]
    if user_iput['dir']:
        did_parts.append(urllib.parse.quote(user_iput['dir'], safe=''))
    if user_iput['type']:
        did_parts.append(urllib.parse.quote(user_iput['type'], safe=''))
    if did_hex:
        did_parts.append(unique_id)
    did_id = ':'.join(did_parts)

    if not did_hex and did_check_unique:
        for d in os.listdir(userdid_filepath):
            did_path = os.path.join(userdid_filepath, d, 'did_document.json')
            if os.path.exists(did_path):
                with open(did_path, 'r', encoding='utf-8') as f:
                    did_dict = json.load(f)
                    if did_dict.get('id') == did_id:
                        logger.error(f"DID已存在: {did_id}")
        return None

    user_dir_name = f"user_{unique_id}" if did_hex else f"user_{user_iput['name']}"
    userdid_filepath = os.path.join(userdid_filepath, user_dir_name)

    path_segments = [user_iput['dir'], user_iput['type']]
    if did_hex:
        path_segments.append(unique_id)
    agent_description_url = f"http://{userdid_hostname}:{userdid_port}/{user_iput['dir']}/{user_iput['type']}/{unique_id if did_hex else ''}/ad.json"

    did_document, keys = create_did_wba_document(
        hostname=userdid_hostname,
        port=userdid_port,
        path_segments=path_segments,
        agent_description_url=agent_description_url
        )
    did_document['id'] = did_id
    if keys:
        did_document['key_id'] = list(keys.keys())[0]

    os.makedirs(userdid_filepath, exist_ok=True)
    with open(f"{userdid_filepath}/did_document.json", "w") as f:
        json.dump(did_document, f, indent=4)

    for key_id, (private_key_pem, public_key_pem) in keys.items():
        with open(f"{userdid_filepath}/{key_id}_private.pem", "wb") as f:
            f.write(private_key_pem)
        with open(f"{userdid_filepath}/{key_id}_public.pem", "wb") as f:
            f.write(public_key_pem)

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_cfg = {
        "name": user_iput['name'],
        "unique_id": unique_id,
        "did": did_document["id"],
        "type": user_iput['type'],
        "owner": {"name": "anpsdk 创造用户", "@id": "https://localhost"},
        "description": "anpsdk的测试用户",
        "version": "0.1.0",
        "created_at": time
    }
    with open(f"{userdid_filepath}/agent_cfg.yaml", "w", encoding='utf-8') as f:
        yaml.dump(agent_cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    private_key = RSA.generate(2048).export_key()
    public_key = RSA.import_key(private_key).publickey().export_key()
    testcontent = {"user_id": 123}
    token = create_jwt(testcontent, private_key)
    token = verify_jwt(token, public_key)
    if testcontent["user_id"] == token["user_id"]:
        with open(f"{userdid_filepath}/private_key.pem", "wb") as f:
            f.write(private_key)
        with open(f"{userdid_filepath}/public_key.pem", "wb") as f:
            f.write(public_key)

    logger.debug(f"DID创建成功: {did_document['id']}")
    logger.debug(f"DID文档已保存到: {userdid_filepath}")
    logger.debug(f"密钥已保存到: {userdid_filepath}")
    logger.debug(f"用户文件已保存到: {userdid_filepath}")
    logger.debug(f"jwt密钥已保存到: {userdid_filepath}")

    try:
        # 创建成功后，立即加载到内存
        user_data_manager = get_user_data_manager()
        new_user_data = user_data_manager.load_single_user(userdid_filepath)

    except Exception as e:
        logger.error(f"创建用户后加载到用户管理器失败，报错: {e}")
        return None

    if new_user_data:
        logger.info(f"新用户已创建并加载到内存: {new_user_data.did}")
    else:
        logger.warning(f"用户创建成功但加载到内存失败: {userdid_filepath}")

    return did_document

    