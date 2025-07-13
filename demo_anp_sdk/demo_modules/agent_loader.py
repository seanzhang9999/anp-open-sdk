from typing import List, Optional
import logging

from anp_sdk.anp_user import ANPUser

logger = logging.getLogger(__name__)
from anp_server.anp_server import ANP_Server
from anp_sdk.anp_sdk_user_data import LocalUserDataManager
from anp_sdk.config import get_global_config


class DemoAgentLoader:
    """演示用Agent加载器"""
    
    @staticmethod
    def load_demo_agents(sdk: ANP_Server) -> List[ANPUser]:
        """加载演示用的智能体"""
        user_data_manager: LocalUserDataManager = sdk.user_data_manager
        config = get_global_config()

        agent_names = [
            config.anp_sdk.agent.demo_agent1,
            config.anp_sdk.agent.demo_agent2,
            config.anp_sdk.agent.demo_agent3
        ]

        agents = []
        for agent_name in agent_names:
            if not agent_name:
                continue

            user_data = user_data_manager.get_user_data_by_name(agent_name)
            if user_data:
                agent = ANPUser.from_name(agent_name)
                agents.append(agent)
            else:
                logger.warning(f'未找到预设名字={agent_name} 的用户数据')
        return agents

    @staticmethod
    def find_hosted_agent(sdk: ANP_Server, user_datas) -> Optional[ANPUser]:
        """查找托管的智能体"""
        for user_data in user_datas:
            agent = ANPUser(sdk, user_data.did)
            if agent.is_hosted_did:
                logger.debug(f"hosted_did: {agent.id}")
                logger.debug(f"parent_did: {agent.parent_did}")
                logger.debug(f"hosted_info: {agent.hosted_info}")
                return agent
        return None

