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
from datetime import datetime

import yaml

from anp_open_sdk.did_tool import create_did_user

logger = logging.getLogger(__name__)
from typing import Dict, List, Optional, Any


from anp_open_sdk.config import get_global_config



class LocalUserData():
    def __init__(self, folder_name: str, agent_cfg: Dict[str, Any], did_doc: Dict[str, Any], did_doc_path, password_paths: Dict[str, str], user_folder_path):
        self.folder_name = folder_name
        self.agent_cfg = agent_cfg
        self.did_doc = did_doc
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
        self.users: Dict[str, LocalUserData] = {}
        self.load_users()
        self._initialized = True

    @property
    def user_dir(self):
        return self._user_dir

    def load_users(self):
        if not os.path.isdir(self._user_dir):
            logger.warning(f"用户目录不存在: {self._user_dir}")
            return

        for entry in os.scandir(self._user_dir):
            if entry.is_dir() and (entry.name.startswith('user_') or entry.name.startswith('user_hosted_')):
                user_folder_path = entry.path
                folder_name = entry.name
                try:
                    cfg_path = os.path.join(user_folder_path, 'agent_cfg.yaml')
                    agent_cfg = {}
                    if os.path.exists(cfg_path):
                        with open(cfg_path, 'r', encoding='utf-8') as f:
                            agent_cfg = yaml.safe_load(f)
                    did_doc_path = os.path.join(user_folder_path, 'did_document.json')
                    did_doc = {}
                    if os.path.exists(did_doc_path):
                        with open(did_doc_path, 'r', encoding='utf-8') as f:
                            did_doc = json.load(f)
                    config = get_global_config()

                    key_id = did_doc.get('key_id') or did_doc.get('publicKey', [{}])[0].get('id') if did_doc.get('publicKey') else config.anp_sdk.user_did_key_id
                    did_private_key_file_path = os.path.join(user_folder_path, f"{key_id}_private.pem")
                    did_public_key_file_path = os.path.join(user_folder_path, f"{key_id}_public.pem")
                    jwt_private_key_file_path = os.path.join(user_folder_path, 'private_key.pem')
                    jwt_public_key_file_path = os.path.join(user_folder_path, 'public_key.pem')
                    password_paths = {
                        "did_private_key_file_path": did_private_key_file_path,
                        "did_public_key_file_path": did_public_key_file_path,
                        "jwt_private_key_file_path": jwt_private_key_file_path,
                        "jwt_public_key_file_path": jwt_public_key_file_path
                    }
                    if did_doc and agent_cfg:
                         user_data = LocalUserData(folder_name, agent_cfg, did_doc, did_doc_path, password_paths, user_folder_path)
                         self.users[user_data.did] = user_data
                except Exception as e:
                    logger.error(f"加载用户数据失败 ({folder_name}): {e}")
            else:
                logger.warning(f"不合格的文件或文件夹: {entry.name},{self._user_dir}")

        logger.debug(f"加载用户数据共 {len(self.users)} 个用户")

    def get_user_data(self, did: str) -> Optional[LocalUserData]:
        return self.users.get(did)

    def get_all_users(self) -> List[LocalUserData]:
        return list(self.users.values())

    def get_user_data_by_name(self, name: str) -> Optional[LocalUserData]:
        for user_data in self.users.values():
            if user_data.name == name:
                return user_data
        return None


