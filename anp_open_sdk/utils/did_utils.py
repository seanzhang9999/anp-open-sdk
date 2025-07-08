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
DID工具函数模块
提供DID相关的通用工具函数
"""

import re
from typing import Optional, Tuple


def parse_wba_did_host_port(did: str) -> Tuple[Optional[str], Optional[int]]:
    """
    从WBA DID中解析主机和端口
    
    支持格式:
    - did:wba:host%3Aport:xxxx (URL编码)
    - did:wba:host:port:xxxx (直接格式)
    - did:wba:host:xxxx (默认端口80)
    
    Args:
        did: WBA DID字符串
        
    Returns:
        Tuple[Optional[str], Optional[int]]: (主机, 端口)
        如果解析失败返回 (None, None)
    """
    # 处理URL编码的端口格式 (host%3Aport)
    m = re.match(r"did:wba:([^%:]+)%3A(\d+):", did)
    if m:
        return m.group(1), int(m.group(2))
    
    # 处理直接格式 (host:port)
    m = re.match(r"did:wba:([^:]+):(\d+):", did)
    if m:
        return m.group(1), int(m.group(2))
    
    # 处理无端口格式 (默认端口80)
    m = re.match(r"did:wba:([^:]+):", did)
    if m:
        return m.group(1), 80
    
    return None, None