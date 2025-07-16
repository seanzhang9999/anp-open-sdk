# ANP SDK DID 格式与多域名体系开发计划

## 项目概述

本文档详细描述了 ANP SDK 中 DID (Decentralized Identifier) 格式的统一配置方案、多域名体系的实现方法，以及相关新功能的开发计划。通过统一的配置管理和 DID 格式管理器，实现了单实例多域名支持，简化了部署和管理复杂度。

## 目录

- [DID 格式规范](#did-格式规范)
- [多域名体系架构](#多域名体系架构)
- [配置文件结构](#配置文件结构)
- [DID 格式管理器](#did-格式管理器)
- [本地 DNS 配置](#本地-dns-配置)
- [开发计划](#开发计划)
- [实施路线图](#实施路线图)
- [使用指南](#使用指南)
- [故障排除](#故障排除)

## DID 格式规范

### 标准格式（保留%3A编码）

```
did:wba:localhost%3A9527:wba:user:abc123
```

**格式说明：**
- `did`: DID 标准前缀
- `wba`: 方法名称（Web-Based Authentication）
- `localhost%3A9527`: 主机和端口（使用%3A编码）
- `wba`: 方法名称重复（用于命名空间）
- `user`: 用户类型
- `abc123`: 唯一标识符

### %3A编码的设计价值

#### 为什么保留%3A编码：

1. **端口识别明确性**
   ```
   did:wba:localhost%3A9527:wba:user:abc123
            ^^^^^^^^
            明确标识这是 localhost:9527
   ```

2. **URL安全性**
   ```bash
   # %3A编码在URL中是安全的
   GET /api/resolve/did:wba:localhost%3A9527:wba:user:abc123
   
   # 标准冒号可能在某些URL解析器中造成问题
   GET /api/resolve/did:wba:localhost:9527:wba:user:abc123
   #                              ^ 可能被误解析为端口分隔符
   ```

3. **非标准端口的明确性**
   ```
   did:wba:example.com%3A8080:wba:user:test    # 清晰：8080端口
   did:wba:example.com:8080:wba:user:test      # 模糊：可能被误解析
   ```

4. **解析确定性**
   - 避免冒号过多导致的解析歧义
   - 在DID字符串中，%3A让端口部分非常明显
   - 提供更好的解析器健壮性

### 用户类型定义

| 类型 | 说明 | 可创建 | 用途 | 路由模板 |
|------|------|--------|------|----------|
| `user` | DNS服务上的用户 | ✅ | 普通用户身份 | `/{method}/user/{user_id}/did.json` |
| `hostuser` | DNS服务托管的用户 | ❌ | 托管身份（私钥不在服务器） | `/{method}/hostuser/{user_id}/did.json` |
| `test` | 测试用户 | ❌ | 共享测试身份 | `/{method}/test/{user_name}/did.json` |

### DID 格式设计理念

#### %3A编码的技术优势
- **URL编码标准**: 符合RFC 3986标准，在HTTP传输中更安全
- **解析清晰性**: 端口部分不会与其他冒号混淆
- **兼容性好**: 在各种URL解析器中表现一致
- **标识明确**: 一眼就能看出这是端口号

#### 真正需要改进的地方
- **多域名路由系统**: 增强基于Host头的路由分发
- **配置管理灵活性**: 提供更灵活的配置选项
- **DID解析器的健壮性**: 优化%3A编码的解析逻辑
- **文档和最佳实践**: 说明%3A编码的设计价值

## 多域名体系架构

### 单实例多域名架构

```
┌─────────────────────────────────────────────────────────────┐
│                    单个服务实例                              │
│                 (0.0.0.0:9527)                             │
├─────────────────────────────────────────────────────────────┤
│  DID 格式管理器 + 请求路由器 (根据 Host 头部分发)            │
├─────────────────────────────────────────────────────────────┤
│  user.localhost:9527     │  service.localhost:9527         │
│  ├── anp_users/          │  ├── anp_users/                 │
│  ├── anp_users_hosted/   │  ├── anp_users_hosted/          │
│  └── agents_config/      │  └── agents_config/             │
├─────────────────────────────────────────────────────────────┤
│  agent.localhost:9527    │  test.localhost:9527            │
│  ├── anp_users/          │  ├── anp_users/                 │
│  ├── anp_users_hosted/   │  ├── anp_users_hosted/          │
│  └── agents_config/      │  └── agents_config/             │
└─────────────────────────────────────────────────────────────┘
```

### 目录结构

```
data_user/
├── user.localhost_9527/          # user.localhost 的数据
│   ├── anp_users/
│   │   ├── user_abc123/
│   │   │   ├── did_document.json
│   │   │   ├── api_interface.yaml
│   │   │   └── api_interface.json
│   │   └── user_def456/
│   ├── anp_users_hosted/
│   └── agents_config/
│       └── suzuki_agent/
│           └── agent_mappings.yaml
├── service.localhost_9527/       # service.localhost 的数据
│   ├── anp_users/
│   ├── anp_users_hosted/
│   └── agents_config/
├── agent.localhost_9527/         # agent.localhost 的数据
│   ├── anp_users/
│   ├── anp_users_hosted/
│   └── agents_config/
└── localhost_9527/               # 默认 localhost 的数据
    ├── anp_users/
    ├── anp_users_hosted/
    └── agents_config/
```

## 配置文件结构

### 主配置文件 (unified_config.yaml)

```yaml
# ==========================================
# DID 格式配置
# ==========================================
did_config:
  # DID 方法和格式
  method: "wba"
  format_template: "did:{method}:{host}%3A{port}:{method}:{user_type}:{user_id}"
  
  # 路由配置
  router_prefix: "/wba"
  user_path_template: "/{method}/user/{user_id}/did.json"
  hostuser_path_template: "/{method}/hostuser/{user_id}/did.json"
  testuser_path_template: "/{method}/tests/{user_name}/did.json"
  
  # 用户类型配置
  user_types:
    user: "user"
    hostuser: "hostuser"
    test: "tests"
  
  # 用户创建权限
  creatable_user_types:
    - "user"
  
  # 主机和端口配置（单实例多域名）
  hosts:
    localhost: 9527
    "user.localhost": 9527
    "service.localhost": 9527
    "agent.localhost": 9527
    "test.localhost": 9527
    "127.0.0.1": 9527
    "agent-did.com": 443
  
  # 路径配置模板
  path_templates:
    user_did_path: "{APP_ROOT}/data_user/{host}_{port}/anp_users"
    user_hosted_path: "{APP_ROOT}/data_user/{host}_{port}/anp_users_hosted"
    agents_cfg_path: "{APP_ROOT}/data_user/{host}_{port}/agents_config"
  
  # URL 编码配置
  url_encoding:
    use_percent_encoding: false
    support_legacy_encoding: true
  
  # 不安全 DID 格式（用于测试和开发）
  insecure_patterns:
    - "did:wba:localhost:*"
    - "did:wba:127.0.0.1:*"
    - "did:wba:*:tests:*"
  
  # 解析配置
  parsing:
    strict_validation: true
    allow_insecure: true
    default_host: "localhost"
    default_port: 9527

# ==========================================
# 服务器配置
# ==========================================
anp_sdk:
  debug_mode: true
  host: "0.0.0.0"  # 监听所有接口
  port: 9527       # 单一端口
```

## 配置文件关系标准

### 当前关系分析

#### 1. 文件位置和作用

**agent_mappings.yaml (在 agents_config/ 目录下)**
- 位置：`data_user/localhost_9527/agents_config/agent_001/agent_mappings.yaml`
- 作用：Agent 的配置和 API 定义
- 内容：Agent 名称、DID、API 路由配置

**agent_cfg.yaml (在 anp_users/ 目录下)**
- 位置：`data_user/localhost_9527/anp_users/user_e0959abab6fc3c3d/agent_cfg.yaml`
- 作用：用户身份的基本信息
- 内容：用户名、唯一ID、DID、类型

#### 2. 当前存在的问题

**问题1：DID 格式不一致**
```yaml
# agent_mappings.yaml 中
did: "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"

# agent_cfg.yaml 中  
did: did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d
```
- agent_mappings.yaml 使用了 %3A 编码
- agent_cfg.yaml 没有使用编码

**问题2：文件结构不统一**
- 有些用户目录有 agent_cfg.yaml，有些没有
- agent_mappings.yaml 和对应的用户目录之间的关联不清晰

#### 3. 建议的标准关系

**统一的文件结构**
```
data_user/localhost_9527/
├── agents_config/
│   └── agent_001/
│       ├── agent_mappings.yaml    # Agent 配置和 API 定义
│       └── agent_register.py      # Agent 注册逻辑
└── anp_users/
    └── user_3ea884878ea5fbb1/
        ├── did_document.json       # DID 文档
        ├── agent_cfg.yaml          # Agent 身份信息
        ├── api_interface.yaml      # API 接口定义
        └── api_interface.json      # JSON-RPC 接口定义
```

### Agent 配置文件标准

#### agent_mappings.yaml (Agent 配置)

**独立DID Agent**
```yaml
# Agent 身份配置
name: "我的小本田"
description: "本田汽车相关的智能助手"
unique_id: "3ea884878ea5fbb1"
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"  # 标准格式，无编码
type: "user"

# 用户数据路径
user_data_path: "anp_users/user_3ea884878ea5fbb1"

# API 配置
api:
  - path: "/hello"
    method: "GET"
    handler: "hello_handler"
    description: "打招呼接口"
  - path: "/info"
    method: "POST"
    handler: "info_handler"
    description: "信息查询接口"

# 元数据
metadata:
  version: "1.0.0"
  created_at: "2024-01-01T00:00:00Z"
  tags: ["automotive", "assistant"]
```

**共享DID Agent**
```yaml
# Agent 身份配置
name: "铃木"
description: "anptool进行web搜索的共享身份"
unique_id: "5fea49e183c6c211"
# 注意：有share_did时不应该有did字段
type: "user"

# 共享DID配置
share_did:
  enabled: true
  shared_did: "did:wba:user.localhost:9527:wba:shared:search"
  path_prefix: "/suzuki"  # 路由时自动添加的前缀

# 用户数据路径
user_data_path: "anp_users/user_5fea49e183c6c211"

# API 配置 - 保持原有格式，不需要修改
api:
  - path: "/search"      # 原始路径，实际访问路径为 /suzuki/search
    method: "GET"
    handler: "web_search_handler"
    description: "网络搜索接口"
  - path: "/info"        # 原始路径，实际访问路径为 /suzuki/info
    method: "POST"
    handler: "info_retrieval_handler"
    description: "信息检索接口"

# 元数据
metadata:
  version: "1.0.0"
  created_at: "2024-01-01T00:00:00Z"
  tags: ["search", "web", "shared"]
  capabilities: ["web_search", "information_retrieval"]
```

#### agent_cfg.yaml (用户身份信息)

```yaml
# 用户身份基本信息
name: "我的小本田"
unique_id: "3ea884878ea5fbb1"
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"
type: "user"

# 关联的 Agent 配置
agent_config_path: "agents_config/agent_001"

# 能力描述
capabilities:
  - "vehicle_info"
  - "maintenance_advice"
  - "general_chat"

# 服务配置
service:
  host: "localhost"
  port: 9527
  endpoints:
    - "/hello"
    - "/info"
```

#### 关联关系

1. **通过DID关联**: agent_mappings.yaml (did: xxx) ←→ agent_cfg.yaml (did: xxx)
2. **通过路径关联**: 
   - agent_mappings.yaml 中的 `user_data_path: "anp_users/user_3ea884878ea5fbb1"`
   - agent_cfg.yaml 中的 `agent_config_path: "agents_config/agent_001"`

#### 共享DID配置规则

1. **有share_did时不应该有did字段**
2. **share_did里不写负责哪个路径，直接给每个agent定一个映射路径**
3. **加载时检查是否有冲突**

**方案A：以 agent_mappings.yaml 为主**
```yaml
# agents_config/agent_001/agent_mappings.yaml
name: "我的小本田"
description: "本田汽车相关的智能助手"
unique_id: "3ea884878ea5fbb1"
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"
type: "user"

# 用户数据路径
user_data_path: "anp_users/user_3ea884878ea5fbb1"

# API 配置
api:
  - path: "/hello"
    method: "GET"
    handler: "hello_handler"
  - path: "/info"
    method: "POST"
    handler: "info_handler"
```

**方案B：双向引用**
```yaml
# agent_mappings.yaml
name: "我的小本田"
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"
user_data_ref: "user_3ea884878ea5fbb1"

# agent_cfg.yaml  
name: "我的小本田"
did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"
agent_config_ref: "agent_001"
```

#### 推荐的实施步骤

1. **统一 DID 格式**
   ```yaml
   # 移除所有 %3A 编码，使用标准格式
   did: "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1"
   ```

2. **标准化文件结构**
   ```
   # 确保每个 agent 都有对应的用户目录
   agents_config/agent_001/ → anp_users/user_3ea884878ea5fbb1/
   ```

3. **更新绑定脚本**
   - 自动创建 agent_cfg.yaml
   - 维护 agent_mappings.yaml 和用户目录的一致性
   - 验证 DID 格式的统一性

4. **配置验证**
   ```python
   def validate_agent_user_binding(agent_config_dir, user_data_dir):
       """验证 Agent 配置和用户数据的一致性"""
       # 检查 DID 一致性
       # 检查文件存在性
       # 检查格式正确性
   ```

#### 总结

理想的关系应该是：
- agent_mappings.yaml 定义 Agent 的配置和能力
- agent_cfg.yaml 存储对应用户的身份信息
- 通过统一的 DID 格式建立关联
- 通过路径引用建立双向关联
- 使用绑定脚本维护一致性

这样可以确保 Agent 配置和用户身份数据的一致性，同时便于管理和维护。

### 配置类型定义

```python
# anp_sdk/config/config_types.py

class DidUserTypeConfig(Protocol):
    """DID 用户类型配置"""
    user: str
    hostuser: str
    test: str

class DidUrlEncodingConfig(Protocol):
    """DID URL 编码配置"""
    use_percent_encoding: bool
    support_legacy_encoding: bool

class DidPathTemplateConfig(Protocol):
    """DID 路径模板配置"""
    user_did_path: str
    user_hosted_path: str
    agents_cfg_path: str

class DidParsingConfig(Protocol):
    """DID 解析配置"""
    strict_validation: bool
    allow_insecure: bool
    default_host: str
    default_port: int

class DidConfig(Protocol):
    """DID 配置协议"""
    method: str
    format_template: str
    router_prefix: str
    user_path_template: str
    hostuser_path_template: str
    testuser_path_template: str
    user_types: DidUserTypeConfig
    creatable_user_types: List[str]
    hosts: Dict[str, int]
    path_templates: DidPathTemplateConfig
    url_encoding: DidUrlEncodingConfig
    insecure_patterns: List[str]
    parsing: DidParsingConfig
```

## DID 格式管理器

### 核心功能

DID 格式管理器 (`DidFormatManager`) 是整个系统的核心组件，负责：

1. **DID 格式化**: 根据配置模板生成标准 DID
2. **DID 解析**: 解析 DID 字符串为结构化数据
3. **身份管理**: 创建和验证 Agent 身份信息
4. **路径管理**: 根据主机和端口动态获取数据路径
5. **兼容性处理**: 支持旧格式的 %3A 编码

### 主要方法

```python
class DidFormatManager:
    def __init__(self):
        """初始化 DID 格式管理器"""
        
    def create_agent_identity(self, name: str, description: str, 
                            host: str, port: int, user_type: str = "user") -> Dict[str, str]:
        """创建 Agent 身份信息"""
        
    def format_did(self, host: str, port: int, user_type: str, unique_id: str) -> str:
        """格式化 DID"""
        
    def parse_did(self, did: str) -> Optional[Dict[str, str]]:
        """解析 DID"""
        
    def normalize_did(self, did: str) -> str:
        """标准化 DID - 移除 %3A 编码"""
        
    def can_create_user_type(self, user_type: str) -> bool:
        """检查用户类型是否可以创建"""
        
    def get_host_port_from_request(self, request) -> Tuple[str, int]:
        """从请求中获取主机和端口"""
        
    def get_data_paths(self, host: str, port: int) -> Dict[str, Path]:
        """获取指定主机端口的数据路径"""
        
    def validate_agent_identity(self, agent_identity: Dict) -> Tuple[bool, str]:
        """验证 Agent 身份信息"""
```

### 使用示例

```python
from anp_sdk.did.did_format_manager import get_did_format_manager

# 获取管理器实例
did_manager = get_did_format_manager()

# 创建 Agent 身份
suzuki_identity = did_manager.create_agent_identity(
    name="铃木",
    description="anptool进行web搜索的共享身份",
    host="user.localhost",
    port=9527
)

# 结果:
# {
#     'name': '铃木',
#     'description': 'anptool进行web搜索的共享身份',
#     'unique_id': '5fea49e183c6c211',
#     'did': 'did:wba:user.localhost:9527:wba:user:5fea49e183c6c211',
#     'type': 'user',
#     'host': 'user.localhost',
#     'port': '9527'
# }
```

## 本地 DNS 配置

### Linux/macOS 脚本 (setup_local_dns.sh)

```bash
#!/bin/bash

# ANP SDK 本地 DNS 配置脚本
# 用于设置多域名本地测试环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 域名列表
DOMAINS=(
    "user.localhost"
    "service.localhost"
    "agent.localhost"
    "test.localhost"
    "api.localhost"
    "admin.localhost"
)

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# 获取 hosts 文件路径
get_hosts_file() {
    local os=$(detect_os)
    case $os in
        "macos"|"linux")
            echo "/etc/hosts"
            ;;
        "windows")
            echo "C:/Windows/System32/drivers/etc/hosts"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# 检查是否有管理员权限
check_permissions() {
    local hosts_file=$(get_hosts_file)
    if [[ "$hosts_file" == "unknown" ]]; then
        echo -e "${RED}❌ 不支持的操作系统${NC}"
        exit 1
    fi
    
    if [[ ! -w "$hosts_file" ]]; then
        echo -e "${YELLOW}⚠️  需要管理员权限来修改 hosts 文件${NC}"
        echo -e "${BLUE}请使用以下命令重新运行:${NC}"
        
        local os=$(detect_os)
        case $os in
            "macos"|"linux")
                echo "sudo $0 $@"
                ;;
            "windows")
                echo "以管理员身份运行此脚本"
                ;;
        esac
        exit 1
    fi
}

# 添加域名到 hosts 文件
add_domains() {
    local hosts_file=$(get_hosts_file)
    local backup_file="${hosts_file}.anp_backup_$(date +%Y%m%d_%H%M%S)"
    
    echo -e "${BLUE}🔧 配置本地 DNS...${NC}"
    
    # 备份原始 hosts 文件
    echo -e "${YELLOW}📋 备份原始 hosts 文件到: $backup_file${NC}"
    cp "$hosts_file" "$backup_file"
    
    # 添加 ANP SDK 标记
    echo "" >> "$hosts_file"
    echo "# ANP SDK Local DNS Configuration - Start" >> "$hosts_file"
    echo "# Generated on $(date)" >> "$hosts_file"
    
    # 添加域名
    for domain in "${DOMAINS[@]}"; do
        # 检查域名是否已存在
        if grep -q "127.0.0.1[[:space:]]*$domain" "$hosts_file"; then
            echo -e "${YELLOW}⚠️  域名 $domain 已存在，跳过${NC}"
        else
            echo "127.0.0.1 $domain" >> "$hosts_file"
            echo -e "${GREEN}✅ 添加域名: $domain${NC}"
        fi
    done
    
    echo "# ANP SDK Local DNS Configuration - End" >> "$hosts_file"
    echo "" >> "$hosts_file"
    
    echo -e "${GREEN}🎉 本地 DNS 配置完成！${NC}"
}

# 移除域名从 hosts 文件
remove_domains() {
    local hosts_file=$(get_hosts_file)
    local temp_file=$(mktemp)
    
    echo -e "${BLUE}🧹 清理本地 DNS 配置...${NC}"
    
    # 移除 ANP SDK 相关的行
    sed '/# ANP SDK Local DNS Configuration - Start/,/# ANP SDK Local DNS Configuration - End/d' "$hosts_file" > "$temp_file"
    
    # 移除单独的域名行（如果存在）
    for domain in "${DOMAINS[@]}"; do
        sed -i.bak "/127\.0\.0\.1[[:space:]]*$domain/d" "$temp_file"
    done
    
    # 替换原文件
    mv "$temp_file" "$hosts_file"
    
    echo -e "${GREEN}✅ 本地 DNS 配置已清理${NC}"
}

# 验证配置
verify_configuration() {
    echo -e "${BLUE}🔍 验证 DNS 配置...${NC}"
    
    for domain in "${DOMAINS[@]}"; do
        if ping -c 1 -W 1000 "$domain" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $domain -> 127.0.0.1${NC}"
        else
            echo -e "${RED}❌ $domain 解析失败${NC}"
        fi
    done
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}ANP SDK 本地 DNS 配置脚本${NC}"
    echo ""
    echo "用法:"
    echo "  $0 setup    - 配置本地 DNS"
    echo "  $0 remove   - 移除本地 DNS 配置"
    echo "  $0 verify   - 验证 DNS 配置"
    echo "  $0 list     - 列出配置的域名"
    echo "  $0 help     - 显示帮助信息"
    echo ""
    echo "配置的域名:"
    for domain in "${DOMAINS[@]}"; do
        echo "  - $domain"
    done
}

# 列出域名
list_domains() {
    echo -e "${BLUE}📋 ANP SDK 配置的域名:${NC}"
    for domain in "${DOMAINS[@]}"; do
        echo -e "${GREEN}  ✓ $domain${NC}"
    done
    
    echo ""
    echo -e "${BLUE}🌐 测试 URL:${NC}"
    for domain in "${DOMAINS[@]}"; do
        echo -e "${YELLOW}  http://$domain:9527${NC}"
    done
}

# 主函数
main() {
    case "${1:-help}" in
        "setup")
            check_permissions "$@"
            add_domains
            echo ""
            echo -e "${BLUE}📋 后续步骤:${NC}"
            echo -e "${YELLOW}1. 启动 ANP SDK 服务: python -m anp_open_sdk_framework.server --host 0.0.0.0 --port 9527${NC}"
            echo -e "${YELLOW}2. 验证配置: $0 verify${NC}"
            echo -e "${YELLOW}3. 访问测试: curl http://user.localhost:9527/wba/user/test/did.json${NC}"
            ;;
        "remove")
            check_permissions "$@"
            remove_domains
            ;;
        "verify")
            verify_configuration
            ;;
        "list")
            list_domains
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
```

### Windows PowerShell 脚本 (setup_local_dns.ps1)

```powershell
# ANP SDK 本地 DNS 配置脚本 (Windows PowerShell)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "remove", "verify", "list", "help")]
    [string]$Action = "help"
)

# 域名列表
$Domains = @(
    "user.localhost",
    "service.localhost", 
    "agent.localhost",
    "test.localhost",
    "api.localhost",
    "admin.localhost"
)

$HostsFile = "C:\Windows\System32\drivers\etc\hosts"

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 添加域名到 hosts 文件
function Add-Domains {
    Write-Host "🔧 配置本地 DNS..." -ForegroundColor Blue
    
    # 备份原始文件
    $BackupFile = "$HostsFile.anp_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "📋 备份原始 hosts 文件到: $BackupFile" -ForegroundColor Yellow
    Copy-Item $HostsFile $BackupFile
    
    # 读取现有内容
    $HostsContent = Get-Content $HostsFile
    
    # 添加标记和域名
    $NewContent = @()
    $NewContent += $HostsContent
    $NewContent += ""
    $NewContent += "# ANP SDK Local DNS Configuration - Start"
    $NewContent += "# Generated on $(Get-Date)"
    
    foreach ($Domain in $Domains) {
        if ($HostsContent -match "127\.0\.0\.1\s+$Domain") {
            Write-Host "⚠️  域名 $Domain 已存在，跳过" -ForegroundColor Yellow
        } else {
            $NewContent += "127.0.0.1 $Domain"
            Write-Host "✅ 添加域名: $Domain" -ForegroundColor Green
        }
    }
    
    $NewContent += "# ANP SDK Local DNS Configuration - End"
    $NewContent += ""
    
    # 写入文件
    $NewContent | Out-File -FilePath $HostsFile -Encoding ASCII
    
    Write-Host "🎉 本地 DNS 配置完成！" -ForegroundColor Green
}

# 移除域名配置
function Remove-Domains {
    Write-Host "🧹 清理本地 DNS 配置..." -ForegroundColor Blue
    
    $HostsContent = Get-Content $HostsFile
    $NewContent = @()
    $SkipLines = $false
    
    foreach ($Line in $HostsContent) {
        if ($Line -match "# ANP SDK Local DNS Configuration - Start") {
            $SkipLines = $true
            continue
        }
        if ($Line -match "# ANP SDK Local DNS Configuration - End") {
            $SkipLines = $false
            continue
        }
        if (-not $SkipLines) {
            # 检查是否是单独的域名行
            $IsDomainLine = $false
            foreach ($Domain in $Domains) {
                if ($Line -match "127\.0\.0\.1\s+$Domain") {
                    $IsDomainLine = $true
                    break
                }
            }
            if (-not $IsDomainLine) {
                $NewContent += $Line
            }
        }
    }
    
    $NewContent | Out-File -FilePath $HostsFile -Encoding ASCII
    Write-Host "✅ 本地 DNS 配置已清理" -ForegroundColor Green
}

# 验证配置
function Test-Configuration {
    Write-Host "🔍 验证 DNS 配置..." -ForegroundColor Blue
    
    foreach ($Domain in $Domains) {
        try {
            $Result = Test-Connection -ComputerName $Domain -Count 1 -Quiet
            if ($Result) {
                Write-Host "✅ $Domain -> 127.0.0.1" -ForegroundColor Green
            } else {
                Write-Host "❌ $Domain 解析失败" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ $Domain 解析失败" -ForegroundColor Red
        }
    }
}

# 列出域名
function Show-Domains {
    Write-Host "📋 ANP SDK 配置的域名:" -ForegroundColor Blue
    foreach ($Domain in $Domains) {
        Write-Host "  ✓ $Domain" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🌐 测试 URL:" -ForegroundColor Blue
    foreach ($Domain in $Domains) {
        Write-Host "  http://$Domain:9527" -ForegroundColor Yellow
    }
}

# 显示帮助
function Show-Help {
    Write-Host "ANP SDK 本地 DNS 配置脚本" -ForegroundColor Blue
    Write-Host ""
    Write-Host "用法:"
    Write-Host "  .\setup_local_dns.ps1 -Action setup    - 配置本地 DNS"
    Write-Host "  .\setup_local_dns.ps1 -Action remove   - 移除本地 DNS 配置"
    Write-Host "  .\setup_local_dns.ps1 -Action verify   - 验证 DNS 配置"
    Write-Host "  .\setup_local_dns.ps1 -Action list     - 列出配置的域名"
    Write-Host "  .\setup_local_dns.ps1 -Action help     - 显示帮助信息"
    Write-Host ""
    Write-Host "配置的域名:"
    foreach ($Domain in $Domains) {
        Write-Host "  - $Domain"
    }
}

# 主逻辑
switch ($Action) {
    "setup" {
        if (-not (Test-Administrator)) {
            Write-Host "❌ 需要管理员权限来修改 hosts 文件" -ForegroundColor Red
            Write-Host "请以管理员身份运行 PowerShell" -ForegroundColor Yellow
            exit 1
        }
        Add-Domains
        Write-Host ""
        Write-Host "📋 后续步骤:" -ForegroundColor Blue
        Write-Host "1. 启动 ANP SDK 服务: python -m anp_open_sdk_framework.server --host 0.0.0.0 --port 9527" -ForegroundColor Yellow
        Write-Host "2. 验证配置: .\setup_local_dns.ps1 -Action verify" -ForegroundColor Yellow
        Write-Host "3. 访问测试: curl http://user.localhost:9527/wba/user/test/did.json" -ForegroundColor Yellow
    }
    "remove" {
        if (-not (Test-Administrator)) {
            Write-Host "❌ 需要管理员权限来修改 hosts 文件" -ForegroundColor Red
            Write-Host "请以管理员身份运行 PowerShell" -ForegroundColor Yellow
            exit 1
        }
        Remove-Domains
    }
    "verify" {
        Test-Configuration
    }
    "list" {
        Show-Domains
    }
    default {
        Show-Help
    }
}
```

## 开发计划

### 修正后的开发重点：保留%3A编码 + 增强多域名支持

基于对%3A编码设计价值的重新认识，开发计划调整为：
- **保留%3A编码**作为设计特性
- **重点实现多域名支持**
- **优化现有DID解析器**
- **完善配置管理系统**

### 阶段一：多域名路由系统 (Week 1-2)

#### 1.1 域名管理器开发
- **目标**: 实现基于Host头的多域名路由
- **交付物**:
  - `anp_open_sdk/domain/domain_manager.py`
  - 域名配置管理
  - 数据路径动态分配

#### 1.2 路由系统增强
- **目标**: 支持多域名请求分发
- **交付物**:
  - 更新 `router_did.py` 支持域名路由
  - 更新 `router_publisher.py` 支持多域名
  - Host头解析和验证逻辑

#### 1.3 配置系统扩展
- **目标**: 支持多域名配置管理
- **交付物**:
  - 更新 `unified_config.yaml` 模板
  - 更新 `config_types.py` 添加域名配置
  - 域名配置验证逻辑

### 阶段二：DID解析器优化 (Week 3-4)

#### 2.1 DID格式管理器重构
- **目标**: 优化%3A编码的解析逻辑
- **交付物**:
  - `anp_open_sdk/did/did_format_manager.py`
  - 增强的%3A编码解析器
  - 更好的错误处理和验证

#### 2.2 解析器性能优化
- **目标**: 提升DID解析性能和健壮性
- **交付物**:
  - 解析缓存机制
  - 批量解析支持
  - 性能基准测试

#### 2.3 兼容性处理
- **目标**: 确保现有DID格式完全兼容
- **交付物**:
  - 格式验证工具
  - 兼容性测试套件
  - 迁移指南（如需要）

### 阶段三：本地DNS和环境配置 (Week 5-6)

#### 3.1 本地DNS配置工具
- **目标**: 提供本地多域名测试环境
- **交付物**:
  - `scripts/setup_local_dns.sh` (Linux/macOS)
  - `scripts/setup_local_dns.ps1` (Windows)
  - 自动化域名配置工具

#### 3.2 数据路径管理
- **目标**: 实现基于域名的数据路径分离
- **交付物**:
  - 动态数据路径解析
  - 多域名数据目录结构
  - 路径冲突检测和解决

#### 3.3 环境管理工具
- **目标**: 简化多域名环境管理
- **交付物**:
  - 环境设置脚本
  - 配置生成工具
  - 状态检查和诊断工具

### 阶段四：测试和文档完善 (Week 7-8)

#### 4.1 集成测试
- **目标**: 确保多域名系统稳定性
- **交付物**:
  - 多域名端到端测试
  - DID解析性能测试
  - 兼容性回归测试

#### 4.2 文档和最佳实践
- **目标**: 提供完整的使用文档
- **交付物**:
  - %3A编码设计文档
  - 多域名配置指南
  - 故障排除手册

#### 4.3 示例和工具
- **目标**: 提供实际使用示例
- **交付物**:
  - 多域名示例应用
  - DID格式最佳实践
  - 开发工具和脚本

## 实施路线图

### 里程碑

| 里程碑 | 时间 | 主要交付物 | 成功标准 |
|--------|------|------------|----------|
| M1: 基础设施完成 | Week 2 | DID 格式管理器、配置系统 | 单元测试通过，基本功能可用 |
| M2: 身份管理完成 | Week 4 | Agent 身份管理、用户绑定 | 身份创建和验证功能完整 |
| M3: 多域名支持完成 | Week 6 | 域名路由、本地 DNS 配置 | 多域名环境正常运行 |
| M4: 系统发布就绪 | Week 8 | 完整测试、文档、示例 | 生产环境部署就绪 |

### 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 配置复杂性 | 高 | 中 | 提供自动化配置工具 |
| 兼容性问题 | 中 | 高 | 保持向后兼容，提供迁移工具 |
| 性能影响 | 中 | 低 | 性能测试，优化关键路径 |
| 文档不足 | 低 | 中 | 并行开发文档，示例驱动 |

### 资源需求

- **开发人员**: 2-3 人
- **测试人员**: 1 人
- **文档人员**: 1 人
- **基础设施**: 本地开发环境，测试服务器

## 使用指南

### 快速开始

#### 1. 环境设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd anp-sdk

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置本地 DNS (Linux/macOS)
sudo ./scripts/setup_local_dns.sh setup

# Windows (以管理员身份运行 PowerShell)
.\scripts\setup_local_dns.ps1 -Action setup
```

#### 2. 启动服务

```bash
# 启动单个实例，监听所有接口
python -m anp_server_framework.anp_server --host 0.0.0.0 --port 9527
```

#### 3. 验证配置

```bash
# 验证 DNS 解析
./scripts/setup_local_dns.sh verify

# 测试不同域名访问
curl http://user.localhost:9527/wba/user/test123/did.json
curl http://service.localhost:9527/wba/user/test456/did.json
curl http://agent.localhost:9527/wba/user/test789/did.json
```

#### 4. 创建 Agent 身份

```bash
# 运行绑定脚本
python scripts/agent_user_binding.py

# 交互式创建身份
# 输入 Agent 名称和描述，系统自动生成 DID
```

### 高级配置

#### 自定义域名

```yaml
# unified_config.yaml
did_config:
  hosts:
    "my-custom.localhost": 9527
    "another-domain.local": 9528
```

#### 生产环境配置

```yaml
# unified_config.yaml
did_config:
  hosts:
    "api.example.com": 443
    "service.example.com": 443
  parsing:
    strict_validation: true
    allow_insecure: false
```

### API 使用示例

#### 创建 DID

```python
from anp_sdk.did.did_format_manager import get_did_format_manager

did_manager = get_did_format_manager()

# 创建用户身份
identity = did_manager.create_agent_identity(
    name="智能助手",
    description="通用智能助手",
    host="user.localhost",
    port=9527
)

print(f"DID: {identity['did']}")
```

#### 解析 DID

```python
# 解析 DID
did = "did:wba:user.localhost:9527:wba:user:abc123"
parsed = did_manager.parse_did(did)

print(f"Host: {parsed['host']}")
print(f"Port: {parsed['port']}")
print(f"User Type: {parsed['user_type']}")
print(f"User ID: {parsed['user_id']}")
```

#### 获取数据路径

```python
# 获取数据路径
paths = did_manager.get_data_paths("user.localhost", 9527)
print(f"用户数据路径: {paths['user_did_path']}")
print(f"配置路径: {paths['agents_cfg_path']}")
```

## 故障排除

### 常见问题

#### 1. 域名解析失败

**症状**: 无法访问 `user.localhost` 等域名

**解决方案**:
```bash
# 检查 hosts 文件
cat /etc/hosts | grep localhost

# 清除 DNS 缓存 (macOS)
sudo dscacheutil -flushcache

# 清除 DNS 缓存 (Windows)
ipconfig /flushdns

# 重新配置 DNS
sudo ./scripts/setup_local_dns.sh setup
```

#### 2. 权限错误

**症状**: 无法修改 hosts 文件

**解决方案**:
```bash
# 确保以管理员身份运行
sudo ./scripts/setup_local_dns.sh setup

# Windows: 以管理员身份运行 PowerShell
```

#### 3. 端口冲突

**症状**: 服务无法启动，端口被占用

**解决方案**:
```bash
# 检查端口占用
lsof -i :9527
netstat -an | grep 9527

# 杀死占用进程
kill -9 <PID>

# 或使用其他端口
python -m anp_server_framework.anp_server --host 0.0.0.0 --port 9528
```

#### 4. DID 格式错误

**症状**: DID 解析失败或格式不正确

**解决方案**:

```python
# 验证 DID 格式
from anp_sdk.did.did_format_manager import get_did_format_manager

did_manager = get_did_format_manager()
did = "your-did-here"

# 尝试解析
parsed = did_manager.parse_did(did)
if not parsed:
    print("DID 格式错误")
    # 使用标准化功能
    normalized = did_manager.normalize_did(did)
    print(f"标准化后: {normalized}")
```

#### 5. 配置文件错误

**症状**: 服务启动失败，配置加载错误

**解决方案**:
```bash
# 验证 YAML 语法
python -c "import yaml; yaml.safe_load(open('unified_config.yaml'))"

# 检查配置路径
python -c "
from anp_open_sdk.config import UnifiedConfig
config = UnifiedConfig()
print('配置加载成功')
"
```

### 调试技巧

#### 启用调试模式

```yaml
# unified_config.yaml
anp_sdk:
  debug_mode: true

# 或环境变量
export ANP_DEBUG=true
```

#### 查看详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启动服务
python -m anp_open_sdk_framework.server --debug
```

#### 测试 DID 功能

```python
# 测试脚本
from anp_sdk.did.did_format_manager import get_did_format_manager


def test_did_functionality():
    did_manager = get_did_format_manager()

    # 测试创建
    identity = did_manager.create_agent_identity(
        "测试", "测试身份", "localhost", 9527
    )
    print(f"✅ 创建成功: {identity['did']}")

    # 测试解析
    parsed = did_manager.parse_did(identity['did'])
    print(f"✅ 解析成功: {parsed}")

    # 测试验证
    valid, msg = did_manager.validate_agent_identity(identity)
    print(f"✅ 验证结果: {valid} - {msg}")


if __name__ == "__main__":
    test_did_functionality()
```

### 性能优化

#### 缓存配置

```python
# 启用 DID 解析缓存
from functools import lru_cache

class DidFormatManager:
    @lru_cache(maxsize=1000)
    def parse_did(self, did: str):
        # 解析逻辑
        pass
```

#### 批量操作

```python
# 批量创建身份
identities = []
for i in range(100):
    identity = did_manager.create_agent_identity(
        f"Agent-{i}", f"测试身份-{i}", "localhost", 9527
    )
    identities.append(identity)
```

## 总结

本开发计划提供了 ANP SDK DID 格式统一和多域名体系的完整实施方案。通过分阶段的开发方式，确保系统的稳定性和可维护性。主要特点包括：

1. **统一的 DID 格式**: 标准化的 DID 格式，易于解析和管理
2. **多域名支持**: 单实例支持多个域名，简化部署
3. **灵活的配置**: 通过配置文件管理所有 DID 相关设置
4. **向后兼容**: 支持旧格式的平滑迁移
5. **完整的工具链**: 从开发到部署的完整工具支持

通过这个计划的实施，ANP SDK 将具备更强的扩展性和易用性，为未来的发展奠定坚实的基础。
