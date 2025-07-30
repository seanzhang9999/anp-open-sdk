import asyncio

from anp_runtime.agent_decorator import agent_message_handler, agent_api
from anp_runtime.anp_service.anp_tool import wrap_business_handler
from anp_runtime.local_service.local_methods_decorators import local_method, register_local_methods_to_agent


def register(agent):
    """
    自定义注册脚本：为 agent 注册任意 API、消息、事件等
    """
    from .agent_handlers import hello_handler, info_handler

    # 注册 /hello POST,GET

    agent_api(agent,"/hello")(wrap_business_handler(hello_handler))
    agent_api(agent,"/info")(info_handler)


    ###

    # 注册一个自定义消息处理器
    async def custom_text_handler(content):
        return {"reply": f"自定义注册收到消息: {content}"}
    
    # 使用新的装饰器方式注册消息处理器
    agent_message_handler(agent,"text")(custom_text_handler)
    # 注册群组事件处理器（如果需要）
    async def handle_group_join(group_id, event_type, event_data):
        return {"status": "success", "message": f"处理群组 {group_id} 的 {event_type} 事件"}
    

    
    # 注册一个本地自定义方法
    # 使用装饰器注册本地方法
    @local_method(description="演示方法，返回agent信息", tags=["demo", "info"])
    def demo_method():
        return f"这是来自 {agent.name} 的演示方法"

    @local_method(description="计算两个数的和", tags=["math", "calculator"])
    def calculate_sum(a: float, b: float):
        return {"result": a + b, "operation": "add"}

    @local_method(description="异步演示方法", tags=["demo", "async"])
    async def async_demo():
        await asyncio.sleep(0.1)
        return "异步方法结果"

    # 自动注册所有标记的本地方法
    register_local_methods_to_agent(agent, locals())

    return agent
