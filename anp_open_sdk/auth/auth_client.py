import json
import logging
import warnings
from typing import Optional, Dict, Tuple, Any

# 核心变化：移除了对 aiohttp, LocalAgent, LocalUserDataManager 等的直接依赖
# 这些现在都由框架层处理
from .did_auth_base import BaseDIDAuthenticator
from anp_open_sdk.auth_methods.wba.implementation import create_pure_authenticator
from aiohttp import ClientResponse # 暂时保留以兼容 handle_response

logger = logging.getLogger(__name__)

# create_authenticator 现在应该使用纯净的实现
# 注意：它需要一个 DIDResolver，这将在框架层被注入
def create_authenticator(resolver) -> BaseDIDAuthenticator:
    # 这个函数现在更像一个工厂，根据配置选择不同的纯净认证器
    return create_pure_authenticator(resolver)

# ---------------------------------------------------------------------------
# 旧的 AgentAuthManager 和 agent_auth_two_way_v2 函数可以被标记为 @deprecated
# 或者直接删除，这里我们选择删除它们以保持整洁。
# ---------------------------------------------------------------------------

async def agent_auth_request(
    caller_agent: str,
    target_agent: str,
    request_url: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    use_two_way_auth: bool = True,  # 添加 use_two_way_auth 参数用于兼容
    # use_two_way_auth 和 auth_method 参数现在由内部逻辑处理
) -> Tuple[int, Any, str, bool]:
    """
      **[已废弃]** 通用认证函数。请迁移到使用 anp_open_sdk_framework.auth.AuthClient 类。

      这个函数现在是一个兼容性包装器，它会在内部创建所有依赖项，
      效率较低。为了获得最佳性能和灵活性，请在您的应用程序中创建
      一个 AuthClient 的单例实例。
      """
    warnings.warn(
        "`agent_auth_request` is deprecated and will be removed in a future version. "
        "Please use the `AuthClient` class from `anp_open_sdk_framework.auth.auth_client`.",
        DeprecationWarning,
        stacklevel=2
    )

    # 为了向后兼容，在函数内部临时创建所有实例
    # 这是一种反模式，但可以确保旧代码还能运行
    try:
        from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import  LocalUserDataManager
        from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
        from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
        from anp_open_sdk_framework.auth.auth_client import AuthClient

        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)

        return await auth_client.authenticated_request(
            caller_agent=caller_agent,
            target_agent=target_agent,
            request_url=request_url,
            method=method,
            json_data=json_data
        )
    except Exception as e:
        logger.error(f"兼容模式下的认证请求失败: {e}", exc_info=True)
        return 500, {"error": str(e)}, f"Authentication failed in compatibility mode: {e}", False


async def handle_response(response: Any) -> Dict:
    """
    这个工具函数与具体认证逻辑无关，可以保留。
    它负责将不同类型的响应（dict, aiohttp.ClientResponse）统一处理为字典。
    """
    if isinstance(response, dict):
        return response
    elif isinstance(response, ClientResponse):
        try:
            if response.status >= 400:
                error_text = await response.text()
                logger.error(f"HTTP错误 {response.status}: {error_text}")
                return {"error": f"HTTP {response.status}", "message": error_text}
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                text = await response.text()
                logger.warning(f"非JSON响应，Content-Type: {content_type}")
                return {"content": text, "content_type": content_type}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            text = await response.text()
            return {"error": "JSON解析失败", "raw_text": text}
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            return {"error": str(e)}
    else:
        logger.error(f"未知响应类型: {type(response)}")
        return {"error": f"未知类型: {type(response)}"}

# agent_token_request 函数现在是多余的，因为Token逻辑已经整合到
# AuthFlowManager 和 FrameworkAuthManager 中，可以安全地移除。