from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging

from ..services.agent_service import agent_service_manager
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class AgentCallRequest(BaseModel):
    method_name: str
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

class AgentCallResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

@router.get("/status")
async def get_agent_status(current_user: dict = Depends(get_current_user)):
    """获取智能体服务状态"""
    return {
        "initialized": agent_service_manager.is_initialized,
        "agents_count": len(agent_service_manager.agents),
        "user": current_user["username"]
    }

@router.get("/methods")
async def get_available_methods(current_user: dict = Depends(get_current_user)):
    """获取可用的智能体方法列表"""
    try:
        methods = await agent_service_manager.get_available_methods()
        return {
            "success": True,
            "methods": methods,
            "count": len(methods)
        }
    except Exception as e:
        logger.error(f"Failed to get available methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/call", response_model=AgentCallResponse)
async def call_agent_method(
    request: AgentCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """调用智能体方法"""
    try:
        if not agent_service_manager.is_initialized:
            raise HTTPException(status_code=503, detail="Agent service not initialized")
            
        logger.info(f"User {current_user['username']} calling method: {request.method_name}")
        
        result = await agent_service_manager.call_orchestrator_method(
            request.method_name,
            *request.args,
            **request.kwargs
        )
        
        return AgentCallResponse(success=True, result=result)
        
    except ValueError as e:
        logger.error(f"Method not found: {e}")
        return AgentCallResponse(success=False, error=f"Method not found: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to call agent method: {e}")
        return AgentCallResponse(success=False, error=str(e))

@router.post("/discover")
async def discover_agents(
    publisher_url: str = "http://localhost:9527/publisher/agents",
    current_user: dict = Depends(get_current_user)
):
    """发现智能体"""
    try:
        result = await agent_service_manager.discover_agents(publisher_url)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to discover agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/calculator")
async def run_calculator_demo(current_user: dict = Depends(get_current_user)):
    """运行计算器演示"""
    try:
        result = await agent_service_manager.run_calculator_demo()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run calculator demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/hello")
async def run_hello_demo(current_user: dict = Depends(get_current_user)):
    """运行Hello演示"""
    try:
        result = await agent_service_manager.run_hello_demo()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run hello demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/ai-crawler")
async def run_ai_crawler_demo(current_user: dict = Depends(get_current_user)):
    """运行AI爬虫演示"""
    try:
        result = await agent_service_manager.run_ai_crawler_demo()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run AI crawler demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/ai-root-crawler")
async def run_ai_root_crawler_demo(current_user: dict = Depends(get_current_user)):
    """运行AI根爬虫演示"""
    try:
        result = await agent_service_manager.run_ai_root_crawler_demo()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run AI root crawler demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/agent-002")
async def run_agent_002_demo(current_user: dict = Depends(get_current_user)):
    """运行Agent 002演示"""
    try:
        result = await agent_service_manager.run_agent_002_demo()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run agent 002 demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demo/agent-002-new")
async def run_agent_002_demo_new(current_user: dict = Depends(get_current_user)):
    """运行Agent 002新演示"""
    try:
        result = await agent_service_manager.run_agent_002_demo_new()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to run agent 002 new demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))