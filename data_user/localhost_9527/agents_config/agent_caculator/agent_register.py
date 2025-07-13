import logging
from .agent_handlers import handle_text_message, add

logger = logging.getLogger(__name__)

def register(agent):
    """注册 Calculator Agent 的消息处理器和API处理器"""
    logger.info(f"  -> 注册 {agent.name} 的消息处理器...")
    
    # 注册文本消息处理器
    agent.register_message_handler("text", handle_text_message)
    
    # 注册API处理器 - 对于共享DID的Agent，注册原始路径
    agent.expose_api("/add", add, methods=["POST"])
    
    logger.info(f"  -> {agent.name} 消息处理器和API处理器注册完成")
