import asyncio

from anp_open_sdk.service.router.router_agent import wrap_business_handler
from anp_open_sdk_framework.local_methods.local_methods_decorators import local_method, register_local_methods_to_agent


def register(agent):
    """
    Custom Registration Script：For agent Register any API、Message、Events, etc.
    """
    from .agent_handlers import hello_handler, info_handler

    # Registration /hello POST,GET
    agent.expose_api("/hello", wrap_business_handler(hello_handler), methods=["POST","GET"])

    # Registration /info POST
    agent.expose_api("/info", info_handler, methods=["POST"])

    # Register a custom message handler.
    @agent.register_message_handler("text")
    async def custom_text_handler(msg):
        return {"reply": f"Custom registration received a message.: {msg.get('content')}"}

    # You can still register for the event.、Scheduled task、Permission verification, etc.
    # agent.register_group_event_handler(...)
    # agent.add_permission_check(...)
    # ...
    
    
    # Register a local custom method
    # Use decorators to register local methods.
    @local_method(description="Demonstration Method，ReturnagentInformation", tags=["demo", "info"])
    def demo_method():
        return f"This is from {agent.name} Demonstration method"

    @local_method(description="Calculate the sum of two numbers.", tags=["math", "calculator"])
    def calculate_sum(a: float, b: float):
        return {"result": a + b, "operation": "add"}

    @local_method(description="Asynchronous demonstration method", tags=["demo", "async"])
    async def async_demo():
        await asyncio.sleep(0.1)
        return "Result of asynchronous method"

    # Automatically register all marked local methods.
    register_local_methods_to_agent(agent, locals())

    return agent



