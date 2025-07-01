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
ANP Open SDK Framework

统一的智能体框架，提供：
- 统一调用器 (UnifiedCaller)
- 统一爬虫 (UnifiedCrawler) 
- 主智能体 (MasterAgent)
- 本地方法管理
"""

from .unified_caller import UnifiedCaller
from .unified_crawler import UnifiedCrawler, ResourceDiscoverer, LocalMethodsDiscoverer, RemoteAgentDiscoverer
from .master_agent import MasterAgent

__version__ = "1.0.0"
__all__ = [
    "UnifiedCaller",
    "UnifiedCrawler", 
    "ResourceDiscoverer",
    "LocalMethodsDiscoverer",
    "RemoteAgentDiscoverer",
    "MasterAgent"
]
