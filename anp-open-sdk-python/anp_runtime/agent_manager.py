import json
import os
import importlib
import inspect
import time
from pathlib import Path

import yaml
import logging
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime

from starlette.requests import Request

from anp_foundation.anp_user_local_data import get_user_data_manager
from anp_foundation.anp_user import ANPUser
from anp_foundation.config import UnifiedConfig
from anp_server.baseline.anp_router_baseline.router_did import url_did_format
from anp_runtime.agent import Agent
logger = logging.getLogger(__name__)



async def save_interface_files(user_full_path: str, interface_data: dict, inteface_file_name: str,
                               interface_file_type: str):
    """保存接口配置文件"""
    # 保存智能体描述文件
    template_ad_path = Path(user_full_path) / inteface_file_name
    template_ad_path = Path(UnifiedConfig.resolve_path(template_ad_path.as_posix()))
    template_ad_path.parent.mkdir(parents=True, exist_ok=True)

    with open(template_ad_path, 'w', encoding='utf-8') as f:
        if interface_file_type.upper() == "JSON":
            json.dump(interface_data, f, ensure_ascii=False, indent=2)
        elif interface_file_type.upper() == "YAML":
            yaml.dump(interface_data, f, allow_unicode=True)
    logger.debug(f"接口文件{inteface_file_name}已保存在: {template_ad_path}")


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
        self.domain_anp_users = {}  # {domain: {port: {agent_id: agent}}}
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

    def register_agent_with_domain(self, agent: Agent, domain: str = None, port: int = None, request: Request = None):
        """
        注册智能体到指定域名

        Args:
            agent: Agent实例
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
        if domain not in self.domain_anp_users:
            self.domain_anp_users[domain] = {}
            self.stats['domains_count'] += 1

        if port not in self.domain_anp_users[domain]:
            self.domain_anp_users[domain][port] = {}

        # 3. 确定注册键：使用 DID+Agent名称 的组合键，确保唯一性
        agent_id =agent.anp_user_did
        agent_name = agent.name if agent.name else "unnamed"
        registration_key = f"{agent_id}#{agent_name}"  # 使用#分隔符避免冲突

        # 4. DID冲突检测（仅对独立DID Agent进行检测）
        if not agent.shared:  # 独立DID Agent
            self._check_did_conflict(agent_id, "independent")
            # 注册为独立DID
            self.did_usage_registry[agent_id] = {
                "type": "independent",
                "agents": [agent_name]
            }
        else:
            # 共享DID Agent
            if agent_id in self.did_usage_registry:
                # 更新共享DID的Agent列表
                if agent_name not in self.did_usage_registry[agent_id]["agents"]:
                    self.did_usage_registry[agent_id]["agents"].append(agent_name)
            else:
                # 新建共享DID记录
                self.did_usage_registry[agent_id] = {
                    "type": "shared",
                    "agents": [agent_name]
                }

        # 5. 检查Agent注册冲突
        if registration_key in self.domain_anp_users[domain][port]:
            self.stats['registration_conflicts'] += 1
            self.logger.warning(f"智能体注册冲突: {domain}:{port} 已存在 {registration_key}")

        # 6. 注册智能体（使用注册键）
        self.domain_anp_users[domain][port][registration_key] = agent

        # 7. 更新全局索引（向后兼容）
        global_key = f"{domain}:{port}:{agent_id}"
        self.global_agents[global_key] = agent
        self.global_agents[agent_id] = agent  # 保持原有行为

        # 同时也用注册键注册，以便查找（添加冲突检测）
        if registration_key != agent_id:
            # 检查Agent名称冲突
            if registration_key in self.global_agents:
                existing_agent = self.global_agents[registration_key]
                if existing_agent.anp_user_did != agent.anp_user_did:  # 不同的Agent使用了相同的名称
                    self.stats['registration_conflicts'] += 1
                    self.logger.warning(f"⚠️ 全局索引Agent名称冲突: '{registration_key}' 已被Agent {existing_agent.name} 使用，现在被Agent {agent.name} 覆盖")

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
        if (request_domain in self.domain_anp_users and
            request_port in self.domain_anp_users[request_domain]):
            agent = self._find_agent_in_domain_port(agent_id, request_domain, request_port)
            if agent:
                return agent

        # 优先级2: 同域名不同端口
        if request_domain in self.domain_anp_users:
            for other_port, agents in self.domain_anp_users[request_domain].items():
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
        agents = self.domain_anp_users[domain][port]
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
            # 3. 检查Agent实例的ID是否匹配
            elif hasattr(agent, 'id') and str(agent.anp_user_did) == agent_id:
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
            self.logger.debug(f"📨 消息路由: 直接路由到 {resp_did}")
            agent = self._find_message_capable_agent(resp_did, domain, port)
        else:
            # 尝试从AgentManager获取共享DID信息
            try:
                from anp_runtime.agent_manager import AgentManager
                agent_info = AgentManager.get_agent_info(resp_did)

                # 如果是共享DID，并且有多个Agent
                if agent_info and len(agent_info) > 1:
                    # 根据API路径前缀选择正确的Agent
                    for agent_name, info in agent_info.items():
                        agent_obj = info.get('agent')
                        if agent_obj and agent_obj.shared and agent_obj.prefix and api_path.startswith(
                                agent_obj.prefix):
                            # 找到匹配的Agent
                            agent = agent_obj
                            self.logger.debug(f"✅ 根据路径前缀 {agent_obj.prefix} 找到共享DID Agent: {agent_name}")
                            break
                    else:
                        # 如果没有找到匹配的Agent，使用常规路由
                        agent = self.find_agent_with_domain_priority(resp_did, domain, port)
                else:
                    # 如果不是共享DID，或者只有一个Agent，使用常规路由
                    agent = self.find_agent_with_domain_priority(resp_did, domain, port)
            except (ImportError, Exception) as e:
                # 如果出错，使用常规路由
                self.logger.warning(f"尝试从AgentManager获取共享DID信息失败: {e}")
                agent = self.find_agent_with_domain_priority(resp_did, domain, port)

        if not agent:
            # 尝试从AgentManager中查找
            try:
                from anp_runtime.agent_manager import AgentManager

                # 检查AgentManager中是否有该Agent
                agent_info = AgentManager.get_agent_info(resp_did)
                if agent_info:
                    # 找到了Agent，获取第一个
                    for agent_name, info in agent_info.items():
                        agent_obj = info.get('agent')
                        if agent_obj:
                            # 注册到router_agent
                            self.register_agent_with_domain(agent_obj, domain, port)
                            agent = agent_obj
                            self.logger.debug(f"✅ 从AgentManager中找到并注册智能体: {resp_did} -> {agent_name}")
                            break
            except (ImportError, Exception) as e:
                self.logger.warning(f"尝试从AgentManager查找Agent失败: {e}")

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
            self.logger.debug(f"🚀 路由请求: {req_did} -> {resp_did} @ {domain}:{port}")
            self.logger.debug(f"route_request -- forward to {agent.anp_user_did}'s handler, forward data:{request_data}\n")
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
        if domain in self.domain_anp_users and port in self.domain_anp_users[domain]:
            agents = list(self.domain_anp_users[domain][port].keys())
        return agents

    def get_agents_by_domain(self, domain: str, port: int = None):
        """获取指定域名下的所有智能体"""
        if domain not in self.domain_anp_users:
            return {}

        if port:
            return self.domain_anp_users[domain].get(port, {})
        else:
            # 返回该域名下所有端口的智能体
            all_agents = {}
            for p, agents in self.domain_anp_users[domain].items():
                for agent_id, agent in agents.items():
                    all_agents[f"{p}:{agent_id}"] = agent
            return all_agents

    def get_domain_statistics(self):
        """获取域名统计信息"""
        stats = self.stats.copy()

        # 详细统计
        domain_details = {}
        for domain, ports in self.domain_anp_users.items():
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

    def register_shared_did(self, shared_did: str, agent: Agent, api_paths: List[str]):
        """注册共享DID配置"""
        if not agent.shared:
            self.logger.error(f"❌ 尝试注册非共享DID Agent到共享DID: {agent.name}")
            raise ValueError(f"Agent {agent.name} 不是共享DID模式，无法注册到共享DID")

        if not agent.prefix:
            self.logger.error(f"❌ 共享DID Agent缺少prefix: {agent.name}")
            raise ValueError(f"共享DID Agent {agent.name} 缺少prefix参数")

        agent_name = agent.name
        path_prefix = agent.prefix

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

    def _find_message_capable_agent(self, did: str, domain: str = None, port: int = None):
        """查找具有消息处理能力的Agent，优先选择主Agent"""
        try:
            from anp_runtime.agent_manager import AgentManager

            # 从AgentManager获取该DID的所有Agent信息
            agent_info = AgentManager.get_agent_info(did)
            if agent_info:
                # 优先查找主Agent（有消息处理权限）
                primary_agent = None
                fallback_agent = None

                for agent_name, info in agent_info.items():
                    agent_obj = info.get('agent')
                    if agent_obj:
                        # 检查是否为主Agent
                        if info.get('primary_agent', False):
                            primary_agent = agent_obj
                            self.logger.debug(f"✅ 找到主Agent用于消息处理: {agent_name}")
                            break
                        # 保存第一个Agent作为备选
                        elif fallback_agent is None:
                            fallback_agent = agent_obj

                # 返回主Agent或备选Agent
                selected_agent = primary_agent or fallback_agent
                if selected_agent:
                    # 注册到router_agent以便后续使用
                    self.register_agent_with_domain(selected_agent, domain, port)

                    # 验证Agent是否有消息处理能力
                    if hasattr(selected_agent, 'message_handlers') and selected_agent.message_handlers:
                        self.logger.debug(f"✅ Agent {selected_agent.name} 具有消息处理能力")
                        return selected_agent
                    else:
                        self.logger.warning(f"⚠️ Agent {selected_agent.name} 没有消息处理器")
                        # 继续使用该Agent，让它返回相应的错误信息
                        return selected_agent

        except (ImportError, Exception) as e:
            self.logger.warning(f"从AgentManager查找消息处理Agent失败: {e}")

        # 回退到原有逻辑
        return self.find_agent_with_domain_priority(did, domain, port)
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


class AgentManager:
    """统一的Agent管理器 - 负责Agent创建、注册和冲突管理"""

    # 类级别的 router_agent 管理
    _router_agent: Optional['AgentRouter'] = None
    _router_initialized: bool = False

    @classmethod
    def initialize_router(cls) -> 'AgentRouter':
        """初始化并返回 AgentRouter 实例"""
        if not cls._router_initialized:
            cls._router_agent = AgentRouter()
            cls._router_initialized = True
            logger.debug("✅ AgentRouter 已初始化")
        return cls._router_agent

    @classmethod
    def get_router_agent(cls) -> 'AgentRouter':
        """获取 AgentRouter 实例，如果未初始化则自动初始化"""
        if cls._router_agent is None:
            logger.warning("⚠️ AgentRouter 未初始化，自动初始化中...")
            return cls.initialize_router()
        return cls._router_agent

    # 类级别的DID使用注册表
    _did_usage_registry: Dict[str, Dict[str, Dict[str, Any]]] = {}  # {did: {agent_name: agent_info}}

    @classmethod
    def get_agent(cls, did: str, agent_name: str) -> Optional[Agent]:
        """全局单例：根据 did + agent_name 拿到 Agent 实例"""
        info = cls.get_agent_info(did, agent_name)
        return info['agent'] if info else None

    @classmethod
    def get_all_agent_instances(cls) -> List[Agent]:
        """获取所有Agent实例"""
        agents = []
        for did, agents_dict in cls._did_usage_registry.items():
            for agent_name, agent_info in agents_dict.items():
                agent = agent_info.get('agent')
                if agent:
                    agents.append(agent)
        return agents

    @classmethod
    def get_agent_by_did(cls, did: str) -> Optional[Agent]:
        """根据DID获取Agent实例（如果有多个，返回第一个）"""
        agents_info = cls.get_agent_info(did)
        if not agents_info:
            return None

        # 返回第一个Agent实例
        agent_name = list(agents_info.keys())[0]
        return cls.get_existing_agent(did, agent_name)

    @classmethod
    def create_agent(cls, anp_user_did_str: str, name: str,
                     shared: bool = False,
                     prefix: Optional[str] = None,
                     primary_agent: bool = False) -> Agent:
        """统一的Agent创建接口

        Args:
            anp_user: ANPUser实例（必选）
            name: Agent名称（必选）
            shared: 是否共享DID（默认False）
            prefix: 共享模式下的API前缀（共享模式必选）
            primary_agent: 是否为主Agent，拥有消息处理权限（共享模式可选）

        Returns:
            Agent: 创建的Agent实例

        Raises:
            ValueError: 当发生冲突时抛出异常
        """
        did = anp_user_did_str

        if not shared:
            # 独占模式：检查DID是否已被使用
            if did in cls._did_usage_registry:
                existing_agents = list(cls._did_usage_registry[did].keys())
                raise ValueError(
                    f"❌ DID独占冲突: {did} 已被Agent '{existing_agents[0]}' 使用\n"
                    f"解决方案:\n"
                    f"  1. 使用不同的DID\n"
                    f"  2. 设置 shared=True 进入共享模式"
                )
        else:
            # 共享模式：检查prefix和主Agent
            if not prefix:
                raise ValueError(f"❌ 共享模式必须提供 prefix 参数 (Agent: {name})")

            if did in cls._did_usage_registry:
                existing_agents = cls._did_usage_registry[did]

                # 检查prefix冲突
                for agent_name, agent_info in existing_agents.items():
                    if agent_info.get('prefix') == prefix:
                        raise ValueError(f"❌ Prefix冲突: {prefix} 已被Agent '{agent_name}' 使用")

                # 检查主Agent冲突 - 只检查同一个DID下的Agent
                if primary_agent:
                    for agent_name, agent_info in existing_agents.items():
                        if agent_info.get('primary_agent'):
                            raise ValueError(
                                f"❌ 主Agent冲突: DID {did} 的主Agent已被 '{agent_name}' 占用\n"
                                f"解决方案:\n"
                                f"  1. 设置 primary_agent=False\n"
                                f"  2. 修改现有主Agent配置"
                            )

        # 创建Agent
        agent = Agent(did, name, shared, prefix, primary_agent)

        # 注册使用记录
        if did not in cls._did_usage_registry:
            cls._did_usage_registry[did] = {}

        cls._did_usage_registry[did][name] = {
            'agent': agent,
            'shared': shared,
            'prefix': prefix,
            'primary_agent': primary_agent,
            'created_at': datetime.now().isoformat()
        }

        logger.debug(f"✅ Agent创建成功: {name}")
        logger.debug(f"   DID: {did} ({'共享' if shared else '独占'})")
        if prefix:
            logger.debug(f"   Prefix: {prefix}")
        if primary_agent:
            logger.debug(f"   主Agent: 是")

        return agent

    @classmethod
    def get_agent_info(cls, did: str, agent_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取Agent信息"""
        if did not in cls._did_usage_registry:
            return None

        if agent_name:
            return cls._did_usage_registry[did].get(agent_name)
        else:
            # 返回该DID下的所有Agent信息
            return cls._did_usage_registry[did]

    @classmethod
    def list_agents(cls) -> Dict[str, Any]:
        """列出所有Agent信息"""
        result = {}
        for did, agents in cls._did_usage_registry.items():
            result[did] = {}
            for agent_name, agent_info in agents.items():
                # 不包含agent实例，避免序列化问题
                result[did][agent_name] = {
                    'shared': agent_info['shared'],
                    'prefix': agent_info['prefix'],
                    'primary_agent': agent_info['primary_agent'],
                    'created_at': agent_info['created_at']
                }
        return result

    @classmethod
    def remove_agent(cls, did: str, agent_name: str) -> bool:
        """移除Agent"""
        if did in cls._did_usage_registry and agent_name in cls._did_usage_registry[did]:
            del cls._did_usage_registry[did][agent_name]

            # 如果该DID下没有Agent了，删除DID记录
            if not cls._did_usage_registry[did]:
                del cls._did_usage_registry[did]

            logger.debug(f"🗑️  Agent已移除: {agent_name} (DID: {did})")
            return True
        return False

    @classmethod
    def clear_all_agents(cls):
        """清除所有Agent（主要用于测试）"""
        cls._did_usage_registry.clear()
        logger.debug("清除所有Agent注册记录")

    @classmethod
    def get_existing_agent(cls, did: str, agent_name: str) -> Optional[Agent]:
        """获取已存在的Agent实例"""
        if did in cls._did_usage_registry and agent_name in cls._did_usage_registry[did]:
            return cls._did_usage_registry[did][agent_name]['agent']
        return None

    @classmethod
    def get_agent_by_anp_user(cls, anp_user):
        """根据ANPUser实例查找对应的Agent实例"""
        for did, agents in cls._did_usage_registry.items():
            for agent_name, agent_info in agents.items():
                agent = agent_info['agent']
                if agent.anp_user == anp_user:
                    return agent
        return None


class LocalAgentManager:
    """本地 Agent 管理器，负责加载、注册和生成接口文档"""

    @staticmethod
    async def load_agent_from_module(yaml_path: str) -> Tuple[Optional[Any], Optional[Any], Optional[Dict]]:
        from anp_runtime.agent_decorator import agent_api
        """从模块路径加载 Agent 实例，返回 (agent_or_new_agent, handler_module, share_did_config)"""
        logger.debug(f"\n🔎 Loading agent module from path: {yaml_path}")
        plugin_dir = os.path.dirname(yaml_path)
        handler_script_path = os.path.join(plugin_dir, "agent_handlers.py")
        register_script_path = os.path.join(plugin_dir, "agent_register.py")

        if not os.path.exists(handler_script_path):
            logger.debug(f"  - ⚠️  Skipping: No 'agent_handlers.py' found in {plugin_dir}")
            return None, None, None

        module_path_prefix = os.path.dirname(plugin_dir).replace(os.sep, ".")
        base_module_name = f"{module_path_prefix}.{os.path.basename(plugin_dir)}"
        base_module_name = base_module_name.replace("/", ".")
        handlers_module = importlib.import_module(f"{base_module_name}.agent_handlers")

        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        # 检查共享DID配置
        share_did_config = None
        share_config = cfg.get('share_did', {})
        if share_config.get('enabled'):
            share_did_config = {
                'shared_did': share_config['shared_did'],
                'path_prefix': share_config.get('path_prefix', ''),
                'primary_agent': share_config.get('primary_agent', False),  # 默认为副Agent
                'api_paths': [api['path'] for api in cfg.get('api', [])]
            }
            logger.debug(f"  -> 检测到共享DID配置: {share_did_config}")

        # 确定Agent的DID（共享DID或独立DID）
        if share_did_config:
            # 对于共享DID的Agent，使用共享DID来获取用户数据
            shared_did = share_did_config['shared_did']
            try:
                # 使用共享DID获取用户数据
                anp_user_did = shared_did
                logger.debug(f"  -> 共享DID Agent {cfg['name']} 使用共享DID: {shared_did}")
            except ValueError as e:
                logger.warning(f"共享DID Agent {cfg['name']} 无法获取共享DID {shared_did} 的用户数据: {e}")
                return None, None, share_did_config
        else:
            # 独立DID的Agent
            anp_user_did = cfg["did"]

        # 创建新的Agent实例 - 全面使用新Agent系统
        if share_did_config:
            # 确保共享DID配置完整
            if not share_did_config.get('path_prefix'):
                raise ValueError(f"❌ 共享DID配置缺少 path_prefix: {base_module_name}")

            anp_agent = AgentManager.create_agent(
                anp_user_did,  cfg['name'],
                shared=True,
                prefix=share_did_config.get('path_prefix', ''),
                primary_agent=share_did_config.get('primary_agent', False)
            )
        else:
            anp_agent = AgentManager.create_agent(anp_user_did, cfg['name'], shared=False)

        # 1. agent_002: 存在 agent_register.py，优先自定义注册
        if os.path.exists(register_script_path):
            register_module = importlib.import_module(f"{base_module_name}.agent_register")
            logger.debug(f"  -> self register agent : {cfg['name']}")
            # 调用register函数注册agent
            if hasattr(register_module, "register"):
                try:
                    register_module.register(anp_agent)
                    logger.debug(f"  -> 执行register函数注册agent: {cfg['name']}")
                except Exception as e:
                    logger.error(f"❌ register函数执行失败: {cfg['name']}, 错误: {e}")
                    # 可以选择继续或者抛出异常
                logger.debug(f"  -> 执行register函数注册agent: {cfg['name']}")

            # 如果同时存在initialize_agent，要返回
            if hasattr(handlers_module, "initialize_agent"):
                logger.debug(f"  -> 调用initialize_agent进行初始化: {cfg['name']}")
                return anp_agent, handlers_module, share_did_config
            return anp_agent, None, share_did_config

        # 2. 普通配置型 agent_001 / agent_caculator
        logger.debug(f"  -> Self-created agent instance: {cfg['name']}")

        # 使用新Agent系统注册API
        for api in cfg.get("api", []):
            handler_func = getattr(handlers_module, api["handler"])

            # 使用装饰器方式注册API
            agent_api(anp_agent, api["path"], auto_wrap=True)(handler_func)
            
            # 新增：保存API配置到Agent实例
            api_config = {
                'params': api.get('params', {}),
                'summary': api.get('summary', ''),
                'result': api.get('result', {}),
                'handler': api["handler"],
                'method': api.get('method', 'POST'),
                'openapi_version': api.get('openapi_version', '3.0.0'),
                'title': api.get('title', ''),
                'version': api.get('version', '1.0.0')
            }
            
            # 计算完整路径（考虑共享DID的prefix）
            full_path = f"{anp_agent.prefix}{api['path']}" if anp_agent.prefix else api["path"]
            anp_agent.set_api_config(full_path, api_config)
            
            logger.debug(f"  - config register agent: {cfg['name']}，api:{api}")
            logger.debug(f"  - 保存API配置: {full_path} -> 参数数量: {len(api_config['params'])}")

        # 注册消息处理器（如果存在）
        LocalAgentManager._register_message_handlers_new(anp_agent, handlers_module, cfg, share_did_config)

        # 3. agent_llm: 存在 initialize_agent
        if hasattr(handlers_module, "initialize_agent"):
            logger.debug(f"  - Calling 'initialize_agent' in module: {base_module_name}.agent_handlers")
            logger.debug(f"  - pre-init agent: {cfg['name']}")
            return anp_agent, handlers_module, share_did_config
        else:
            return anp_agent, None, share_did_config

    @staticmethod
    def _register_message_handlers_new(new_agent: Agent, handlers_module, cfg: Dict, share_did_config: Optional[Dict]):
        """注册消息处理器（新Agent系统）"""
        # 在函数内部导入
        from anp_runtime.agent_decorator import agent_message_handler

        # 检查是否是共享DID模式但不是主Agent
        is_shared_non_primary = False
        if share_did_config:  # 只检查share_did_config是否存在
            is_primary = share_did_config.get('primary_agent', False)
            if not is_primary:
                is_shared_non_primary = True
                logger.info(f"ℹ️ 注意: {cfg.get('name')} 是共享DID的非主Agent，将跳过消息处理器注册 (这是预期行为)")

        # 如果已知是共享DID的非主Agent，直接跳过注册尝试
        if is_shared_non_primary:
            logger.info(f"✅ 已跳过 {cfg.get('name')} 的消息处理器注册 (共享DID非主Agent)")
            return

        # 检查是否有消息处理器
        if hasattr(handlers_module, "handle_message"):
            try:
                # 使用装饰器方式注册消息处理器
                agent_message_handler(new_agent, "*")(handlers_module.handle_message)
                logger.debug(f"  -> 注册消息处理器: {cfg.get('name')} -> DID {new_agent.anp_user_did}")
            except PermissionError as e:
                logger.warning(f"⚠️ 预期行为: {e}")

        # 检查是否有特定类型的消息处理器
        for msg_type in ["text", "command", "query", "notification"]:
            handler_name = f"handle_{msg_type}_message"
            if hasattr(handlers_module, handler_name):
                handler_func = getattr(handlers_module, handler_name)
                try:
                    # 使用装饰器方式注册消息处理器
                    agent_message_handler(new_agent, msg_type)(handler_func)
                    logger.debug(f"  -> 注册{msg_type}消息处理器: {cfg.get('name')} -> DID {new_agent.anp_user_did}")
                except PermissionError as e:
                    logger.warning(f"⚠️ 预期行为: {e}")

    @staticmethod
    def _extract_api_params(agent_obj, path: str, handler) -> Dict:
        """提取API参数，优先使用配置，回退到函数签名
        
        Args:
            agent_obj: Agent实例
            path: API路径
            handler: 处理函数
            
        Returns:
            Dict: 参数字典 {param_name: {type: str, description: str, default: any}}
        """
        params = {}
        
        # 优先使用保存的配置参数 - 修复：支持多种路径匹配策略
        if hasattr(agent_obj, 'api_configs'):
            config_params = None
            
            # 1. 直接匹配原始路径
            if path in agent_obj.api_configs:
                config_params = agent_obj.api_configs[path].get('params', {})
                logger.info(f"✅ 直接路径匹配: {path}")
            
            # 2. 如果是共享DID，尝试匹配完整路径（包含prefix）
            elif hasattr(agent_obj, 'prefix') and agent_obj.prefix:
                full_path_with_prefix = f"{agent_obj.prefix}{path}"
                if full_path_with_prefix in agent_obj.api_configs:
                    config_params = agent_obj.api_configs[full_path_with_prefix].get('params', {})
                    logger.info(f"✅ 完整路径匹配: {full_path_with_prefix} -> {path}")
            
            # 3. 反向匹配：如果path包含prefix，尝试移除prefix后查找
            elif hasattr(agent_obj, 'prefix') and agent_obj.prefix and path.startswith(agent_obj.prefix):
                original_path = path[len(agent_obj.prefix):]
                if original_path in agent_obj.api_configs:
                    config_params = agent_obj.api_configs[original_path].get('params', {})
                    logger.info(f"✅ 反向路径匹配: {path} -> {original_path}")
            
            # 处理找到的配置参数
            if config_params:
                for name, param_config in config_params.items():
                    params[name] = {
                        "type": param_config.get('type', 'Any'),
                        "description": param_config.get('description', ''),
                    }
                    # 如果有默认值，添加到参数中
                    if 'value' in param_config:
                        params[name]['default'] = param_config['value']
                
                if params:
                    logger.info(f"✅ 使用配置参数: {path} -> {len(params)} 个参数")
                    return params
        
        # 回退到函数签名分析 - 增强处理wrap_business_handler包装的函数
        try:
            sig = inspect.signature(handler)
            param_names = list(sig.parameters.keys())
            
            # 检查是否是wrap_business_handler包装的函数
            is_wrapped = hasattr(handler, '_original_func') or hasattr(handler, '__wrapped__')
            
            if is_wrapped:
                # 对于包装的函数，尝试获取原始函数签名
                original_func = getattr(handler, '_original_func', None) or getattr(handler, '__wrapped__', None)
                if original_func:
                    try:
                        original_sig = inspect.signature(original_func)
                        for name, param in original_sig.parameters.items():
                            # 跳过框架参数和self参数
                            if name not in ["self", "request_data", "request"]:
                                param_type = "Any"
                                if param.annotation != inspect._empty and hasattr(param.annotation, "__name__"):
                                    param_type = param.annotation.__name__
                                elif param.annotation != inspect._empty:
                                    param_type = str(param.annotation)
                                
                                params[name] = {
                                    "type": param_type,
                                    "description": f"Parameter {name}"
                                }
                                
                                # 如果有默认值，添加到参数中
                                if param.default != inspect._empty:
                                    params[name]['default'] = param.default
                        
                        if params:
                            logger.info(f"✅ 从包装函数提取参数: {path} -> {len(params)} 个参数")
                            return params
                    except Exception as e:
                        logger.warning(f"提取包装函数原始签名失败: {path} - {e}")
            
            # 对于非包装函数，从当前函数签名提取
            for name, param in sig.parameters.items():
                # 跳过框架参数和self参数
                if name not in ["self", "request_data", "request"]:
                    param_type = "Any"
                    if param.annotation != inspect._empty and hasattr(param.annotation, "__name__"):
                        param_type = param.annotation.__name__
                    elif param.annotation != inspect._empty:
                        param_type = str(param.annotation)
                        
                    params[name] = {
                        "type": param_type,
                        "description": f"Parameter {name}"
                    }
                    
                    # 如果有默认值，添加到参数中
                    if param.default != inspect._empty:
                        params[name]['default'] = param.default
            
            # 如果函数签名没有找到参数，尝试从函数源码中提取参数使用情况
            if not params:
                try:
                    source_params = LocalAgentManager._extract_params_from_source(handler)
                    if source_params:
                        params.update(source_params)
                        logger.info(f"📝 从源码分析提取参数: {path} -> {len(params)} 个参数")
                        return params
                except Exception as e:
                    logger.debug(f"从源码提取参数失败: {path} - {e}")
            
            if params:
                logger.info(f"🔄 使用函数签名参数: {path} -> {len(params)} 个参数")
            else:
                logger.info(f"⚠️ 未找到参数: {path} (函数签名中只有 request_data/request)")
                
        except Exception as e:
            logger.warning(f"提取函数签名参数失败: {path} - {e}")
        
        return params

    @staticmethod
    def _extract_params_from_source(handler) -> Dict:
        """从函数源码中提取参数使用情况
        
        Args:
            handler: 处理函数
            
        Returns:
            Dict: 参数字典 {param_name: {type: str, description: str, default: any}}
        """
        params = {}
        
        try:
            import ast
            import textwrap
            
            # 获取函数源码
            source = inspect.getsource(handler)
            # 去除缩进
            source = textwrap.dedent(source)
            
            # 解析AST
            tree = ast.parse(source)
            
            # 查找params.get()调用
            class ParamVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.found_params = {}
                
                def visit_Call(self, node):
                    # 查找 params.get('param_name', default_value) 模式
                    if (isinstance(node.func, ast.Attribute) and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'params' and
                        node.func.attr == 'get' and
                        len(node.args) >= 1):
                        
                        # 获取参数名
                        if isinstance(node.args[0], ast.Constant):
                            param_name = node.args[0].value
                            default_value = None
                            
                            # 获取默认值
                            if len(node.args) >= 2:
                                if isinstance(node.args[1], ast.Constant):
                                    default_value = node.args[1].value
                                elif isinstance(node.args[1], ast.Num):  # Python < 3.8 兼容
                                    default_value = node.args[1].n
                                elif isinstance(node.args[1], ast.Str):  # Python < 3.8 兼容
                                    default_value = node.args[1].s
                            
                            # 推断类型
                            param_type = "Any"
                            if default_value is not None:
                                param_type = type(default_value).__name__
                            
                            self.found_params[param_name] = {
                                "type": param_type,
                                "description": f"Parameter {param_name}",
                            }
                            
                            if default_value is not None:
                                self.found_params[param_name]['default'] = default_value
                    
                    self.generic_visit(node)
            
            visitor = ParamVisitor()
            visitor.visit(tree)
            params = visitor.found_params
            
        except Exception as e:
            logger.debug(f"源码分析失败: {e}")
        
        return params

    @staticmethod
    def generate_custom_openapi_from_router(agent: Agent) -> Dict:
        """根据 Agent 的路由生成自定义的 OpenAPI 规范"""
        did = agent.anp_user_did
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{agent.name}Agent API",
                "version": "1.0.0"
            },
            "paths": {}
        }

        # 检查是否为共享DID模式
        is_shared_did = agent.shared
        all_agents_with_same_did = []

        # 从AgentManager获取共享该DID的所有Agent
        if did in AgentManager._did_usage_registry:
            agents_info = AgentManager._did_usage_registry[did]
            # 如果有多个Agent使用同一个DID，说明是共享DID模式
            if len(agents_info) > 1:
                is_shared_did = True
                all_agents_with_same_did = [info['agent'] for info in agents_info.values()]

        if is_shared_did:
            logger.debug(f"检测到共享DID模式，DID: {did}，共有 {len(all_agents_with_same_did)} 个Agent共享")
            for shared_agent in all_agents_with_same_did:
                # 获取该Agent的路由信息
                for path, handler in shared_agent.api_routes.items():
                    # 避免重复添加路由
                    if path in openapi["paths"]:
                        continue
                    # 从处理函数获取参数信息 - 优先使用配置参数
                    params = LocalAgentManager._extract_api_params(shared_agent, path, handler)
                    properties = {name: {"type": param_info.get("type", "string")} for name, param_info in params.items()}
                    # 使用处理函数的文档字符串作为摘要
                    summary = handler.__doc__ or f"{shared_agent.name}的{path}接口"
                    openapi["paths"][path] = {
                        "post": {
                            "summary": summary,
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": properties
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "返回结果",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
        else:
            for path, handler in agent.api_routes.items():
                # 非共享DID模式，保持原有逻辑
                # 从处理函数获取参数信息 - 优先使用配置参数
                params = LocalAgentManager._extract_api_params(agent, path, handler)
                properties = {name: {"type": param_info.get("type", "string")} for name, param_info in params.items()}
                # 使用处理函数的文档字符串作为摘要
                summary = handler.__doc__ or f"{agent.name}的{path}接口"
                openapi["paths"][path] = {
                    "post": {
                        "summary": summary,
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": properties
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "返回结果",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }

        return openapi

    @staticmethod
    async def generate_and_save_agent_interfaces(agent: Agent):
        """为指定的 agent 生成并保存接口文件，按 DID 聚合所有 agent 的方法"""
        logger.debug(f"开始为 agent '{agent.name}' ({agent.anp_user_did}) 生成接口文件...")

        did = agent.anp_user_did
        user_data_manager = get_user_data_manager()
        user_data = user_data_manager.get_user_data(did)
        if not user_data:
            logger.error(f"无法找到 DID '{did}' 的用户数据，无法保存接口文件。")
            return
        user_full_path = user_data.user_dir

        # 1. 生成并保存 OpenAPI YAML 文件 (按 DID 聚合)
        try:
            openapi_data = LocalAgentManager.generate_custom_openapi_from_router_by_did(did)
            await save_interface_files(
                user_full_path=user_full_path,
                interface_data=openapi_data,
                inteface_file_name="api_interface.yaml",
                interface_file_type="YAML"
            )
            logger.debug(f"✅ 为 DID '{did}' 生成聚合 OpenAPI YAML 文件成功")
        except Exception as e:
            logger.error(f"为 DID '{did}' 生成 OpenAPI YAML 文件失败: {e}")

        # 2. 生成并保存 JSON-RPC 文件 (按 DID 聚合)
        try:
            jsonrpc_data = {
                "jsonrpc": "2.0",
                "info": {
                    "title": f"DID {did} JSON-RPC Interface",
                    "version": "0.1.0",
                    "description": f"Methods offered by DID {did}"
                },
                "methods": []
            }

            # 获取与该 DID 关联的所有 Agent
            agents_info = AgentManager.get_agent_info(did)
            if not agents_info:
                logger.warning(f"无法找到 DID '{did}' 关联的 Agent，生成空的 JSON-RPC 文件。")
            else:
                # 遍历所有 Agent，获取它们的 API 路由
                for agent_name, agent_info in agents_info.items():
                    agent_obj = agent_info['agent']
                    prefix = agent_info.get('prefix', '')

                    # 收集所有其他Agent的prefix，用于独占模式判断
                    other_prefixes = [info.get('prefix', '') for name, info in agents_info.items()
                                      if name != agent_name and info.get('prefix')]

                    # 获取该 Agent 的 API 路由
                    api_routes = {}

                    # 从 agent.api_routes 获取路由
                    if hasattr(agent_obj, 'api_routes'):
                        for path, handler in agent_obj.api_routes.items():
                            # 检查路径是否属于当前Agent（通过prefix匹配）
                            if prefix and path.startswith(prefix):
                                # 这才是属于当前Agent的路由
                                api_routes[path] = handler
                            elif not prefix and not any(path.startswith(p) for p in other_prefixes if p):
                                # 独占模式的路由，且不以其他Agent的prefix开头
                                api_routes[path] = handler

                   
                    for path, handler in api_routes.items():
                        # 路径已经是完整路径，不需要再添加prefix
                        full_path = path

                        # 从路径生成方法名
                        method_name = full_path.strip('/').replace('/', '.')

                        # 从处理函数获取参数信息 - 优先使用配置参数
                        params = LocalAgentManager._extract_api_params(agent_obj, full_path, handler)

                        # 获取处理函数的文档字符串作为摘要
                        summary = handler.__doc__ or f"{agent_obj.name}的{path}接口"

                        # 创建方法对象
                        method_obj = {
                            "name": method_name,
                            "summary": summary,
                            "description": f"由 {agent_obj.name} 提供的服务",
                            "params": params,
                            "tags": [agent_obj.name]  # 使用 agent 名称作为标签，便于分组
                        }

                        # 添加元数据
                        method_obj["meta"] = {
                            "openapi": "3.0.0",
                            "info": {"title": f"{agent_obj.name} API", "version": "1.0.0"},
                            "httpMethod": "POST",
                            "endpoint": full_path
                        }

                        # 添加到方法列表
                        jsonrpc_data["methods"].append(method_obj)
                        logger.debug(f"  - 添加JSON-RPC方法: {method_name} <- {full_path}")

            # 保存JSON-RPC文件
            await save_interface_files(
                user_full_path=user_full_path,
                interface_data=jsonrpc_data,
                inteface_file_name="api_interface.json",
                interface_file_type="JSON"
            )
            logger.debug(f"✅ 为 DID '{did}' 生成聚合 JSON-RPC 文件成功")
        except Exception as e:
            logger.error(f"为 DID '{did}' 生成 JSON-RPC 文件失败: {e}")

        # 3. 生成并保存 ad.json 文件
        try:
            # 为该 DID 生成 ad.json
            await LocalAgentManager.generate_and_save_did_ad_json(did)
        except Exception as e:
            logger.error(f"为 DID '{did}' 生成 ad.json 文件失败: {e}")

    @staticmethod
    def generate_custom_openapi_from_router_by_did(did: str) -> Dict:
        """根据 DID 生成自定义的 OpenAPI 规范，包含该 DID 下所有 Agent 的 API 路由"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": f"DID {did} API",
                "version": "1.0.0",
                "description": f"所有与 DID {did} 关联的服务接口"
            },
            "paths": {}
        }

        # 获取与该 DID 关联的所有 Agent
        agents_info = AgentManager.get_agent_info(did)
        if not agents_info:
            logger.warning(f"无法找到 DID '{did}' 关联的 Agent，生成空的 OpenAPI 规范。")
            return openapi

        # 遍历所有 Agent，获取它们的 API 路由
        for agent_name, agent_info in agents_info.items():
            agent = agent_info['agent']
            prefix = agent_info.get('prefix', '')

            # 收集所有其他Agent的prefix，用于独占模式判断
            other_prefixes = [info.get('prefix', '') for name, info in agents_info.items()
                              if name != agent_name and info.get('prefix')]

            # 获取该 Agent 的 API 路由
            api_routes = {}

            # 从 agent.api_routes 获取路由
            if hasattr(agent, 'api_routes'):
                for path, handler in agent.api_routes.items():
                    # 检查路径是否属于当前Agent（通过prefix匹配）
                    if prefix and path.startswith(prefix):
                        # 这才是属于当前Agent的路由
                        api_routes[path] = handler
                    elif not prefix and not any(path.startswith(p) for p in other_prefixes if p):
                        # 独占模式的路由，且不以其他Agent的prefix开头
                        api_routes[path] = handler



            for path, handler in api_routes.items():
                # 路径已经是完整路径，不需要再添加prefix
                full_path = path

                # 从处理函数获取参数信息 - 优先使用配置参数
                params = LocalAgentManager._extract_api_params(agent, full_path, handler)
                properties = {name: {"type": param_info.get("type", "string")} for name, param_info in params.items()}

                # 获取处理函数的文档字符串作为摘要
                summary = handler.__doc__ or f"{agent.name}的{path}接口"

                # 添加到 OpenAPI 规范
                openapi["paths"][full_path] = {
                    "post": {
                        "summary": summary,
                        "description": f"由 {agent.name} 提供的服务",
                        "tags": [agent.name],  # 使用 agent 名称作为标签，便于分组
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": properties
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "返回结果",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }

        return openapi

    @staticmethod
    async def generate_and_save_did_ad_json(did: str):
        """为指定的 DID 生成并保存 ad.json 文件，包含该 DID 的所有服务"""
        logger.debug(f"开始为 DID '{did}' 生成 ad.json...")

        # 获取用户数据
        user_data_manager = get_user_data_manager()
        user_data = user_data_manager.get_user_data(did)
        if not user_data:
            logger.error(f"无法找到 DID '{did}' 的用户数据，无法保存 ad.json。")
            return
        user_full_path = user_data.user_dir

        # 获取与该 DID 关联的所有 Agent
        agents_info = AgentManager.get_agent_info(did)
        if not agents_info:
            logger.error(f"无法找到 DID '{did}' 关联的 Agent，无法生成 ad.json。")
            return

        # 确定主 Agent（如果有）
        primary_agent = None
        for agent_name, agent_info in agents_info.items():
            if agent_info.get('primary_agent', False):
                primary_agent = agent_info['agent']
                break

        # 如果没有主 Agent，使用第一个 Agent
        if not primary_agent and agents_info:
            primary_agent = next(iter(agents_info.values()))['agent']

        # 基本 ad.json 结构
        ad_json = {
            "@context": {
                "@vocab": "https://schema.org/",
                "did": "https://w3id.org/did#",
                "ad": "https://agent-network-protocol.com/ad#"
            },
            "@type": "ad:AgentDescription",
            "name": f"DID Services for {did}",
            "owner": {
                "name": f"{did} 的拥有者",
                "@id": did
            },
            "description": f"Services provided by DID {did}",
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "security_definitions": {
                "didwba_sc": {
                    "scheme": "didwba",
                    "in": "header",
                    "name": "Authorization"
                }
            },
            "ad:interfaces": []
        }

        # 添加标准接口
        interfaces = []

        # 从 DID 获取主机和端口
        from urllib.parse import quote, unquote
        parts = did.split(':')
        hostname = parts[2]
        # 解码端口部分，如果存在
        if '%3A' in hostname:
            hostname = unquote(hostname)  # 将 %3A 解码为 :

        host, port = hostname.split(':') if ':' in hostname else (hostname, '80')

        interfaces.extend([
            {
                "@type": "ad:NaturalLanguageInterface",
                "protocol": "YAML",
                "url": f"http://{host}:{port}/wba/user/{quote(did)}/nlp_interface.yaml",
                "description": "提供自然语言交互接口的OpenAPI的YAML文件"
            },
            {
                "@type": "ad:StructuredInterface",
                "protocol": "YAML",
                "url": f"http://{host}:{port}/wba/user/{quote(did)}/api_interface.yaml",
                "description": "智能体的 YAML 描述的接口调用方法"
            },
            {
                "@type": "ad:StructuredInterface",
                "protocol": "JSON",
                "url": f"http://{host}:{port}/wba/user/{quote(did)}/api_interface.json",
                "description": "智能体的 JSON RPC 描述的接口调用方法"
            }
        ])

        # 聚合所有 Agent 的 API 路由
        for agent_name, agent_info in agents_info.items():
            agent = agent_info['agent']
            prefix = agent_info.get('prefix', '')

            # 收集所有其他Agent的prefix，用于独占模式判断
            other_prefixes = [info.get('prefix', '') for name, info in agents_info.items()
                              if name != agent_name and info.get('prefix')]

            # 获取该 Agent 的 API 路由
            if hasattr(agent, 'api_routes'):
                for path, handler in agent.api_routes.items():
                    # 检查路径是否属于当前Agent（通过prefix匹配）
                    if prefix and path.startswith(prefix):
                        # 这才是属于当前Agent的路由
                        full_path = path  # 路径已经包含prefix，不需要再添加
                        handler_name = handler.__name__ if hasattr(handler, '__name__') else 'unknown'
                        interfaces.append({
                            "@type": "ad:StructuredInterface",
                            "protocol": "HTTP",
                            "name": full_path.replace('/', '_').strip('_'),
                            "url": f"/agent/api/{did}{full_path}",
                            "description": f"{agent.name} API 路径 {full_path} 的端点 (处理器: {handler_name})"
                        })
                    elif not prefix and not any(path.startswith(p) for p in other_prefixes if p):
                        # 独占模式的路由，且不以其他Agent的prefix开头
                        full_path = path
                        handler_name = handler.__name__ if hasattr(handler, '__name__') else 'unknown'
                        interfaces.append({
                            "@type": "ad:StructuredInterface",
                            "protocol": "HTTP",
                            "name": full_path.replace('/', '_').strip('_'),
                            "url": f"/agent/api/{did}{full_path}",
                            "description": f"{agent.name} API 路径 {full_path} 的端点 (处理器: {handler_name})"
                        })

            

        # 去重逻辑
        seen_urls = set()
        unique_interfaces = []
        for interface in interfaces:
            url = interface.get('url')
            if url not in seen_urls:
                unique_interfaces.append(interface)
                seen_urls.add(url)

        ad_json["ad:interfaces"] = unique_interfaces


        # 保存 ad.json
        ad_json_path = Path(user_full_path) / "ad.json"
        ad_json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(ad_json_path, 'w', encoding='utf-8') as f:
            json.dump(ad_json, f, ensure_ascii=False, indent=2)

        logger.debug(f"✅ 为 DID '{did}' 生成 ad.json 成功: {ad_json_path}")
