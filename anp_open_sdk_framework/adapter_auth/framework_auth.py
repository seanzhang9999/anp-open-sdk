# anp_open_sdk_framework/auth/framework_auth.py
from typing import Optional, Dict, Any, Tuple
from anp_open_sdk.core.auth_flow import AuthFlowManager
from anp_open_sdk.core.base_user_data import BaseUserDataManager
from anp_open_sdk.core.base_transport import BaseTransport
from .did_resolver_wba import FrameworkDIDResolver # 导入我们新的解析器


class FrameworkAuthManager:
    """
    框架层的认证管理器，负责组装和执行完整的认证流程。
    """

    def __init__(self, user_data_manager: BaseUserDataManager, transport: BaseTransport):
        self.user_data_manager = user_data_manager
        self.transport = transport
        self.resolver = FrameworkDIDResolver(transport, user_data_manager)

    async def authenticated_request(self, caller_did: str, target_did: str, url: str, method: str, json_data: Optional[Dict] = None) -> Any:
        caller_user_data = self.user_data_manager.get_user_data(caller_did)
        if not caller_user_data:
            raise ValueError(f"Caller DID not found: {caller_did}")

        # --- 关键修复 ---
        # 框架层负责I/O：在将user_data传递给核心层之前，确保其已从文件加载到内存。
        try:
            if not hasattr(caller_user_data, 'did_doc') or not caller_user_data.did_doc:
                with open(caller_user_data.did_document_path, 'r', encoding='utf-8') as f:
                    caller_user_data.did_doc = json.load(f)

            if not hasattr(caller_user_data, 'private_key') or not caller_user_data.private_key:
                with open(caller_user_data.did_private_key_file_path, 'r', encoding='utf-8') as f:
                    caller_user_data.private_key = f.read()
        except (IOError, AttributeError, json.JSONDecodeError) as e:
            raise IOError(f"无法从路径加载 {caller_did} 的认证资料: {e}")

        # 实例化纯净的认证流程管理器，并注入解析器
        flow_manager = AuthFlowManager(caller_user_data, self.resolver)

        # 1. 首次尝试：使用双向认证
        request_context = await flow_manager.prepare_request_context(
            target_did, url, method, json_data, use_two_way_auth=True
        )
        response_context = await self.transport.send(request_context)

        # 2. 检查是否需要回退到单向认证
        if response_context.status_code in [401, 403]:
            # 收到401/403，可能是对方不支持双向认证，按旧逻辑回退
            request_context_oneway = await flow_manager.prepare_request_context(
                target_did, url, method, json_data, use_two_way_auth=False
            )
            response_context = await self.transport.send(request_context_oneway)

        # 3. 处理最终的响应
        auth_result = await flow_manager.process_response(response_context, target_did)

        if not auth_result.is_successful:
            raise Exception(f"Authentication failed or request failed: {auth_result.error_message} - Body: {auth_result.body}")

        # 4. 执行副作用：存储Token
        if auth_result.token_to_store:
            caller_user_data.store_token_from_remote(target_did, auth_result.token_to_store, 3600)

        return auth_result.body