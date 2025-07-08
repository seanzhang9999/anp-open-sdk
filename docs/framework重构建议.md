# ANP Open SDK Framework 重构建议

## 目录

1. [执行摘要](#执行摘要)
2. [当前架构分析](#当前架构分析)
3. [问题识别](#问题识别)
4. [重构目标](#重构目标)
5. [新架构设计](#新架构设计)
6. [详细实施计划](#详细实施计划)
7. [代码示例](#代码示例)
8. [测试策略](#测试策略)
9. [迁移策略](#迁移策略)
10. [预期收益](#预期收益)

## 执行摘要

ANP Open SDK Framework 当前已经实现了丰富的功能，但随着功能的增加，框架结构变得复杂，存在职责不清、耦合度高等问题。本文档提出了一个全面的重构方案，旨在通过清晰的分层架构、服务化设计和插件化机制，提升框架的可维护性、可扩展性和性能。

## 当前架构分析

### 现有功能梳理

基于对 `demo_anp_open_sdk_framework/framework_demo.py` 的分析，当前框架包含以下核心功能：

1. **动态 Agent 加载** - 从目录动态加载和管理智能体
2. **HTTP API 暴露** - 智能体可以暴露 HTTP API 和本地方法
3. **统一调用机制** - 通过 UnifiedCaller 和 UnifiedCrawler 调用和爬取 API
4. **主智能体** - MasterAgent 作为本地主智能体处理复杂任务
5. **服务封装** - 基于 HTTP API 封装消息组等新服务
6. **外围能力注入** - 提供用户管理、DID 解析等上下文能力
7. **智能体描述服务** - 生成智能体描述信息，管理智能体间联系
8. **持久化考虑** - 计划从文件持久化迁移到数据库
9. **DID 文档托管** - 处理 DID 文档的托管与发布
10. **多智能体路由** - 一个端口下的多 DID 智能体路由

### 当前目录结构

```
anp_open_sdk_framework/
├── __init__.py
├── agent_manager.py          # Agent 管理
├── master_agent.py           # 主智能体
├── unified_caller.py         # 统一调用器
├── unified_crawler.py        # 统一爬虫
├── adapter_auth/             # 认证适配器
├── adapter_transport/        # 传输适配器
├── adapter_user_data/        # 用户数据适配器
├── auth/                     # 认证相关
├── local_methods/            # 本地方法管理
└── service/                  # 服务层
    ├── interaction/          # 交互服务（ANPTool、消息组等）
    ├── publisher/            # 发布服务（DID 托管）
    └── router/               # 路由服务（多智能体路由）
```

## 问题识别

### 1. 架构问题

- **职责不清**: `ANPTool` 同时承担网络调用、本地调用、认证、爬虫等多重职责
- **层次混乱**: Service 层包含了从底层工具到高层业务逻辑的各种功能
- **耦合严重**: 各组件之间存在复杂的相互依赖

### 2. 代码组织问题

- **模块边界模糊**: 难以确定新功能应该放在哪个模块
- **重复代码**: 相似功能在不同地方重复实现
- **测试困难**: 组件耦合导致单元测试难以编写

### 3. 扩展性问题

- **插件机制缺失**: 添加新功能需要修改核心代码
- **配置不灵活**: 功能启用/禁用需要修改代码
- **标准支持不足**: 难以集成 MCP 等标准协议

## 重构目标

### 核心目标

1. **职责分离** - 每个模块有清晰的单一职责
2. **可扩展性** - 通过插件机制轻松添加新功能
3. **可维护性** - 降低耦合度，提高代码质量
4. **性能优化** - 减少不必要的依赖和调用开销
5. **标准兼容** - 原生支持 MCP 等标准协议

### 具体指标

- 单元测试覆盖率 > 80%
- 模块间依赖深度 < 3 层
- 新功能开发时间减少 50%
- 支持运行时插件加载/卸载

## 新架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  用户应用、Demo、测试程序                                      │
├─────────────────────────────────────────────────────────────┤
│                  Orchestration Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   MasterAgent   │  │ WorkflowEngine  │  │ TaskScheduler   │ │
│  │   (任务编排)     │  │   (工作流)      │  │   (任务调度)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  AgentService   │  │CommunicationSvc │  │ DiscoveryService│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │PublishingService│  │  RoutingService │  │ SecurityService │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Core Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ UnifiedCaller   │  │UnifiedCrawler   │  │LocalMethodsMgr  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Tools Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   MCP Tools     │  │  ANP Tools      │  │Integration Tools│ │
│  │ (通用工具)       │  │ (框架特化)       │  │  (组合工具)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Adapter Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  AuthAdapter    │  │TransportAdapter │  │ StorageAdapter  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Core SDK                               │
│  ANP 协议实现、DID 管理、基础认证                              │
└─────────────────────────────────────────────────────────────┘
```

### 新目录结构

```
anp_open_sdk_framework/
├── __init__.py
├── config/                          # 配置管理
│   ├── __init__.py
│   ├── framework_config.py          # 框架配置
│   └── service_registry.py          # 服务注册表
│
├── orchestration/                   # 编排层
│   ├── __init__.py
│   ├── master_agent.py             # 重构后的主智能体
│   ├── workflow_engine.py          # 工作流引擎
│   ├── task_scheduler.py           # 任务调度器
│   └── execution_context.py        # 执行上下文
│
├── services/                       # 服务层
│   ├── __init__.py
│   ├── agent/                      # 智能体管理服务
│   │   ├── __init__.py
│   │   ├── agent_manager.py       # 智能体管理器
│   │   ├── lifecycle_manager.py   # 生命周期管理
│   │   └── registry_service.py    # 注册服务
│   ├── communication/              # 通信服务
│   │   ├── __init__.py
│   │   ├── message_service.py     # 消息服务
│   │   ├── p2p_service.py         # 点对点通信
│   │   └── group_service.py       # 群组通信
│   ├── discovery/                  # 发现服务
│   │   ├── __init__.py
│   │   ├── resource_discovery.py  # 资源发现
│   │   ├── agent_discovery.py     # 智能体发现
│   │   └── api_discovery.py       # API 发现
│   ├── publishing/                 # 发布服务
│   │   ├── __init__.py
│   │   ├── did_publishing.py      # DID 发布
│   │   ├── document_hosting.py    # 文档托管
│   │   └── mail_backend.py        # 邮件后端
│   ├── routing/                    # 路由服务
│   │   ├── __init__.py
│   │   ├── request_router.py      # 请求路由
│   │   ├── session_manager.py     # 会话管理
│   │   └── contact_manager.py     # 联系人管理
│   └── security/                   # 安全服务
│       ├── __init__.py
│       ├── auth_service.py        # 认证服务
│       └── permission_service.py  # 权限服务
│
├── core/                           # 核心层
│   ├── __init__.py
│   ├── unified_caller.py           # 简化的统一调用器
│   ├── unified_crawler.py          # 简化的统一爬虫
│   ├── local_methods/              # 本地方法管理
│   │   ├── __init__.py
│   │   ├── method_manager.py      # 方法管理器
│   │   ├── method_registry.py     # 方法注册表
│   │   └── doc_generator.py       # 文档生成器
│   └── interfaces/                 # 核心接口定义
│       ├── __init__.py
│       ├── caller_interface.py    # 调用器接口
│       ├── crawler_interface.py   # 爬虫接口
│       └── service_interface.py   # 服务接口
│
├── tools/                          # 工具层
│   ├── __init__.py
│   ├── mcp/                        # MCP 工具集成
│   │   ├── __init__.py
│   │   ├── mcp_client.py          # MCP 客户端
│   │   └── mcp_bridge.py          # MCP 桥接器
│   ├── anp/                        # ANP 特化工具
│   │   ├── __init__.py
│   │   ├── network_tool.py        # 网络工具
│   │   ├── crawler_tool.py        # 爬虫工具
│   │   ├── analysis_tool.py       # 分析工具
│   │   └── did_tool.py            # DID 工具
│   └── integration/                # 集成工具
│       ├── __init__.py
│       ├── tool_orchestrator.py   # 工具编排器
│       └── composite_tools.py     # 组合工具
│
├── adapters/                       # 适配器层
│   ├── __init__.py
│   ├── auth/                       # 认证适配器
│   │   ├── __init__.py
│   │   ├── auth_adapter.py        # 认证适配器
│   │   └── did_resolver.py        # DID 解析器
│   ├── transport/                  # 传输适配器
│   │   ├── __init__.py
│   │   ├── http_transport.py      # HTTP 传输
│   │   └── websocket_transport.py # WebSocket 传输
│   ├── storage/                    # 存储适配器
│   │   ├── __init__.py
│   │   ├── file_storage.py        # 文件存储
│   │   └── database_storage.py    # 数据库存储
│   └── external/                   # 外部系统适配器
│       ├── __init__.py
│       └── llm_adapter.py         # LLM 适配器
│
├── plugins/                        # 插件系统
│   ├── __init__.py
│   ├── plugin_manager.py           # 插件管理器
│   ├── plugin_interface.py         # 插件接口
│   └── builtin_plugins/            # 内置插件
│
└── utils/                          # 工具函数
    ├── __init__.py
    ├── dependency_injection.py     # 依赖注入
    ├── event_system.py             # 事件系统
    └── metrics.py                  # 指标收集
```

### 核心设计原则

1. **单一职责原则** - 每个模块只负责一个功能领域
2. **依赖倒置原则** - 高层模块不依赖低层模块，都依赖抽象
3. **开闭原则** - 对扩展开放，对修改关闭
4. **接口隔离原则** - 使用多个专门的接口，而不是单一的总接口
5. **迪米特法则** - 一个对象应该对其他对象有最少的了解

## 详细实施计划

### 阶段 1: 基础架构搭建（2-3 周）

#### 目标
建立新的目录结构和基础框架，实现核心基础设施。

#### 任务清单

1. **创建新目录结构**
   ```bash
   # 创建完整的目录结构
   mkdir -p anp_open_sdk_framework/{config,orchestration,services/{agent,communication,discovery,publishing,routing,security},core/{interfaces,local_methods},tools/{mcp,anp,integration},adapters/{auth,transport,storage,external},plugins/builtin_plugins,utils}
   ```

2. **实现依赖注入容器**
   ```python
   # utils/dependency_injection.py
   from typing import Type, Dict, Any, Callable
   import inspect
   
   class DIContainer:
       def __init__(self):
           self._services: Dict[Type, Callable] = {}
           self._singletons: Dict[Type, Any] = {}
       
       def register(self, interface: Type, implementation: Type, singleton: bool = True):
           """注册服务"""
           self._services[interface] = implementation
           if not singleton:
               self._singletons.pop(interface, None)
       
       def resolve(self, interface: Type) -> Any:
           """解析服务"""
           if interface in self._singletons:
               return self._singletons[interface]
           
           if interface not in self._services:
               raise ValueError(f"Service {interface} not registered")
           
           implementation = self._services[interface]
           
           # 自动注入依赖
           sig = inspect.signature(implementation.__init__)
           kwargs = {}
           for param_name, param in sig.parameters.items():
               if param_name == 'self':
                   continue
               if param.annotation != param.empty:
                   kwargs[param_name] = self.resolve(param.annotation)
           
           instance = implementation(**kwargs)
           
           if interface not in self._singletons:
               self._singletons[interface] = instance
           
           return instance
   ```

3. **定义核心接口**
   ```python
   # core/interfaces/service_interface.py
   from abc import ABC, abstractmethod
   from typing import Dict, Any
   
   class ServiceInterface(ABC):
       """所有服务的基础接口"""
       
       @abstractmethod
       async def initialize(self, config: Dict[str, Any]) -> None:
           """初始化服务"""
           pass
       
       @abstractmethod
       async def cleanup(self) -> None:
           """清理服务资源"""
           pass
       
       @abstractmethod
       def get_status(self) -> Dict[str, Any]:
           """获取服务状态"""
           pass
   ```

4. **实现配置管理系统**
   ```python
   # config/framework_config.py
   import yaml
   from typing import Dict, Any, List
   from pathlib import Path
   
   class FrameworkConfig:
       def __init__(self, config_file: str):
           self.config_file = Path(config_file)
           self.config_data: Dict[str, Any] = {}
           self.enabled_services: List[str] = []
           self.service_configs: Dict[str, Dict[str, Any]] = {}
           self.plugin_configs: Dict[str, Dict[str, Any]] = {}
           
       def load_config(self) -> None:
           """加载配置文件"""
           with open(self.config_file, 'r') as f:
               self.config_data = yaml.safe_load(f)
           
           self.enabled_services = self.config_data.get('enabled_services', [])
           self.service_configs = self.config_data.get('services', {})
           self.plugin_configs = self.config_data.get('plugins', {})
       
       def get_service_config(self, service_name: str) -> Dict[str, Any]:
           """获取服务配置"""
           return self.service_configs.get(service_name, {})
   ```

5. **实现事件系统**
   ```python
   # utils/event_system.py
   from typing import Dict, List, Callable, Any
   import asyncio
   
   class EventSystem:
       def __init__(self):
           self._handlers: Dict[str, List[Callable]] = {}
       
       def on(self, event_name: str, handler: Callable) -> None:
           """注册事件处理器"""
           if event_name not in self._handlers:
               self._handlers[event_name] = []
           self._handlers[event_name].append(handler)
       
       async def emit(self, event_name: str, *args, **kwargs) -> None:
           """触发事件"""
           if event_name in self._handlers:
               tasks = []
               for handler in self._handlers[event_name]:
                   if asyncio.iscoroutinefunction(handler):
                       tasks.append(handler(*args, **kwargs))
                   else:
                       handler(*args, **kwargs)
               
               if tasks:
                   await asyncio.gather(*tasks)
   ```

### 阶段 2: 服务层重构（3-4 周）

#### 目标
将现有功能按服务边界重新组织，实现清晰的服务化架构。

#### 任务清单

1. **智能体管理服务**
   ```python
   # services/agent/agent_manager.py
   from typing import Dict, List, Optional
   from core.interfaces.service_interface import ServiceInterface
   from anp_open_sdk.anp_sdk_agent import LocalAgent
   
   class AgentManager(ServiceInterface):
       def __init__(self):
           self.agents: Dict[str, LocalAgent] = {}
           self.agent_metadata: Dict[str, Dict] = {}
       
       async def initialize(self, config: Dict[str, Any]) -> None:
           """初始化智能体管理服务"""
           # 加载配置的智能体
           agent_configs = config.get('agents', [])
           for agent_config in agent_configs:
               await self.load_agent(agent_config)
       
       async def cleanup(self) -> None:
           """清理所有智能体"""
           for agent_id in list(self.agents.keys()):
               await self.unregister_agent(agent_id)
       
       def get_status(self) -> Dict[str, Any]:
           """获取服务状态"""
           return {
               'active_agents': len(self.agents),
               'agent_list': list(self.agents.keys())
           }
       
       async def register_agent(self, agent: LocalAgent, metadata: Dict = None) -> str:
           """注册智能体"""
           agent_id = str(agent.id)
           self.agents[agent_id] = agent
           self.agent_metadata[agent_id] = metadata or {}
           return agent_id
       
       async def unregister_agent(self, agent_id: str) -> bool:
           """注销智能体"""
           if agent_id in self.agents:
               agent = self.agents.pop(agent_id)
               self.agent_metadata.pop(agent_id, None)
               # 执行清理逻辑
               if hasattr(agent, 'cleanup'):
                   await agent.cleanup()
               return True
           return False
       
       def get_agent(self, agent_id: str) -> Optional[LocalAgent]:
           """获取智能体实例"""
           return self.agents.get(agent_id)
       
       def list_agents(self) -> List[Dict[str, Any]]:
           """列出所有智能体"""
           return [
               {
                   'id': agent_id,
                   'name': agent.name,
                   'metadata': self.agent_metadata.get(agent_id, {})
               }
               for agent_id, agent in self.agents.items()
           ]
       
       async def load_agent(self, agent_config: Dict[str, Any]) -> Optional[str]:
           """从配置加载智能体"""
           # 实现动态加载逻辑
           pass
   ```

2. **通信服务**
   ```python
   # services/communication/message_service.py
   from typing import Dict, Any, List, Optional
   from core.interfaces.service_interface import ServiceInterface
   from dataclasses import dataclass
   from datetime import datetime
   
   @dataclass
   class Message:
       from_did: str
       to_did: str
       content: Any
       timestamp: datetime
       message_type: str = "text"
       metadata: Dict[str, Any] = None
   
   class MessageService(ServiceInterface):
       def __init__(self, agent_manager):
           self.agent_manager = agent_manager
           self.message_queue: Dict[str, List[Message]] = {}
           self.message_handlers: Dict[str, List[Callable]] = {}
       
       async def initialize(self, config: Dict[str, Any]) -> None:
           """初始化消息服务"""
           self.max_queue_size = config.get('max_queue_size', 1000)
           self.enable_persistence = config.get('enable_persistence', False)
       
       async def cleanup(self) -> None:
           """清理消息队列"""
           self.message_queue.clear()
           self.message_handlers.clear()
       
       def get_status(self) -> Dict[str, Any]:
           """获取服务状态"""
           return {
               'queued_messages': sum(len(q) for q in self.message_queue.values()),
               'registered_handlers': len(self.message_handlers)
           }
       
       async def send_message(self, from_did: str, to_did: str, 
                            content: Any, message_type: str = "text",
                            metadata: Dict[str, Any] = None) -> bool:
           """发送消息到指定智能体"""
           message = Message(
               from_did=from_did,
               to_did=to_did,
               content=content,
               timestamp=datetime.now(),
               message_type=message_type,
               metadata=metadata or {}
           )
           
           # 检查目标智能体是否存在
           target_agent = self.agent_manager.get_agent(to_did)
           if not target_agent:
               return False
           
           # 添加到消息队列
           if to_did not in self.message_queue:
               self.message_queue[to_did] = []
           
           self.message_queue[to_did].append(message)
           
           # 触发消息处理器
           await self._trigger_handlers(to_did, message)
           
           return True
       
       async def broadcast_message(self, from_did: str, content: Any,
                                 message_type: str = "text",
                                 metadata: Dict[str, Any] = None) -> int:
           """广播消息到所有智能体"""
           agents = self.agent_manager.list_agents()
           sent_count = 0
           
           for agent_info in agents:
               agent_id = agent_info['id']
               if agent_id != from_did:  # 不发送给自己
                   success = await self.send_message(
                       from_did, agent_id, content, message_type, metadata
                   )
                   if success:
                       sent_count += 1
           
           return sent_count
       
       def register_handler(self, agent_id: str, handler: Callable) -> None:
           """注册消息处理器"""
           if agent_id not in self.message_handlers:
               self.message_handlers[agent_id] = []
           self.message_handlers[agent_id].append(handler)
       
       async def _trigger_handlers(self, agent_id: str, message: Message) -> None:
           """触发消息处理器"""
           if agent_id in self.message_handlers:
               for handler in self.message_handlers[agent_id]:
                   await handler(message)
   ```

3. **发现服务**
   ```python
   # services/discovery/resource_discovery.py
   from typing import Dict, List, Any, Optional
   from core.interfaces.service_interface import ServiceInterface
   from dataclasses import dataclass
   
   @dataclass
   class Resource:
       resource_id: str
       resource_type: str  # 'agent', 'api', 'method'
       name: str
       description: str
       metadata: Dict[str, Any]
       agent_id: Optional[str] = None
   
   class ResourceDiscoveryService(ServiceInterface):
       def __init__(self, agent_manager):
           self.agent_manager = agent_manager
           self.resource_registry: Dict[str, Resource] = {}
           self.resource_index: Dict[str, List[str]] = {
               'agent': [],
               'api': [],
               'method': []
           }
       
       async def initialize(self, config: Dict[str, Any]) -> None:
           """初始化发现服务"""
           self.enable_auto_discovery = config.get('enable_auto_discovery', True)
           self.discovery_interval = config.get('discovery_interval', 60)
           
           if self.enable_auto_discovery:
               await self._start_auto_discovery()
       
       async def cleanup(self) -> None:
           """清理资源注册表"""
           self.resource_registry.clear()
           for key in self.resource_index:
               self.resource_index[key].clear()
       
       def get_status(self) -> Dict[str, Any]:
           """获取服务状态"""
           return {
               'total_resources': len(self.resource_registry),
               'resources_by_type': {
                   k: len(v) for k, v in self.resource_index.items()
               }
           }
       
       async def register_resource(self, resource: Resource) -> str:
           """注册资源"""
           resource_id = resource.resource_id
           self.resource_registry[resource_id] = resource
           
           # 更新索引
           if resource.resource_type in self.resource_index:
               self.resource_index[resource.resource_type].append(resource_id)
           
           return resource_id
       
       async def discover_agents(self, criteria: Dict[str, Any] = None) -> List[Resource]:
           """发现智能体"""
           agent_resources = []
           
           for agent_info in self.agent_manager.list_agents():
               resource = Resource(
                   resource_id=f"agent:{agent_info['id']}",
                   resource_type='agent',
                   name=agent_info['name'],
                   description=agent_info.get('metadata', {}).get('description', ''),
                   metadata=agent_info.get('metadata', {}),
                   agent_id=agent_info['id']
               )
               
               if self._matches_criteria(resource, criteria):
                   agent_resources.append(resource)
           
           return agent_resources
       
       async def discover_apis(self, agent_id: str = None) -> List[Resource]:
           """发现 API 资源"""
           api_resources = []
           
           if agent_id:
               # 发现特定智能体的 API
               agent = self.agent_manager.get_agent(agent_id)
               if agent and hasattr(agent, 'get_apis'):
                   apis = await agent.get_apis()
                   for api in apis:
                       resource = Resource(
                           resource_id=f"api:{agent_id}:{api['path']}",
                           resource_type='api',
                           name=api['name'],
                           description=api.get('description', ''),
                           metadata=api,
                           agent_id=agent_id
                       )
                       api_resources.append(resource)
           
           return api_resources
       
       def _matches_criteria(self, resource: Resource, criteria: Dict[str, Any]) -> bool:
           """检查资源是否匹配条件"""
           if not criteria:
               return True
           
           # 实现匹配逻辑
           for key, value in criteria.items():
               if hasattr(resource, key):
                   if getattr(resource, key) != value:
                       return False
               elif key in resource.metadata:
                   if resource.metadata[key] != value:
                       return False
           
           return True
   ```

### 阶段 3: 工具层重构（2-3 周）

#### 目标
拆分和重组工具功能，实现清晰的工具职责分离。

#### 任务清单

1. **拆分 ANPTool 为专门的工具**
   ```python
   # tools/anp/network_tool.py
   from typing import Dict, Any, Optional
   import aiohttp
   import json
   
   class NetworkTool:
       """专注于网络 HTTP 调用的工具"""
       
       def __init__(self):
           self.session: Optional[aiohttp.ClientSession] = None
       
       async def initialize(self):
           """初始化网络会话"""
           self.session = aiohttp.ClientSession()
       
       async def cleanup(self):
           """清理网络会话"""
           if self.session:
               await self.session.close()
       
       async def http_request(self, url: str, method: str = "GET",
                            headers: Dict[str, str] = None,
                            params: Dict[str, Any] = None,
                            json_data: Dict[str, Any] = None,
                            timeout: int = 30) -> Dict[str, Any]:
           """执行 HTTP 请求"""
           if not self.session:
               await self.initialize()
           
           request_kwargs = {
               'url': url,
               'method': method,
               'headers': headers or {},
               'params': params or {},
               'timeout': aiohttp.ClientTimeout(total=timeout)
           }
           
           if json_data and method in ['POST', 'PUT', 'PATCH']:
               request_kwargs['json'] = json_data
           
           try:
               async with self.session.request(**request_kwargs) as response:
                   content = await response.text()
                   
                   # 尝试解析 JSON
                   try:
                       data = json.loads(content)
                   except json.JSONDecodeError:
                       data = {'text': content}
                   
                   return {
                       'status_code': response.status,
                       'headers': dict(response.headers),
                       'data': data,
                       'url': str(response.url)
                   }
           except Exception as e:
               return {
                   'status_code': 500,
                   'error': str(e),
                   'url': url
               }
       
       async def authenticated_request(self, url: str, auth_client,
                                     caller_did: str, target_did: str,
                                     **kwargs) -> Dict[str, Any]:
           """带认证的 HTTP 请求"""
           # 使用 auth_client 进行认证
           return await auth_client.authenticated_request(
               caller_agent=caller_did,
               target_agent=target_did,
               request_url=url,
               **kwargs
           )
   ```

   ```python
   # tools/anp/crawler_tool.py
   from typing import List, Dict, Set, Any
   from urllib.parse import urljoin, urlparse
   import re
   
   class CrawlerTool:
       """专注于网页/API 爬取的工具"""
       
       def __init__(self, network_tool):
           self.network_tool = network_tool
           self.visited_urls: Set[str] = set()
       
       async def crawl_url(self, url: str, max_depth: int = 3,
                         current_depth: int = 0) -> Dict[str, Any]:
           """爬取单个 URL"""
           if current_depth >= max_depth or url in self.visited_urls:
               return {'url': url, 'skipped': True}
           
           self.visited_urls.add(url)
           
           # 获取内容
           response = await self.network_tool.http_request(url)
           
           if response.get('status_code') != 200:
               return {'url': url, 'error': response.get('error')}
           
           content = response.get('data', {})
           
           # 提取链接
           links = self.extract_links(content, url)
           
           # 递归爬取子链接
           sub_results = []
           if current_depth < max_depth - 1:
               for link in links[:5]:  # 限制每层爬取的链接数
                   sub_result = await self.crawl_url(link, max_depth, current_depth + 1)
                   sub_results.append(sub_result)
           
           return {
               'url': url,
               'content': content,
               'links': links,
               'sub_results': sub_results,
               'depth': current_depth
           }
       
       def extract_links(self, content: Any, base_url: str) -> List[str]:
           """从内容中提取链接"""
           links = []
           
           if isinstance(content, dict):
               # 从 JSON 中提取链接
               for key, value in content.items():
                   if key in ['url', 'href', 'link', 'endpoint', 'serviceEndpoint']:
                       if isinstance(value, str) and value.startswith(('http://', 'https://', '/')):
                           links.append(urljoin(base_url, value))
                   elif isinstance(value, (dict, list)):
                       links.extend(self.extract_links(value, base_url))
           elif isinstance(content, list):
               for item in content:
                   links.extend(self.extract_links(item, base_url))
           elif isinstance(content, str):
               # 从文本中提取 URL
               url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
               found_urls = re.findall(url_pattern, content)
               links.extend(found_urls)
           
           return list(set(links))  # 去重
       
       async def batch_crawl(self, urls: List[str],
                           concurrent_limit: int = 5) -> List[Dict[str, Any]]:
           """批量爬取多个 URL"""
           import asyncio
           
           results = []
           for i in range(0, len(urls), concurrent_limit):
               batch = urls[i:i + concurrent_limit]
               batch_results = await asyncio.gather(
                   *[self.crawl_url(url) for url in batch],
                   return_exceptions=True
               )
               results.extend(batch_results)
           
           return results
   ```

   ```python
   # tools/anp/analysis_tool.py
   from typing import Dict, List, Any, Tuple
   import json
   
   class AnalysisTool:
       """专注于数据分析和处理的工具"""
       
       def analyze_api_structure(self, api_doc: Dict[str, Any]) -> Dict[str, Any]:
           """分析 API 文档结构"""
           analysis = {
               'endpoints': [],
               'methods': {},
               'parameters': {},
               'authentication': None
           }
           
           # 分析端点
           if 'paths' in api_doc:  # OpenAPI 格式
               for path, methods in api_doc['paths'].items():
                   analysis['endpoints'].append(path)
                   for method, details in methods.items():
                       if method not in analysis['methods']:
                           analysis['methods'][method] = []
                       analysis['methods'][method].append(path)
                       
                       # 分析参数
                       if 'parameters' in details:
                           analysis['parameters'][f"{method} {path}"] = details['parameters']
           
           # 分析认证
           if 'security' in api_doc:
               analysis['authentication'] = api_doc['security']
           elif 'securityDefinitions' in api_doc:
               analysis['authentication'] = api_doc['securityDefinitions']
           
           return analysis
       
       def extract_method_info(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
           """提取方法信息"""
           methods = []
           
           # 从不同格式中提取方法
           if 'methods' in content:
               for method_name, method_info in content['methods'].items():
                   methods.append({
                       'name': method_name,
                       'type': 'method',
                       **method_info
                   })
           
           if 'functions' in content:
               for func_name, func_info in content['functions'].items():
                   methods.append({
                       'name': func_name,
                       'type': 'function',
                       **func_info
                   })
           
           if 'apis' in content:
               for api_info in content['apis']:
                   methods.append({
                       'name': api_info.get('name', api_info.get('path', 'unknown')),
                       'type': 'api',
                       **api_info
                   })
           
           return methods
       
       def calculate_similarity(self, text1: str, text2: str) -> float:
           """计算文本相似度（简单实现）"""
           # 转换为小写
           text1 = text1.lower()
           text2 = text2.lower()
           
           # 分词
           words1 = set(text1.split())
           words2 = set(text2.split())
           
           # 计算 Jaccard 相似度
           intersection = words1.intersection(words2)
           union = words1.union(words2)
           
           if not union:
               return 0.0
           
           return len(intersection) / len(union)
       
       def find_best_match(self, query: str, candidates: List[Dict[str, Any]],
                         key_field: str = 'name') -> Tuple[Dict[str, Any], float]:
           """找到最佳匹配"""
           best_match = None
           best_score = 0.0
           
           for candidate in candidates:
               candidate_text = str(candidate.get(key_field, ''))
               score = self.calculate_similarity(query, candidate_text)
               
               if score > best_score:
                   best_score = score
                   best_match = candidate
           
           return best_match, best_score
   ```

2. **MCP 工具集成**
   ```python
   # tools/mcp/mcp_client.py
   from typing import Dict, Any, List, Optional
   import asyncio
   import json
   
   class MCPClient:
       """MCP (Model Context Protocol) 客户端"""
       
       def __init__(self, server_configs: List[Dict[str, Any]]):
           self.servers: Dict[str, MCPServer] = {}
           self.tools: Dict[str, MCPTool] = {}
           
           for config in server_configs:
               self._connect_server(config)
       
       def _connect_server(self, config: Dict[str, Any]):
           """连接到 MCP 服务器"""
           server_name = config['name']
           server = MCPServer(config)
           self.servers[server_name] = server
           
           # 注册服务器提供的工具
           for tool in server.get_tools():
               tool_id = f"{server_name}:{tool.name}"
               self.tools[tool_id] = tool
       
       async def execute_tool(self, tool_name: str, **kwargs) -> Any:
           """执行 MCP 工具"""
           if tool_name not in self.tools:
               raise ValueError(f"Tool {tool_name} not found")
           
           tool = self.tools[tool_name]
           return await tool.execute(**kwargs)
       
       def list_tools(self) -> List[Dict[str, Any]]:
           """列出所有可用工具"""
           return [
               {
                   'id': tool_id,
                   'name': tool.name,
                   'description': tool.description,
                   'parameters': tool.parameters
               }
               for tool_id, tool in self.tools.items()
           ]
   
   class MCPServer:
       """MCP 服务器连接"""
       
       def __init__(self, config: Dict[str, Any]):
           self.name = config['name']
           self.transport = config['transport']
           self.tools: List[MCPTool] = []
           
       def get_tools(self) -> List['MCPTool']:
           """获取服务器提供的工具"""
           # 实现与 MCP 服务器的通信
           return self.tools
   
   class MCPTool:
       """MCP 工具"""
       
       def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
           self.name = name
           self.description = description
           self.parameters = parameters
       
       async def execute(self, **kwargs) -> Any:
           """执行工具"""
           # 实现工具执行逻辑
           pass
   ```

3. **集成工具**
   ```python
   # tools/integration/tool_orchestrator.py
   from typing import Dict, Any, List, Optional
   
   class ToolOrchestrator:
       """工具编排器 - 组合多个工具完成复杂任务"""
       
       def __init__(self, di_container):
           self.di_container = di_container
           self.network_tool = di_container.resolve(NetworkTool)
           self.crawler_tool = di_container.resolve(CrawlerTool)
           self.analysis_tool = di_container.resolve(AnalysisTool)
           self.mcp_client = di_container.resolve(MCPClient)
       
       async def intelligent_discovery(self, query: str, initial_url: str,
                                     use_llm: bool = True) -> Dict[str, Any]:
           """智能发现功能 - 组合爬虫、分析和 LLM"""
           # 1. 爬取初始 URL
           crawl_result = await self.crawler_tool.crawl_url(initial_url)
           
           # 2. 分析爬取的内容
           if crawl_result.get('content'):
               api_analysis = self.analysis_tool.analyze_api_structure(
                   crawl_result['content']
               )
               methods = self.analysis_tool.extract_method_info(
                   crawl_result['content']
               )
           else:
               api_analysis = {}
               methods = []
           
           # 3. 使用 LLM 进行智能匹配（如果启用）
           if use_llm and methods:
               # 使用 MCP 的 LLM 工具
               llm_result = await self.mcp_client.execute_tool(
                   'llm:analyze',
                   query=query,
                   context={
                       'methods': methods,
                       'api_structure': api_analysis
                   }
               )
               best_match = llm_result.get('best_match')
           else:
               # 使用简单的相似度匹配
               best_match, score = self.analysis_tool.find_best_match(
                   query, methods
               )
           
           # 4. 执行找到的方法
           if best_match:
               if best_match.get('type') == 'api':
                   # 调用 API
                   result = await self.network_tool.http_request(
                       best_match['url'],
                       method=best_match.get('method', 'GET')
                   )
               else:
                   # 其他类型的调用
                   result = {'message': 'Method found but execution not implemented'}
           else:
               result = {'message': 'No matching method found'}
           
           return {
               'query': query,
               'crawl_result': crawl_result,
               'analysis': api_analysis,
               'methods_found': len(methods),
               'best_match': best_match,
               'execution_result': result
           }
       
       async def execute_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
           """执行工作流"""
           results = {}
           
           for step in workflow_definition['steps']:
               step_name = step['name']
               tool_name = step['tool']
               params = step.get('params', {})
               
               # 参数可能引用之前步骤的结果
               resolved_params = self._resolve_params(params, results)
               
               # 执行工具
               if tool_name.startswith('mcp:'):
                   result = await self.mcp_client.execute_tool(
                       tool_name.replace('mcp:', ''),
                       **resolved_params
                   )
               elif tool_name == 'network':
                   result = await self.network_tool.http_request(**resolved_params)
               elif tool_name == 'crawler':
                   result = await self.crawler_tool.crawl_url(**resolved_params)
               elif tool_name == 'analysis':
                   method = resolved_params.pop('method')
                   result = getattr(self.analysis_tool, method)(**resolved_params)
               else:
                   result = {'error': f'Unknown tool: {tool_name}'}
               
               results[step_name] = result
           
           return results
       
       def _resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
           """解析参数中的引用"""
           resolved = {}
           
           for key, value in params.items():
               if isinstance(value, str) and value.startswith('$'):
                   # 引用格式: $step_name.field.subfield
                   ref_path = value[1:].split('.')
                   resolved[key] = self._get_nested_value(context, ref_path)
               else:
                   resolved[key] = value
           
           return resolved
       
       def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
           """获取嵌套值"""
           current = data
           for key in path:
               if isinstance(current, dict) and key in current:
                   current = current[key]
               else:
                   return None
           return current
   ```

### 阶段 4: 核心层简化（2 周）

#### 目标
简化核心组件，使其专注于核心职责。

#### 任务清单

1. **简化 UnifiedCaller**
   ```python
   # core/unified_caller.py
   from typing import Any, Dict, Optional
   from core.interfaces.caller_interface import CallerInterface
   
   class UnifiedCaller(CallerInterface):
       """统一调用器 - 简化版，专注于调用路由"""
       
       def __init__(self, network_tool, local_method_manager):
           self.network_tool = network_tool
           self.local_methods = local_method_manager
       
       async def call(self, target: str, method: str, **kwargs) -> Any:
           """统一调用接口"""
           if self._is_local(target):
               return await self._call_local(target, method, **kwargs)
           else:
               return await self._call_remote(target, method, **kwargs)
       
       def _is_local(self, target: str) -> bool:
           """判断是否为本地调用"""
           return target.startswith('local://') or self.local_methods.has_agent(target)
       
       async def _call_local(self, target: str, method: str, **kwargs) -> Any:
           """本地方法调用"""
           if target.startswith('local://'):
               target = target.replace('local://', '')
           
           return await self.local_methods.call_method(target, method, **kwargs)
       
       async def _call_remote(self, target: str, method: str, **kwargs) -> Any:
           """远程方法调用"""
           # 构建 URL
           if not target.startswith(('http://', 'https://')):
               # 假设是 DID，需要解析为 URL
               target = await self._resolve_did_to_url(target)
           
           url = f"{target}/{method}"
           
           # 提取 HTTP 方法和参数
           http_method = kwargs.pop('http_method', 'POST')
           params = kwargs.pop('params', None)
           json_data = kwargs
           
           return await self.network_tool.http_request(
               url=url,
               method=http_method,
               params=params,
               json_data=json_data if json_data else None
           )
       
       async def _resolve_did_to_url(self, did: str) -> str:
           """解析 DID 为 URL"""
           # 简化实现，实际应该查询 DID 文档
           parts = did.split(':')
           if len(parts) >= 3 and parts[0] == 'did' and parts[1] == 'wba':
               host_port = parts[2].replace('%3A', ':')
               return f"http://{host_port}"
           return did
   ```

2. **简化 UnifiedCrawler**
   ```python
   # core/unified_crawler.py
   from typing import Dict, List, Any, Optional
   from core.interfaces.crawler_interface import CrawlerInterface
   
   class UnifiedCrawler(CrawlerInterface):
       """统一爬虫 - 简化版，专注于资源发现"""
       
       def __init__(self, crawler_tool, discovery_service, analysis_tool):
           self.crawler_tool = crawler_tool
           self.discovery_service = discovery_service
           self.analysis_tool = analysis_tool
           self.discovered_resources: Dict[str, Any] = {}
       
       async def discover_resources(self, criteria: Dict[str, Any] = None) -> Dict[str, List[Any]]:
           """发现资源"""
           resources = {
               'agents': [],
               'apis': [],
               'methods': []
           }
           
           # 1. 发现本地智能体
           local_agents = await self.discovery_service.discover_agents(criteria)
           resources['agents'].extend(local_agents)
           
           # 2. 发现每个智能体的 API
           for agent in local_agents:
               agent_apis = await self.discovery_service.discover_apis(agent.agent_id)
               resources['apis'].extend(agent_apis)
           
           # 3. 发现方法
           for api in resources['apis']:
               if 'methods' in api.metadata:
                   for method in api.metadata['methods']:
                       resources['methods'].append({
                           'agent_id': api.agent_id,
                           'api_path': api.name,
                           **method
                       })
           
           # 缓存发现的资源
           self.discovered_resources = resources
           
           return resources
       
       async def search_resources(self, query: str, resource_type: str = None) -> List[Any]:
           """搜索资源"""
           if not self.discovered_resources:
               await self.discover_resources()
           
           results = []
           
           # 确定搜索范围
           if resource_type:
               search_scope = {resource_type: self.discovered_resources.get(resource_type, [])}
           else:
               search_scope = self.discovered_resources
           
           # 在每种资源类型中搜索
           for res_type, resources in search_scope.items():
               for resource in resources:
                   # 简单的关键词匹配
                   resource_text = json.dumps(resource).lower()
                   if query.lower() in resource_text:
                       results.append({
                           'type': res_type,
                           'resource': resource,
                           'score': self.analysis_tool.calculate_similarity(
                               query, resource.get('name', '')
                           )
                       })
           
           # 按相似度排序
           results.sort(key=lambda x: x['score'], reverse=True)
           
           return results
       
       async def crawl_and_analyze(self, url: str, max_depth: int = 3) -> Dict[str, Any]:
           """爬取并分析 URL"""
           # 爬取
           crawl_result = await self.crawler_tool.crawl_url(url, max_depth)
           
           # 分析
           analysis = {
               'url': url,
               'content_type': self._detect_content_type(crawl_result.get('content', {})),
               'resources_found': []
           }
           
           if crawl_result.get('content'):
               # 分析 API 结构
               if analysis['content_type'] == 'api_doc':
                   api_analysis = self.analysis_tool.analyze_api_structure(
                       crawl_result['content']
                   )
                   analysis['api_structure'] = api_analysis
               
               # 提取方法
               methods = self.analysis_tool.extract_method_info(crawl_result['content'])
               analysis['methods'] = methods
               
               # 注册发现的资源
               for method in methods:
                   resource = {
                       'url': url,
                       'method': method,
                       'discovered_at': datetime.now().isoformat()
                   }
                   analysis['resources_found'].append(resource)
           
           return analysis
       
       def _detect_content_type(self, content: Any) -> str:
           """检测内容类型"""
           if isinstance(content, dict):
               if 'openapi' in content or 'swagger' in content:
                   return 'api_doc'
               elif 'methods' in content or 'functions' in content:
                   return 'method_list'
               elif '@context' in content:
                   return 'json_ld'
           return 'unknown'
   ```

3. **本地方法管理器**
   ```python
   # core/local_methods/method_manager.py
   from typing import Dict, Any, Callable, List, Optional
   import inspect
   
   class LocalMethodManager:
       """本地方法管理器"""
       
       def __init__(self):
           self.agents: Dict[str, Any] = {}
           self.methods: Dict[str, Dict[str, Callable]] = {}
           self.method_metadata: Dict[str, Dict[str, Any]] = {}
       
       def register_agent(self, agent_id: str, agent_instance: Any) -> None:
           """注册智能体"""
           self.agents[agent_id] = agent_instance
           self.methods[agent_id] = {}
           self.method_metadata[agent_id] = {}
           
           # 自动发现和注册方法
           self._discover_methods(agent_id, agent_instance)
       
       def _discover_methods(self, agent_id: str, agent_instance: Any) -> None:
           """发现智能体的方法"""
           for name, method in inspect.getmembers(agent_instance, inspect.ismethod):
               # 跳过私有方法
               if name.startswith('_'):
                   continue
               
               # 检查是否有装饰器标记
               if hasattr(method, '_exposed') or hasattr(method, 'exposed'):
                   self.register_method(agent_id, name, method)
       
       def register_method(self, agent_id: str, method_name: str,
                         method: Callable, metadata: Dict[str, Any] = None) -> None:
           """注册方法"""
           if agent_id not in self.methods:
               self.methods[agent_id] = {}
               self.method_metadata[agent_id] = {}
           
           self.methods[agent_id][method_name] = method
           
           # 提取方法元数据
           sig = inspect.signature(method)
           default_metadata = {
               'name': method_name,
               'parameters': str(sig),
               'doc': inspect.getdoc(method) or '',
               'is_async': inspect.iscoroutinefunction(method)
           }
           
           self.method_metadata[agent_id][method_name] = {
               **default_metadata,
               **(metadata or {})
           }
       
       def has_agent(self, agent_id: str) -> bool:
           """检查智能体是否存在"""
           return agent_id in self.agents
       
       def has_method(self, agent_id: str, method_name: str) -> bool:
           """检查方法是否存在"""
           return agent_id in self.methods and method_name in self.methods[agent_id]
       
       async def call_method(self, agent_id: str, method_name: str, **kwargs) -> Any:
           """调用方法"""
           if not self.has_method(agent_id, method_name):
               raise ValueError(f"Method {agent_id}.{method_name} not found")
           
           method = self.methods[agent_id][method_name]
           metadata = self.method_metadata[agent_id][method_name]
           
           # 调用方法
           if metadata['is_async']:
               return await method(**kwargs)
           else:
               return method(**kwargs)
       
       def list_agents(self) -> List[str]:
           """列出所有智能体"""
           return list(self.agents.keys())
       
       def list_methods(self, agent_id: str = None) -> Dict[str, List[str]]:
           """列出方法"""
           if agent_id:
               return {agent_id: list(self.methods.get(agent_id, {}).keys())}
           else:
               return {
                   aid: list(methods.keys())
                   for aid, methods in self.methods.items()
               }
       
       def get_method_metadata(self, agent_id: str, method_name: str) -> Dict[str, Any]:
           """获取方法元数据"""
           return self.method_metadata.get(agent_id, {}).get(method_name, {})
   ```

### 阶段 5: 编排层重构（2-3 周）

#### 目标
重构 MasterAgent，实现工作流引擎和任务调度器。

#### 任务清单

1. **重构 MasterAgent**
   ```python
   # orchestration/master_agent.py
   from typing import Dict, Any, Optional, List
   from orchestration.workflow_engine import WorkflowEngine
   from tools.integration.tool_orchestrator import ToolOrchestrator
   
   class MasterAgent:
       """主智能体 - 负责任务理解和编排"""
       
       def __init__(self, workflow_engine: WorkflowEngine, 
                    tool_orchestrator: ToolOrchestrator,
                    discovery_service):
           self.workflow_engine = workflow_engine
           self.tool_orchestrator = tool_orchestrator
           self.discovery_service = discovery_service
           self.task_history: List[Dict[str, Any]] = []
       
       async def execute_task(self, task_description: str, 
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
           """执行任务"""
           # 1. 分析任务类型
           task_type = self._analyze_task_type(task_description)
           
           # 2. 根据任务类型生成工作流
           workflow = await self._generate_workflow(task_type, task_description, context)
           
           # 3. 执行工作流
           result = await self.workflow_engine.execute_workflow(workflow)
           
           # 4. 记录任务历史
           self.task_history.append({
               'task': task_description,
               'type': task_type,
               'context': context,
               'workflow': workflow,
               'result': result,
               'timestamp': datetime.now().isoformat()
           })
           
           return result
       
       def _analyze_task_type(self, task_description: str) -> str:
           """分析任务类型"""
           task_lower = task_description.lower()
           
           if any(word in task_lower for word in ['查找', '搜索', 'find', 'search']):
               return 'search'
           elif any(word in task_lower for word in ['调用', '执行', 'call', 'execute']):
               return 'execute'
           elif any(word in task_lower for word in ['分析', '理解', 'analyze', 'understand']):
               return 'analyze'
           else:
               return 'general'
       
       async def _generate_workflow(self, task_type: str, task_description: str,
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
           """生成工作流"""
           if task_type == 'search':
               return self._create_search_workflow(task_description, context)
           elif task_type == 'execute':
               return self._create_execution_workflow(task_description, context)
           elif task_type == 'analyze':
               return self._create_analysis_workflow(task_description, context)
           else:
               return self._create_general_workflow(task_description, context)
       
       def _create_search_workflow(self, task_description: str,
                                 context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
           """创建搜索工作流"""
           return {
               'name': 'search_workflow',
               'steps': [
                   {
                       'name': 'discover_resources',
                       'tool': 'discovery',
                       'params': {
                           'criteria': self._extract_search_criteria(task_description)
                       }
                   },
                   {
                       'name': 'search_resources',
                       'tool': 'crawler',
                       'params': {
                           'query': task_description,
                           'resources': '$discover_resources.result'
                       }
                   },
                   {
                       'name': 'analyze_results',
                       'tool': 'analysis',
                       'params': {
                           'method': 'find_best_match',
                           'query': task_description,
                           'candidates': '$search_resources.result'
                       }
                   }
               ]
           }
       
       def _extract_search_criteria(self, task_description: str) -> Dict[str, Any]:
           """提取搜索条件"""
           # 简单实现，实际应该使用 NLP
           criteria = {}
           
           if '智能体' in task_description or 'agent' in task_description.lower():
               criteria['resource_type'] = 'agent'
           elif 'API' in task_description or 'api' in task_description.lower():
               criteria['resource_type'] = 'api'
           elif '方法' in task_description or 'method' in task_description.lower():
               criteria['resource_type'] = 'method'
           
           return criteria
   ```

2. **实现工作流引擎**
   ```python
   # orchestration/workflow_engine.py
   from typing import Dict, Any, List, Optional
   import asyncio
   from enum import Enum
   
   class WorkflowStatus(Enum):
       PENDING = "pending"
       RUNNING = "running"
       COMPLETED = "completed"
       FAILED = "failed"
       PAUSED = "paused"
   
   class WorkflowEngine:
       """工作流引擎"""
       
       def __init__(self, tool_orchestrator):
           self.tool_orchestrator = tool_orchestrator
           self.workflows: Dict[str, Dict[str, Any]] = {}
           self.execution_context: Dict[str, Any] = {}
       
       async def create_workflow(self, workflow_definition: Dict[str, Any]) -> str:
           """创建工作流"""
           workflow_id = f"wf_{len(self.workflows)}_{datetime.now().timestamp()}"
           
           self.workflows[workflow_id] = {
               'id': workflow_id,
               'definition': workflow_definition,
               'status': WorkflowStatus.PENDING,
               'created_at': datetime.now().isoformat(),
               'started_at': None,
               'completed_at': None,
               'results': {},
               'errors': []
           }
           
           return workflow_id
       
       async def execute_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
           """执行工作流"""
           workflow_id = await self.create_workflow(workflow_definition)
           
           workflow = self.workflows[workflow_id]
           workflow['status'] = WorkflowStatus.RUNNING
           workflow['started_at'] = datetime.now().isoformat()
           
           try:
               # 执行工作流步骤
               results = await self._execute_steps(
                   workflow_definition['steps'],
                   workflow_id
               )
               
               workflow['status'] = WorkflowStatus.COMPLETED
               workflow['results'] = results
               
               return {
                   'workflow_id': workflow_id,
                   'status': 'completed',
                   'results': results
               }
               
           except Exception as e:
               workflow['status'] = WorkflowStatus.FAILED
               workflow['errors'].append(str(e))
               
               return {
                   'workflow_id': workflow_id,
                   'status': 'failed',
                   'error': str(e)
               }
           finally:
               workflow['completed_at'] = datetime.now().isoformat()
       
       async def _execute_steps(self, steps: List[Dict[str, Any]], 
                              workflow_id: str) -> Dict[str, Any]:
           """执行工作流步骤"""
           context = {}
           
           for step in steps:
               step_name = step['name']
               
               # 检查条件
               if 'condition' in step:
                   if not self._evaluate_condition(step['condition'], context):
                       continue
               
               # 执行步骤
               if step.get('parallel'):
                   # 并行执行
                   result = await self._execute_parallel_step(step, context)
               else:
                   # 串行执行
                   result = await self._execute_single_step(step, context)
               
               context[step_name] = {'result': result}
               
               # 更新工作流状态
               self.workflows[workflow_id]['results'][step_name] = result
           
           return context
       
       async def _execute_single_step(self, step: Dict[str, Any],
                                    context: Dict[str, Any]) -> Any:
           """执行单个步骤"""
           tool_name = step['tool']
           params = step.get('params', {})
           
           # 解析参数中的引用
           resolved_params = self._resolve_params(params, context)
           
           # 执行工具
           return await self.tool_orchestrator.execute_tool(
               tool_name, **resolved_params
           )
       
       async def _execute_parallel_step(self, step: Dict[str, Any],
                                      context: Dict[str, Any]) -> List[Any]:
           """并行执行步骤"""
           tasks = []
           
           for sub_step in step['steps']:
               task = self._execute_single_step(sub_step, context)
               tasks.append(task)
           
           return await asyncio.gather(*tasks)
       
       def _resolve_params(self, params: Dict[str, Any], 
                         context: Dict[str, Any]) -> Dict[str, Any]:
           """解析参数中的引用"""
           resolved = {}
           
           for key, value in params.items():
               if isinstance(value, str) and value.startswith('$'):
                   # 引用格式: $step_name.field
                   ref_path = value[1:].split('.')
                   resolved[key] = self._get_nested_value(context, ref_path)
               elif isinstance(value, dict):
                   resolved[key] = self._resolve_params(value, context)
               elif isinstance(value, list):
                   resolved[key] = [
                       self._resolve_params(item, context) if isinstance(item, dict) else item
                       for item in value
                   ]
               else:
                   resolved[key] = value
           
           return resolved
       
       def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
           """获取嵌套值"""
           current = data
           for key in path:
               if isinstance(current, dict) and key in current:
                   current = current[key]
               else:
                   return None
           return current
       
       def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
           """评估条件"""
           # 简单实现，支持基本的条件判断
           # 格式: "step_name.result.field == value"
           try:
               # 这里应该实现一个安全的表达式评估器
               # 暂时使用简单的字符串比较
               return True
           except:
               return False
       
       async def pause_workflow(self, workflow_id: str) -> bool:
           """暂停工作流"""
           if workflow_id in self.workflows:
               workflow = self.workflows[workflow_id]
               if workflow['status'] == WorkflowStatus.RUNNING:
                   workflow['status'] = WorkflowStatus.PAUSED
                   return True
           return False
       
       async def resume_workflow(self, workflow_id: str) -> bool:
           """恢复工作流"""
           if workflow_id in self.workflows:
               workflow = self.workflows[workflow_id]
               if workflow['status'] == WorkflowStatus.PAUSED:
                   workflow['status'] = WorkflowStatus.RUNNING
                   # 继续执行剩余步骤
                   return True
           return False
       
       def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
           """获取工作流状态"""
           if workflow_id in self.workflows:
               workflow = self.workflows[workflow_id]
               return {
                   'id': workflow_id,
                   'status': workflow['status'].value,
                   'created_at': workflow['created_at'],
                   'started_at': workflow['started_at'],
                   'completed_at': workflow['completed_at'],
                   'results': workflow['results'],
                   'errors': workflow['errors']
               }
           return None
   ```

3. **实现任务调度器**
   ```python
   # orchestration/task_scheduler.py
   from typing import Dict, Any, List, Optional, Callable
   import asyncio
   from datetime import datetime, timedelta
   import heapq
   
   class TaskScheduler:
       """任务调度器"""
       
       def __init__(self, workflow_engine):
           self.workflow_engine = workflow_engine
           self.scheduled_tasks: List[Tuple[datetime, str, Dict]] = []
           self.recurring_tasks: Dict[str, Dict[str, Any]] = {}
           self.task_results: Dict[str, Any] = {}
           self._running = False
           self._scheduler_task = None
       
       async def start(self):
           """启动调度器"""
           self._running = True
           self._scheduler_task = asyncio.create_task(self._scheduler_loop())
       
       async def stop(self):
           """停止调度器"""
           self._running = False
           if self._scheduler_task:
               await self._scheduler_task
       
       async def _scheduler_loop(self):
           """调度器主循环"""
           while self._running:
               now = datetime.now()
               
               # 检查定时任务
               while self.scheduled_tasks and self.scheduled_tasks[0][0] <= now:
                   _, task_id, task_data = heapq.heappop(self.scheduled_tasks)
                   asyncio.create_task(self._execute_task(task_id, task_data))
               
               # 检查循环任务
               for task_id, task_info in self.recurring_tasks.items():
                   if task_info['next_run'] <= now:
                       asyncio.create_task(self._execute_task(task_id, task_info['data']))
                       # 计算下次运行时间
                       task_info['next_run'] = now + task_info['interval']
               
               # 休眠一小段时间
               await asyncio.sleep(1)
       
       async def schedule_task(self, task_data: Dict[str, Any], 
                             delay: Optional[timedelta] = None,
                             run_at: Optional[datetime] = None) -> str:
           """调度任务"""
           task_id = f"task_{len(self.scheduled_tasks)}_{datetime.now().timestamp()}"
           
           if run_at:
               scheduled_time = run_at
           elif delay:
               scheduled_time = datetime.now() + delay
           else:
               scheduled_time = datetime.now()
           
           heapq.heappush(self.scheduled_tasks, (scheduled_time, task_id, task_data))
           
           return task_id
       
       async def schedule_recurring_task(self, task_data: Dict[str, Any],
                                       interval: timedelta,
                                       start_immediately: bool = True) -> str:
           """调度循环任务"""
           task_id = f"recurring_{len(self.recurring_tasks)}_{datetime.now().timestamp()}"
           
           self.recurring_tasks[task_id] = {
               'data': task_data,
               'interval': interval,
               'next_run': datetime.now() if start_immediately else datetime.now() + interval,
               'created_at': datetime.now()
           }
           
           return task_id
       
       async def cancel_task(self, task_id: str) -> bool:
           """取消任务"""
           # 从定时任务中移除
           self.scheduled_tasks = [
               (time, tid, data) 
               for time, tid, data in self.scheduled_tasks 
               if tid != task_id
           ]
           heapq.heapify(self.scheduled_tasks)
           
           # 从循环任务中移除
           if task_id in self.recurring_tasks:
               del self.recurring_tasks[task_id]
               return True
           
           return False
       
       async def _execute_task(self, task_id: str, task_data: Dict[str, Any]):
           """执行任务"""
           try:
               # 如果是工作流任务
               if 'workflow' in task_data:
                   result = await self.workflow_engine.execute_workflow(
                       task_data['workflow']
                   )
               # 如果是简单任务
               elif 'function' in task_data:
                   func = task_data['function']
                   args = task_data.get('args', [])
                   kwargs = task_data.get('kwargs', {})
                   
                   if asyncio.iscoroutinefunction(func):
                       result = await func(*args, **kwargs)
                   else:
                       result = func(*args, **kwargs)
               else:
                   result = {'error': 'Invalid task data'}
               
               self.task_results[task_id] = {
                   'status': 'completed',
                   'result': result,
                   'completed_at': datetime.now().isoformat()
               }
               
           except Exception as e:
               self.task_results[task_id] = {
                   'status': 'failed',
                   'error': str(e),
                   'completed_at': datetime.now().isoformat()
               }
       
       def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
           """获取任务结果"""
           return self.task_results.get(task_id)
       
       def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
           """列出所有调度的任务"""
           tasks = []
           
           # 定时任务
           for scheduled_time, task_id, _ in self.scheduled_tasks:
               tasks.append({
                   'id': task_id,
                   'type': 'scheduled',
                   'scheduled_time': scheduled_time.isoformat()
               })
           
           # 循环任务
           for task_id, task_info in self.recurring_tasks.items():
               tasks.append({
                   'id': task_id,
                   'type': 'recurring',
                   'interval': str(task_info['interval']),
                   'next_run': task_info['next_run'].isoformat()
               })
           
           return tasks
   ```

### 阶段 6: 插件系统和配置驱动（2 周）

#### 目标
实现插件化架构和配置驱动的服务加载。

#### 任务清单

1. **插件管理器**
   ```python
   # plugins/plugin_manager.py
   import importlib
   import inspect
   from typing import Dict, Any, List, Type
   from pathlib import Path
   
   class PluginManager:
       """插件管理器"""
       
       def __init__(self):
           self.plugins: Dict[str, Plugin] = {}
           self.plugin_paths: List[Path] = []
       
       def add_plugin_path(self, path: str):
           """添加插件路径"""
           plugin_path = Path(path)
           if plugin_path.exists() and plugin_path.is_dir():
               self.plugin_paths.append(plugin_path)
       
       def load_plugins(self):
           """加载所有插件"""
           for plugin_path in self.plugin_paths:
               self._load_plugins_from_path(plugin_path)
       
       def _load_plugins_from_path(self, path: Path):
           """从路径加载插件"""
           for file_path in path.glob('*.py'):
               if file_path.name.startswith('_'):
                   continue
               
               module_name = file_path.stem
               spec = importlib.util.spec_from_file_location(module_name, file_path)
               module = importlib.util.module_from_spec(spec)
               spec.loader.exec_module(module)
               
               # 查找插件类
               for name, obj in inspect.getmembers(module):
                   if (inspect.isclass(obj) and 
                       issubclass(obj, Plugin) and 
                       obj != Plugin):
                       plugin_instance = obj()
                       self.register_plugin(plugin_instance)
       
       def register_plugin(self, plugin: 'Plugin'):
           """注册插件"""
           plugin_id = plugin.get_id()
           self.plugins[plugin_id] = plugin
           plugin.on_register(self)
       
       def unregister_plugin(self, plugin_id: str):
           """注销插件"""
           if plugin_id in self.plugins:
               plugin = self.plugins.pop(plugin_id)
               plugin.on_unregister()
       
       def get_plugin(self, plugin_id: str) -> Optional['Plugin']:
           """获取插件"""
           return self.plugins.get(plugin_id)
       
       def list_plugins(self) -> List[Dict[str, Any]]:
           """列出所有插件"""
           return [
               {
                   'id': plugin_id,
                   'name': plugin.get_name(),
                   'version': plugin.get_version(),
                   'description': plugin.get_description()
               }
               for plugin_id, plugin in self.plugins.items()
           ]
       
       async def initialize_plugins(self, config: Dict[str, Any]):
           """初始化所有插件"""
           for plugin_id, plugin in self.plugins.items():
               plugin_config = config.get(plugin_id, {})
               await plugin.initialize(plugin_config)
       
       async def cleanup_plugins(self):
           """清理所有插件"""
           for plugin in self.plugins.values():
               await plugin.cleanup()
   ```

2. **插件接口**
   ```python
   # plugins/plugin_interface.py
   from abc import ABC, abstractmethod
   from typing import Dict, Any, List, Optional
   
   class Plugin(ABC):
       """插件基类"""
       
       @abstractmethod
       def get_id(self) -> str:
           """获取插件 ID"""
           pass
       
       @abstractmethod
       def get_name(self) -> str:
           """获取插件名称"""
           pass
       
       @abstractmethod
       def get_version(self) -> str:
           """获取插件版本"""
           pass
       
       @abstractmethod
       def get_description(self) -> str:
           """获取插件描述"""
           pass
       
       def get_dependencies(self) -> List[str]:
           """获取插件依赖"""
           return []
       
       def on_register(self, plugin_manager):
           """插件注册时调用"""
           pass
       
       def on_unregister(self):
           """插件注销时调用"""
           pass
       
       async def initialize(self, config: Dict[str, Any]):
           """初始化插件"""
           pass
       
       async def cleanup(self):
           """清理插件资源"""
           pass
       
       def get_services(self) -> Dict[str, Any]:
           """获取插件提供的服务"""
           return {}
       
       def get_tools(self) -> Dict[str, Any]:
           """获取插件提供的工具"""
           return {}
       
       def get_commands(self) -> Dict[str, Any]:
           """获取插件提供的命令"""
           return {}
   
   class ServicePlugin(Plugin):
       """服务插件基类"""
       
       @abstractmethod
       def create_service(self) -> Any:
           """创建服务实例"""
           pass
   
   class ToolPlugin(Plugin):
       """工具插件基类"""
       
       @abstractmethod
       def create_tool(self) -> Any:
           """创建工具实例"""
           pass
   ```

3. **配置驱动的框架启动**
   ```python
   # config/framework_bootstrap.py
   from typing import Dict, Any
   from utils.dependency_injection import DIContainer
   from config.framework_config import FrameworkConfig
   from plugins.plugin_manager import PluginManager
   
   class FrameworkBootstrap:
       """框架启动器"""
       
       def __init__(self, config_file: str):
           self.config = FrameworkConfig(config_file)
           self.di_container = DIContainer()
           self.plugin_manager = PluginManager()
           self.services = {}
       
       async def bootstrap(self):
           """启动框架"""
           # 1. 加载配置
           self.config.load_config()
           
           # 2. 注册核心服务
           await self._register_core_services()
           
           # 3. 加载插件
           await self._load_plugins()
           
           # 4. 启动服务
           await self._start_services()
           
           return self
       
       async def _register_core_services(self):
           """注册核心服务"""
           # 注册基础服务
           from services.agent.agent_manager import AgentManager
           from services.communication.message_service import MessageService
           from services.discovery.resource_discovery import ResourceDiscoveryService
           
           self.di_container.register(AgentManager, AgentManager)
           self.di_container.register(MessageService, MessageService)
           self.di_container.register(ResourceDiscoveryService, ResourceDiscoveryService)
           
           # 注册工具
           from tools.anp.network_tool import NetworkTool
           from tools.anp.crawler_tool import CrawlerTool
           from tools.anp.analysis_tool import AnalysisTool
           
           self.di_container.register(NetworkTool, NetworkTool)
           self.di_container.register(CrawlerTool, CrawlerTool)
           self.di_container.register(AnalysisTool, AnalysisTool)
           
           # 注册核心组件
           from core.unified_caller import UnifiedCaller
           from core.unified_crawler import UnifiedCrawler
           from core.local_methods.method_manager import LocalMethodManager
           
           self.di_container.register(UnifiedCaller, UnifiedCaller)
           self.di_container.register(UnifiedCrawler, UnifiedCrawler)
           self.di_container.register(LocalMethodManager, LocalMethodManager)
       
       async def _load_plugins(self):
           """加载插件"""
           plugin_paths = self.config.config_data.get('plugin_paths', [])
           
           for path in plugin_paths:
               self.plugin_manager.add_plugin_path(path)
           
           self.plugin_manager.load_plugins()
           
           # 初始化插件
           plugin_configs = self.config.plugin_configs
           await self.plugin_manager.initialize_plugins(plugin_configs)
           
           # 注册插件提供的服务
           for plugin_id, plugin in self.plugin_manager.plugins.items():
               services = plugin.get_services()
               for service_name, service_class in services.items():
                   self.di_container.register(service_class, service_class)
       
       async def _start_services(self):
           """启动服务"""
           enabled_services = self.config.enabled_services
           
           for service_name in enabled_services:
               service_config = self.config.get_service_config(service_name)
               
               # 解析服务类
               service_class = self._resolve_service_class(service_name)
               if not service_class:
                   continue
               
               # 创建服务实例
               service_instance = self.di_container.resolve(service_class)
               
               # 初始化服务
               await service_instance.initialize(service_config)
               
               # 保存服务实例
               self.services[service_name] = service_instance
       
       def _resolve_service_class(self, service_name: str):
           """解析服务类"""
           # 服务名到类的映射
           service_mapping = {
               'agent_manager': 'AgentManager',
               'message_service': 'MessageService',
               'discovery_service': 'ResourceDiscoveryService',
               # ... 其他服务
           }
           
           class_name = service_mapping.get(service_name)
           if class_name:
               # 这里应该动态导入，简化示例
               return globals().get(class_name)
           
           return None
       
       async def shutdown(self):
           """关闭框架"""
           # 1. 停止服务
           for service in self.services.values():
               await service.cleanup()
           
           # 2. 清理插件
           await self.plugin_manager.cleanup_plugins()
           
           # 3. 清理资源
           self.services.clear()
   ```

## 测试策略

### 单元测试示例

```python
# tests/test_network_tool.py
import pytest
from tools.anp.network_tool import NetworkTool

@pytest.mark.asyncio
async def test_http_request():
    """测试 HTTP 请求"""
    tool = NetworkTool()
    await tool.initialize()
    
    try:
        result = await tool.http_request(
            url="https://httpbin.org/get",
            method="GET"
        )
        
        assert result['status_code'] == 200
        assert 'data' in result
    finally:
        await tool.cleanup()

@pytest.mark.asyncio
async def test_http_request_with_params():
    """测试带参数的 HTTP 请求"""
    tool = NetworkTool()
    await tool.initialize()
    
    try:
        result = await tool.http_request(
            url="https://httpbin.org/get",
            method="GET",
            params={'key': 'value'}
        )
        
        assert result['status_code'] == 200
        assert result['data']['args']['key'] == 'value'
    finally:
        await tool.cleanup()
```

### 集成测试示例

```python
# tests/test_service_integration.py
import pytest
from services.agent.agent_manager import AgentManager
from services.communication.message_service import MessageService

@pytest.mark.asyncio
async def test_agent_message_integration():
    """测试智能体管理和消息服务集成"""
    # 创建服务
    agent_manager = AgentManager()
    message_service = MessageService(agent_manager)
    
    # 初始化服务
    await agent_manager.initialize({})
    await message_service.initialize({})
    
    try:
        # 注册智能体
        from anp_open_sdk.anp_sdk_agent import LocalAgent
        agent1 = LocalAgent("agent1", "Agent 1")
        agent2 = LocalAgent("agent2", "Agent 2")
        
        await agent_manager.register_agent(agent1)
        await agent_manager.register_agent(agent2)
        
        # 发送消息
        success = await message_service.send_message(
            "agent1", "agent2", "Hello from agent1"
        )
        
        assert success == True
        assert "agent2" in message_service.message_queue
        assert len(message_service.message_queue["agent2"]) == 1
        
    finally:
        await message_service.cleanup()
        await agent_manager.cleanup()
```

### 端到端测试示例

```python
# tests/test_e2e_workflow.py
import pytest
from config.framework_bootstrap import FrameworkBootstrap

@pytest.mark.asyncio
async def test_complete_workflow():
    """测试完整的工作流"""
    # 启动框架
    bootstrap = FrameworkBootstrap("test_config.yaml")
    framework = await bootstrap.bootstrap()
    
    try:
        # 获取主智能体
        master_agent = framework.services.get('master_agent')
        
        # 执行搜索任务
        result = await master_agent.execute_task(
            "查找所有可用的智能体"
        )
        
        assert result['status'] == 'completed'
        assert 'agents' in result['results']
        
    finally:
        await bootstrap.shutdown()
```

## 迁移策略

### 渐进式迁移计划

#### 第一阶段：并行开发（1-2 周）
1. **保持现有代码运行**
   - 不修改现有的 `anp_open_sdk_framework` 代码
   - 创建新的 `anp_open_sdk_framework_v2` 目录
   - 实现核心基础设施

2. **建立兼容层**
   ```python
   # compatibility/legacy_adapter.py
   class LegacyAdapter:
       """旧版本兼容适配器"""
       
       def __init__(self, new_framework):
           self.new_framework = new_framework
       
       def get_unified_caller(self):
           """获取兼容的 UnifiedCaller"""
           return LegacyUnifiedCallerWrapper(
               self.new_framework.di_container.resolve(UnifiedCaller)
           )
   ```

#### 第二阶段：功能迁移（2-3 周）
1. **迁移核心功能**
   - Agent 管理功能
   - 统一调用功能
   - 本地方法管理

2. **迁移服务层**
   - 通信服务
   - 发现服务
   - 路由服务

3. **迁移工具层**
   - 拆分 ANPTool
   - 实现新的工具接口

#### 第三阶段：切换和验证（1-2 周）
1. **A/B 测试**
   ```python
   # 配置文件控制使用哪个版本
   framework_version: "v2"  # 或 "v1"
   ```

2. **性能对比**
   - 基准测试
   - 内存使用分析
   - 响应时间对比

3. **功能验证**
   - 回归测试
   - 集成测试
   - 用户验收测试

#### 第四阶段：完全切换（1 周）
1. **更新文档**
2. **迁移指南**
3. **废弃旧版本**

### 风险控制措施

1. **版本控制**
   ```python
   # 使用特性开关
   class FeatureFlags:
       USE_NEW_CALLER = False
       USE_NEW_CRAWLER = False
       USE_NEW_SERVICES = False
   ```

2. **回滚机制**
   - 保留旧版本代码
   - 配置快速切换
   - 数据兼容性保证

3. **监控和告警**
   ```python
   # utils/metrics.py
   class MetricsCollector:
       def record_api_call(self, api_name, duration, success):
           """记录 API 调用指标"""
           pass
       
       def record_error(self, error_type, error_message):
           """记录错误"""
           pass
   ```

## 预期收益

### 短期收益（1-2 个月）

1. **代码质量提升**
   - 模块职责清晰，易于理解
   - 单元测试覆盖率从 30% 提升到 80%
   - 代码复杂度降低 40%

2. **开发效率提升**
   - 新功能开发时间减少 50%
   - Bug 修复时间减少 60%
   - 代码审查时间减少 30%

3. **系统稳定性**
   - 错误率降低 70%
   - 平均故障恢复时间减少 80%

### 长期收益（3-6 个月）

1. **可扩展性**
   - 插件开发时间从天级降到小时级
   - 支持运行时动态加载/卸载功能
   - 第三方开发者贡献增加

2. **性能优化**
   - API 响应时间减少 30%
   - 内存使用减少 25%
   - 并发处理能力提升 3 倍

3. **生态建设**
   - 插件市场建立
   - 社区活跃度提升
   - 标准协议支持（MCP 等）

### 投资回报分析

| 指标 | 当前状态 | 重构后 | 改进幅度 |
|------|---------|--------|----------|
| 代码行数 | 15,000 | 12,000 | -20% |
| 模块数量 | 20 | 35 | +75%（更细粒度）|
| 平均模块大小 | 750 行 | 340 行 | -55% |
| 测试覆盖率 | 30% | 80% | +167% |
| 新功能开发时间 | 5 天 | 2.5 天 | -50% |
| Bug 修复时间 | 2 天 | 0.8 天 | -60% |
| 部署时间 | 30 分钟 | 10 分钟 | -67% |

## 总结

本重构方案通过以下关键改进，将显著提升 ANP Open SDK Framework 的质量：

1. **清晰的分层架构** - 每层职责明确，依赖关系简单
2. **服务化设计** - 功能模块化，易于独立开发和测试
3. **工具职责分离** - 每个工具专注单一功能
4. **插件化机制** - 支持动态扩展，降低耦合
5. **配置驱动** - 灵活的运行时配置

通过渐进式迁移策略，可以在保证系统稳定的前提下，逐步完成重构，最终实现一个更加健壮、灵活、高效的智能体框架。

## 附录：配置文件示例

```yaml
# framework_config.yaml
framework:
  version: "2.0"
  
enabled_services:
  - agent_manager
  - message_service
  - discovery_service
  - routing_service
  
services:
  agent_manager:
    max_agents: 100
    auto_cleanup: true
    
  message_service:
    max_queue_size: 10000
    enable_persistence: true
    
  discovery_service:
    enable_auto_discovery: true
    discovery_interval: 60
    
plugins:
  - path: ./plugins/builtin
  - path: ./plugins/custom
  
plugin_configs:
  mcp_plugin:
    servers:
      - name: "llm_server"
        transport: "stdio"
        command: ["mcp-server-llm"]
        
tools:
  network:
    timeout: 30
    max_retries: 3
    
  crawler:
    max_depth: 3
    concurrent_limit: 5
    
orchestration:
  workflow_engine:
    max_concurrent_workflows: 10
    
  task_scheduler:
    max_scheduled_tasks: 1000
```

---

**文档版本**: 1.0  
**创建日期**: 2025-01-08  
**作者**: ANP Framework Team  
**状态**: 待审核
