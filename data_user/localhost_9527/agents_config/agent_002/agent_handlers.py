from starlette.responses import JSONResponse
from anp_open_sdk_framework.local_methods.local_methods_decorators import local_method, register_local_methods_to_agent


async def hello_handler( request, message ):
    """
    这是一个打招呼的API，传入message参数即可返回问候语。
    """
    agent_name = request.state.agent.name
    return {
        "msg": f"{agent_name}的/hello接口收到请求:",
        "inbox": message
    }

async def info_handler(request_data, request):
    agent = getattr(request.state, "agent", None)
    return JSONResponse(
        content={
            "msg": f"{agent.name}的/info接口收到请求:",
            "param": request_data.get("params")
        },
        status_code=200
    )
    
    
@local_method(description="计算两个数的和", tags=["math", "calculator"])
def calculate_sum(a: float, b: float):
    return {"result": a + b, "operation": "add"}

