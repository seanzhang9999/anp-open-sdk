# DID/AD 配置化方案设计

## 1. 概述

本方案旨在解决 `router_did.py` 和 `router_publisher.py` 中 DID 文档和 Agent 描述（AD）生成逻辑的硬编码问题，通过配置化提升系统的灵活性和可维护性。

## 2. 现状分析

### 2.1 当前问题

#### router_did.py 中的硬编码问题
- **默认模板硬编码**（134-152行）：版本号、创建时间、安全定义等完全固定
- **静态接口硬编码**（164-183行）：接口列表和描述固定不变
- **路径构建逻辑固定**：缺乏灵活的路径策略

#### router_publisher.py 中的硬编码问题
- **路径构建逻辑固定**：文件路径构建方式单一
- **错误处理信息硬编码**：错误消息不支持国际化

### 2.2 影响范围
- 降低系统扩展性和可维护性
- 限制不同环境的适配能力
- 增加定制化部署成本
- 影响用户体验和个性化需求

## 3. 配置化方案设计

### 3.1 整体架构

```
config/
├── did_templates/
│   ├── default_ad_template.json
│   ├── default_did_template.json
│   └── custom_templates/
│       ├── {user_id}_ad_template.json
│       └── {user_id}_did_template.json
├── interface_configs/
│   ├── default_interfaces.json
│   ├── static_interfaces.json
│   └── custom_interfaces/
│       └── {user_id}_interfaces.json
└── path_strategies/
    ├── default_path_strategy.json
    └── custom_path_strategies.json
```

### 3.2 配置文件结构

#### 3.2.1 AD 模板配置 (default_ad_template.json)

```json
{
  "template_version": "1.0.0",
  "default_values": {
    "version": "0.1.0",
    "created_at": "2025-04-21T00:00:00Z",
    "security_definitions": {
      "didwba_sc": {
        "scheme": "didwba",
        "in": "header",
        "name": "Authorization"
      }
    }
  },
  "context": {
    "@vocab": "https://schema.org/",
    "did": "https://w3id.org/did#",
    "ad": "https://agent-network-protocol.com/ad#"
  },
  "type": "ad:AgentDescription",
  "name_template": "ANP Agent {agent.name}",
  "owner_template": {
    "name": "{agent.name}的开发者",
    "@id": "{agent.id}"
  },
  "description_template": "ANP Agent {agent.name} - {agent.description}",
  "customizable_fields": [
    "name",
    "description",
    "version",
    "owner",
    "security_definitions"
  ]
}
```

#### 3.2.2 静态接口配置 (static_interfaces.json)

```json
{
  "interfaces": [
    {
      "name": "natural_language_interface",
      "@type": "ad:NaturalLanguageInterface",
      "protocol": "YAML",
      "url_template": "http://{host}:{port}/wba/user/{user_id}/nlp_interface.yaml",
      "description": "提供自然语言交互接口的OpenAPI的YAML文件，可以通过接口与智能体进行自然语言交互"
    },
    {
      "name": "structured_interface_yaml",
      "@type": "ad:StructuredInterface",
      "protocol": "YAML",
      "url_template": "http://{host}:{port}/wba/user/{user_id}/api_interface.yaml",
      "description": "智能体的 YAML 描述的接口调用方法"
    },
    {
      "name": "structured_interface_json",
      "@type": "ad:StructuredInterface",
      "protocol": "JSON",
      "url_template": "http://{host}:{port}/wba/user/{user_id}/api_interface.json",
      "description": "智能体的 JSON RPC 描述的接口调用方法"
    }
  ],
  "filter_rules": {
    "include_patterns": [
      "/agent/api/"
    ],
    "exclude_patterns": [
      "/internal/",
      "/admin/"
    ]
  }
}
```

#### 3.2.3 路径策略配置 (default_path_strategy.json)

```json
{
  "strategies": {
    "did_document_path": {
      "pattern": "{user_did_path}/user_{user_id}/did_document.json",
      "fallback_patterns": [
        "{user_did_path}/user_{user_id}/did.json"
      ]
    },
    "hosted_did_path": {
      "pattern": "{user_hosted_path}/user_{user_id}/did_document.json",
      "fallback_patterns": [
        "{user_hosted_path}/user_{user_id}/did.json"
      ]
    },
    "template_ad_path": {
      "pattern": "{user_full_path}/template-ad.json",
      "fallback_patterns": [
        "{config_path}/did_templates/default_ad_template.json"
      ]
    },
    "openapi_yaml_path": {
      "pattern": "{user_did_path}/{user_dir}/{yaml_file_name}.yaml"
    },
    "jsonrpc_path": {
      "pattern": "{user_did_path}/{user_dir}/{jsonrpc_file_name}.json"
    }
  }
}
```

### 3.3 配置管理器设计

#### 3.3.1 配置加载器 (ConfigLoader)

```python
class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._templates_cache = {}
        self._interfaces_cache = {}
        self._strategies_cache = {}
    
    def load_ad_template(self, user_id: str = None) -> Dict:
        """加载 AD 模板，支持用户自定义覆盖"""
        
    def load_interfaces_config(self, user_id: str = None) -> Dict:
        """加载接口配置，支持用户自定义"""
        
    def load_path_strategy(self, strategy_name: str) -> Dict:
        """加载路径策略配置"""
        
    def reload_config(self):
        """重新加载配置（热更新）"""
```

#### 3.3.2 模板渲染器 (TemplateRenderer)

```python
class TemplateRenderer:
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
    
    def render_ad_document(self, agent, request, user_id: str) -> Dict:
        """渲染 AD 文档"""
        
    def render_interfaces(self, agent, request, endpoints: Dict) -> List[Dict]:
        """渲染接口列表"""
        
    def resolve_path(self, strategy_name: str, **kwargs) -> Path:
        """解析路径策略"""
```

## 4. 实现方案

### 4.1 重构步骤

#### 第一阶段：基础设施搭建
1. 创建配置文件目录结构
2. 实现 ConfigLoader 和 TemplateRenderer
3. 创建默认配置文件

#### 第二阶段：路由层重构
1. 重构 `router_did.py` 中的 `get_agent_description` 函数
2. 重构 `router_publisher.py` 中的路径处理逻辑
3. 添加配置热更新支持

#### 第三阶段：功能增强
1. 添加用户级别的配置覆盖
2. 实现配置验证和错误处理
3. 添加配置管理 API

### 4.2 核心代码示例

#### 重构后的 get_agent_description 函数

```python
@router.get("/wba/user/{user_id}/ad.json", summary="Get agent description")
async def get_agent_description(user_id: str, request: Request) -> Dict:
    """
    返回符合 schema.org/did/ad 规范的 JSON-LD 格式智能体描述
    """
    # 获取配置管理器
    config_loader = request.app.state.config_loader
    template_renderer = request.app.state.template_renderer
    
    # 解析 DID 和获取 agent
    resp_did = url_did_format(user_id, request)
    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent with DID {resp_did} not found")
    
    sdk = request.app.state.sdk
    agent = sdk.get_agent(resp_did)
    
    if agent.is_hosted_did:
        raise HTTPException(status_code=403, detail=f"{resp_did} is hosted did")
    
    # 获取动态端点
    endpoints = get_dynamic_endpoints(sdk, agent, resp_did)
    
    # 使用模板渲染器生成 AD 文档
    result = template_renderer.render_ad_document(agent, request, user_id)
    
    return result
```

## 5. 兼容性考虑

### 5.1 向后兼容
- 保留原有硬编码逻辑作为默认配置
- 支持渐进式迁移
- 提供配置迁移工具

### 5.2 版本管理
- 配置文件版本化
- 支持多版本配置并存
- 提供配置升级路径

## 6. 性能优化

### 6.1 缓存策略
- 配置文件缓存
- 模板编译缓存
- 支持配置热更新

### 6.2 延迟加载
- 按需加载配置
- 用户级配置懒加载
- 配置预编译

## 7. 安全考虑

### 7.1 配置验证
- 配置文件格式验证
- 模板安全检查
- 路径遍历防护

### 7.2 权限控制
- 配置文件访问权限
- 用户级配置隔离
- 敏感信息脱敏

## 8. 测试策略

### 8.1 单元测试
- ConfigLoader 测试
- TemplateRenderer 测试
- 路径解析测试

### 8.2 集成测试
- 端到端配置测试
- 性能基准测试
- 兼容性测试

## 9. 实施计划

### 9.1 时间安排
- 第一阶段：2周（基础设施）
- 第二阶段：3周（路由重构）
- 第三阶段：2周（功能增强）
- 测试和优化：1周

### 9.2 风险控制
- 分阶段实施
- 充分测试
- 回滚机制

## 10. 总结

本配置化方案通过将硬编码逻辑抽象为可配置的模板和策略，显著提升了系统的灵活性和可维护性。方案设计考虑了兼容性、性能、安全性等多个方面，为系统的长期发展奠定了良好基础。

建议按照分阶段实施的方式逐步推进，确保系统稳定性的同时获得配置化带来的收益。