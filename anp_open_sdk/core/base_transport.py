# anp_open_sdk/core/base_transport.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class RequestContext:
    """与传输无关的请求上下文。"""
    method: str
    url: str
    headers: Dict[str, str]
    json_data: Optional[Dict[str, Any]] = None

@dataclass
class ResponseContext:
    """与传输无关的响应上下文。"""
    status_code: int
    headers: Dict[str, str]
    json_data: Optional[Dict[str, Any]] = None
    text_data: Optional[str] = None

class BaseTransport(ABC):
    """网络传输的抽象基类。"""
    @abstractmethod
    async def send(self, request: RequestContext) -> ResponseContext: ...