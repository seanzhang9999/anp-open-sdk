import json
from datetime import datetime
from json import JSONEncoder

import yaml
import aiohttp
import os
from pathlib import Path
from typing import Dict, Any, Optional

from anp_open_sdk.anp_sdk_agent import LocalAgent
from anp_open_sdk.utils.did_utils import parse_wba_did_host_port
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager
import logging

from anp_open_sdk_framework.auth.auth_client import AuthClient
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller

logger = logging.getLogger(__name__)

from anp_open_sdk.protocol import create_did_wba_auth_header as DIDWbaAuthHeader
from anp_open_sdk.auth.auth_client import agent_auth_request


class ANPTool:
    name: str = "anp_tool"
    description: str = """使用代理网络协议（ANP）与其他智能体进行交互。
1. 使用时需要输入 URL 和 HTTP 方法。
2. URL 可以是标准的 http/https URL，用于远程调用。
3. URL 也可以是 `local://<agent_did>/<method_name>` 格式，用于调用本地注册的方法，这种方式更快。
4. 注意：任何使用 ANPTool 获取的 URL 都必须使用 ANPTool 调用，不要直接调用。
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "(必填) 代理描述文件、API 端点或本地方法调用的 URI",
            },
            "method": {
                "type": "string",
                "description": "(可选) 远程调用时的 HTTP 方法，如 GET、POST 等，默认为 GET",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "default": "GET",
            },
            "headers": {
                "type": "object",
                "description": "(可选) 远程调用时的 HTTP 请求头",
                "default": {},
            },
            "params": {
                "type": "object",
                "description": "(可选) 远程调用时的 URL 查询参数，或本地调用的部分参数",
                "default": {},
            },
            "body": {
                "type": "object",
                "description": "(可选) 远程 POST/PUT 请求的请求体，或本地调用的部分参数",
            },
        },
        "required": ["url"],
    }

    # 声明 auth_client 和 local_caller 字段
    auth_client: Optional[AuthClient] = None
    local_caller: Optional[LocalMethodsCaller] = None

    def __init__(
            self,
            auth_client: Optional[AuthClient] = None,
            local_caller: Optional[LocalMethodsCaller] = None,
            did_document_path: Optional[str] = None,
            private_key_path: Optional[str] = None,
            **data,
    ):
        """
                使用 AuthClient 和本地调用器初始化 ANPTool

                参数:
                    auth_client (AuthClient, 可选): 用于执行认证请求的客户端实例。
                    local_caller (LocalMethodsCaller, 可选): 用于执行本地方法的调用器实例。
                    did_document_path (str, 可选): DID文档路径，用于向后兼容。
                    private_key_path (str, 可选): 私钥路径，用于向后兼容。
                """
        # 移除super().__init__(**data)调用，因为object.__init__不接受额外参数
        self.local_caller = local_caller
        # 直接使用传入的 auth_client 实例
        self.auth_client = auth_client
        # 保存兼容性参数，但不使用它们（这是一个过渡版本）
        self.did_document_path = did_document_path
        self.private_key_path = private_key_path



    def _parse_local_uri(self, uri: str) -> (str, str):
        """解析本地 URI，例如 local://<agent_did>/<method_name>"""
        try:
            path = uri.replace("local://", "")
            agent_did, method_name = path.split('/', 1)
            return agent_did, method_name
        except ValueError:
            raise ValueError(f"无效的本地 URI 格式: {uri}. 期望格式为 'local://<agent_did>/<method_name>'.")

    def _get_caller_did_from_auth_client(self) -> str:
        """从现有的 auth_client 配置中提取 DID"""
        try:
            # 方法1: 从 auth_client 的 DID 文档路径读取
            if hasattr(self, 'auth_client') and self.auth_client:
                did_doc_path = getattr(self.auth_client, 'did_document_path', None)
                if did_doc_path and os.path.exists(did_doc_path):
                    with open(did_doc_path, 'r') as f:
                        did_doc = json.load(f)
                        return did_doc.get('id', 'unknown')
            
            # 方法2: 从默认路径读取（与 __init__ 中的逻辑一致）
            current_dir = Path(__file__).parent
            base_dir = current_dir.parent
            default_did_path = base_dir / "use_did_test_public/coder.json"
            
            if default_did_path.exists():
                with open(default_did_path, 'r') as f:
                    did_doc = json.load(f)
                    return did_doc.get('id', 'unknown')
                    
        except Exception as e:
            logger.debug(f"获取 caller DID 失败: {e}")
        
        return 'unknown'

    async def execute(
            self,
            url: str,
            method: str = "GET",
            headers: Dict[str, str] = None,
            params: Dict[str, Any] = None,
            body: Dict[str, Any] = None,
            caller_agent: str = None,    # 新增：调用方智能体 DID
            target_agent: str = None,    # 新增：目标智能体 DID
            use_auth: bool = True        # 新增：是否使用认证
    ) -> Dict[str, Any]:
        """
        执行本地或远程调用。
        - 对于 'local://' URI, 执行本地方法调用。
        - 对于 'http(s)://' URL, 执行远程 HTTP 请求。
        
        参数:
            caller_agent: 调用方智能体 DID，如果为 None 则从配置中自动获取
            target_agent: 目标智能体 DID，如果为 None 则使用单向认证
            use_auth: 是否使用认证，False 时回退到原有的 aiohttp 实现
        """
        if url.startswith("local://"):
            if not self.local_caller:
                return {"status_code": 500, "error": "ANPTool 未配置本地调用器，无法执行本地调用。", "source": "local"}

            try:
                target_did, method_name = self._parse_local_uri(url)

                # 合并 params 和 body 作为本地调用的参数
                kwargs = (params or {}).copy()
                if body:
                    kwargs.update(body)

                # 使用本地调用器执行方法
                method_key = f"{target_did}::{method_name}"
                result = await self.local_caller.call_method_by_key(
                    method_key,
                    **kwargs
                )
                return {"status_code": 200, "data": result, "source": "local"}
            except Exception as e:
                logger.error(f"本地调用失败: {e}")
                return {"status_code": 500, "error": str(e), "source": "local"}
        else:
            # 对于 http/https URL，执行远程调用
            return await self._execute_remote_http_request(url, method, headers, params, body, caller_agent, target_agent, use_auth)

    async def _execute_remote_http_request(
            self,
            url: str,
            method: str = "GET",
            headers: Dict[str, str] = None,
            params: Dict[str, Any] = None,
            body: Dict[str, Any] = None,
            caller_agent: str = None,
            target_agent: str = None,
            use_auth: bool = True
    ) -> Dict[str, Any]:
        """
        执行远程 HTTP 请求以与其他代理交互
        
        参数:
            caller_agent: 调用方智能体 DID，如果为 None 则从配置中自动获取
            target_agent: 目标智能体 DID，如果为 None 则使用单向认证
            use_auth: 是否使用认证，False 时回退到原有的 aiohttp 实现
        """
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        logger.debug(f"ANP 远程请求: {method} {url}")

        # 如果不使用认证，回退到原有的 aiohttp 实现
        if not use_auth:
            return await self._execute_legacy_http_request(url, method, headers, params, body)

        # 检查 auth_client 是否被注入
        if not self.auth_client:
            logger.error("ANPTool 未配置 AuthClient，无法执行认证请求。")
            return {"error": "ANPTool is not configured with an AuthClient.", "status_code": 500}

        # 获取 caller_agent
        # 注意：这里的逻辑需要调整，因为我们不能再从文件路径推断DID
        # 理想情况下，caller_agent 应该总是被明确提供
        if not caller_agent:
            # 这是一个临时的、不理想的回退方案
            logger.warning("调用 execute 时未提供 caller_agent，认证可能失败。")
            caller_agent = "unknown_caller"

        # 确定认证模式
        use_two_way_auth = target_agent is not None and target_agent != 'unknown'

        # 准备完整的 URL（包含查询参数）
        final_url = url
        if params:
            from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
            parsed_url = urlparse(url)
            existing_params = parse_qs(parsed_url.query)

            # 合并现有参数和新参数
            for key, value in params.items():
                existing_params[key] = [str(value)]

            # 重新构建 URL
            new_query = urlencode(existing_params, doseq=True)
            final_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))

        try:
            status, response, info, is_auth_pass = await self.auth_client.authenticated_request(
                caller_agent=caller_agent,
                target_agent=target_agent or caller_agent,  # 单向认证时使用 caller_agent
                request_url=final_url,
                method=method.upper(),
                json_data=body,
                # custom_headers 参数在我们的新架构中不再需要，因为它被包含在请求上下文中
            )


            logger.debug(f"ANP 认证响应: 状态码 {status}")

            # 处理响应，保持与原有格式兼容
            return await self._process_two_way_response(response, final_url, status, info, is_auth_pass)

        except Exception as e:
            logger.debug(f"认证请求失败: {str(e)}")
            return {
                "error": f"认证请求失败: {str(e)}",
                "status_code": 500,
                "url": url
            }

    async def _execute_legacy_http_request(
            self,
            url: str,
            method: str = "GET",
            headers: Dict[str, str] = None,
            params: Dict[str, Any] = None,
            body: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        原有的 aiohttp 实现，作为不使用认证时的回退选项
        """
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        logger.debug(f"ANP 传统请求 (无认证): {method} {url}")

        if "Content-Type" not in headers and method in ["POST", "PUT", "PATCH"]:
            headers["Content-Type"] = "application/json"

        if self.auth_client:
            try:
                auth_headers = self.auth_client.get_auth_header(url)
                headers.update(auth_headers)
            except Exception as e:
                logger.debug(f"获取认证头失败: {str(e)}")

        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "url": url,
                "headers": headers,
                "params": params,
            }
            if body is not None and method in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = body

            http_method = getattr(session, method.lower())

            try:
                async with http_method(**request_kwargs) as response:
                    logger.debug(f"ANP 传统响应: 状态码 {response.status}")
                    if (
                            response.status == 401
                            and "Authorization" in headers
                            and self.auth_client
                    ):
                        logger.warning("认证失败 (401)，尝试重新获取认证")
                        self.auth_client.clear_token(url)
                        headers.update(
                            self.auth_client.get_auth_header(url, force_new=True)
                        )
                        request_kwargs["headers"] = headers
                        async with http_method(**request_kwargs) as retry_response:
                            logger.debug(
                                f"ANP 重试响应: 状态码 {retry_response.status}"
                            )
                            return await self._process_response(retry_response, url)
                    return await self._process_response(response, url)
            except aiohttp.ClientError as e:
                logger.debug(f"HTTP 请求失败: {str(e)}")
                return {"error": f"HTTP 请求失败: {str(e)}", "status_code": 500}

    async def _process_response(self, response, url):
        """处理 HTTP 响应"""
        # 如果认证成功，更新 token
        if response.status == 200 and self.auth_client:
            try:
                self.auth_client.update_token(url, dict(response.headers))
            except Exception as e:
                logger.debug(f"更新 token 失败: {str(e)}")

        # 获取响应内容类型
        content_type = response.headers.get("Content-Type", "").lower()

        # 获取响应文本
        text = await response.text()

        # 根据内容类型处理响应
        if "application/json" in content_type:
            try:
                result = json.loads(text)
                logger.debug("成功解析 JSON 响应")
            except json.JSONDecodeError:
                logger.warning("Content-Type 声明为 JSON 但解析失败，返回原始文本")
                result = {"text": text, "format": "text", "content_type": content_type}
        elif "application/yaml" in content_type or "application/x-yaml" in content_type:
            try:
                result = yaml.safe_load(text)
                logger.debug("成功解析 YAML 响应")
                result = {"data": result, "format": "yaml", "content_type": content_type}
            except yaml.YAMLError:
                logger.warning("Content-Type 声明为 YAML 但解析失败，返回原始文本")
                result = {"text": text, "format": "text", "content_type": content_type}
        else:
            result = {"text": text, "format": "text", "content_type": content_type}

        # 添加状态码到结果
        if isinstance(result, dict):
            result["status_code"] = response.status
        else:
            result = {"data": result, "status_code": response.status, "format": "unknown",
                      "content_type": content_type}

        # 添加 URL 到结果以便跟踪
        result["url"] = str(url)

        return result

    async def execute_with_two_way_auth(
            self,
            url: str,
            method: str = "GET",
            headers: Dict[str, str] = None,
            params: Dict[str, Any] = None,
            body: Dict[str, Any] = None,
            anpsdk=None,  # 添加 anpsdk 参数
            caller_agent: str = None,  # 添加发起 agent 参数
            target_agent: str = None,  # 添加目标 agent 参数
            use_two_way_auth: bool = False  # 是否使用双向认证
    ) -> Dict[str, Any]:
        """
        使用双向认证执行 HTTP 请求以与其他代理交互

        参数:
            url (str): 代理描述文件或 API 端点的 URL
            method (str, 可选): HTTP 方法，默认为 "GET"
            headers (Dict[str, str], 可选): HTTP 请求头（将传递给 agent_auth_two_way 处理）
            params (Dict[str, Any], 可选): URL 查询参数
            body (Dict[str, Any], 可选): POST/PUT 请求的请求体

        返回:
            Dict[str, Any]: 响应内容
        """

        if headers is None:
            headers = {}
        if params is None:
            params = {}

        logger.debug(f"ANP 双向认证请求: {method} {url}")

        try:
            # 1. 准备完整的 URL（包含查询参数）
            final_url = url
            if params:
                from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
                parsed_url = urlparse(url)
                existing_params = parse_qs(parsed_url.query)

                # 合并现有参数和新参数
                for key, value in params.items():
                    existing_params[key] = [str(value)]

                # 重新构建 URL
                new_query = urlencode(existing_params, doseq=True)
                final_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))

            # 2. 准备请求体数据
            request_data = None
            if body is not None and method.upper() in ["POST", "PUT", "PATCH"]:
                request_data = body

            # 3. 调用 agent_auth_two_way（需要传入必要的参数）
            # 注意：这里暂时使用占位符，后续需要根据实际情况调整

            status, response, info, is_auth_pass = await self.auth_client.authenticated_request(
                caller_agent=caller_agent,  # 需要传入调用方智能体ID
                target_agent=target_agent,  # 需要传入目标方智能体ID，如果对方没有ID，可以随便写，因为对方不会响应这个信息
                request_url=final_url,
                method=method.upper(),
                json_data=request_data,
            )

            logger.debug(f"ANP 双向认证响应: 状态码 {status}")

            # 4. 处理响应，保持与原 execute 方法相同的响应格式
            result = await self._process_two_way_response(response, final_url, status, info, is_auth_pass)

            return result

        except Exception as e:
            logger.debug(f"双向认证请求失败: {str(e)}")
            return {
                "error": f"双向认证请求失败: {str(e)}",
                "status_code": 500,
                "url": url
            }

    async def _process_two_way_response(self, response, url, status, info, is_auth_pass):
        """处理双向认证的 HTTP 响应"""

        # 如果 response 已经是处理过的字典格式
        if isinstance(response, dict):
            result = response
        elif isinstance(response, str):
            # 尝试解析为 JSON
            try:
                result = json.loads(response)
                logger.debug("成功解析 JSON 响应")
            except json.JSONDecodeError:
                # 如果不是 JSON，作为文本处理
                result = {
                    "text": response,
                    "format": "text",
                    "content_type": "text/plain"
                }
        else:
            # 其他类型的响应
            result = {
                "data": response,
                "format": "unknown",
                "content_type": "unknown"
            }

        # 添加状态码和其他信息
        if isinstance(result, dict):
            result["status_code"] = status
            result["url"] = str(url)
            result["auth_info"] = info
            result["is_auth_pass"] = is_auth_pass
        else:
            result = {
                "data": result,
                "status_code": status,
                "url": str(url),
                "auth_info": info,
                "is_auth_pass": is_auth_pass,
                "format": "unknown"
            }

        return result


class CustomJSONEncoder(JSONEncoder):
    """自定义 JSON 编码器，处理 OpenAI 对象"""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


class ANPToolCrawler:
    """ANP Tool 智能爬虫 - 简化版本"""

    # 在构造函数中接收 auth_client
    def __init__(self, auth_client: Optional[AuthClient] = None):
        self.auth_client = auth_client


    async def run_crawler_demo(self, task_input: str, initial_url: str,
                             use_two_way_auth: bool = True, req_did: str = None,
                             resp_did: str = None, task_type: str = "code_generation"):
        """运行爬虫演示"""
        try:
            # 获取调用者智能体
            caller_agent = await self._get_caller_agent(req_did)
            if not caller_agent:
                return {"error": "无法获取调用者智能体"}

            # 根据任务类型创建不同的提示模板
            if task_type == "weather_query":
                prompt_template = self._create_weather_search_prompt_template()
                agent_name = "天气查询爬虫"
                max_documents = 10
            elif task_type == "root_query":
                prompt_template = self._create_root_search_prompt_template()
                agent_name = "多智能体搜索爬虫"
                max_documents = 120
            elif task_type == "function_query":
                prompt_template = self._create_function_search_prompt_template()
                agent_name = "功能搜索爬虫"
                max_documents = 10
            else:
                prompt_template = self._create_code_search_prompt_template()
                agent_name = "代码生成爬虫"
                max_documents = 10

            # 调用通用智能爬虫
            result = await self._intelligent_crawler(
                anpsdk=None,
                caller_agent=str(caller_agent.id),
                target_agent=str(resp_did) if resp_did else str(caller_agent.id),
                use_two_way_auth=use_two_way_auth,
                user_input=task_input,
                initial_url=initial_url,
                prompt_template=prompt_template,
                #did_document_path=caller_agent.did_document_path,
                #private_key_path=caller_agent.private_key_path,
                task_type=task_type,
                max_documents=max_documents,
                agent_name=agent_name
            )

            return result

        except Exception as e:
            logger.error(f"爬虫演示失败: {e}")
            return {"error": str(e)}

    async def _get_caller_agent(self, req_did: str = None):
        """获取调用者智能体"""
        if req_did is None:
            user_data_manager = LocalUserDataManager()
            user_data_manager.load_users()
            user_data = user_data_manager.get_user_data_by_name("托管智能体_did:wba:agent-did.com:test:public")
            if user_data:
                agent = LocalAgent.from_did(user_data.did)
                logger.debug(f"使用托管身份智能体进行爬取: {agent.name}")
                return agent
            else:
                logger.error("未找到托管智能体")
                return None
        else:
            return LocalAgent.from_did(req_did)

    def _create_root_search_prompt_template(self):
        """创建溯源搜索智能体的提示模板"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""
                 你是一个智能搜索工具。你的目标是根据用户输入要求从原始链接给出的agent列表，逐一查询agent描述文件，选择合适的agent，调用工具完成代码任务。

                 ## 当前任务
                 {{task_description}}

                 ## 重要提示
                 1. 你使用的anp_tool非常强大，可以访问内网和外网地址，它已经帮你访问初始URL（{{initial_url}}）并获取了agent列表文件附在最后，
                 2. 每个agent的did格式为 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211'，从 did格式可以获取agent的did文件地址
                 例如 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211' 的did地址为 
                 http://localhost:9527/wba/user/5fea49e183c6c211/did.json
                 3. 从 did文件中，可以获得 "serviceEndpoint": "http://localhost:9527/wba/user/5fea49e183c6c211/ad.json"
                 4. 从 ad.json，你可以获得这个代理的详细结构、功能和 API 使用方法。
                 5. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。
                 6. 你要优先理解api_interface.json这样的文件对api使用方式的描述，特别是参数的配置，params下属的字段可以直接作为api的参数
                 7. 你可以使用 anp_tool 获取任何 URL 的内容。
                 8. 该工具可以处理各种响应格式。
                 9. 阅读每个文档以找到与任务相关的信息或 API 端点。
                 10. 你需要自己决定爬取路径，不要等待用户指令。
                 11. 注意：你最多可以爬取 6 个 agent，每个agent最多可以爬取20次，达到此限制后必须结束搜索。

                 ## 工作流程
                 1. 获取初始 URL 的内容并理解代理的功能。
                 2. 分析内容以找到所有可能的链接和 API 文档。
                 3. 解析 API 文档以了解 API 的使用方法。
                 4. 根据任务需求构建请求以获取所需的信息。
                 5. 继续探索相关链接，直到找到足够的信息。
                 6. 总结信息并向用户提供最合适的建议。

                 提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。

                 ## 日期
                 当前日期：{current_date}
                 """
    def _create_function_search_prompt_template(self) :
        """创建功能搜索智能体的提示模板"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""
                你是一个智能搜索工具。你的目标是根据用户输入要求识别合适的工具，调用工具完成代码任务。

                ## 当前任务
                {{task_description}}

                ## 重要提示
                1. 你将收到一个初始 URL（{{initial_url}}），这是一个代理描述文件。
                2. 你需要理解这个代理的结构、功能和 API 使用方法。
                3. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。
                4. 你可以使用 anp_tool 获取任何 URL 的内容。
                5. 该工具可以处理各种响应格式。
                6. 阅读每个文档以找到与任务相关的信息或 API 端点。
                7. 你需要自己决定爬取路径，不要等待用户指令。
                8. 注意：你最多可以爬取 10 个 URL，达到此限制后必须结束搜索。

                ## 工作流程
                1. 获取初始 URL 的内容并理解代理的功能。
                2. 分析内容以找到所有可能的链接和 API 文档。
                3. 解析 API 文档以了解 API 的使用方法。
                4. 根据任务需求构建请求以获取所需的信息。
                5. 继续探索相关链接，直到找到足够的信息。
                6. 总结信息并向用户提供最合适的建议。

                提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。

                ## 日期
                当前日期：{current_date}
                """
    def _create_code_search_prompt_template(self):
        """创建代码搜索智能体的提示模板"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""
        你是一个通用的智能代码工具。你的目标是根据用户输入要求调用工具完成代码任务。

        ## 当前任务
        {{task_description}}

        ## 重要提示
        1. 你将收到一个初始 URL（{{initial_url}}），这是一个代理描述文件。
        2. 你需要理解这个代理的结构、功能和 API 使用方法。
        3. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。
        4. 你可以使用 anp_tool 获取任何 URL 的内容。
        5. 该工具可以处理各种响应格式。
        6. 阅读每个文档以找到与任务相关的信息或 API 端点。
        7. 你需要自己决定爬取路径，不要等待用户指令。
        8. 注意：你最多可以爬取 10 个 URL，达到此限制后必须结束搜索。

        ## 工作流程
        1. 获取初始 URL 的内容并理解代理的功能。
        2. 分析内容以找到所有可能的链接和 API 文档。
        3. 解析 API 文档以了解 API 的使用方法。
        4. 根据任务需求构建请求以获取所需的信息。
        5. 继续探索相关链接，直到找到足够的信息。
        6. 总结信息并向用户提供最合适的建议。

        提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。

        ## 日期
        当前日期：{current_date}
        """

    def _create_weather_search_prompt_template(self):
        """创建天气搜索智能体的提示模板"""
        return """
        你是一个通用智能网络数据探索工具。你的目标是通过递归访问各种数据格式（包括JSON-LD、YAML等）来找到用户需要的信息和API以完成特定任务。

        ## 当前任务
        {task_description}

        ## 重要提示
        1. 你将收到一个初始URL（{initial_url}），这是一个代理描述文件。
        2. 你需要理解这个代理的结构、功能和API使用方法。
        3. 你需要像网络爬虫一样持续发现和访问新的URL和API端点。
        4. 你可以使用anp_tool来获取任何URL的内容。
        5. 此工具可以处理各种响应格式。
        6. 阅读每个文档以找到与任务相关的信息或API端点。
        7. 你需要自己决定爬取路径，不要等待用户指令。
        8. 注意：你最多可以爬取10个URL，并且必须在达到此限制后结束搜索。

        ## 爬取策略
        1. 首先获取初始URL的内容，理解代理的结构和API。
        2. 识别文档中的所有URL和链接，特别是serviceEndpoint、url、@id等字段。
        3. 分析API文档以理解API用法、参数和返回值。
        4. 根据API文档构建适当的请求，找到所需信息。
        5. 记录所有你访问过的URL，避免重复爬取。
        6. 总结所有你找到的相关信息，并提供详细的建议。

        对于天气查询任务，你需要:
        1. 找到天气查询API端点
        2. 理解如何正确构造请求参数（如城市名、日期等）
        3. 发送天气查询请求
        4. 获取并展示天气信息

        提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。
        """

    async def _intelligent_crawler(self, user_input: str, initial_url: str,
                                 prompt_template: str,  anpsdk=None,
                                 caller_agent: str = None, target_agent: str = None,
                                 use_two_way_auth: bool = True, task_type: str = "general",
                                 max_documents: int = 10, agent_name: str = "智能爬虫"):
        """通用智能爬虫功能"""
        logger.info(f"启动{agent_name}智能爬取: {initial_url}")

        # 初始化变量
        visited_urls = set()
        crawled_documents = []

        # 初始化ANPTool，并传入注入的 auth_client
        # 注意：这里的 self.auth_client 是从 ANPToolCrawler 的构造函数中传入的
        anp_tool = ANPTool(
            auth_client=self.auth_client
        )

        # 获取初始URL内容
        try:
            initial_content = await anp_tool.execute_with_two_way_auth(
                url=initial_url, method='GET', headers={}, params={}, body={},
                anpsdk=anpsdk, caller_agent=caller_agent,
                target_agent=target_agent, use_two_way_auth=use_two_way_auth
            )
            visited_urls.add(initial_url)
            crawled_documents.append(
                {"url": initial_url, "method": "GET", "content": initial_content}
            )
            logger.debug(f"成功获取初始URL: {initial_url}")
        except Exception as e:
            logger.error(f"获取初始URL失败: {str(e)}")
            return self._create_error_result(str(e), visited_urls, crawled_documents, task_type)

        # 创建LLM客户端
        client = self._create_llm_client()
        if not client:
            return self._create_error_result("LLM客户端创建失败", visited_urls, crawled_documents, task_type)

        # 创建初始消息
        messages = self._create_initial_messages(prompt_template, user_input, initial_url, initial_content, agent_name)

        # 开始对话循环
        result = await self._conversation_loop(
            client, messages, anp_tool, crawled_documents, visited_urls,
            max_documents, anpsdk, caller_agent, target_agent, use_two_way_auth
        )

        return self._create_success_result(result, visited_urls, crawled_documents, task_type, messages)

    def _create_error_result(self, error_msg: str, visited_urls: set,
                           crawled_documents: list, task_type: str):
        """创建错误结果"""
        return {
            "content": f"错误: {error_msg}",
            "type": "error",
            "visited_urls": list(visited_urls),
            "crawled_documents": crawled_documents,
            "task_type": task_type,
        }

    def _create_success_result(self, content: str, visited_urls: set,
                             crawled_documents: list, task_type: str, messages: list):
        """创建成功结果"""
        return {
            "content": content,
            "type": "text",
            "visited_urls": [doc["url"] for doc in crawled_documents],
            "crawled_documents": crawled_documents,
            "task_type": task_type,
            "messages": messages,
        }

    def _create_llm_client(self):
        """创建LLM客户端"""
        try:
            model_provider = os.environ.get("MODEL_PROVIDER", "openai").lower()
            if model_provider == "openai":
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    base_url=os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
        )
                return client

            else:
                logger.error("需要配置 OpenAI")
                return None
        except Exception as e:
            logger.error(f"创建LLM客户端失败: {e}")
            return None

    def _create_initial_messages(self, prompt_template: str, user_input: str,
                               initial_url: str, initial_content: dict, agent_name: str):
        """创建初始消息"""
        formatted_prompt = prompt_template.format(
            task_description=user_input, initial_url=initial_url
        )

        return [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": user_input},
            {
                "role": "system",
                "content": f"我已获取初始URL的内容。以下是{agent_name}的描述数据:\n\n```json\n{json.dumps(initial_content, ensure_ascii=False, indent=2)}\n```\n\n请分析这些数据，理解{agent_name}的功能和API使用方法。找到你需要访问的链接，并使用anp_tool获取更多信息以完成用户的任务。",
            },
        ]

    async def _conversation_loop(self, client, messages: list, anp_tool: ANPTool,
                               crawled_documents: list, visited_urls: set,
                               max_documents: int, anpsdk=None, caller_agent: str = None,
                               target_agent: str = None, use_two_way_auth: bool = True):
        """对话循环处理"""
        model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4")
        current_iteration = 0

        while current_iteration < max_documents:
            current_iteration += 1
            logger.info(f"开始爬取迭代 {current_iteration}/{max_documents}")

            if len(crawled_documents) >= max_documents:
                logger.info(f"已达到最大爬取文档数 {max_documents}，停止爬取")
                messages.append({
                    "role": "system",
                    "content": f"你已爬取 {len(crawled_documents)} 个文档，达到最大爬取限制 {max_documents}。请根据获取的信息做出最终总结。",
                })

            try:
                completion = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=self._get_available_tools(anp_tool),
                    tool_choice="auto",
                )

                response_message = completion.choices[0].message
                logger.info(f"\n模型返回:\n{response_message}")
                messages.append({
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": response_message.tool_calls,
                })


                if not response_message.tool_calls:
                    logger.debug("模型没有请求任何工具调用，结束爬取")
                    break

                # 处理工具调用
                await self._handle_tool_calls(
                    response_message.tool_calls, messages, anp_tool,
                    crawled_documents, visited_urls, anpsdk, caller_agent,
                    target_agent, use_two_way_auth, max_documents
                )

                if len(crawled_documents) >= max_documents and current_iteration < max_documents:
                    continue

            except Exception as e:
                logger.error(f"模型调用失败: {e}")
                messages.append({
                    "role": "system",
                    "content": f"处理过程中发生错误: {str(e)}。请根据已获取的信息做出最佳判断。",
                })
                break

        # 返回最后的响应内容
        if messages and messages[-1]["role"] == "assistant":
            return messages[-1].get("content", "处理完成")
        return "处理完成"

    def _get_available_tools(self, anp_tool_instance):
        """获取可用工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "anp_tool",
                    "description": anp_tool_instance.description,
                    "parameters": anp_tool_instance.parameters,
                },
            }
        ]

    async def _handle_tool_calls(self, tool_calls, messages: list, anp_tool: ANPTool,
                               crawled_documents: list, visited_urls: set,
                               anpsdk=None, caller_agent: str = None,
                               target_agent: str = None, use_two_way_auth: bool = False,
                               max_documents: int = 10):
        """处理工具调用"""
        for tool_call in tool_calls:
            if tool_call.function.name == "anp_tool":
                await self._handle_anp_tool_call(
                    tool_call, messages, anp_tool, crawled_documents, visited_urls,
                    anpsdk, caller_agent, target_agent, use_two_way_auth
                )

                if len(crawled_documents) >= max_documents:
                    break

    async def _handle_anp_tool_call(self, tool_call, messages: list, anp_tool: ANPTool,
                                  crawled_documents: list, visited_urls: set,
                                  anpsdk=None, caller_agent: str = None,
                                  target_agent: str = None, use_two_way_auth: bool = False):
        """处理ANP工具调用"""
        function_args = json.loads(tool_call.function.arguments)

        url = function_args.get("url")
        method = function_args.get("method", "GET")
        headers = function_args.get("headers", {})
        # 兼容 "parameters":{"params":{...}}、"parameters":{"a":...} 以及直接 "params":{...} 的情况
        params = function_args.get("params", {})
        if not params and "parameters" in function_args and isinstance(function_args["parameters"], dict):
                    parameters = function_args["parameters"]
                    if "params" in parameters and isinstance(parameters["params"], dict):
                        params = parameters["params"]
                    else:
                        # 如果parameters本身就是参数字典（如{"a":2.88888,"b":999933.4445556}），直接作为params
                        params = parameters
        body = function_args.get("body", {})


        # 2. --- URL 健壮性修复 ---
        # 检查URL是否为相对路径，如果是，则根据target_agent的DID补全
        if url and not url.startswith(('http://', 'https://')):
            if not target_agent:
                logger.warning(f"无法补全相对URL '{url}'，因为缺少 target_agent DID。")
            else:
                host, port = parse_wba_did_host_port(target_agent)
                if not host:
                    logger.error(f"无法从目标DID '{target_agent}' 中解析主机以补全相对URL '{url}'")
                else:
                    base_url = f"http://{host}:{port}"
                    # 确保相对路径前有一个斜杠
                    url = f"{base_url}{url if url.startswith('/') else '/' + url}"
                    logger.info(f"已将相对URL补全为: {url}")
        # 处理消息参数
        if len(body) == 0:
            message_value = self._find_message_in_args(function_args)
            if message_value is not None:
                logger.debug(f"模型发出调用消息：{message_value}")
                body = {"message": message_value}
        logger.info(f"根据模型要求组装请求:\n{url}:{method}\nheaders:{headers}params:{params}body:{body}")
        try:
            if use_two_way_auth:
                result = await anp_tool.execute_with_two_way_auth(
                    url=url, method=method, headers=headers, params=params, body=body,
                    anpsdk=anpsdk, caller_agent=caller_agent,
                    target_agent=target_agent, use_two_way_auth=use_two_way_auth
                )
            else:
                result = await anp_tool.execute(
                    url=url, method=method, headers=headers, params=params, body=body
                )

            logger.debug(f"ANPTool 响应 [url: {url}]")

            visited_urls.add(url)
            crawled_documents.append({"url": url, "method": method, "content": result})
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        except Exception as e:
            logger.error(f"ANPTool调用失败 {url}: {str(e)}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps({
                    "error": f"ANPTool调用失败: {url}",
                    "message": str(e),
                }),
            })

    def _find_message_in_args(self, data):
        """递归查找参数中的message值"""
        if isinstance(data, dict):
            if "message" in data:
                return data["message"]
            for value in data.values():
                result = self._find_message_in_args(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_message_in_args(item)
                if result:
                    return result
        return None
