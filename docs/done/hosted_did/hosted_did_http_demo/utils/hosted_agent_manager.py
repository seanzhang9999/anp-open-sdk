"""
托管Agent管理器

负责发现、注册和管理托管Agent
"""

from typing import List, Dict, Any, Optional
from anp_open_sdk.utils.log_base import logging as logger
from anp_open_sdk_framework.server.anp_server import ANPUser


class HostedAgentManager:
    """托管Agent管理器"""
    
    def __init__(self):
        self.hosted_agents = []
        self.agent_registry = {}
    
    async def discover_hosted_agents(self, sdk) -> List[ANPUser]:
        """发现系统中的托管Agent"""
        try:
            hosted_agents = []
            
            # 获取用户数据管理器
            if hasattr(sdk, 'user_data_manager'):
                user_data_manager = sdk.user_data_manager
                user_datas = user_data_manager.get_all_users()
                
                # 遍历所有用户数据，查找托管Agent
                for user_data in user_datas:
                    try:
                        agent = ANPUser.from_did(user_data.did)
                        
                        # 检查是否为托管Agent
                        if hasattr(agent, 'is_hosted_did') and agent.is_hosted_did:
                            # 设置托管Agent名称
                            if not hasattr(agent, 'name') or not agent.name:
                                agent.name = f"托管Agent_{agent.id.split(':')[-1][:8]}"
                            
                            hosted_agents.append(agent)
                            logger.debug(f"发现托管Agent: {agent.name} ({agent.id})")
                            
                            # 记录托管信息
                            if hasattr(agent, 'parent_did') and agent.parent_did:
                                logger.debug(f"  父DID: {agent.parent_did}")
                            if hasattr(agent, 'hosted_info') and agent.hosted_info:
                                logger.debug(f"  托管信息: {agent.hosted_info}")
                                
                    except Exception as e:
                        logger.warning(f"处理用户数据时出错: {e}")
                        continue
            
            self.hosted_agents = hosted_agents
            logger.info(f"发现 {len(hosted_agents)} 个托管Agent")
            return hosted_agents
            
        except Exception as e:
            logger.error(f"发现托管Agent失败: {e}")
            return []
    
    def register_hosted_agent(self, agent: ANPUser, sdk) -> bool:
        """注册托管Agent到SDK"""
        try:
            if sdk and hasattr(sdk, 'register_agent'):
                sdk.register_agent(agent)
                self.agent_registry[agent.id] = agent
                logger.info(f"注册托管Agent: {agent.name}")
                return True
            else:
                logger.error("SDK不支持Agent注册")
                return False
                
        except Exception as e:
            logger.error(f"注册托管Agent失败: {e}")
            return False
    
    def unregister_hosted_agent(self, agent_id: str, sdk) -> bool:
        """从SDK注销托管Agent"""
        try:
            if sdk and hasattr(sdk, 'unregister_agent'):
                sdk.unregister_agent(agent_id)
                if agent_id in self.agent_registry:
                    del self.agent_registry[agent_id]
                logger.info(f"注销托管Agent: {agent_id}")
                return True
            else:
                logger.error("SDK不支持Agent注销")
                return False
                
        except Exception as e:
            logger.error(f"注销托管Agent失败: {e}")
            return False
    
    def get_hosted_agent_info(self, agent: ANPUser) -> Dict[str, Any]:
        """获取托管Agent详细信息"""
        try:
            info = {
                'id': agent.id,
                'name': getattr(agent, 'name', 'Unknown'),
                'is_hosted': getattr(agent, 'is_hosted_did', False),
                'parent_did': getattr(agent, 'parent_did', None),
                'hosted_info': getattr(agent, 'hosted_info', None),
                'host': getattr(agent, 'host', None),
                'port': getattr(agent, 'port', None),
                'created_at': None,
                'status': 'active'
            }
            
            # 尝试获取创建时间
            if hasattr(agent, 'user_data') and agent.user_data:
                user_data_path = getattr(agent.user_data, 'user_data_path', None)
                if user_data_path:
                    import os
                    try:
                        stat = os.stat(user_data_path)
                        info['created_at'] = stat.st_ctime
                    except:
                        pass
            
            return info
            
        except Exception as e:
            logger.error(f"获取托管Agent信息失败: {e}")
            return {}
    
    def filter_hosted_agents(self, agents: List[ANPUser], 
                           filter_criteria: Dict[str, Any]) -> List[ANPUser]:
        """根据条件过滤托管Agent"""
        try:
            filtered_agents = []
            
            for agent in agents:
                match = True
                
                # 检查父DID过滤条件
                if 'parent_did' in filter_criteria:
                    expected_parent = filter_criteria['parent_did']
                    actual_parent = getattr(agent, 'parent_did', None)
                    if actual_parent != expected_parent:
                        match = False
                
                # 检查主机过滤条件
                if 'host' in filter_criteria:
                    expected_host = filter_criteria['host']
                    actual_host = getattr(agent, 'host', None)
                    if actual_host != expected_host:
                        match = False
                
                # 检查端口过滤条件
                if 'port' in filter_criteria:
                    expected_port = filter_criteria['port']
                    actual_port = getattr(agent, 'port', None)
                    if actual_port != expected_port:
                        match = False
                
                # 检查名称模式过滤条件
                if 'name_pattern' in filter_criteria:
                    pattern = filter_criteria['name_pattern']
                    agent_name = getattr(agent, 'name', '')
                    if pattern not in agent_name:
                        match = False
                
                if match:
                    filtered_agents.append(agent)
            
            logger.debug(f"过滤结果: {len(filtered_agents)}/{len(agents)} 个Agent符合条件")
            return filtered_agents
            
        except Exception as e:
            logger.error(f"过滤托管Agent失败: {e}")
            return agents
    
    def get_hosted_agents_summary(self) -> Dict[str, Any]:
        """获取托管Agent摘要信息"""
        try:
            summary = {
                'total_count': len(self.hosted_agents),
                'registered_count': len(self.agent_registry),
                'agents_by_host': {},
                'agents_by_parent': {},
                'active_agents': []
            }
            
            for agent in self.hosted_agents:
                # 按主机分组
                host = getattr(agent, 'host', 'unknown')
                if host not in summary['agents_by_host']:
                    summary['agents_by_host'][host] = 0
                summary['agents_by_host'][host] += 1
                
                # 按父DID分组
                parent_did = getattr(agent, 'parent_did', 'unknown')
                if parent_did not in summary['agents_by_parent']:
                    summary['agents_by_parent'][parent_did] = 0
                summary['agents_by_parent'][parent_did] += 1
                
                # 活跃Agent列表
                if agent.id in self.agent_registry:
                    summary['active_agents'].append({
                        'id': agent.id,
                        'name': getattr(agent, 'name', 'Unknown'),
                        'host': host
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"获取托管Agent摘要失败: {e}")
            return {}
    
    async def setup_hosted_agent_handlers(self, agent: ANPUser) -> bool:
        """为托管Agent设置消息处理器"""
        try:
            @agent.register_message_handler("*")
            async def handle_hosted_message(msg):
                """托管Agent通用消息处理器"""
                logger.debug(f"[{agent.name}] 收到消息: {msg}")
                
                # 构建回复消息
                reply_content = f"这是来自托管Agent {agent.name} 的自动回复"
                
                # 如果消息包含内容，添加到回复中
                if isinstance(msg, dict) and 'content' in msg:
                    reply_content += f"，已收到消息: {msg['content']}"
                
                return {
                    "reply": reply_content,
                    "timestamp": self._get_current_timestamp(),
                    "agent_id": agent.id,
                    "agent_name": agent.name
                }
            
            logger.info(f"托管Agent {agent.name} 消息处理器设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置托管Agent消息处理器失败: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def test_hosted_agent_communication(self, agent: ANPUser, 
                                            target_agent: ANPUser, 
                                            message: str) -> Dict[str, Any]:
        """测试托管Agent通信"""
        try:
            from anp_open_sdk_framework.adapter.anp_service.agent_message_p2p import agent_msg_post
            
            # 发送测试消息
            response = await agent_msg_post(None, agent.id, target_agent.id, message)
            
            result = {
                'success': True,
                'sender': agent.id,
                'receiver': target_agent.id,
                'message': message,
                'response': response,
                'timestamp': self._get_current_timestamp()
            }
            
            logger.info(f"托管Agent通信测试成功: {agent.name} -> {target_agent.name}")
            return result
            
        except Exception as e:
            logger.error(f"托管Agent通信测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'sender': agent.id,
                'receiver': target_agent.id,
                'message': message,
                'timestamp': self._get_current_timestamp()
            }
    
    def cleanup_hosted_agents(self, sdk) -> int:
        """清理所有托管Agent"""
        try:
            cleanup_count = 0
            
            for agent_id in list(self.agent_registry.keys()):
                if self.unregister_hosted_agent(agent_id, sdk):
                    cleanup_count += 1
            
            self.hosted_agents.clear()
            self.agent_registry.clear()
            
            logger.info(f"清理完成，注销了 {cleanup_count} 个托管Agent")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"清理托管Agent失败: {e}")
            return 0
