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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse import urlencode, quote

from anp_foundation.anp_user import ANPUser, RemoteANPUser
from anp_foundation.auth.auth_client import send_authenticated_request
from anp_transformer.anp_service.agent_api_call import response_to_dict


async def agent_msg_post(caller_agent: str, target_agent: str, content: str, message_type: str = "text"):
    """发送消息给目标智能体"""
    caller_agent_obj = ANPUser.from_did(caller_agent)
    target_agent_obj = RemoteANPUser(target_agent)
    url_params = {
        "req_did": caller_agent_obj.id,
        "resp_did": target_agent_obj.id
    }
    url_params = urlencode(url_params)
    target_agent_path = quote(target_agent)
    msg = {
        "req_did": caller_agent_obj.id,
        "message_type": message_type,
        "content": content
    }
    # 使用统一路由：/agent/api/{did}/message/post
    url = f"http://{target_agent_obj.host}:{target_agent_obj.port}/agent/api/{target_agent_path}/message/post?{url_params}"

    status, response, info, is_auth_pass = await send_authenticated_request(
        caller_agent, target_agent, url, method="POST", json_data=msg
    )
    return  await response_to_dict(response)
