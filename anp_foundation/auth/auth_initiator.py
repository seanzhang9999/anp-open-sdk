import json
import logging
from contextlib import nullcontext
from urllib.parse import unquote

from agent_connect.authentication import resolve_did_wba_document

from anp_foundation.did.agent_connect_hotpatch.authentication.did_wba import extract_auth_header_parts_two_way, \
    verify_auth_header_signature_two_way
from ..anp_user_local_data import get_user_data_manager

from anp_foundation.did.did_tool import AuthenticationContext, verify_timestamp, \
     create_did_auth_header_from_user_data

logger = logging.getLogger(__name__)

import string
from typing import Optional, Dict, Tuple, Any

import aiohttp

from ..anp_user import ANPUser



async def send_authenticated_request(
    caller_agent: str,target_agent: str,request_url,
    method: str = "GET", json_data: Optional[Dict] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    use_two_way_auth: bool = True,
) -> Tuple[int, str, str, bool]:
    """通用认证函数，自动优先用本地token，否则走DID认证，token失效自动fallback"""


    """
    暂时屏蔽token分支 token方案需要升级保证安全
    caller_agent_obj = LocalAgent.from_did(caller_credentials.did_document.did)
    token_info = caller_agent_obj.contact_manager.get_token_to_remote(target_agent)
    from datetime import datetime, timezone
    if token_info and not token_info.get("is_revoked", False):
        expires_at = token_info.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < expires_at:
            token = token_info["token"]
            status, response_data = await agent_token_request(
                request_url, token, caller_credentials.did_document.did, target_agent, method, json_data
            )
            if status == 401 or status == 403:
                if hasattr(caller_agent_obj.contact_manager, 'revoke_token_from_remote'):
                    caller_agent_obj.contact_manager.revoke_token_from_remote(target_agent)
            else:
                return status, response_data, "token认证请求", status == 200
    """
    status, response, info, is_auth_pass = await _execute_wba_auth_flow(
        caller_agent,target_agent,request_url,
        method,json_data,
        custom_headers,
        use_two_way_auth
    )
    logger.info(f"request:{request_url} \n status: {status}, ,auth_status {is_auth_pass} \ninfo: {info}")

    return  status, response, info, is_auth_pass




async def _execute_wba_auth_flow(
    caller_did:str,target_did: str,request_url: str,
    method: str = "GET",json_data: Optional[Dict] = None,
    custom_headers: Dict[str, str] = None,
    use_two_way_auth: bool = True
) -> Tuple[int, str, str, bool]:
    if custom_headers is None:
        custom_headers = {}
    context = AuthenticationContext(
        caller_did=caller_did,target_did=target_did,request_url=request_url,
        method=method,custom_headers=custom_headers,
        json_data=json_data,
        use_two_way_auth=use_two_way_auth
    )
    caller_agent = ANPUser.from_did(context.caller_did)
    try:
        status_code, response_auth_header, response_data = await _send_wba_http_request(
            context
        )
        if status_code == 401 or status_code == 403:
            context.use_two_way_auth = False
            status_code, response_auth_header, response_data = await _send_wba_http_request(
                context
            )
            if status_code == 200:
                auth_value, token = _parse_token_from_response(response_auth_header)
                if token:
                    if auth_value == "单向认证":
                        caller_agent.contact_manager.store_token_from_remote(context.target_did, token)
                        message = f"单向认证成功! 已保存 {context.target_did} 颁发的token:{token}"
                        return status_code, response_data, message, True
                    else:
                        message = f"返回200，但是token单向认证失败，可能是其他认证token，认证失败"
                        return status_code, response_data, message, False
                else:
                    message = "返回200，没有token，可能是无认证页面"
                    return status_code, response_data, message, True
            elif status_code == 401 or status_code == 403:
                message = "双向和单向认证均返回401/403，认证失败"
                return status_code, response_data , message, False
            else:
                token = None
                if status_code != 404:
                    auth_value, token = _parse_token_from_response(response_auth_header)
                if token:
                    if auth_value == "单向认证":
                        caller_agent.contact_manager.store_token_from_remote(context.target_did, token)
                        message = f"未返回200，但是单向认证成功!可能有逻辑层错误，已保存 {context.target_did} 颁发的token:{token}"
                        return status_code, response_data, message, True
                    else:
                        message = f"未返回200，未返回401/403，token单向认证失败，可能是其他认证token，认证失败"
                        return status_code, response_data, message, False
                else:
                    message = " 未返回200，未返回401/403，没有token，可能是其他错误"
                    return status_code, response_data, message, True
        else:
            if status_code == 200:
                auth_value, token = _parse_token_from_response(response_auth_header)
                if token:
                    response_auth_header = json.loads(response_auth_header.get("Authorization"))
                    response_auth_header = response_auth_header.get("resp_did_auth_header")
                    response_auth_header = response_auth_header.get("Authorization")
                    if await _verify_response_auth_header(response_auth_header):
                        caller_agent.contact_manager.store_token_from_remote(context.target_did, token)
                        message = f"DID双向认证成功! 已保存 {context.target_did} 颁发的token"
                        return status_code, response_data, message, True
                    else:
                        message = f"返回200，返回token，但是resp_did返回认证验证失败! 状态: {status_code}\n响应: {response_data}"
                        return status_code, response_data, message, False
                else:
                    message = f"返回200，无token，可能是无认证页面 状态: {status_code}\n响应: {response_data}"
                    return status_code, response_data, message, True
            else:
                token = None
                if status_code != 404:
                    auth_value, token = _parse_token_from_response(response_auth_header)
                if token:
                    if await _verify_response_auth_header(response_auth_header):
                        caller_agent.contact_manager.store_token_from_remote(context.target_did, token)
                        message = f"未返回200，未返回401/403，但是DID双向认证成功! 应该是逻辑层有错误，已保存 {context.target_did} 颁发的token:{token}"
                        return status_code, response_data, message, True
                    else:
                        message = f"未返回200，未返回401/403，resp_did返回认证验证失败! 状态: {status_code}\n响应: {response_data}"
                        return status_code, response_data, message, False
                else:
                    message = f"未返回200，未返回401/403，未返回token，应有其他错误！ 状态: {status_code}\n响应: {response_data}"
                    return status_code, response_data, message, False

    except Exception as e:
        logger.error(f"认证过程中发生错误: {e}")
        return 500, '', f"请求中发生错误: {str(e)}", False


async def _send_request_with_token(target_url: str, token: str, sender_did: str, targeter_did: string, method: str = "GET",
                             json_data: Optional[Dict] = None) -> Tuple[int, Dict[str, Any]]:
    try:

        #当前方案需要后续改进，当前并不安全
        headers = {
            "Authorization": f"Bearer {token}",
            "req_did": f"{sender_did}",
            "resp_did": f"{targeter_did}"
        }

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(
                    target_url,
                    headers=headers
                ) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    return status, response_data
            elif method.upper() == "POST":
                async with session.post(
                    target_url,
                    headers=headers,
                    json=json_data
                ) as response:
                    status = response.status
                    response_data = await response.json() if status == 200 else {}
                    return status, response_data
            else:
                logger.debug(f"Unsupported HTTP method: {method}")
                return 400, {"error": "Unsupported HTTP method"}
    except Exception as e:
        logger.debug(f"Error sending request with token: {e}")
        return 500, {"error": str(e)}



def _parse_token_from_response(response_header: Dict) -> Tuple[Optional[str], Optional[str]]:
    """从响应头中获取DIDAUTHHeader

    Args:
        response_header: 响应头字典

    Returns:
        Tuple[str, str]: (did_auth_header, token) 双向认证头和访问令牌
    """
    if "Authorization" not in response_header:
        return "没有Auth头", None


    auth_value = response_header["Authorization"]
    if isinstance(auth_value, str):
        import re
        match = re.match(r'^bearer\s+(.+)$', auth_value, re.IGNORECASE)
        if match:
            token = match.group(1)
            logger.debug("获得单向认证令牌，兼容无双向认证的服务")
            return "单向认证", token
            # 如果不是Bearer格式，尝试解析为JSON
        try:
            auth_data = json.loads(auth_value)
            # 解析后应该是字典格式
            if isinstance(auth_data, dict):
                token = auth_data.get("access_token")
                did_auth_header = auth_data.get("resp_did_auth_header", {}).get("Authorization")
                if did_auth_header and token:
                    return "双向认证", token
                else:
                    return "AuthDict无法识别", None
            else:
                return "JSON解析后格式错误", None
        except json.JSONDecodeError:
            return ("JSON解析AuthToken失败"), None
    else:
        try:
            auth_value= json.loads(auth_value)
            token = auth_value.get("access_token")
            did_auth_header =auth_value.get("resp_did_auth_header", {}).get("Authorization")
            if did_auth_header and token:
                logger.debug("令牌包含双向认证信息，进行双向校验")
                return "双向认证", token
            else:
                logger.error("[错误] 解析失败，缺少必要字段" + str(auth_value))
                return "AuthDict无法识别", None
        except Exception as e:
            logger.error("[错误] 处理 Authorization 字典时出错: " + str(e))
            return "JSON解析AuthDict失败", None



async def _verify_response_auth_header(auth_value: str) -> bool:

    """检查响应头中的DIDAUTHHeader是否正确

    Args:
        auth_value: 认证头字符串

    Returns:
        bool: 验证是否成功
    """
    try:
        # 处理CIMultiDictProxy类型的headers
        if hasattr(auth_value, 'get') and callable(auth_value.get):
            # 如果auth_value是headers对象，尝试获取Authorization头
            auth_header = auth_value.get('Authorization')
            if auth_header:
                auth_value = auth_header
            else:
                logger.error("在headers中未找到Authorization头")
                return False

        # 尝试解析JSON格式的auth_value
        if isinstance(auth_value, str) and auth_value.startswith('{') and auth_value.endswith('}'):
            try:
                auth_json = json.loads(auth_value)
                # 检查是否有嵌套的Authorization头
                if 'resp_did_auth_header' in auth_json and 'Authorization' in auth_json['resp_did_auth_header']:
                    auth_value = auth_json['resp_did_auth_header']['Authorization']
            except json.JSONDecodeError:
                # 如果不是有效的JSON，保持原样
                pass

        # 确保auth_value是字符串
        if not isinstance(auth_value, str):
            auth_value = str(auth_value)
        header_parts = extract_auth_header_parts_two_way(auth_value)
    except Exception as e:
        logger.error(f"无法从AuthHeader中解析信息: {e}")
        return False

    if not header_parts:
        logger.error("AuthHeader格式错误")
        return False

    did, nonce, timestamp, resp_did, keyid, signature = header_parts
    logger.debug(f"用 {did}的{keyid}检验")

    is_valid, error_msg = verify_timestamp(timestamp)
    if not is_valid:
        return False


    # 尝试使用自定义解析器解析DID文档
    did_document = await _resolve_did_document_insecurely(did)

    # 如果自定义解析器失败，尝试使用标准解析器
    if not did_document:
        try:
            did_document = await resolve_did_wba_document(did)
        except Exception as e:
            logger.error(f"标准DID解析器也失败: {e}")
            return False

    if not did_document:
        logger.error("Failed to resolve DID document")
        return False

    try:
        # 重新构造完整的授权头
        full_auth_header = auth_value
        # 用固定值测试返回认证，本地没有做http过滤逻辑，直接写即可
        service_domain =  "virtual.WBAback"

        # 调用验证函数
        is_valid, message = verify_auth_header_signature_two_way(
            auth_header=full_auth_header,
            did_document=did_document,
            service_domain=service_domain
        )

        logger.debug(f"签名验证结果: {is_valid}, 消息: {message}")
        return is_valid

    except Exception as e:
        logger.error(f"验证签名时出错: {e}")
        return False


async def _send_wba_http_request(context: AuthenticationContext) -> Tuple[bool, str, Dict[str, Any]]:
    """执行WBA认证请求"""
    import aiohttp


    """执行WBA认证请求"""
    try:
        # 构建认证头
        auth_headers = _build_wba_auth_header(context)
        request_url = context.request_url
        method = getattr(context, 'method', 'GET')
        json_data = getattr(context, 'json_data', None)
        custom_headers = getattr(context, 'custom_headers', None)
        resp_did = getattr(context, 'target_did', None)
        if custom_headers:
            # 合并认证头和自定义头，auth_headers 优先覆盖
            merged_headers = {**custom_headers ,**auth_headers}
        else:
            merged_headers = auth_headers
        # 发送带认证头的请求
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(request_url, headers=merged_headers) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_text = await response.text()
                        try:
                            response_data = json.loads(response_text)
                        except Exception:
                            response_data = {"text": response_text}
                            # 检查 Authorization header
                    return status, response.headers, response_data
            elif method.upper() == "POST":
                async with session.post(request_url, headers=merged_headers, json=json_data) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_text = await response.text()
                        try:
                            response_data = json.loads(response_text)
                        except Exception:
                            response_data = {"text": response_text}
                    return status, response.headers, response_data
            else:
                logger.debug(f"Unsupported HTTP method: {method}")
                return False, "",{"error": "Unsupported HTTP method"}
    except Exception as e:
        logger.debug(f"Error in authenticate_request: {e}", exc_info=True)
        return False, "", {"error": str(e)}


async def _resolve_did_document_insecurely(did: str) -> Optional[Dict]:
    """
    解析本地DID文档

    Args:
        did: DID标识符，例如did:wba:localhost%3A8000:wba:user:123456

    Returns:
        Optional[Dict]: 解析出的DID文档，如果解析失败则返回None
    """
    try:
        # logger.debug(f"解析本地DID文档: {did}")

        # 解析DID标识符
        parts = did.split(':')
        if len(parts) < 5 or parts[0] != 'did' or parts[1] != 'wba':
            logger.debug(f"无效的DID格式: {did}")
            return None

        # 提取主机名、端口和用户ID
        hostname = parts[2]
        # 解码端口部分，如果存在
        if '%3A' in hostname:
            hostname = unquote(hostname)  # 将 %3A 解码为 :

        path_segments = parts[3:]
        user_id = path_segments[-1]
        user_dir = path_segments[-2]

        # logger.debug(f"DID 解析结果 - 主机名: {hostname}, 用户ID: {user_id}")


        http_url = f"http://{hostname}/wba/{user_dir}/{user_id}/did.json"

        # 这里使用异步HTTP请求
        async with aiohttp.ClientSession() as session:
            async with session.get(http_url, ssl=False) as response:
                if response.status == 200:
                    did_document = await response.json()
                    logger.debug(f"通过DID标识解析的{http_url}获取{did}的DID文档")
                    return did_document
                else:
                    logger.debug(f"did本地解析器地址{http_url}获取失败，状态码: {response.status}")
                    return None
    except Exception as e:
        logger.debug(f"解析DID文档时出错: {e}")
        return None


def _build_wba_auth_header(context):
    user_data_manager = get_user_data_manager()
    user_data = user_data_manager.get_user_data(context.caller_did)
    if not user_data:
        raise ValueError(f"Could not find user data for DID: {context.caller_did}")

    # 临时回退到文件路径方式进行调试
    auth_header_builder = create_did_auth_header_from_user_data(user_data)

    if context.use_two_way_auth:
        # 双向认证
        auth_headers = auth_header_builder.get_auth_header_two_way(
            context.request_url, context.target_did
        )
    else:
        # 单向/降级认证
        auth_headers = auth_header_builder.get_auth_header(
            context.request_url
        )
    return auth_headers
