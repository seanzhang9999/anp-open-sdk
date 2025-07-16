import logging
logger = logging.getLogger(__name__)

async def add(request_data, request):
    """计算两个数的和"""
    try:
        # 从request_data中提取参数
        params = request_data.get('params', {})
        a = float(params.get('a', 0))
        b = float(params.get('b', 0))
        
        result = a + b
        logger.info(f"  -> Calculator Agent: Performed {a} + {b} = {result}")
        return {"result": result}
    except (ValueError, TypeError) as e:
        logger.error(f"Calculator Agent: 参数错误 - {e}")
        return {
            "error": f"参数错误: {str(e)}",
            "expected_format": {"params": {"a": 2.88888, "b": 999933.4445556}}
        }

# 消息处理器
async def handle_text_message(content):
    logger.info(f"Calculator Agent 收到text消息: {content}")
    return {"reply": f"Calculator Agent 回复: 确认收到消息 '{content}'，我是计算器智能体，可以帮您进行数学计算！"}

# 这个简单的Agent不需要初始化或清理，所以我们省略了这些函数
