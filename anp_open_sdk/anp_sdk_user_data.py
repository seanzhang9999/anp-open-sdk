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
import shutil
from datetime import datetime

import yaml
from cryptography.hazmat.primitives.serialization import load_pem_private_key


logger = logging.getLogger(__name__)
from typing import Dict, List, Optional, Any, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa


from anp_open_sdk.config import get_global_config



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
        from anp_open_sdk import anp_user_tool

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

    def load_all_users(self):
        """
        [重构] 扫描用户目录，实例化LocalUserData，并建立索引。
        此方法将不再关心文件内容的具体解析。
        """
        if not os.path.isdir(self._user_dir):
            logger.warning(f"用户目录不存在: {self._user_dir}")
            return

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
                    self.users_by_did[user_data.did] = user_data
                    if user_data.name:
                        self.users_by_name[user_data.name] = user_data
                else:
                    logger.warning(f"用户 {folder_name} 加载成功但缺少DID，无法索引。")

            except Exception as e:
                logger.error(f"加载用户数据失败 ({folder_name}): {e}", exc_info=True)

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

    def create_hosted_user(self, parent_user_data: 'LocalUserData', host: str, port: str, did_document: dict) -> Tuple[
        bool, Optional['LocalUserData']]:
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
            hosted_dir_name = f"user_hosted_{host}_{port}_{did_suffix}"
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

    @property
    def user_dir(self):
        return self._user_dir
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
