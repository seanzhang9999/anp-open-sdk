# anp_open_sdk_framework/auth/auth_client.py (新文件)
import logging
from typing import Optional, Dict, Any, Tuple
from ..adapter_auth.framework_auth import FrameworkAuthManager

logger = logging.getLogger(__name__)

class AuthClient:
    """
    一个有状态的认证客户端，封装了所有客户端认证逻辑。
    这是进行认证调用的推荐方式。
    """
    def __init__(self, auth_manager: FrameworkAuthManager):
        """
        在构造函数中注入依赖。

        Args:
            auth_manager: 一个预先配置好的框架层认证管理器实例。
        """
        self.auth_manager = auth_manager
        logger.debug("AuthClient 初始化完成。")

    async def authenticated_request(
        self,
        caller_agent: str,
        target_agent: str,
        request_url: str,
        method: str = "GET",
        json_data: Optional[Dict] = None,
    ) -> Tuple[int, Any, str, bool]:
        """
        执行一个完整的、带认证的请求。
        这个方法取代了旧的全局函数 agent_auth_request。
        """
        try:
            logger.debug(f"发起认证请求: 从 {caller_agent} 到 {target_agent}")
            # 直接使用实例变量中的 auth_manager
            response_body = await self.auth_manager.authenticated_request(
                caller_did=caller_agent,
                target_did=target_agent,
                url=request_url,
                method=method,
                json_data=json_data
            )
            logger.debug(f"认证请求成功，目标: {target_agent}")
            return 200, response_body, "Authentication successful", True
        except Exception as e:
            logger.error(f"认证请求失败: {e}", exc_info=True)
            status_code = getattr(e, 'status_code', 500)
            return status_code, {"error": str(e)}, f"Authentication failed: {e}", False