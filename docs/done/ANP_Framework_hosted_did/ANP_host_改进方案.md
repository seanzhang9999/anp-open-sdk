# ANP SDK 托管DID改进方案

**项目**: ANP Open SDK  
**功能**: 托管DID申请流程轻量化改进  
**设计日期**: 2025年1月11日  
**状态**: 📋 设计完成，待实施  

## 📋 项目概述

本文档描述了ANP SDK中托管DID申请流程的改进方案，将原有的邮件申请方式改进为更轻量、更直接的HTTP API方式，同时保持与现有系统的完全兼容性。

## 🎯 改进目标

### 现有问题分析
1. **邮件复杂性**: 邮件配置复杂，容易让用户困扰
2. **实时性差**: 邮件方式无法提供即时反馈
3. **依赖性强**: 需要邮件服务的额外配置和维护
4. **调试困难**: 邮件流程难以调试和监控

### 改进目标
1. **轻量化**: 使用HTTP API替代邮件，减少依赖
2. **实时性**: 提供即时的申请反馈和状态查询
3. **生产就绪**: 支持异步处理和复杂业务流程
4. **向后兼容**: 保持现有代码和目录结构不变

## 🚀 核心设计理念

### 两步异步流程
```
客户端申请 → 服务器处理 → 发布结果 → 客户端检查
   ↓           ↓           ↓         ↓
request    处理队列     结果存储    check轮询
```

### 设计优势
- **异步处理**: 申请和检查分离，支持长时间处理
- **生产就绪**: 支持复杂的业务处理流程
- **可扩展**: 队列和结果管理支持高并发
- **可监控**: 完整的状态跟踪和日志
- **容错性**: 支持重试和错误恢复
- **轮询友好**: 客户端可以定期检查结果

## 📁 目录结构设计

### 现有目录结构（保持不变）

```
data_user/
├── user_localhost_9527/                    # 客户端A
│   ├── anp_users/
│   │   ├── user_abc123/                    # 客户端A自己的DID
│   │   │   └── did_document.json
│   │   └── user_hosted_open_localhost_9527_f2f7744eab8d1ca9/  # 从open.localhost收到的托管DID
│   │       └── [create_hosted_did创建的文件]
│   └── agents_config/
├── open_localhost_9527/                    # 托管服务器
│   ├── anp_users_hosted/                   # 服务器创建的托管DID
│   │   └── user_f2f7744eab8d1ca9/
│   │       ├── did_document_request.json   # 原始申请
│   │       └── did_document.json           # 创建的托管DID
│   ├── hosted_did_queue/                   # 新增：HTTP申请队列
│   │   ├── pending/
│   │   ├── processing/
│   │   ├── completed/
│   │   └── failed/
│   ├── hosted_did_results/                 # 新增：HTTP结果存储
│   │   ├── pending/
│   │   └── acknowledged/
│   └── agents_config/
└── service_localhost_9527/                 # 另一个客户端B
    ├── anp_users/
    │   ├── user_def456/                    # 客户端B自己的DID
    │   └── user_hosted_open_localhost_9527_xyz789/  # 从open.localhost收到的托管DID
    └── agents_config/
```

### 关键设计原则
1. **保持现有结构**: 完全不改变现有的 `anp_users/` 和 `anp_users_hosted/` 结构
2. **兼容现有方法**: 继续使用现有的 `create_hosted_did` 方法
3. **新增队列目录**: 只在托管服务器端新增队列和结果管理目录
4. **客户端无变化**: 客户端的目录结构完全不变

## 🔧 技术实现方案

### 1. 基于现有结构的HTTP接口增强

#### 现有架构优势分析
✅ **已完成的重构成果**:
- `router_host.py`: 专门负责托管DID的Web接口，已支持多域名
- `anp_server_hoster.py`: 独立的托管业务逻辑，包含完整的DIDHostManager
- 清晰的职责分离和模块化设计

#### router_host.py 增强方案

```python
# anp_server_framework/anp_server/router/router_host.py
# 在现有文件基础上添加HTTP申请接口

from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import uuid


# 添加请求模型
class HostedDIDRequest(BaseModel):
  """托管DID申请请求"""
  did_document: Dict[str, Any]
  requester_did: str
  callback_info: Optional[Dict[str, Any]] = None


class HostedDIDRequestResponse(BaseModel):
  """托管DID申请响应"""
  success: bool
  request_id: str = None
  message: str = None
  estimated_processing_time: Optional[int] = None


# 在现有router基础上添加新接口
@router.post("/wba/hosted-did/request", response_model=HostedDIDRequestResponse)
async def submit_hosted_did_request(request: Request, hosted_request: HostedDIDRequest):
  """
  第一步：提交托管DID申请（HTTP方式）
  
  复用现有的域名管理和验证逻辑
  """
  try:
    # 复用现有的域名管理逻辑
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 复用现有的域名验证逻辑
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
      logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
      raise HTTPException(status_code=403, detail=error_msg)

    # 确保域名目录存在
    domain_manager.ensure_domain_directories(host, port)

    # 基本验证
    if not hosted_request.did_document or not hosted_request.requester_did:
      raise HTTPException(status_code=400, detail="DID文档和申请者DID不能为空")

    if not hosted_request.requester_did.startswith('did:wba:'):
      raise HTTPException(status_code=400, detail="申请者DID格式不正确")

    # 生成申请ID
    request_id = str(uuid.uuid4())

    # 使用队列管理器处理申请
    from anp_server import HostedDIDQueueManager
    queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
    success = await queue_manager.add_request(request_id, hosted_request)

    if success:
      logger.info(f"收到托管DID申请: {request_id}, 申请者: {hosted_request.requester_did}")
      return HostedDIDRequestResponse(
        success=True,
        request_id=request_id,
        message="申请已提交，请使用request_id查询处理结果",
        estimated_processing_time=300  # 预估5分钟处理时间
      )
    else:
      raise HTTPException(status_code=500, detail="申请提交失败")

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"处理托管DID申请失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/status/{request_id}")
async def check_hosted_did_status(request: Request, request_id: str):
  """查询申请状态（中间状态检查）"""
  try:
    # 复用现有的域名管理逻辑
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    from anp_server import HostedDIDQueueManager
    queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
    status_info = await queue_manager.get_request_status(request_id)

    if not status_info:
      raise HTTPException(status_code=404, detail="申请ID不存在")

    return status_info

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"查询申请状态失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/check/{requester_did_id}")
async def check_hosted_did_result(request: Request, requester_did_id: str):
  """
  第二步：检查托管DID处理结果
  
  客户端使用自己的DID ID来检查是否有新的托管DID结果
  支持轮询调用
  """
  try:
    # 复用现有的域名管理逻辑
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    from anp_server.did_host.hosted_did_result_manager import HostedDIDResultManager
    result_manager = HostedDIDResultManager.create_for_domain(host, port)
    results = await result_manager.get_results_for_requester(requester_did_id)

    return {
      "success": True,
      "results": results,
      "total": len(results),
      "check_time": time.time(),
      "host": host,
      "port": port
    }

  except Exception as e:
    logger.error(f"检查托管DID结果失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/wba/hosted-did/acknowledge/{result_id}")
async def acknowledge_hosted_did_result(request: Request, result_id: str):
  """确认已收到托管DID结果"""
  try:
    # 复用现有的域名管理逻辑
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    from anp_server.did_host.hosted_did_result_manager import HostedDIDResultManager
    result_manager = HostedDIDResultManager.create_for_domain(host, port)
    success = await result_manager.acknowledge_result(result_id)

    if success:
      return {"success": True, "message": "结果确认成功"}
    else:
      raise HTTPException(status_code=404, detail="结果ID不存在")

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"确认托管DID结果失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/list")
async def list_hosted_dids(request: Request):
  """列出当前域名下的所有托管DID"""
  try:
    # 复用现有的域名管理逻辑
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
      raise HTTPException(status_code=403, detail=error_msg)

    # 使用现有的路径获取逻辑
    paths = domain_manager.get_all_data_paths(host, port)
    hosted_dir = paths['user_hosted_path']

    hosted_dids = []

    # 遍历托管DID目录
    for user_dir in hosted_dir.glob('user_*/'):
      try:
        did_doc_path = user_dir / 'did_document.json'
        request_path = user_dir / 'did_document_request.json'

        if did_doc_path.exists():
          with open(did_doc_path, 'r', encoding='utf-8') as f:
            did_doc = json.load(f)

          hosted_info = {
            'user_id': user_dir.name.replace('user_', ''),
            'hosted_did_id': did_doc.get('id'),
            'created_at': user_dir.stat().st_ctime
          }

          # 如果有原始请求信息
          if request_path.exists():
            with open(request_path, 'r', encoding='utf-8') as f:
              request_info = json.load(f)
            hosted_info['original_did'] = request_info.get('id')

          hosted_dids.append(hosted_info)

      except Exception as e:
        logger.warning(f"读取托管DID信息失败 {user_dir}: {e}")

    return {
      "hosted_dids": sorted(hosted_dids, key=lambda x: x.get('created_at', 0), reverse=True),
      "total": len(hosted_dids),
      "host": host,
      "port": port
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"列出托管DID失败: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 2. anp_server_hoster.py 增强方案

#### 现有DIDHostManager增强

```python
# anp_server_framework/anp_server/anp_server_hoster.py
# 在现有DIDHostManager基础上添加多域名支持

class DIDHostManager:
  """DID托管管理器（增强版）"""

  def __init__(self, hosted_dir: str = None, host: str = None, port: int = None):
    """
    初始化DID托管管理器
    
    Args:
        hosted_dir: DID托管目录路径，如果为None则使用默认路径
        host: 指定主机名（用于多域名环境）
        port: 指定端口（用于多域名环境）
    """
    if host and port:
      # 多域名模式：使用指定的主机和端口
      from anp_sdk.domain import get_domain_manager
      domain_manager = get_domain_manager()
      paths = domain_manager.get_all_data_paths(host, port)
      self.hosted_dir = paths['user_hosted_path']
      self.hostdomain = host
      self.hostport = str(port)
    else:
      # 兼容模式：使用现有逻辑
      config = get_global_config()
      self.hosted_dir = Path(hosted_dir or config.anp_sdk.user_hosted_path)
      self.hostdomain = os.environ.get('HOST_DID_DOMAIN', 'localhost')
      self.hostport = os.environ.get('HOST_DID_PORT', '9527')

    self.hosted_dir.mkdir(parents=True, exist_ok=True)

    # 保持现有的其他初始化逻辑
    self.hostname = socket.gethostname()
    self.hostip = socket.gethostbyname(self.hostname)

  @classmethod
  def create_for_domain(cls, host: str, port: int) -> 'DIDHostManager':
    """为指定域名创建DID托管管理器"""
    return cls(host=host, port=port)

  def _modify_did_document(self, did_document: dict, sid: str) -> dict:
    """
    修改DID文档，更新主机信息和ID（增强版）
    
    支持多域名环境的DID格式化
    """
    old_id = did_document['id']
    parts = old_id.split(':')

    if len(parts) > 3:
      # 使用当前域名的格式化逻辑
      if int(self.hostport) in [80, 443]:
        host_part = self.hostdomain
      else:
        host_part = f"{self.hostdomain}%3A{self.hostport}"

      parts[2] = host_part

      # 将user替换为hostuser
      for i in range(len(parts)):
        if parts[i] == "user":
          parts[i] = "hostuser"
      parts[-1] = sid
      new_id = ':'.join(parts)
      did_document['id'] = new_id

      # 递归替换所有出现的old_id（保持现有逻辑）
      def replace_all_old_id(did_document, old_id, new_id):
        if isinstance(did_document, dict):
          return {
            key: replace_all_old_id(value, old_id, new_id)
            for key, value in did_document.items()
          }
        elif isinstance(did_document, list):
          return [replace_all_old_id(item, old_id, new_id) for item in did_document]
        elif isinstance(did_document, str):
          return did_document.replace(old_id, new_id)
        else:
          return did_document

      did_document = replace_all_old_id(did_document, old_id, new_id)

    return did_document

  # 保持所有现有方法不变：is_duplicate_did, store_did_document
```

#### 新增HTTP处理函数

```python
# anp_server_framework/anp_server/anp_server_hoster.py
# 添加HTTP方式的托管DID处理函数

async def register_hosted_did_http(agent: ANPUser, target_host: str, target_port: int = 9527) -> Tuple[bool, str, str]:
  """
  HTTP方式申请托管DID
  
  Args:
      agent: ANP用户
      target_host: 目标托管服务主机
      target_port: 目标托管服务端口
      
  Returns:
      tuple: (是否成功, 申请ID, 错误信息)
  """
  try:
    if not agent.user_data.did_document:
      return False, "", "当前用户没有DID文档"

    # 构建申请请求
    request_data = {
      "did_document": agent.user_data.did_document,
      "requester_did": agent.user_data.did_document.get('id'),
      "callback_info": {
        "client_host": agent.host,
        "client_port": agent.port
      }
    }

    # 发送申请请求
    target_url = f"http://{target_host}:{target_port}/wba/hosted-did/request"

    import httpx
    async with httpx.AsyncClient() as client:
      response = await client.post(
        target_url,
        json=request_data,
        timeout=30.0
      )

      if response.status_code == 200:
        result = response.json()
        if result.get('success'):
          request_id = result.get('request_id')
          logger.info(f"托管DID申请已提交: {request_id}")
          return True, request_id, ""
        else:
          error_msg = result.get('message', '申请失败')
          return False, "", error_msg
      else:
        error_msg = f"申请请求失败: HTTP {response.status_code}"
        logger.error(error_msg)
        return False, "", error_msg

  except Exception as e:
    error_msg = f"申请托管DID失败: {e}"
    logger.error(error_msg)
    return False, "", error_msg


async def check_hosted_did_http(agent: ANPUser) -> Tuple[bool, List[Dict[str, Any]], str]:
  """
  HTTP方式检查托管DID结果
  
  Args:
      agent: ANP用户
      
  Returns:
      tuple: (是否成功, 结果列表, 错误信息)
  """
  try:
    if not agent.user_data.did_document:
      return False, [], "当前用户没有DID文档"

    # 从自己的DID中提取ID
    did_parts = agent.user_data.did_document.get('id', '').split(':')
    requester_id = did_parts[-1] if did_parts else ""

    if not requester_id:
      return False, [], "无法从DID中提取用户ID"

    # 检查结果（可以检查多个托管服务）
    all_results = []

    # 从配置获取目标服务列表
    config = get_global_config()
    target_services = config.hosted_did.get('target_services', [
      {"host": "localhost", "port": 9527},
      {"host": "open.localhost", "port": 9527},
    ])

    import httpx
    for service in target_services:
      target_host = service['host']
      target_port = service['port']

      try:
        check_url = f"http://{target_host}:{target_port}/wba/hosted-did/check/{requester_id}"

        async with httpx.AsyncClient() as client:
          response = await client.get(check_url, timeout=10.0)

          if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('results'):
              for res in result['results']:
                res['source_host'] = target_host
                res['source_port'] = target_port
              all_results.extend(result['results'])

      except Exception as e:
        logger.warning(f"检查托管服务 {target_host}:{target_port} 失败: {e}")

    return True, all_results, ""

  except Exception as e:
    error_msg = f"检查托管DID结果失败: {e}"
    logger.error(error_msg)
    return False, [], error_msg


# 统一的处理函数（兼容新旧方式）
async def register_hosted_did(agent: ANPUser, use_http: bool = True, target_host: str = None, target_port: int = 9527):
  """
  注册托管DID（支持HTTP和邮件两种方式）
  
  Args:
      agent: ANP用户
      use_http: 是否使用HTTP方式（默认True）
      target_host: 目标主机（HTTP方式使用）
      target_port: 目标端口（HTTP方式使用）
  """
  if use_http and target_host:
    # 使用新的HTTP方式
    success, request_id, error = await register_hosted_did_http(agent, target_host, target_port)
    if success:
      logger.info(f"托管DID申请已提交: {request_id}")
      return True
    else:
      logger.error(f"托管DID申请失败: {error}")
      return False
  else:
    # 保持现有的邮件方式完全不变
    try:
      did_document = agent.user_data.did_document
      if did_document is None:
        raise ValueError("当前 LocalAgent 未包含 did_document")

      config = get_global_config()
      use_local = config.mail.use_local_backend
      logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")

      mail_manager = EnhancedMailManager(use_local_backend=use_local)
      register_email = os.environ.get('REGISTER_MAIL_USER')
      success = mail_manager.send_hosted_did_request(did_document, register_email)

      if success:
        logger.info(f"{agent.anp_user_id}的托管DID申请邮件已发送")
        return True
      else:
        logger.error("发送托管DID申请邮件失败")
        return False
    except Exception as e:
      logger.error(f"注册托管DID失败: {e}")
      return False


async def check_hosted_did(agent: ANPUser, use_http: bool = True):
  """
  检查托管DID（支持HTTP和邮件两种方式）
  """
  if use_http:
    # 使用新的HTTP方式检查
    try:
      success, results, error = await check_hosted_did_http(agent)

      if success and results:
        # 处理结果，使用现有的create_hosted_did方法
        processed_count = 0
        for result in results:
          try:
            if result.get('success') and result.get('hosted_did_document'):
              hosted_did_doc = result['hosted_did_document']
              source_host = result.get('source_host', 'unknown')
              source_port = result.get('source_port', 9527)

              # 使用现有的create_hosted_did方法
              success, hosted_dir_name = agent.create_hosted_did(
                source_host, str(source_port), hosted_did_doc
              )

              if success:
                logger.info(f"托管DID已保存到: {hosted_dir_name}")
                processed_count += 1
              else:
                logger.error(f"保存托管DID失败: {hosted_dir_name}")
            else:
              logger.warning(f"托管DID申请失败: {result.get('error_message', '未知错误')}")

          except Exception as e:
            logger.error(f"处理托管DID结果失败: {e}")

        if processed_count > 0:
          return f"成功处理{processed_count}个托管DID结果"
        else:
          return "没有新的托管DID结果"
      elif error:
        return f"检查托管DID结果时发生错误: {error}"
      else:
        return "没有找到匹配的托管DID结果"

    except Exception as e:
      logger.error(f"HTTP检查托管DID失败: {e}")
      return f"HTTP检查托管DID时发生错误: {e}"
  else:
    # 保持现有的邮件方式完全不变
    try:
      import re
      import json

      config = get_global_config()
      use_local = config.mail.use_local_backend
      logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")

      mail_manager = EnhancedMailManager(use_local_backend=use_local)
      responses = mail_manager.get_unread_hosted_responses()

      if not responses:
        return "没有找到匹配的托管 DID 激活邮件"

      count = 0
      for response in responses:
        try:
          body = response.get('content', '')
          message_id = response.get('message_id')
          try:
            if isinstance(body, str):
              did_document = json.loads(body)
            else:
              did_document = body
          except Exception as e:
            logger.debug(f"无法解析 did_document: {e}")
            continue

          did_id = did_document.get('id', '')
          m = re.search(r'did:wba:([^:]+)%3A(\d+):', did_id)
          if not m:
            logger.debug(f"无法从id中提取host:port: {did_id}")
            continue

          host = m.group(1)
          port = m.group(2)

          # 使用现有的create_hosted_did方法
          success, hosted_dir_name = agent.create_hosted_did(host, port, did_document)
          if success:
            mail_manager.mark_message_as_read(message_id)
            logger.info(f"已创建{agent.anp_user_id}申请的托管DID{did_id}的文件夹: {hosted_dir_name}")
            count += 1
          else:
            logger.error(f"创建托管DID文件夹失败: {host}:{port}")
        except Exception as e:
          logger.error(f"处理邮件时出错: {e}")

      if count > 0:
        return f"成功处理{count}封托管DID邮件"
      else:
        return "未能成功处理任何托管DID邮件"
    except Exception as e:
      logger.error(f"检查托管DID时发生错误: {e}")
      return f"检查托管DID时发生错误: {e}"


# 保持现有的check_did_host_request函数，但添加多域名支持
async def check_did_host_request(host: str = None, port: int = None):
  """
  检查DID托管请求（支持多域名）
  
  Args:
      host: 指定主机名（用于多域名环境）
      port: 指定端口（用于多域名环境）
  """
  try:
    config = get_global_config()
    use_local = config.mail.use_local_backend
    logger.debug(f"管理邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")

    mail_manager = EnhancedMailManager(use_local_backend=use_local)

    # 根据参数创建DID管理器
    if host and port:
      did_manager = DIDHostManager.create_for_domain(host, port)
    else:
      did_manager = DIDHostManager()

    did_requests = mail_manager.get_unread_did_requests()
    if not did_requests:
      return "没有新的DID托管请求"

    result = "开始处理DID托管请求\n"
    for request in did_requests:
      did_document = request['content']
      from_address = request['from_address']
      message_id = request['message_id']

      parsed_json = json.loads(did_document)
      did_document_dict = dict(parsed_json)

      if did_manager.is_duplicate_did(did_document):
        mail_manager.send_reply_email(
          from_address,
          "DID已申请",
          "重复的DID申请，请联系管理员"
        )
        mail_manager.mark_message_as_read(message_id)
        result += f"{from_address}的DID {did_document_dict.get('id')} 已申请，退回\n"
        continue

      success, new_did_doc, error = did_manager.store_did_document(did_document_dict)
      if success:
        mail_manager.send_reply_email(
          from_address,
          "ANP HOSTED DID RESPONSED",
          new_did_doc)

        result += f"{from_address}的DID {new_did_doc['id']} 已保存到域名 {did_manager.hostdomain}:{did_manager.hostport}\n"
      else:
        mail_manager.send_reply_email(
          from_address,
          "DID托管申请失败",
          f"处理DID文档时发生错误: {error}"
        )
        result += f"{from_address}的DID处理失败: {error}\n"
      mail_manager.mark_message_as_read(message_id)

    logger.info(f"DID托管受理检查结果{result}")
    return result
  except Exception as e:
    error_msg = f"处理DID托管请求时发生错误: {e}"
    logger.error(error_msg)
    return error_msg
```

### 3. 队列管理器设计

```python
# anp_server_framework/anp_server/did_host/hosted_did_queue_manager.py

from enum import Enum
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from anp_sdk.domain import get_domain_manager
from anp_sdk.utils.log_base import logging as logger


class RequestStatus(Enum):
  """申请状态枚举"""
  PENDING = "pending"  # 等待处理
  PROCESSING = "processing"  # 正在处理
  COMPLETED = "completed"  # 处理完成
  FAILED = "failed"  # 处理失败


class HostedDIDQueueManager:
  """托管DID申请队列管理器"""

  def __init__(self, host: str, port: int):
    self.host = host
    self.port = port
    self.domain_manager = get_domain_manager()

    # 获取队列存储路径
    paths = self.domain_manager.get_all_data_paths(host, port)
    self.queue_dir = paths['base_path'] / "hosted_did_queue"
    self.queue_dir.mkdir(parents=True, exist_ok=True)

    # 子目录
    (self.queue_dir / "pending").mkdir(exist_ok=True)
    (self.queue_dir / "processing").mkdir(exist_ok=True)
    (self.queue_dir / "completed").mkdir(exist_ok=True)
    (self.queue_dir / "failed").mkdir(exist_ok=True)

  @classmethod
  def create_for_domain(cls, host: str, port: int) -> 'HostedDIDQueueManager':
    """为指定域名创建队列管理器"""
    return cls(host, port)

  async def add_request(self, request_id: str, hosted_request) -> bool:
    """添加申请到队列"""
    try:
      request_data = {
        "request_id": request_id,
        "requester_did": hosted_request.requester_did,
        "did_document": hosted_request.did_document,
        "callback_info": hosted_request.callback_info,
        "submit_time": time.time(),
        "status": RequestStatus.PENDING.value,
        "host": self.host,
        "port": self.port
      }

      # 保存到pending目录
      request_file = self.queue_dir / "pending" / f"{request_id}.json"
      with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)

      logger.info(f"申请已添加到队列: {request_id}")
      return True

    except Exception as e:
      logger.error(f"添加申请到队列失败: {e}")
      return False

  async def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
    """获取申请状态"""
    try:
      # 在各个状态目录中查找
      for status in RequestStatus:
        request_file = self.queue_dir / status.value / f"{request_id}.json"
        if request_file.exists():
          with open(request_file, 'r', encoding='utf-8') as f:
            request_data = json.load(f)

          return {
            "request_id": request_id,
            "status": status.value,
            "submit_time": request_data.get("submit_time"),
            "process_time": request_data.get("process_time"),
            "complete_time": request_data.get("complete_time"),
            "message": request_data.get("message", ""),
            "requester_did": request_data.get("requester_did")
          }

      return None

    except Exception as e:
      logger.error(f"获取申请状态失败: {e}")
      return None

  async def get_pending_requests(self) -> List[Dict[str, Any]]:
    """获取待处理的申请"""
    try:
      pending_requests = []
      pending_dir = self.queue_dir / "pending"

      for request_file in pending_dir.glob("*.json"):
        try:
          with open(request_file, 'r', encoding='utf-8') as f:
            request_data = json.load(f)
          pending_requests.append(request_data)
        except Exception as e:
          logger.warning(f"读取申请文件失败 {request_file}: {e}")

      # 按提交时间排序
      return sorted(pending_requests, key=lambda x: x.get("submit_time", 0))

    except Exception as e:
      logger.error(f"获取待处理申请失败: {e}")
      return []

  async def move_request_status(self, request_id: str, from_status: RequestStatus,
                                to_status: RequestStatus, message: str = "") -> bool:
    """移动申请状态"""
    try:
      from_file = self.queue_dir / from_status.value / f"{request_id}.json"
      to_file = self.queue_dir / to_status.value / f"{request_id}.json"

      if not from_file.exists():
        logger.warning(f"申请文件不存在: {from_file}")
        return False

      # 读取并更新数据
      with open(from_file, 'r', encoding='utf-8') as f:
        request_data = json.load(f)

      request_data["status"] = to_status.value
      request_data["message"] = message

      if to_status == RequestStatus.PROCESSING:
        request_data["process_time"] = time.time()
      elif to_status in [RequestStatus.COMPLETED, RequestStatus.FAILED]:
        request_data["complete_time"] = time.time()

      # 保存到新位置
      with open(to_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)

      # 删除原文件
      from_file.unlink()

      logger.info(f"申请状态已更新: {request_id} {from_status.value} -> {to_status.value}")
      return True

    except Exception as e:
      logger.error(f"移动申请状态失败: {e}")
      return False
```

### 3. 结果管理器设计

```python
# anp_server_framework/anp_server/did_host/hosted_did_result_manager.py

class HostedDIDResultManager:
    """托管DID结果管理器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.domain_manager = get_domain_manager()
        
        # 获取结果存储路径
        paths = self.domain_manager.get_all_data_paths(host, port)
        self.results_dir = paths['base_path'] / "hosted_did_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        (self.results_dir / "pending").mkdir(exist_ok=True)      # 待客户端获取
        (self.results_dir / "acknowledged").mkdir(exist_ok=True) # 已确认收到
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'HostedDIDResultManager':
        """为指定域名创建结果管理器"""
        return cls(host, port)
    
    async def publish_result(self, request_id: str, requester_did: str, 
                           hosted_did_document: Dict[str, Any], success: bool = True, 
                           error_message: str = "") -> bool:
        """发布处理结果"""
        # 实现结果发布逻辑
        pass
    
    async def get_results_for_requester(self, requester_did_id: str) -> List[Dict[str, Any]]:
        """获取指定申请者的处理结果"""
        # 实现结果获取逻辑
        pass
    
    async def acknowledge_result(self, result_id: str) -> bool:
        """确认结果已收到"""
        # 实现结果确认逻辑
        pass
```

### 4. 后台处理器设计

```python
# anp_server_framework/anp_server/did_host/hosted_did_processor.py

class HostedDIDProcessor:
    """托管DID后台处理器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        self.result_manager = HostedDIDResultManager.create_for_domain(host, port)
        self.did_manager = DIDManager.create_for_domain(host, port)
        self.running = False
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'HostedDIDProcessor':
        """为指定域名创建处理器"""
        return cls(host, port)
    
    async def start_processing(self):
        """启动后台处理"""
        self.running = True
        logger.info(f"托管DID处理器启动: {self.host}:{self.port}")
        
        while self.running:
            try:
                await self.process_pending_requests()
                await asyncio.sleep(10)  # 每10秒检查一次
            except Exception as e:
                logger.error(f"处理循环出错: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒
    
    def stop_processing(self):
        """停止后台处理"""
        self.running = False
        logger.info(f"托管DID处理器停止: {self.host}:{self.port}")
    
    async def process_pending_requests(self):
        """处理待处理的申请"""
        # 实现申请处理逻辑
        pass
    
    async def perform_business_logic(self, request_data: Dict[str, Any]):
        """
        执行实际的业务逻辑
        
        这里可以添加：
        - 身份验证
        - 审批流程
        - 外部系统调用
        - 合规检查
        等等
        """
        # 模拟处理时间
        await asyncio.sleep(2)
        
        # 这里可以添加实际的业务逻辑
        logger.debug(f"执行业务逻辑: {request_data['request_id']}")
```

### 5. 客户端增强

```python
# anp_sdk/anp_user.py (添加到ANPUser类)

async def request_hosted_did_async(self, target_host: str, target_port: int = 9527) -> Tuple[bool, str, str]:
    """
    异步申请托管DID（第一步：提交申请）
    
    Returns:
        tuple: (是否成功, 申请ID, 错误信息)
    """
    try:
        if not self.user_data.did_document:
            return False, "", "当前用户没有DID文档"
        
        # 构建申请请求
        request_data = {
            "did_document": self.user_data.did_document,
            "requester_did": self.user_data.did_document.get('id'),
            "callback_info": {
                "client_host": self.host,
                "client_port": self.port
            }
        }
        
        # 发送申请请求
        target_url = f"http://{target_host}:{target_port}/did_host/hosted-did/request"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    request_id = result.get('request_id')
                    logger.info(f"托管DID申请已提交: {request_id}")
                    return True, request_id, ""
                else:
                    error_msg = result.get('message', '申请失败')
                    return False, "", error_msg
            else:
                error_msg = f"申请请求失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return False, "", error_msg
                
    except Exception as e:
        error_msg = f"申请托管DID失败: {e}"
        logger.error(error_msg)
        return False, "", error_msg

async def check_hosted_did_results(self) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    检查托管DID处理结果（第二步：检查结果）
    
    Returns:
        tuple: (是否成功, 结果列表, 错误信息)
    """
    try:
        if not self.user_data.did_document:
            return False, [], "当前用户没有DID文档"
        
        # 从自己的DID中提取ID
        did_parts = self.user_data.did_document.get('id', '').split(':')
        requester_id = did_parts[-1] if did_parts else ""
        
        if not requester_id:
            return False, [], "无法从DID中提取用户ID"
        
        # 检查结果（可以检查多个托管服务）
        all_results = []
        
        # 这里可以配置多个托管服务地址
        target_services = [
            ("localhost", 9527),
            ("open.localhost", 9527),
            # 可以添加更多托管服务
        ]
        
        for target_host, target_port in target_services:
            try:
                check_url = f"http://{target_host}:{target_port}/wba/hosted-did/check/{requester_id}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(check_url, timeout=10.0)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success') and result.get('results'):
                            for res in result['results']:
                                res['source_host'] = target_host
                                res['source_port'] = target_port
                            all_results.extend(result['results'])
                    
            except Exception as e:
                logger.warning(f"检查托管服务 {target_host}:{target_port} 失败: {e}")
        
        return True, all_results, ""
        
    except Exception as e:
        error_msg = f"检查托管DID结果失败: {e}"
        logger.error(error_msg)
        return False, [], error_msg

async def process_hosted_did_results(self, results: List[Dict[str, Any]]) -> int:
    """
    处理托管DID结果
    
    使用现有的create_hosted_did方法保存到本地
    在anp_users/下创建user_hosted_{host}_{port}_{id}/目录
    """
    processed_count = 0
    
    for result in results:
        try:
            if result.get('success') and result.get('hosted_did_document'):
                hosted_did_doc = result['hosted_did_document']
                source_host = result.get('source_host', 'unknown')
                source_port = result.get('source_port', 9527)
                
                # 使用现有的create_hosted_did方法
                # 这会在anp_users/下创建user_hosted_{host}_{port}_{id}/目录
                success, hosted_dir_name = self.create_hosted_did(
                    source_host, str(source_port), hosted_did_doc
                )
                
                if success:
                    # 确认收到结果
                    await self._acknowledge_hosted_did_result(
                        result['result_id'], source_host, source_port
                    )
                    
                    logger.info(f"托管DID已保存到: {hosted_dir_name}")
                    logger.info(f"托管DID ID: {hosted_did_doc.get('id')}")
                    processed_count += 1
                else:
                    logger.error(f"保存托管DID失败: {hosted_dir_name}")
            else:
                logger.warning(f"托管DID申请失败: {result.get('error_message', '未知错误')}")
                
        except Exception as e:
            logger.error(f"处理托管DID结果失败: {e}")
    
    return processed_count

async def poll_hosted_did_results(self, interval: int = 30, max_polls: int = 20) -> int:
    """
    轮询托管DID结果
    
    Args:
        interval: 轮询间隔（秒）
        max_polls: 最大轮询次数
        
    Returns:
        int: 总共处理的结果数量
    """
    total_processed = 0
    
    for i in range(max_polls):
        try:
            success, results, error = await self.check_hosted_did_results()
            
            if success and results:
                processed = await self.process_hosted_did_results(results)
                total_processed += processed
                
                if processed > 0:
                    logger.info(f"轮询第{i+1}次: 处理了{processed}个托管DID结果")
            
            if i < max_polls - 1:  # 不是最后一次
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"轮询托管DID结果失败: {e}")
            await asyncio.sleep(interval)
    
    return total_processed
```

### 6. 兼容性处理

```python
# anp_server_framework/anp_server/did_host/anp_sdk_publisher.py
# 修改现有函数，添加HTTP选项

async def register_hosted_did(agent: ANPUser, use_http: bool = True, target_host: str = None, target_port: int = 9527):
    """
    注册托管DID（支持HTTP和邮件两种方式）
    
    Args:
        agent: ANP用户
        use_http: 是否使用HTTP方式（默认True）
        target_host: 目标主机（HTTP方式使用）
        target_port: 目标端口（HTTP方式使用）
    """
    if use_http and target_host:
        # 使用新的HTTP方式
        success, request_id, error = await agent.request_hosted_did_async(target_host, target_port)
        if success:
            logger.info(f"托管DID申请已提交: {request_id}")
            return True
        else:
            logger.error(f"托管DID申请失败: {error}")
            return False
    else:
        # 保持现有的邮件方式完全不变
        try:
            # ... 现有的邮件逻辑完全不变
            pass
        except Exception as e:
            logger.error(f"注册托管DID失败: {e}")
            return False

async def check_hosted_did(agent: ANPUser, use_http: bool = True):
    """
    检查托管DID（支持HTTP和邮件两种方式）
    """
    if use_http:
        # 使用新的HTTP方式检查
        try:
            success, results, error = await agent.check_hosted_did_results()
            
            if success and results:
                processed = await agent.process_hosted_did_results(results)
                if processed > 0:
                    return f"成功处理{processed}个托管DID结果"
                else:
                    return "没有新的托管DID结果"
            elif error:
                return f"检查托管DID结果时发生错误: {error}"
            else:
                return "没有找到匹配的托管DID结果"
                
        except Exception as e:
            logger.error(f"HTTP检查托管DID失败: {e}")
            return f"HTTP检查托管DID时发生错误: {e}"
    else:
        # 保持现有的邮件方式完全不变
        # 调用现有的 agent.create_hosted_did(host, port, did_document)
        # 在anp_users/下创建user_hosted_{host}_{port}_{id}/目录
        try:
            # ... 现有的邮件逻辑完全不变
            pass
        except Exception as e:
            logger.error(f"检查托管DID时发生错误: {e}")
            return f"检查托管DID时发生错误: {e}"
```

## 📋 配置文件支持

### unified_config.yaml 增强

```yaml
# 托管DID配置
hosted_did:
  use_http_api: true              # 是否使用HTTP API（默认true）
  use_email_backup: false         # 是否保留邮件作为备用（默认false）
  check_interval: 30              # 检查间隔（秒）
  max_poll_attempts: 20           # 最大轮询次数
  processing_timeout: 300         # 处理超时时间（秒）
  
  # 目标托管服务列表
  target_services:
    - host: "localhost"
      port: 9527
    - host: "open.localhost"  
      port: 9527
  
  # 业务处理配置
  business_logic:
    enable_identity_verification: true    # 启用身份验证
    enable_approval_workflow: false       # 启用审批流程
    enable_compliance_check: true         # 启用合规检查
    auto_approve_known_clients: true      # 自动批准已知客户端
```

## 🎯 使用示例

### 完整流程演示

```python
# 完整的使用示例
async def demo_complete_hosted_did_flow():
    """演示完整的托管DID流程"""
    
    # 1. 客户端A (user.localhost:9527)
    user_a = ANPUser(host="user.localhost", port=9527)
    await user_a.initialize()
    
    print(f"客户端A的DID: {user_a.user_data.did_document.get('id')}")
    
    # 2. 第一步：提交申请到托管服务器 (open.localhost:9527)
    success, request_id, error = await user_a.request_hosted_did_async(
        target_host="open.localhost",
        target_port=9527
    )
    
    if success:
        print(f"✅ 申请已提交到 open.localhost:9527，申请ID: {request_id}")
        
        # 3. 第二步：轮询检查结果
        print("🔄 开始轮询检查结果...")
        processed_count = await user_a.poll_hosted_did_results(
            interval=10,  # 每10秒检查一次
            max_polls=30  # 最多检查30次
        )
        
        if processed_count > 0:
            print(f"🎉 成功处理了 {processed_count} 个托管DID结果")
            
            # 4. 查看创建的目录
            user_data_path = user_a.user_data_path
            hosted_dirs = list(user_data_path.glob("user_hosted_open_localhost_9527_*"))
            
            for hosted_dir in hosted_dirs:
                print(f"📁 创建的托管DID目录: {hosted_dir.name}")
                
                # 查看托管DID文档
                did_doc_path = hosted_dir / "did_document.json"
                if did_doc_path.exists():
                    with open(did_doc_path, 'r', encoding='utf-8') as f:
                        hosted_did_doc = json.load(f)
                    print(f"🆔 托管DID ID: {hosted_did_doc.get('id')}")
        else:
            print("⚠️ 没有收到托管DID结果")
    else:
        print(f"❌ 申请失败: {error}")

# 运行演示
if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_complete_hosted_did_flow())
```

### 基于现有结构的使用方式

```python
# 导入现有的托管逻辑
from anp_server import (
  register_hosted_did, check_hosted_did, check_did_host_request
)

# 旧方式（邮件）- 保持不变
success = await register_hosted_did(agent, use_http=False)
result = await check_hosted_did(agent, use_http=False)

# 新方式（HTTP）- 基于现有函数
success = await register_hosted_did(
  agent,
  use_http=True,
  target_host="open.localhost",
  target_port=9527
)
result = await check_hosted_did(agent, use_http=True)

# 配置驱动方式
config = get_global_config()
use_http = config.hosted_did.get('use_http_api', True)
success = await register_hosted_did(agent, use_http=use_http)
result = await check_hosted_did(agent, use_http=use_http)

# 服务器端处理（支持多域名）
result = await check_did_host_request(host="open.localhost", port=9527)
```

### HTTP API调用示例

```bash
# 申请托管DID
curl -X POST "http://open.localhost:9527/wba/hosted-did/request" \
  -H "Content-Type: application/json" \
  -d '{
    "did_document": {...},
    "requester_did": "did:wba:user.localhost:9527:wba:user:abc123"
  }'

# 查询申请状态
curl "http://open.localhost:9527/wba/hosted-did/status/request-id-123"

# 检查处理结果
curl "http://open.localhost:9527/wba/hosted-did/check/abc123"

# 列出托管DID
curl "http://open.localhost:9527/wba/hosted-did/list"

# 获取托管DID文档（现有接口）
curl "http://open.localhost:9527/wba/hostuser/xyz789/did.json"
```

## 📊 实施计划（基于现有重构成果）

### ✅ 已完成的重构成果
- `router_host.py`: 托管DID的Web接口专用路由，已支持多域名
- `anp_server_hoster.py`: 独立的托管业务逻辑，包含完整的DIDHostManager
- 清晰的职责分离和模块化设计

### 阶段一：HTTP接口增强（Week 1）

#### 1.1 router_host.py 增强
- **目标**: 在现有路由基础上添加HTTP申请接口
- **交付物**:
  - 添加 `/wba/hosted-did/request` 申请接口
  - 添加 `/wba/hosted-did/status/{request_id}` 状态查询接口
  - 添加 `/wba/hosted-did/check/{requester_did_id}` 结果检查接口
  - 添加 `/wba/hosted-did/acknowledge/{result_id}` 确认接口
  - 添加 `/wba/hosted-did/list` 列表接口

#### 1.2 anp_server_hoster.py 增强
- **目标**: 在现有DIDHostManager基础上添加HTTP支持
- **交付物**:
  - 为DIDHostManager添加多域名支持
  - 添加 `register_hosted_did_http` 函数
  - 添加 `check_hosted_did_http` 函数
  - 更新现有函数支持HTTP/邮件双模式

### 阶段二：队列和结果管理（Week 2）

#### 2.1 队列管理器开发
- **目标**: 实现申请队列和状态管理
- **交付物**:
  - `hosted_did_queue_manager.py`
  - 申请状态枚举和转换逻辑
  - 队列文件存储和管理

#### 2.2 结果管理器开发
- **目标**: 实现结果存储和分发机制
- **交付物**:
  - `hosted_did_result_manager.py`
  - 结果发布和确认逻辑
  - 按申请者分组的结果管理

### 阶段三：后台处理器（Week 3）

#### 3.1 后台处理器开发
- **目标**: 实现异步申请处理逻辑
- **交付物**:
  - `hosted_did_processor.py`
  - 与现有DIDHostManager的集成
  - 业务逻辑处理框架
  - 错误处理和重试机制

#### 3.2 处理器与现有逻辑集成
- **目标**: 将处理器与现有的托管逻辑集成
- **交付物**:
  - 处理器调用现有的 `store_did_document` 方法
  - 结果发布到结果管理器
  - 状态更新和日志记录

### 阶段四：客户端增强（Week 4）

#### 4.1 ANPUser HTTP方法
- **目标**: 为ANPUser添加HTTP申请和检查方法
- **交付物**:
  - `request_hosted_did_async` 方法
  - `check_hosted_did_results` 方法
  - `process_hosted_did_results` 方法
  - `poll_hosted_did_results` 轮询方法

#### 4.2 与现有create_hosted_did集成
- **目标**: 确保HTTP结果使用现有的存储逻辑
- **交付物**:
  - HTTP结果调用现有的 `create_hosted_did` 方法
  - 保持现有的目录结构 `user_hosted_{host}_{port}_{id}`
  - 完整的兼容性测试

### 阶段五：配置和兼容性（Week 5）

#### 5.1 配置系统增强
- **目标**: 完善配置支持
- **交付物**:
  - 更新 `unified_config.yaml` 添加hosted_did配置
  - 目标服务列表配置
  - HTTP/邮件方式选择配置

#### 5.2 兼容性处理
- **目标**: 确保新旧方式可以并存
- **交付物**:
  - 更新现有的 `register_hosted_did` 函数支持双模式
  - 更新现有的 `check_hosted_did` 函数支持双模式
  - 统一的调用接口

### 阶段六：测试和文档（Week 6）

#### 6.1 集成测试
- **目标**: 确保系统稳定性
- **交付物**:
  - HTTP申请流程端到端测试
  - 多域名环境测试
  - 兼容性回归测试
  - 性能测试

#### 6.2 文档和示例
- **目标**: 完善使用文档
- **交付物**:
  - API文档更新
  - 使用示例和最佳实践
  - 迁移指南
  - 故障排除手册

## 🎉 预期收益

### 技术收益
1. **简化部署**: 减少邮件服务依赖，降低部署复杂度
2. **提升性能**: HTTP API提供更快的响应速度
3. **增强监控**: 完整的状态跟踪和日志记录
4. **提高可靠性**: 减少邮件服务故障点

### 业务收益
1. **改善用户体验**: 实时反馈和状态查询
2. **支持复杂流程**: 可以集成审批、验证等业务逻辑
3. **提高可扩展性**: 支持高并发和大规模部署
4. **降低维护成本**: 减少邮件相关的配置和维护工作

### 兼容性保证
1. **零破坏性**: 现有代码和目录结构完全不变
2. **渐进迁移**: 可以逐步从邮件切换到HTTP
3. **双重保障**: HTTP和邮件可以并存
4. **配置驱动**: 通过配置控制使用方式

## 📝 风险评估与缓解

### 主要风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 现有结构破坏 | 高 | 极低 | 基于现有router_host.py和anp_server_hoster.py增强 |
| 兼容性问题 | 中 | 低 | 保持现有函数签名和行为不变 |
| 性能影响 | 中 | 低 | 复用现有的域名管理和路径解析逻辑 |
| 配置复杂性 | 低 | 中 | 基于现有配置结构，提供合理默认值 |

### 缓解策略
1. **基于现有结构**: 完全基于已重构的router_host.py和anp_server_hoster.py
2. **保持现有逻辑**: DIDHostManager和现有处理逻辑完全不变
3. **渐进增强**: 只添加新功能，不修改现有功能
4. **充分测试**: 重点测试与现有逻辑的集成

## 📞 总结

基于您已完成的结构重构，本改进方案提供了一个完整的托管DID申请流程轻量化解决方案：

### ✅ 基于现有重构的优势
1. **结构清晰**: 基于已重构的router_host.py和anp_server_hoster.py
2. **职责明确**: Web接口和业务逻辑完全分离
3. **多域名就绪**: 现有结构已支持多域名，只需增强功能
4. **零破坏性**: 完全基于现有结构增强，不破坏任何现有逻辑

### ✅ 核心改进特点
1. **轻量化设计**: 使用HTTP API替代邮件，减少依赖
2. **生产就绪**: 支持异步处理和复杂业务流程
3. **完全兼容**: 保持现有DIDHostManager和处理逻辑不变
4. **可扩展性**: 支持高并发和多域名环境
5. **易于监控**: 完整的状态跟踪和日志记录

### ✅ 实施优势
1. **快速实施**: 基于现有结构，实施周期缩短到6周
2. **风险极低**: 不修改现有逻辑，只添加新功能
3. **测试简单**: 重点测试新增功能和集成点
4. **维护友好**: 保持清晰的模块化结构

### ✅ 技术架构优势
```
现有架构基础:
router_host.py (Web接口) ←→ anp_server_hoster.py (业务逻辑)
                ↓                        ↓
        HTTP API增强              DIDHostManager增强
                ↓                        ↓
        队列管理器 ←→ 结果管理器 ←→ 后台处理器
```

通过这个基于现有重构成果的改进方案，ANP SDK将以最小的风险和最快的速度获得现代化的托管DID处理能力，为用户提供更好的体验。

---

**文档版本**: v1.0  
**最后更新**: 2025年1月11日  
**状态**: 设计完成，待实施 📋