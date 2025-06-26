from starlette.responses import JSONResponse


async def hello_handler( request,request_data):
    agent = getattr(request.state, "agent", None)
    return JSONResponse(
        content={
            "msg": f"{agent.name}Of/helloThe interface has received the request.:",
            "param": request_data.get("params")
        },
        status_code=200
    )

async def info_handler(request, request_data):
    agent = getattr(request.state, "agent", None)
    return JSONResponse(
        content={
            "msg": f"{agent.name}Of/infoThe interface has received the request.:",
            "param": request_data.get("params")
        },
        status_code=200
    )