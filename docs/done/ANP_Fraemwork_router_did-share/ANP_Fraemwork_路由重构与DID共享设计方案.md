# ANP SDK 路由重构与DID共享设计方案

## 📋 目录
1. [概述](#概述)
2. [当前问题分析](#当前问题分析)
3. [路由统一重构](#路由统一重构)
4. [DID共享机制](#did共享机制)
5. [配置文件标准化](#配置文件标准化)
6. [实现细节](#实现细节)
7. [部署与迁移](#部署与迁移)

## 概述

本方案旨在解决ANP SDK中Agent管理、路由分散、DID绑定等问题，通过统一路由架构和DID共享机制，实现更简洁、高效的Agent服务管理。

**🎉 重大突破：2025年7月13日，共享DID路由重构核心功能已成功实现并测试通过！**

### 核心目标
- ✅ 统一所有Agent通信到 `/agent/api/` 路由 **[已实现]**
- ✅ 支持DID共享，多个Agent共用一个DID **[已实现]**
- � 标准化配置文件格式和关系 **[部分完成]**
- 🔄 提供完整的检查和修复工具 **[进行中]**

### 实现成果
- ✅ **Calculator Agent** 和 **LLM Agent** 成功共享同一个DID
- ✅ 路径前缀机制完美工作：`/calculator/add` 和 `/llm/chat`
- ✅ Agent注册机制优化，修复共享DID Agent相互覆盖问题
- ✅ 智能路由解析，支持API调用和消息发送的不同策略
- ✅ 完整的测试验证：API调用(10+20=30)和消息发送功能正常

## 当前问题分析

### 1. 路由分散问题
```
当前分散的通信方式：
├── /agent/api/          # API调用
├── /agent/message/      # 消息发送  
├── /agent/group/        # 群组操作
└── 独立的GroupMember SDK # 群组成员管理
```

### 2. Agent管理混乱
- ANP_Server 运行时管理 vs LocalAgentManager 配置管理
- 缺乏统一的Agent生命周期管理
- 配置与运行时状态分离

### 3. DID绑定问题
- DID格式不一致（%3A编码问题）
- agent_mappings.yaml 与 agent_cfg.yaml 关系不清晰
- 缺乏DID共享机制

## 路由统一重构

### 1. 统一路由架构

#### 目标架构
```
统一路由格式：
├── /agent/api/{did}/message/send           # 消息发送
├── /agent/api/{did}/group/{group_id}/join  # 群组加入
├── /agent/api/{did}/group/{group_id}/message # 群组消息
├── /agent/api/{did}/custom_api             # 自定义API
└── /agent/api/{did}/*                      # 其他所有API
```

#### 路由器增强
```python
class UnifiedAgentRouter(AgentRouter):
    """统一Agent路由器"""
    
    def __init__(self, anp_server: ANP_Server):
        super().__init__()
        self.anp_server = anp_server
        self.config_manager = LocalAgentManager()
        self.shared_did_registry = {}  # shared_did -> SharedDIDConfig
        self.path_validator = SharedDIDPathValidator()
        
    async def route_unified_request(self, req_did: str, resp_did: str, 
                                  api_path: str, method: str, 
                                  request_data: Dict, request: Request):
        """统一路由处理"""
        
        # 1. 检查是否为共享DID
        if resp_did in self.shared_did_registry:
            target_agent_id, original_path = self._resolve_shared_did(resp_did, api_path)
            resp_did = target_agent_id
            api_path = original_path
        
        # 2. 构建请求数据
        unified_request_data = {
            'path': api_path,
            'method': method,
            'data': request_data,
            'headers': dict(request.headers)
        }
        
        # 3. 路由到具体Agent
        return await self._route_to_agent(req_did, resp_did, unified_request_data, request)
    
    def _resolve_shared_did(self, shared_did: str, api_path: str) -> Tuple[str, str]:
        """解析共享DID，返回(target_agent_id, original_path)"""
        config = self.shared_did_registry[shared_did]
        
        # 精确匹配
        if api_path in config['path_mappings']:
            agent_id, original_path = config['path_mappings'][api_path]
            return agent_id, original_path
        
        # 前缀匹配
        for full_path, (agent_id, original_path) in config['path_mappings'].items():
            if api_path.startswith(full_path.rstrip('*')):
                # 计算相对路径
                relative_path = api_path[len(full_path.rstrip('*')):]
                final_path = f"{original_path.rstrip('/')}{relative_path}"
                return agent_id, final_path
        
        raise ValueError(f"共享DID {shared_did} 中未找到路径 {api_path} 的处理器")
```

### 2. Agent管理统一

#### 混合管理模式

```python
class UnifiedAgentManager:
   """统一Agent管理器 - 结合配置管理和运行时管理"""

   def __init__(self, anp_server: ANP_Server):
      self.anp_server = anp_server
      self.config_manager = LocalAgentManager()
      self.runtime_agents = {}  # agent_id -> agent_instance
      self.shared_did_mappings = {}  # shared_did -> [agent_ids]

   async def load_and_register_agents(self):
      """从配置加载Agent并注册到服务器"""

      # 1. 发现所有Agent配置
      agent_configs = self._discover_agent_configs()

      # 2. 验证配置
      self._validate_configurations(agent_configs)

      # 3. 加载Agent实例
      for config_path in agent_configs:
         agent, handler_module = self.config_manager.load_agent_from_module(config_path)
         if agent:
            # 注册到运行时
            self.runtime_agents[agent.anp_user_id] = agent
            self.anp_server.register_anp_user(agent)

            # 处理共享DID
            await self._process_shared_did_config(agent, config_path)

            # 生成接口文档
            await self.config_manager.generate_and_save_agent_interfaces(agent, self.anp_server)

   async def _process_shared_did_config(self, agent: ANPUser, config_path: str):
      """处理共享DID配置"""
      with open(config_path, 'r') as f:
         config = yaml.safe_load(f)

      share_config = config.get('share_did', {})
      if share_config.get('enabled'):
         shared_did = share_config['shared_did']
         path_prefix = share_config.get('path_prefix', '')

         if shared_did not in self.shared_did_mappings:
            self.shared_did_mappings[shared_did] = []

         self.shared_did_mappings[shared_did].append({
            'agent_id': agent.anp_user_id,
            'path_prefix': path_prefix,
            'original_paths': [api['path'] for api in config.get('api', [])]
         })
```

## DID共享机制

### 1. 配置格式

#### 独立DID Agent
```yaml
# agents_config/weather_basic/agent_mappings.yaml
name: "weather_basic"
description: "基础天气服务"
unique_id: "weather001"
did: "did:wba:localhost:9527:wba:user:weather001"  # 标准格式，无编码
type: "user"

# 用户数据路径
user_data_path: "anp_users/user_weather001"

# API 配置
api:
  - path: "/current"
    method: "GET"
    handler: "get_current_weather"
  - path: "/today"
    method: "GET" 
    handler: "get_today_weather"
```

#### 共享DID Agent
```yaml
# agents_config/weather_advanced/agent_mappings.yaml
name: "weather_advanced"
description: "高级天气服务"
unique_id: "weather002"
# 注意：有share_did时不应该有did字段
type: "user"

# 共享DID配置
share_did:
  enabled: true
  shared_did: "did:wba:localhost:9527:wba:shared:weather"
  path_prefix: "/advanced"  # 路由时自动添加的前缀

# 用户数据路径
user_data_path: "anp_users/user_weather002"

# API 配置 - 保持原有格式，不需要修改
api:
  - path: "/forecast"      # 原始路径，实际访问路径为 /advanced/forecast
    method: "GET"
    handler: "get_forecast"
  - path: "/alerts"        # 原始路径，实际访问路径为 /advanced/alerts
    method: "GET"
    handler: "get_weather_alerts"
```

### 2. 路径冲突检测

```python
class SharedDIDPathValidator:
    """共享DID路径冲突检测器"""
    
    def __init__(self):
        self.shared_did_groups = {}  # shared_did -> {agents: [], path_map: {}}
    
    def load_agent_configs(self, config_dirs):
        """加载所有agent配置并分组"""
        for config_dir in config_dirs:
            config_file = os.path.join(config_dir, "agent_mappings.yaml")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                share_config = config.get('share_did', {})
                if share_config.get('enabled'):
                    shared_did = share_config['shared_did']
                    path_prefix = share_config.get('path_prefix', '')
                    
                    if shared_did not in self.shared_did_groups:
                        self.shared_did_groups[shared_did] = {
                            'agents': [],
                            'path_map': {}
                        }
                    
                    # 收集该agent的所有API路径（加上前缀后的完整路径）
                    agent_paths = []
                    for api in config.get('api', []):
                        original_path = api['path']
                        # 组合完整路径：path_prefix + original_path
                        full_path = f"{path_prefix.rstrip('/')}{original_path}"
                        agent_paths.append(full_path)
                        
                        # 检查路径冲突（基于完整路径）
                        if full_path in self.shared_did_groups[shared_did]['path_map']:
                            existing_agent = self.shared_did_groups[shared_did]['path_map'][full_path]
                            raise ValueError(f"路径冲突: {full_path} 被 {existing_agent} 和 {config['name']} 同时声明")
                        
                        self.shared_did_groups[shared_did]['path_map'][full_path] = config['name']
                    
                    self.shared_did_groups[shared_did]['agents'].append({
                        'name': config['name'],
                        'unique_id': config['unique_id'],
                        'path_prefix': path_prefix,
                        'original_paths': [api['path'] for api in config.get('api', [])],  # 原始路径
                        'full_paths': agent_paths,  # 完整路径
                        'config_file': config_file
                    })
    
    def validate_path_conflicts(self) -> Dict[str, List[str]]:
        """检测路径冲突"""
        conflicts = {}
        
        for shared_did, group_info in self.shared_did_groups.items():
            path_conflicts = []
            path_owners = {}
            
            for agent in group_info['agents']:
                for path in agent['full_paths']:
                    if path in path_owners:
                        conflict_msg = f"路径 '{path}' 冲突: {path_owners[path]} vs {agent['name']}"
                        path_conflicts.append(conflict_msg)
                    else:
                        path_owners[path] = agent['name']
            
            if path_conflicts:
                conflicts[shared_did] = path_conflicts
        
        return conflicts
    
    def suggest_path_fixes(self, shared_did: str) -> List[str]:
        """建议路径修复方案"""
        suggestions = []
        group_info = self.shared_did_groups.get(shared_did, {})
        
        for agent in group_info.get('agents', []):
            if not agent.get('path_prefix'):
                suggestion = f"建议为 {agent['name']} 添加 path_prefix: '/{agent['unique_id']}'"
                suggestions.append(suggestion)
        
        return suggestions
```

### 3. 路由示例

```python
# 客户端请求示例
# 请求: POST /agent/api/did:wba:localhost:9527:wba:shared:weather
# Body: {"path": "/advanced/forecast", "method": "GET", "data": {...}}

# 路由器处理流程：
# 1. 识别为共享DID: did:wba:localhost:9527:wba:shared:weather
# 2. 根据路径 "/advanced/forecast" 找到对应的agent: weather_advanced
# 3. 将路径转换为原始路径: "/forecast"
# 4. 转发给 weather_advanced agent 处理

# 内部路由映射表：
shared_did_registry = {
    "did:wba:localhost:9527:wba:shared:weather": {
        "path_mappings": {
            "/basic/current": ("weather_basic_agent_id", "/current"),
            "/basic/today": ("weather_basic_agent_id", "/today"),
            "/advanced/forecast": ("weather_advanced_agent_id", "/forecast"),
            "/advanced/alerts": ("weather_advanced_agent_id", "/alerts")
        }
    }
}
```

## 配置文件标准化

### 1. 文件结构标准
```
data_user/localhost_9527/
├── agents_config/
│   ├── agent_001/
│   │   ├── agent_mappings.yaml    # Agent 配置和 API 定义
│   │   ├── agent_handlers.py      # Agent 处理器
│   │   └── agent_register.py      # Agent 注册逻辑（可选）
│   └── weather_service/
│       ├── agent_mappings.yaml    # 共享DID配置
│       └── agent_handlers.py
└── anp_users/
    ├── user_3ea884878ea5fbb1/
    │   ├── did_document.json       # DID 文档
    │   ├── agent_cfg.yaml          # Agent 身份信息
    │   ├── api_interface.yaml      # API 接口定义
    │   └── api_interface.json      # JSON-RPC 接口定义
    └── user_weather002/
        ├── did_document.json
        ├── agent_cfg.yaml
        └── ...
```

### 2. 配置关系标准

#### agent_mappings.yaml (Agent配置 - 在agents_config/目录下)
```yaml
# Agent 身份配置
name: "weather_advanced"
description: "高级天气服务"
unique_id: "weather002"
did: "did:wba:localhost:9527:wba:user:weather002"  # 标准格式，无编码
type: "user"

# 用户数据路径
user_data_path: "anp_users/user_weather002"

# API 配置
api:
  - path: "/forecast"
    method: "GET"
    handler: "get_forecast"
    description: "获取天气预报"
  - path: "/alerts"
    method: "GET"
    handler: "get_alerts"
    description: "获取天气警报"

# 元数据
metadata:
  version: "1.0.0"
  created_at: "2024-01-01T00:00:00Z"
  tags: ["weather", "advanced"]
```

#### agent_cfg.yaml (用户身份信息 - 在anp_users/目录下)
```yaml
# 用户身份基本信息
name: "weather_advanced"
unique_id: "weather002"
did: "did:wba:localhost:9527:wba:user:weather002"
type: "user"

# 关联的 Agent 配置
agent_config_path: "agents_config/weather_advanced"

# 能力描述
capabilities:
  - "weather_forecast"
  - "weather_alerts"
  - "advanced_analysis"

# 服务配置
service:
  host: "localhost"
  port: 9527
  endpoints:
    - "/forecast"
    - "/alerts"
```

#### 关联关系
1. **通过DID关联**: agent_mappings.yaml (did: xxx) ←→ agent_cfg.yaml (did: xxx)
2. **通过路径关联**: 
   - agent_mappings.yaml 中的 `user_data_path: "anp_users/user_weather002"`
   - agent_cfg.yaml 中的 `agent_config_path: "agents_config/weather_advanced"`

#### 共享DID的配置差异
```yaml
# 独立DID的agent_mappings.yaml
name: "weather_basic"
unique_id: "weather001"
did: "did:wba:localhost:9527:wba:user:weather001"  # 有独立DID
user_data_path: "anp_users/user_weather001"

# 共享DID的agent_mappings.yaml
name: "weather_advanced"
unique_id: "weather002"
# 注意：有share_did时不应该有did字段
share_did:
  enabled: true
  shared_did: "did:wba:localhost:9527:wba:shared:weather"
  path_prefix: "/advanced"
user_data_path: "anp_users/user_weather002"
```

### 3. DID格式标准化

#### 标准DID格式
```yaml
# ✅ 正确格式
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"

# ❌ 错误格式（包含编码）
did: "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"

# ✅ 共享DID格式
shared_did: "did:wba:localhost:9527:wba:shared:weather"
```

## 实现细节

### 1. 增强的绑定检查脚本

```python
class EnhancedAgentUserBindingManager(AgentUserBindingManager):
    
    def __init__(self, root_dir: Optional[str] = None):
        super().__init__(root_dir)
        self.shared_did_configs = {}
        self.path_validator = SharedDIDPathValidator()
    
    def validate_config_consistency(self):
        """验证配置一致性"""
        errors = []
        
        for file_path, agent_info in self.agent_mappings.items():
            config = agent_info['config']
            
            # 检查1: share_did和did不能同时存在
            has_did = 'did' in config and config['did']
            has_share_did = 'share_did' in config and config['share_did'].get('enabled')
            
            if has_did and has_share_did:
                errors.append(f"{agent_info['name']}: 不能同时配置 'did' 和 'share_did'")
            
            if not has_did and not has_share_did:
                errors.append(f"{agent_info['name']}: 必须配置 'did' 或 'share_did' 之一")
            
            # 检查2: DID格式标准化
            if has_did:
                did = config['did']
                if '%3A' in did:
                    errors.append(f"{agent_info['name']}: DID格式应使用标准格式，不要使用 %3A 编码")
            
            # 检查3: 共享DID格式
            if has_share_did:
                shared_did = config['share_did']['shared_did']
                if ':shared:' not in shared_did:
                    errors.append(f"{agent_info['name']}: 共享DID应包含 ':shared:' 标识")
        
        return errors
    
    def check_shared_did_path_conflicts(self):
        """检查共享DID路径冲突"""
        try:
            config_dirs = [str(info['file_path'].parent) for info in self.agent_mappings.values()]
            self.path_validator.load_agent_configs(config_dirs)
            conflicts = self.path_validator.validate_path_conflicts()
            return conflicts
        except Exception as e:
            return {"error": str(e)}
    
    def fix_did_format(self, file_path: str) -> bool:
        """修复DID格式"""
        agent_info = self.agent_mappings[file_path]
        config = agent_info['config']
        
        if 'did' in config and '%3A' in config['did']:
            # 修复DID格式
            old_did = config['did']
            new_did = old_did.replace('%3A', ':')
            config['did'] = new_did
            
            try:
                with open(agent_info['file_path'], 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                
                print(f"   ✅ 已修复DID格式: {old_did} -> {new_did}")
                return True
            except Exception as e:
                print(f"   ❌ 修复DID格式失败: {e}")
                return False
        
        return True
    
    def run_enhanced_checks(self):
        """运行增强检查"""
        print("🚀 开始增强的Agent用户绑定检查...")
        
        # 1. 基础检查
        self.discover_directories()
        self.load_agent_mappings()
        self.load_user_dids()
        
        # 2. 配置一致性检查
        print("\n🔍 检查配置一致性...")
        consistency_errors = self.validate_config_consistency()
        if consistency_errors:
            print("❌ 发现配置一致性错误:")
            for error in consistency_errors:
                print(f"   {error}")
        
        # 3. DID格式修复
        print("\n🔧 检查并修复DID格式...")
        for file_path in self.agent_mappings:
            self.fix_did_format(file_path)
        
        # 4. 共享DID路径冲突检查
        print("\n🔍 检查共享DID路径冲突...")
        path_conflicts = self.check_shared_did_path_conflicts()
        if "error" in path_conflicts:
            print(f"❌ 路径冲突检查失败: {path_conflicts['error']}")
        elif path_conflicts:
            print("❌ 发现共享DID路径冲突:")
            for shared_did, conflicts in path_conflicts.items():
                print(f"   共享DID: {shared_did}")
                for conflict in conflicts:
                    print(f"     {conflict}")
                
                # 提供修复建议
                suggestions = self.path_validator.suggest_path_fixes(shared_did)
                if suggestions:
                    print("   修复建议:")
                    for suggestion in suggestions:
                        print(f"     {suggestion}")
        else:
            print("✅ 共享DID路径检查通过!")
        
        # 5. 生成报告
        self.generate_enhanced_report()
```

### 2. 路由中间件

```python
class UnifiedRoutingMiddleware:
   """统一路由中间件"""

   def __init__(self, agent_manager: UnifiedAgentManager):
      self.agent_manager = agent_manager
      self.router = agent_manager.anp_server.router_agent

   async def __call__(self, request: Request, call_next):
      """中间件处理逻辑"""

      # 检查是否为Agent API请求
      if request.url.path.startswith('/agent/api/'):
         return await self._handle_agent_request(request)

      # 其他请求正常处理
      return await call_next(request)

   async def _handle_agent_request(self, request: Request):
      """处理Agent API请求"""

      # 解析路径: /agent/api/{did}/{api_path}
      path_parts = request.url.path.split('/')
      if len(path_parts) < 4:
         raise HTTPException(status_code=400, detail="Invalid agent API path")

      resp_did = path_parts[3]  # 目标DID
      api_path = '/' + '/'.join(path_parts[4:]) if len(path_parts) > 4 else '/'

      # 获取请求DID（从认证头中）
      req_did = self._extract_req_did_from_auth(request)

      # 获取请求数据
      if request.method == 'POST':
         request_data = await request.json()
      else:
         request_data = dict(request.query_params)

      # 统一路由处理
      return await self.router.route_unified_request(
         req_did=req_did,
         resp_did=resp_did,
         api_path=api_path,
         method=request.method,
         request_data=request_data,
         request=request
      )
```

## 部署与迁移

### 1. 迁移步骤

#### 第一阶段：配置标准化
1. 运行 `agent_user_binding.py --auto-fix` 修复DID格式
2. 更新所有 `agent_mappings.yaml` 到标准格式
3. 验证配置一致性

#### 第二阶段：路由统一
1. 部署统一路由中间件
2. 更新客户端调用方式
3. 逐步迁移现有API调用

#### 第三阶段：DID共享
1. 识别需要共享DID的Agent组
2. 配置共享DID和路径前缀
3. 测试路径冲突检测

### 2. 兼容性保证

```python
class BackwardCompatibilityRouter:
    """向后兼容路由器"""
    
    def __init__(self, unified_router: UnifiedAgentRouter):
        self.unified_router = unified_router
    
    async def handle_legacy_request(self, request: Request):
        """处理旧版本请求"""
        
        # 旧版本路径映射
        legacy_mappings = {
            '/agent/message/': '/agent/api/{did}/message/',
            '/agent/group/': '/agent/api/{did}/group/',
        }
        
        # 转换为新格式
        for old_pattern, new_pattern in legacy_mappings.items():
            if request.url.path.startswith(old_pattern):
                # 提取DID和转换路径
                new_path = self._convert_legacy_path(request.url.path, old_pattern, new_pattern)
                # 转发到统一路由器
                return await self._forward_to_unified_router(request, new_path)
        
        # 不是旧版本请求，正常处理
        return None
```

### 3. 监控和日志

```python
class AgentRoutingMonitor:
    """Agent路由监控"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'shared_did_requests': 0,
            'path_conflicts': 0,
            'routing_errors': 0
        }
    
    def log_request(self, req_did: str, resp_did: str, api_path: str, success: bool):
        """记录请求日志"""
        self.metrics['total_requests'] += 1
        
        if ':shared:' in resp_did:
            self.metrics['shared_did_requests'] += 1
        
        if not success:
            self.metrics['routing_errors'] += 1
        
        logger.info(f"Agent路由: {req_did} -> {resp_did}{api_path} ({'成功' if success else '失败'})")
    
    def get_metrics(self) -> Dict:
        """获取监控指标"""
        return self.metrics.copy()
```

## 多域名路由增强

### 1. 多域名支持问题分析

#### 当前 `AgentRouter` 的问题

```python
# 当前的问题代码
class AgentRouter:
   def __init__(self):
      self.local_agents = {}  # 问题：全局共享，没有域名隔离

   def register_agent(self, agent):
      self.local_agents[str(agent.anp_user_id)] = agent  # 问题：可能覆盖不同域名的同名agent

   async def route_request(self, req_did: str, resp_did: str, request_data: Dict, request: Request):
      resp_did = url_did_format(resp_did, request)
      if resp_did in self.local_agents:  # 问题：没有验证域名权限
         return await self.local_agents[resp_did].handle_request(...)
```

#### 具体风险场景
1. **域名A**: `user.localhost:9527` 注册了 `agent_001`
2. **域名B**: `service.localhost:9527` 也注册了 `agent_001`
3. **结果**: 后注册的会覆盖先注册的，导致路由错误

#### 安全风险
- 跨域名的智能体访问
- 域名权限绕过
- 数据泄露风险

### 2. 增强的 AgentRouter 设计

#### 新的数据结构
```python
class EnhancedAgentRouter(AgentRouter):
    def __init__(self):
        # 多级索引结构：domain -> port -> agent_id -> agent
        self.domain_agents = {}  # {domain: {port: {agent_id: agent}}}
        self.global_agents = {}  # 向后兼容的全局索引
        self.domain_manager = get_domain_manager()
        self.logger = logger
        
        # 统计信息
        self.stats = {
            'total_agents': 0,
            'domains_count': 0,
            'registration_conflicts': 0,
            'routing_errors': 0
        }
```

#### 增强的注册方法

```python
def register_agent_with_domain(self, agent, domain: str = None, port: int = None, request: Request = None):
   """
   注册智能体到指定域名
   
   Args:
       agent: 智能体实例
       domain: 域名（可选，从request中提取）
       port: 端口（可选，从request中提取）
       request: HTTP请求对象（用于自动提取域名信息）
   """
   # 1. 确定域名和端口
   if request:
      domain, port = self.domain_manager.get_host_port_from_request(request)
   elif not domain or not port:
      domain, port = self.domain_manager._get_default_host_port()

   # 2. 验证域名权限
   is_valid, error_msg = self.domain_manager.validate_domain_access(domain, port)
   if not is_valid:
      raise ValueError(f"域名注册被拒绝: {error_msg}")

   # 3. 确保域名目录存在
   self.domain_manager.ensure_domain_directories(domain, port)

   # 4. 初始化域名结构
   if domain not in self.domain_anp_users:
      self.domain_anp_users[domain] = {}
      self.stats['domains_count'] += 1

   if port not in self.domain_anp_users[domain]:
      self.domain_anp_users[domain][port] = {}

   # 5. 检查冲突
   agent_id = str(agent.anp_user_id)
   if agent_id in self.domain_anp_users[domain][port]:
      self.stats['registration_conflicts'] += 1
      self.logger.warning(f"智能体注册冲突: {domain}:{port} 已存在 {agent_id}")
      if not getattr(agent, 'allow_override', False):
         raise ValueError(f"智能体 {agent_id} 已在 {domain}:{port} 注册")

   # 6. 注册智能体
   self.domain_anp_users[domain][port][agent_id] = agent

   # 7. 更新全局索引（向后兼容）
   global_key = f"{domain}:{port}:{agent_id}"
   self.global_agents[global_key] = agent
   self.global_agents[agent_id] = agent  # 保持原有行为

   # 8. 更新统计
   self.stats['total_agents'] += 1

   self.logger.info(f"✅ 智能体注册成功: {agent_id} @ {domain}:{port}")
   return agent


# 向后兼容的注册方法
def register_agent(self, agent):
   """向后兼容的注册方法"""
   return self.register_agent_with_domain(agent)
```

#### 增强的路由方法

```python
async def route_request_with_domain_validation(self, req_did: str, resp_did: str,
                                               request_data: Dict, request: Request) -> Any:
   """带域名验证的路由请求"""

   # 1. 提取请求域名信息
   domain, port = self.domain_manager.get_host_port_from_request(request)

   # 2. 验证域名访问权限
   is_valid, error_msg = self.domain_manager.validate_domain_access(domain, port)
   if not is_valid:
      self.stats['routing_errors'] += 1
      raise HTTPException(status_code=403, detail=f"域名访问被拒绝: {error_msg}")

   # 3. 格式化目标DID
   resp_did = url_did_format(resp_did, request)

   # 4. 多级查找智能体
   agent = self._find_agent_with_domain_priority(resp_did, domain, port)

   if not agent:
      self.stats['routing_errors'] += 1
      available_agents = self._get_available_agents_for_domain(domain, port)
      raise ValueError(
         f"未找到智能体: {resp_did} @ {domain}:{port}\n"
         f"可用智能体: {available_agents}"
      )

   # 5. 验证跨域访问权限
   if not self._validate_cross_domain_access(req_did, resp_did, domain, port):
      self.stats['routing_errors'] += 1
      raise HTTPException(status_code=403, detail="跨域访问被拒绝")

   # 6. 设置请求上下文
   request.state.anp_user = agent
   request.state.domain = domain
   request.state.port = port

   # 7. 执行路由
   try:
      self.logger.info(f"🚀 路由请求: {req_did} -> {resp_did} @ {domain}:{port}")
      result = await agent.handle_request(req_did, request_data, request)
      return result
   except Exception as e:
      self.stats['routing_errors'] += 1
      self.logger.error(f"❌ 路由执行失败: {e}")
      raise


def _find_agent_with_domain_priority(self, agent_id: str, domain: str, port: int):
   """
   按优先级查找智能体：
   1. 当前域名:端口下的智能体
   2. 当前域名下其他端口的智能体
   3. 全局智能体（向后兼容）
   """
   # 优先级1: 精确匹配域名和端口
   if (domain in self.domain_anp_users and
           port in self.domain_anp_users[domain] and
           agent_id in self.domain_anp_users[domain][port]):
      return self.domain_anp_users[domain][port][agent_id]

   # 优先级2: 同域名不同端口
   if domain in self.domain_anp_users:
      for other_port, agents in self.domain_anp_users[domain].items():
         if agent_id in agents:
            self.logger.warning(f"跨端口访问: {agent_id} @ {domain}:{other_port} -> {domain}:{port}")
            return agents[agent_id]

   # 优先级3: 全局查找（向后兼容）
   if agent_id in self.global_agents:
      self.logger.warning(f"全局智能体访问: {agent_id}")
      return self.global_agents[agent_id]

   return None


def _validate_cross_domain_access(self, req_did: str, resp_did: str, domain: str, port: int) -> bool:
   """验证跨域访问权限"""
   try:
      # 检查是否允许跨域访问
      cross_domain_config = self.domain_manager.config.did_config.cross_domain
      if not cross_domain_config.get('enabled', False):
         return True  # 默认允许

      # 检查白名单
      whitelist = cross_domain_config.get('whitelist', [])
      if req_did in whitelist:
         return True

      # 检查黑名单
      blacklist = cross_domain_config.get('blacklist', [])
      if req_did in blacklist:
         return False

      # 检查域名规则
      domain_rules = cross_domain_config.get('domain_rules', {})
      current_domain_key = f"{domain}:{port}"
      if current_domain_key in domain_rules:
         allowed_patterns = domain_rules[current_domain_key]
         for pattern in allowed_patterns:
            if self.domain_manager._match_pattern(req_did, pattern):
               return True
         return False

      return True  # 默认允许

   except Exception as e:
      self.logger.error(f"跨域访问验证失败: {e}")
      return True  # 出错时默认允许
```

### 3. 域名管理增强

#### 智能体查询方法

```python
def get_agents_by_domain(self, domain: str, port: int = None) -> Dict:
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


def get_domain_statistics(self) -> Dict:
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


def cleanup_domain(self, domain: str, port: int = None):
   """清理指定域名的智能体"""
   if domain not in self.domain_anp_users:
      return

   if port:
      # 清理指定端口
      if port in self.domain_anp_users[domain]:
         agents = self.domain_anp_users[domain][port]
         for agent_id in list(agents.keys()):
            self._unregister_agent(domain, port, agent_id)
         del self.domain_anp_users[domain][port]
   else:
      # 清理整个域名
      for port in list(self.domain_anp_users[domain].keys()):
         self.cleanup_domain(domain, port)
      del self.domain_anp_users[domain]
      self.stats['domains_count'] -= 1


def _unregister_agent(self, domain: str, port: int, agent_id: str):
   """注销智能体"""
   # 从域名索引中移除
   if (domain in self.domain_anp_users and
           port in self.domain_anp_users[domain] and
           agent_id in self.domain_anp_users[domain][port]):
      del self.domain_anp_users[domain][port][agent_id]
      self.stats['total_agents'] -= 1

   # 从全局索引中移除
   global_key = f"{domain}:{port}:{agent_id}"
   if global_key in self.global_agents:
      del self.global_agents[global_key]

   # 如果没有其他域名使用，也从简单索引中移除
   if agent_id in self.global_agents:
      # 检查是否还有其他域名在使用
      still_in_use = False
      for d, ports in self.domain_anp_users.items():
         for p, agents in ports.items():
            if agent_id in agents:
               still_in_use = True
               break
         if still_in_use:
            break

      if not still_in_use:
         del self.global_agents[agent_id]
```

### 4. 配置文件增强

#### 域名配置示例
```yaml
# unified_config.yaml
did_config:
  hosts:
    localhost: 9527
    user.localhost: 9527
    service.localhost: 9527
    api.localhost: 8080
  
  parsing:
    default_host: "localhost"
    default_port: 9527
    allow_insecure: true
  
  cross_domain:
    enabled: true
    whitelist:
      - "did:wba:localhost:9527:wba:admin:*"
    blacklist:
      - "did:wba:malicious.com:*"
    domain_rules:
      "user.localhost:9527":
        - "did:wba:localhost:9527:wba:user:*"
        - "did:wba:service.localhost:9527:wba:service:*"
      "service.localhost:9527":
        - "did:wba:*:wba:user:*"
  
  insecure_patterns:
    - "*.tests.com:*"
    - "localhost:*"
```

### 5. 监控和调试工具

#### 域名路由监控
```python
class DomainRoutingMonitor:
    def __init__(self, router: EnhancedAgentRouter):
        self.router = router
        self.request_log = []
        self.error_log = []
    
    def log_request(self, req_did: str, resp_did: str, domain: str, port: int, 
                   success: bool, error_msg: str = None):
        """记录路由请求"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'req_did': req_did,
            'resp_did': resp_did,
            'domain': domain,
            'port': port,
            'success': success,
            'error_msg': error_msg
        }
        
        self.request_log.append(log_entry)
        if not success:
            self.error_log.append(log_entry)
        
        # 保持日志大小
        if len(self.request_log) > 1000:
            self.request_log = self.request_log[-500:]
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-50:]
    
    def get_domain_health(self) -> Dict:
        """获取域名健康状态"""
        stats = self.router.get_domain_statistics()
        
        # 计算成功率
        recent_requests = self.request_log[-100:]  # 最近100个请求
        if recent_requests:
            success_count = sum(1 for req in recent_requests if req['success'])
            success_rate = success_count / len(recent_requests)
        else:
            success_rate = 1.0
        
        return {
            'total_domains': stats['domains_count'],
            'total_agents': stats['total_agents'],
            'success_rate': success_rate,
            'recent_errors': len([e for e in self.error_log if 
                                datetime.fromisoformat(e['timestamp']) > 
                                datetime.now() - timedelta(hours=1)]),
            'domain_details': stats['domain_details']
        }
```

### 6. 实施计划

#### 第一阶段：基础架构升级
1. **实现 EnhancedAgentRouter**
   - 替换现有的 AgentRouter
   - 保持向后兼容性
   - 添加域名隔离功能

2. **集成域名管理器**
   - 在路由中集成 DomainManager
   - 添加域名验证逻辑
   - 实现跨域访问控制

#### 第二阶段：监控和工具
1. **部署监控系统**
   - 实现 DomainRoutingMonitor
   - 添加健康检查端点
   - 配置告警机制

2. **开发调试工具**
   - 域名统计查询接口
   - 智能体注册状态查看
   - 路由冲突检测工具

#### 第三阶段：配置和优化
1. **配置文件标准化**
   - 更新域名配置格式
   - 添加跨域访问规则
   - 配置安全策略

2. **性能优化**
   - 优化路由查找算法
   - 添加缓存机制
   - 减少内存占用

### 7. 测试和验证

#### 单元测试
```python
class TestEnhancedAgentRouter:
    def test_domain_isolation(self):
        """测试域名隔离功能"""
        router = EnhancedAgentRouter()
        
        # 在不同域名注册同名智能体
        agent1 = MockAgent("agent_001")
        agent2 = MockAgent("agent_001")
        
        router.register_agent_with_domain(agent1, "user.localhost", 9527)
        router.register_agent_with_domain(agent2, "service.localhost", 9527)
        
        # 验证隔离效果
        assert router.get_agents_by_domain("user.localhost", 9527)["agent_001"] == agent1
        assert router.get_agents_by_domain("service.localhost", 9527)["agent_001"] == agent2
    
    def test_cross_domain_access_control(self):
        """测试跨域访问控制"""
        # 配置跨域规则
        # 测试白名单、黑名单、域名规则
        pass
    
    def test_routing_priority(self):
        """测试路由优先级"""
        # 测试域名优先级查找逻辑
        pass
```

#### 集成测试
```python
class TestDomainRoutingIntegration:
    def test_multi_domain_deployment(self):
        """测试多域名部署场景"""
        # 模拟多域名环境
        # 测试路由正确性
        pass
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 验证旧版本客户端仍能正常工作
        pass
```

## 总结

本方案通过以下核心改进实现了ANP SDK的架构优化：

### ✅ 主要收益
1. **统一路由**: 所有Agent通信统一到 `/agent/api/` 下
2. **DID共享**: 支持多个Agent共享一个DID，提高资源利用率
3. **配置标准化**: 统一的配置文件格式和关系
4. **自动化工具**: 完整的检查、修复和监控工具
5. **向后兼容**: 平滑迁移，不影响现有功能
6. **多域名支持**: 完整的域名隔离和跨域访问控制

### 🎯 技术特点
- 基于路径的智能路由
- 自动冲突检测和修复建议
- 完整的配置验证机制
- 灵活的Agent管理架构
- 详细的监控和日志系统
- 多级域名隔离机制
- 智能的路由优先级算法

### 🔒 安全增强
- 域名级别的访问控制
- 跨域访问权限验证
- 智能体注册冲突检测
- 详细的审计日志

这个设计既解决了当前的架构问题，又为未来的扩展提供了良好的基础，特别是在多域名环境下的安全性和可管理性方面有了显著提升。
