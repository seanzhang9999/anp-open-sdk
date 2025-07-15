import logging
from .agent_handlers import handle_text_message, add

logger = logging.getLogger(__name__)

def register(agent):
    """注册 Calculator Agent 的消息处理器和API处理器"""
    logger.info(f"  -> 注册 {agent.name} 的消息处理器...")
    
    # 注册文本消息处理器
    if "text" not in agent.message_handlers:
        agent.message_handlers["text"] = handle_text_message
    else:
        logger.warning(f"⚠️  消息类型 'text' 已有处理器，跳过注册")
    
    # 注册API处理器 - 对于共享DID的Agent，注册原始路径
    agent.api("/add")(add)
    
    logger.info(f"  -> {agent.name} 消息处理器和API处理器注册完成")
