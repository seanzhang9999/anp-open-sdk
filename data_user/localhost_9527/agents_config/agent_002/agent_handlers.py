from starlette.responses import JSONResponse


async def hello_handler( request, message ):
    """
    This is a greeting.API，InputmessageThe parameter can return a greeting.。
    """
    agent_name = request.state.agent.name
    return {
        "msg": f"{agent_name}Of/helloThe interface has received the request.:",
        "inbox": message
    }

async def info_handler(request_data, request):
    agent = getattr(request.state, "agent", None)
    return JSONResponse(
        content={
            "msg": f"{agent.name}Of/infoThe interface has received the request.:",
            "param": request_data.get("params")
        },
        status_code=200
    )