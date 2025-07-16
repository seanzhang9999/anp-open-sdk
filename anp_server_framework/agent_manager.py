import json
import os
import importlib
import inspect
from pathlib import Path

import yaml
import logging
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime

from anp_sdk.anp_user_local_data import get_user_data_manager
from anp_sdk.anp_user import ANPUser
from anp_sdk.config import UnifiedConfig
from anp_sdk.did.did_tool import parse_wba_did_host_port
from anp_server_framework.anp_service.anp_tool import wrap_business_handler
from anp_server_framework.agent import Agent
from urllib.parse import quote
logger = logging.getLogger(__name__)


class AgentManager:
    """统一的Agent管理器 - 负责Agent创建、注册和冲突管理"""
    
    # 类级别的DID使用注册表
    _did_usage_registry: Dict[str, Dict[str, Dict[str, Any]]] = {}  # {did: {agent_name: agent_info}}

    @classmethod
    def get_agent(cls, did: str, agent_name: str) -> Optional[Agent]:
        """全局单例：根据 did + agent_name 拿到 Agent 实例"""
        info = cls.get_agent_info(did, agent_name)
        return info['agent'] if info else None


    @classmethod
    def create_agent(cls, anp_user: ANPUser, name: str, 
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
        did = anp_user.id
        
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
        agent = Agent(anp_user, name, shared, prefix, primary_agent)
        
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
        from anp_server_framework.agent_decorator import agent_api, agent_message_handler
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
                anp_user = ANPUser.from_did(shared_did)
                logger.debug(f"  -> 共享DID Agent {cfg['name']} 使用共享DID: {shared_did}")
            except ValueError as e:
                logger.warning(f"共享DID Agent {cfg['name']} 无法获取共享DID {shared_did} 的用户数据: {e}")
                return None, None, share_did_config
        else:
            # 独立DID的Agent
            anp_user = ANPUser.from_did(cfg["did"])

        anp_user.name = cfg["name"]

        # 创建新的Agent实例 - 全面使用新Agent系统
        if share_did_config:
            # 确保共享DID配置完整
            if not share_did_config.get('path_prefix'):
                raise ValueError(f"❌ 共享DID配置缺少 path_prefix: {anp_user.name}")

            anp_agent = AgentManager.create_agent(
                anp_user, anp_user.name,
                shared=True,
                prefix=share_did_config.get('path_prefix', ''),
                primary_agent=share_did_config.get('primary_agent', False)
            )
        else:
            anp_agent = AgentManager.create_agent(anp_user, anp_user.name, shared=False)


        # 1. agent_002: 存在 agent_register.py，优先自定义注册
        if os.path.exists(register_script_path):
            register_module = importlib.import_module(f"{base_module_name}.agent_register")
            logger.debug(f"  -> self register agent : {anp_user.name}")
            # 调用register函数注册agent
            if hasattr(register_module, "register"):
                try:
                    register_module.register(anp_agent)
                    logger.debug(f"  -> 执行register函数注册agent: {anp_user.name}")
                except Exception as e:
                    logger.error(f"❌ register函数执行失败: {anp_user.name}, 错误: {e}")
                    # 可以选择继续或者抛出异常
                logger.debug(f"  -> 执行register函数注册agent: {anp_user.name}")

            # 如果同时存在initialize_agent，要返回
            if hasattr(handlers_module, "initialize_agent"):
                logger.debug(f"  -> 调用initialize_agent进行初始化: {anp_user.name}")
                return anp_agent, handlers_module, share_did_config
            return anp_agent, None, share_did_config

        # 2. agent_llm: 存在 initialize_agent
        if hasattr(handlers_module, "initialize_agent"):
            logger.debug(f"  - Calling 'initialize_agent' in module: {base_module_name}.agent_handlers")
            logger.debug(f"  - pre-init agent: {anp_user.name}")
            return anp_agent, handlers_module, share_did_config


        # 3. 普通配置型 agent_001 / agent_caculator
        logger.debug(f"  -> Self-created agent instance: {anp_user.name}")
        

        # 使用新Agent系统注册API
        for api in cfg.get("api", []):
            handler_func = getattr(handlers_module, api["handler"])
            
            # 使用装饰器方式注册API
            agent_api(anp_agent, api["path"], auto_wrap=True)(handler_func)
            logger.debug(f"  - config register agent: {anp_user.name}，api:{api}")
        
        # 注册消息处理器（如果存在）
        LocalAgentManager._register_message_handlers_new(anp_agent, handlers_module, cfg, share_did_config)
        
        return anp_agent, None, share_did_config


    @staticmethod
    def _register_message_handlers_new(new_agent: Agent, handlers_module, cfg: Dict, share_did_config: Optional[Dict]):
        """注册消息处理器（新Agent系统）"""
        # 在函数内部导入
        from anp_server_framework.agent_decorator import agent_message_handler

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
                logger.debug(f"  -> 注册消息处理器: {cfg.get('name')} -> DID {new_agent.anp_user.id}")
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
                    logger.debug(f"  -> 注册{msg_type}消息处理器: {cfg.get('name')} -> DID {new_agent.anp_user.id}")
                except PermissionError as e:
                    logger.warning(f"⚠️ 预期行为: {e}")

    @staticmethod
    def generate_custom_openapi_from_router(agent: Agent) -> Dict:
        """根据 Agent 的路由生成自定义的 OpenAPI 规范"""
        did = agent.anp_user_id
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
                    sig = inspect.signature(handler)
                    param_names = [p for p in sig.parameters if p not in ("request_data", "request")]
                    properties = {name: {"type": "string"} for name in param_names}
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
                sig = inspect.signature(handler)
                param_names = [p for p in sig.parameters if p not in ("request_data", "request")]
                properties = {name: {"type": "string"} for name in param_names}
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
        logger.debug(f"开始为 agent '{agent.name}' ({agent.anp_user_id}) 生成接口文件...")

        did = agent.anp_user_id
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

                    # 获取该 Agent 的 API 路由
                    api_routes = {}

                    # 从 agent.api_routes 获取路由
                    if hasattr(agent_obj, 'api_routes'):
                        api_routes.update(agent_obj.api_routes)

                    # 从 agent.anp_user.api_routes 获取路由（如果存在）
                    if hasattr(agent_obj, 'anp_user') and hasattr(agent_obj.anp_user, 'api_routes'):
                        api_routes.update(agent_obj.anp_user.api_routes)

                    for path, handler in api_routes.items():
                        # 构建完整路径
                        full_path = f"{prefix}{path}" if prefix else path

                        # 从路径生成方法名
                        method_name = full_path.strip('/').replace('/', '.')

                        # 从处理函数获取参数信息
                        sig = inspect.signature(handler)
                        params = {
                            name: {"type": param.annotation.__name__ if (
                                    param.annotation != inspect._empty and hasattr(param.annotation,
                                                                                   "__name__")) else "Any"}
                            for name, param in sig.parameters.items() if name not in ["self", "request_data", "request"]
                        }

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

            # 获取该 Agent 的 API 路由
            api_routes = {}

            # 从 agent.api_routes 获取路由
            if hasattr(agent, 'api_routes'):
                api_routes.update(agent.api_routes)

            # 从 agent.anp_user.api_routes 获取路由（如果存在）
            if hasattr(agent, 'anp_user') and hasattr(agent.anp_user, 'api_routes'):
                api_routes.update(agent.anp_user.api_routes)

            for path, handler in api_routes.items():
                # 构建完整路径
                full_path = f"{prefix}{path}" if prefix else path

                # 从处理函数获取参数信息
                sig = inspect.signature(handler)
                param_names = [p for p in sig.parameters if p not in ("request_data", "request")]
                properties = {name: {"type": "string"} for name in param_names}

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

            # 获取该 Agent 的 API 路由
            if hasattr(agent, 'api_routes'):
                for path, handler in agent.api_routes.items():
                    full_path = f"{prefix}{path}" if prefix else path
                    handler_name = handler.__name__ if hasattr(handler, '__name__') else 'unknown'
                    interfaces.append({
                        "@type": "ad:StructuredInterface",
                        "protocol": "HTTP",
                        "name": full_path.replace('/', '_').strip('_'),
                        "url": f"/agent/api/{did}{full_path}",
                        "description": f"{agent.name} API 路径 {full_path} 的端点 (处理器: {handler_name})"
                    })

            # 如果 agent 有 anp_user 属性，也获取其 API 路由
            if hasattr(agent, 'anp_user') and hasattr(agent.anp_user, 'api_routes'):
                for path, handler in agent.anp_user.api_routes.items():
                    full_path = f"{prefix}{path}" if prefix else path
                    handler_name = handler.__name__ if hasattr(handler, '__name__') else 'unknown'
                    interfaces.append({
                        "@type": "ad:StructuredInterface",
                        "protocol": "HTTP",
                        "name": full_path.replace('/', '_').strip('_'),
                        "url": f"/agent/api/{did}{full_path}",
                        "description": f"{agent.name} API 路径 {full_path} 的端点 (处理器: {handler_name})"
                    })

        ad_json["ad:interfaces"] = interfaces

        # 保存 ad.json
        ad_json_path = Path(user_full_path) / "ad.json"
        ad_json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(ad_json_path, 'w', encoding='utf-8') as f:
            json.dump(ad_json, f, ensure_ascii=False, indent=2)

        logger.debug(f"✅ 为 DID '{did}' 生成 ad.json 成功: {ad_json_path}")

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

