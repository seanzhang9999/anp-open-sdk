import logging
from .agent_handlers import chat_completion, handle_message, handle_text_message

logger = logging.getLogger(__name__)

def register(agent):
    """注册 LLM Agent 的API处理器和消息处理器"""
    logger.info(f"  -> 注册 {agent.name} 的API处理器...")
    
    # 注册API处理器 - 对于共享DID的Agent，注册原始路径
    agent.expose_api("/chat", chat_completion, methods=["POST"])
    
    # 注册消息处理器
    logger.info(f"  -> 注册 {agent.name} 的消息处理器...")
    agent.register_message_handler("*", handle_message, agent_name=agent.name)
    agent.register_message_handler("text", handle_text_message, agent_name=agent.name)
    
    logger.info(f"  -> {agent.name} API处理器和消息处理器注册完成")
