# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote

from aiohttp import ClientResponse

from anp_sdk.anp_user import RemoteANPUser, ANPUser
from anp_sdk.did.did_tool import logger
from anp_sdk.auth.auth_client import send_authenticated_request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

async def agent_api_call(
    caller_agent: str,
    target_agent: str,
    api_path: str,
    params: Optional[Dict] = None,
    method: str = "GET"
) -> Dict:
        """通用方式调用智能体的 API (支持 GET/POST)"""
        caller_agent_obj = ANPUser.from_did(caller_agent)
        target_agent_obj = RemoteANPUser(target_agent)
        target_agent_path = quote(target_agent)
        if method.upper() == "POST":
            req = {"params": params or {}}
            url_params = {
                "req_did": caller_agent_obj.id,
                    "resp_did": target_agent_obj.id
            }
            url_params = urlencode(url_params)
            url = f"http://{target_agent_obj.host}:{target_agent_obj.port}/agent/api/{target_agent_path}{api_path}?{url_params}"
            status, response, info, is_auth_pass = await send_authenticated_request(
                caller_agent, target_agent, url, method="POST", json_data=req
            )
        else:
            url_params = {
                "req_did": caller_agent_obj.id,
                "resp_did": target_agent_obj.id,
                "params": json.dumps(params) if params else ""
            }
            url_params = urlencode(url_params)
            url = f"http://{target_agent_obj.host}:{target_agent_obj.port}/agent/api/{target_agent_path}{api_path}?{url_params}"
            status, response, info, is_auth_pass = await send_authenticated_request(
                caller_agent, target_agent, url, method="GET")
        return await response_to_dict(response)

async def agent_api_call_post(caller_agent: str, target_agent: str, api_path: str, params: Optional[Dict] = None) -> Dict:
    return await agent_api_call(caller_agent, target_agent, api_path, params, method="POST")

async def agent_api_call_get(caller_agent: str, target_agent: str, api_path: str, params: Optional[Dict] = None) -> Dict:
    return await agent_api_call(caller_agent, target_agent, api_path, params, method="GET")


async def response_to_dict(response: Any) -> Dict:
    if isinstance(response, dict):
        return response
    elif isinstance(response, str):
        # 新增：处理字符串响应
        try:
            # 尝试解析为 JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 不是 JSON，返回包装后的字符串
            return {
                "type": "text",
                "content": response,
                "format": "string"
            }
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
        # 尝试将未知类型转换为字符串
        try:
            return {
                "type": "unknown",
                "content": str(response),
                "original_type": str(type(response))
            }
        except Exception as e:
            return {"error": f"无法处理的类型: {type(response)}", "exception": str(e)}
