# anp_open_sdk_framework/transports/http_transport.py
import aiohttp
from typing import Optional, Dict, Any
from anp_open_sdk.core.base_transport import BaseTransport, RequestContext, ResponseContext

class HttpTransport(BaseTransport):
    """使用aiohttp实现网络传输。"""
    async def send(self, request: RequestContext) -> ResponseContext:
        async with aiohttp.ClientSession(headers=request.headers) as session:
            async with session.request(
                method=request.method,
                url=request.url,
                json=request.json_data
            ) as response:
                try:
                    json_data = await response.json()
                    text_data = None
                except Exception:
                    json_data = None
                    text_data = await response.text()

                return ResponseContext(
                    status_code=response.status,
                    headers=dict(response.headers),
                    json_data=json_data,
                    text_data=text_data
                )