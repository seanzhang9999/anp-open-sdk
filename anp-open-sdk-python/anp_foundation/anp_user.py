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
import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional

from anp_foundation.anp_user_local_data import get_user_data_manager

logger = logging.getLogger(__name__)

from anp_foundation.config import get_global_config
from anp_foundation.did.did_tool import parse_wba_did_host_port
from anp_foundation.contact_manager import ContactManager

class RemoteANPUser:
    def __init__(self, id: str, name: str = None, host: str = None, port: int = None, **kwargs):
        self.id = id
        self.name = name
        self.host = host
        self.port = port
        if self.id and (self.host is None or self.port is None):
            self.host, self.port = parse_wba_did_host_port(self.id)
        self.extra = kwargs

    def to_dict(self):
        return {
            "did": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            **self.extra
        }

class ANPUser:
    """本地智能体，代表当前用户的DID身份"""

    # 类级别的实例缓存，确保同一个DID只有一个ANPUser实例
    _instances = {}

    def __init__(self, user_data, name: str = "未命名", agent_type: str = "personal"):
        """初始化本地智能体
        
        Args:
            user_data: 用户数据对象
            agent_type: 智能体类型，"personal"或"anp_service"
        """
        self.user_data = user_data
        user_dir = self.user_data.user_dir

        if name == "未命名":
            if self.user_data.name  is not None:
                self.name = self.user_data.name
            else:
                self.name = f"未命名智能体{self.user_data.did}"
        self.id = self.user_data.did
        self.name = name
        self.user_dir = user_dir
        self.agent_type = agent_type
        
        # 将实例添加到缓存中（如果还没有的话）
        if self.id not in self._instances:
            self._instances[self.id] = self
            logger.debug(f"🆕 缓存ANPUser实例 (直接构造): {self.id}")
        else:
            logger.debug(f"🔄 ANPUser实例已存在于缓存中: {self.id}")
        config = get_global_config()
        self.key_id = config.anp_sdk.user_did_key_id

        self.did_document_path = self.user_data.did_doc_path
        self.private_key_path = self.user_data.did_private_key_file_path
        self.jwt_private_key_path = self.user_data.jwt_private_key_file_path
        self.jwt_public_key_path = self.user_data.jwt_public_key_file_path

        self.logger = logger
        self._ws_connections = {}
        self._sse_clients = set()
        # 托管DID标识
        self.is_hosted_did = self.user_data.is_hosted_did
        self.parent_did = self.user_data.parent_did
        self.hosted_info = self.user_data.hosted_info
        import requests
        self.requests = requests

        # 群组相关属性
        self.group_queues = {}  # 群组消息队列: {group_id: {client_id: Queue}}
        self.group_members = {}  # 群组成员列表: {group_id: set(did)}

        # 新增：联系人管理器
        self.contact_manager = ContactManager(self.user_data)
        
        # 为了向后兼容，添加API路由和消息处理器属性
        self.api_routes = {}  # path -> handler
        self.message_handlers = {}  # type -> handler

    @classmethod
    def from_did(cls, did: str, name: str = "未命名", agent_type: str = "personal"):
        # 检查实例缓存
        if did in cls._instances:
            logger.debug(f"🔄 复用ANPUser实例: {did}")
            return cls._instances[did]
        
        user_data_manager = get_user_data_manager()
        user_data = user_data_manager.get_user_data(did)
        if not user_data:
            # 尝试刷新用户数据
            logger.debug(f"用户 {did} 不在内存中，尝试刷新用户数据...")
            user_data_manager.scan_and_load_new_users()
            # 再次尝试获取
            user_data = user_data_manager.get_user_data(did)
            if not user_data:
                # 如果还是找不到，抛出异常
                raise ValueError(f"未找到 DID 为 '{did}' 的用户数据。请检查您的用户目录和配置文件。")
        if name == "未命名":
            name = user_data.name
        if not user_data:
            raise ValueError(f"未找到 DID 为 {did} 的用户数据")
        
        # 创建新实例并缓存
        instance = cls(user_data, name, agent_type)
        cls._instances[did] = instance
        logger.debug(f"🆕 创建并缓存ANPUser实例: {did}")
        return instance

    def __del__(self):
        """确保在对象销毁时释放资源"""
        try:
            for ws in self._ws_connections.values():
                self.logger.debug(f"LocalAgent {self.id} 销毁时存在未关闭的WebSocket连接")
            self._ws_connections.clear()
            self._sse_clients.clear()
            self.logger.debug(f"LocalAgent {self.id} 资源已释放")
        except Exception:
            pass
                
    def get_host_dids(self):
        """获取用户目录"""
        return self.user_dir



    def get_token_to_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.get_token_to_remote(remote_did)

    def store_token_from_remote(self, remote_did, token, hosted_did=None):
        return self.contact_manager.store_token_from_remote(remote_did, token)

    def get_token_from_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.get_token_from_remote(remote_did)

    def revoke_token_to_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.revoke_token_to_remote(remote_did)

    def add_contact(self, remote_agent):
        contact = remote_agent if isinstance(remote_agent, dict) else remote_agent.to_dict() if hasattr(remote_agent, "to_dict") else {
            "did": remote_agent.id,
            "host": getattr(remote_agent, "host", None),
            "port": getattr(remote_agent, "port", None),
            "name": getattr(remote_agent, "name", None)
        }
        self.contact_manager.add_contact(contact)

    def get_contact(self, remote_did: str):
        return self.contact_manager.get_contact(remote_did)

    def list_contacts(self):
        return self.contact_manager.list_contacts()

    async def request_hosted_did_async(self, target_host: str, target_port: int = 9527) -> Tuple[bool, str, str]:
        """
        异步申请托管DID（第一步：提交申请）
        
        Args:
            target_host: 目标托管服务主机
            target_port: 目标托管服务端口
            
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
                    "client_host": getattr(self, 'host', 'localhost'),
                    "client_port": getattr(self, 'port', 9527)
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
                        logger.debug(f"托管DID申请已提交: {request_id}")
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
            
            import httpx
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
                    success, hosted_result = self.create_hosted_did(
                        source_host, str(source_port), hosted_did_doc
                    )
                    
                    if success:
                        # 确认收到结果
                        await self._acknowledge_hosted_did_result(
                            result.get('result_id', ''), source_host, source_port
                        )
                        
                        logger.debug(f"托管DID已保存: {hosted_result}")
                        logger.debug(f"托管DID ID: {hosted_did_doc.get('id')}")
                        processed_count += 1
                    else:
                        logger.error(f"保存托管DID失败: {hosted_result}")
                else:
                    logger.warning(f"托管DID申请失败: {result.get('error_message', '未知错误')}")
                    
            except Exception as e:
                logger.error(f"处理托管DID结果失败: {e}")
        
        return processed_count

    async def _acknowledge_hosted_did_result(self, result_id: str, source_host: str, source_port: int):
        """确认收到托管DID结果"""
        try:
            if not result_id:
                return
                
            ack_url = f"http://{source_host}:{source_port}/wba/hosted-did/acknowledge/{result_id}"
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(ack_url, timeout=10.0)
                if response.status_code == 200:
                    logger.debug(f"已确认托管DID结果: {result_id}")
                else:
                    logger.warning(f"确认托管DID结果失败: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"确认托管DID结果时出错: {e}")

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
                        logger.debug(f"轮询第{i+1}次: 处理了{processed}个托管DID结果")
                
                if i < max_polls - 1:  # 不是最后一次
                    await asyncio.sleep(interval)
                    
            except Exception as e:
                logger.error(f"轮询托管DID结果失败: {e}")
                await asyncio.sleep(interval)
        
        return total_processed

    def create_hosted_did(self, host: str, port: str, did_document: dict) -> Tuple[bool, Any]:
        """
        [新] 创建一个托管DID。此方法将调用数据管理器来处理持久化和内存加载。
        """
        manager = get_user_data_manager()
        success, new_user_data = manager.create_hosted_user(
            parent_user_data=self.user_data,
            host=host,
            port=port,
            did_document=did_document
        )
        if success:
            # 使用缓存机制创建ANPUser实例
            hosted_did = new_user_data.did
            if hosted_did in self._instances:
                logger.debug(f"🔄 复用ANPUser实例 (托管DID): {hosted_did}")
                return True, self._instances[hosted_did]
            
            # 创建新实例并缓存
            instance = ANPUser(user_data=new_user_data)
            self._instances[hosted_did] = instance
            logger.debug(f"🆕 创建并缓存ANPUser实例 (托管DID): {hosted_did}")
            return True, instance
        return False, None

    def get_or_create_agent(self, name: Optional[str] = None, shared: bool = False, 
                           prefix: Optional[str] = None, primary_agent: bool = False):
        """获取或创建与此ANPUser关联的Agent实例
        
        Args:
            name: Agent名称，默认使用ANPUser的name
            shared: 是否共享DID模式
            prefix: 共享模式下的API前缀
            primary_agent: 是否为主Agent
            
        Returns:
            Agent: 关联的Agent实例
        """
        from anp_runtime.agent_manager import AgentManager
        from anp_runtime.agent import Agent
        
        # 查找与此ANPUser关联的Agent实例
        agent = AgentManager.get_agent_by_anp_user(self)
        if agent:
            logger.debug(f"🔄 复用已存在的Agent: {agent.name}")
            return agent
        
        # 如果没有找到，创建新的Agent实例
        agent_name = name or self.name
        agent = Agent(self, agent_name, shared, prefix, primary_agent)
        
        # 迁移API路由到新Agent
        for path, handler in list(self.api_routes.items()):
            agent._api(path)(handler)
            logger.debug(f"🔄 迁移API到新Agent: {path}")
        
        # 迁移消息处理器到新Agent
        for msg_type, handler in list(self.message_handlers.items()):
            try:
                agent._message_handler(msg_type)(handler)
                logger.debug(f"🔄 迁移消息处理器到新Agent: {msg_type}")
            except PermissionError as e:
                logger.warning(f"⚠️ 消息处理器迁移失败: {e}")
        
        logger.debug(f"✅ 为ANPUser创建新Agent: {agent_name}")
        return agent
    
    async def handle_request(self, req_did: str, request_data: Dict[str, Any], request):
        """向后兼容的请求处理方法 - 桥接到新Agent系统"""
        # 获取或创建Agent实例
        agent = self.get_or_create_agent()
        
        # 使用Agent处理请求
        logger.debug(f"🔄 ANPUser.handle_request 桥接到 Agent: {agent.name}")
        return await agent.handle_request(req_did, request_data, request)
