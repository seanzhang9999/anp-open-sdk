import logging

from anp_server_framework.agent_decorator import agent_api, agent_message_handler
from .agent_handlers import handle_text_message, add

logger = logging.getLogger(__name__)

def register(agent):
    """注册 Calculator Agent 的消息处理器和API处理器"""
    logger.info(f"  -> 注册 {agent.name} 的API处理器...")
    
    # 先注册API处理器（重要的功能）
    agent_api(agent,"/add")(add)
    logger.info(f"  -> {agent.name} API处理器注册完成")
    
    # 再尝试注册消息处理器（可选功能）
    logger.info(f"  -> 注册 {agent.name} 的消息处理器...")
    try:
        if "text" not in agent.message_handlers:
            agent_message_handler(agent,"text")(handle_text_message)
        else:
            logger.warning(f"⚠️  消息类型 'text' 已有处理器，跳过注册")
        logger.info(f"  -> {agent.name} 消息处理器注册完成")
    except PermissionError as e:
        logger.info(f"ℹ️ 预期行为: {e}")
        logger.info(f"✅ {agent.name} 消息处理器注册被跳过 (共享DID非主Agent)")