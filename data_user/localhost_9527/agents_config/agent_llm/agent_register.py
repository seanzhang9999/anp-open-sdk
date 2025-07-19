import logging

from anp_transformer.agent_decorator import agent_api,agent_message_handler
from .agent_handlers import chat_completion, handle_message, handle_text_message

logger = logging.getLogger(__name__)

def register(agent):
    """注册 LLM Agent 的API处理器和消息处理器"""
    logger.info(f"  -> 注册 {agent.name} 的API处理器...")
    
    # 注册API处理器 - 对于共享DID的Agent，注册原始路径
    agent_api(agent,"/chat")(chat_completion)

    # 注册消息处理器
    logger.info(f"  -> 注册 {agent.name} 的消息处理器...")
    
    # 检查是否已有消息处理器，避免冲突
    if "*" not in agent.message_handlers:
        agent_message_handler(agent,"*")(handle_text_message)
    else:
        logger.warning(f"⚠️  消息类型 '*' 已有处理器，跳过注册")
    
    if "text" not in agent.message_handlers:
        agent_message_handler(agent,"text")(handle_text_message)
    else:
        logger.warning(f"⚠️  消息类型 'text' 已有处理器，跳过注册")
    
    logger.info(f"  -> {agent.name} API处理器和消息处理器注册完成")
