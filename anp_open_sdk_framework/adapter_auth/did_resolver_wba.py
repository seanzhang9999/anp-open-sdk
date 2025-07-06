# anp_open_sdk_framework/auth/did_resolver.py
from typing import Optional
from anp_open_sdk.auth.did_auth_base import BaseDIDResolver
from anp_open_sdk.auth.schemas import DIDDocument
from anp_open_sdk.core.base_transport import BaseTransport, RequestContext


class FrameworkDIDResolver(BaseDIDResolver):
    """
    框架层的DID解析器，负责通过网络或本地缓存获取DID文档。
    """

    def __init__(self, transport: BaseTransport, user_data_manager):
        self.transport = transport
        self.user_data_manager = user_data_manager

    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        # 1. 优先从本地加载 (如果存在)
        local_user = self.user_data_manager.get_user_data(did)
        if local_user:
            return DIDDocument.from_dict(local_user.did_document)

        # 2. 如果本地没有，通过网络获取
        #    (这里的URL构造逻辑需要根据WBA规范确定)
        #    例如: http://{host}:{port}/.well-known/did.json
        #    这是一个简化的示例
        from urllib.parse import urlparse
        parsed_did = urlparse(did.replace("did:wba:", "http://").replace("%3A", ":"))
        did_doc_url = f"{parsed_did.scheme}://{parsed_did.netloc}/.well-known/did.json"

        request = RequestContext(method="GET", url=did_doc_url, headers={})
        response = await self.transport.send(request)

        if response.status_code == 200 and response.json_data:
            return DIDDocument.from_dict(response.json_data)

        return None