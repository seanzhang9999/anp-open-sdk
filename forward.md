好的，我来提供具体的代码实现：

## 1. 创建 anp_server_framework/framework_server.py

```python
# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import asyncio
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from anp_sdk.config import get_global_config
from anp_server_framework.router_agent import router as agent_router

logger = logging.getLogger(__name__)

class FrameworkServer:
    """简化的Framework Server - 专注于Agent路由处理"""
    
    def __init__(self, host="localhost", port=9528):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ANP Framework Server",
            description="ANP Framework Server - Agent路由处理",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        # 包含Agent路由
        self.app.include_router(agent_router)
        
        # 健康检查
        @self.app.get("/", tags=["status"])
        async def root():
            return {
                "status": "running",
                "service": "ANP Framework Server",
                "version": "0.1.0",
                "description": "简化的Agent路由处理服务"
            }
        
        @self.app.get("/health", tags=["status"])
        async def health():
            return {"status": "healthy"}
    
    def run(self):
        """启动服务器"""
        import uvicorn
        logger.info(f"🚀 启动Framework Server: http://{self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)

if __name__ == "__main__":
    # 从配置获取端口
    config = get_global_config()
    framework_url = getattr(config.anp_sdk, "framework_server_url", "http://localhost:9528")
    port = int(framework_url.split(":")[-1])
    
    server = FrameworkServer(port=port)
    server.run()
```

## 3. 创建 anp_server_framework/router_agent.py

```python
# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import logging
from fastapi import Request, APIRouter
from typing import Dict, Any
from datetime import datetime
import time

from anp_server_framework.agent import Agent
from anp_server_framework.agent_manager import AgentManager

logger = logging.getLogger(__name__)

# 导入原有的AgentRouter类（核心逻辑保持一致）
from anp_server.router.router_agent import (
    AgentSearchRecord, AgentContactBook, SessionRecord, 
    ApiCallRecord, AgentRouter
)

router = APIRouter(prefix="/agent", tags=["agent"])

# 创建全局路由器实例
framework_router = AgentRouter()

@router.post("/api/{did}/{subpath:path}")
async def handle_agent_api(did: str, subpath: str, request: Request):
    """Framework Server的API处理 - 直接本地处理，无转发"""
    
    # 获取请求数据
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    
    # 构造请求数据
    request_data = {
        **data,
        "type": "api_call",
        "path": f"/{subpath}",
        "req_did": request.query_params.get("req_did", "framework_caller")
    }
    
    try:
        logger.debug(f"🔧 Framework Server处理API请求: {did}/{subpath}")
        
        # 直接使用本地路由处理
        result = await framework_router.route_request(
            request_data["req_did"],
            did,
            request_data,
            request
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Framework Server处理API请求失败: {e}")
        return {"status": "error", "message": f"处理请求失败: {str(e)}"}

@router.post("/api/{did}/message/post")
async def handle_agent_message(did: str, request: Request):
    """Framework Server的消息处理 - 直接本地处理，无转发"""
    
    # 获取请求数据
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    
    # 构造请求数据
    request_data = {
        **data,
        "type": "message",
        "req_did": request.query_params.get("req_did", "framework_caller")
    }
    
    try:
        logger.debug(f"🔧 Framework Server处理消息: {did}")
        
        # 直接使用本地路由处理
        result = await framework_router.route_request(
            request_data["req_did"],
            did,
            request_data,
            request
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Framework Server处理消息失败: {e}")
        return {"anp_result": {"status": "error", "message": f"处理消息失败: {str(e)}"}}

# 提供路由器访问接口，供外部注册Agent使用
def get_framework_router():
    """获取Framework Server的路由器实例"""
    return framework_router
```

## 4. 创建启动脚本 start_framework_server.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANP Framework Server 启动脚本
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from anp_sdk.config import get_global_config
from anp_server_framework.framework_server import FrameworkServer
from anp_server_framework.agent_manager import LocalAgentManager

logger = logging.getLogger(__name__)

async def load_agents_to_framework():
    """加载Agent到Framework Server"""
    try:
        config = get_global_config()
        agents_cfg_path = getattr(config.multi_agent_mode, "agents_cfg_path", None)
        
        if not agents_cfg_path:
            logger.warning("未配置agents_cfg_path，跳过Agent加载")
            return
        
        agents_cfg_path = config.resolve_path(agents_cfg_path)
        if not os.path.exists(agents_cfg_path):
            logger.warning(f"Agent配置路径不存在: {agents_cfg_path}")
            return
        
        logger.info(f"🔍 开始从 {agents_cfg_path} 加载Agent...")
        
        # 获取Framework路由器
        from anp_server_framework.router_agent import get_framework_router
        framework_router = get_framework_router()
        
        # 遍历加载Agent
        for agent_dir in os.listdir(agents_cfg_path):
            agent_path = os.path.join(agents_cfg_path, agent_dir)
            if not os.path.isdir(agent_path):
                continue
            
            yaml_path = os.path.join(agent_path, "agent_mappings.yaml")
            if not os.path.exists(yaml_path):
                continue
            
            try:
                logger.info(f"📦 加载Agent: {agent_dir}")
                agent, handler_module, share_did_config = await LocalAgentManager.load_agent_from_module(yaml_path)
                
                if agent:
                    # 注册到Framework路由器
                    framework_router.register_agent_with_domain(agent)
                    logger.info(f"✅ Agent注册成功: {agent.name} (DID: {agent.anp_user.id})")
                    
                    # 如果有initialize_agent，调用它
                    if handler_module and hasattr(handler_module, "initialize_agent"):
                        await handler_module.initialize_agent(agent)
                        logger.info(f"🔧 Agent初始化完成: {agent.name}")
                
            except Exception as e:
                logger.error(f"❌ 加载Agent失败 {agent_dir}: {e}")
                continue
        
        logger.info("🎉 Agent加载完成")
        
    except Exception as e:
        logger.error(f"❌ 加载Agent过程出错: {e}")

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 获取配置
        config = get_global_config()
        framework_url = getattr(config.anp_sdk, "framework_server_url", "http://localhost:9528")
        port = int(framework_url.split(":")[-1])
        
        logger.info("🚀 启动ANP Framework Server...")
        logger.info(f"📍 服务地址: http://localhost:{port}")
        
        # 异步加载Agent
        asyncio.run(load_agents_to_framework())
        
        # 启动服务器
        server = FrameworkServer(port=port)
        server.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Framework Server已停止")
    except Exception as e:
        logger.error(f"❌ Framework Server启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 使用方法

1. __启动Framework Server__:

```bash
python start_framework_server.py
```

2. __启动主服务器并启用转发__: 修改配置文件中的 `use_framework_server: true`

3. __测试转发__:

```bash
# 测试API调用
curl -X POST "http://localhost:9527/agent/api/did:wba:localhost%3A9527:wba:user:xxx/test" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

这样就实现了你要求的功能：两边都有router_agent.py，主服务器可以转发到Framework Server，处理逻辑完全等效，且Framework Server尽可能简化。

需要我创建这些文件吗？请告诉我是否需要调整什么地方。



是的，完全可以实现！而且你的想法很好，通过 `anp_server/router/router_agent.py` 来中转 WebSocket 和 HTTP SSE/Streamable 连接是一个很好的架构设计。

## WebSocket 和 SSE 中转的可行性分析

### 1. __技术可行性__

✅ __完全可行__ - FastAPI 和 aiohttp 都原生支持：

- WebSocket 代理转发
- HTTP SSE (Server-Sent Events) 流式响应代理
- 异步流数据中转

### 2. __架构优势__

- 🔄 __统一入口__: 所有连接都通过 anp_server 统一管理
- 🛡️ __认证中心化__: 在 anp_server 层统一处理认证
- 📊 __监控集中__: 连接状态、流量监控都在一处
- 🔧 __配置灵活__: 可以动态切换本地/远程处理

### 3. __实现方案__

我建议在现有的 `router_agent.py` 基础上添加以下路由：

#### WebSocket 中转路由

```python
@router.websocket("/ws/{did}/{subpath:path}")
async def websocket_proxy(websocket: WebSocket, did: str, subpath: str):
    """WebSocket代理 - 中转到framework_server或本地处理"""
    
    config = get_global_config()
    use_framework_server = getattr(config.anp_sdk, "use_framework_server", False)
    framework_server_url = getattr(config.anp_sdk, "framework_server_url", "http://localhost:9528")
    
    if use_framework_server:
        # 转发到framework_server的WebSocket
        await proxy_websocket_to_framework(websocket, did, subpath, framework_server_url)
    else:
        # 本地WebSocket处理
        await handle_local_websocket(websocket, did, subpath)
```

#### SSE 中转路由

```python
@router.get("/stream/{did}/{subpath:path}")
async def sse_proxy(did: str, subpath: str, request: Request):
    """SSE流式响应代理"""
    
    config = get_global_config()
    use_framework_server = getattr(config.anp_sdk, "use_framework_server", False)
    framework_server_url = getattr(config.anp_sdk, "framework_server_url", "http://localhost:9528")
    
    if use_framework_server:
        # 转发到framework_server并流式返回
        return await proxy_sse_to_framework(did, subpath, request, framework_server_url)
    else:
        # 本地SSE处理
        return await handle_local_sse(did, subpath, request)
```

### 4. __关键技术点__

#### WebSocket 代理实现

```python
async def proxy_websocket_to_framework(websocket: WebSocket, did: str, subpath: str, framework_url: str):
    await websocket.accept()
    
    # 建立到framework_server的WebSocket连接
    framework_ws_url = framework_url.replace("http://", "ws://") + f"/agent/ws/{did}/{subpath}"
    
    async with websockets.connect(framework_ws_url) as framework_ws:
        # 双向数据转发
        await asyncio.gather(
            forward_client_to_framework(websocket, framework_ws),
            forward_framework_to_client(framework_ws, websocket)
        )
```

#### SSE 流式代理实现

```python
async def proxy_sse_to_framework(did: str, subpath: str, request: Request, framework_url: str):
    target_url = f"{framework_url}/agent/stream/{did}/{subpath}"
    
    async def event_stream():
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, params=dict(request.query_params)) as response:
                async for chunk in response.content.iter_chunked(1024):
                    yield chunk.decode('utf-8')
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 5. __安全考虑__

由于你提到不用考虑端到端安全（同一方），我们可以：

- 直接转发 WebSocket 消息
- 保持连接状态同步
- 简化认证流程（在 anp_server 层统一处理）

### 6. __性能优化__

- 🚀 __连接池__: 复用到 framework_server 的连接
- 📦 __缓冲优化__: 合理的缓冲区大小
- ⚡ __异步处理__: 全异步避免阻塞

这样的设计让 `anp_server` 成为一个完整的代理层，可以无缝地在本地处理和远程转发之间切换，同时保持 API 的一致性。
