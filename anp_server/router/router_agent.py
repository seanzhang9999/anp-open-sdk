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
import logging

from anp_server.router.router_did import url_did_format

logger = logging.getLogger(__name__)


from fastapi import Request
from typing import Dict, Any, List
from datetime import datetime
import time

from anp_sdk.utils.log_base import  logging as logger
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))

class AgentSearchRecord:
    """智能体搜索记录"""
    
    def __init__(self):
        self.search_history = []
    
    def record_search(self, searcher_did: str, query: str, results: List[str]):
        """记录搜索行为"""
        self.search_history.append({
            "timestamp": datetime.now().isoformat(),
            "searcher_did": searcher_did,
            "query": query,
            "results": results,
            "result_count": len(results)
        })
        
    def get_recent_searches(self, limit: int = 10):
        """获取最近的搜索记录"""
        return self.search_history[-limit:]


class AgentContactBook:
    """智能体通讯录"""
    
    def __init__(self, owner_did: str):
        self.owner_did = owner_did
        self.contacts = {}  # did -> 联系人信息
    
    def add_contact(self, did: str, name: str = None, description: str = "", tags: List[str] = None):
        """添加联系人"""
        if did not in self.contacts:
            self.contacts[did] = {
                "did": did,
                "name": name or did.split(":")[-1],
                "description": description,
                "tags": tags or [],
                "first_contact": datetime.now().isoformat(),
                "last_contact": datetime.now().isoformat(),
                "interaction_count": 1
            }
        else:
            self.update_interaction(did)
    
    def update_interaction(self, did: str):
        """更新交互记录"""
        if did in self.contacts:
            self.contacts[did]["last_contact"] = datetime.now().isoformat()
            self.contacts[did]["interaction_count"] += 1
    
    def get_contacts(self, tag: str = None):
        """获取联系人列表"""
        if tag:
            return {did: info for did, info in self.contacts.items() if tag in info["tags"]}
        return self.contacts


class SessionRecord:
    """会话记录"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> 会话信息
    
    def create_session(self, req_did: str, resp_did: str):
        """创建会话"""
        session_id = f"{req_did}_{resp_did}_{int(time.time())}"
        self.sessions[session_id] = {
            "session_id": session_id,
            "req_did": req_did,
            "resp_did": resp_did,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "messages": [],
            "status": "active"
        }
        return session_id
    
    def add_message(self, session_id: str, message: Dict):
        """添加消息"""
        if session_id in self.sessions:
            self.sessions[session_id]["messages"].append({
                "timestamp": datetime.now().isoformat(),
                "content": message,
                "direction": "outgoing" if message.get("sender") == self.sessions[session_id]["req_did"] else "incoming"
            })
    
    def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.sessions:
            self.sessions[session_id]["end_time"] = datetime.now().isoformat()
            self.sessions[session_id]["status"] = "closed"
    
    def get_active_sessions(self):
        """获取活跃会话"""
        return {sid: session for sid, session in self.sessions.items() if session["status"] == "active"}


class ApiCallRecord:
    """API调用记录"""
    
    def __init__(self):
        self.api_calls = []
    
    def record_api_call(self, caller_did: str, target_did: str, api_path: str, method: str, params: Dict, response: Dict, duration_ms: int):
        """记录API调用"""
        self.api_calls.append({
            "timestamp": datetime.now().isoformat(),
            "caller_did": caller_did,
            "target_did": target_did,
            "api_path": api_path,
            "method": method,
            "params": params,
            "response_status": response.get("status"),
            "duration_ms": duration_ms,
            "success": response.get("status") == "success"
        })
    
    def get_recent_calls(self, limit: int = 20):
        """获取最近的API调用记录"""
        return self.api_calls[-limit:]


class AgentRouter:
    """增强的智能体路由器，支持多域名管理和智能体隔离，以及DID共享"""
    
    def __init__(self):
        # 多级索引结构：domain -> port -> agent_id -> agent
        self.domain_agents = {}  # {domain: {port: {agent_id: agent}}}
        self.global_agents = {}  # 向后兼容的全局索引 {agent_id: agent}
        self.logger = logger
        
        # 共享DID注册表：shared_did -> {path_mappings: {full_path: (agent_id, original_path)}}
        self.shared_did_registry = {}
        
        # DID使用注册表：did -> {"type": "independent|shared", "agents": [...]}
        self.did_usage_registry = {}
        
        # 统计信息
        self.stats = {
            'total_agents': 0,
            'domains_count': 0,
            'registration_conflicts': 0,
            'routing_errors': 0,
            'shared_did_count': 0,
            'did_conflicts': 0
        }
    
    def register_agent(self, agent):
        """注册智能体（向后兼容方法）"""
        return self.register_agent_with_domain(agent)
    
    def register_agent_with_domain(self, agent, domain: str = None, port: int = None, request: Request = None):
        """
        注册智能体到指定域名
        
        Args:
            agent: 智能体实例
            domain: 域名（可选，从request中提取或使用默认值）
            port: 端口（可选，从request中提取或使用默认值）
            request: HTTP请求对象（用于自动提取域名信息）
        """
        # 1. 确定域名和端口
        if request:
            domain, port = self._get_host_port_from_request(request)
        elif not domain or not port:
            domain, port = self._get_default_host_port()
        
        # 2. 初始化域名结构
        if domain not in self.domain_agents:
            self.domain_agents[domain] = {}
            self.stats['domains_count'] += 1
        
        if port not in self.domain_agents[domain]:
            self.domain_agents[domain][port] = {}
        
        # 3. 确定注册键：使用 DID+Agent名称 的组合键，确保唯一性
        agent_id = str(agent.id)
        agent_name = agent.name if hasattr(agent, 'name') and agent.name else "unnamed"
        registration_key = f"{agent_id}#{agent_name}"  # 使用#分隔符避免冲突
        
        # 4. DID冲突检测（仅对独立DID Agent进行检测）
        if registration_key == agent_id:  # 独立DID Agent
            self._check_did_conflict(agent_id, "independent")
            # 注册为独立DID
            self.did_usage_registry[agent_id] = {
                "type": "independent", 
                "agents": [agent.name if hasattr(agent, 'name') else agent_id]
            }
        
        # 5. 检查Agent注册冲突
        if registration_key in self.domain_agents[domain][port]:
            self.stats['registration_conflicts'] += 1
            self.logger.warning(f"智能体注册冲突: {domain}:{port} 已存在 {registration_key}")
        
        # 6. 注册智能体（使用注册键）
        self.domain_agents[domain][port][registration_key] = agent
        
        # 7. 更新全局索引（向后兼容）
        global_key = f"{domain}:{port}:{agent_id}"
        self.global_agents[global_key] = agent
        self.global_agents[agent_id] = agent  # 保持原有行为
        
        # 同时也用注册键注册，以便查找（添加冲突检测）
        if registration_key != agent_id:
            # 检查Agent名称冲突
            if registration_key in self.global_agents:
                existing_agent = self.global_agents[registration_key]
                if existing_agent.id != agent.id:  # 不同的Agent使用了相同的名称
                    self.stats['registration_conflicts'] += 1
                    self.logger.warning(f"⚠️ 全局索引Agent名称冲突: '{registration_key}' 已被Agent {existing_agent.id} 使用，现在被Agent {agent.id} 覆盖")
            
            self.global_agents[registration_key] = agent
        
        # 8. 更新统计
        self.stats['total_agents'] += 1
        
        self.logger.debug(f"✅ 智能体注册成功: {registration_key} (DID: {agent_id}) @ {domain}:{port}")
        return agent
    
    def _get_host_port_from_request(self, request: Request):
        """从请求中提取域名和端口"""
        try:
            host = request.headers.get("host", "localhost:9527")
            if ":" in host:
                domain, port_str = host.split(":", 1)
                port = int(port_str)
            else:
                domain = host
                port = 9527  # 默认端口
            return domain, port
        except Exception as e:
            self.logger.warning(f"解析请求域名失败: {e}")
            return self._get_default_host_port()
    
    def _get_default_host_port(self):
        """获取默认域名和端口"""
        return "localhost", 9527
        
    def get_agent(self, did: str):
        """获取指定DID的智能体（向后兼容方法）"""
        return self.global_agents.get(str(did))
    
    def find_agent_with_domain_priority(self, agent_id: str, request_domain: str = None, request_port: int = None):
        """
        按优先级查找智能体：
        1. 当前请求域名:端口下的智能体
        2. 当前域名下其他端口的智能体
        3. 全局智能体（向后兼容）
        """
        agent_id = str(agent_id)
        
        # 如果没有提供域名信息，使用全局查找
        if not request_domain or not request_port:
            return self._find_agent_in_global_index(agent_id)
        
        # 优先级1: 精确匹配域名和端口
        if (request_domain in self.domain_agents and 
            request_port in self.domain_agents[request_domain]):
            agent = self._find_agent_in_domain_port(agent_id, request_domain, request_port)
            if agent:
                return agent
        
        # 优先级2: 同域名不同端口
        if request_domain in self.domain_agents:
            for other_port, agents in self.domain_agents[request_domain].items():
                agent = self._find_agent_in_agents_dict(agent_id, agents)
                if agent:
                    self.logger.warning(f"跨端口访问: {agent_id} @ {request_domain}:{other_port} -> {request_domain}:{request_port}")
                    return agent
        
        # 优先级3: 全局查找（向后兼容）
        agent = self._find_agent_in_global_index(agent_id)
        if agent:
            self.logger.warning(f"全局智能体访问: {agent_id}")
            return agent
        
        return None
    
    def _find_agent_in_domain_port(self, agent_id: str, domain: str, port: int):
        """在指定域名端口下查找Agent"""
        agents = self.domain_agents[domain][port]
        return self._find_agent_in_agents_dict(agent_id, agents)
    
    def _find_agent_in_agents_dict(self, agent_id: str, agents: dict):
        """在Agent字典中查找Agent，支持DID和Agent名称查找"""
        # 1. 直接匹配（向后兼容）
        if agent_id in agents:
            return agents[agent_id]
        
        # 2. 通过组合键匹配（DID#Agent名称）
        for key, agent in agents.items():
            if '#' in key:
                did_part, name_part = key.split('#', 1)
                if did_part == agent_id or name_part == agent_id:
                    return agent
        
        return None
    
    def _find_agent_in_global_index(self, agent_id: str):
        """在全局索引中查找Agent"""
        # 1. 直接匹配（向后兼容）
        if agent_id in self.global_agents:
            return self.global_agents[agent_id]
        
        # 2. 通过组合键匹配
        for key, agent in self.global_agents.items():
            if '#' in key:
                did_part, name_part = key.split('#', 1)
                if did_part == agent_id or name_part == agent_id:
                    return agent
        
        return None

    async def route_request(self, req_did: str, resp_did: str, request_data: Dict, request: Request) -> Any:
        """增强的路由请求处理，支持域名优先级查找和共享DID路由"""
        
        # 1. 提取请求域名信息
        domain, port = self._get_host_port_from_request(request)
        
        # 2. 格式化目标DID
        resp_did = url_did_format(resp_did, request)
        
        # 3. 检查请求类型和是否需要共享DID路由
        api_path = request_data.get("path", "")
        request_type = request_data.get("type", "")
        
        # 消息类型请求不使用共享DID路由，直接路由到Agent
        if request_type == "message" or api_path.startswith("/message/"):
            self.logger.info(f"📨 消息路由: 直接路由到 {resp_did}")
            agent = self.find_agent_with_domain_priority(resp_did, domain, port)
        elif resp_did in self.shared_did_registry and api_path and request_type == "api_call":
            # 共享DID API路由处理
            target_agent_name, original_path = self._resolve_shared_did(resp_did, api_path)
            if target_agent_name and original_path:
                # 更新请求数据中的路径
                request_data = request_data.copy()
                request_data["path"] = original_path
                # 使用目标Agent的名称进行路由（因为共享DID的Agent使用名称注册）
                agent = self.find_agent_with_domain_priority(target_agent_name, domain, port)
                self.logger.info(f"🔄 共享DID路由: {resp_did}{api_path} -> {target_agent_name}{original_path}")
            else:
                self.stats['routing_errors'] += 1
                raise ValueError(f"共享DID {resp_did} 中未找到路径 {api_path} 的处理器")
        else:
            # 常规路由处理
            agent = self.find_agent_with_domain_priority(resp_did, domain, port)
        
        if not agent:
            self.stats['routing_errors'] += 1
            available_agents = self._get_available_agents_for_domain(domain, port)
            error_msg = f"未找到智能体: {resp_did} @ {domain}:{port}\n可用智能体: {available_agents}"
            self.logger.error(error_msg)
            raise ValueError(f"未找到本地智能体: {resp_did}")
        
        # 4. 验证智能体可调用性
        if not hasattr(agent.handle_request, "__call__"):
            self.logger.error(f"{resp_did} 的 `handle_request` 不是一个可调用对象")
            raise TypeError(f"{resp_did} 的 `handle_request` 不是一个可调用对象")
        
        # 5. 设置请求上下文
        request.state.agent = agent
        request.state.domain = domain
        request.state.port = port
        
        # 6. 执行路由
        try:
            self.logger.info(f"🚀 路由请求: {req_did} -> {resp_did} @ {domain}:{port}")
            self.logger.info(f"route_request -- forward to {agent.id}'s handler, forward data:{request_data}\n")
            self.logger.debug(f"route_request -- url: {request.url} \nbody: {await request.body()}")
            
            result = await agent.handle_request(req_did, request_data, request)
            return result
        except Exception as e:
            self.stats['routing_errors'] += 1
            self.logger.error(f"❌ 路由执行失败: {e}")
            raise
    
    def _get_available_agents_for_domain(self, domain: str, port: int):
        """获取指定域名下的可用智能体列表"""
        agents = []
        if domain in self.domain_agents and port in self.domain_agents[domain]:
            agents = list(self.domain_agents[domain][port].keys())
        return agents
    
    def get_agents_by_domain(self, domain: str, port: int = None):
        """获取指定域名下的所有智能体"""
        if domain not in self.domain_agents:
            return {}
        
        if port:
            return self.domain_agents[domain].get(port, {})
        else:
            # 返回该域名下所有端口的智能体
            all_agents = {}
            for p, agents in self.domain_agents[domain].items():
                for agent_id, agent in agents.items():
                    all_agents[f"{p}:{agent_id}"] = agent
            return all_agents
    
    def get_domain_statistics(self):
        """获取域名统计信息"""
        stats = self.stats.copy()
        
        # 详细统计
        domain_details = {}
        for domain, ports in self.domain_agents.items():
            domain_details[domain] = {
                'ports': list(ports.keys()),
                'total_agents': sum(len(agents) for agents in ports.values()),
                'agents_by_port': {
                    str(port): list(agents.keys()) 
                    for port, agents in ports.items()
                }
            }
        
        stats['domain_details'] = domain_details
        return stats
    
    def get_all_agents(self):
        """获取所有智能体（向后兼容方法）"""
        return self.global_agents
    
    def register_shared_did(self, shared_did: str, agent_name: str, path_prefix: str, api_paths: List[str]):
        """注册共享DID配置"""
        if shared_did not in self.shared_did_registry:
            self.shared_did_registry[shared_did] = {
                'path_mappings': {}
            }
            self.stats['shared_did_count'] += 1
        
        # 为每个API路径创建映射
        for api_path in api_paths:
            # 完整路径 = path_prefix + api_path
            full_path = f"{path_prefix.rstrip('/')}{api_path}"
            self.shared_did_registry[shared_did]['path_mappings'][full_path] = (agent_name, api_path)
            self.logger.debug(f"📝 注册共享DID路径映射: {shared_did}{full_path} -> {agent_name}{api_path}")
    
    def _resolve_shared_did(self, shared_did: str, api_path: str):
        """解析共享DID，返回(target_agent_id, original_path)"""
        if shared_did not in self.shared_did_registry:
            return None, None
        
        config = self.shared_did_registry[shared_did]
        path_mappings = config.get('path_mappings', {})
        
        # 精确匹配
        if api_path in path_mappings:
            agent_id, original_path = path_mappings[api_path]
            return agent_id, original_path
        
        # 前缀匹配（用于通配符路径）
        for full_path, (agent_id, original_path) in path_mappings.items():
            if full_path.endswith('*') and api_path.startswith(full_path.rstrip('*')):
                # 计算相对路径
                relative_path = api_path[len(full_path.rstrip('*')):]
                final_path = f"{original_path.rstrip('/')}{relative_path}"
                return agent_id, final_path
        
        return None, None
    
    def get_shared_did_info(self, shared_did: str):
        """获取共享DID信息"""
        return self.shared_did_registry.get(shared_did, {})
    
    def list_shared_dids(self):
        """列出所有共享DID"""
        return list(self.shared_did_registry.keys())
    
    def _check_did_conflict(self, did: str, new_type: str):
        """检查DID使用冲突"""
        if did in self.did_usage_registry:
            existing_type = self.did_usage_registry[did]["type"]
            if existing_type != new_type:
                self.stats['did_conflicts'] += 1
                error_msg = f"❌ DID冲突: {did} 已被用作{existing_type}DID，不能用作{new_type}DID"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
