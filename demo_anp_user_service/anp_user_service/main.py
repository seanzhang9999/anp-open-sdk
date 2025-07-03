from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from anp_user_service.app.routers import auth, chat, agents
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="ANP User Service with Agent Integration")

# CORS (Cross-Origin Resource Sharing)
# Allow your Chrome extension to call this API
# Replace "chrome-extension://<YOUR_EXTENSION_ID>" with your actual extension ID
# or use "*" for development (less secure).
origins = [
    "http://localhost", # If testing UI locally
    "http://localhost:8080", # Common dev server port
    "null", # For local file testing if popup is opened directly
    # "chrome-extension://your_chrome_extension_id_here" # IMPORTANT for production
    "chrome-extension://djlkliaeodleddflahameeolknjgikdl"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/agent", tags=["Agent Chat"])
app.include_router(agents.router, prefix="/agents", tags=["Agent Management"])

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 Starting ANP User Service...")
    # 初始化智能体服务
    from anp_user_service.app.services.agent_service import agent_service_manager
    success = await agent_service_manager.initialize_agents()
    if success:
        logger.info("✅ Agent service initialized successfully")
    else:
        logger.error("❌ Failed to initialize agent service")
    
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 Shutting down ANP User Service...")
    # 清理智能体服务
    from anp_user_service.app.services.agent_service import agent_service_manager
    await agent_service_manager.cleanup()

@app.get("/")
async def root():
    return {"message": "Welcome to the ANP User Service with Agent Integration!"}

# To run the backend (from mcp-chat-extension/backend_py directory):
# Make sure anp_open_sdk is in PYTHONPATH if not installed
# Example: export PYTHONPATH=$PYTHONPATH:$(pwd)/..
# Then: uvicorn app.main:app --reload --port 8000