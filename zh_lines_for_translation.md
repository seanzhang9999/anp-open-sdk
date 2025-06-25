
## ./data_user/localhost_9527/agents_config/agent_002/agent_handlers.py

- Line 6: `    这是一个打招呼的API，传入message参数即可返回问候语。`
  - Translation:     This is a greeting API; pass in the message parameter to return a greeting.

- Line 10: `        "msg": f"{agent_name}的/hello接口收到请求:",`
  - Translation:         "msg": f"Request received by {agent_name}'s /hello endpoint:"

- Line 18: `            "msg": f"{agent.name}的/info接口收到请求:",`
  - Translation:             "msg": f"Request received at {agent.name}'s /info endpoint:"


## ./data_user/localhost_9527/agents_config/agent_002/agent_register.py

- Line 9: `    自定义注册脚本：为 agent 注册任意 API、消息、事件等`
  - Translation:     Custom registration script: Register any API, message, event, etc. for the agent.

- Line 13: `    # 注册 /hello POST,GET`
  - Translation:     # Register /hello POST,GET

- Line 16: `    # 注册 /info POST`
  - Translation:     # Register /info POST

- Line 19: `    # 注册一个自定义消息处理器`
  - Translation:     # Register a custom message handler

- Line 22: `        return {"reply": f"自定义注册收到消息: {msg.get('content')}"}`
  - Translation:         return {"reply": f"Custom registration received message: {msg.get('content')}"}

- Line 24: `    # 你还可以注册事件、定时任务、权限校验等`
  - Translation:     # You can also register events, scheduled tasks, permission checks, etc.

- Line 30: `    # 注册一个本地自定义方法`
  - Translation:     # Register a local custom method

- Line 31: `    # 使用装饰器注册本地方法`
  - Translation:     # Use a decorator to register a local method

- Line 32: `    @local_method(description="演示方法，返回agent信息", tags=["demo", "info"])`
  - Translation:     @local_method(description="Demonstration method, returns agent information", tags=["demo", "info"])

- Line 34: `        return f"这是来自 {agent.name} 的演示方法"`
  - Translation:         return f"This is a demonstration method from {agent.name}"

- Line 36: `    @local_method(description="计算两个数的和", tags=["math", "calculator"])`
  - Translation:     @local_method(description="Calculate the sum of two numbers", tags=["math", "calculator"])

- Line 40: `    @local_method(description="异步演示方法", tags=["demo", "async"])`
  - Translation:     @local_method(description="Asynchronous demonstration method", tags=["demo", "async"])

- Line 43: `        return "异步方法结果"`
  - Translation:         return "Asynchronous method result"

- Line 45: `    # 自动注册所有标记的本地方法`
  - Translation:     # Automatically register all tagged local methods


## ./data_user/localhost_9527/agents_config/agent_llm/agent_handlers.py

- Line 6: `# --- 模块级变量，代表这个Agent实例的状态 ---`
  - Translation: # --- Module-level variable representing the state of this Agent instance ---

- Line 7: `# 这些变量在模块被加载时创建，并贯穿整个应用的生命周期`
  - Translation: # These variables are created when the module is loaded and persist throughout the application's lifecycle.

- Line 14: `    初始化钩子，现在由插件自己负责创建和配置Agent实例。`
  - Translation:     Initialize the hook, now the plugin is responsible for creating and configuring the Agent instance itself.

- Line 15: `    它不再接收参数，而是返回创建好的agent实例。`
  - Translation:     It no longer accepts parameters, but returns the created agent instance.

- Line 22: `    # 1. 使用传入的 agent 实例`
  - Translation:     # 1. Use the passed-in agent instance

- Line 25: `    # __file__ 是当前文件的路径`
  - Translation:     # `__file__` is the path of the current file.

- Line 32: `    # 3. 创建并存储LLM客户端作为模块级变量`
  - Translation:     # 3. Create and store the LLM client as a module-level variable

- Line 38: `    # 4. 自己注册自己的API`
  - Translation:     # 4. Register your own API

- Line 39: `    # 注意：现在是直接在模块内调用实例的方法`
  - Translation:     # Note: The method of the instance is now called directly within the module.

- Line 43: `    # 5. 将创建和配置好的agent实例返回给加载器`
  - Translation:     # 5. Return the created and configured agent instance to the loader.

- Line 49: `    清理钩子，现在也直接使用模块级变量。`
  - Translation:     Cleanup hook, now also directly uses module-level variables.

- Line 60: `    API处理函数，现在直接使用模块内的 my_llm_client。`
  - Translation:     API handling function, now directly using my_llm_client within the module.

- Line 61: `    它不再需要从request中获取agent实例。`
  - Translation:     It no longer needs to obtain the agent instance from the request.


## ./data_user/localhost_9527/agents_config/agent_caculator/agent_handlers.py

- Line 12: `            "error": f'use: {{"params": {params}}} 来调用'`
  - Translation:             "error": f'use: {{"params": {params}}} to invoke'

- Line 14: `# 这个简单的Agent不需要初始化或清理，所以我们省略了这些函数`
  - Translation: # This simple Agent does not require initialization or cleanup, so we have omitted these functions.


## ./data_user/localhost_9527/agents_config/orchestrator_agent/agent_handlers.py

- Line 3: `import httpx  # 需要安装 httpx: pip install httpx`
  - Translation: import httpx  # Requires installation of httpx: pip install httpx

- Line 16: `# 在初始化时创建调用器`
  - Translation: # Create invoker during initialization

- Line 18: `# --- 模块级变量 ---`
  - Translation: # --- Module-level variable ---

- Line 23: `    初始化钩子，创建和配置Agent实例，并附加特殊能力。`
  - Translation:     Initialize the hook, create and configure the Agent instance, and attach special capabilities.

- Line 31: `    # 关键步骤：将函数作为方法动态地附加到创建的 Agent 实例上`
  - Translation:     # Key step: Dynamically attach functions as methods to the created Agent instance.

- Line 45: `    发现并获取所有已发布Agent的详细描述。`
  - Translation:     Discover and retrieve detailed descriptions of all published Agents.

- Line 46: `    这个函数将被附加到 Agent 实例上作为方法。`
  - Translation:     This function will be attached to the Agent instance as a method.

- Line 54: `            # 1. 访问  获取公开的 agent 列表`
  - Translation:             # Access to obtain the public agent list

- Line 69: `                # 2. 获取每个 agent 的 DID Document`
  - Translation:                 # 2. Retrieve the DID Document for each agent

- Line 76: `                    caller_agent=my_agent_instance.id,  # 使用 self.id 作为调用者`
  - Translation:                     caller_agent=my_agent_instance.id,  # Use self.id as the caller

- Line 90: `                # 3. 从 DID Document 中提取 ad.json 的地址并获取内容`
  - Translation:                 # 3. Extract the address of ad.json from the DID Document and retrieve its content.

- Line 133: `    # 构造 JSON-RPC 请求参数`
  - Translation:     # Construct JSON-RPC request parameters

- Line 142: `    logger.info(f"计算api调用结果: {result}")`
  - Translation:     logger.info(f"Calculate API call result: {result}")

- Line 149: `    # 构造 JSON-RPC 请求参数`
  - Translation:     # Construct JSON-RPC request parameters

- Line 157: `    logger.info(f"hello api调用结果: {result}")`
  - Translation:     logger.info(f"hello API call result: {result}")

- Line 168: `    # 协作智能体通过爬虫向组装后的智能体请求服务`
  - Translation:     # Collaborative agents request services from the assembled agents via web crawlers.

- Line 169: `    task_description = "我需要计算两个浮点数相加 2.88888+999933.4445556"`
  - Translation:     task_description = "I need to calculate the sum of two floating-point numbers 2.88888 + 999933.4445556"

- Line 174: `            req_did=my_agent_instance.id,  # 请求方是协作智能体`
  - Translation:             req_did=my_agent_instance.id,  # The requester is a collaborative agent

- Line 175: `            resp_did=target_did,  # 目标是组装后的智能体`
  - Translation:             resp_did=target_did,  # The target is the assembled agent

- Line 178: `            use_two_way_auth=True,  # 使用双向认证`
  - Translation:             use_two_way_auth=True,  # Use two-way authentication

- Line 181: `        logger.debug(f"智能调用结果: {result}")`
  - Translation:         logger.debug(f"Smart invocation result: {result}")

- Line 185: `        logger.info(f"智能调用过程中出错: {e}")`
  - Translation:         logger.info(f"Error during intelligent invocation: {e}")

- Line 197: `    # 协作智能体通过爬虫向组装后的智能体请求服务`
  - Translation:     # Collaborative agents request services from the assembled agents via web crawlers.

- Line 198: `    task_description = "我需要计算两个浮点数相加 2.88888+999933.4445556"`
  - Translation:     task_description = "I need to calculate the sum of two floating-point numbers 2.88888 + 999933.4445556"

- Line 207: `            use_two_way_auth=True,  # 使用双向认证`
  - Translation:             use_two_way_auth=True,  # Use two-way authentication

- Line 210: `        logger.debug(f"智能探索结果: {result}")`
  - Translation:         logger.debug(f"Intelligent exploration result: {result}")

- Line 214: `        logger.info(f"智能探索过程中出错: {e}")`
  - Translation:         logger.info(f"Error during intelligent exploration: {e}")

- Line 220: `    """调用 agent_002 上的自定义演示方法"""`
  - Translation:     """Call the custom demonstration method on agent_002"""

- Line 222: `        # 通过 sdk 获取 agent_002 实例`
  - Translation:         # Get the agent_002 instance through the SDK

- Line 225: `            return "错误：未找到 agent_002"`
  - Translation:             return "Error: agent_002 not found"

- Line 227: `        # 调用 agent_002 上的方法`
  - Translation:         # Call the method on agent_002

- Line 232: `            return "错误：在 agent_002 上未找到 demo_method"`
  - Translation:             return "Error: demo_method not found on agent_002"

- Line 235: `        logger.error(f"调用 agent_002.demo_method 失败: {e}")`
  - Translation:         logger.error(f"Failed to call agent_002.demo_method: {e}")

- Line 236: `        return f"调用 agent_002.demo_method 时出错: {e}"`
  - Translation:         return f"Error occurred while calling agent_002.demo_method: {e}"

- Line 240: `    """通过搜索调用 agent_002 的演示方法"""`
  - Translation:     """Invoke the demo method of agent_002 through search"""

- Line 242: `        # 方式1：通过关键词搜索调用`
  - Translation:         # Method 1: Invoke through keyword search

- Line 244: `        logger.info(f"搜索调用结果: {result}")`
  - Translation:         logger.info(f"Search invocation result: {result}")

- Line 246: `        # 方式2：通过方法键直接调用`
  - Translation:         # Method 2: Direct invocation via method key

- Line 251: `        logger.info(f"直接调用结果: {result2}")`
  - Translation:         logger.info(f"Direct call result: {result2}")

- Line 256: `        logger.error(f"调用失败: {e}")`
  - Translation:         logger.error(f"Call failed: {e}")

- Line 257: `        return f"调用时出错: {e}"`
  - Translation:         return f"Error occurred during invocation: {e}"

- Line 261: `    """搜索可用的本地方法"""`
  - Translation:     Search for available local methods

- Line 270: `    清理钩子。`
  - Translation:     Cleanup hook.


## ./data_user/localhost_9527/agents_config/agent_001/agent_handlers.py

- Line 8: `            "msg": f"{agent.name}的/hello接口收到请求:",`
  - Translation:             "msg": f"Request received by {agent.name}'s /hello endpoint:"

- Line 18: `            "msg": f"{agent.name}的/info接口收到请求:",`
  - Translation:             "msg": f"Request received by {agent.name}'s /info endpoint:"


## ./anp_user_service/app/routers/chat.py

- Line 38: `        apiBase=HttpUrl(f"http://{config.anp_user_service.api_base}"),  # 必须是 http(s):// 开头的有效URL`
  - Translation:         apiBase=HttpUrl(f"http://{config.anp_user_service.api_base}"),  # Must be a valid URL starting with http(s)://


## ./anp_user_service/app/models/schemas.py

- Line 11: `    anp_user_name: Optional[str] = None # e.g., '智能体创建删除示范用户'`
  - Translation:     anp_user_name: Optional[str] = None # e.g., 'Agent Creation and Deletion Demo User'


## ./test/test_anpsdk_all.py

- Line 3: `ANP SDK Demo 自动化集成测试`
  - Translation: ANP SDK Demo Automated Integration Testing

- Line 5: `本脚本自动化测试 anp_open_sdk_demo 的主要演示功能，确保各主要流程可正常跑通。`
  - Translation: This script automates testing of the main demonstration functions of anp_open_sdk_demo, ensuring that all major processes can run smoothly.

- Line 20: `setup_logging() # 假设 setup_logging 内部也改用 get_global_config()`
  - Translation: setup_logging() # Assume setup_logging internally also uses get_global_config()

- Line 23: `# 添加项目路径`
  - Translation: # Add project path

- Line 34: `    """初始化演示环境，返回 DemoTaskRunner 和 agent 列表"""`
  - Translation:     """Initialize the demo environment, return DemoTaskRunner and agent list"""

- Line 57: `    logger.info("\n=== 测试1: 智能体信息爬虫演示 ===")`
  - Translation:     logger.info("\n=== Test 1: Agent Information Crawler Demonstration ===")

- Line 60: `        logger.info("✅ 智能体信息爬虫演示通过")`
  - Translation:         logger.info("✅ Agent information crawler demo passed")

- Line 63: `        logger.error(f"❌ 智能体信息爬虫演示失败: {e}")`
  - Translation:         logger.error(f"❌ Agent information crawler demonstration failed: {e}")

- Line 68: `    logger.info("\n=== 测试2: API 调用演示 ===")`
  - Translation:     logger.info("\n=== Test 2: API Call Demonstration ===")

- Line 71: `        logger.info("✅ API 调用演示通过")`
  - Translation:         logger.info("✅ API call demonstration passed")

- Line 74: `        logger.error(f"❌ API 调用演示失败: {e}")`
  - Translation:         logger.error(f"❌ API call demonstration failed: {e}")

- Line 79: `    logger.info("\n=== 测试3: 消息发送演示 ===")`
  - Translation:     logger.info("\n=== Test 3: Message Sending Demonstration ===")

- Line 82: `        logger.info("✅ 消息发送演示通过")`
  - Translation:         logger.info("✅ Message sending demonstration passed")

- Line 85: `        logger.error(f"❌ 消息发送演示失败: {e}")`
  - Translation:         logger.error(f"❌ Message sending demonstration failed: {e}")

- Line 90: `    logger.info("\n=== 测试4: 智能体生命周期演示 ===")`
  - Translation:     logger.info("\n=== Test 4: Demonstration of Agent Lifecycle ===")

- Line 93: `        logger.info("✅ 智能体生命周期演示通过")`
  - Translation:         logger.info("✅ Agent lifecycle demonstration passed")

- Line 96: `        logger.error(f"❌ 智能体生命周期演示失败: {e}")`
  - Translation:         logger.error(f"❌ Agent lifecycle demonstration failed: {e}")

- Line 101: `    logger.info("\n=== 测试5: 托管 DID 演示 ===")`
  - Translation:     logger.info("\n=== Test 5: Managed DID Demonstration ===")

- Line 104: `        logger.info("✅ 托管 DID 演示通过")`
  - Translation:         logger.info("✅ Managed DID demo passed")

- Line 107: `        logger.error(f"❌ 托管 DID 演示失败: {e}")`
  - Translation:         logger.error(f"❌ Hosted DID demonstration failed: {e}")

- Line 112: `    logger.info("\n=== 测试6: 群聊演示 ===")`
  - Translation:     logger.info("\n=== Test 6: Group Chat Demonstration ===")

- Line 115: `        logger.info("✅ 群聊演示通过")`
  - Translation:         logger.info("✅ Group chat demo passed")

- Line 118: `        logger.error(f"❌ 群聊演示失败: {e}")`
  - Translation:         logger.error(f"❌ Group chat demonstration failed: {e}")

- Line 123: `    logger.info("🚀 开始 ANP SDK 全部演示自动化测试")`
  - Translation:     logger.info("🚀 Starting ANP SDK full demonstration automated testing")

- Line 127: `        logger.error("智能体不足3个，无法执行全部演示")`
  - Translation:         logger.error("Fewer than 3 agents available, unable to execute the entire demonstration")

- Line 147: `                logger.info("✅ 通过")`
  - Translation:                 logger.info("✅ Passed")

- Line 150: `                logger.error("❌ 失败")`
  - Translation:                 logger.error("❌ Failure")

- Line 153: `            logger.error(f"❌ 异常: {e}")`
  - Translation:             logger.error(f"❌ Exception: {e}")

- Line 156: `    logger.info(f"📊 测试结果: {passed} 通过, {failed} 失败")`
  - Translation:     logger.info(f"📊 Test results: {passed} passed, {failed} failed")

- Line 159: `        logger.info("🎉 所有演示通过！ANP SDK 工作正常。")`
  - Translation:         logger.info("🎉 All demos passed! ANP SDK is working properly.")

- Line 161: `        logger.warning("⚠️  部分演示失败，请检查环境和配置。")`
  - Translation:         logger.warning("⚠️  Some demonstrations failed, please check the environment and configuration.")


## ./test/test_auth_refactor.py

- Line 3: `认证模块重构测试`
  - Translation: Authentication module refactoring test

- Line 5: `测试从文件路径操作到内存数据操作的重构前后功能一致性`
  - Translation: Test the consistency of functionality before and after refactoring from file path operations to memory data operations.

- Line 17: `# 添加项目路径`
  - Translation: # Add project path

- Line 35: `    """认证重构测试类"""`
  - Translation:     """Authentication Refactoring Test Class"""

- Line 39: `        """设置测试环境"""`
  - Translation:         """Set up the test environment"""

- Line 46: `        """清理测试环境"""`
  - Translation:         """Clean up the test environment"""

- Line 51: `        """每个测试方法前的设置"""`
  - Translation:         Setup before each test method

- Line 52: `        # 创建测试用户`
  - Translation:         # Create test user

- Line 56: `        """创建测试用户"""`
  - Translation:         Create test user

- Line 78: `                logger.info(f"创建测试用户: {did_doc['id']}")`
  - Translation:                 logger.info(f"Create test user: {did_doc['id']}")

- Line 81: `        """测试从文件路径创建DID凭证"""`
  - Translation:         Test creating DID credentials from file path

- Line 83: `            pytest.skip("没有可用的测试用户")`
  - Translation:             pytest.skip("No test users available")

- Line 88: `        # 测试从文件路径创建凭证`
  - Translation:         # Test creating credentials from file path

- Line 99: `        logger.info("✅ DID凭证从文件路径创建测试通过")`
  - Translation:         logger.info("✅ DID credential creation from file path test passed")

- Line 102: `        """测试DID凭证的内存操作"""`
  - Translation:         Test memory operations of DID credentials

- Line 104: `            pytest.skip("没有可用的测试用户")`
  - Translation:             pytest.skip("No test user available")

- Line 109: `        # 从文件创建凭证`
  - Translation:         # Create credentials from file

- Line 115: `        # 测试内存操作`
  - Translation:         # Test memory operations

- Line 121: `        # 测试添加新密钥对`
  - Translation:         # Test adding a new key pair

- Line 131: `        logger.info("✅ DID凭证内存操作测试通过")`
  - Translation:         logger.info("✅ DID credential memory operation test passed")

- Line 134: `        """测试认证头构建"""`
  - Translation:         Test authentication header construction

- Line 136: `            pytest.skip("需要至少2个测试用户")`
  - Translation:             pytest.skip("Requires at least 2 test users")

- Line 142: `        # 创建认证上下文`
  - Translation:         # Create authentication context

- Line 151: `        # 创建凭证`
  - Translation:         # Create credential

- Line 157: `        # 测试认证头构建`
  - Translation:         # Test authentication header construction

- Line 164: `        logger.info("✅ 认证头构建测试通过")`
  - Translation:         logger.info("✅ Authentication header construction test passed")

- Line 167: `        """测试完整的认证流程"""`
  - Translation:         """Test the complete authentication process"""

- Line 169: `            pytest.skip("需要至少2个测试用户")`
  - Translation:             pytest.skip("Requires at least 2 test users")

- Line 171: `        # 启动SDK服务器`
  - Translation:         # Start the SDK server

- Line 174: `        # 创建智能体`
  - Translation:         # Create Agent

- Line 178: `        # 注册API处理器`
  - Translation:         # Register API handler

- Line 181: `            return {"status": "success", "message": "API调用成功"}`
  - Translation:             return {"status": "success", "message": "API call successful"}

- Line 183: `        # 注册智能体`
  - Translation:         # Register Agent

- Line 187: `        # 启动服务器（在后台）`
  - Translation:         # Start the server (in the background)

- Line 192: `        # 等待服务器启动`
  - Translation:         # Waiting for the server to start

- Line 196: `            # 测试认证请求`
  - Translation:             # Test authentication request

- Line 205: `            assert success, f"认证失败: {message}"`
  - Translation:             assert success, f"Authentication failed: {message}"

- Line 206: `            assert status == 200, f"HTTP状态码错误: {status}"`
  - Translation:             assert status == 200, f"HTTP status code error: {status}"

- Line 208: `            logger.info("✅ 完整认证流程测试通过")`
  - Translation:             logger.info("✅ Full authentication process test passed")

- Line 211: `            # 清理`
  - Translation:             # Cleanup

- Line 216: `        """测试令牌操作"""`
  - Translation:         Test token operation

- Line 218: `            pytest.skip("没有可用的测试用户")`
  - Translation:             pytest.skip("No test users available")

- Line 223: `        # 测试存储令牌`
  - Translation:         # Test storage token

- Line 227: `        # 测试获取令牌`
  - Translation:         # Test for obtaining token

- Line 232: `        # 测试撤销令牌`
  - Translation:         # Test revoke token

- Line 235: `        logger.info("✅ 令牌操作测试通过")`
  - Translation:         logger.info("✅ Token operation test passed")

- Line 238: `        """测试联系人管理"""`
  - Translation:         Test contact management

- Line 240: `            pytest.skip("没有可用的测试用户")`
  - Translation:             pytest.skip("No test users available")

- Line 244: `        # 测试添加联系人`
  - Translation:         # Test adding a contact

- Line 247: `            "name": "测试联系人",`
  - Translation:             "name": "Test Contact",

- Line 254: `        # 测试获取联系人`
  - Translation:         # Test to retrieve contacts

- Line 259: `        # 测试列出所有联系人`
  - Translation:         # Test to list all contacts

- Line 264: `        logger.info("✅ 联系人管理测试通过")`
  - Translation:         logger.info("✅ Contact management test passed")

- Line 267: `        """测试内存操作与文件操作的一致性"""`
  - Translation:         """Test the consistency between memory operations and file operations"""

- Line 269: `            pytest.skip("没有可用的测试用户")`
  - Translation:             pytest.skip("No test users available")

- Line 274: `        # 从文件创建凭证`
  - Translation:         # Create credentials from file

- Line 280: `        # 验证DID文档一致性`
  - Translation:         # Verify DID document consistency

- Line 283: `        # 验证密钥对一致性`
  - Translation:         # Verify key pair consistency

- Line 289: `        logger.info("✅ 内存与文件操作一致性测试通过")`
  - Translation:         logger.info("✅ Memory and file operation consistency test passed")

- Line 292: `    """运行所有认证测试"""`
  - Translation:     """Run all authentication tests"""

- Line 295: `    # 设置日志`
  - Translation:     # Set up logging

- Line 301: `    # 运行测试`
  - Translation:     # Run tests

- Line 306: `    """运行异步测试"""`
  - Translation:     """Run asynchronous tests"""

- Line 313: `        # 运行同步测试`
  - Translation:         # Run synchronization test

- Line 318: `        # 运行异步测试`
  - Translation:         # Run asynchronous test

- Line 324: `        logger.info("🎉 所有认证测试通过！")`
  - Translation:         logger.info("🎉 All authentication tests passed!")

- Line 327: `        logger.error(f"❌ 测试失败: {e}")`
  - Translation:         logger.error(f"❌ Test failed: {e}")

- Line 333: `    # 可以选择运行pytest或直接运行异步测试`
  - Translation:     # You can choose to run pytest or directly run asynchronous tests.


## ./test/test_unified_config.py

- Line 3: `统一配置系统测试脚本`
  - Translation: Unified configuration system test script

- Line 5: `测试内容：`
  - Translation: Test content:

- Line 6: `1. 基本配置加载和访问`
  - Translation: 1. Basic configuration loading and access

- Line 7: `2. 属性访问和代码提示`
  - Translation: 2. Attribute access and code suggestions

- Line 8: `3. 环境变量映射和类型转换`
  - Translation: 3. Environment variable mapping and type conversion

- Line 9: `4. 路径解析和占位符替换`
  - Translation: 4. Path parsing and placeholder replacement

- Line 10: `5. 敏感信息保护`
  - Translation: 5. Sensitive Information Protection

- Line 11: `6. 向后兼容性`
  - Translation: 6. Backward compatibility

- Line 21: `# 添加项目路径`
  - Translation: # Add project path

- Line 25: `    """测试基本配置加载"""`
  - Translation:     Test basic configuration loading

- Line 26: `    logger.info("\n=== 测试1: 基本配置加载 ===")`
  - Translation:     logger.info("\n=== Test 1: Basic Configuration Loading ===")

- Line 31: `        # 测试配置加载`
  - Translation:         # Test configuration loading

- Line 32: `        logger.info(f"✅ 配置文件路径: {config._config_file}")`
  - Translation:         logger.info(f"✅ Configuration file path: {config._config_file}")

- Line 33: `        logger.info(f"✅ 项目根目录: {config.get_app_root()}")`
  - Translation:         logger.info(f"✅ Project root directory: {config.get_app_root()}")

- Line 35: `        # 测试基本配置访问`
  - Translation:         # Test basic configuration access

- Line 36: `        logger.info(f"✅ ANP SDK端口: {config.anp_sdk.port}")`
  - Translation:         logger.info(f"✅ ANP SDK Port: {config.anp_sdk.port}")

- Line 37: `        logger.info(f"✅ ANP SDK主机: {config.anp_sdk.host}")`
  - Translation:         logger.info(f"✅ ANP SDK Host: {config.anp_sdk.host}")

- Line 38: `        logger.info(f"✅ 调试模式: {config.anp_sdk.debug_mode}")`
  - Translation:         logger.info(f"✅ Debug Mode: {config.anp_sdk.debug_mode}")

- Line 42: `        logger.error(f"❌ 基本配置加载失败: {e}")`
  - Translation:         logger.error(f"❌ Failed to load basic configuration: {e}")

- Line 46: `    """测试属性访问"""`
  - Translation:     """Test attribute access"""

- Line 47: `    logger.info("\n=== 测试2: 属性访问 ===")`
  - Translation:     logger.info("\n=== Test 2: Attribute Access ===")

- Line 52: `        # 测试多级属性访问`
  - Translation:         # Test multi-level attribute access

- Line 53: `        logger.info(f"✅ LLM模型: {config.llm.default_model}")`
  - Translation:         logger.info(f"✅ LLM Model: {config.llm.default_model}")

- Line 54: `        logger.info(f"✅ LLM最大Token: {config.llm.max_tokens}")`
  - Translation:         logger.info(f"✅ LLM Maximum Tokens: {config.llm.max_tokens}")

- Line 55: `        logger.info(f"✅ 邮件SMTP端口: {config.mail.smtp_port}")`
  - Translation:         logger.info(f"✅ Email SMTP Port: {config.mail.smtp_port}")

- Line 57: `        # 测试智能体配置`
  - Translation:         # Test agent configuration

- Line 58: `        logger.info(f"✅ 演示智能体1: {config.anp_sdk.agent.demo_agent1}")`
  - Translation:         logger.info(f"✅ Demo Agent 1: {config.anp_sdk.agent.demo_agent1}")

- Line 59: `        logger.info(f"✅ 演示智能体2: {config.anp_sdk.agent.demo_agent2}")`
  - Translation:         logger.info(f"✅ Demonstration Agent 2: {config.anp_sdk.agent.demo_agent2}")

- Line 61: `        # 测试配置修改`
  - Translation:         # Test configuration modification

- Line 64: `        logger.info(f"✅ 修改端口: {original_port} -> {config.anp_sdk.port}")`
  - Translation:         logger.info(f"✅ Port changed: {original_port} -> {config.anp_sdk.port}")

- Line 65: `        config.anp_sdk.port = original_port  # 恢复`
  - Translation:         config.anp_sdk.port = original_port  # Restore

- Line 69: `        logger.error(f"❌ 属性访问测试失败: {e}")`
  - Translation:         logger.error(f"❌ Attribute access test failed: {e}")

- Line 73: `    """测试环境变量"""`
  - Translation:     "Test environment variables"

- Line 74: `    logger.info("\n=== 测试3: 环境变量映射 ===")`
  - Translation:     logger.info("\n=== Test 3: Environment Variable Mapping ===")

- Line 79: `        # 设置测试环境变量`
  - Translation:         # Set test environment variables

- Line 84: `        # 重新加载环境变量`
  - Translation:         # Reload environment variables

- Line 87: `        # 测试预定义环境变量`
  - Translation:         # Test predefined environment variables

- Line 88: `        logger.info(f"✅ 调试模式 (ANP_DEBUG): {config.env.debug_mode}")`
  - Translation:         logger.info(f"✅ Debug Mode (ANP_DEBUG): {config.env.debug_mode}")

- Line 89: `        logger.info(f"✅ 端口 (ANP_PORT): {config.env.port}")`
  - Translation:         logger.info(f"✅ Port (ANP_PORT): {config.env.port}")

- Line 90: `        logger.info(f"✅ 端口类型: {type(config.env.port)}")`
  - Translation:         logger.info(f"✅ Port type: {type(config.env.port)}")

- Line 92: `        # 测试动态环境变量`
  - Translation:         # Test dynamic environment variables

- Line 93: `        logger.info(f"✅ 测试变量 (TEST_VAR): {config.env.test_var}")`
  - Translation:         logger.info(f"✅ Test Variable (TEST_VAR): {config.env.test_var}")

- Line 95: `        # 测试系统环境变量`
  - Translation:         # Test system environment variables

- Line 97: `            logger.info(f"✅ PATH路径数量: {len(config.env.system_path)}")`
  - Translation:             logger.info(f"✅ Number of PATH paths: {len(config.env.system_path)}")

- Line 98: `            logger.info(f"✅ 第一个PATH: {config.env.system_path[0]}")`
  - Translation:             logger.info(f"✅ First PATH: {config.env.system_path[0]}")

- Line 101: `            logger.info(f"✅ 用户主目录: {config.env.home_dir}")`
  - Translation:             logger.info(f"✅ User home directory: {config.env.home_dir}")

- Line 102: `            logger.info(f"✅ 主目录类型: {type(config.env.home_dir)}")`
  - Translation:             logger.info(f"✅ Main directory type: {type(config.env.home_dir)}")

- Line 106: `        logger.error(f"❌ 环境变量测试失败: {e}")`
  - Translation:         logger.error(f"❌ Environment variable test failed: {e}")

- Line 110: `    """测试路径解析"""`
  - Translation:     Test path parsing

- Line 111: `    logger.info("\n=== 测试4: 路径解析 ===")`
  - Translation:     logger.info("\n=== Test 4: Path Parsing ===")

- Line 116: `        # 测试占位符解析`
  - Translation:         # Test placeholder parsing

- Line 119: `        logger.info(f"✅ 原始路径: {user_path}")`
  - Translation:         logger.info(f"✅ Original path: {user_path}")

- Line 120: `        logger.info(f"✅ 解析后路径: {resolved_path}")`
  - Translation:         logger.info(f"✅ Resolved path: {resolved_path}")

- Line 121: `        logger.info(f"✅ 是否为绝对路径: {resolved_path.is_absolute()}")`
  - Translation:         logger.info(f"✅ Is it an absolute path: {resolved_path.is_absolute()}")

- Line 123: `        # 测试相对路径解析`
  - Translation:         # Test relative path resolution

- Line 125: `        logger.info(f"✅ 相对路径解析: {relative_path}")`
  - Translation:         logger.info(f"✅ Relative path resolution: {relative_path}")

- Line 127: `        # 测试手动占位符`
  - Translation:         # Test manual placeholder

- Line 129: `        logger.info(f"✅ 手动占位符: {manual_path}")`
  - Translation:         logger.info(f"✅ Manual placeholder: {manual_path}")

- Line 133: `        logger.error(f"❌ 路径解析测试失败: {e}")`
  - Translation:         logger.error(f"❌ Path parsing test failed: {e}")

- Line 137: `    """测试敏感信息"""`
  - Translation:     Test sensitive information

- Line 138: `    logger.info("\n=== 测试5: 敏感信息保护 ===")`
  - Translation:     logger.info("\n=== Test 5: Sensitive Information Protection ===")

- Line 143: `        # 设置敏感信息环境变量`
  - Translation:         # Set sensitive information environment variables

- Line 147: `        # 测试敏感信息访问`
  - Translation:         # Test sensitive information access

- Line 151: `        logger.info(f"✅ API密钥存在: {api_key is not None}")`
  - Translation:         logger.info(f"✅ API key exists: {api_key is not None}")

- Line 152: `        logger.info(f"✅ 邮件密码存在: {mail_pwd is not None}")`
  - Translation:         logger.info(f"✅ Email password exists: {mail_pwd is not None}")

- Line 153: `        logger.info(f"✅ API密钥前缀: {api_key[:10] if api_key else 'None'}...")`
  - Translation:         logger.info(f"✅ API key prefix: {api_key[:10] if api_key else 'None'}...")

- Line 155: `        # 测试敏感信息不在普通配置中`
  - Translation:         # Test that sensitive information is not in the regular configuration.

- Line 157: `        logger.info(f"✅ 敏感信息字典: {secrets_dict}")`
  - Translation:         logger.info(f"✅ Sensitive information dictionary: {secrets_dict}")

- Line 161: `        logger.error(f"❌ 敏感信息测试失败: {e}")`
  - Translation:         logger.error(f"❌ Sensitive information test failed: {e}")

- Line 165: `    """测试路径工具"""`
  - Translation:     """Test Path Tool"""

- Line 166: `    logger.info("\n=== 测试6: 路径工具 ===")`
  - Translation:     logger.info("\n=== Test 6: Path Utility ===")

- Line 169: `        # 先检查原始 PATH 环境变量`
  - Translation:         # First, check the original PATH environment variable.

- Line 171: `        logger.info(f"✅ 原始PATH长度: {len(raw_path)}")`
  - Translation:         logger.info(f"✅ Original PATH length: {len(raw_path)}")

- Line 173: `        # 测试在PATH中查找文件`
  - Translation:         # Test for finding files in PATH

- Line 174: `        # 分别测试每个功能，避免一个错误影响全部`
  - Translation:         # Test each function separately to prevent one error from affecting everything.

- Line 179: `                logger.info(f"✅ 找到Python3: {python_paths[0]}")`
  - Translation:                 logger.info(f"✅ Python3 found: {python_paths[0]}")

- Line 181: `                logger.warning("⚠️  未找到Python3")`
  - Translation:                 logger.warning("⚠️  Python3 not found")

- Line 183: `            logger.warning(f"⚠️  查找Python3时出错: {e}")`
  - Translation:             logger.warning(f"⚠️  Error occurred while searching for Python3: {e}")

- Line 186: `        # 测试路径信息`
  - Translation:         # Test path information

- Line 188: `        logger.info(f"✅ 路径信息: {path_info}")`
  - Translation:         logger.info(f"✅ Path information: {path_info}")

- Line 190: `        # 测试添加路径到PATH（谨慎测试）`
  - Translation:         # Test adding path to PATH (test with caution)

- Line 199: `        logger.info(f"✅ 路径已添加: {test_path in new_path}")`
  - Translation:         logger.info(f"✅ Path added: {test_path in new_path}")

- Line 201: `        # 恢复原始PATH`
  - Translation:         # Restore original PATH

- Line 206: `        logger.error(f"❌ 路径工具测试失败: {e}")`
  - Translation:         logger.error(f"❌ Path tool test failed: {e}")

- Line 212: `    """测试配置持久化"""`
  - Translation:     "Test configuration persistence"

- Line 213: `    logger.info("\n=== 测试8: 配置持久化 ===")`
  - Translation:     logger.info("\n=== Test 8: Configuration Persistence ===")

- Line 218: `        # 创建临时配置文件`
  - Translation:         # Create temporary configuration file

- Line 229: `        # 使用临时配置创建新的配置实例`
  - Translation:         # Create a new configuration instance using temporary settings

- Line 233: `        logger.info(f"✅ 临时配置端口: {temp_config.anp_sdk.port}")`
  - Translation:         logger.info(f"✅ Temporary configuration port: {temp_config.anp_sdk.port}")

- Line 234: `        logger.info(f"✅ 临时配置主机: {temp_config.anp_sdk.host}")`
  - Translation:         logger.info(f"✅ Temporary configuration host: {temp_config.anp_sdk.host}")

- Line 236: `        # 修改并保存`
  - Translation:         # Modify and save

- Line 239: `        logger.info(f"✅ 配置保存成功: {success}")`
  - Translation:         logger.info(f"✅ Configuration saved successfully: {success}")

- Line 241: `        # 重新加载验证`
  - Translation:         # Reload verification

- Line 243: `        logger.info(f"✅ 重新加载后端口: {temp_config.anp_sdk.port}")`
  - Translation:         logger.info(f"✅ Reloaded backend port: {temp_config.anp_sdk.port}")

- Line 245: `        # 清理`
  - Translation:         # Cleanup

- Line 250: `        logger.error(f"❌ 配置持久化测试失败: {e}")`
  - Translation:         logger.error(f"❌ Configuration persistence test failed: {e}")

- Line 254: `    """测试类型转换"""`
  - Translation:     """Test type conversion"""

- Line 255: `    logger.info("\n=== 测试9: 类型转换 ===")`
  - Translation:     logger.info("\n=== Test 9: Type Conversion ===")

- Line 260: `        # 设置不同类型的环境变量`
  - Translation:         # Set different types of environment variables

- Line 273: `        # 测试类型转换`
  - Translation:         # Test type conversion

- Line 276: `        # 创建临时配置测试类型转换`
  - Translation:         # Create temporary configuration test type conversion

- Line 301: `        logger.info(f"✅ 布尔值(true): {temp_config.env.test_bool_true} ({type(temp_config.env.test_bool_true)})")`
  - Translation:         logger.info(f"✅ Boolean value (true): {temp_config.env.test_bool_true} ({type(temp_config.env.test_bool_true)})")

- Line 302: `        logger.info(f"✅ 布尔值(false): {temp_config.env.test_bool_false} ({type(temp_config.env.test_bool_false)})")`
  - Translation:         logger.info(f"✅ Boolean value (false): {temp_config.env.test_bool_false} ({type(temp_config.env.test_bool_false)})")

- Line 303: `        logger.info(f"✅ 整数: {temp_config.env.test_int} ({type(temp_config.env.test_int)})")`
  - Translation:         logger.info(f"✅ Integer: {temp_config.env.test_int} ({type(temp_config.env.test_int)})")

- Line 304: `        logger.info(f"✅ 浮点数: {temp_config.env.test_float} ({type(temp_config.env.test_float)})")`
  - Translation:         logger.info(f"✅ Float: {temp_config.env.test_float} ({type(temp_config.env.test_float)})")

- Line 305: `        logger.info(f"✅ 列表: {temp_config.env.test_list} ({type(temp_config.env.test_list)})")`
  - Translation:         logger.info(f"✅ List: {temp_config.env.test_list} ({type(temp_config.env.test_list)})")

- Line 306: `        logger.info(f"✅ 路径: {temp_config.env.test_path} ({type(temp_config.env.test_path)})")`
  - Translation:         logger.info(f"✅ Path: {temp_config.env.test_path} ({type(temp_config.env.test_path)})")

- Line 308: `        # 清理`
  - Translation:         # Cleanup

- Line 313: `        logger.error(f"❌ 类型转换测试失败: {e}")`
  - Translation:         logger.error(f"❌ Type conversion test failed: {e}")

- Line 317: `    """测试错误处理"""`
  - Translation:     Test error handling

- Line 318: `    logger.info("\n=== 测试10: 错误处理 ===")`
  - Translation:     logger.info("\n=== Test 10: Error Handling ===")

- Line 323: `        # 测试访问不存在的配置项`
  - Translation:         # Test access to non-existent configuration items

- Line 326: `            logger.error("❌ 应该抛出AttributeError")`
  - Translation:             logger.error("❌ An AttributeError should be raised")

- Line 329: `            logger.info(f"✅ 正确处理不存在的配置项: {e}")`
  - Translation:             logger.info(f"✅ Correctly handled non-existent configuration item: {e}")

- Line 331: `        # 测试访问不存在的环境变量`
  - Translation:         # Test accessing a non-existent environment variable

- Line 333: `        logger.info(f"✅ 不存在的环境变量返回: {nonexistent_env}")`
  - Translation:         logger.info(f"✅ Nonexistent environment variable returned: {nonexistent_env}")

- Line 335: `        # 测试访问不存在的敏感信息`
  - Translation:         # Test access to non-existent sensitive information

- Line 338: `            logger.error("❌ 应该抛出AttributeError")`
  - Translation:             logger.error("❌ Should throw AttributeError")

- Line 341: `            logger.info(f"✅ 正确处理不存在的敏感信息: {e}")`
  - Translation:             logger.info(f"✅ Correctly handled non-existent sensitive information: {e}")

- Line 345: `        logger.error(f"❌ 错误处理测试失败: {e}")`
  - Translation:         logger.error(f"❌ Error handling test failed: {e}")

- Line 349: `    """运行所有测试"""`
  - Translation:     """Run all tests"""

- Line 350: `    logger.info("🚀 开始统一配置系统测试")`
  - Translation:     logger.info("🚀 Starting unified configuration system test")

- Line 372: `                logger.info("✅ 通过")`
  - Translation:                 logger.info("✅ Passed")

- Line 375: `                logger.error("❌ 失败")`
  - Translation:                 logger.error("❌ Failure")

- Line 378: `            logger.error(f"❌ 异常: {e}")`
  - Translation:             logger.error(f"❌ Exception: {e}")

- Line 381: `    logger.info(f"📊 测试结果: {passed} 通过, {failed} 失败")`
  - Translation:     logger.info(f"📊 Test results: {passed} passed, {failed} failed")

- Line 384: `        logger.info("🎉 所有测试通过！统一配置系统工作正常。")`
  - Translation:         logger.info("🎉 All tests passed! Unified configuration system is functioning properly.")

- Line 386: `        logger.warning("⚠️  部分测试失败，请检查配置。")`
  - Translation:         logger.warning("⚠️  Some tests failed, please check the configuration.")


## ./test/test_auth_integration.py

- Line 3: `认证模块集成测试`
  - Translation: Integration test for the authentication module

- Line 5: `验证重构后的认证模块与现有系统的完整集成`
  - Translation: Verify the complete integration of the refactored authentication module with the existing system.

- Line 13: `# 添加项目路径`
  - Translation: # Add project path

- Line 16: `# 初始化配置`
  - Translation: # Initialize configuration

- Line 19: `# 设置应用根目录为项目根目录`
  - Translation: # Set the application root directory as the project root directory.

- Line 30: `# 设置日志`
  - Translation: # Set up logging

- Line 38: `    """创建测试用户"""`
  - Translation:     """Create test user"""

- Line 39: `    logger.info("=== 创建测试用户 ===")`
  - Translation:     logger.info("=== Creating test user ===")

- Line 54: `            logger.info(f"✅ 用户{i+1}创建成功: {did_doc['id']}")`
  - Translation:             logger.info(f"✅ User {i+1} created successfully: {did_doc['id']}")

- Line 56: `            logger.error(f"❌ 用户{i+1}创建失败")`
  - Translation:             logger.error(f"❌ User {i+1} creation failed")

- Line 62: `    """测试新旧方式的兼容性"""`
  - Translation:     Test the compatibility of new and old methods

- Line 63: `    logger.info("=== 测试新旧方式兼容性 ===")`
  - Translation:     logger.info("=== Testing compatibility between new and old methods ===")

- Line 69: `        logger.error("❌ 用户数据获取失败")`
  - Translation:         logger.error("❌ Failed to retrieve user data")

- Line 73: `        # 方式1：传统文件路径方式`
  - Translation:         # Method 1: Traditional file path method

- Line 79: `        # 方式2：新的内存方式`
  - Translation:         # Method 2: New memory approach

- Line 82: `        # 验证两种方式创建的凭证是否一致`
  - Translation:         # Verify whether the credentials created by the two methods are consistent.

- Line 86: `        # 验证密钥对是否一致`
  - Translation:         # Verify whether the key pair is consistent.

- Line 93: `        logger.info("✅ 新旧方式创建的凭证完全一致")`
  - Translation:         logger.info("✅ The credentials created by the new and old methods are completely consistent")

- Line 97: `        logger.error(f"❌ 兼容性测试失败: {e}")`
  - Translation:         logger.error(f"❌ Compatibility test failed: {e}")

- Line 101: `    """测试认证头一致性"""`
  - Translation:     Test authentication header consistency

- Line 102: `    logger.info("=== 测试认证头一致性 ===")`
  - Translation:     logger.info("=== Testing Authentication Header Consistency ===")

- Line 108: `        # 创建认证上下文`
  - Translation:         # Create authentication context

- Line 117: `        # 方式1：使用传统认证器`
  - Translation:         # Method 1: Use traditional authenticator

- Line 126: `        # 方式2：使用内存版认证器`
  - Translation:         # Method 2: Use in-memory authenticator

- Line 134: `        # 验证认证头结构一致性`
  - Translation:         # Verify the consistency of the authentication header structure.

- Line 138: `        # 验证认证头都包含Authorization字段`
  - Translation:         # Verify that all authentication headers contain the Authorization field.

- Line 139: `        logger.info("✅ 认证头结构验证通过")`
  - Translation:         logger.info("✅ Authentication header structure validation passed")

- Line 140: `        logger.info(f"  旧版本认证头: {auth_headers_old['Authorization'][:50]}...")`
  - Translation:         logger.info(f"  Old version authentication header: {auth_headers_old['Authorization'][:50]}...")

- Line 141: `        logger.info(f"  新版本认证头: {auth_headers_new['Authorization'][:50]}...")`
  - Translation:         logger.info(f"  New version authentication header: {auth_headers_new['Authorization'][:50]}...")

- Line 143: `        # 解析认证头参数（简化版本，只验证基本结构）`
  - Translation:         # Parse authentication header parameters (simplified version, only verify basic structure)

- Line 145: `            # 检查是否包含基本的DID认证格式（支持DIDWba和DID-WBA）`
  - Translation:             # Check if it contains the basic DID authentication format (supports DIDWba and DID-WBA)

- Line 153: `        assert old_valid, "旧版本认证头格式无效"`
  - Translation:         assert old_valid, "The old version authentication header format is invalid"

- Line 154: `        assert new_valid, "新版本认证头格式无效"`
  - Translation:         assert new_valid, "The new version authentication header format is invalid"

- Line 156: `        logger.info("✅ 认证头格式验证通过")`
  - Translation:         logger.info("✅ Authentication header format validation passed")

- Line 161: `        logger.error(f"❌ 认证头一致性测试失败: {e}")`
  - Translation:         logger.error(f"❌ Authentication header consistency test failed: {e}")

- Line 165: `    """测试与LocalAgent的集成"""`
  - Translation:     """Test integration with LocalAgent"""

- Line 166: `    logger.info("=== 测试LocalAgent集成 ===")`
  - Translation:     logger.info("=== Testing LocalAgent Integration ===")

- Line 169: `        # 创建智能体`
  - Translation:         # Create Agent

- Line 174: `            logger.info(f"✅ 智能体创建成功: {agent.name}")`
  - Translation:             logger.info(f"✅ Agent created successfully: {agent.name}")

- Line 176: `        # 测试智能体的内存凭证`
  - Translation:         # Test the agent's memory credentials

- Line 184: `            # 测试密钥操作`
  - Translation:             # Test key operation

- Line 190: `            assert len(private_key_bytes) == 32  # secp256k1私钥长度`
  - Translation:             assert len(private_key_bytes) == 32  # secp256k1 private key length

- Line 191: `            assert len(public_key_bytes) == 65   # 未压缩公钥长度`
  - Translation:             assert len(public_key_bytes) == 65   # Uncompressed public key length

- Line 193: `        logger.info("✅ LocalAgent集成测试通过")`
  - Translation:         logger.info("✅ LocalAgent integration test passed")

- Line 197: `        logger.error(f"❌ LocalAgent集成测试失败: {e}")`
  - Translation:         logger.error(f"❌ LocalAgent integration test failed: {e}")

- Line 201: `    """性能基准测试"""`
  - Translation:     """Performance Benchmarking"""

- Line 202: `    logger.info("=== 性能基准测试 ===")`
  - Translation:     logger.info("=== Performance Benchmarking ===")

- Line 210: `        # 测试凭证创建性能`
  - Translation:         # Test credential creation performance

- Line 213: `        # 文件版本性能`
  - Translation:         # File version performance

- Line 222: `        # 内存版本性能`
  - Translation:         # Memory version performance

- Line 228: `        # 认证头构建性能`
  - Translation:         # Authentication Header Construction Performance

- Line 237: `        # 文件版本认证头构建`
  - Translation:         # File version authentication header construction

- Line 248: `        # 内存版本认证头构建`
  - Translation:         # Memory Version Authentication Header Construction

- Line 258: `        logger.info("✅ 性能基准测试完成")`
  - Translation:         logger.info("✅ Performance benchmark test completed")

- Line 259: `        logger.info(f"  凭证创建 - 文件版本 ({iterations}次): {file_time:.4f}秒")`
  - Translation:         logger.info(f"  Voucher Creation - File Version ({iterations} times): {file_time:.4f} seconds")

- Line 260: `        logger.info(f"  凭证创建 - 内存版本 ({iterations}次): {memory_time:.4f}秒")`
  - Translation:         logger.info(f"  Voucher creation - memory version ({iterations} times): {memory_time:.4f} seconds")

- Line 261: `        logger.info(f"  凭证创建性能提升: {file_time/memory_time:.2f}x")`
  - Translation:         logger.info(f"  Voucher creation performance improvement: {file_time/memory_time:.2f}x")

- Line 262: `        logger.info(f"  认证头构建 - 文件版本 ({iterations}次): {file_auth_time:.4f}秒")`
  - Translation:         logger.info(f"  Authentication Header Construction - File Version ({iterations} times): {file_auth_time:.4f} seconds")

- Line 263: `        logger.info(f"  认证头构建 - 内存版本 ({iterations}次): {memory_auth_time:.4f}秒")`
  - Translation:         logger.info(f"  Authentication header construction - in-memory version ({iterations} times): {memory_auth_time:.4f} seconds")

- Line 264: `        logger.info(f"  认证头构建性能提升: {file_auth_time/memory_auth_time:.2f}x")`
  - Translation:         logger.info(f"  Authentication header construction performance improvement: {file_auth_time/memory_auth_time:.2f}x")

- Line 269: `        logger.error(f"❌ 性能基准测试失败: {e}")`
  - Translation:         logger.error(f"❌ Performance benchmark test failed: {e}")

- Line 273: `    """运行集成测试"""`
  - Translation:     """Run integration tests"""

- Line 274: `    logger.info("🚀 开始认证模块集成测试")`
  - Translation:     logger.info("🚀 Starting authentication module integration test")

- Line 277: `    # 1. 创建测试用户`
  - Translation:     # 1. Create test user

- Line 280: `        logger.error("❌ 测试用户创建失败")`
  - Translation:         logger.error("❌ Failed to create test user")

- Line 283: `    # 2. 测试新旧方式兼容性`
  - Translation:     # 2. Test compatibility between new and old methods

- Line 287: `    # 3. 测试认证头一致性`
  - Translation:     # 3. Test authentication header consistency

- Line 291: `    # 4. 测试LocalAgent集成`
  - Translation:     # 4. Test LocalAgent integration

- Line 295: `    # 5. 性能基准测试`
  - Translation:     # 5. Performance Benchmark Testing

- Line 300: `    logger.info("🎉 所有集成测试通过！")`
  - Translation:     logger.info("🎉 All integration tests passed!")

- Line 301: `    logger.info("✨ 认证模块重构完全成功")`
  - Translation:     logger.info("✨ Authentication module refactoring completely successful")

- Line 302: `    logger.info("📈 性能显著提升，向后兼容性完美")`
  - Translation:     logger.info("📈 Significant performance improvement, perfect backward compatibility")


## ./test/test_memory_auth.py

- Line 3: `内存版本认证功能测试`
  - Translation: Memory version authentication feature test

- Line 5: `测试新的内存数据操作认证功能`
  - Translation: Test the new memory data operation authentication feature.

- Line 13: `# 添加项目路径`
  - Translation: # Add project path

- Line 16: `# 初始化配置`
  - Translation: # Initialize configuration

- Line 19: `# 设置应用根目录为项目根目录`
  - Translation: # Set the application root directory as the project root directory.

- Line 28: `# 设置日志`
  - Translation: # Set up logging

- Line 36: `    """测试内存凭证创建"""`
  - Translation:     Test memory credential creation

- Line 37: `    logger.info("=== 测试内存凭证创建 ===")`
  - Translation:     logger.info("=== Testing Memory Credential Creation ===")

- Line 39: `    # 创建测试用户`
  - Translation:     # Create test user

- Line 50: `        logger.error("❌ 用户创建失败")`
  - Translation:         logger.error("❌ User creation failed")

- Line 53: `    logger.info(f"✅ 用户创建成功: {did_doc['id']}")`
  - Translation:     logger.info(f"✅ User created successfully: {did_doc['id']}")

- Line 55: `    # 获取用户数据`
  - Translation:     # Retrieve user data

- Line 60: `        logger.error("❌ 用户数据获取失败")`
  - Translation:         logger.error("❌ Failed to retrieve user data")

- Line 63: `    # 测试内存凭证创建`
  - Translation:     # Test memory credential creation

- Line 67: `            logger.info(f"✅ 内存凭证创建成功")`
  - Translation:             logger.info(f"✅ Memory credential created successfully")

- Line 69: `            logger.info(f"  密钥对数量: {len(credentials.key_pairs)}")`
  - Translation:             logger.info(f"  Number of key pairs: {len(credentials.key_pairs)}")

- Line 72: `            logger.error("❌ 内存凭证创建失败")`
  - Translation:             logger.error("❌ Memory credential creation failed")

- Line 75: `        logger.error(f"❌ 内存凭证创建异常: {e}")`
  - Translation:         logger.error(f"❌ Memory credential creation exception: {e}")

- Line 79: `    """测试内存版本认证头构建"""`
  - Translation:     "Test memory version authentication header construction"

- Line 80: `    logger.info("=== 测试内存版本认证头构建 ===")`
  - Translation:     logger.info("=== Testing Memory Version Authentication Header Construction ===")

- Line 83: `        # 创建认证上下文`
  - Translation:         # Create authentication context

- Line 92: `        # 使用内存版本构建器`
  - Translation:         # Use the in-memory version builder

- Line 96: `        logger.info(f"✅ 内存版本认证头构建成功")`
  - Translation:         logger.info(f"✅ Memory version authentication header constructed successfully")

- Line 97: `        logger.info(f"  认证头键数量: {len(auth_headers)}")`
  - Translation:         logger.info(f"  Number of authentication header keys: {len(auth_headers)}")

- Line 99: `            logger.info(f"  包含Authorization头")`
  - Translation:             logger.info(f"  Contains Authorization header")

- Line 100: `            logger.info(f"  认证头内容: {auth_headers['Authorization'][:100]}...")`
  - Translation:             logger.info(f"  Authentication header content: {auth_headers['Authorization'][:100]}...")

- Line 105: `        logger.error(f"❌ 内存版本认证头构建失败: {e}")`
  - Translation:         logger.error(f"❌ Memory version authentication header construction failed: {e}")

- Line 109: `    """测试内存认证包装器"""`
  - Translation:     """Test memory authentication wrapper"""

- Line 110: `    logger.info("=== 测试内存认证包装器 ===")`
  - Translation:     logger.info("=== Testing Memory Authentication Wrapper ===")

- Line 113: `        # 创建包装器`
  - Translation:         # Create wrapper

- Line 116: `        # 测试双向认证`
  - Translation:         # Test bidirectional authentication

- Line 122: `        # 测试单向认证`
  - Translation:         # Test one-way authentication

- Line 125: `        logger.info(f"✅ 内存认证包装器测试成功")`
  - Translation:         logger.info(f"✅ Memory authentication wrapper test succeeded")

- Line 126: `        logger.info(f"  双向认证头: {len(auth_headers_two_way)} 个键")`
  - Translation:         logger.info(f"  Two-way authentication headers: {len(auth_headers_two_way)} keys")

- Line 127: `        logger.info(f"  单向认证头: {len(auth_headers_one_way)} 个键")`
  - Translation:         logger.info(f"  One-way authentication headers: {len(auth_headers_one_way)} keys")

- Line 132: `        logger.error(f"❌ 内存认证包装器测试失败: {e}")`
  - Translation:         logger.error(f"❌ Memory authentication wrapper test failed: {e}")

- Line 136: `    """测试内存密钥操作"""`
  - Translation:     Test memory key operations

- Line 137: `    logger.info("=== 测试内存密钥操作 ===")`
  - Translation:     logger.info("=== Testing memory key operations ===")

- Line 140: `        # 测试获取私钥字节`
  - Translation:         # Test retrieving private key bytes

- Line 143: `            logger.info(f"✅ 私钥字节获取成功: {len(private_key_bytes)} 字节")`
  - Translation:             logger.info(f"✅ Private key bytes successfully obtained: {len(private_key_bytes)} bytes")

- Line 145: `            logger.warning("⚠️ 私钥字节获取失败")`
  - Translation:             logger.warning("⚠️ Failed to obtain private key bytes")

- Line 147: `        # 测试获取公钥字节`
  - Translation:         # Test retrieving public key bytes

- Line 150: `            logger.info(f"✅ 公钥字节获取成功: {len(public_key_bytes)} 字节")`
  - Translation:             logger.info(f"✅ Public key bytes successfully retrieved: {len(public_key_bytes)} bytes")

- Line 152: `            logger.warning("⚠️ 公钥字节获取失败")`
  - Translation:             logger.warning("⚠️ Failed to obtain public key bytes")

- Line 157: `        logger.error(f"❌ 内存密钥操作测试失败: {e}")`
  - Translation:         logger.error(f"❌ Memory key operation test failed: {e}")

- Line 161: `    """测试性能对比"""`
  - Translation:     Test performance comparison

- Line 162: `    logger.info("=== 测试性能对比 ===")`
  - Translation:     logger.info("=== Performance Comparison Test ===")

- Line 167: `        # 测试文件版本性能`
  - Translation:         # Test file version performance

- Line 176: `        # 测试内存版本性能`
  - Translation:         # Test memory version performance

- Line 182: `        logger.info(f"✅ 性能对比完成")`
  - Translation:         logger.info(f"✅ Performance comparison completed")

- Line 183: `        logger.info(f"  文件版本 (10次): {file_time:.4f} 秒")`
  - Translation:         logger.info(f"  File version (10 times): {file_time:.4f} seconds")

- Line 184: `        logger.info(f"  内存版本 (10次): {memory_time:.4f} 秒")`
  - Translation:         logger.info(f"  Memory version (10 times): {memory_time:.4f} seconds")

- Line 185: `        logger.info(f"  性能提升: {file_time/memory_time:.2f}x")`
  - Translation:         logger.info(f"  Performance improvement: {file_time/memory_time:.2f}x")

- Line 190: `        logger.error(f"❌ 性能对比测试失败: {e}")`
  - Translation:         logger.error(f"❌ Performance comparison test failed: {e}")

- Line 194: `    """运行所有测试"""`
  - Translation:     """Run all tests"""

- Line 195: `    logger.info("🚀 开始内存版本认证功能测试")`
  - Translation:     logger.info("🚀 Starting memory version authentication feature test")

- Line 198: `    # 1. 测试内存凭证创建`
  - Translation:     # 1. Test memory credential creation

- Line 204: `    # 2. 测试内存版本认证头构建`
  - Translation:     # 2. Test memory version authentication header construction

- Line 209: `    # 3. 测试内存认证包装器`
  - Translation:     # 3. Test memory authentication wrapper

- Line 214: `    # 4. 测试内存密钥操作`
  - Translation:     # 4. Test memory key operations

- Line 219: `    # 5. 测试性能对比`
  - Translation:     # 5. Test performance comparison

- Line 225: `    logger.info("🎉 所有内存版本认证测试通过！")`
  - Translation:     logger.info("🎉 All memory version authentication tests passed!")

- Line 226: `    logger.info("✨ 重构成功：从文件操作迁移到内存操作")`
  - Translation:     logger.info("✨ Refactoring successful: migrated from file operations to in-memory operations")


## ./test/test_auth_simple.py

- Line 3: `简化的认证模块测试`
  - Translation: Simplified authentication module test

- Line 5: `测试当前认证功能是否正常工作`
  - Translation: Test whether the current authentication function is working properly.

- Line 13: `# 添加项目路径`
  - Translation: # Add project path

- Line 16: `# 初始化配置`
  - Translation: # Initialize configuration

- Line 19: `# 设置应用根目录为项目根目录`
  - Translation: # Set the application root directory as the project root directory.

- Line 29: `# 设置日志`
  - Translation: # Set up logging

- Line 37: `    """测试用户创建"""`
  - Translation:     Test user creation

- Line 38: `    logger.info("=== 测试用户创建 ===")`
  - Translation:     logger.info("=== Test User Creation ===")

- Line 50: `        logger.info(f"✅ 用户创建成功: {did_doc['id']}")`
  - Translation:         logger.info(f"✅ User created successfully: {did_doc['id']}")

- Line 53: `        logger.error("❌ 用户创建失败")`
  - Translation:         logger.error("❌ User creation failed")

- Line 57: `    """测试用户数据加载"""`
  - Translation:     Test user data loading

- Line 58: `    logger.info("=== 测试用户数据加载 ===")`
  - Translation:     logger.info("=== Test User Data Loading ===")

- Line 64: `        logger.info(f"✅ 用户数据加载成功")`
  - Translation:         logger.info(f"✅ User data loaded successfully")

- Line 66: `        logger.info(f"  名称: {user_data.name}")`
  - Translation:         logger.info(f"  Name: {user_data.name}")

- Line 67: `        logger.info(f"  DID文档路径: {user_data.did_doc_path}")`
  - Translation:         logger.info(f"  DID document path: {user_data.did_doc_path}")

- Line 68: `        logger.info(f"  私钥路径: {user_data.did_private_key_file_path}")`
  - Translation:         logger.info(f"  Private key path: {user_data.did_private_key_file_path}")

- Line 71: `        logger.error("❌ 用户数据加载失败")`
  - Translation:         logger.error("❌ Failed to load user data")

- Line 75: `    """测试DID凭证创建"""`
  - Translation:     """Test DID Credential Creation"""

- Line 76: `    logger.info("=== 测试DID凭证创建 ===")`
  - Translation:     logger.info("=== Testing DID Credential Creation ===")

- Line 84: `        logger.info(f"✅ DID凭证创建成功")`
  - Translation:         logger.info(f"✅ DID credential created successfully")

- Line 86: `        logger.info(f"  密钥对数量: {len(credentials.key_pairs)}")`
  - Translation:         logger.info(f"  Number of key pairs: {len(credentials.key_pairs)}")

- Line 88: `        # 测试密钥对获取`
  - Translation:         # Test key pair retrieval

- Line 91: `            logger.info(f"  密钥对获取成功: {key_pair.key_id}")`
  - Translation:             logger.info(f"  Key pair successfully obtained: {key_pair.key_id}")

- Line 93: `            logger.warning("  未找到key-1密钥对")`
  - Translation:             logger.warning("Key pair for key-1 not found")

- Line 98: `        logger.error(f"❌ DID凭证创建失败: {e}")`
  - Translation:         logger.error(f"❌ DID credential creation failed: {e}")

- Line 102: `    """测试LocalAgent创建"""`
  - Translation:     Test LocalAgent creation

- Line 103: `    logger.info("=== 测试LocalAgent创建 ===")`
  - Translation:     logger.info("=== Testing LocalAgent Creation ===")

- Line 107: `        logger.info(f"✅ LocalAgent创建成功")`
  - Translation:         logger.info(f"✅ LocalAgent created successfully")

- Line 109: `        logger.info(f"  名称: {agent.name}")`
  - Translation:         logger.info(f"  Name: {agent.name}")

- Line 110: `        logger.info(f"  用户目录: {agent.user_dir}")`
  - Translation:         logger.info(f"  User directory: {agent.user_dir}")

- Line 114: `        logger.error(f"❌ LocalAgent创建失败: {e}")`
  - Translation:         logger.error(f"❌ Failed to create LocalAgent: {e}")

- Line 118: `    """测试认证头构建"""`
  - Translation:     Test authentication header construction

- Line 119: `    logger.info("=== 测试认证头构建 ===")`
  - Translation:     logger.info("=== Testing Authentication Header Construction ===")

- Line 122: `        # 创建认证上下文`
  - Translation:         # Create authentication context

- Line 131: `        # 创建凭证`
  - Translation:         # Create credential

- Line 137: `        # 创建认证器并构建认证头`
  - Translation:         # Create authenticator and construct authentication header

- Line 141: `        logger.info(f"✅ 认证头构建成功")`
  - Translation:         logger.info(f"✅ Authentication header constructed successfully")

- Line 142: `        logger.info(f"  认证头键数量: {len(auth_headers)}")`
  - Translation:         logger.info(f"  Number of authentication header keys: {len(auth_headers)}")

- Line 144: `            logger.info(f"  包含Authorization头")`
  - Translation:             logger.info(f"  Contains Authorization header")

- Line 149: `        logger.error(f"❌ 认证头构建失败: {e}")`
  - Translation:         logger.error(f"❌ Failed to construct authentication header: {e}")

- Line 153: `    """运行所有测试"""`
  - Translation:     """Run all tests"""

- Line 154: `    logger.info("🚀 开始认证模块基础功能测试")`
  - Translation:     logger.info("🚀 Starting basic functionality tests for the authentication module")

- Line 157: `    # 1. 测试用户创建`
  - Translation:     # 1. Test user creation

- Line 162: `    # 2. 测试用户数据加载`
  - Translation:     # 2. Test user data loading

- Line 167: `    # 3. 测试DID凭证创建`
  - Translation:     # 3. Test DID credential creation

- Line 172: `    # 4. 测试LocalAgent创建`
  - Translation:     # 4. Test LocalAgent creation

- Line 177: `    # 5. 测试认证头构建`
  - Translation:     # 5. Test authentication header construction

- Line 183: `    logger.info("🎉 所有基础测试通过！")`
  - Translation:     logger.info("🎉 All basic tests passed!")


## ./anp_open_sdk_demo/anp_demo_main.py

- Line 6: `"""ANP SDK 综合演示程序"""`
  - Translation: """ANP SDK Comprehensive Demo Program"""

- Line 18: `setup_logging() # 假设 setup_logging 内部也改用 get_global_config()`
  - Translation: setup_logging() # Assume that setup_logging is also modified to use get_global_config() internally.

- Line 22: `logger.debug("启动 ANP Demo...")`
  - Translation: logger.debug("Starting ANP Demo...")

- Line 23: `logger.debug(f"Python版本: {sys.version}")`
  - Translation: logger.debug(f"Python version: {sys.version}")

- Line 24: `logger.debug(f"工作目录: {sys.path[0]}")`
  - Translation: logger.debug(f"Working directory: {sys.path[0]}")

- Line 26: `    logger.debug("导入模块...")`
  - Translation:     logger.debug("Importing module...")

- Line 34: `    logger.debug("✓ 所有模块导入成功")`
  - Translation:     logger.debug("✓ All modules imported successfully")

- Line 36: `    logger.debug(f"✗ 模块导入失败: {e}")`
  - Translation:     logger.debug(f"✗ Module import failed: {e}")

- Line 42: `    """ANP SDK 演示应用程序主类"""`
  - Translation:     """ANP SDK Demo Application Main Class"""

- Line 45: `        logger.debug("初始化 ANPDemoApplication...")`
  - Translation:         logger.debug("Initializing ANPDemoApplication...")

- Line 52: `            # 初始化服务`
  - Translation:             # Initialize service

- Line 56: `            # 初始化组件`
  - Translation:             # Initialize component

- Line 60: `            # 运行时状态`
  - Translation:             # Runtime status

- Line 64: `            logger.debug("✓ ANPDemoApplication 初始化成功")`
  - Translation:             logger.debug("✓ ANPDemoApplication initialized successfully")

- Line 66: `            logger.debug(f"✗ ANPDemoApplication 初始化失败: {e}")`
  - Translation:             logger.debug(f"✗ ANPDemoApplication initialization failed: {e}")

- Line 71: `        """主运行方法"""`
  - Translation:         """Main execution method"""

- Line 73: `            logger.debug("开始运行演示...")`
  - Translation:             logger.debug("Starting to run the demo...")

- Line 74: `            self.step_helper.pause("ANP SDK 演示程序启动")`
  - Translation:             self.step_helper.pause("ANP SDK demo program startup")

- Line 76: `            # 初始化SDK和agents`
  - Translation:             # Initialize SDK and agents

- Line 79: `            # 选择运行模式`
  - Translation:             # Select operating mode

- Line 87: `            # 默认开发模式`
  - Translation:             # Default development mode

- Line 91: `            logger.debug("用户中断演示")`
  - Translation:             logger.debug("User interrupted the demonstration")

- Line 93: `            logger.error(f"Demo运行错误: {e}")`
  - Translation:             logger.error(f"Demo runtime error: {e}")

- Line 99: `        """初始化所有组件"""`
  - Translation:         Initialize all components

- Line 101: `            logger.debug("初始化组件...")`
  - Translation:             logger.debug("Initializing components...")

- Line 102: `            self.step_helper.pause("初始化SDK")`
  - Translation:             self.step_helper.pause("Initialize SDK")

- Line 104: `            # 初始化SDK`
  - Translation:             # Initialize SDK

- Line 107: `            # 加载agents`
  - Translation:             # Load agents

- Line 108: `            self.step_helper.pause("加载智能体")`
  - Translation:             self.step_helper.pause("Load agent")

- Line 112: `                logger.error("智能体不足3个，无法完成全部演示")`
  - Translation:                 logger.error("There are fewer than 3 agents, unable to complete the entire demonstration")

- Line 113: `                logger.debug(f"当前找到 {len(self.agents)} 个智能体")`
  - Translation:                 logger.debug(f"Currently found {len(self.agents)} agents")

- Line 118: `            # 注册API和消息处理器`
  - Translation:             # Register API and message handler

- Line 119: `            self.step_helper.pause("注册处理器")`
  - Translation:             self.step_helper.pause("Register processor")

- Line 124: `            # 注册agents到SDK`
  - Translation:             # Register agents to SDK

- Line 125: `            self.step_helper.pause("注册智能体到SDK")`
  - Translation:             self.step_helper.pause("Register the agent to the SDK")

- Line 129: `            # 启动服务器`
  - Translation:             # Start the server

- Line 130: `            self.step_helper.pause("启动服务器")`
  - Translation:             self.step_helper.pause("Start the server")

- Line 133: `            if not self.args.f:  # 快速模式不显示提示`
  - Translation:             if not self.args.f:  # Do not display prompts in fast mode

- Line 134: `                logger.debug("服务器已启动，查看'/'了解状态,'/docs'了解基础api")`
  - Translation:                 logger.debug("Server started, check '/' for status, '/docs' for basic API information")

- Line 136: `            logger.debug("✓ 组件初始化完成")`
  - Translation:             logger.debug("✓ Component initialization complete")

- Line 139: `            logger.error(f"组件初始化失败: {e}")`
  - Translation:             logger.error(f"Component initialization failed: {e}")

- Line 144: `        """开发模式"""`
  - Translation:         "Development Mode"

- Line 145: `        logger.debug("启动开发模式演示")`
  - Translation:         logger.debug("Starting development mode demonstration")

- Line 157: `        """分步执行模式"""`
  - Translation:         "Step-by-step execution mode"

- Line 158: `        logger.debug("启动分步执行模式演示")`
  - Translation:         logger.debug("Start step-by-step execution mode demonstration")

- Line 170: `        """快速执行模式"""`
  - Translation:         "Fast Execution Mode"

- Line 171: `        logger.debug("启动快速执行模式演示")`
  - Translation:         logger.debug("Initiating fast execution mode demonstration")

- Line 183: `        """清理资源"""`
  - Translation:         Clean up resources

- Line 184: `        logger.debug("开始清理资源...")`
  - Translation:         logger.debug("Starting to clean up resources...")

- Line 190: `            logger.debug("资源清理完成")`
  - Translation:             logger.debug("Resource cleanup completed")

- Line 192: `            logger.error(f"清理资源时出错: {e}")`
  - Translation:             logger.error(f"Error occurred while cleaning up resources: {e}")

- Line 197: `        logger.debug("解析命令行参数...")`
  - Translation:         logger.debug("Parsing command line arguments...")

- Line 198: `        parser = argparse.ArgumentParser(description='ANP SDK 综合演示程序')`
  - Translation:         parser = argparse.ArgumentParser(description='ANP SDK Comprehensive Demo Program')

- Line 199: `        parser.add_argument('-d', action='store_true', help='开发测试模式')`
  - Translation:         parser.add_argument('-d', action='store_true', help='development test mode')

- Line 200: `        parser.add_argument('-s', action='store_true', help='步骤执行模式')`
  - Translation:         parser.add_argument('-s', action='store_true', help='Step execution mode')

- Line 201: `        parser.add_argument('-f', action='store_true', help='快速执行模式')`
  - Translation:         parser.add_argument('-f', action='store_true', help='Fast execution mode')

- Line 202: `        parser.add_argument('--domain', default='localhost', help='指定测试域名')`
  - Translation:         parser.add_argument('--domain', default='localhost', help='Specify the test domain name')

- Line 206: `        # 默认开发模式`
  - Translation:         # Default development mode

- Line 210: `        logger.debug(f"运行模式: {'开发模式' if args.d else '步骤模式' if args.s else '快速模式'}")`
  - Translation:         logger.debug(f"Run mode: {'Development mode' if args.d else 'Step mode' if args.s else 'Fast mode'}")

- Line 216: `        logger.debug(f"程序执行失败: {e}")`
  - Translation:         logger.debug(f"Program execution failed: {e}")


## ./anp_open_sdk_demo/__init__.py

- Line 1: `"""演示模块包"""`
  - Translation: """Demo module package"""


## ./anp_open_sdk_demo/demo_modules/demo_tasks.py

- Line 8: `load_dotenv()  # 这会加载项目根目录下的 .env 文件`
  - Translation: load_dotenv()  # This will load the .env file in the project's root directory

- Line 39: `    """演示任务运行器"""`
  - Translation:     Demonstration Task Runner

- Line 51: `        """运行所有演示"""`
  - Translation:         """Run all demos"""

- Line 53: `            logger.error("智能体不足，无法执行演示")`
  - Translation:             logger.error("Insufficient agents, unable to execute demonstration")

- Line 63: `            await self.run_hosted_did_demo(agent1)  # 添加托管 DID 演示`
  - Translation:             await self.run_hosted_did_demo(agent1)  # Add hosted DID demo

- Line 65: `            self.step_helper.pause("所有演示完成")`
  - Translation:             self.step_helper.pause("All demonstrations completed")

- Line 68: `            logger.error(f"演示执行过程中发生错误: {e}")`
  - Translation:             logger.error(f"An error occurred during the demonstration execution: {e}")

- Line 72: `        """API调用演示"""`
  - Translation:         API call demonstration

- Line 73: `        self.step_helper.pause("步骤1: 演示API调用")`
  - Translation:         self.step_helper.pause("Step 1: Demonstrate API call")

- Line 75: `        # 显示智能体信息`
  - Translation:         # Display agent information

- Line 77: `        # GET请求演示`
  - Translation:         # GET request demonstration

- Line 78: `        self.step_helper.pause("演示GET请求到/hello接口")`
  - Translation:         self.step_helper.pause("Demonstrate GET request to /hello endpoint")

- Line 82: `        logger.debug(f"{agent2.name}GET调用{agent1.name}的/hello接口响应: {resp}")`
  - Translation:         logger.debug(f"{agent2.name} GET call to {agent1.name}'s /hello endpoint response: {resp}")

- Line 83: `        # POST请求演示`
  - Translation:         # POST request demonstration

- Line 84: `        self.step_helper.pause("演示POST请求到/info接口")`
  - Translation:         self.step_helper.pause("Demonstrate POST request to /info endpoint")

- Line 88: `        logger.debug(f"{agent1.name}POST调用{agent2.name}的/info接口响应: {resp}")`
  - Translation:         logger.debug(f"{agent1.name} POST call to {agent2.name}'s /info endpoint response: {resp}")

- Line 90: `        # GET请求演示`
  - Translation:         # GET request demonstration

- Line 91: `        self.step_helper.pause("演示GET请求到/info接口")`
  - Translation:         self.step_helper.pause("Demonstrate GET request to /info endpoint")

- Line 95: `        logger.debug(f"{agent1.name}GET调用{agent2.name}的/info接口响应: {resp}")`
  - Translation:         logger.debug(f"{agent1.name} GET call to {agent2.name}'s /info endpoint response: {resp}")

- Line 98: `        # 导入必要的模块`
  - Translation:         # Import necessary modules

- Line 109: `            logger.debug("=== 开始消息演示（包含临时用户创建） ===")`
  - Translation:             logger.debug("=== Starting message demonstration (including temporary user creation) ===")

- Line 111: `            # 1. 创建临时用户`
  - Translation:             # 1. Create a temporary user

- Line 112: `            logger.debug("步骤1: 创建临时用户")`
  - Translation:             logger.debug("Step 1: Create a temporary user")

- Line 114: `                'name': '智能体创建删除示范用户',`
  - Translation:                 'name': 'Agent Creation and Deletion Demo User',

- Line 116: `                'port': 9527,  # 演示在同一台服务器，使用相同端口`
  - Translation:                 'port': 9527,  # Demonstration on the same server using the same port

- Line 117: `                'dir': 'wba', # 理论上可以自定义，当前由于did 路由的did.json服务在wba/user，所以要保持一致`
  - Translation:                 'dir': 'wba', # Theoretically customizable, currently needs to remain consistent because the did routing's did.json service is at wba/user

- Line 118: `                'type': 'user'# 用户可以自定义did 路由的did.json服务在路径，确保和did名称路径一致即可`
  - Translation:                 'type': 'user' # Users can customize the DID routing did.json service in the path, just ensure it is consistent with the DID name path.

- Line 123: `                logger.error("临时用户创建失败")`
  - Translation:                 logger.error("Failed to create temporary user")

- Line 126: `            logger.debug(f"临时用户创建成功，DID: {did_document['id']}")`
  - Translation:             logger.debug(f"Temporary user created successfully, DID: {did_document['id']}")

- Line 128: `            # 创建LocalAgent实例`
  - Translation:             # Create LocalAgent instance

- Line 131: `            # 注册到SDK`
  - Translation:             # Register to SDK

- Line 133: `            logger.debug(f"临时智能体 {temp_agent.name} 注册成功")`
  - Translation:             logger.debug(f"Temporary agent {temp_agent.name} registered successfully")

- Line 135: `            # 3. 为临时智能体注册消息监听函数`
  - Translation:             # 3. Register message listener function for the temporary agent.

- Line 136: `            logger.debug("步骤3: 注册消息监听函数")`
  - Translation:             logger.debug("Step 3: Register message listener function")

- Line 141: `                """临时智能体的消息处理函数"""`
  - Translation:                 """Temporary agent message handling function"""

- Line 142: `                logger.debug(f"[{temp_agent.name}] 收到消息: {msg}")`
  - Translation:                 logger.debug(f"[{temp_agent.name}] Message received: {msg}")

- Line 144: `                # 自动回复消息`
  - Translation:                 # Auto-reply message

- Line 145: `                reply_content = f"这是来自临时智能体 {temp_agent.name} 的自动回复,确认收到消息{msg.get('content')}"`
  - Translation:                 reply_content = f"This is an automated reply from temporary agent {temp_agent.name}, confirming receipt of the message {msg.get('content')}"

- Line 151: `            logger.debug(f"临时智能体 {temp_agent.name} 消息监听函数注册完成")`
  - Translation:             logger.debug(f"Temporary agent {temp_agent.name} message listener function registration completed")

- Line 153: `            # 4. 与其他智能体进行消息交互`
  - Translation:             # 4. Interact with other agents through messaging

- Line 154: `            logger.debug("步骤4: 开始消息交互演示")`
  - Translation:             logger.debug("Step 4: Begin message interaction demonstration")

- Line 156: `            # 临时智能体向agent2发送消息`
  - Translation:             # Temporary agent sends a message to agent2

- Line 158: `            resp = await agent_msg_post(self.sdk, temp_agent.id, agent2.id, f"你好，我是{temp_agent.name}")`
  - Translation:             resp = await agent_msg_post(self.sdk, temp_agent.id, agent2.id, f"Hello, I am {temp_agent.name}")

- Line 159: `            logger.debug(f"[{temp_agent.name}] 已发送消息给 {agent2.name},响应: {resp}")`
  - Translation:             logger.debug(f"[{temp_agent.name}] Message sent to {agent2.name}, response: {resp}")

- Line 162: `            # 临时智能体向agent3发送消息`
  - Translation:             # Temporary agent sends a message to agent3

- Line 164: `            resp = await agent_msg_post(self.sdk, temp_agent.id, agent3.id, f"你好，我是{temp_agent.name}")`
  - Translation:             resp = await agent_msg_post(self.sdk, temp_agent.id, agent3.id, f"Hello, I am {temp_agent.name}")

- Line 165: `            logger.debug(f"[{temp_agent.name}] 已发送消息给 {agent3.name},响应: {resp}")`
  - Translation:             logger.debug(f"[{temp_agent.name}] Message sent to {agent3.name}, response: {resp}")

- Line 168: `            # agent1向临时智能体发送消息`
  - Translation:             # agent1 sends a message to the temporary agent

- Line 170: `            resp = await agent_msg_post(self.sdk, agent1.id, temp_agent.id, f"你好，我是{agent1.name}")`
  - Translation:             resp = await agent_msg_post(self.sdk, agent1.id, temp_agent.id, f"Hello, I am {agent1.name}")

- Line 171: `            logger.debug(f"[{agent1.name}] 已发送消息给 {temp_agent.name},响应: {resp}")`
  - Translation:             logger.debug(f"[{agent1.name}] Message sent to {temp_agent.name}, response: {resp}")

- Line 175: `            # 显示消息交互总结`
  - Translation:             # Display message interaction summary

- Line 176: `            logger.debug("=== 消息交互总结 ===")`
  - Translation:             logger.debug("=== Message Interaction Summary ===")

- Line 177: `            logger.debug(f"临时智能体 {temp_agent.name} 成功与以下智能体进行了消息交互:")`
  - Translation:             logger.debug(f"Temporary agent {temp_agent.name} successfully exchanged messages with the following agents:")

- Line 178: `            logger.debug(f"  - 发送消息给: {agent2.name}, {agent3.name}")`
  - Translation:             logger.debug(f"  - Sending message to: {agent2.name}, {agent3.name}")

- Line 179: `            logger.debug(f"  - 接收消息来自: {agent1.name}")`
  - Translation:             logger.debug(f"  - Message received from: {agent1.name}")

- Line 180: `            logger.debug("所有消息都已正确处理和回复")`
  - Translation:             logger.debug("All messages have been correctly processed and replied to")

- Line 183: `            logger.error(f"消息演示过程中发生错误: {e}")`
  - Translation:             logger.error(f"An error occurred during message demonstration: {e}")

- Line 185: `            logger.error(f"详细错误信息: {traceback.format_exc()}")`
  - Translation:             logger.error(f"Detailed error information: {traceback.format_exc()}")

- Line 188: `            # 5. 清理：删除临时用户`
  - Translation:             # 5. Cleanup: Delete temporary users

- Line 189: `            logger.debug("步骤5: 清理临时用户")`
  - Translation:             logger.debug("Step 5: Clean up temporary users")

- Line 195: `                    logger.error("无法找到刚创建的用户目录")`
  - Translation:                     logger.error("Unable to find the newly created user directory")

- Line 200: `                    # 从SDK中注销`
  - Translation:                     # Logout from SDK

- Line 202: `                    logger.debug(f"临时智能体 {temp_agent.name} 已从SDK注销")`
  - Translation:                     logger.debug(f"Temporary agent {temp_agent.name} has been deregistered from the SDK")

- Line 205: `                    # 删除用户目录`
  - Translation:                     # Delete user directory

- Line 212: `                        logger.debug(f"临时用户目录已删除: {user_full_path}")`
  - Translation:                         logger.debug(f"Temporary user directory has been deleted: {user_full_path}")

- Line 214: `                        logger.warning(f"临时用户目录不存在: {user_full_path}")`
  - Translation:                         logger.warning(f"Temporary user directory does not exist: {user_full_path}")

- Line 216: `                logger.debug("临时智能体清理完成")`
  - Translation:                 logger.debug("Temporary agent cleanup completed")

- Line 219: `                logger.error(f"清理临时用户时发生错误: {e}")`
  - Translation:                 logger.error(f"An error occurred while cleaning up temporary users: {e}")

- Line 222: `        """托管 DID 演示"""`
  - Translation:         "Hosted DID Demo"

- Line 223: `        self.step_helper.pause("步骤5: 演示托管 DID 功能")`
  - Translation:         self.step_helper.pause("Step 5: Demonstrate the hosted DID feature")

- Line 226: `            # Part 1: 申请托管 DID`
  - Translation:             # Part 1: Apply for hosting DID

- Line 227: `            logger.debug("=== Part 1: 申请托管 DID ===")`
  - Translation:             logger.debug("=== Part 1: Request Hosting DID ===")

- Line 228: `            self.step_helper.pause("准备申请 hosted_did")`
  - Translation:             self.step_helper.pause("Preparing to apply for hosted_did")

- Line 232: `                logger.debug(f"✓ {agent1.name} 申请托管 DID 发送成功")`
  - Translation:                 logger.debug(f"✓ {agent1.name} successfully sent the request to host DID")

- Line 234: `                logger.debug(f"✗ {agent1.name} 申请托管 DID 发送失败")`
  - Translation:                 logger.debug(f"✗ {agent1.name} failed to send DID hosting request")

- Line 239: `            # 服务器查询托管申请状态`
  - Translation:             # Server query hosting application status

- Line 240: `            logger.debug("服务器查询托管 DID 申请状态...")`
  - Translation:             logger.debug("Querying server for hosted DID application status...")

- Line 243: `            logger.debug(f"服务器处理托管情况: {server_result}")`
  - Translation:             logger.debug(f"Server handling hosting situation: {server_result}")

- Line 245: `            # 智能体查询自己的托管状态`
  - Translation:             # Agent queries its hosting status.

- Line 247: `            logger.debug(f"{agent1.name} 托管申请查询结果: {agent_result}")`
  - Translation:             logger.debug(f"{agent1.name} Hosting Application Query Result: {agent_result}")

- Line 249: `            # Part 2: 托管智能体消息交互演示`
  - Translation:             # Part 2: Hosted Agent Message Interaction Demo

- Line 250: `            logger.debug("\n=== Part 2: 托管智能体消息交互演示 ===")`
  - Translation:             logger.debug("\n=== Part 2: Demonstration of Managed Agent Message Interaction ===")

- Line 251: `            self.step_helper.pause("开始托管智能体消息交互")`
  - Translation:             self.step_helper.pause("Start hosting agent message interaction")

- Line 253: `            # 加载用户数据`
  - Translation:             # Load user data

- Line 258: `            # 查找并注册托管智能体`
  - Translation:             # Find and register managed agents

- Line 262: `                logger.warning("未找到托管智能体，跳过托管消息演示")`
  - Translation:                 logger.warning("Managed agent not found, skipping managed message demonstration")

- Line 264: `            # 跳过 公共托管智能体 找到最近的一个自己申请的托管智能体 因为公共托管智能体没开消息服务`
  - Translation:             # Skip public hosting agents and find the nearest self-applied hosting agent because public hosting agents do not have messaging services enabled.

- Line 266: `            hosted_agent.name = "本地托管智能体"`
  - Translation:             hosted_agent.name = "Locally Hosted Agent"

- Line 270: `                logger.debug(f"[{hosted_agent.name}] 收到消息: {msg}")`
  - Translation:                 logger.debug(f"[{hosted_agent.name}] Message received: {msg}")

- Line 271: `                reply_content = f"这是来自托管智能体 {hosted_agent.name} 的自动回复，已收到消息: {msg.get('content')}"`
  - Translation:                 reply_content = f"This is an automated reply from the hosted agent {hosted_agent.name}, message received: {msg.get('content')}"

- Line 279: `            # 查找公共托管智能体`
  - Translation:             # Find public hosted agents

- Line 280: `            public_hosted_data = user_data_manager.get_user_data_by_name("托管智能体_did:wba:agent-did.com:test:public")`
  - Translation:             public_hosted_data = user_data_manager.get_user_data_by_name("Hosted Agent_did:wba:agent-did.com:test:public")

- Line 284: `                logger.debug(f"注册公共托管智能体: {public_hosted_agent.name}")`
  - Translation:                 logger.debug(f"Registering public hosted agent: {public_hosted_agent.name}")

- Line 286: `                # 托管智能体之间的消息交互`
  - Translation:                 # Message interaction between managed agents

- Line 287: `                self.step_helper.pause("托管智能体消息交互演示")`
  - Translation:                 self.step_helper.pause("Demonstration of Managed Agent Message Interaction")

- Line 289: `                # 公共托管智能体向托管智能体发送消息`
  - Translation:                 # Public hosting agent sends a message to the hosted agent.

- Line 294: `                    f"你好，我是{public_hosted_agent.name}"`
  - Translation:                     f"Hello, I am {public_hosted_agent.name}"

- Line 300: `                # 托管智能体向普通智能体发送消息`
  - Translation:                 # Managed agent sends a message to the regular agent.

- Line 305: `                    f"你好，我是托管智能体 {hosted_agent.name}"`
  - Translation:                     f"Hello, I am the hosted agent {hosted_agent.name}"

- Line 311: `                # 普通智能体向托管智能体发送消息`
  - Translation:                 # A regular agent sends a message to a hosted agent.

- Line 316: `                    f"你好托管智能体，我是 {agent1.name}"`
  - Translation:                     f"Hello, hosted agent, I am {agent1.name}"

- Line 320: `                # 显示托管状态总结`
  - Translation:                 # Display hosting status summary

- Line 321: `                logger.debug("\n=== 托管 DID 演示总结 ===")`
  - Translation:                 logger.debug("\n=== Managed DID Demonstration Summary ===")

- Line 322: `                logger.debug(f"1. {agent1.name} 成功申请了托管 DID")`
  - Translation:                 logger.debug(f"1. {agent1.name} successfully applied for hosting DID")

- Line 323: `                logger.debug(f"2. 托管智能体 {hosted_agent.name} 已注册并可以正常通信")`
  - Translation:                 logger.debug(f"2. Hosted agent {hosted_agent.name} is registered and can communicate normally")

- Line 324: `                logger.debug("3. 托管智能体可以与普通智能体和其他托管智能体进行消息交互")`
  - Translation:                 logger.debug("3. Managed agents can interact with regular agents and other managed agents through messaging")

- Line 326: `                # 清理：注销托管智能体`
  - Translation:                 # Cleanup: Deregister managed agents

- Line 330: `                logger.debug("托管智能体已注销")`
  - Translation:                 logger.debug("Managed agent has been deregistered")

- Line 333: `                logger.warning("未找到公共托管智能体，跳过部分演示")`
  - Translation:                 logger.warning("Public hosted agent not found, skipping part of the demo")

- Line 336: `            logger.error(f"托管 DID 演示过程中发生错误: {e}")`
  - Translation:             logger.error(f"An error occurred during the hosted DID demonstration: {e}")

- Line 338: `            logger.error(f"详细错误信息: {traceback.format_exc()}")`
  - Translation:             logger.error(f"Detailed error information: {traceback.format_exc()}")

- Line 340: `        self.step_helper.pause("托管 DID 演示完成")`
  - Translation:         self.step_helper.pause("Custody DID demonstration completed")

- Line 344: `        """消息发送演示"""`
  - Translation:         """Message Sending Demo"""

- Line 345: `        self.step_helper.pause("步骤2: 演示消息发送")`
  - Translation:         self.step_helper.pause("Step 2: Demonstrate message sending")

- Line 347: `        logger.debug(f"演示：{agent2.name}向{agent3.name}发送消息")`
  - Translation:         logger.debug(f"Demo: {agent2.name} sends a message to {agent3.name}")

- Line 348: `        resp = await agent_msg_post(self.sdk, agent2.id, agent3.id, f"你好，我是{agent2.name}")`
  - Translation:         resp = await agent_msg_post(self.sdk, agent2.id, agent3.id, f"Hello, I am {agent2.name}")

- Line 349: `        logger.debug(f"{agent2.name}向{agent3.name}发送消息响应: {resp}")`
  - Translation:         logger.debug(f"{agent2.name} sends message response to {agent3.name}: {resp}")

- Line 351: `        self.step_helper.pause("消息发送完成，观察回复")`
  - Translation:         self.step_helper.pause("Message sent, observe the response")

- Line 353: `        logger.debug(f"演示：{agent3.name}向{agent1.name}发送消息")`
  - Translation:         logger.debug(f"Demo: {agent3.name} sends a message to {agent1.name}")

- Line 354: `        resp = await agent_msg_post(self.sdk, agent3.id, agent1.id, f"你好，我是{agent3.name}")`
  - Translation:         resp = await agent_msg_post(self.sdk, agent3.id, agent1.id, f"Hello, I am {agent3.name}")

- Line 355: `        logger.debug(f"{agent3.name}向{agent1.name}发送消息响应: {resp}")`
  - Translation:         logger.debug(f"{agent3.name} sends message response to {agent1.name}: {resp}")

- Line 358: `        """ANP工具爬虫演示 - 使用ANP协议进行智能体信息爬取"""`
  - Translation:         """ANP Tool Crawler Demonstration - Using ANP Protocol for Agent Information Crawling"""

- Line 359: `        self.step_helper.pause("步骤3: 演示ANP工具爬虫功能")`
  - Translation:         self.step_helper.pause("Step 3: Demonstrate the ANP tool's crawler functionality")

- Line 361: `        # 引入必要的依赖`
  - Translation:         # Import necessary dependencies

- Line 362: `        logger.debug("成功导入ANPTool")`
  - Translation:         logger.debug("Successfully imported ANPTool")

- Line 368: `        user_data = user_data_manager.get_user_data_by_name("托管智能体_did:wba:agent-did.com:test:public")`
  - Translation:         user_data = user_data_manager.get_user_data_by_name("Managed Agent_did:wba:agent-did.com:test:public")

- Line 374: `         # 搜索智能体的URL`
  - Translation:          # Search agent's URL

- Line 377: `        # 定义任务`
  - Translation:         # Define task

- Line 379: `            "input": "查询北京天津上海今天的天气",`
  - Translation:             "input": "Query the weather in Beijing, Tianjin, and Shanghai today"

- Line 383: `        # 创建搜索智能体的提示模板`
  - Translation:         # Create a prompt template for the search agent

- Line 385: `        你是一个通用智能网络数据探索工具。你的目标是通过递归访问各种数据格式（包括JSON-LD、YAML等）来找到用户需要的信息和API以完成特定任务。`
  - Translation:         You are a general intelligent network data exploration tool. Your goal is to find the information and APIs needed by the user to complete specific tasks by recursively accessing various data formats (including JSON-LD, YAML, etc.).

- Line 387: `        ## 当前任务`
  - Translation:         ## Current task

- Line 390: `        ## 重要提示`
  - Translation:         ## Important Notice

- Line 391: `        1. 你将收到一个初始URL（{initial_url}），这是一个代理描述文件。`
  - Translation:         You will receive an initial URL ({initial_url}), which is a proxy description file.

- Line 392: `        2. 你需要理解这个代理的结构、功能和API使用方法。`
  - Translation:         2. You need to understand the structure, functionality, and API usage of this proxy.

- Line 393: `        3. 你需要像网络爬虫一样持续发现和访问新的URL和API端点。`
  - Translation:         3. You need to continuously discover and access new URLs and API endpoints like a web crawler.

- Line 394: `        4. 你可以使用anp_tool来获取任何URL的内容。`
  - Translation:         4. You can use anp_tool to retrieve the content of any URL.

- Line 395: `        5. 此工具可以处理各种响应格式。`
  - Translation:         5. This tool can handle various response formats.

- Line 396: `        6. 阅读每个文档以找到与任务相关的信息或API端点。`
  - Translation:         6. Read each document to find information or API endpoints related to the task.

- Line 397: `        7. 你需要自己决定爬取路径，不要等待用户指令。`
  - Translation:         7. You need to determine the crawling path yourself; do not wait for user instructions.

- Line 398: `        8. 注意：你最多可以爬取10个URL，并且必须在达到此限制后结束搜索。`
  - Translation:         8. Note: You can crawl up to 10 URLs, and you must stop the search after reaching this limit.

- Line 400: `        ## 爬取策略`
  - Translation:         ## Crawling Strategy

- Line 401: `        1. 首先获取初始URL的内容，理解代理的结构和API。`
  - Translation:         1. First, retrieve the content of the initial URL to understand the structure of the proxy and the API.

- Line 402: `        2. 识别文档中的所有URL和链接，特别是serviceEndpoint、url、@id等字段。`
  - Translation:         2. Identify all URLs and links in the document, especially fields like serviceEndpoint, url, @id, etc.

- Line 403: `        3. 分析API文档以理解API用法、参数和返回值。`
  - Translation:         3. Analyze the API documentation to understand the API usage, parameters, and return values.

- Line 404: `        4. 根据API文档构建适当的请求，找到所需信息。`
  - Translation:         4. Construct appropriate requests according to the API documentation to find the required information.

- Line 405: `        5. 记录所有你访问过的URL，避免重复爬取。`
  - Translation:         5. Record all the URLs you have visited to avoid duplicate crawling.

- Line 406: `        6. 总结所有你找到的相关信息，并提供详细的建议。`
  - Translation:         6. Summarize all the relevant information you have found and provide detailed recommendations.

- Line 408: `        对于天气查询任务，你需要:`
  - Translation:         For the weather query task, you need to:

- Line 409: `        1. 找到天气查询API端点`
  - Translation:         1. Find the weather query API endpoint

- Line 410: `        2. 理解如何正确构造请求参数（如城市名、日期等）`
  - Translation:         2. Understand how to correctly construct request parameters (such as city name, date, etc.)

- Line 411: `        3. 发送天气查询请求`
  - Translation:         3. Send weather query request

- Line 412: `        4. 获取并展示天气信息`
  - Translation:         4. Retrieve and display weather information

- Line 414: `        提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。`
  - Translation:         Provide detailed information and clear explanations to help users understand the information you found and your recommendations.

- Line 416: `        # 获取 did_document_path, private_key_path`
  - Translation:         # Get did_document_path, private_key_path

- Line 421: `        # 调用通用智能爬虫`
  - Translation:         # Invoke the general intelligent crawler

- Line 423: `            anpsdk=self.sdk,  # 添加 anpsdk 参数`
  - Translation:             anpsdk=self.sdk,  # Add anpsdk parameter

- Line 424: `            caller_agent = str(agent_anptool.id) ,  # 添加发起 agent 参数`
  - Translation:             caller_agent = str(agent_anptool.id) ,  # Add initiating agent parameter

- Line 425: `            target_agent = str(agent2.id)  ,  # 添加目标 agent 参数`
  - Translation:             `target_agent = str(agent2.id)  ,  # Add target agent parameter`

- Line 426: `            use_two_way_auth = True,  # 是否使用双向认证`
  - Translation:             use_two_way_auth = True,  # Whether to use two-way authentication

- Line 434: `            agent_name="搜索智能体"`
  - Translation:             agent_name = "Search Agent"

- Line 437: `        self.step_helper.pause("搜索智能体演示完成")`
  - Translation:         self.step_helper.pause("Search agent demonstration completed")

- Line 442: `        """显示智能体信息"""`
  - Translation:         Display agent information

- Line 443: `        self.step_helper.pause("显示智能体ad.json信息")`
  - Translation:         self.step_helper.pause("Display agent ad.json information")

- Line 454: `                logger.debug(f"{agent.name}的ad.json信息:")`
  - Translation:                 logger.debug(f"ad.json information for {agent.name}:")

- Line 459: `                    logger.debug(f"响应: {data}")`
  - Translation:                     logger.debug(f"Response: {data}")

- Line 461: `                logger.error(f"获取{agent.name}信息失败: {e}")`
  - Translation:                 logger.error(f"Failed to retrieve information for {agent.name}: {e}")

- Line 471: `        anpsdk=None,  # 添加 anpsdk 参数`
  - Translation:         anpsdk = None,  # Add anpsdk parameter

- Line 472: `        caller_agent: str = None,  # 添加发起 agent 参数`
  - Translation:         caller_agent: str = None,  # Add initiating agent parameter

- Line 473: `        target_agent: str = None,  # 添加目标 agent 参数`
  - Translation:         target_agent: str = None,  # Add target agent parameter

- Line 474: `        use_two_way_auth: bool = False,  # 是否使用双向认证`
  - Translation:         use_two_way_auth: bool = False,  # Whether to use two-way authentication

- Line 477: `        agent_name: str = "智能爬虫"`
  - Translation:         agent_name: str = "Intelligent Crawler"

- Line 481: `        通用智能爬虫功能 - 使用大模型自主决定爬取路径`
  - Translation:         General intelligent crawler function - autonomously determine crawling paths using large models

- Line 483: `        参数:`
  - Translation:         Parameters:

- Line 484: `            user_input: 用户输入的任务描述`
  - Translation:             user_input: Task description entered by the user

- Line 485: `            initial_url: 初始URL`
  - Translation:             initial_url: Initial URL

- Line 486: `            prompt_template: 提示模板字符串，需要包含{task_description}和{initial_url}占位符`
  - Translation:             prompt_template: A template string for prompts, which must include placeholders {task_description} and {initial_url}.

- Line 487: `            task_type: 任务类型`
  - Translation:             task_type: Task Type

- Line 488: `            max_documents: 最大爬取文档数`
  - Translation:             max_documents: Maximum number of documents to crawl

- Line 489: `            agent_name: 代理名称（用于日志显示）`
  - Translation:             agent_name: Agent Name (for log display)

- Line 490: `            did_document_path: DID文档路径，如果为None将使用默认路径`
  - Translation:             did_document_path: DID document path, if None, the default path will be used.

- Line 491: `            private_key_path: 私钥路径，如果为None将使用默认路径`
  - Translation:             private_key_path: Private key path, if None, the default path will be used

- Line 493: `        返回:`
  - Translation:         Return:

- Line 494: `            Dict: 包含爬取结果的字典`
  - Translation:             Dict: Dictionary containing the crawling results

- Line 496: `        self.step_helper.pause(f"启动{agent_name}智能爬取: {initial_url}")`
  - Translation:         self.step_helper.pause(f"Initiating intelligent crawling for {agent_name}: {initial_url}")

- Line 498: `        # 引入必要的依赖`
  - Translation:         # Import necessary dependencies

- Line 501: `        # 初始化变量`
  - Translation:         # Initialize variable

- Line 505: `        # 初始化ANPTool`
  - Translation:         # Initialize ANPTool

- Line 506: `        logger.debug("初始化ANP工具...")`
  - Translation:         logger.debug("Initializing ANP tool...")

- Line 512: `        # 获取初始URL内容`
  - Translation:         # Retrieve initial URL content

- Line 514: `            logger.debug(f"开始获取初始URL: {initial_url}")`
  - Translation:             logger.debug(f"Starting to retrieve the initial URL: {initial_url}")

- Line 520: `            logger.debug(f"成功获取初始URL: {initial_url}")`
  - Translation:             logger.debug(f"Successfully obtained initial URL: {initial_url}")

- Line 522: `            logger.error(f"获取初始URL {initial_url} 失败: {str(e)}")`
  - Translation:             logger.error(f"Failed to retrieve initial URL {initial_url}: {str(e)}")

- Line 524: `                "content": f"获取初始URL失败: {str(e)}",`
  - Translation:                 "content": f"Failed to retrieve initial URL: {str(e)}",

- Line 531: `        # 创建初始消息`
  - Translation:         # Create initial message

- Line 541: `                "content": f"我已获取初始URL的内容。以下是{agent_name}的描述数据:\n\n```json\n{json.dumps(initial_content, ensure_ascii=False, indent=2)}\n```\n\n请分析这些数据，理解{agent_name}的功能和API使用方法。找到你需要访问的链接，并使用anp_tool获取更多信息以完成用户的任务。",`
  - Translation:                 "content": f"I have obtained the content of the initial URL. Here is the descriptive data for {agent_name}:\n\n```json\n{json.dumps(initial_content, ensure_ascii=False, indent=2)}\n```\n\nPlease analyze this data to understand the functionality and API usage of {agent_name}. Find the links you need to access, and use anp_tool to obtain more information to complete the user's task."

- Line 545: `        # 创建客户端`
  - Translation:         # Create client

- Line 547: `            # 尝试使用环境变量创建合适的客户端`
  - Translation:             # Attempt to create an appropriate client using environment variables.

- Line 561: `            logger.error(f"创建LLM客户端失败: {e}")`
  - Translation:             logger.error(f"Failed to create LLM client: {e}")

- Line 563: `                "content": f"LLM客户端创建失败: {str(e)}",`
  - Translation:                 "content": f"LLM client creation failed: {str(e)}",

- Line 570: `        # 开始对话循环`
  - Translation:         # Start conversation loop

- Line 575: `            logger.debug(f"开始爬取迭代 {current_iteration}/{max_documents}")`
  - Translation:             logger.debug(f"Starting crawl iteration {current_iteration}/{max_documents}")

- Line 577: `            # 检查是否已达到最大爬取文档数`
  - Translation:             # Check if the maximum number of documents to crawl has been reached

- Line 579: `                logger.debug(f"已达到最大爬取文档数 {max_documents}，停止爬取")`
  - Translation:                 logger.debug(f"Reached the maximum number of documents to crawl {max_documents}, stopping the crawl")

- Line 580: `                # 添加消息通知模型已达到最大爬取限制`
  - Translation:                 # Add message notification: the model has reached the maximum crawling limit.

- Line 583: `                    "content": f"你已爬取 {len(crawled_documents)} 个文档，达到最大爬取限制 {max_documents}。请根据获取的信息做出最终总结。",`
  - Translation:                     "content": f"You have crawled {len(crawled_documents)} documents, reaching the maximum crawl limit of {max_documents}. Please make a final summary based on the information obtained."

- Line 586: `            # 获取模型响应`
  - Translation:             # Get model response

- Line 587: `            self.step_helper.pause(f"迭代 {current_iteration}: 请求模型分析和决策")`
  - Translation:             self.step_helper.pause(f"Iteration {current_iteration}: Requesting model analysis and decision-making")

- Line 604: `                # 显示模型分析`
  - Translation:                 # Display model analysis

- Line 606: `                    logger.debug(f"模型分析:\n{response_message.content}")`
  - Translation:                     logger.debug(f"Model analysis:\n{response_message.content}")

- Line 608: `                # 检查对话是否应该结束`
  - Translation:                 # Check if the conversation should end

- Line 610: `                    logger.debug("模型没有请求任何工具调用，结束爬取")`
  - Translation:                     logger.debug("The model did not request any tool invocation, ending the crawl")

- Line 613: `                # 处理工具调用`
  - Translation:                 # Process tool invocation

- Line 614: `                self.step_helper.pause(f"迭代 {current_iteration}: 执行工具调用")`
  - Translation:                 self.step_helper.pause(f"Iteration {current_iteration}: Execute tool invocation")

- Line 615: `                logger.debug(f"执行 {len(response_message.tool_calls)} 个工具调用")`
  - Translation:                 logger.debug(f"Executing {len(response_message.tool_calls)} tool calls")

- Line 628: `                    # 如果已达到最大爬取文档数，停止处理工具调用`
  - Translation:                     # If the maximum number of documents to crawl has been reached, stop processing tool invocation.

- Line 632: `                # 如果已达到最大爬取文档数，做出最终总结`
  - Translation:                 # If the maximum number of documents to crawl has been reached, make the final summary.

- Line 634: `                    logger.debug(f"已达到最大爬取文档数 {max_documents}，做出最终总结")`
  - Translation:                     logger.debug(f"Reached the maximum number of documents to crawl {max_documents}, making the final summary")

- Line 638: `                logger.error(f"模型调用或工具处理失败: {e}")`
  - Translation:                 logger.error(f"Model invocation or tool processing failed: {e}")

- Line 642: `                # 添加失败信息到消息列表`
  - Translation:                 # Add failure information to the message list

- Line 645: `                    "content": f"在处理过程中发生错误: {str(e)}。请根据已获取的信息做出最佳判断。",`
  - Translation:                     "content": f"An error occurred during processing: {str(e)}. Please make the best judgment based on the information obtained.",

- Line 648: `                # 再给模型一次机会总结`
  - Translation:                 # Give the model another chance to summarize.

- Line 656: `                    # 如果再次失败，使用最后成功的消息`
  - Translation:                     # If it fails again, use the last successful message.

- Line 660: `                        # 创建一个简单的错误回复`
  - Translation:                         # Create a simple error response

- Line 662: `                            "content": f"很抱歉，在处理您的请求时遇到了错误。已爬取的文档数: {len(crawled_documents)}。"`
  - Translation:                             "content": f"Sorry, an error occurred while processing your request. Number of documents crawled: {len(crawled_documents)}."

- Line 665: `                # 退出循环`
  - Translation:                 # Exit the loop

- Line 668: `        # 创建结果`
  - Translation:         # Create result

- Line 678: `        # 显示结果`
  - Translation:         # Display results

- Line 679: `        self.step_helper.pause(f"{agent_name}智能爬取完成，显示结果")`
  - Translation:         self.step_helper.pause(f"{agent_name} intelligent crawling completed, displaying results")

- Line 680: `        logger.debug(f"\n=== {agent_name}响应 ===")`
  - Translation:         logger.debug(f"\n=== {agent_name} Response ===")

- Line 683: `        logger.debug("\n=== 访问过的URL ===")`
  - Translation:         logger.debug("\n=== Visited URLs ===")

- Line 687: `        logger.debug(f"\n=== 总共爬取了 {len(result.get('crawled_documents', []))} 个文档 ===")`
  - Translation:         logger.debug(f"\n=== A total of {len(result.get('crawled_documents', []))} documents were crawled ===")

- Line 691: `        # 定义可用工具`
  - Translation:         # Define available tools

- Line 693: `        """获取可用工具列表"""`
  - Translation:         """Get the list of available tools"""

- Line 714: `        anpsdk = None,  # 添加 anpsdk 参数`
  - Translation:         anpsdk = None,  # Add anpsdk parameter

- Line 715: `        caller_agent: str = None,  # 添加发起 agent 参数`
  - Translation:         caller_agent: str = None,  # Add initiating agent parameter

- Line 716: `        target_agent: str = None,  # 添加目标 agent 参数`
  - Translation:         target_agent: str = None,  # Add target agent parameter

- Line 717: `        use_two_way_auth: bool = False  # 是否使用双向认证`
  - Translation:         use_two_way_auth: bool = False  # Whether to use two-way authentication

- Line 719: `        """处理工具调用"""`
  - Translation:         Handle tool invocation

- Line 731: `                # 使用 ANPTool 获取 URL 内容`
  - Translation:                 # Use ANPTool to retrieve URL content

- Line 741: `                logger.debug(f"ANPTool 响应 [url: {url}]")`
  - Translation:                 logger.debug(f"ANPTool response [url: {url}]")

- Line 743: `                # 记录访问过的 URL 和获取的内容`
  - Translation:                 # Record visited URLs and retrieved content

- Line 755: `                logger.error(f"使用 ANPTool 获取 URL {url} 时出错: {str(e)}")`
  - Translation:                 logger.error(f"Error occurred while using ANPTool to get URL {url}: {str(e)}")

- Line 763: `                                "error": f"使用 ANPTool 获取 URL 失败: {url}",`
  - Translation:                                 "error": f"Failed to retrieve URL using ANPTool: {url}",

- Line 772: `        """使用新的 GroupRunner SDK 运行群聊演示"""`
  - Translation:         """Run group chat demo using the new GroupRunner SDK"""

- Line 774: `        logger.debug("🚀 运行增强群聊演示 (使用增强的 GroupMember 与 GroupRunner)")`
  - Translation:         logger.debug("🚀 Running enhanced group chat demo (using enhanced GroupMember and GroupRunner)")

- Line 777: `            # 注册 GroupRunner`
  - Translation:             # Register GroupRunner

- Line 778: `            logger.debug("📋 注册 GroupRunner...")`
  - Translation:             logger.debug("📋 Registering GroupRunner...")

- Line 782: `            # 创建 GroupMember 客户端（使用不同的扩展类）`
  - Translation:             # Create GroupMember client (using different extension classes)

- Line 783: `            logger.debug("👥 创建群组成员客户端...")`
  - Translation:             logger.debug("👥 Creating group member client...")

- Line 788: `            # 使用不同的扩展 GroupMember`
  - Translation:             # Use different extensions for GroupMember

- Line 793: `            # 设置本地 SDK 优化`
  - Translation:             # Set local SDK optimization

- Line 798: `            # 定义消息处理器`
  - Translation:             # Define message handler

- Line 808: `            # 演示1: 普通群聊`
  - Translation:             # Demo 1: Regular Group Chat

- Line 809: `            logger.debug("\n📋 演示1: 普通群聊")`
  - Translation:             logger.debug("\n📋 Demo 1: Regular Group Chat")

- Line 812: `            # 加入群组`
  - Translation:             # Join Group

- Line 813: `            logger.debug("👥 加入普通群聊...")`
  - Translation:             logger.debug("👥 Joining a regular group chat...")

- Line 818: `            # 开始监听`
  - Translation:             # Start listening

- Line 823: `            await asyncio.sleep(1)  # 等待监听器启动`
  - Translation:             await asyncio.sleep(1)  # Wait for the listener to start

- Line 825: `            # 发送消息`
  - Translation:             # Send message

- Line 826: `            logger.debug("\n💬 发送普通群聊消息...")`
  - Translation:             logger.debug("\n💬 Sending a regular group chat message...")

- Line 834: `            # 演示2: 审核群聊`
  - Translation:             # Demo 2: Review Group Chat

- Line 835: `            logger.debug("\n🛡️ 演示2: 审核群聊")`
  - Translation:             logger.debug("\n🛡️ Demo 2: Review Group Chat")

- Line 838: `            # 加入审核群组`
  - Translation:             # Join the review group

- Line 839: `            logger.debug("👥 加入审核群聊...")`
  - Translation:             logger.debug("👥 Joining the review group chat...")

- Line 843: `            # 开始监听审核群组`
  - Translation:             # Start monitoring the audit group.

- Line 848: `            # 发送正常消息`
  - Translation:             # Send normal message

- Line 849: `            logger.debug("\n💬 发送正常消息...")`
  - Translation:             logger.debug("\n💬 Sending a normal message...")

- Line 853: `            # 发送违规消息`
  - Translation:             # Send violation message

- Line 854: `            logger.debug("\n🚫 发送违规消息...")`
  - Translation:             logger.debug("\n🚫 Sending violation message...")

- Line 858: `            # 发送另一个正常消息`
  - Translation:             # Send another normal message

- Line 862: `            # 显示扩展信息`
  - Translation:             # Display extended information

- Line 863: `            logger.debug("\n📊 扩展功能信息:")`
  - Translation:             logger.debug("\n📊 Extension Feature Information:")

- Line 865: `            logger.debug("存储功能 (member1):")`
  - Translation:             logger.debug("Storage function (member1):")

- Line 869: `            logger.debug("\n统计功能 (member2):")`
  - Translation:             logger.debug("\nStatistics Function (member2):")

- Line 874: `                logger.debug("\n完整功能 (member3):")`
  - Translation:                 logger.debug("\nFull functionality (member3):")

- Line 878: `            # 显示群组日志`
  - Translation:             # Display group logs

- Line 879: `            logger.debug("\n📋 显示群组运行日志:")`
  - Translation:             logger.debug("\n📋 Display group operation log:")

- Line 885: `            for group_name, log_file in zip(["普通群聊", "审核群聊"], group_log_files):`
  - Translation:             for group_name, log_file in zip(["Regular Group Chat", "Review Group Chat"], group_log_files):

- Line 891: `            # 显示接收到的消息`
  - Translation:             # Display the received message

- Line 892: `            logger.debug("\n📁 显示接收到的群组消息:")`
  - Translation:             logger.debug("\n📁 Display received group message:")

- Line 895: `            # 获取简化的 agent ID 作为文件名前缀`
  - Translation:             # Get the simplified agent ID as the file name prefix

- Line 899: `            # 只显示有存储功能的 agent 的消息`
  - Translation:             # Only display messages from agents with storage functionality.

- Line 909: `                    logger.debug(f"\n📨 {agent.name}: 使用的是 {agent_type} 类，不具备存储功能")`
  - Translation:                     logger.debug(f"\n📨 {agent.name}: Using the {agent_type} class, which does not have storage capabilities")

- Line 911: `            # 清空所有文件`
  - Translation:             # Clear all files

- Line 918: `            # 清理`
  - Translation:             # Cleanup

- Line 919: `            logger.debug("\n🧹 清理群聊连接...")`
  - Translation:             logger.debug("\n🧹 Cleaning up group chat connections...")

- Line 932: `            logger.debug("✅ 增强群聊演示完成")`
  - Translation:             logger.debug("✅ Enhanced group chat demonstration completed")

- Line 935: `            logger.debug(f"❌ 增强群聊演示过程中出错: {e}")`
  - Translation:             logger.debug(f"❌ Error occurred during enhanced group chat demonstration: {e}")

- Line 940: `        """清空demo_data目录及其子目录中的所有文件，但保留目录结构"""`
  - Translation:         """Clear all files in the demo_data directory and its subdirectories, but retain the directory structure"""

- Line 941: `        self.step_helper.pause("开始清空demo_data目录下的所有文件")`
  - Translation:         self.step_helper.pause("Start clearing all files in the demo_data directory")

- Line 944: `            # 获取demo_data目录路径`
  - Translation:             # Get the path of the demo_data directory

- Line 947: `                logger.warning(f"demo_data目录不存在: {demo_data_path}")`
  - Translation:                 logger.warning(f"The demo_data directory does not exist: {demo_data_path}")

- Line 951: `            logger.debug(f"正在清空目录: {demo_data_path}")`
  - Translation:             logger.debug(f"Clearing directory: {demo_data_path}")

- Line 953: `            # 遍历目录及其子目录`
  - Translation:             # Traverse the directory and its subdirectories

- Line 955: `                # 清空文件`
  - Translation:                 # Clear the file

- Line 959: `                        # 清空文件内容而非删除文件，这样保留文件结构`
  - Translation:                         # Clear the file content instead of deleting the file, thus preserving the file structure.

- Line 963: `                        logger.debug(f"已清空文件: {file_path}")`
  - Translation:                         logger.debug(f"File has been cleared: {file_path}")

- Line 965: `                        logger.error(f"清空文件失败 {file_path}: {e}")`
  - Translation:                         logger.error(f"Failed to clear file {file_path}: {e}")

- Line 967: `            logger.debug(f"清空完成，共处理了 {count_removed} 个文件")`
  - Translation:             logger.debug(f"Clearing completed, a total of {count_removed} files processed")

- Line 969: `            logger.error(f"清空demo_data时发生错误: {e}")`
  - Translation:             logger.error(f"Error occurred while clearing demo_data: {e}")

- Line 973: `        self.step_helper.pause("demo_data清空完成")`
  - Translation:         self.step_helper.pause("Demo data clearing completed")

- Line 976: `        """显示接收到的消息"""`
  - Translation:         Display the received message

- Line 977: `        logger.debug(f"\n{agent_name}接收到的群聊消息:")`
  - Translation:         logger.debug(f"\nGroup chat message received by {agent_name}:")

- Line 986: `                logger.debug(f"批量收到消息:\n{json.dumps(messages, ensure_ascii=False, indent=2)}")`
  - Translation:                 logger.debug(f"Batch received messages:\n{json.dumps(messages, ensure_ascii=False, indent=2)}")

- Line 988: `                logger.debug("未收到任何消息")`
  - Translation:                 logger.debug("No messages received")

- Line 990: `            logger.error(f"读取消息文件失败: {e}")`
  - Translation:             logger.error(f"Failed to read message file: {e}")

- Line 994: `        """显示 agent 接收到的群组消息"""`
  - Translation:         Display the group message received by the agent

- Line 999: `                logger.debug(f"\n📨 {agent_name} 接收到的消息 ({len(messages)} 条):")`
  - Translation:                 logger.debug(f"\n📨 Messages received by {agent_name} ({len(messages)} items):")

- Line 1009: `                logger.debug(f"\n📨 {agent_name}: 没有找到消息文件")`
  - Translation:                 logger.debug(f"\n📨 {agent_name}: Message file not found")

- Line 1011: `            logger.debug(f"❌ 读取 {agent_name} 的消息文件时出错: {e}")`
  - Translation:             logger.debug(f"❌ Error reading message file for {agent_name}: {e}")

- Line 1014: `        """显示群组运行日志"""`
  - Translation:         Display group operation log

- Line 1019: `                logger.debug(f"\n📋 {group_name} 运行日志 ({len(logs)} 条):")`
  - Translation:                 logger.debug(f"\n📋 {group_name} Run Log ({len(logs)} entries):")

- Line 1032: `                        content += f" (原因: {log.get('reason', 'unknown')})"`
  - Translation:                         content += f" (Reason: {log.get('reason', 'unknown')})"

- Line 1037: `                logger.debug(f"\n📋 {group_name}: 没有找到日志文件")`
  - Translation:                 logger.debug(f"\n📋 {group_name}: Log file not found")

- Line 1039: `            logger.debug(f"❌ 读取 {group_name} 日志文件时出错: {e}")`
  - Translation:             logger.debug(f"❌ Error reading {group_name} log file: {e}")


## ./anp_open_sdk_demo/demo_modules/step_helper.py

- Line 4: `project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # 根据需要调整路径深度`
  - Translation: project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Adjust the path depth as needed

- Line 11: `init()  # 初始化colorama`
  - Translation: init()  # Initialize colorama

- Line 15: `    """演示步骤辅助工具"""`
  - Translation:     """Demonstration Step Assistance Tool"""

- Line 21: `        """暂停执行，等待用户确认"""`
  - Translation:         Pause execution, waiting for user confirmation

- Line 27: `                  f"{Fore.YELLOW}按任意键继续...{Style.RESET_ALL}")`
  - Translation:                   f"{Fore.YELLOW}Press any key to continue...{Style.RESET_ALL}")

- Line 31: `        """从helper.json加载帮助文本"""`
  - Translation:         """Load help text from helper.json"""

- Line 43: `            logger.error(f"读取帮助文件时发生错误: {e}")`
  - Translation:             logger.error(f"An error occurred while reading the help file: {e}")


## ./anp_open_sdk_demo/demo_modules/__init__.py

- Line 1: `"""演示模块包"""`
  - Translation: """Demo module package"""


## ./anp_open_sdk_demo/demo_modules/agent_batch_registry.py

- Line 15: `    """演示用Agent注册器"""`
  - Translation:     Agent registrar for demonstration

- Line 19: `        """注册API处理器"""`
  - Translation:         """Register API handler"""

- Line 21: `            logger.warning("智能体数量不足，无法注册所有API处理器")`
  - Translation:             logger.warning("Insufficient number of agents, unable to register all API handlers")

- Line 28: `        # 智能体的第一种API发布方式：装饰器`
  - Translation:         # First method of API exposure for the agent: Decorator

- Line 33: `                "msg": f"{agent1.name}的/hello接口收到请求:",`
  - Translation:                 "msg": f"Request received at {agent1.name}'s /hello endpoint:"

- Line 39: `        # 智能体的另一种API发布方式：显式注册`
  - Translation:         # Another way to publish the agent's API: explicit registration

- Line 43: `                "msg": f"{agent2.name}的/info接口收到请求:",`
  - Translation:                 "msg": f"Request received by {agent2.name}'s /info endpoint:"

- Line 52: `        """注册消息处理器"""`
  - Translation:         """Register message handler"""

- Line 54: `            logger.warning("智能体数量不足，无法注册所有消息处理器")`
  - Translation:             logger.warning("Insufficient number of agents, unable to register all message handlers")

- Line 61: `            logger.debug(f"{agent1.name}收到text消息: {msg}")`
  - Translation:             logger.debug(f"{agent1.name} received text message: {msg}")

- Line 62: `            return {"reply": f"{agent1.name}回复:确认收到text消息:{msg.get('content')}"}`
  - Translation:             return {"reply": f"{agent1.name} replies: Confirm receipt of text message: {msg.get('content')}"}

- Line 65: `            logger.debug(f"{agent2.name}收到text消息: {msg}")`
  - Translation:             logger.debug(f"{agent2.name} received text message: {msg}")

- Line 66: `            return {"reply": f"{agent2.name}回复:确认收到text消息:{msg.get('content')}"}`
  - Translation:             return {"reply": f"{agent2.name} replies: Confirm receipt of text message: {msg.get('content')}"}

- Line 71: `            logger.debug(f"{agent3.name}收到*类型消息: {msg}")`
  - Translation:             logger.debug(f"{agent3.name} received a * type message: {msg}")

- Line 73: `                "reply": f"{agent3.name}回复:确认收到{msg.get('type')}类型"`
  - Translation:                 "reply": f"{agent3.name} replies: Confirmation received for {msg.get('type')} type"

- Line 74: `                         f"{msg.get('message_type')}格式的消息:{msg.get('content')}"`
  - Translation:                          Message of type {msg.get('message_type')}: {msg.get('content')}

- Line 79: `        """注册群组事件处理器"""`
  - Translation:         """Register group event handler"""

- Line 82: `                logger.debug(f"{agent.name}收到群{group_id}的{event_type}事件，内容：{event_data}")`
  - Translation:                 logger.debug(f"{agent.name} received a {event_type} event from group {group_id}, content: {event_data}")

- Line 89: `        """保存群聊消息到文件"""`
  - Translation:         """Save group chat messages to a file"""

- Line 92: `            # 确保目录存在`
  - Translation:             # Ensure the directory exists

- Line 97: `            # 追加消息到文件`
  - Translation:             # Append message to file

- Line 101: `            logger.error(f"保存群聊消息到文件时出错: {e}")`
  - Translation:             logger.error(f"Error saving group chat message to file: {e}")


## ./anp_open_sdk_demo/demo_modules/customized_group_member.py

- Line 13: `    """带存储功能的 GroupMemberSDK"""`
  - Translation:     """GroupMemberSDK with storage functionality"""

- Line 25: `            logger.debug(f"🗂️ 存储目录已创建: {self.storage_dir}")  # 添加调试信息`
  - Translation:             logger.debug(f"🗂️ Storage directory created: {self.storage_dir}")  # Add debug information

- Line 28: `        """保存接收到的消息"""`
  - Translation:         """Save the received message"""

- Line 34: `        logger.debug(f"📝 正在保存消息到 {message_file}")  # 添加调试信息`
  - Translation:         logger.debug(f"📝 Saving message to {message_file}")  # Add debug information

- Line 46: `        # 读取现有消息`
  - Translation:         # Read existing messages

- Line 55: `        # 添加新消息`
  - Translation:         # Add new message

- Line 58: `        # 写回文件`
  - Translation:         # Write back to the file

- Line 63: `        """保存群组事件"""`
  - Translation:         Save group event

- Line 78: `        # 读取现有事件`
  - Translation:         # Read existing events

- Line 87: `        # 添加新事件`
  - Translation:         # Add new event

- Line 90: `        # 写回文件`
  - Translation:         # Write back to file

- Line 96: `        """重写加入群组方法，添加存储功能"""`
  - Translation:         Override the join group method to add storage functionality

- Line 109: `        """重写离开群组方法，添加存储功能"""`
  - Translation:         """Override the leave group method to add storage functionality"""

- Line 121: `        """重写发送消息方法，添加存储功能"""`
  - Translation:         """Override the send message method to add storage functionality"""

- Line 125: `            # 保存发送的消息`
  - Translation:             # Save the sent message

- Line 139: `        """保存发送的消息"""`
  - Translation:         """Save the sent message"""

- Line 155: `        # 读取现有消息`
  - Translation:         # Read existing messages

- Line 164: `        # 添加新消息`
  - Translation:         # Add new message

- Line 167: `        # 写回文件`
  - Translation:         # Write back to file

- Line 173: `        """重写监听方法，添加存储功能"""`
  - Translation:         """Override the listener method to add storage functionality"""

- Line 175: `        # 包装回调函数以添加存储功能`
  - Translation:         # Wrap the callback function to add storage functionality.

- Line 177: `            # 先存储消息`
  - Translation:             # First, store the message.

- Line 181: `            # 再调用原始回调`
  - Translation:             # Call the original callback again

- Line 184: `        # 调用父类的监听方法`
  - Translation:         # Call the listener method of the parent class

- Line 188: `        """获取存储统计信息"""`
  - Translation:         """Get storage statistics"""

- Line 195: `        # 统计各种文件`
  - Translation:         # Count various files

- Line 222: `    """带统计功能的 GroupMemberSDK"""`
  - Translation:     """GroupMemberSDK with statistical features"""

- Line 238: `        """重写加入群组方法，添加统计功能"""`
  - Translation:         """Override the join group method to add statistical functionality"""

- Line 250: `        """重写发送消息方法，添加统计功能"""`
  - Translation:         Override the send message method to add statistical functionality

- Line 264: `        """重写监听方法，添加统计功能"""`
  - Translation:         """Override the listener method to add statistical functionality"""

- Line 267: `            # 更新统计`
  - Translation:             # Update statistics

- Line 280: `            # 调用原始回调`
  - Translation:             # Invoke the original callback

- Line 286: `        """获取统计信息"""`
  - Translation:         """Get statistics"""

- Line 288: `        stats["groups_joined"] = list(stats["groups_joined"])  # 转换 set 为 list`
  - Translation:         stats["groups_joined"] = list(stats["groups_joined"])  # Convert set to list

- Line 293: `    """完整功能的 GroupMember（继承存储功能，添加统计功能）"""`
  - Translation:     """Full-featured GroupMember (inherits storage functionality, adds statistical functionality)"""

- Line 301: `        # 添加统计功能`
  - Translation:         # Add statistical functionality

- Line 312: `        """重写加入群组方法，同时支持存储和统计"""`
  - Translation:         Override the join group method to support storage and statistics

- Line 323: `        """重写发送消息方法，同时支持存储和统计"""`
  - Translation:         """Override the send message method to support both storage and statistics"""

- Line 337: `        """重写监听方法，同时支持存储和统计"""`
  - Translation:         """Override the listener method to support both storage and statistics"""

- Line 340: `            # 更新统计`
  - Translation:             # Update statistics

- Line 353: `            # 存储功能在父类的 listen_group 中已经处理`
  - Translation:             # The storage functionality has already been handled in the listen_group of the parent class.

- Line 354: `            # 调用原始回调`
  - Translation:             # Invoke original callback

- Line 357: `        # 调用 GroupMemberWithStorage 的 listen_group，它会处理存储`
  - Translation:         # Call `listen_group` of `GroupMemberWithStorage`, it will handle storage.

- Line 361: `        """获取统计信息"""`
  - Translation:         """Get statistics"""

- Line 367: `        """获取完整信息（存储 + 统计）"""`
  - Translation:         """Get complete information (storage + statistics)"""


## ./anp_open_sdk_demo/demo_modules/customized_group_runner.py

- Line 13: `    """带文件日志功能的基础 GroupRunner"""`
  - Translation:     """Base GroupRunner with file logging capability"""

- Line 19: `        logger.debug(f"🗂️ 群组日志目录已创建: {self.log_dir}")  # 添加调试信息`
  - Translation:         logger.debug(f"🗂️ Group log directory created: {self.log_dir}")  # Add debug information

- Line 22: `        """保存消息到文件"""`
  - Translation:         Save message to file

- Line 25: `        # 读取现有消息`
  - Translation:         # Read existing messages

- Line 34: `        # 添加新消息`
  - Translation:         # Add new message

- Line 37: `        # 写回文件`
  - Translation:         # Write back to the file

- Line 43: `    """带日志的简单聊天室"""`
  - Translation:     """Simple chat room with logging"""

- Line 48: `        # 记录加入事件`
  - Translation:         # Log join event

- Line 59: `        # 广播加入消息`
  - Translation:         # Broadcast join message

- Line 73: `        # 记录离开事件`
  - Translation:         # Record the exit event

- Line 84: `        # 广播离开消息`
  - Translation:         # Broadcast leave message

- Line 97: `        # 保存消息到文件`
  - Translation:         # Save message to file

- Line 108: `        # 广播消息给所有人（除了发送者）`
  - Translation:         # Broadcast message to everyone (except the sender)

- Line 113: `    """带日志和审核的聊天室"""`
  - Translation:     """Chat room with logging and auditing"""

- Line 123: `        # 检查黑名单`
  - Translation:         # Check blacklist

- Line 128: `        # 第一个加入的是管理员`
  - Translation:         # The first to join is the administrator.

- Line 137: `        # 记录加入事件`
  - Translation:         # Log join event

- Line 149: `        # 广播加入消息`
  - Translation:         # Broadcast join message

- Line 163: `        # 如果是管理员离开，移除管理员权限`
  - Translation:         # If the administrator leaves, remove administrator privileges.

- Line 168: `        # 记录离开事件`
  - Translation:         # Log exit event

- Line 179: `        # 广播离开消息`
  - Translation:         # Broadcast leave message

- Line 192: `        # 检查违禁词`
  - Translation:         # Check for prohibited words

- Line 197: `            # 记录被拦截的消息`
  - Translation:             # Log intercepted messages

- Line 208: `            # 发送警告给发送者`
  - Translation:             # Send a warning to the sender

- Line 221: `        # 保存通过审核的消息`
  - Translation:         # Save the messages that have passed the review

- Line 232: `        # 广播消息`
  - Translation:         # Broadcast message


## ./anp_open_sdk_demo/demo_modules/agent_loader.py

- Line 10: `    """演示用Agent加载器"""`
  - Translation:     """Demo Agent Loader"""

- Line 14: `        """加载演示用的智能体"""`
  - Translation:         """Load the demo agent"""

- Line 34: `                logger.warning(f'未找到预设名字={agent_name} 的用户数据')`
  - Translation:                 logger.warning(f'User data not found for preset name={agent_name}')

- Line 39: `        """查找托管的智能体"""`
  - Translation:         """Find managed agents"""


## ./anp_open_sdk_demo/services/sdk_manager.py

- Line 8: `    """SDK管理器"""`
  - Translation:     """SDK Manager"""

- Line 15: `        """初始化SDK"""`
  - Translation:         Initialize SDK

- Line 16: `        logger.debug("初始化ANPSDK...")`
  - Translation:         logger.debug("Initializing ANPSDK...")

- Line 21: `        """启动服务器"""`
  - Translation:         """Start the server"""

- Line 22: `        logger.debug("启动服务器...")`
  - Translation:         logger.debug("Starting the server...")

- Line 28: `                logger.error(f"服务器启动错误: {e}")`
  - Translation:                 logger.error(f"Server startup error: {e}")

- Line 34: `        # 等待服务器启动`
  - Translation:         # Waiting for the server to start

- Line 36: `        logger.debug("服务器启动完成")`
  - Translation:         logger.debug("Server startup complete")

- Line 40: `        """停止服务器"""`
  - Translation:         """Stop the server"""

- Line 42: `            logger.debug("停止服务器...")`
  - Translation:             logger.debug("Stopping the server...")


## ./anp_open_sdk_demo/services/__init__.py

- Line 1: `"""服务模块包"""`
  - Translation: """Service module package"""


## ./anp_open_sdk_demo/services/dns_service.py

- Line 8: `    """演示DNS服务"""`
  - Translation:     """Demonstrate DNS service"""

- Line 17: `        """注册子域名"""`
  - Translation:         """Register subdomain"""

- Line 20: `        logger.debug(f"注册域名: {full_domain} -> {port}")`
  - Translation:         logger.debug(f"Register domain: {full_domain} -> {port}")

- Line 23: `        """解析域名"""`
  - Translation:         Parse domain name

- Line 25: `        logger.debug(f"解析域名: {domain} -> {resolved}")`
  - Translation:         logger.debug(f"Resolving domain: {domain} -> {resolved}")

- Line 29: `        """启动DNS服务"""`
  - Translation:         """Start DNS service"""

- Line 30: `        logger.debug("启动DNS服务...")`
  - Translation:         logger.debug("Starting DNS service...")

- Line 35: `                # 模拟DNS服务运行`
  - Translation:                 # Simulate DNS service operation

- Line 43: `        """停止DNS服务"""`
  - Translation:         """Stop DNS service"""

- Line 44: `        logger.debug("停止DNS服务...")`
  - Translation:         logger.debug("Stopping DNS service...")

- Line 50: `        """获取已注册的域名"""`
  - Translation:         """Retrieve registered domain names"""


## ./anp_open_sdk_framework/agent_manager.py

- Line 16: `    """本地 Agent 管理器，负责加载、注册和生成接口文档"""`
  - Translation:     """Local Agent Manager, responsible for loading, registering, and generating API documentation"""

- Line 20: `        """从模块路径加载 Agent 实例"""`
  - Translation:         """Load Agent instance from module path"""

- Line 38: `        # 1. agent_002: 存在 agent_register.py，优先自定义注册`
  - Translation:         # 1. agent_002: Exists in agent_register.py, prioritize custom registration

- Line 48: `        # 2. agent_llm: 存在 initialize_agent`
  - Translation:         # 2. agent_llm: Exists initialize_agent

- Line 57: `        # 3. 普通配置型 agent_001 / agent_caculator`
  - Translation:         # 3. Standard Configuration Type agent_001 / agent_calculator

- Line 74: `        """根据 Agent 的路由生成自定义的 OpenAPI 规范"""`
  - Translation:         """Generate custom OpenAPI specifications based on the routing of the Agent"""

- Line 90: `            summary = summary_map.get(path, handler.__doc__ or f"{agent.name}的{path}接口")`
  - Translation:             summary = summary_map.get(path, handler.__doc__ or f"{agent.name}'s {path} interface")

- Line 108: `                            "description": "返回结果",`
  - Translation:                             "description": "Return result",

- Line 122: `        """为指定的 agent 生成并保存 OpenAPI (YAML) 和 JSON-RPC 接口文件"""`
  - Translation:         """Generate and save OpenAPI (YAML) and JSON-RPC interface files for the specified agent"""

- Line 123: `        logger.debug(f"开始为 agent '{agent.name}' ({agent.id}) 生成接口文件...")`
  - Translation:         logger.debug(f"Starting to generate interface file for agent '{agent.name}' ({agent.id})...")

- Line 127: `            logger.error(f"无法找到 agent '{agent.name}' 的用户数据，无法保存接口文件。")`
  - Translation:             logger.error(f"Unable to find user data for agent '{agent.name}', unable to save interface file.")

- Line 131: `        # 2. 生成并保存 OpenAPI YAML 文件`
  - Translation:         # 2. Generate and save the OpenAPI YAML file

- Line 141: `            logger.error(f"为 agent '{agent.name}' 生成 OpenAPI YAML 文件失败: {e}")`
  - Translation:             logger.error(f"Failed to generate OpenAPI YAML file for agent '{agent.name}': {e}")

- Line 143: `        # 3. 生成并保存 JSON-RPC 文件`
  - Translation:         # 3. Generate and save JSON-RPC file

- Line 184: `            logger.error(f"为 agent '{agent.name}' 生成 JSON-RPC 文件失败: {e}")`
  - Translation:             logger.error(f"Failed to generate JSON-RPC file for agent '{agent.name}': {e}")


## ./anp_open_sdk_framework/local_methods/local_methods_doc.py

- Line 7: `    """本地方法文档生成器"""`
  - Translation:     """Local Method Documentation Generator"""

- Line 11: `        """生成所有本地方法的文档"""`
  - Translation:         """Generate documentation for all local methods"""

- Line 18: `        # 保存到文件`
  - Translation:         # Save to file

- Line 22: `        print(f"📚 已生成本地方法文档: {output_path}")`
  - Translation:         print(f"📚 Local method documentation generated: {output_path}")

- Line 27: `        """搜索本地方法"""`
  - Translation:         Search for local methods

- Line 31: `            # 关键词匹配`
  - Translation:             # Keyword Matching

- Line 36: `            # Agent名称匹配`
  - Translation:             # Agent Name Matching

- Line 40: `            # 标签匹配`
  - Translation:             # Tag Matching

- Line 58: `        """获取指定方法的详细信息"""`
  - Translation:         """Get detailed information of the specified method"""


## ./anp_open_sdk_framework/local_methods/local_methods_decorators.py

- Line 6: `# 全局注册表，存储所有本地方法信息`
  - Translation: # Global registry, storing all local method information.

- Line 11: `    本地方法装饰器`
  - Translation:     Local method decorator

- Line 14: `        description: 方法描述`
  - Translation:         description: Method description

- Line 15: `        tags: 方法标签`
  - Translation:         tags: method tags

- Line 18: `        # 获取函数签名信息`
  - Translation:         # Get function signature information

- Line 21: `        # 存储方法信息到全局注册表`
  - Translation:         # Store method information in the global registry

- Line 28: `            "agent_did": None,  # 稍后注册时填入`
  - Translation:             "agent_did": None,  # To be filled in during registration later

- Line 34: `        # 解析参数信息`
  - Translation:         # Parse parameter information

- Line 42: `        # 标记函数并存储信息`
  - Translation:         # Mark the function and store information

- Line 51: `    将标记的本地方法注册到agent，并更新全局注册表`
  - Translation:     Register the marked local method to the agent and update the global registry.

- Line 61: `            # 注册到agent`
  - Translation:             # Register to agent

- Line 64: `            # 更新全局注册表`
  - Translation:             # Update global registry

- Line 73: `            print(f"✅ 已注册本地方法: {agent.name}.{name}")`
  - Translation:             print(f"✅ Registered local method: {agent.name}.{name}")

- Line 75: `    print(f"📝 共注册了 {registered_count} 个本地方法到 {agent.name}")`
  - Translation:     print(f"📝 A total of {registered_count} local methods have been registered to {agent.name}")


## ./anp_open_sdk_framework/local_methods/local_methods_caller.py

- Line 8: `    """本地方法调用器"""`
  - Translation:     "Local Method Invoker"

- Line 16: `        通过搜索关键词找到方法并调用`
  - Translation:         Find the method by searching for keywords and invoke it.

- Line 19: `            search_keyword: 搜索关键词`
  - Translation:             search_keyword: Search keyword

- Line 20: `            *args, **kwargs: 方法参数`
  - Translation:             *args, **kwargs: method parameters

- Line 22: `        # 搜索方法`
  - Translation:         # Search method

- Line 26: `            raise ValueError(f"未找到包含关键词 '{search_keyword}' 的方法")`
  - Translation:             raise ValueError(f"Method containing the keyword '{search_keyword}' not found")

- Line 30: `            raise ValueError(f"找到多个匹配的方法: {method_list}，请使用更具体的关键词")`
  - Translation:             raise ValueError(f"Multiple matching methods found: {method_list}, please use more specific keywords")

- Line 32: `        # 调用找到的方法`
  - Translation:         # Call the found method

- Line 41: `        通过方法键调用方法`
  - Translation:         Call the method using the method key

- Line 44: `            method_key: 方法键 (格式: agent_did::method_name)`
  - Translation:             method_key: Method Key (Format: agent_did::method_name)

- Line 45: `            *args, **kwargs: 方法参数`
  - Translation:             *args, **kwargs: method parameters

- Line 47: `        # 获取方法信息`
  - Translation:         # Get method information

- Line 50: `            raise ValueError(f"未找到方法: {method_key}")`
  - Translation:             raise ValueError(f"Method not found: {method_key}")

- Line 52: `        # 获取目标agent`
  - Translation:         # Get target agent

- Line 55: `            raise ValueError(f"未找到agent: {method_info['agent_did']}")`
  - Translation:             raise ValueError(f"Agent not found: {method_info['agent_did']}")

- Line 57: `        # 获取方法`
  - Translation:         # Get method

- Line 60: `            raise AttributeError(f"Agent {method_info['agent_name']} 没有方法 {method_name}")`
  - Translation:             raise AttributeError(f"Agent {method_info['agent_name']} does not have the method {method_name}")

- Line 64: `            raise TypeError(f"{method_name} 不是可调用方法")`
  - Translation:             raise TypeError(f"{method_name} is not a callable method")

- Line 66: `        # 调用方法`
  - Translation:         # Method invocation

- Line 67: `        print(f"🚀 调用方法: {method_info['agent_name']}.{method_name}")`
  - Translation:         print(f"🚀 Invoking method: {method_info['agent_name']}.{method_name}")

- Line 74: `        """列出所有可用的本地方法"""`
  - Translation:         """List all available local methods"""


## ./anp_open_sdk_framework_demo/agent_user_binding.py

- Line 12: `setup_logging() # 假设 setup_logging 内部也改用 get_global_config()`
  - Translation: setup_logging() # Assume that setup_logging is also modified to use get_global_config() internally.

- Line 45: `    # 检查重复`
  - Translation:     # Check for duplicates

- Line 50: `            print(f"❌ DID重复: {did} 被以下多个agent使用：")`
  - Translation:             print(f"❌ Duplicate DID: {did} is used by multiple agents:")

- Line 54: `    # 检查未绑定或不存在的did`
  - Translation:     # Check for unbound or non-existent did

- Line 62: `            print(f"\n⚠️  {yaml_path} 未绑定有效DID。")`
  - Translation:             print(f"\n⚠️  {yaml_path} is not bound to a valid DID.")

- Line 63: `            print("可用用户DID如下：")`
  - Translation:             print("Available user DID as follows:")

- Line 67: `            print(f"  [N] 新建用户DID")`
  - Translation:             print(f"  [N] Create new user DID")

- Line 68: `            choice = input("请选择要绑定的DID编号，或输入N新建：").strip()`
  - Translation:             choice = input("Please select the DID number to bind, or enter N to create a new one:").strip()

- Line 70: `                # 新建用户流程`
  - Translation:                 # New User Flow

- Line 71: `                print("请输入新用户信息：")`
  - Translation:                 print("Please enter new user information:")

- Line 72: `                name = input("用户名: ")`
  - Translation:                 name = input("Username: ")

- Line 73: `                host = input("主机名: ")`
  - Translation:                 host = input("Hostname: ")

- Line 74: `                port = input("端口号: ")`
  - Translation:                 port = input("Port number: ")

- Line 75: `                host_dir = input("主机路径: ")`
  - Translation:                 host_dir = input("Host path: ")

- Line 76: `                agent_type = input("用户类型: ")`
  - Translation:                 agent_type = input("User Type: ")

- Line 87: `                    print(f"新用户DID创建成功: {new_did}")`
  - Translation:                     print(f"New user DID created successfully: {new_did}")

- Line 90: `                    print("新建DID失败，跳过。")`
  - Translation:                     print("Failed to create new DID, skipping.")

- Line 97: `                    print(f"已绑定DID: {new_did}")`
  - Translation:                     print(f"Bound DID: {new_did}")

- Line 100: `                    print("无效选择，跳过。")`
  - Translation:                     print("Invalid selection, skipping.")

- Line 102: `            # 写回yaml`
  - Translation:             # Write back to YAML

- Line 105: `            print(f"已更新 {yaml_path} 的DID。")`
  - Translation:             print(f"Updated the DID of {yaml_path}.")

- Line 107: `    # 如果没有重复和未绑定不存在，列出yaml文件里的name、did和对应的users_data里的yaml里的name`
  - Translation:     # If there are no duplicates and unbound entries, list the name, did from the yaml file, and the corresponding name from users_data in the yaml file.

- Line 109: `        print("\n当前Agent与用户绑定关系:")`
  - Translation:         print("\nCurrent binding relationship between Agent and User:")

- Line 111: `        print(f"{'Agent名称':<20} {'Agent DID':<45} {'绑定用户':<20}\n")`
  - Translation:         print(f"{'Agent Name':<20} {'Agent DID':<45} {'Bound User':<20}\n")

- Line 118: `            agent_name = cfg.get("name", "未命名")`
  - Translation:             agent_name = cfg.get("name", "Unnamed")

- Line 119: `            agent_did = cfg.get("did", "无DID")`
  - Translation:             agent_did = cfg.get("did", "No DID")

- Line 121: `            # 查找对应的用户名`
  - Translation:             # Find the corresponding username

- Line 122: `            user_name = user_dids.get(agent_did, "未绑定")`
  - Translation:             user_name = user_dids.get(agent_did, "Not Bound")


## ./anp_open_sdk_framework_demo/framework_demo.py

- Line 25: `setup_logging() # 假设 setup_logging 内部也改用 get_global_config()`
  - Translation: setup_logging() # Assume setup_logging internally also uses get_global_config()

- Line 37: `    # --- 加载和初始化所有Agent模块 ---`
  - Translation:     # --- Load and initialize all Agent modules ---

- Line 47: `    # 过滤掉加载失败的`
  - Translation:     # Filter out the failed loads

- Line 57: `    # --- 启动SDK ---`
  - Translation:     # --- Initialize SDK ---

- Line 61: `    # --- 新增：后期初始化循环 ---`
  - Translation:     # Added: Post-initialization loop

- Line 67: `            await module.initialize_agent(agent, sdk)  # 传入 agent 和 sdk 实例`
  - Translation:             await module.initialize_agent(agent, sdk)  # Pass in the agent and sdk instances

- Line 73: `    # 用线程启动 server`
  - Translation:     # Use a thread to start the server

- Line 82: `    # 生成本地方法文档供查看，如果只是调用，不需要`
  - Translation:     # Generate local method documentation for review; if only calling, not needed.

- Line 83: `    # 在当前程序脚本所在目录下生成文档`
  - Translation:     # Generate documents in the directory where the current program script is located.

- Line 96: `        # 直接调用 agent 实例上的方法`
  - Translation:         # Directly call the method on the agent instance.

- Line 98: `        # agent中的自动抓取函数，自动从主地址搜寻所有did/ad/yaml文档`
  - Translation:         # The automatic scraping function in the agent automatically searches for all did/ad/yaml documents from the main address.

- Line 100: `        # agent中的联网调用函数，调用计算器`
  - Translation:         # Network call function in agent, call calculator

- Line 102: `        # agent中的联网调用函数，相当于发送消息`
  - Translation:         # The network call function in the agent is equivalent to sending a message.

- Line 104: `        # agent中的AI联网爬取函数，从一个did地址开始爬取`
  - Translation:         # AI network crawling function in agent, starting from a did address

- Line 106: `        # agent中的AI联网爬取函数，从多个did汇总地址开始爬取`
  - Translation:         # The AI networking crawling function in the agent starts crawling from multiple aggregated addresses of dids.

- Line 108: `        # agent中的本地api去调用另一个agent的本地api`
  - Translation:         # The local API in the agent calls the local API of another agent.

- Line 111: `        # agent中的本地api通过搜索本地api注册表去调用另一个agent的本地api`
  - Translation:         # The local API in the agent calls another agent's local API by searching the local API registry.

- Line 118: `    input("按任意键停止服务")`
  - Translation:     input("Press any key to stop the service")

- Line 120: `    # --- 清理 ---`
  - Translation:     # --- Cleanup ---

- Line 123: `    # 停止服务器`
  - Translation:     # Stop the server

- Line 124: `    # 注意：start_server() 是在单独线程中调用的，sdk.stop_server() 只有在 ANPSDK 实现了对应的停止机制时才有效`
  - Translation:     # Note: start_server() is called in a separate thread, and sdk.stop_server() is only effective when ANPSDK implements the corresponding stop mechanism.

- Line 131: `            logger.debug("  - sdk 实例没有 stop_server 方法，无法主动停止服务。")`
  - Translation:             logger.debug("  - SDK instance does not have a stop_server method, unable to actively stop the service.")

- Line 133: `    # 清理 Agent`
  - Translation:     # Clean up Agent


## ./scripts/extract_and_translate_zh.py

- Line 4: `SRC_DIR = '.'  # 根目录，可自定义`
  - Translation: SRC_DIR = '.'  # Root directory, customizable


## ./scripts/auto_translate_md_with_llm.py

- Line 5: `# 你可以用 openai.AsyncOpenAI 或 openai.OpenAI`
  - Translation: # You can use openai.AsyncOpenAI or openai.OpenAI

- Line 16: `    # 1. 提取原文前缀（如 #、//、空格等）`
  - Translation:     # 1. Extract the original text prefix (e.g., #, //, spaces, etc.)

- Line 35: `        # 2. 去除 ```、```python 及多余换行`
  - Translation:         # 2. Remove ``` and ```python and extra line breaks

- Line 37: `        # 3. 去掉翻译内容开头的 //、#、空格等注释符`
  - Translation:         # 3. Remove the comment symbols such as //, #, spaces, etc. from the beginning of the translation content.

- Line 39: `        # 4. 用原文前缀替换`
  - Translation:         # 4. Replace with original text prefix

- Line 57: `            # 下一行是 Translation`
  - Translation:             # The next line is Translation

- Line 61: `                # 只翻译空的 Translation`
  - Translation:                 # Translate only the empty Translation

- Line 64: `                        # 达到上限，后续内容原样追加`
  - Translation:                         # Reached the limit, subsequent content will be appended as is.

- Line 75: `    # 写回`
  - Translation:     # Write back


## ./scripts/replace_from_md.py

- Line 18: `                # 读取下一行的 Translation`
  - Translation:                 # Read the next line's translation

- Line 32: `            # 只替换完全匹配的行`
  - Translation:             # Only replace lines that match completely


## ./anp_open_sdk/anp_sdk_agent.py

- Line 54: `    """本地智能体，代表当前用户的DID身份"""`
  - Translation:     """Local agent, representing the current user's DID identity"""

- Line 55: `    api_config: List[Dict[str, Any]]  # 用于多智能体加载时 从agent_mappings.yaml加载api相关扩展描述`
  - Translation:     api_config: List[Dict[str, Any]]  # Used for loading API-related extension descriptions from agent_mappings.yaml when loading multiple agents

- Line 57: `    def __init__(self, user_data, name: str = "未命名", agent_type: str = "personal"):`
  - Translation:     def __init__(self, user_data, name: str = "Unnamed", agent_type: str = "personal"):

- Line 58: `        """初始化本地智能体`
  - Translation:         """Initialize local agent

- Line 61: `            user_data: 用户数据对象`
  - Translation:             user_data: User data object

- Line 62: `            agent_type: 智能体类型，"personal"或"service"`
  - Translation:             agent_type: Agent type, "personal" or "service"

- Line 67: `        if name == "未命名":`
  - Translation:         if name == "Untitled":

- Line 71: `                self.name = f"未命名智能体{self.user_data.did}"`
  - Translation:                 self.name = f"Unnamed Agent {self.user_data.did}"

- Line 87: `        # 托管DID标识`
  - Translation:         # Managed DID Identifier

- Line 93: `        # 新增: API与消息handler注册表`
  - Translation:         # Added: API and message handler registry

- Line 96: `        # 新增: 群事件handler注册表`
  - Translation:         # Addition: Group event handler registry

- Line 99: `        # [(event_type, handler)] 全局handler`
  - Translation:         # [(event_type, handler)] Global handler

- Line 102: `        # 群组相关属性`
  - Translation:         # Group-related attributes

- Line 103: `        self.group_queues = {}  # 群组消息队列: {group_id: {client_id: Queue}}`
  - Translation:         self.group_queues = {}  # Group message queues: {group_id: {client_id: Queue}}

- Line 104: `        self.group_members = {}  # 群组成员列表: {group_id: set(did)}`
  - Translation:         self.group_members = {}  # Group member list: {group_id: set(did)}

- Line 106: `        # 新增：联系人管理器`
  - Translation:         # Added: Contact Manager

- Line 110: `    def from_did(cls, did: str, name: str = "未命名", agent_type: str = "personal"):`
  - Translation:     def from_did(cls, did: str, name: str = "Unnamed", agent_type: str = "personal"):

- Line 115: `        if name == "未命名":`
  - Translation:         if name == "Untitled":

- Line 118: `            raise ValueError(f"未找到 DID 为 {did} 的用户数据")`
  - Translation:             raise ValueError(f"User data with DID {did} not found")

- Line 128: `            logger.error(f"未找到 name 为 {name} 的用户数据")`
  - Translation:             logger.error(f"User data with name {name} not found")

- Line 133: `        """确保在对象销毁时释放资源"""`
  - Translation:         """Ensure resources are released when the object is destroyed"""

- Line 136: `                self.logger.debug(f"LocalAgent {self.id} 销毁时存在未关闭的WebSocket连接")`
  - Translation:                 self.logger.debug(f"LocalAgent {self.id} has unclosed WebSocket connections upon destruction")

- Line 139: `            self.logger.debug(f"LocalAgent {self.id} 资源已释放")`
  - Translation:             self.logger.debug(f"LocalAgent {self.id} resources have been released")

- Line 144: `        """获取用户目录"""`
  - Translation:         """Get user directory"""

- Line 147: `    # 支持装饰器和函数式注册API`
  - Translation:     # Support for decorators and functional registration API

- Line 156: `                    "summary": f.__doc__ or f"{self.name}的{path}接口",`
  - Translation:                     "summary": f.__doc__ or f"{self.name}'s {path} interface",

- Line 165: `                    logger.debug(f"注册 API: {api_info}")`
  - Translation:                     logger.debug(f"Register API: {api_info}")

- Line 173: `                "summary": func.__doc__ or f"{self.name}的{path}接口",`
  - Translation:                 "summary": func.__doc__ or f"Interface of {path} for {self.name}",

- Line 182: `                logger.debug(f"注册 API: {api_info}")`
  - Translation:                 logger.debug(f"Register API: {api_info}")

- Line 222: `                self.logger.error(f"群事件处理器出错: {e}")`
  - Translation:                 self.logger.error(f"Group event handler error: {e}")

- Line 264: `                        f"发送到 handler的请求数据{request_data}\n"                        `
  - Translation:                         f"Request data sent to handler: {request_data}\n"

- Line 265: `                        f"完整请求为 url: {request.url} \n"`
  - Translation:                         f"Complete request is url: {request.url} \n"

- Line 267: `                    self.logger.error(f"API调用错误: {e}")`
  - Translation:                     self.logger.error(f"API call error: {e}")

- Line 275: `                    content={"status": "error", "message": f"未找到API: {api_path}"}`
  - Translation:                     content={"status": "error", "message": f"API not found: {api_path}"}

- Line 287: `                    self.logger.error(f"消息处理错误: {e}")`
  - Translation:                     self.logger.error(f"Message processing error: {e}")

- Line 290: `                return {"anp_result": {"status": "error", "message": f"未找到消息处理器: {msg_type}"}}`
  - Translation:                 return {"anp_result": {"status": "error", "message": f"Message handler not found: {msg_type}"}}

- Line 292: `            return {"anp_result": {"status": "error", "message": "未知的请求类型"}}`
  - Translation:             return {"anp_result": {"status": "error", "message": "Unknown request type"}}

- Line 329: `            logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")`
  - Translation:             logger.debug(f"Initialize before checking registration email, using local file email backend parameters: {use_local}")

- Line 333: `                return "没有找到匹配的托管 DID 激活邮件"`
  - Translation:                 return "No matching hosted DID activation email found"

- Line 345: `                        logger.debug(f"无法解析 did_document: {e}")`
  - Translation:                         logger.debug(f"Unable to parse did_document: {e}")

- Line 350: `                        logger.debug(f"无法从id中提取host:port: {did_id}")`
  - Translation:                         logger.debug(f"Unable to extract host:port from id: {did_id}")

- Line 357: `                        logger.debug(f"已创建托管DID文件夹: {hosted_dir_name}")`
  - Translation:                         logger.debug(f"Hosted DID folder created: {hosted_dir_name}")

- Line 360: `                        logger.error(f"创建托管DID文件夹失败: {host}:{port}")`
  - Translation:                         logger.error(f"Failed to create hosted DID folder: {host}:{port}")

- Line 362: `                    logger.error(f"处理邮件时出错: {e}")`
  - Translation:                     logger.error(f"Error occurred while processing email: {e}")

- Line 364: `                return f"成功处理{count}封托管DID邮件"`
  - Translation:                 return f"Successfully processed {count} hosted DID emails"

- Line 366: `                return "未能成功处理任何托管DID邮件"`
  - Translation:                 return "Failed to successfully process any hosted DID messages"

- Line 368: `            logger.error(f"检查托管DID时发生错误: {e}")`
  - Translation:             logger.error(f"Error occurred while checking hosted DID: {e}")

- Line 369: `            return f"检查托管DID时发生错误: {e}"`
  - Translation:             return f"An error occurred while checking the hosted DID: {e}"

- Line 378: `                raise ValueError("当前 LocalAgent 未包含 did_document")`
  - Translation:                 raise ValueError("The current LocalAgent does not contain a did_document")

- Line 382: `            logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")`
  - Translation:             logger.debug(f"Initialization before registration email check, using local file email backend settings: {use_local}")

- Line 387: `                logger.debug("托管DID申请邮件已发送")`
  - Translation:                 logger.debug("Managed DID application email has been sent")

- Line 390: `                logger.error("发送托管DID申请邮件失败")`
  - Translation:                 logger.error("Failed to send the hosted DID application email")

- Line 393: `            logger.error(f"注册托管DID失败: {e}")`
  - Translation:             logger.error(f"Failed to register hosted DID: {e}")

- Line 412: `                logger.warning(f"读取托管配置失败: {e}")`
  - Translation:                 logger.warning(f"Failed to read managed configuration: {e}")

- Line 441: `                did_suffix = "无法匹配随机数"`
  - Translation:                 did_suffix = "Unable to match random number"

- Line 453: `                    logger.debug(f"已复制密钥文件: {key_file}")`
  - Translation:                     logger.debug(f"Key file copied: {key_file}")

- Line 455: `                    logger.warning(f"源密钥文件不存在: {src_path}")`
  - Translation:                     logger.warning(f"Source key file does not exist: {src_path}")

- Line 467: `                    'purpose': f"对外托管服务 - {host}:{port}"`
  - Translation:                     'purpose': f"External Hosting Service - {host}:{port}"

- Line 473: `            logger.debug(f"托管DID文件夹创建成功: {hosted_dir}")`
  - Translation:             logger.debug(f"Hosted DID folder created successfully: {hosted_dir}")

- Line 476: `            logger.error(f"创建托管DID文件夹失败: {e}")`
  - Translation:             logger.error(f"Failed to create managed DID folder: {e}")

- Line 485: `        # 其他模式由ANPSDK主导`
  - Translation:         # Other modes are led by ANPSDK.

- Line 503: `        # 可扩展更多自服务API`
  - Translation:         # Scalable for more self-service APIs

- Line 512: `                self.logger.error(f"WebSocket代理连接失败: {e}")`
  - Translation:                 self.logger.error(f"WebSocket proxy connection failed: {e}")

- Line 519: `            # 处理来自中心的请求`
  - Translation:             # Process requests from the center

- Line 520: `            # 这里可以根据data内容调用self.handle_request等`
  - Translation:             # Here you can call self.handle_request, etc., based on the content of data.

- Line 521: `            # 例如:`
  - Translation:             # For example:

- Line 524: `                # 伪造一个Request对象`
  - Translation:                 # Forge a Request object

- Line 532: `            # 可扩展其他消息类型`
  - Translation:             # Expandable to other message types


## ./anp_open_sdk/anp_sdk.py

- Line 33: `# 在模块顶部获取 logger，这是标准做法`
  - Translation: # Get the logger at the top of the module, which is standard practice.

- Line 38: `    """ANP SDK主类，支持多种运行模式"""`
  - Translation:     """ANP SDK main class, supports multiple operating modes"""

- Line 120: `        # 其他模式由LocalAgent主导`
  - Translation:         # Other modes are led by LocalAgent.

- Line 139: `                    # 处理代理注册、DID发布、API代理等`
  - Translation:                     # Handle proxy registration, DID issuance, API proxy, etc.

- Line 141: `                    self.logger.error(f"WebSocket客户端断开: {e}")`
  - Translation:                     self.logger.error(f"WebSocket client disconnected: {e}")

- Line 164: `            logger.debug(f"管理邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")`
  - Translation:             logger.debug(f"Initialize before checking management email, using local file mail backend settings: {use_local}")

- Line 170: `                return "没有新的DID托管请求"`
  - Translation:                 return "No new DID hosting requests"

- Line 172: `            result = "开始处理DID托管请求\n"`
  - Translation:             result = "Start processing DID hosting request\n"

- Line 184: `                        "DID已申请",`
  - Translation:                         "DID has been applied for"

- Line 185: `                        "重复的DID申请，请联系管理员"`
  - Translation:                         Duplicate DID application, please contact the administrator.

- Line 188: `                    result += f"{from_address}的DID {did_document_dict.get('id')} 已申请，退回\n"`
  - Translation:                     result += f"DID {did_document_dict.get('id')} from {from_address} has been applied for, returning\n"

- Line 198: `                    result += f"{from_address}的DID {new_did_doc['id']} 已保存\n"`
  - Translation:                     result += f"DID {new_did_doc['id']} from {from_address} has been saved\n"

- Line 202: `                        "DID托管申请失败",`
  - Translation:                         "DID hosting application failed"

- Line 203: `                        f"处理DID文档时发生错误: {error}"`
  - Translation:                         f"An error occurred while processing the DID document: {error}"

- Line 205: `                    result += f"{from_address}的DID处理失败: {error}\n"`
  - Translation:                     result += f"DID processing failed for {from_address}: {error}\n"

- Line 211: `            error_msg = f"处理DID托管请求时发生错误: {e}"`
  - Translation:             error_msg = f"An error occurred while processing the DID hosting request: {e}"

- Line 217: `        self.logger.debug(f"已注册智能体到SDK: {agent.id}")`
  - Translation:         self.logger.debug(f"Agent registered to SDK: {agent.id}")

- Line 269: `                                    "description": "成功响应",`
  - Translation:                                     "description": "Successful response"

- Line 329: `                                "description": "成功响应",`
  - Translation:                                 "description": "Successful response"

- Line 617: `                self.logger.debug(f"WebSocket客户端断开连接: {client_id}")`
  - Translation:                 self.logger.debug(f"WebSocket client disconnected: {client_id}")

- Line 621: `                self.logger.error(f"WebSocket处理错误: {e}")`
  - Translation:                 self.logger.error(f"WebSocket handling error: {e}")

- Line 626: `        logger.debug(f"准备处理接收到的消息内容: {message}")`
  - Translation:         logger.debug(f"Preparing to process the received message content: {message}")

- Line 638: `                self.logger.error(f"消息处理器执行错误: {e}")`
  - Translation:                 self.logger.error(f"Message processor execution error: {e}")

- Line 641: `            return {"status": "error", "message": f"未找到处理{message_type}类型消息的处理器"}`
  - Translation:             return {"status": "error", "message": f"Handler for message type {message_type} not found"}

- Line 645: `            self.logger.warning("服务器已经在运行")`
  - Translation:             self.logger.warning("The server is already running")

- Line 648: `            self.logger.debug("检测到Mac环境，使用特殊启动方式")`
  - Translation:             self.logger.debug("Mac environment detected, using special startup method")

- Line 657: `        # 2. 修正配置项的名称`
  - Translation:         # 2. Correct the configuration item name.

- Line 696: `            self.logger.debug("已发送服务器关闭信号")`
  - Translation:             self.logger.debug("Server shutdown signal has been sent")

- Line 698: `        self.logger.debug("服务器已停止")`
  - Translation:         self.logger.debug("Server has stopped")

- Line 721: `                self.logger.error("智能体未初始化")`
  - Translation:                 self.logger.error("Agent not initialized")

- Line 731: `            self.logger.error(f"API调用失败: {e}")`
  - Translation:             self.logger.error(f"API call failed: {e}")

- Line 761: `                self.logger.error(f"未找到目标智能体: {target_did}")`
  - Translation:                 self.logger.error(f"Target agent not found: {target_did}")

- Line 772: `                self.logger.debug(f"消息已发送到 {target_did}: {message[:50]}...")`
  - Translation:                 self.logger.debug(f"Message sent to {target_did}: {message[:50]}...")

- Line 774: `                self.logger.error(f"消息发送失败到 {target_did}")`
  - Translation:                 self.logger.error(f"Failed to send message to {target_did}")

- Line 778: `            self.logger.error(f"发送消息失败: {e}")`
  - Translation:             self.logger.error(f"Failed to send message: {e}")

- Line 786: `                self.logger.error(f"WebSocket广播失败: {e}")`
  - Translation:                 self.logger.error(f"WebSocket broadcast failed: {e}")

- Line 787: `        self.logger.debug(f"向{len(self.sse_clients)}个SSE客户端广播消息")`
  - Translation:         self.logger.debug(f"Broadcasting message to {len(self.sse_clients)} SSE clients")

- Line 805: `            return {"status": "error", "message": f"未找到智能体: {resp_did}"}`
  - Translation:             return {"status": "error", "message": f"Agent not found: {resp_did}"}

- Line 813: `                self.logger.error(f"API调用错误: {e}")`
  - Translation:                 self.logger.error(f"API call error: {e}")

- Line 816: `            return {"status": "error", "message": f"未找到API: {api_path} [{method}]"}`
  - Translation:             return {"status": "error", "message": f"API not found: {api_path} [{method}]"}

- Line 834: `                logger.debug(f"解析did失败: {did}, 错误: {e}")`
  - Translation:                 logger.debug(f"Failed to parse did: {did}, Error: {e}")


## ./anp_open_sdk/anp_sdk_user_data.py

- Line 19: `ANP用户工具`
  - Translation: ANP User Tool

- Line 21: `这个程序提供了ANP用户管理的基本功能：`
  - Translation: This program provides basic functionality for ANP user management:

- Line 22: `1. 创建新用户 (-n)`
  - Translation: 1. Create a new user (-n)

- Line 23: `2. 列出所有用户 (-l)`
  - Translation: 2. List all users (-l)

- Line 24: `3. 按服务器信息排序显示用户 (-s)`
  - Translation: 3. Sort and display users by server information (-s)

- Line 57: `        logger.debug(f"用户 {name} 创建成功，DID: {did_document['id']}")`
  - Translation:         logger.debug(f"User {name} created successfully, DID: {did_document['id']}")

- Line 60: `        logger.error(f"用户 {name} 创建失败")`
  - Translation:         logger.error(f"Failed to create user {name}")

- Line 65: `        logger.debug("未找到任何用户")`
  - Translation:         logger.debug("No users found")

- Line 107: `    logger.debug(f"找到 {len(users_info)} 个用户，按创建时间从新到旧排序：")`
  - Translation:     logger.debug(f"Found {len(users_info)} users, sorted by creation time from newest to oldest:")

- Line 109: `        logger.debug(f"[{i}] 用户名: {user['name']}")`
  - Translation:         logger.debug(f"[{i}] Username: {user['name']}")

- Line 111: `        logger.debug(f"    类型: {user['type']}")`
  - Translation:         logger.debug(f"    Type: {user['type']}")

- Line 112: `        logger.debug(f"    服务器: {user['host']}:{user['port']}")`
  - Translation:         logger.debug(f"    Server: {user['host']}:{user['port']}")

- Line 113: `        logger.debug(f"    创建时间: {user['created_date']}")`
  - Translation:         logger.debug(f"    Creation Time: {user['created_date']}")

- Line 114: `        logger.debug(f"    目录: {user['dir']}")`
  - Translation:         logger.debug(f"    Directory: {user['dir']}")

- Line 120: `        logger.debug("未找到任何用户")`
  - Translation:         logger.debug("No users found")

- Line 159: `    logger.debug(f"找到 {len(users_info)} 个用户，按服务器信息排序：")`
  - Translation:     logger.debug(f"Found {len(users_info)} users, sorted by server information:")

- Line 161: `        logger.debug(f"[{i}] 服务器: {user['host']}:{user['port']}")`
  - Translation:         logger.debug(f"[{i}] Server: {user['host']}:{user['port']}")

- Line 162: `        logger.debug(f"    用户名: {user['name']}")`
  - Translation:         logger.debug(f"    Username: {user['name']}")

- Line 164: `        logger.debug(f"    类型: {user['type']}")`
  - Translation:         logger.debug(f"    Type: {user['type']}")

- Line 165: `        logger.debug(f"    目录: {user['dir']}")`
  - Translation:         logger.debug(f"    Directory: {user['dir']}")

- Line 169: `    parser = argparse.ArgumentParser(description='ANP用户工具')`
  - Translation:     parser = argparse.ArgumentParser(description='ANP User Tool')

- Line 171: `                        help='创建新用户，需要提供：用户名 主机名 端口号 主机路径 用户类型')`
  - Translation:                         help='Create a new user, requires: username hostname port number host path user type'

- Line 172: `    parser.add_argument('-l', action='store_true', help='显示所有用户信息，按从新到旧创建顺序排序')`
  - Translation:     parser.add_argument('-l', action='store_true', help='Display all user information, sorted by creation order from newest to oldest')

- Line 173: `    parser.add_argument('-s', action='store_true', help='显示所有用户信息，按用户服务器 端口 用户类型排序')`
  - Translation:     parser.add_argument('-s', action='store_true', help='Display all user information, sorted by user server, port, and user type')

- Line 209: `        # 新增：内存中的密钥数据`
  - Translation:         # Addition: Key data in memory

- Line 214: `        """加载密钥数据到内存"""`
  - Translation:         """Load key data into memory"""

- Line 219: `            logger.warning(f"加载内存凭证失败: {e}")`
  - Translation:             logger.warning(f"Failed to load memory credentials: {e}")

- Line 223: `        """获取内存中的DID凭证"""`
  - Translation:         Retrieve DID credentials from memory

- Line 229: `        """获取私钥字节数据"""`
  - Translation:         """Get private key byte data"""

- Line 238: `        """获取公钥字节数据"""`
  - Translation:         """Get public key byte data"""

- Line 323: `            logger.warning(f"用户目录不存在: {self._user_dir}")`
  - Translation:             logger.warning(f"User directory does not exist: {self._user_dir}")

- Line 358: `                    logger.error(f"加载用户数据失败 ({folder_name}): {e}")`
  - Translation:                     logger.error(f"Failed to load user data ({folder_name}): {e}")

- Line 360: `                logger.warning(f"不合格的文件或文件夹: {entry.name},{self._user_dir}")`
  - Translation:                 logger.warning(f"Non-compliant file or folder: {entry.name},{self._user_dir}")

- Line 362: `        logger.debug(f"加载用户数据共 {len(self.users)} 个用户")`
  - Translation:         logger.debug(f"Loaded user data for a total of {len(self.users)} users")

- Line 392: `                logger.debug(f"读取配置文件 {cfg_path} 出错: {e}")`
  - Translation:                 logger.debug(f"Error reading configuration file {cfg_path}: {e}")

- Line 406: `                        logger.debug(f"已加载用户 {user_dir} 的 DID 文档")`
  - Translation:                         logger.debug(f"Loaded DID document for user {user_dir}")

- Line 409: `                logger.error(f"读取DID文档 {did_path} 出错: {e}")`
  - Translation:                 logger.error(f"Error reading DID document {did_path}: {e}")

- Line 411: `    logger.error(f"未找到DID为 {did} 的用户文档")`
  - Translation:     logger.error(f"User document with DID {did} not found")

- Line 426: `        logger.error("缺少必需的参数字段")`
  - Translation:         logger.error("Missing required parameter field")

- Line 463: `        logger.debug(f"用户名 {base_name} 已存在，使用新名称：{new_name}")`
  - Translation:         logger.debug(f"Username {base_name} already exists, using new name: {new_name}")

- Line 488: `                        logger.error(f"DID已存在: {did_id}")`
  - Translation:                         logger.error(f"DID already exists: {did_id}")

- Line 525: `        "owner": {"name": "anpsdk 创造用户", "@id": "https://localhost"},`
  - Translation:         "owner": {"name": "anpsdk creator user", "@id": "https://localhost"},

- Line 526: `        "description": "anpsdk的测试用户",`
  - Translation:         "description": "Test user for anpsdk",

- Line 544: `    logger.debug(f"DID创建成功: {did_document['id']}")`
  - Translation:     logger.debug(f"DID creation successful: {did_document['id']}")

- Line 545: `    logger.debug(f"DID文档已保存到: {userdid_filepath}")`
  - Translation:     logger.debug(f"DID document has been saved to: {userdid_filepath}")

- Line 546: `    logger.debug(f"密钥已保存到: {userdid_filepath}")`
  - Translation:     logger.debug(f"Key has been saved to: {userdid_filepath}")

- Line 547: `    logger.debug(f"用户文件已保存到: {userdid_filepath}")`
  - Translation:     logger.debug(f"User file has been saved to: {userdid_filepath}")

- Line 548: `    logger.debug(f"jwt密钥已保存到: {userdid_filepath}")`
  - Translation:     logger.debug(f"JWT key has been saved to: {userdid_filepath}")

- Line 567: `        logger.error(f"生成 JWT token 失败: {e}")`
  - Translation:         logger.error(f"Failed to generate JWT token: {e}")

- Line 579: `        logger.error(f"验证 JWT token 失败: {e}")`
  - Translation:         logger.error(f"Failed to validate JWT token: {e}")

- Line 599: `    """保存接口配置文件"""`
  - Translation:     """Save interface configuration file"""

- Line 600: `    # 保存智能体描述文件`
  - Translation:     # Save the agent description file

- Line 610: `    logger.debug(f"接口文件{inteface_file_name}已保存在: {template_ad_path}")`
  - Translation:     logger.debug(f"The interface file {inteface_file_name} has been saved at: {template_ad_path}")


## ./anp_open_sdk/contact_manager.py

- Line 3: `        self.user_data = user_data  # BaseUserData 实例`
  - Translation:         self.user_data = user_data  # BaseUserData instance

- Line 10: `        # 加载联系人和 token 信息到缓存`
  - Translation:         # Load contact and token information into cache

- Line 51: `        """撤销与目标DID相关的本地token"""`
  - Translation:         """Revoke local tokens associated with the target DID"""


## ./anp_open_sdk/base_user_data.py

- Line 19: `ANP用户工具`
  - Translation: ANP User Tool

- Line 21: `这个程序提供了ANP用户管理的基本功能：`
  - Translation: This program provides basic functionality for ANP user management:

- Line 22: `1. 创建新用户 (-n)`
  - Translation: 1. Create a new user (-n)

- Line 23: `2. 列出所有用户 (-l)`
  - Translation: 2. List all users (-l)

- Line 24: `3. 按服务器信息排序显示用户 (-s)`
  - Translation: 3. Sort and display users by server information (-s)


## ./anp_open_sdk/config/config_types.py

- Line 1: `"""配置类型定义和协议`
  - Translation: """Configuration type definition and protocol

- Line 3: `此模块提供配置项的类型提示和协议定义，支持IDE代码提示和类型检查。`
  - Translation: This module provides type hints and protocol definitions for configuration items, supporting IDE code suggestions and type checking.

- Line 14: `    """ANP SDK 智能体配置协议"""`
  - Translation:     """ANP SDK Agent Configuration Protocol"""

- Line 20: `    """ANP SDK 配置协议"""`
  - Translation:     """ANP SDK Configuration Protocol"""

- Line 39: `    """ANP SDK 代理配置协议"""`
  - Translation:     ANP SDK Proxy Configuration Protocol

- Line 46: `    """LLM 配置协议"""`
  - Translation:     """LLM Configuration Protocol"""

- Line 54: `    """邮件配置协议"""`
  - Translation:     """Email Configuration Protocol"""

- Line 68: `    """聊天配置协议"""`
  - Translation:     """Chat Configuration Protocol"""

- Line 74: `    """Web API 服务器配置协议"""`
  - Translation:     """Web API Server Configuration Protocol"""

- Line 81: `    """Web API 配置协议"""`
  - Translation:     """Web API Configuration Protocol"""

- Line 86: `    """性能优化配置协议"""`
  - Translation:     """Performance Optimization Configuration Protocol"""

- Line 93: `    """环境变量配置协议"""`
  - Translation:     "Environment Variable Configuration Protocol"

- Line 94: `    # 应用配置`
  - Translation:     # Application Configuration

- Line 99: `    # 系统环境变量`
  - Translation:     # System environment variables

- Line 109: `    # 开发工具`
  - Translation:     # Development Tools

- Line 114: `    # API 密钥`
  - Translation:     # API Key

- Line 118: `    # 邮件密码`
  - Translation:     # Email password

- Line 123: `    # 数据库和服务`
  - Translation:     # Database and services

- Line 127: `    # 其他配置`
  - Translation:     # Other configurations

- Line 137: `    """日志配置协议"""`
  - Translation:     """Log Configuration Protocol"""

- Line 145: `    """敏感信息配置协议"""`
  - Translation:     """Sensitive Information Configuration Protocol"""

- Line 155: `    """统一配置协议"""`
  - Translation:     """Unified Configuration Protocol"""

- Line 156: `    # 主要配置节点`
  - Translation:     # Main configuration node

- Line 166: `    # 环境变量和敏感信息`
  - Translation:     # Environment variables and sensitive information

- Line 170: `    # 方法`
  - Translation:     # Method


## ./anp_open_sdk/config/__init__.py

- Line 15: `"""ANP Open SDK 配置模块`
  - Translation: """ANP Open SDK Configuration Module

- Line 17: `提供统一的配置管理功能，支持：`
  - Translation: Provide unified configuration management capabilities, support:

- Line 18: `- 统一配置管理（unified_config.py）`
  - Translation: - Unified Configuration Management (unified_config.py)

- Line 19: `- 类型提示和协议（config_types.py）`
  - Translation: - Type hints and protocols (config_types.py)

- Line 20: `- 向后兼容的动态配置（dynamic_config.py）`
  - Translation: Backward-compatible dynamic configuration (dynamic_config.py)

- Line 24: `# 导入新的统一配置`
  - Translation: # Import new unified configuration

- Line 31: `# 使用 __all__ 明确声明包的公共接口，这是一个非常好的实践`
  - Translation: # Using __all__ to explicitly declare the public interface of a package is a very good practice.


## ./anp_open_sdk/config/unified_config.py

- Line 15: `"""统一配置管理模块`
  - Translation: Unified Configuration Management Module

- Line 17: `此模块提供统一的配置管理功能，支持：`
  - Translation: This module provides unified configuration management functionality, supporting:

- Line 18: `- YAML配置文件管理`
  - Translation: - YAML Configuration File Management

- Line 19: `- 环境变量映射和类型转换`
  - Translation: - Environment variable mapping and type conversion

- Line 20: `- 路径占位符自动解析`
  - Translation: - Path placeholder auto-resolution

- Line 21: `- 属性访问和代码提示`
  - Translation: - Property access and code hints

- Line 22: `- 敏感信息保护`
  - Translation: - Sensitive Information Protection

- Line 41: `# --- 新增部分 ---`
  - Translation: # --- New Section ---

- Line 43: `# 1. 定义一个模块级的“保管员”，初始时为 None`
  - Translation: # 1. Define a module-level "custodian", initially set to None.

- Line 48: `    【注册函数】由应用入口调用，设置全局唯一的配置实例。`
  - Translation:     【Register Function】Called by the application entry point to set a globally unique configuration instance.

- Line 52: `        # 可以加一个警告，防止被意外覆盖`
  - Translation:         # A warning can be added to prevent accidental overwriting.

- Line 58: `    【解析函数】供库内其他模块调用，获取已设置的全局配置实例。`
  - Translation:     【Parse function】Available for other modules within the library to call, retrieves the already set global configuration instance.

- Line 61: `        # 这是关键的保护措施！`
  - Translation:         # This is a critical safeguard!

- Line 66: `    # 使用 cast 来帮助类型检查器理解 _global_config 符合协议`
  - Translation:     # Use cast to help the type checker understand that _global_config conforms to the protocol.

- Line 119: `        raise AttributeError(f"配置项 '{self._parent_path}.{name}' 不存在")`
  - Translation:         raise AttributeError(f"Configuration item '{self._parent_path}.{name}' does not exist")

- Line 157: `        raise AttributeError(f"环境变量配置项 '{name}' 不存在")`
  - Translation:         raise AttributeError(f"The environment variable configuration item '{name}' does not exist")

- Line 189: `        raise AttributeError(f"敏感配置项 '{name}' 未定义")`
  - Translation:         raise AttributeError(f"Sensitive configuration item '{name}' is undefined")

- Line 201: `    # 1. 添加一个类属性来存储 app_root`
  - Translation:     # 1. Add a class attribute to store app_root

- Line 211: `        # 如果类属性尚未设置，则使用实例的 _app_root 设置它`
  - Translation:         # If the class attribute is not set, use the instance's _app_root to set it.

- Line 216: `                f"新的 UnifiedConfig 实例指定了不同的 app_root。 "`
  - Translation:                 f"The new UnifiedConfig instance specifies a different app_root."

- Line 217: `                f"类方法将继续使用第一个初始化的路径: {UnifiedConfig._app_root_cls}"`
  - Translation:                 f"Class method will continue to use the first initialized path: {UnifiedConfig._app_root_cls}"

- Line 220: `        # 2. 加载 .env 文件`
  - Translation:         # 2. Load the .env file

- Line 224: `            self.logger.info(f"已从 {env_path} 加载环境变量")`
  - Translation:             self.logger.info(f"Environment variables have been loaded from {env_path}")

- Line 226: `        # 3. 解析配置文件路径`
  - Translation:         # 3. Parse configuration file path

- Line 249: `            # 默认配置文件路径基于 app_root`
  - Translation:             # Default configuration file path based on app_root

- Line 276: `            # 现在可以调用类方法`
  - Translation:             # Now the class method can be called

- Line 341: `                        self.logger.info(f"已从 {self._config_file} 加载配置")`
  - Translation:                         self.logger.info(f"Configuration loaded from {self._config_file}")

- Line 345: `                    self.logger.info(f"已创建默认配置文件 {self._config_file}")`
  - Translation:                     self.logger.info(f"Default configuration file {self._config_file} has been created")

- Line 347: `                self.logger.error(f"加载配置出错: {e}")`
  - Translation:                 self.logger.error(f"Error loading configuration: {e}")

- Line 357: `                self.logger.info(f"已保存配置到 {self._config_file}")`
  - Translation:                 self.logger.info(f"Configuration has been saved to {self._config_file}")

- Line 360: `                self.logger.error(f"保存配置出错: {e}")`
  - Translation:                 self.logger.error(f"Error saving configuration: {e}")

- Line 367: `        self.logger.info("配置已重新加载")`
  - Translation:         self.logger.info("Configuration has been reloaded")

- Line 369: `        # 这是从 path_resolver 移入的核心方法`
  - Translation:         # This is the core method moved from path_resolver.

- Line 374: `        解析路径，将{APP_ROOT}替换为实际的应用根目录并返回绝对路径。`
  - Translation:         Parse the path, replace {APP_ROOT} with the actual application root directory, and return the absolute path.

- Line 377: `            path: 包含{APP_ROOT}占位符的路径字符串或Path对象。`
  - Translation:             path: A path string or Path object containing the {APP_ROOT} placeholder.

- Line 380: `            解析后的绝对路径 Path 对象。`
  - Translation:             The parsed absolute path Path object.

- Line 383: `            raise RuntimeError("UnifiedConfig 尚未初始化，无法解析路径。请先创建 UnifiedConfig 实例。")`
  - Translation:             raise RuntimeError("UnifiedConfig has not been initialized, unable to resolve the path. Please create a UnifiedConfig instance first.")

- Line 395: `        """获取已初始化的应用根目录。"""`
  - Translation:         """Get the initialized application root directory."""

- Line 397: `            raise RuntimeError("UnifiedConfig 尚未初始化，无法获取 app_root。请先创建 UnifiedConfig 实例。")`
  - Translation:             raise RuntimeError("UnifiedConfig has not been initialized, unable to retrieve app_root. Please create a UnifiedConfig instance first.")

- Line 433: `            self.logger.error(f"在 PATH 中查找文件 {filename} 时出错: {e}")`
  - Translation:             self.logger.error(f"Error occurred while searching for file {filename} in PATH: {e}")

- Line 464: `            self.logger.error(f"获取路径信息时出错: {e}")`
  - Translation:             self.logger.error(f"Error occurred while retrieving path information: {e}")

- Line 473: `            self.logger.warning(f"默认配置文件 {default_config_path} 不存在。将使用空配置。")`
  - Translation:             self.logger.warning(f"The default configuration file {default_config_path} does not exist. An empty configuration will be used.")


## ./anp_open_sdk/auth/memory_auth_header_builder.py

- Line 4: `内存版本的认证头构建器`
  - Translation: Memory version authentication header builder

- Line 6: `这个模块提供了不依赖文件路径的认证头构建功能，直接使用内存中的密钥数据。`
  - Translation: This module provides authentication header construction functionality that does not rely on file paths, directly using key data in memory.

- Line 22: `    """基于内存数据的WBA认证头构建器"""`
  - Translation:     """WBA authentication header builder based on in-memory data"""

- Line 25: `        """使用内存中的凭证数据构建认证头"""`
  - Translation:         """Construct authentication headers using credential data in memory"""

- Line 27: `            # 获取密钥对`
  - Translation:             # Retrieve key pair

- Line 30: `                raise ValueError("未找到密钥对")`
  - Translation:                 raise ValueError("Key pair not found")

- Line 32: `            # 生成nonce和时间戳`
  - Translation:             # Generate nonce and timestamp

- Line 37: `            # 构建签名载荷`
  - Translation:             # Construct signature payload

- Line 39: `                # 双向认证格式`
  - Translation:                 # Mutual authentication format

- Line 48: `                # 单向认证格式`
  - Translation:                 # Unidirectional authentication format

- Line 58: `            # 使用私钥签名`
  - Translation:             # Use the private key to sign

- Line 61: `            # 构建认证头`
  - Translation:             # Build authentication header

- Line 83: `            logger.error(f"构建认证头失败: {e}")`
  - Translation:             logger.error(f"Failed to construct authentication header: {e}")

- Line 87: `        """使用私钥签名载荷"""`
  - Translation:         """Use the private key to sign the payload"""

- Line 92: `            # 从字节重建私钥对象`
  - Translation:             # Reconstruct the private key object from bytes

- Line 98: `            # 签名`
  - Translation:             # Signature

- Line 104: `            # 转换为base64`
  - Translation:             # Convert to base64

- Line 108: `            logger.error(f"签名失败: {e}")`
  - Translation:             logger.error(f"Signature failed: {e}")

- Line 112: `        """解析认证头（继承自基类的实现）"""`
  - Translation:         """Parse authentication header (implementation inherited from base class)"""

- Line 114: `            # 移除 "DID-WBA " 前缀`
  - Translation:             # Remove the "DID-WBA " prefix

- Line 118: `            # 解析参数`
  - Translation:             # Parse parameters

- Line 128: `            logger.error(f"解析认证头失败: {e}")`
  - Translation:             logger.error(f"Failed to parse authentication header: {e}")

- Line 132: `    """内存认证头包装器，兼容现有的DIDWbaAuthHeader接口"""`
  - Translation:     """Memory authentication header wrapper, compatible with the existing DIDWbaAuthHeader interface"""

- Line 139: `        """生成双向认证头"""`
  - Translation:         """Generate bidirectional authentication header"""

- Line 149: `        """生成单向认证头"""`
  - Translation:         Generate one-way authentication header

- Line 159: `    """创建基于内存数据的认证头客户端"""`
  - Translation:     Create an authentication header client based on in-memory data


## ./anp_open_sdk/auth/did_auth_base.py

- Line 9: `    """DID解析器基类"""`
  - Translation:     """DID Parser Base Class"""

- Line 13: `        """解析DID文档"""`
  - Translation:         """Parse DID document"""

- Line 18: `        """检查是否支持该DID方法"""`
  - Translation:         Check if the DID method is supported

- Line 22: `    """DID签名器基类"""`
  - Translation:     """Base class for DID signer"""

- Line 26: `        """签名载荷"""`
  - Translation:         """Signature Payload"""

- Line 31: `        """验证签名"""`
  - Translation:         Verify signature

- Line 35: `    """认证头构建器基类"""`
  - Translation:     """Base class for authentication header builder"""

- Line 39: `        """构建认证头"""`
  - Translation:         """Build authentication header"""

- Line 44: `        """解析认证头"""`
  - Translation:         Parse authentication header

- Line 49: `    认证基类，包含通用认证相关方法`
  - Translation:     Authentication base class, includes general authentication-related methods.

- Line 54: `        抽象方法：从认证头中提取 req_did 和 target_did（或 resp_did）`
  - Translation:         Abstract method: Extract req_did and target_did (or resp_did) from the authentication header

- Line 59: `    """DID认证器基类"""`
  - Translation:     """DID Authenticator Base Class"""

- Line 69: `        """认证请求"""`
  - Translation:         """Authentication Request"""

- Line 75: `        """验证响应"""`
  - Translation:         """Validate Response"""


## ./anp_open_sdk/auth/auth_client.py

- Line 31: `    """智能体认证管理器"""`
  - Translation:     "Agent Authentication Manager"

- Line 74: `                                message = f"接收方DID认证头验证失败! 状态: {status_code}\n响应: {response_data}"`
  - Translation:                                 message = f"Recipient DID authentication header verification failed! Status: {status_code}\nResponse: {response_data}"

- Line 77: `                            message = f"DID双向认证成功! 已保存 {context.target_did} 颁发的token:{token}"`
  - Translation:                             message = f"DID mutual authentication successful! Token issued by {context.target_did} has been saved: {token}"

- Line 81: `                            message = f"单向认证成功! 已保存 {context.target_did} 颁发的token:{token}"`
  - Translation:                             message = f"Unidirectional authentication successful! Token issued by {context.target_did} has been saved: {token}"

- Line 84: `                        message = "无token，可能是无认证页面或第一代协议"`
  - Translation:                         message = "No token, possibly an unauthenticated page or first-generation protocol"

- Line 87: `                    message = "401错误，认证失败"`
  - Translation:                     message = "401 Error, Authentication Failed"

- Line 98: `                                message = f"接收方DID认证头验证失败! 状态: {status_code}\n响应: {response_data}"`
  - Translation:                                 message = f"Recipient DID authentication header verification failed! Status: {status_code}\nResponse: {response_data}"

- Line 101: `                            message = f"DID双向认证成功! 已保存 {context.target_did} 颁发的token:{token}"`
  - Translation:                             message = f"DID mutual authentication successful! Token issued by {context.target_did} has been saved: {token}"

- Line 105: `                            message = f"单向认证成功! 已保存 {context.target_did} 颁发的token:{token}"`
  - Translation:                             message = f"Unidirectional authentication successful! Token issued by {context.target_did} has been saved: {token}"

- Line 108: `                        message = "无token，可能是无认证页面或第一代协议"`
  - Translation:                         message = "No token, possibly an unauthenticated page or first-generation protocol"

- Line 111: `                    message = "401错误，认证失败"`
  - Translation:                     message = "401 Error, Authentication Failed"

- Line 114: `            logger.error(f"认证过程中发生错误: {e}")`
  - Translation:             logger.error(f"An error occurred during authentication: {e}")

- Line 115: `            return 500, '', f"认证错误: {str(e)}", False`
  - Translation:             return 500, '', f"Authentication error: {str(e)}", False

- Line 127: `    """通用认证函数，自动优先用本地token，否则走DID认证，token失效自动fallback"""`
  - Translation:     """General authentication function, automatically prioritizes using local token, otherwise uses DID authentication, automatically falls back if token is invalid"""

- Line 137: `    暂时屏蔽token分支 token方案需要升级保证安全`
  - Translation:     Temporarily disable the token branch; the token scheme needs upgrading to ensure security.

- Line 156: `                return status, response_data, "token认证请求", status == 200`
  - Translation:                 return status, response_data, "token authentication request", status == 200

- Line 174: `                logger.error(f"HTTP错误 {response.status}: {error_text}")`
  - Translation:                 logger.error(f"HTTP error {response.status}: {error_text}")

- Line 181: `                logger.warning(f"非JSON响应，Content-Type: {content_type}")`
  - Translation:                 logger.warning(f"Non-JSON response, Content-Type: {content_type}")

- Line 184: `            logger.error(f"JSON解析失败: {e}")`
  - Translation:             logger.error(f"JSON parsing failed: {e}")

- Line 186: `            return {"error": "JSON解析失败", "raw_text": text}`
  - Translation:             return {"error": "JSON parsing failed", "raw_text": text}

- Line 188: `            logger.error(f"处理响应时出错: {e}")`
  - Translation:             logger.error(f"Error processing response: {e}")

- Line 191: `        logger.error(f"未知响应类型: {type(response)}")`
  - Translation:         logger.error(f"Unknown response type: {type(response)}")

- Line 192: `        return {"error": f"未知类型: {type(response)}"}`
  - Translation:         return {"error": f"Unknown type: {type(response)}"}

- Line 198: `        #当前方案需要后续改进，当前并不安全`
  - Translation:         #The current solution requires further improvement and is not secure at present.


## ./anp_open_sdk/auth/did_auth_wba.py

- Line 26: `    """WBA DID解析器实现"""`
  - Translation:     """WBA DID parser implementation"""

- Line 29: `        """解析WBA DID文档"""`
  - Translation:         Parse WBA DID document

- Line 31: `            # 先尝试本地解析`
  - Translation:             # First attempt local parsing

- Line 36: `                # 回退到标准解析器`
  - Translation:                 # Fallback to the standard parser

- Line 50: `            logger.error(f"DID解析失败: {e}")`
  - Translation:             logger.error(f"DID resolution failed: {e}")

- Line 55: `        """检查是否支持WBA DID方法"""`
  - Translation:         Check if WBA DID method is supported

- Line 59: `    """WBA DID签名器实现"""`
  - Translation:     WBA DID Signer Implementation

- Line 62: `        """使用Ed25519签名"""`
  - Translation:         Use Ed25519 signature

- Line 70: `        """验证Ed25519签名"""`
  - Translation:         Verify Ed25519 signature

- Line 79: `            logger.error(f"签名验证失败: {e}")`
  - Translation:             logger.error(f"Signature verification failed: {e}")

- Line 91: `            # 优先用 hotpatch 的 DIDWbaAuthHeader`
  - Translation:             # Prefer using the DIDWbaAuthHeader from hotpatch.

- Line 98: `            # 用 agent_connect 的 DIDWbaAuthHeader`
  - Translation:             # Use DIDWbaAuthHeader of agent_connect

- Line 105: `        # 判断是否有 get_auth_header_two_way 方法`
  - Translation:         # Check if there is a get_auth_header_two_way method

- Line 107: `            # 双向认证`
  - Translation:             # Two-way authentication

- Line 112: `            # 单向/降级认证`
  - Translation:             # Unidirectional/Downgrade Authentication

- Line 133: `                logger.error(f"解析认证头失败: {e}")`
  - Translation:                 logger.error(f"Failed to parse authentication header: {e}")

- Line 137: `    """WBA DID认证器实现"""`
  - Translation:     "WBA DID Authenticator Implementation"

- Line 141: `        # 其他初始化（如有）`
  - Translation:         # Other initializations (if any)

- Line 144: `        """执行WBA认证请求"""`
  - Translation:         Execute WBA authentication request

- Line 148: `        """执行WBA认证请求"""`
  - Translation:         Execute WBA authentication request

- Line 150: `            # 构建认证头`
  - Translation:             # Build authentication header

- Line 158: `                # 合并认证头和自定义头，auth_headers 优先覆盖`
  - Translation:                 # Merge authentication headers and custom headers, with auth_headers taking precedence.

- Line 162: `            # 发送带认证头的请求`
  - Translation:             # Send a request with an authentication header

- Line 175: `                                # 检查 Authorization header`
  - Translation:                                 # Check Authorization header

- Line 198: `        """验证WBA响应（借鉴 handle_did_auth 主要认证逻辑）"""`
  - Translation:         """Verify WBA response (referencing the main authentication logic of handle_did_auth)"""

- Line 207: `            # 1. 尝试解析为两路认证`
  - Translation:             # 1. Attempt to parse as two-factor authentication

- Line 215: `                # 回退到标准认证`
  - Translation:                 # Revert to standard authentication

- Line 227: `            # 2. 验证时间戳`
  - Translation:             # 2. Verify timestamp

- Line 246: `                logger.debug(f"nonce通过防重放验证{nonce}")`
  - Translation:                 logger.debug(f"Nonce passed the anti-replay verification {nonce}")

- Line 248: `            # 3. 解析DID文档`
  - Translation:             # 3. Parse DID document

- Line 258: `            # 4. 验证签名`
  - Translation:             # 4. Verify Signature

- Line 287: `        支持两路和标准认证头的 DID 提取`
  - Translation:         Support DID extraction for dual-path and standard authentication headers

- Line 290: `            # 优先尝试两路认证`
  - Translation:             # Priority: Attempt two-way authentication first.

- Line 300: `            # 回退到标准认证`
  - Translation:             # Revert to standard authentication

- Line 314: `    从 did:wba:host%3Aport:xxxx / did:wba:host:port:xxxx / did:wba:host:xxxx`
  - Translation:     From did:wba:host%3Aport:xxxx / did:wba:host:port:xxxx / did:wba:host:xxxx

- Line 315: `    解析 host 和 port`
  - Translation:     Parse host and port

- Line 329: `    """从响应头中获取DIDAUTHHeader`
  - Translation:     """Get DIDAUTHHeader from the response headers"""

- Line 332: `        response_header: 响应头字典`
  - Translation:         response_header: Response header dictionary

- Line 335: `        Tuple[str, str]: (did_auth_header, token) 双向认证头和访问令牌`
  - Translation:         Tuple[str, str]: (did_auth_header, token) Bidirectional authentication header and access token

- Line 341: `                logger.debug("获得单向认证令牌，兼容无双向认证的服务")`
  - Translation:                 logger.debug("Obtained one-way authentication token, compatible with services without mutual authentication")

- Line 351: `                    logger.debug("令牌包含双向认证信息，进行双向校验")`
  - Translation:                     logger.debug("The token contains mutual authentication information, proceeding with mutual verification")

- Line 354: `                    logger.error("[错误] 解析失败，缺少必要字段" + str(auth_value))`
  - Translation:                     logger.error("[Error] Parsing failed, missing required field" + str(auth_value))

- Line 357: `                logger.error("[错误] 处理 Authorization 字典时出错: " + str(e))`
  - Translation:                 logger.error("[Error] An error occurred while processing the Authorization dictionary: " + str(e))

- Line 360: `        logger.debug("response_header不包含'Authorization',无需处理令牌")`
  - Translation:         logger.debug("response_header does not contain 'Authorization', no need to process the token")

- Line 365: `    """检查响应头中的DIDAUTHHeader是否正确`
  - Translation:     """Check if the DIDAUTHHeader in the response header is correct

- Line 368: `        auth_value: 认证头字符串`
  - Translation:         auth_value: Authentication header string

- Line 371: `        bool: 验证是否成功`
  - Translation:         bool: Verify if successful

- Line 376: `        logger.error(f"无法从AuthHeader中解析信息: {e}")`
  - Translation:         logger.error(f"Unable to parse information from AuthHeader: {e}")

- Line 380: `        logger.error("AuthHeader格式错误")`
  - Translation:         logger.error("AuthHeader format error")

- Line 384: `    logger.debug(f"用 {did}的{keyid}检验")`
  - Translation:     logger.debug(f"Verify with {keyid} of {did}")

- Line 390: `    # 尝试使用自定义解析器解析DID文档`
  - Translation:     # Attempt to parse the DID document using a custom parser.

- Line 393: `    # 如果自定义解析器失败，尝试使用标准解析器`
  - Translation:     # If the custom parser fails, try using the standard parser.

- Line 398: `            logger.error(f"标准DID解析器也失败: {e}")`
  - Translation:             logger.error(f"Standard DID resolver also failed: {e}")

- Line 406: `        # 重新构造完整的授权头`
  - Translation:         # Reconstruct the complete authorization header.

- Line 408: `        target_url = "virtual.WBAback" # 迁就现在的url parse代码`
  - Translation:         target_url = "virtual.WBAback" # Accommodate the current url parse code

- Line 410: `        # 调用验证函数`
  - Translation:         # Call the validation function

- Line 417: `        logger.debug(f"签名验证结果: {is_valid}, 消息: {message}")`
  - Translation:         logger.debug(f"Signature verification result: {is_valid}, Message: {message}")

- Line 421: `        logger.error(f"验证签名时出错: {e}")`
  - Translation:         logger.error(f"Error occurred while verifying signature: {e}")


## ./anp_open_sdk/auth/did_auth_wba_custom_did_resolver.py

- Line 16: `自定义DID文档解析器，用于本地测试环境`
  - Translation: Custom DID document parser for local testing environment.

- Line 30: `    解析本地DID文档`
  - Translation:     Parse local DID document

- Line 33: `        did: DID标识符，例如did:wba:localhost%3A8000:wba:user:123456`
  - Translation:         did: DID identifier, for example did:wba:localhost%3A8000:wba:user:123456

- Line 36: `        Optional[Dict]: 解析出的DID文档，如果解析失败则返回None`
  - Translation:         Optional[Dict]: The parsed DID document, returns None if parsing fails.

- Line 39: `        # logger.debug(f"解析本地DID文档: {did}")`
  - Translation:         # logger.debug(f"Parsing local DID document: {did}")

- Line 41: `        # 解析DID标识符`
  - Translation:         # Parse DID identifier

- Line 44: `            logger.debug(f"无效的DID格式: {did}")`
  - Translation:             logger.debug(f"Invalid DID format: {did}")

- Line 47: `        # 提取主机名、端口和用户ID`
  - Translation:         # Extract hostname, port, and user ID

- Line 49: `        # 解码端口部分，如果存在`
  - Translation:         # Decoding port section, if present

- Line 51: `            hostname = unquote(hostname)  # 将 %3A 解码为 :`
  - Translation:             hostname = unquote(hostname)  # Decode %3A to :

- Line 57: `        # logger.debug(f"DID 解析结果 - 主机名: {hostname}, 用户ID: {user_id}")`
  - Translation:         # logger.debug(f"DID parsing result - Hostname: {hostname}, User ID: {user_id}")

- Line 59: `        # 查找本地文件系统中的DID文档`
  - Translation:         # Search for DID documents in the local file system

- Line 64: `            # logger.debug(f"找到本地DID文档: {did_path}")`
  - Translation:             # logger.debug(f"Found local DID document: {did_path}")

- Line 69: `        # 如果本地未找到，尝试通过HTTP请求获取`
  - Translation:         # If not found locally, attempt to retrieve via HTTP request.

- Line 73: `        # 这里使用异步HTTP请求`
  - Translation:         # Using asynchronous HTTP requests here

- Line 78: `                    logger.debug(f"通过DID标识解析的{http_url}获取{did}的DID文档")`
  - Translation:                     logger.debug(f"Obtaining the DID document for {did} via DID identifier resolution of {http_url}")

- Line 81: `                    logger.debug(f"did本地解析器地址{http_url}获取失败，状态码: {response.status}")`
  - Translation:                     logger.debug(f"Failed to obtain the local parser address {http_url}, status code: {response.status}")

- Line 85: `        logger.debug(f"解析DID文档时出错: {e}")`
  - Translation:         logger.debug(f"Error parsing DID document: {e}")


## ./anp_open_sdk/auth/auth_server.py

- Line 34: `# 在模块顶部获取 logger，这是标准做法`
  - Translation: # Get the logger at the top of the module, which is standard practice.

- Line 35: `from ..config.config_types import BaseUnifiedConfigProtocol # 导入协议`
  - Translation: from ..config.config_types import BaseUnifiedConfigProtocol # Import protocol

- Line 81: `        wba_auth = WBAAuth()  # 新增初始化`
  - Translation:         wba_auth = WBAAuth()  # Added initialization

- Line 82: `        return WBADIDAuthenticator(resolver, signer, header_builder, wba_auth)  # 传递 wba_auth`
  - Translation:         return WBADIDAuthenticator(resolver, signer, header_builder, wba_auth)  # Pass wba_auth

- Line 104: `                logger.debug(f"Bearer认证失败: {e}")`
  - Translation:                 logger.debug(f"Bearer authentication failed: {e}")

- Line 122: `                logger.debug(f"服务端认证验证失败: {e}")`
  - Translation:                 logger.debug(f"Server authentication verification failed: {e}")

- Line 131: `            req_did: 请求方DID`
  - Translation:             req_did: Requester DID

- Line 132: `            resp_did: 响应方DID`
  - Translation:             resp_did: Response Party DID

- Line 150: `            # 检查LocalAgent中是否存储了该req_did的token信息`
  - Translation:             # Check whether the token information for req_did is stored in LocalAgent.

- Line 168: `                # 检查token是否被撤销`
  - Translation:                 # Check if the token has been revoked

- Line 173: `                # 检查token是否过期（使用存储的过期时间，而不是token中的时间）`
  - Translation:                 # Check if the token has expired (use the stored expiration time, not the time in the token)

- Line 178: `                # 验证token是否匹配`
  - Translation:                 # Verify if the token matches

- Line 183: `                logger.debug(f" {req_did}提交的token在LocalAgent存储中未过期,快速通过!")`
  - Translation:                 logger.debug(f" The token submitted by {req_did} has not expired in LocalAgent storage, fast pass!")

- Line 185: `                # 如果LocalAgent中没有存储token信息，则使用公钥验证`
  - Translation:                 # If there is no token information stored in LocalAgent, use public key verification.

- Line 207: `                # 可选：进一步校验 req_did、resp_did 的值`
  - Translation:                 # Optional: Further validate the values of req_did and resp_did

- Line 213: `                # 校验 exp 是否过期`
  - Translation:                 # Check if exp has expired

- Line 218: `                logger.debug(f"LocalAgent存储中未找到{req_did}提交的token,公钥验证通过")`
  - Translation:                 logger.debug(f"Token submitted by {req_did} not found in LocalAgent storage, public key verification passed")

- Line 237: `    # 生成访问令牌`
  - Translation:     # Generate access token

- Line 248: `    # logger.debug(f"认证成功，已生成访问令牌")`
  - Translation:     # logger.debug(f"Authentication successful, access token generated")

- Line 249: `    # 如果resp_did存在，加载resp_did的DID文档并组装DID认证头`
  - Translation:     # If resp_did exists, load the DID document of resp_did and assemble the DID authentication header.

- Line 251: `    if resp_did and resp_did != "没收到":`
  - Translation:     if resp_did and resp_did != "Not received":

- Line 253: `            # 获取resp_did用户目录`
  - Translation:             # Get the resp_did user directory

- Line 258: `            # 检查文件是否存在`
  - Translation:             # Check if the file exists

- Line 260: `                # 创建DID认证客户端`
  - Translation:                 # Create DID authentication client

- Line 266: `                # 获取认证头（用于返回给req_did进行验证,此时 req是现在的did）`
  - Translation:                 # Get authentication header (used to return to req_did for verification, at this point req is the current did)

- Line 267: `                target_url = "http://virtual.WBAback:9999"  # 使用当前请求的域名`
  - Translation:                 target_url = "http://virtual.WBAback:9999"  # Use the domain name of the current request

- Line 270: `                # 打印认证头`
  - Translation:                 # Print authentication header

- Line 273: `            # logger.debug(f"成功加载resp_did的DID文档并生成认证头")`
  - Translation:             # logger.debug(f"Successfully loaded the DID document of resp_did and generated the authentication header")

- Line 275: `                logger.warning(f"resp_did的DID文档或私钥不存在: {did_document_path} or {private_key_path}")`
  - Translation:                 logger.warning(f"The DID document or private key for resp_did does not exist: {did_document_path} or {private_key_path}")

- Line 277: `            logger.debug(f"加载resp_did的DID文档时出错: {e}")`
  - Translation:             logger.debug(f"Error loading the DID document for resp_did: {e}")

- Line 327: `        logger.debug(f"安全中间件拦截/wba/auth进行认证")`
  - Translation:         logger.debug(f"Security middleware intercepts /wba/auth for authentication")

- Line 330: `            raise HTTPException(status_code=401, detail=f"认证失败: {msg}")`
  - Translation:             raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}")

- Line 340: `    logger.debug(f"安全中间件拦截检查url:\n{request.url}")`
  - Translation:     logger.debug(f"Security middleware intercepts and checks URL:\n{request.url}")

- Line 343: `        raise HTTPException(status_code=401, detail=f"认证失败: {msg}")`
  - Translation:         raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}")


## ./anp_open_sdk/auth/schemas.py

- Line 11: `    """DID密钥对内存对象 (支持 secp256k1)"""`
  - Translation:     """DID key pair memory object (supports secp256k1)"""

- Line 12: `    private_key: bytes = Field(..., description="私钥字节")`
  - Translation:     private_key: bytes = Field(..., description="Private key bytes")

- Line 13: `    public_key: bytes = Field(..., description="公钥字节")`
  - Translation:     public_key: bytes = Field(..., description="Public key bytes")

- Line 14: `    key_id: str = Field(..., description="密钥ID")`
  - Translation:     key_id: str = Field(..., description="Key ID")

- Line 15: `    """DID密钥对内存对象"""`
  - Translation:     DID key pair memory object

- Line 21: `        """从 secp256k1 私钥字节创建密钥对"""`
  - Translation:         """Create a key pair from secp256k1 private key bytes"""

- Line 38: `        """从PEM/PKCS8 secp256k1私钥文件创建密钥对"""`
  - Translation:         """Create a key pair from a PEM/PKCS8 secp256k1 private key file"""

- Line 61: `    """DID文档内存对象"""`
  - Translation:     """DID Document Memory Object"""

- Line 62: `    did: str = Field(..., description="DID标识符")`
  - Translation:     did: str = Field(..., description="DID identifier")

- Line 70: `        """从文件路径加载（向后兼容）"""`
  - Translation:         """Load from file path (backward compatibility)"""

- Line 84: `        """获取指定的验证方法"""`
  - Translation:         """Get the specified validation method"""

- Line 91: `    """DID凭证集合"""`
  - Translation:     """DID Credential Set"""

- Line 96: `        """获取指定的密钥对"""`
  - Translation:         """Get the specified key pair"""

- Line 100: `        """添加密钥对"""`
  - Translation:         Add key pair

- Line 105: `        """从文件路径创建（向后兼容）"""`
  - Translation:         """Create from file path (backward compatible)"""

- Line 115: `        """从内存数据创建DID凭证"""`
  - Translation:         """Create DID credentials from memory data"""

- Line 116: `        # 创建DID文档对象`
  - Translation:         # Create DID document object

- Line 125: `        # 创建密钥对对象`
  - Translation:         # Create a key pair object

- Line 128: `        # 创建凭证对象`
  - Translation:         # Create credential object

- Line 135: `        """从用户数据对象创建DID凭证"""`
  - Translation:         """Create a DID credential from the user data object"""

- Line 136: `        # 读取私钥文件内容到内存`
  - Translation:         # Read the private key file content into memory

- Line 140: `        # 解析私钥`
  - Translation:         # Parse private key

- Line 145: `        # 获取私钥字节`
  - Translation:         # Get private key bytes

- Line 147: `            # EC私钥（secp256k1等）`
  - Translation:             # EC private key (such as secp256k1)

- Line 150: `            # 其他类型私钥的处理 - 先尝试序列化为DER格式`
  - Translation:             # Handling of other types of private keys - first attempt to serialize to DER format

- Line 158: `                # 如果失败，尝试PEM格式`
  - Translation:                 # If it fails, try PEM format.

- Line 165: `        # 获取key_id`
  - Translation:         # Retrieve key_id

- Line 173: `    """认证上下文"""`
  - Translation:     "Authentication Context"

- Line 183: `    domain: Optional[str] = None  # 新增 domain 字段`
  - Translation:     domain: Optional[str] = None  # Add a new domain field


## ./anp_open_sdk/auth/vc_helper.py

- Line 16: `验证凭证(VC)辅助模块`
  - Translation: Verification Credential (VC) Auxiliary Module

- Line 18: `提供创建和验证DID验证凭证(Verifiable Credential)的功能`
  - Translation: Provides functionality for creating and verifying DID Verifiable Credentials (Verifiable Credential).

- Line 32: `import jcs  # 用于规范化JSON`
  - Translation: import jcs  # Used for normalizing JSON

- Line 38: `    """加载私钥"""`
  - Translation:     Load private key

- Line 44: `        logger.error(f"加载私钥时出错: {str(e)}")`
  - Translation:         logger.error(f"Error loading private key: {str(e)}")

- Line 55: `    创建验证凭证(VC)`
  - Translation:     Create a Verifiable Credential (VC)

- Line 58: `        did_document: DID文档`
  - Translation:         did_document: DID Document

- Line 59: `        private_key_path: 私钥路径`
  - Translation:         private_key_path: Private key path

- Line 60: `        nonce: 服务器提供的nonce`
  - Translation:         nonce: nonce provided by the server

- Line 61: `        expires_in: 凭证有效期（秒）`
  - Translation:         expires_in: Token validity period (seconds)

- Line 64: `        Dict: 验证凭证，如果创建失败则返回None`
  - Translation:         Dict: Verify credentials, return None if creation fails

- Line 67: `        # 获取DID ID和验证方法`
  - Translation:         # Get DID ID and verification method

- Line 70: `            logger.error("DID文档中缺少id字段")`
  - Translation:             logger.error("Missing id field in DID document")

- Line 75: `            logger.error("DID文档中缺少verificationMethod字段")`
  - Translation:             logger.error("Missing verificationMethod field in DID document")

- Line 78: `        # 使用第一个验证方法`
  - Translation:         # Use the first validation method

- Line 81: `        # 创建凭证`
  - Translation:         # Create credential

- Line 101: `        # 加载私钥`
  - Translation:         # Load private key

- Line 106: `        # 准备签名数据`
  - Translation:         # Prepare signature data

- Line 110: `        # 计算签名`
  - Translation:         # Calculate signature

- Line 117: `            # 将签名编码为Base64`
  - Translation:             # Encode the signature in Base64

- Line 120: `            # 添加签名到凭证`
  - Translation:             # Add signature to credentials

- Line 131: `            logger.error("不支持的私钥类型")`
  - Translation:             logger.error("Unsupported private key type")

- Line 134: `        logger.error(f"创建验证凭证时出错: {str(e)}")`
  - Translation:         logger.error(f"Error occurred while creating verification credentials: {str(e)}")

- Line 144: `    验证验证凭证(VC)`
  - Translation:     Verify Verification Credential (VC)

- Line 147: `        credential: 验证凭证`
  - Translation:         credential: Verification credential

- Line 148: `        did_document: DID文档`
  - Translation:         did_document: DID Document

- Line 149: `        expected_nonce: 预期的nonce，如果提供则验证nonce是否匹配`
  - Translation:         expected_nonce: Expected nonce, if provided, verify whether the nonce matches

- Line 152: `        bool: 验证是否通过`
  - Translation:         bool: Verification Passed

- Line 155: `        # 验证基本字段`
  - Translation:         # Validate basic fields

- Line 157: `            logger.error("验证凭证缺少必要字段")`
  - Translation:             logger.error("The credential verification is missing necessary fields")

- Line 160: `        # 验证过期时间`
  - Translation:         # Verify expiration time

- Line 164: `                logger.error("验证凭证已过期")`
  - Translation:                 logger.error("The verification credential has expired")

- Line 167: `        # 验证nonce`
  - Translation:         # Verify nonce

- Line 171: `                logger.error(f"Nonce不匹配: 预期 {expected_nonce}, 实际 {credential_nonce}")`
  - Translation:                 logger.error(f"Nonce mismatch: expected {expected_nonce}, actual {credential_nonce}")

- Line 174: `        # 验证签名`
  - Translation:         # Verify Signature

- Line 175: `        # 注意：这里简化了签名验证过程，实际应用中应该使用专门的VC库`
  - Translation:         # Note: The signature verification process is simplified here; a specialized VC library should be used in actual applications.

- Line 176: `        # 例如，可以使用DID解析器获取公钥，然后验证签名`
  - Translation:         # For example, you can use a DID resolver to obtain the public key and then verify the signature.

- Line 178: `        # 这里假设验证通过`
  - Translation:         # Assume validation is successful here.

- Line 181: `        logger.error(f"验证凭证时出错: {str(e)}")`
  - Translation:         logger.error(f"Error verifying credentials: {str(e)}")


## ./anp_open_sdk/auth/token_nonce_auth.py

- Line 35: `        private_key_path: 私钥路径`
  - Translation:         private_key_path: Private key path

- Line 121: `        logger.debug(f"读取到Token签名密钥文件{key_path}，准备签发Token")`
  - Translation:         logger.debug(f"Token signature key file {key_path} read, preparing to issue Token")


## ./anp_open_sdk/agent_connect_hotpatch/authentication/did_wba_auth_header.py

- Line 110: `            # 根据请求，对特定的 user_hosted_agent 路径只记录 info`
  - Translation:             # According to the request, only log info for the specific user_hosted_agent path.

- Line 124: `            # 失败原因已在 _load_private_key 中记录`
  - Translation:             # The reason for failure has been logged in _load_private_key.

- Line 143: `            # logger.debug("尝试添加DID认证头自")`
  - Translation:             # logger.debug("Attempting to add DID authentication header")

- Line 166: `        获取认证头。`
  - Translation:         Get authentication header.

- Line 167: `        支持 server_url 为 FastAPI/Starlette Request 对象或字符串。`
  - Translation:         Support server_url as a FastAPI/Starlette Request object or string.

- Line 183: `                # 生成失败，确保不会使用过期的头`
  - Translation:                 # Generation failed, ensure that expired headers are not used.

- Line 209: `            logger.debug(f"响应头中没有 Authorization 字段，跳过 token 更新。URL: {server_url}")`
  - Translation:             logger.debug(f"No Authorization field in response headers, skipping token update. URL: {server_url}")

- Line 213: `            token_value = auth_data[7:]  # 移除 "Bearer " 前缀`
  - Translation:             token_value = auth_data[7:]  # Remove the "Bearer " prefix

- Line 214: `            logger.debug(f"解析到bearer token: {token_value}")`
  - Translation:             logger.debug(f"Parsed bearer token: {token_value}")


## ./anp_open_sdk/agent_connect_hotpatch/authentication/did_wba.py

- Line 306: `    logger.debug(f"[签名] canonical_json:{canonical_json}")`
  - Translation:     logger.debug(f"[Signature] canonical_json:{canonical_json}")

- Line 308: `    logger.debug(f"[签名] content_hash:{content_hash.hex()} ")`
  - Translation:     logger.debug(f"[Signature] content_hash:{content_hash.hex()} ")

- Line 326: `    logger.debug(f"生成认证头: 提交方 {did} -> 认证方 {resp_did}")`
  - Translation:     logger.debug(f"Generate authentication header: Submitter {did} -> Authenticator {resp_did}")

- Line 327: `    #logger.debug(f"生成认证头: {auth_header}")`
  - Translation:     #logger.debug(f"Generate authentication header: {auth_header}")

- Line 666: `        logger.debug(f"[验签] canonical_json:{canonical_json}")`
  - Translation:         logger.debug(f"[Signature Verification] canonical_json:{canonical_json}")

- Line 667: `        logger.debug(f"[验签] content_hash:{content_hash.hex()}")`
  - Translation:         logger.debug(f"[Signature Verification] content_hash:{content_hash.hex()}")


## ./anp_open_sdk/utils/log_base.py

- Line 22: `# 从我们的类型定义中导入协议`
  - Translation: # Import protocol from our type definitions

- Line 28: `    """用于在控制台输出彩色日志的格式化器。"""`
  - Translation:     """Formatter for outputting colored logs in the console."""

- Line 40: `        # 使用 get 方法并提供默认值，稍微更健壮`
  - Translation:         # Use the get method and provide a default value for slightly more robustness.

- Line 46: `# 一个防止重复配置的全局标志`
  - Translation: # A global flag to prevent duplicate configuration

- Line 52: `    根据传入的配置对象来设置根日志记录器。`
  - Translation:     Set the root logger according to the passed configuration object.

- Line 54: `    这个函数应该在应用启动时被调用一次。`
  - Translation:     This function should be called once when the application starts.

- Line 57: `        config: 一个符合 UnifiedConfigProtocol 协议的完整配置对象。`
  - Translation:         config: A complete configuration object conforming to the UnifiedConfigProtocol protocol.

- Line 65: `    # 从配置中安全地获取日志设置`
  - Translation:     # Safely retrieve log settings from the configuration.

- Line 68: `    # 默认值`
  - Translation:     # Default value

- Line 79: `    # 将字符串级别转换为 logging 的整数级别`
  - Translation:     # Convert the string level to the integer level for logging

- Line 82: `    # 获取根日志记录器`
  - Translation:     # Get the root logger

- Line 86: `    # 清理已存在的 handlers，避免重复打印`
  - Translation:     # Clear existing handlers to avoid duplicate logging.

- Line 90: `    # --- 配置控制台 Handler ---`
  - Translation:     # --- Configure Console Handler ---

- Line 98: `    # --- 配置可选的文件 Handler ---`
  - Translation:     # --- Configure optional file Handler ---

- Line 101: `            # 使用 config 对象的方法来解析路径，这是最健壮的方式`
  - Translation:             # Use the methods of the config object to parse the path; this is the most robust approach.

- Line 104: `            # 确保目录存在，不再使用 sudo`
  - Translation:             # Ensure the directory exists, no longer use sudo

- Line 118: `            root_logger.info(f"日志将记录到文件: {log_file_path}")`
  - Translation:             root_logger.info(f"Logs will be recorded to the file: {log_file_path}")

- Line 120: `            root_logger.error(f"设置文件日志记录器失败 ({log_file}): {e}")`
  - Translation:             root_logger.error(f"Failed to set up file logger ({log_file}): {e}")

- Line 123: `    root_logger.info(f"日志系统配置完成，级别: {log_level_str}。")`
  - Translation:     root_logger.info(f"Log system configuration completed, level: {log_level_str}.")


## ./anp_open_sdk/service/publisher/anp_sdk_publisher_mail_backend.py

- Line 30: `    """邮件后端抽象基类"""`
  - Translation:     """Abstract Base Class for Email Backend"""

- Line 34: `        """发送邮件"""`
  - Translation:         """Send Email"""

- Line 39: `        """获取未读邮件"""`
  - Translation:         """Get unread emails"""

- Line 44: `        """标记邮件为已读"""`
  - Translation:         email as read

- Line 49: `    """本地文件邮件后端，用于测试"""`
  - Translation:     """Local file email backend for testing"""

- Line 55: `        # 创建子目录`
  - Translation:         # Create subdirectory

- Line 61: `        """发送邮件到本地文件"""`
  - Translation:         """Send email to local file"""

- Line 76: `            # 保存到发件箱`
  - Translation:             # Save to Outbox

- Line 81: `            # 同时保存到收件箱`
  - Translation:             # Also save to the inbox

- Line 86: `            logger.debug(f"本地邮件已发送: {subject} -> {to_address}")`
  - Translation:             logger.debug(f"Local email sent: {subject} -> {to_address}")

- Line 90: `            logger.error(f"发送本地邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to send local email: {e}")

- Line 94: `        """获取未读邮件"""`
  - Translation:         """Retrieve unread emails"""

- Line 109: `                    logger.warning(f"读取邮件文件失败 {email_file}: {e}")`
  - Translation:                     logger.warning(f"Failed to read email file {email_file}: {e}")

- Line 114: `            logger.error(f"获取未读邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to retrieve unread emails: {e}")

- Line 118: `        """标记邮件为已读"""`
  - Translation:         Mark email as read

- Line 131: `                        # 移动到已读目录`
  - Translation:                         # Move to the read directory

- Line 136: `                        # 删除原文件`
  - Translation:                         # Delete the original file

- Line 139: `                        logger.debug(f"邮件已标记为已读: {message_id}")`
  - Translation:                         logger.debug(f"Email marked as read: {message_id}")

- Line 143: `                    logger.warning(f"处理邮件文件失败 {email_file}: {e}")`
  - Translation:                     logger.warning(f"Failed to process email file {email_file}: {e}")

- Line 148: `            logger.error(f"标记邮件为已读失败: {e}")`
  - Translation:             logger.error(f"Failed to mark email as read: {e}")

- Line 152: `        """模拟托管DID响应邮件"""`
  - Translation:         """Simulate hosting DID response email"""

- Line 153: `        response_content = f"""托管DID申请已批准`
  - Translation:         response_content = f"""Hosted DID application has been approved.

- Line 155: `主机: {host}`
  - Translation: Host: {host}

- Line 156: `端口: {port}`
  - Translation: Port: {port}

- Line 157: `父DID: {parent_did}`
  - Translation: Parent DID: {parent_did}

- Line 159: `请使用以下信息配置您的托管DID。"""`
  - Translation: Please use the following information to configure your hosted DID.

- Line 170: `    """Gmail邮件后端"""`
  - Translation:     """Gmail Mail Backend"""

- Line 173: `        # 优先从 dynamic_config 获取配置，回退到环境变量`
  - Translation:         # Prefer to obtain configuration from dynamic_config, fallback to environment variables.

- Line 183: `            raise ValueError('请在环境变量中配置邮箱用户名和密码')`
  - Translation:             raise ValueError('Please configure the email username and password in the environment variables')

- Line 185: `        # 配置SOCKS代理（如果需要）`
  - Translation:         # Configure SOCKS proxy (if needed)

- Line 195: `        """连接到IMAP服务器"""`
  - Translation:         "Connect to IMAP server"

- Line 201: `        """发送邮件"""`
  - Translation:         Email

- Line 213: `            logger.debug(f"邮件已发送: {subject} -> {to_address}")`
  - Translation:             logger.debug(f"Email sent: {subject} -> {to_address}")

- Line 217: `            logger.error(f"发送邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to send email: {e}")

- Line 221: `        """获取未读邮件"""`
  - Translation:         Retrieve unread emails

- Line 226: `            # 构建搜索条件`
  - Translation:             # Build search criteria

- Line 246: `                        # 解析邮件内容`
  - Translation:                         # Parse email content

- Line 267: `                    logger.warning(f"解析邮件失败 {num}: {e}")`
  - Translation:                     logger.warning(f"Failed to parse email {num}: {e}")

- Line 273: `            logger.error(f"获取未读邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to retrieve unread emails: {e}")

- Line 277: `        """标记邮件为已读"""`
  - Translation:         Mark email as read

- Line 286: `            logger.error(f"标记邮件为已读失败: {e}")`
  - Translation:             logger.error(f"Failed to mark email as read: {e}")

- Line 291: `    """增强的邮件管理器"""`
  - Translation:     Enhanced Mail Manager

- Line 295: `        初始化邮件管理器`
  - Translation:         Initialize the email manager

- Line 298: `            use_local_backend: 是否使用本地文件后端（用于测试）`
  - Translation:             use_local_backend: Whether to use the local file backend (for testing)

- Line 299: `            local_mail_dir: 本地邮件存储目录`
  - Translation:             local_mail_dir: Local mail storage directory

- Line 301: `        logger.debug(f"使用本地文件邮件后端参数设置:{use_local_backend}")`
  - Translation:         logger.debug(f"Using local file mail backend parameter settings: {use_local_backend}")

- Line 308: `            logger.debug("使用本地文件邮件后端")`
  - Translation:             logger.debug("Using local file email backend")

- Line 312: `            logger.debug("使用Gmail邮件后端")`
  - Translation:             logger.debug("Using Gmail email backend")

- Line 315: `        """发送邮件"""`
  - Translation:         """Send Email"""

- Line 319: `        """发送回复邮件（兼容旧接口）"""`
  - Translation:         """Send reply email (compatible with old interface)"""

- Line 323: `        """获取未读的DID请求邮件"""`
  - Translation:         Retrieve unread DID request emails

- Line 327: `        """获取未读的托管DID响应邮件"""`
  - Translation:         Retrieve unread managed DID response emails

- Line 331: `        """标记邮件为已读"""`
  - Translation:         Mark email as read

- Line 335: `        """发送托管DID申请邮件"""`
  - Translation:         """Send hosted DID application email"""

- Line 344: `            logger.debug(f"发送托管DID申请邮件: {to_address}")`
  - Translation:             logger.debug(f"Sending hosted DID application email: {to_address}")

- Line 353: `            logger.error(f"发送托管DID申请邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to send hosted DID application email: {e}")

- Line 357: `        """模拟托管DID响应（仅本地后端支持）"""`
  - Translation:         """Simulate hosted DID response (supported by local backend only)"""

- Line 361: `            logger.warning("模拟托管DID响应仅在本地后端支持")`
  - Translation:             logger.warning("Simulated hosted DID response is only supported on the local backend")

- Line 365: `# 兼容性函数，保持向后兼容`
  - Translation: # Compatibility function, maintain backward compatibility

- Line 367: `    """原MailManager类的兼容性包装"""`
  - Translation:     """Compatibility wrapper for the original MailManager class"""

- Line 370: `        # 检查是否设置了测试模式`
  - Translation:         # Check if test mode is enabled

- Line 377: `# 测试工具函数`
  - Translation: # Test utility function

- Line 379: `    """创建测试用的邮件管理器"""`
  - Translation:     Create a mail manager for testing

- Line 384: `    """设置测试环境"""`
  - Translation:     """Set up the test environment"""

- Line 388: `    # 创建一些测试邮件`
  - Translation:     # Create some test emails

- Line 391: `        subject="测试邮件",`
  - Translation:         subject="Test Email",

- Line 392: `        content="这是一封测试邮件",`
  - Translation:         content = "This is a test email",

- Line 396: `    logger.debug(f"测试环境已设置，邮件存储路径: {mail_storage_path}")`
  - Translation:     logger.debug(f"Test environment set, mail storage path: {mail_storage_path}")

- Line 401: `    # 测试代码`
  - Translation:     # Test code

- Line 402: `    logger.debug("测试邮件管理器...")`
  - Translation:     logger.debug("Testing mail manager...")

- Line 404: `    # 创建测试环境`
  - Translation:     # Create a test environment

- Line 407: `    # 测试发送邮件`
  - Translation:     # Test sending email

- Line 414: `    # 测试获取未读邮件`
  - Translation:     # Test for retrieving unread emails

- Line 416: `    logger.debug(f"未读DID请求: {len(unread)}")`
  - Translation:     logger.debug(f"Unread DID requests: {len(unread)}")

- Line 418: `    # 测试模拟响应`
  - Translation:     # Test simulated response

- Line 425: `    # 测试获取响应邮件`
  - Translation:     # Test to retrieve response email

- Line 427: `    logger.debug(f"未读响应: {len(responses)}")`
  - Translation:     logger.debug(f"Unread responses: {len(responses)}")

- Line 429: `    logger.debug(f"测试完成，邮件存储在: {storage_path}")`
  - Translation:     logger.debug(f"Test completed, email stored at: {storage_path}")


## ./anp_open_sdk/service/publisher/anp_sdk_publisher.py

- Line 9: `    """DID管理器，用于处理DID文档的存储和管理"""`
  - Translation:     """DID Manager, used for handling the storage and management of DID documents"""

- Line 13: `        初始化DID管理器`
  - Translation:         Initialize DID manager

- Line 16: `            hosted_dir: DID托管目录路径，如果为None则使用默认路径`
  - Translation:             hosted_dir: DID hosting directory path, use default path if None

- Line 21: `        # 获取主机配置`
  - Translation:         # Get host configuration

- Line 29: `        检查DID是否已存在`
  - Translation:         Check if DID already exists

- Line 32: `            did_document: DID文档`
  - Translation:             did_document: DID Document

- Line 35: `            bool: 是否存在重复的DID`
  - Translation:             bool: Is there a duplicate DID?

- Line 38: `            if isinstance(did_document, str):  # 可能是 JSON 字符串`
  - Translation:             if isinstance(did_document, str):  # It might be a JSON string

- Line 40: `                    did_document = json.loads(did_document)  # 解析 JSON`
  - Translation:                     did_document = json.loads(did_document)  # Parse JSON

- Line 42: `                    return None  # 解析失败，返回 None`
  - Translation:                     return None  # Parsing failed, return None

- Line 43: `            if isinstance(did_document, dict):  # 确保是字典`
  - Translation:             if isinstance(did_document, dict):  # Ensure it is a dictionary

- Line 44: `                return did_document.get('id')  # 取值`
  - Translation:                 return did_document.get('id')  # Get value

- Line 59: `                logger.error(f"读取DID文档失败: {e}")`
  - Translation:                 logger.error(f"Failed to read DID document: {e}")

- Line 64: `        存储DID文档`
  - Translation:         Store DID document

- Line 67: `            did_document: DID文档`
  - Translation:             did_document: DID Document

- Line 70: `            tuple: (是否成功, 新的DID ID, 错误信息)`
  - Translation:             tuple: (Success, New DID ID, Error Message)

- Line 73: `            # 生成新的sid`
  - Translation:             # Generate a new SID

- Line 78: `            # 保存原始请求`
  - Translation:             # Save the original request

- Line 83: `            # 修改DID文档`
  - Translation:             # Modify DID document

- Line 86: `            # 保存修改后的文档`
  - Translation:             # Save the modified document

- Line 94: `            error_msg = f"存储DID文档失败: {e}"`
  - Translation:             error_msg = f"Failed to store DID document: {e}"

- Line 100: `        修改DID文档，更新主机信息和ID`
  - Translation:         Modify the DID document to update host information and ID.

- Line 103: `            did_document: 原始DID文档`
  - Translation:             did_document: Original DID Document

- Line 104: `            sid: 新的会话ID`
  - Translation:             sid: New session ID

- Line 107: `            dict: 修改后的DID文档`
  - Translation:             dict: Modified DID document

- Line 113: `            # 更新主机和端口部分`
  - Translation:             # Update host and port section

- Line 115: `            # 将user替换为hostuser`
  - Translation:             # Replace user with hostuser

- Line 123: `            # 更新相关字段`
  - Translation:             # Update relevant fields

- Line 125: `                #递归遍历整个 DID 文档，替换所有出现的 old_id`
  - Translation:                 #Recursively traverse the entire DID document and replace all occurrences of old_id.

- Line 126: `                if isinstance(did_document, dict):  # 处理字典`
  - Translation:                 if isinstance(did_document, dict):  # Handle dictionary

- Line 131: `                elif isinstance(did_document, list):  # 处理列表`
  - Translation:                 elif isinstance(did_document, list):  # Handle list

- Line 133: `                elif isinstance(did_document, str):  # 处理字符串`
  - Translation:                 elif isinstance(did_document, str):  # Handle string

- Line 136: `                    return did_document  # 其他类型不变`
  - Translation:                     return did_document  # Other types remain unchanged

- Line 137: `            # 全局替换所有 `old_id``
  - Translation:             # Globally replace all `old_id`.


## ./anp_open_sdk/service/publisher/anp_sdk_publisher_mail_mgr.py

- Line 12: `    """邮箱管理器，用于处理DID托管请求的邮件操作"""`
  - Translation:     """Email manager for handling email operations related to DID hosting requests"""

- Line 19: `            raise ValueError('请在环境变量中配置 HOSTER_MAIL_USER/HOSTER_MAIL_PASSWORD')`
  - Translation:             raise ValueError('Please configure HOSTER_MAIL_USER/HOSTER_MAIL_PASSWORD in the environment variables')

- Line 21: `        # 设置 SOCKS5 代理`
  - Translation:         # Set SOCKS5 proxy

- Line 26: `        """连接到IMAP服务器"""`
  - Translation:         "Connect to IMAP server"

- Line 32: `        """发送回复邮件"""`
  - Translation:         Send reply email

- Line 45: `            logger.error(f"发送回复邮件失败: {e}")`
  - Translation:             logger.error(f"Failed to send reply email: {e}")

- Line 49: `        """获取未读的DID托管请求邮件"""`
  - Translation:         Retrieve unread DID hosting request emails

- Line 70: `            # 解析邮件正文`
  - Translation:             # Parse email body

- Line 92: `                logger.error(f"解析DID文档失败: {e}")`
  - Translation:                 logger.error(f"Failed to parse DID document: {e}")

- Line 98: `        """将邮件标记为已读"""`
  - Translation:         Mark the email as read

- Line 106: `            logger.error(f"标记邮件为已读失败: {e}")`
  - Translation:             logger.error(f"Failed to mark email as read: {e}")


## ./anp_open_sdk/service/interaction/agent_api_call.py

- Line 35: `        """通用方式调用智能体的 API (支持 GET/POST)"""`
  - Translation:         """General method for calling the agent's API (supports GET/POST)"""


## ./anp_open_sdk/service/interaction/agent_message_p2p.py

- Line 24: `    """发送消息给目标智能体"""`
  - Translation:     """Send a message to the target agent"""


## ./anp_open_sdk/service/interaction/anp_tool.py

- Line 23: `    description: str = """使用代理网络协议（ANP）与其他智能体进行交互。`
  - Translation:     description: str = """Interact with other agents using the Agent Network Protocol (ANP).

- Line 24: `1. 使用时需要输入文档 URL 和 HTTP 方法。`
  - Translation: 1. When using, you need to input the document URL and HTTP method.

- Line 25: `2. 在工具内部，URL 将被解析，并根据解析结果调用相应的 API。`
  - Translation: 2. Within the tool, the URL will be parsed, and the corresponding API will be called based on the parsing result.

- Line 26: `3. 注意：任何使用 ANPTool 获取的 URL 都必须使用 ANPTool 调用，不要直接调用。`
  - Translation: 3. Note: Any URL obtained using ANPTool must be called using ANPTool, do not call directly.

- Line 33: `                "description": "(必填) 代理描述文件或 API 端点的 URL",`
  - Translation:                 "description": "(Required) URL of the proxy description file or API endpoint",

- Line 37: `                "description": "(可选) HTTP 方法，如 GET、POST、PUT 等，默认为 GET",`
  - Translation:                 "description": "(Optional) HTTP method, such as GET, POST, PUT, etc., defaults to GET",

- Line 43: `                "description": "(可选) HTTP 请求头",`
  - Translation:                 "description": "(Optional) HTTP request header",

- Line 48: `                "description": "(可选) URL 查询参数",`
  - Translation:                 "description": "(Optional) URL query parameter",

- Line 53: `                "description": "(可选) POST/PUT 请求的请求体",`
  - Translation:                 "description": "(Optional) Request body for POST/PUT requests",

- Line 59: `    # 声明 auth_client 字段`
  - Translation:     # Declare the auth_client field

- Line 69: `        使用 DID 认证初始化 ANPTool`
  - Translation:         Initialize ANPTool using DID authentication

- Line 71: `        参数:`
  - Translation:         Parameters:

- Line 72: `            did_document_path (str, 可选): DID 文档文件路径。如果为 None，则使用默认路径。`
  - Translation:             did_document_path (str, optional): Path to the DID document file. If None, the default path is used.

- Line 73: `            private_key_path (str, 可选): 私钥文件路径。如果为 None，则使用默认路径。`
  - Translation:             private_key_path (str, optional): Path to the private key file. If None, the default path is used.

- Line 77: `        # 获取当前脚本目录`
  - Translation:         # Get the current script directory

- Line 79: `        # 获取项目根目录`
  - Translation:         # Get the project root directory

- Line 82: `        # 使用提供的路径或默认路径`
  - Translation:         # Use the provided path or the default path

- Line 84: `            # 首先尝试从环境变量中获取`
  - Translation:             # First, try to obtain from environment variables

- Line 87: `                # 使用默认路径`
  - Translation:                 # Use the default path

- Line 91: `            # 首先尝试从环境变量中获取`
  - Translation:             # First, try to obtain from the environment variables.

- Line 94: `                # 使用默认路径`
  - Translation:                 # Use the default path

- Line 100: `            f"ANPTool 初始化 - DID 路径: {did_document_path}, 私钥路径: {private_key_path}"`
  - Translation:             f"ANPTool Initialization - DID Path: {did_document_path}, Private Key Path: {private_key_path}"

- Line 116: `        执行 HTTP 请求以与其他代理交互`
  - Translation:         Execute HTTP request to interact with other agents

- Line 118: `        参数:`
  - Translation:         Parameters:

- Line 119: `            url (str): 代理描述文件或 API 端点的 URL`
  - Translation:             url (str): URL of the proxy description file or API endpoint

- Line 120: `            method (str, 可选): HTTP 方法，默认为 "GET"`
  - Translation:             method (str, optional): HTTP method, defaults to "GET"

- Line 121: `            headers (Dict[str, str], 可选): HTTP 请求头`
  - Translation:             headers (Dict[str, str], optional): HTTP request headers

- Line 122: `            params (Dict[str, Any], 可选): URL 查询参数`
  - Translation:             params (Dict[str, Any], optional): URL query parameters

- Line 123: `            body (Dict[str, Any], 可选): POST/PUT 请求的请求体`
  - Translation:             body (Dict[str, Any], optional): Request body for POST/PUT requests

- Line 125: `        返回:`
  - Translation:         Return:

- Line 126: `            Dict[str, Any]: 响应内容`
  - Translation:             Dict[str, Any]: Response content

- Line 134: `        logger.debug(f"ANP 请求: {method} {url}")`
  - Translation:         logger.debug(f"ANP Request: {method} {url}")

- Line 136: `        # 添加基本请求头`
  - Translation:         # Add basic request headers

- Line 140: `        # 添加 DID 认证`
  - Translation:         # Add DID authentication

- Line 146: `                logger.debug(f"获取认证头失败: {str(e)}")`
  - Translation:                 logger.debug(f"Failed to obtain authentication header: {str(e)}")

- Line 149: `            # 准备请求参数`
  - Translation:             # Prepare request parameters

- Line 156: `            # 如果有请求体且方法支持，添加请求体`
  - Translation:             # If there is a request body and the method supports it, add the request body.

- Line 160: `            # 执行请求`
  - Translation:             # Execute request

- Line 165: `                    logger.debug(f"ANP 响应: 状态码 {response.status}")`
  - Translation:                     logger.debug(f"ANP Response: Status Code {response.status}")

- Line 167: `                    # 检查响应状态`
  - Translation:                     # Check response status

- Line 174: `                            "认证失败 (401)，尝试重新获取认证"`
  - Translation:                             "Authentication failed (401), attempting to re-authenticate"

- Line 176: `                        # 如果认证失败且使用了 token，清除 token 并重试`
  - Translation:                         # If authentication fails and a token is used, clear the token and retry.

- Line 178: `                        # 重新获取认证头`
  - Translation:                         # Reacquire authentication header

- Line 182: `                        # 重新执行请求`
  - Translation:                         # Retry the request

- Line 186: `                                f"ANP 重试响应: 状态码 {retry_response.status}"`
  - Translation:                                 f"ANP Retry Response: Status Code {retry_response.status}"

- Line 192: `                logger.debug(f"HTTP 请求失败: {str(e)}")`
  - Translation:                 logger.debug(f"HTTP request failed: {str(e)}")

- Line 193: `                return {"error": f"HTTP 请求失败: {str(e)}", "status_code": 500}`
  - Translation:                 return {"error": f"HTTP request failed: {str(e)}", "status_code": 500}

- Line 196: `        """处理 HTTP 响应"""`
  - Translation:         Handle HTTP response

- Line 197: `        # 如果认证成功，更新 token`
  - Translation:         # If authentication is successful, update the token.

- Line 202: `                logger.debug(f"更新 token 失败: {str(e)}")`
  - Translation:                 logger.debug(f"Failed to update token: {str(e)}")

- Line 204: `        # 获取响应内容类型`
  - Translation:         # Get response content type

- Line 207: `        # 获取响应文本`
  - Translation:         # Get response text

- Line 210: `        # 根据内容类型处理响应`
  - Translation:         # Handle response based on content type

- Line 212: `            # 处理 JSON 响应`
  - Translation:             # Process JSON response

- Line 215: `                logger.debug("成功解析 JSON 响应")`
  - Translation:                 logger.debug("Successfully parsed JSON response")

- Line 218: `                    "Content-Type 声明为 JSON 但解析失败，返回原始文本"`
  - Translation:                     "Content-Type declared as JSON but parsing failed, returning raw text"

- Line 222: `            # 处理 YAML 响应`
  - Translation:             # Process YAML response

- Line 225: `                logger.debug("成功解析 YAML 响应")`
  - Translation:                 logger.debug("Successfully parsed YAML response")

- Line 233: `                    "Content-Type 声明为 YAML 但解析失败，返回原始文本"`
  - Translation:                     "Content-Type declared as YAML but parsing failed, returning raw text"

- Line 237: `            # 默认返回文本`
  - Translation:             # Default return text

- Line 240: `        # 添加状态码到结果`
  - Translation:         # Add status code to the result

- Line 251: `        # 添加 URL 到结果以便跟踪`
  - Translation:         # Add URL to results for tracking

- Line 263: `            anpsdk=None,  # 添加 anpsdk 参数`
  - Translation:             anpsdk = None,  # Add anpsdk parameter

- Line 264: `            caller_agent: str = None,  # 添加发起 agent 参数`
  - Translation:             caller_agent: str = None,  # Add initiating agent parameter

- Line 265: `            target_agent: str = None,  # 添加目标 agent 参数`
  - Translation:             target_agent: str = None,  # Add target agent parameter

- Line 266: `            use_two_way_auth: bool = False  # 是否使用双向认证`
  - Translation:             use_two_way_auth: bool = False  # Whether to use two-way authentication

- Line 269: `        使用双向认证执行 HTTP 请求以与其他代理交互`
  - Translation:         Perform HTTP requests using mutual authentication to interact with other proxies.

- Line 271: `        参数:`
  - Translation:         Parameters:

- Line 272: `            url (str): 代理描述文件或 API 端点的 URL`
  - Translation:             url (str): URL of the proxy description file or API endpoint

- Line 273: `            method (str, 可选): HTTP 方法，默认为 "GET"`
  - Translation:             method (str, optional): HTTP method, defaults to "GET"

- Line 274: `            headers (Dict[str, str], 可选): HTTP 请求头（将传递给 agent_auth_two_way 处理）`
  - Translation:             headers (Dict[str, str], optional): HTTP request headers (will be passed to agent_auth_two_way for processing)

- Line 275: `            params (Dict[str, Any], 可选): URL 查询参数`
  - Translation:             params (Dict[str, Any], optional): URL query parameters

- Line 276: `            body (Dict[str, Any], 可选): POST/PUT 请求的请求体`
  - Translation:             body (Dict[str, Any], optional): The request body for POST/PUT requests

- Line 278: `        返回:`
  - Translation:         Return:

- Line 279: `            Dict[str, Any]: 响应内容`
  - Translation:             Dict[str, Any]: Response content

- Line 287: `        logger.debug(f"ANP 双向认证请求: {method} {url}")`
  - Translation:         logger.debug(f"ANP bidirectional authentication request: {method} {url}")

- Line 290: `            # 1. 准备完整的 URL（包含查询参数）`
  - Translation:             # 1. Prepare the complete URL (including query parameters)

- Line 297: `                # 合并现有参数和新参数`
  - Translation:                 # Merge existing parameters with new parameters

- Line 301: `                # 重新构建 URL`
  - Translation:                 # Reconstruct URL

- Line 312: `            # 2. 准备请求体数据`
  - Translation:             # 2. Prepare request body data

- Line 317: `            # 3. 调用 agent_auth_two_way（需要传入必要的参数）`
  - Translation:             # 3. Call agent_auth_two_way (necessary parameters need to be passed in)

- Line 318: `            # 注意：这里暂时使用占位符，后续需要根据实际情况调整`
  - Translation:             # Note: A placeholder is temporarily used here, and adjustments will be needed based on actual circumstances later.

- Line 321: `                caller_agent=caller_agent,  # 需要传入调用方智能体ID`
  - Translation:                 caller_agent=caller_agent,  # Caller agent ID needs to be passed in

- Line 322: `                target_agent=target_agent,  # 需要传入目标方智能体ID，如果对方没有ID，可以随便写，因为对方不会响应这个信息`
  - Translation:                 target_agent=target_agent,  # The target agent ID needs to be provided. If the other party does not have an ID, you can enter any value, as the other party will not respond to this information.

- Line 326: `                custom_headers=headers,  # 传递自定义头部给 agent_auth_two_way 处理`
  - Translation:                 custom_headers=headers,  # Pass custom headers for agent_auth_two_way processing

- Line 330: `            logger.debug(f"ANP 双向认证响应: 状态码 {status}")`
  - Translation:             logger.debug(f"ANP bidirectional authentication response: Status code {status}")

- Line 332: `            # 4. 处理响应，保持与原 execute 方法相同的响应格式`
  - Translation:             # 4. Handle the response, maintaining the same response format as the original execute method.

- Line 338: `            logger.debug(f"双向认证请求失败: {str(e)}")`
  - Translation:             logger.debug(f"Bidirectional authentication request failed: {str(e)}")

- Line 340: `                "error": f"双向认证请求失败: {str(e)}",`
  - Translation:                 "error": f"Bidirectional authentication request failed: {str(e)}",

- Line 346: `        """处理双向认证的 HTTP 响应"""`
  - Translation:         """Handle HTTP response for mutual authentication"""

- Line 348: `        # 如果 response 已经是处理过的字典格式`
  - Translation:         # If response is already in processed dictionary format

- Line 352: `            # 尝试解析为 JSON`
  - Translation:             # Attempt to parse as JSON

- Line 355: `                logger.debug("成功解析 JSON 响应")`
  - Translation:                 logger.debug("Successfully parsed JSON response")

- Line 357: `                # 如果不是 JSON，作为文本处理`
  - Translation:                 # If not JSON, process as text

- Line 364: `            # 其他类型的响应`
  - Translation:             # Other types of responses

- Line 371: `        # 添加状态码和其他信息`
  - Translation:         # Add status codes and other information

- Line 391: `    """自定义 JSON 编码器，处理 OpenAI 对象"""`
  - Translation:     """Custom JSON encoder to handle OpenAI objects"""

- Line 402: `    """ANP Tool 智能爬虫 - 简化版本"""`
  - Translation:     """ANP Tool Intelligent Crawler - Simplified Version"""

- Line 409: `        """运行爬虫演示"""`
  - Translation:         """Run the crawler demonstration"""

- Line 411: `            # 获取调用者智能体`
  - Translation:             # Get the caller agent

- Line 414: `                return {"error": "无法获取调用者智能体"}`
  - Translation:                 return {"error": "Unable to retrieve caller agent"}

- Line 416: `            # 根据任务类型创建不同的提示模板`
  - Translation:             # Create different prompt templates based on the task type

- Line 419: `                agent_name = "天气查询爬虫"`
  - Translation:                 agent_name = "Weather Query Crawler"

- Line 423: `                agent_name = "多智能体搜索爬虫"`
  - Translation:                 agent_name = "Multi-Agent Search Crawler"

- Line 427: `                agent_name = "功能搜索爬虫"`
  - Translation:                 agent_name = "Function Search Crawler"

- Line 431: `                agent_name = "代码生成爬虫"`
  - Translation:                 agent_name = "Code Generation Crawler"

- Line 434: `            # 调用通用智能爬虫`
  - Translation:             # Invoke the universal intelligent crawler

- Line 453: `            logger.error(f"爬虫演示失败: {e}")`
  - Translation:             logger.error(f"Web crawler demonstration failed: {e}")

- Line 457: `        """获取调用者智能体"""`
  - Translation:         """Get the caller agent"""

- Line 461: `            user_data = user_data_manager.get_user_data_by_name("托管智能体_did:wba:agent-did.com:test:public")`
  - Translation:             user_data = user_data_manager.get_user_data_by_name("Managed Agent_did:wba:agent-did.com:test:public")

- Line 464: `                logger.debug(f"使用托管身份智能体进行爬取: {agent.name}")`
  - Translation:                 logger.debug(f"Crawling using managed identity agent: {agent.name}")

- Line 467: `                logger.error("未找到托管智能体")`
  - Translation:                 logger.error("Managed agent not found")

- Line 473: `        """创建溯源搜索智能体的提示模板"""`
  - Translation:         """Create a prompt template for a traceability search agent"""

- Line 476: `                 你是一个智能搜索工具。你的目标是根据用户输入要求从原始链接给出的agent列表，逐一查询agent描述文件，选择合适的agent，调用工具完成代码任务。`
  - Translation:                  You are an intelligent search tool. Your goal is to query the agent description files one by one from the list of agents provided by the original link based on user input requirements, select the appropriate agent, and call the tool to complete the code task.

- Line 478: `                 ## 当前任务`
  - Translation:                  ## Current task

- Line 481: `                 ## 重要提示`
  - Translation:                  ## Important Notice

- Line 482: `                 1. 你使用的anp_tool非常强大，可以访问内网和外网地址，你将用它访问初始URL（{{initial_url}}），它是一个agent列表文件，`
  - Translation:                  1. The anp_tool you are using is very powerful, capable of accessing both internal and external network addresses. You will use it to access the initial URL ({{initial_url}}), which is an agent list file.

- Line 483: `                 2. 每个agent的did格式为 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211'，从 did格式可以获取agent的did文件地址`
  - Translation:                  2. The format of each agent's DID is 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211', from which the DID file address of the agent can be obtained.

- Line 484: `                 例如 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211' 的did地址为 `
  - Translation:                  For example, the DID address of 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211' is

- Line 486: `                 3. 从 did文件中，可以获得 "serviceEndpoint": "http://localhost:9527/wba/user/5fea49e183c6c211/ad.json"`
  - Translation:                  3. From the did file, you can obtain "serviceEndpoint": "http://localhost:9527/wba/user/5fea49e183c6c211/ad.json"

- Line 487: `                 4. 从 ad.json，你可以获得这个代理的详细结构、功能和 API 使用方法。`
  - Translation:                  4. From ad.json, you can obtain the detailed structure, functionality, and API usage methods of this proxy.

- Line 488: `                 5. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。`
  - Translation:                  5. You need to continuously discover and access new URLs and API endpoints like a web crawler.

- Line 489: `                 6. 你要优先理解api_interface.json这样的文件对api使用方式的描述，特别是参数的配置，params下属的字段可以直接作为api的参数`
  - Translation:                  6. You should prioritize understanding the description of API usage in files like api_interface.json, especially the configuration of parameters. Fields under params can be directly used as API parameters.

- Line 490: `                 7. 你可以使用 anp_tool 获取任何 URL 的内容。`
  - Translation:                  7. You can use anp_tool to retrieve the content of any URL.

- Line 491: `                 8. 该工具可以处理各种响应格式。`
  - Translation:                  8. This tool can handle various response formats.

- Line 492: `                 9. 阅读每个文档以找到与任务相关的信息或 API 端点。`
  - Translation:                  9. Read each document to find information or API endpoints related to the task.

- Line 493: `                 10. 你需要自己决定爬取路径，不要等待用户指令。`
  - Translation:                  10. You need to decide the crawling path yourself; do not wait for user instructions.

- Line 494: `                 11. 注意：你最多可以爬取 6 个 agent，每个agent最多可以爬取20次，达到此限制后必须结束搜索。`
  - Translation:                  11. Note: You can crawl up to 6 agents, with each agent being crawled a maximum of 20 times. Once this limit is reached, the search must be terminated.

- Line 496: `                 ## 工作流程`
  - Translation:                  ## Workflow

- Line 497: `                 1. 获取初始 URL 的内容并理解代理的功能。`
  - Translation:                  1. Retrieve the content of the initial URL and understand the functionality of the proxy.

- Line 498: `                 2. 分析内容以找到所有可能的链接和 API 文档。`
  - Translation:                  2. Analyze the content to find all possible links and API documentation.

- Line 499: `                 3. 解析 API 文档以了解 API 的使用方法。`
  - Translation:                  3. Parse the API documentation to understand how to use the API.

- Line 500: `                 4. 根据任务需求构建请求以获取所需的信息。`
  - Translation:                  4. Construct requests according to task requirements to obtain the necessary information.

- Line 501: `                 5. 继续探索相关链接，直到找到足够的信息。`
  - Translation:                  5. Continue exploring relevant links until sufficient information is found.

- Line 502: `                 6. 总结信息并向用户提供最合适的建议。`
  - Translation:                  6. Summarize the information and provide the most suitable advice to the user.

- Line 504: `                 提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。`
  - Translation:                  Provide detailed information and clear explanations to help users understand the information you found and your recommendations.

- Line 506: `                 ## 日期`
  - Translation:                  ## Date

- Line 507: `                 当前日期：{current_date}`
  - Translation:                  Current date: {current_date}

- Line 510: `        """创建功能搜索智能体的提示模板"""`
  - Translation:         """Create a prompt template for a feature search agent"""

- Line 513: `                你是一个智能搜索工具。你的目标是根据用户输入要求识别合适的工具，调用工具完成代码任务。`
  - Translation:                 You are an intelligent search tool. Your goal is to identify the appropriate tool based on user input requirements and invoke the tool to complete code tasks.

- Line 515: `                ## 当前任务`
  - Translation:                 ## Current task

- Line 518: `                ## 重要提示`
  - Translation:                 ## Important Notice

- Line 519: `                1. 你将收到一个初始 URL（{{initial_url}}），这是一个代理描述文件。`
  - Translation:                 1. You will receive an initial URL ({{initial_url}}), which is a proxy description file.

- Line 520: `                2. 你需要理解这个代理的结构、功能和 API 使用方法。`
  - Translation:                 2. You need to understand the structure, functionality, and API usage of this proxy.

- Line 521: `                3. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。`
  - Translation:                 3. You need to continuously discover and access new URLs and API endpoints like a web crawler.

- Line 522: `                4. 你可以使用 anp_tool 获取任何 URL 的内容。`
  - Translation:                 4. You can use anp_tool to retrieve the content of any URL.

- Line 523: `                5. 该工具可以处理各种响应格式。`
  - Translation:                 5. This tool can handle various response formats.

- Line 524: `                6. 阅读每个文档以找到与任务相关的信息或 API 端点。`
  - Translation:                 6. Read each document to find information or API endpoints related to the task.

- Line 525: `                7. 你需要自己决定爬取路径，不要等待用户指令。`
  - Translation:                 7. You need to decide the crawling path yourself; do not wait for user instructions.

- Line 526: `                8. 注意：你最多可以爬取 10 个 URL，达到此限制后必须结束搜索。`
  - Translation:                 8. Note: You can crawl up to 10 URLs, and must stop searching once this limit is reached.

- Line 528: `                ## 工作流程`
  - Translation:                 ## Workflow

- Line 529: `                1. 获取初始 URL 的内容并理解代理的功能。`
  - Translation:                 1. Retrieve the content of the initial URL and understand the function of the proxy.

- Line 530: `                2. 分析内容以找到所有可能的链接和 API 文档。`
  - Translation:                 2. Analyze the content to find all possible links and API documentation.

- Line 531: `                3. 解析 API 文档以了解 API 的使用方法。`
  - Translation:                 3. Parse the API documentation to understand how to use the API.

- Line 532: `                4. 根据任务需求构建请求以获取所需的信息。`
  - Translation:                 4. Construct requests according to task requirements to obtain the necessary information.

- Line 533: `                5. 继续探索相关链接，直到找到足够的信息。`
  - Translation:                 5. Continue exploring related links until sufficient information is found.

- Line 534: `                6. 总结信息并向用户提供最合适的建议。`
  - Translation:                 6. Summarize the information and provide the most suitable advice to the user.

- Line 536: `                提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。`
  - Translation:                 Provide detailed information and clear explanations to help users understand the information you found and your recommendations.

- Line 538: `                ## 日期`
  - Translation:                 ## Date

- Line 539: `                当前日期：{current_date}`
  - Translation:                 Current Date: {current_date}

- Line 542: `        """创建代码搜索智能体的提示模板"""`
  - Translation:         """Create a prompt template for the code search agent"""

- Line 545: `        你是一个通用的智能代码工具。你的目标是根据用户输入要求调用工具完成代码任务。`
  - Translation:         You are a general intelligent code tool. Your goal is to call tools to complete code tasks based on user input requirements.

- Line 547: `        ## 当前任务`
  - Translation:         ## Current task

- Line 550: `        ## 重要提示`
  - Translation:         ## Important Notice

- Line 551: `        1. 你将收到一个初始 URL（{{initial_url}}），这是一个代理描述文件。`
  - Translation:         You will receive an initial URL ({{initial_url}}), which is a proxy description file.

- Line 552: `        2. 你需要理解这个代理的结构、功能和 API 使用方法。`
  - Translation:         2. You need to understand the structure, functionality, and API usage of this proxy.

- Line 553: `        3. 你需要像网络爬虫一样不断发现和访问新的 URL 和 API 端点。`
  - Translation:         3. You need to continuously discover and access new URLs and API endpoints like a web crawler.

- Line 554: `        4. 你可以使用 anp_tool 获取任何 URL 的内容。`
  - Translation:         4. You can use anp_tool to retrieve the content of any URL.

- Line 555: `        5. 该工具可以处理各种响应格式。`
  - Translation:         5. This tool can handle various response formats.

- Line 556: `        6. 阅读每个文档以找到与任务相关的信息或 API 端点。`
  - Translation:         6. Read each document to find information or API endpoints related to the task.

- Line 557: `        7. 你需要自己决定爬取路径，不要等待用户指令。`
  - Translation:         7. You need to decide the crawling path yourself; do not wait for user instructions.

- Line 558: `        8. 注意：你最多可以爬取 10 个 URL，达到此限制后必须结束搜索。`
  - Translation:         8. Note: You can crawl up to 10 URLs, and must stop searching once this limit is reached.

- Line 560: `        ## 工作流程`
  - Translation:         ## Workflow

- Line 561: `        1. 获取初始 URL 的内容并理解代理的功能。`
  - Translation:         1. Retrieve the content of the initial URL and understand the functionality of the proxy.

- Line 562: `        2. 分析内容以找到所有可能的链接和 API 文档。`
  - Translation:         2. Analyze the content to find all possible links and API documentation.

- Line 563: `        3. 解析 API 文档以了解 API 的使用方法。`
  - Translation:         3. Parse the API documentation to understand how to use the API.

- Line 564: `        4. 根据任务需求构建请求以获取所需的信息。`
  - Translation:         4. Construct the request according to task requirements to obtain the necessary information.

- Line 565: `        5. 继续探索相关链接，直到找到足够的信息。`
  - Translation:         5. Continue exploring related links until sufficient information is found.

- Line 566: `        6. 总结信息并向用户提供最合适的建议。`
  - Translation:         6. Summarize the information and provide the most suitable advice to the user.

- Line 568: `        提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。`
  - Translation:         Provide detailed information and clear explanations to help users understand the information you found and your recommendations.

- Line 570: `        ## 日期`
  - Translation:         ## Date

- Line 571: `        当前日期：{current_date}`
  - Translation:         Current Date: {current_date}

- Line 575: `        """创建天气搜索智能体的提示模板"""`
  - Translation:         """Create a prompt template for the weather search agent"""

- Line 577: `        你是一个通用智能网络数据探索工具。你的目标是通过递归访问各种数据格式（包括JSON-LD、YAML等）来找到用户需要的信息和API以完成特定任务。`
  - Translation:         You are a general intelligent network data exploration tool. Your goal is to find the information and APIs needed by the user to complete specific tasks by recursively accessing various data formats (including JSON-LD, YAML, etc.).

- Line 579: `        ## 当前任务`
  - Translation:         ## Current task

- Line 582: `        ## 重要提示`
  - Translation:         ## Important Notice

- Line 583: `        1. 你将收到一个初始URL（{initial_url}），这是一个代理描述文件。`
  - Translation:         You will receive an initial URL ({initial_url}), which is a proxy description file.

- Line 584: `        2. 你需要理解这个代理的结构、功能和API使用方法。`
  - Translation:         2. You need to understand the structure, functionality, and API usage of this proxy.

- Line 585: `        3. 你需要像网络爬虫一样持续发现和访问新的URL和API端点。`
  - Translation:         3. You need to continuously discover and access new URLs and API endpoints like a web crawler.

- Line 586: `        4. 你可以使用anp_tool来获取任何URL的内容。`
  - Translation:         4. You can use anp_tool to retrieve the content of any URL.

- Line 587: `        5. 此工具可以处理各种响应格式。`
  - Translation:         5. This tool can handle various response formats.

- Line 588: `        6. 阅读每个文档以找到与任务相关的信息或API端点。`
  - Translation:         6. Read each document to find information or API endpoints related to the task.

- Line 589: `        7. 你需要自己决定爬取路径，不要等待用户指令。`
  - Translation:         7. You need to determine the crawling path yourself; do not wait for user instructions.

- Line 590: `        8. 注意：你最多可以爬取10个URL，并且必须在达到此限制后结束搜索。`
  - Translation:         8. Note: You can crawl up to 10 URLs, and you must end the search after reaching this limit.

- Line 592: `        ## 爬取策略`
  - Translation:         ## Scraping strategy

- Line 593: `        1. 首先获取初始URL的内容，理解代理的结构和API。`
  - Translation:         1. First, retrieve the content of the initial URL to understand the structure of the proxy and the API.

- Line 594: `        2. 识别文档中的所有URL和链接，特别是serviceEndpoint、url、@id等字段。`
  - Translation:         2. Identify all URLs and links in the document, especially fields like serviceEndpoint, url, @id, etc.

- Line 595: `        3. 分析API文档以理解API用法、参数和返回值。`
  - Translation:         3. Analyze the API documentation to understand the API usage, parameters, and return values.

- Line 596: `        4. 根据API文档构建适当的请求，找到所需信息。`
  - Translation:         4. Construct appropriate requests according to the API documentation to find the required information.

- Line 597: `        5. 记录所有你访问过的URL，避免重复爬取。`
  - Translation:         5. Record all the URLs you have visited to avoid duplicate crawling.

- Line 598: `        6. 总结所有你找到的相关信息，并提供详细的建议。`
  - Translation:         6. Summarize all the relevant information you have found and provide detailed recommendations.

- Line 600: `        对于天气查询任务，你需要:`
  - Translation:         For the weather query task, you need to:

- Line 601: `        1. 找到天气查询API端点`
  - Translation:         1. Locate the weather query API endpoint

- Line 602: `        2. 理解如何正确构造请求参数（如城市名、日期等）`
  - Translation:         2. Understand how to correctly construct request parameters (such as city name, date, etc.)

- Line 603: `        3. 发送天气查询请求`
  - Translation:         3. Send weather query request

- Line 604: `        4. 获取并展示天气信息`
  - Translation:         4. Retrieve and display weather information

- Line 606: `        提供详细的信息和清晰的解释，帮助用户理解你找到的信息和你的建议。`
  - Translation:         Provide detailed information and clear explanations to help users understand the information you found and your recommendations.

- Line 614: `                                 max_documents: int = 10, agent_name: str = "智能爬虫"):`
  - Translation:                                  max_documents: int = 10, agent_name: str = "Smart Crawler"):

- Line 615: `        """通用智能爬虫功能"""`
  - Translation:         """General intelligent crawler functionality"""

- Line 616: `        logger.info(f"启动{agent_name}智能爬取: {initial_url}")`
  - Translation:         logger.info(f"Initiating intelligent crawling for {agent_name}: {initial_url}")

- Line 618: `        # 初始化变量`
  - Translation:         # Initialize variable

- Line 622: `        # 初始化ANPTool`
  - Translation:         # Initialize ANPTool

- Line 628: `        # 获取初始URL内容`
  - Translation:         # Retrieve initial URL content

- Line 639: `            logger.debug(f"成功获取初始URL: {initial_url}")`
  - Translation:             logger.debug(f"Successfully obtained initial URL: {initial_url}")

- Line 641: `            logger.error(f"获取初始URL失败: {str(e)}")`
  - Translation:             logger.error(f"Failed to retrieve initial URL: {str(e)}")

- Line 644: `        # 创建LLM客户端`
  - Translation:         # Create LLM client

- Line 647: `            return self._create_error_result("LLM客户端创建失败", visited_urls, crawled_documents, task_type)`
  - Translation:             return self._create_error_result("Failed to create LLM client", visited_urls, crawled_documents, task_type)

- Line 649: `        # 创建初始消息`
  - Translation:         # Create initial message

- Line 652: `        # 开始对话循环`
  - Translation:         # Start the conversation loop

- Line 662: `        """创建错误结果"""`
  - Translation:         Create error result

- Line 664: `            "content": f"错误: {error_msg}",`
  - Translation:             "content": f"Error: {error_msg}",

- Line 673: `        """创建成功结果"""`
  - Translation:         """Creation successful result"""

- Line 684: `        """创建LLM客户端"""`
  - Translation:         """Create LLM client"""

- Line 696: `                logger.error("需要配置 OpenAI")`
  - Translation:                 logger.error("OpenAI configuration is required")

- Line 699: `            logger.error(f"创建LLM客户端失败: {e}")`
  - Translation:             logger.error(f"Failed to create LLM client: {e}")

- Line 704: `        """创建初始消息"""`
  - Translation:         Create initial message

- Line 714: `                "content": f"我已获取初始URL的内容。以下是{agent_name}的描述数据:\n\n```json\n{json.dumps(initial_content, ensure_ascii=False, indent=2)}\n```\n\n请分析这些数据，理解{agent_name}的功能和API使用方法。找到你需要访问的链接，并使用anp_tool获取更多信息以完成用户的任务。",`
  - Translation:                 "content": f"I have obtained the content of the initial URL. Below is the descriptive data of {agent_name}:\n\n```json\n{json.dumps(initial_content, ensure_ascii=False, indent=2)}\n```\n\nPlease analyze this data to understand the functionality and API usage of {agent_name}. Find the links you need to access and use anp_tool to get more information to complete the user's task."

- Line 722: `        """对话循环处理"""`
  - Translation:         """Dialogue loop processing"""

- Line 728: `            logger.info(f"开始爬取迭代 {current_iteration}/{max_documents}")`
  - Translation:             logger.info(f"Starting to crawl iteration {current_iteration}/{max_documents}")

- Line 731: `                logger.info(f"已达到最大爬取文档数 {max_documents}，停止爬取")`
  - Translation:                 logger.info(f"Reached the maximum number of documents to crawl {max_documents}, stopping the crawl")

- Line 734: `                    "content": f"你已爬取 {len(crawled_documents)} 个文档，达到最大爬取限制 {max_documents}。请根据获取的信息做出最终总结。",`
  - Translation:                     "content": f"You have crawled {len(crawled_documents)} documents, reaching the maximum crawl limit of {max_documents}. Please make a final summary based on the information obtained."

- Line 746: `                logger.info(f"\n模型返回:\n{response_message}")`
  - Translation:                 logger.info(f"\nModel returned:\n{response_message}")

- Line 755: `                    logger.debug("模型没有请求任何工具调用，结束爬取")`
  - Translation:                     logger.debug("The model did not request any tool invocation, ending the crawl")

- Line 758: `                # 处理工具调用`
  - Translation:                 # Handle tool invocation

- Line 769: `                logger.error(f"模型调用失败: {e}")`
  - Translation:                 logger.error(f"Model invocation failed: {e}")

- Line 772: `                    "content": f"处理过程中发生错误: {str(e)}。请根据已获取的信息做出最佳判断。",`
  - Translation:                     "content": f"An error occurred during processing: {str(e)}. Please make the best judgment based on the information obtained.",

- Line 776: `        # 返回最后的响应内容`
  - Translation:         # Return the final response content

- Line 778: `            return messages[-1].get("content", "处理完成")`
  - Translation:             return messages[-1].get("content", "Processing complete")

- Line 779: `        return "处理完成"`
  - Translation:         return "Processing complete"

- Line 782: `        """获取可用工具列表"""`
  - Translation:         """Get the list of available tools"""

- Line 799: `        """处理工具调用"""`
  - Translation:         """Handle tool invocation"""

- Line 814: `        """处理ANP工具调用"""`
  - Translation:         """Handle ANP tool invocation"""

- Line 820: `        # 兼容 "parameters":{"params":{...}}、"parameters":{"a":...} 以及直接 "params":{...} 的情况`
  - Translation:         # Compatible with "parameters":{"params":{...}}, "parameters":{"a":...}, and directly "params":{...} scenarios.

- Line 827: `                        # 如果parameters本身就是参数字典（如{"a":2.88888,"b":999933.4445556}），直接作为params`
  - Translation:                         # If parameters itself is a parameter dictionary (e.g., {"a":2.88888,"b":999933.4445556}), use it directly as params

- Line 831: `        # 处理消息参数`
  - Translation:         # Process message parameters

- Line 835: `                logger.debug(f"模型发出调用消息：{message_value}")`
  - Translation:                 logger.debug(f"Model issued a call message: {message_value}")

- Line 837: `        logger.info(f"根据模型要求组装请求:\n{url}:{method}\nheaders:{headers}params:{params}body:{body}")`
  - Translation:         logger.info(f"Assembling request according to model requirements:\n{url}:{method}\nheaders:{headers}params:{params}body:{body}")

- Line 850: `            logger.debug(f"ANPTool 响应 [url: {url}]")`
  - Translation:             logger.debug(f"ANPTool response [url: {url}]")

- Line 861: `            logger.error(f"ANPTool调用失败 {url}: {str(e)}")`
  - Translation:             logger.error(f"ANPTool invocation failed {url}: {str(e)}")

- Line 866: `                    "error": f"ANPTool调用失败: {url}",`
  - Translation:                     "error": f"ANPTool invocation failed: {url}",

- Line 872: `        """递归查找参数中的message值"""`
  - Translation:         """Recursively search for the message value in the parameters"""


## ./anp_open_sdk/service/interaction/anp_sdk_group_member.py

- Line 1: `# Agent 端 SDK 用于简化 agent 与群组的交互`
  - Translation: # Agent-side SDK is used to simplify the interaction between the agent and the group.

- Line 4: `import time  # 添加缺失的导入`
  - Translation: import time  # Add missing import

- Line 11: `    """Agent 端的群组 SDK"""`
  - Translation:     """Group SDK on the agent side"""

- Line 24: `        """设置本地 SDK 实例（用于本地优化）"""`
  - Translation:         """Set up local SDK instance (for local optimization)"""

- Line 29: `        """加入群组"""`
  - Translation:         Join Group

- Line 31: `            # 本地优化路径`
  - Translation:             # Local optimization path

- Line 46: `        # HTTP 请求路径`
  - Translation:         # HTTP request path

- Line 58: `        """离开群组"""`
  - Translation:         Group

- Line 60: `            # 本地优化路径`
  - Translation:             # Local optimization path

- Line 65: `        # HTTP 请求路径`
  - Translation:         # HTTP request path

- Line 79: `        """发送消息到群组"""`
  - Translation:         Send message to group

- Line 81: `            # 本地优化路径`
  - Translation:             # Local optimization path

- Line 95: `        # HTTP 请求路径`
  - Translation:         # HTTP request path

- Line 108: `        """监听群组消息"""`
  - Translation:         Listen to group messages

- Line 110: `            # 本地优化路径`
  - Translation:             # Local optimization path

- Line 134: `        # HTTP SSE 路径`
  - Translation:         # HTTP SSE Path

- Line 161: `        """停止监听群组消息"""`
  - Translation:         Stop listening to group messages

- Line 172: `        """获取群组成员列表"""`
  - Translation:         Get the list of group members

- Line 174: `            # 本地优化路径`
  - Translation:             # Local optimization path

- Line 179: `        # HTTP 请求路径`
  - Translation:         # HTTP request path


## ./anp_open_sdk/service/interaction/anp_sdk_group_runner.py

- Line 18: `    """消息类型枚举"""`
  - Translation:     """Message Type Enumeration"""

- Line 27: `    """群组消息"""`
  - Translation:     """Group Message"""

- Line 36: `        """转换为字典"""`
  - Translation:         """Convert to dictionary"""

- Line 48: `    """Agent 信息"""`
  - Translation:     """Agent Information"""

- Line 55: `        """转换为字典"""`
  - Translation:         """Convert to dictionary"""

- Line 64: `    """GroupRunner 基类 - 开发者继承此类实现自己的群组逻辑"""`
  - Translation:     """GroupRunner base class - Developers inherit this class to implement their own group logic"""

- Line 74: `        """处理 agent 加入请求`
  - Translation:         """Handle agent join request"""

- Line 77: `            agent: 要加入的 Agent 信息`
  - Translation:             agent: Information of the Agent to be added

- Line 80: `            True 允许加入，False 拒绝`
  - Translation:             True allows joining, False denies

- Line 86: `        """处理 agent 离开`
  - Translation:         Handle agent departure

- Line 89: `            agent: 离开的 Agent 信息`
  - Translation:             agent: Information of the departing Agent

- Line 95: `        """处理消息`
  - Translation:         Process message

- Line 98: `            message: 接收到的消息`
  - Translation:             message: Received message

- Line 101: `            可选的响应消息`
  - Translation:             Optional response message

- Line 106: `        """广播消息给所有监听的 agent"""`
  - Translation:         Broadcast message to all listening agents

- Line 119: `        """发送消息给特定 agent"""`
  - Translation:         """Send a message to a specific agent"""

- Line 127: `        """移除成员"""`
  - Translation:         Remove member

- Line 132: `            # 清理监听器`
  - Translation:             # Clean up listeners

- Line 139: `        """获取所有成员"""`
  - Translation:         """Get all members"""

- Line 143: `        """获取特定成员"""`
  - Translation:         Get specific member

- Line 147: `        """检查是否是成员"""`
  - Translation:         """Check if it is a member"""

- Line 152: `        """注册消息监听器"""`
  - Translation:         """Register message listener"""

- Line 157: `        """注销消息监听器"""`
  - Translation:         Unregister message listener

- Line 165: `        """启动 GroupRunner"""`
  - Translation:         """Start GroupRunner"""

- Line 170: `        """停止 GroupRunner"""`
  - Translation:         Stop GroupRunner

- Line 172: `        # 通知所有成员群组关闭`
  - Translation:         # Notify all members that the group is closing.

- Line 184: `    """群组管理器 - 管理所有 GroupRunner"""`
  - Translation:     """Group Manager - Manages all GroupRunners"""

- Line 193: `        """注册 GroupRunner"""`
  - Translation:         Register GroupRunner

- Line 200: `        # 保存自定义路由模式`
  - Translation:         # Save custom routing pattern

- Line 206: `        # 启动 runner`
  - Translation:         # Start runner

- Line 210: `        """注销 GroupRunner"""`
  - Translation:         Unregister GroupRunner

- Line 220: `        """获取群组的 runner"""`
  - Translation:         """Get the group's runner"""

- Line 224: `        """列出所有群组"""`
  - Translation:         List all groups


## ./anp_open_sdk/service/router/router_auth.py

- Line 51: `        if req_did != "": # token 用户`
  - Translation:         if req_did != "": # token user

- Line 53: `        else: # did 用户   `
  - Translation:         else: # did user

- Line 55: `                # 检查auth_data是否为字符串`
  - Translation:                 # Check if auth_data is a string

- Line 62: `        logger.warning(f"解析认证数据时出错: {e}")`
  - Translation:         logger.warning(f"Error parsing authentication data: {e}")

- Line 65: `    #logger.debug(f"请求方{user}通过认证中间件认证，认证方返回token和自身认证头")`
  - Translation:     #logger.debug(f"The requester {user} is authenticated through the authentication middleware, and the authenticator returns a token and its own authentication header")

- Line 84: `    将类似于 'key1="value1", key2="value2"' 的字符串解析为字典`
  - Translation:     Parse a string similar to 'key1="value1", key2="value2"' into a dictionary.

- Line 88: `        # 先按逗号分割，再按等号分割`
  - Translation:         # First split by comma, then split by equals sign.

- Line 94: `        logger.warning(f"解析认证字符串为字典时出错: {e}")`
  - Translation:         logger.warning(f"Error parsing authentication string into dictionary: {e}")


## ./anp_open_sdk/service/router/router_publisher.py

- Line 55: `    获取已发布的代理列表，直接从运行中的 SDK 实例获取。`
  - Translation:     Get the list of published proxies directly from the running SDK instance.

- Line 56: `    发布设置:`
  - Translation:     Release Settings:

- Line 57: `    - open: 公开给所有人`
  - Translation:     - open: Open to everyone

- Line 60: `        # 通过 request.app.state 获取在 ANPSDK 初始化时存储的 sdk 实例`
  - Translation:         # Use request.app.state to retrieve the sdk instance stored during ANPSDK initialization.

- Line 63: `        # 从 SDK 实例中获取所有已注册的 agent`
  - Translation:         # Get all registered agents from the SDK instance

- Line 64: `        all_agents = sdk.get_agents() # 使用 get_agents() 公共方法`
  - Translation:         all_agents = sdk.get_agents() # Use the public method get_agents()


## ./anp_open_sdk/service/router/router_did.py

- Line 70: `# 注意：托管 DID 文档的功能已移至 router_publisher.py`
  - Translation: # Note: The function for hosting DID documents has been moved to router_publisher.py

- Line 71: `# 未来对于托管 did-doc/ad.json/yaml 以及消息转发/api转发都将通过 publisher 路由处理`
  - Translation: # In the future, the routing of publisher will handle the hosting of did-doc/ad.json/yaml and message forwarding/API forwarding.

- Line 77: `    user_id可以是did 也可以是 最后hex序号`
  - Translation:     user_id can be either did or the final hex number.

- Line 78: `    返回符合 schema.org/did/ad 规范的 JSON-LD 格式智能体描述，端点信息动态取自 agent 实例。`
  - Translation:     Return a JSON-LD formatted agent description that complies with the schema.org/did/ad specification, with endpoint information dynamically retrieved from the agent instance.

- Line 98: `    # 获取基础端点`
  - Translation:     # Get base endpoint

- Line 99: `    # 动态遍历 FastAPI 路由，自动生成 endpoints`
  - Translation:     # Dynamically iterate FastAPI routes to automatically generate endpoints

- Line 105: `            # 只导出 /agent/api/、/agent/message/、/agent/group/、/wba/ 相关路由`
  - Translation:             # Only export routes related to /agent/api/, /agent/message/, /agent/group/, /wba/

- Line 109: `            # endpoint 名称自动生成`
  - Translation:             # Endpoint name auto-generation

- Line 113: `                "description": getattr(route, "summary", getattr(route, "name", "相关端点"))`
  - Translation:                 "description": getattr(route, "summary", getattr(route, "name", "Related Endpoint"))

- Line 120: `            "description": f"API 路径 {path} 的端点"`
  - Translation:             "description": f"Endpoint for API path {path}"

- Line 123: `    # 读取 ad.json 模板文件`
  - Translation:     # Read the ad.json template file

- Line 132: `    # 默认模板内容`
  - Translation:     # Default template content

- Line 136: `            "name": f"{agent.name}的开发者",`
  - Translation:             "name": f"{agent.name}'s developer",

- Line 157: `    # 从模板获取或初始化接口列表，使用 "ad:interfaces" 作为标准键，并兼容旧的 "interfaces"`
  - Translation:     # Get or initialize the interface list from the template, using "ad:interfaces" as the standard key, and compatible with the old "interfaces".

- Line 158: `    # 只保留 /agent/api/ 相关接口`
  - Translation:     # Only retain interfaces related to /agent/api/

- Line 161: `    # 添加您指定的静态接口`
  - Translation:     # Add your specified static interface

- Line 162: `    # 添加静态接口（如需保留，可注释掉以下三项）`
  - Translation:     # Add static interfaces (comment out the following three items if you want to keep them)

- Line 168: `            "description": "提供自然语言交互接口的OpenAPI的YAML文件，可以通过接口与智能体进行自然语言交互."`
  - Translation:             "description": "YAML file for OpenAPI providing a natural language interaction interface, enabling natural language interaction with agents through the interface."

- Line 174: `            "description": "智能体的 YAML 描述的接口调用方法"`
  - Translation:             "description": "Interface invocation method described by the agent's YAML"

- Line 180: `            "description": "智能体的 JSON RPC 描述的接口调用方法"`
  - Translation:             "description": "Interface call method described by the agent's JSON RPC"

- Line 184: `    # 只添加 /agent/api/ 相关端点`
  - Translation:     # Only add endpoints related to /agent/api/

- Line 199: `    # 添加动态发现的端点，并统一格式`
  - Translation:     # Add dynamically discovered endpoints and unify the format.

- Line 214: `    # 确保必要的字段存在`
  - Translation:     # Ensure the necessary fields are present

- Line 229: `        # 新增处理：如果 user_id 不包含 %3A，按 : 分割，第四个部分是数字，则把第三个 : 换成 %3A`
  - Translation:         # New handling: If user_id does not contain %3A, split by :, and if the fourth part is a number, replace the third : with %3A.


## ./anp_open_sdk/service/router/router_agent.py

- Line 33: `    """智能体搜索记录"""`
  - Translation:     """Agent Search Record"""

- Line 39: `        """记录搜索行为"""`
  - Translation:         """Record search behavior"""

- Line 49: `        """获取最近的搜索记录"""`
  - Translation:         Get the most recent search records

- Line 54: `    """智能体通讯录"""`
  - Translation:     "Agent Directory"

- Line 58: `        self.contacts = {}  # did -> 联系人信息`
  - Translation:         self.contacts = {}  # did -> Contact information

- Line 61: `        """添加联系人"""`
  - Translation:         """Add Contact"""

- Line 76: `        """更新交互记录"""`
  - Translation:         interaction record

- Line 82: `        """获取联系人列表"""`
  - Translation:         """Get contact list"""

- Line 89: `    """会话记录"""`
  - Translation:     """Session Record"""

- Line 92: `        self.sessions = {}  # session_id -> 会话信息`
  - Translation:         self.sessions = {}  # session_id -> session information

- Line 95: `        """创建会话"""`
  - Translation:         """Create session"""

- Line 109: `        """添加消息"""`
  - Translation:         """Add Message"""

- Line 118: `        """关闭会话"""`
  - Translation:         """Close session"""

- Line 124: `        """获取活跃会话"""`
  - Translation:         """Get active sessions"""

- Line 129: `    """API调用记录"""`
  - Translation:     """API Call Log"""

- Line 135: `        """记录API调用"""`
  - Translation:         """Log API call"""

- Line 149: `        """获取最近的API调用记录"""`
  - Translation:         """Get the most recent API call records"""

- Line 154: `    """智能体路由器，负责管理多个本地智能体并路由请求"""`
  - Translation:     Agent router, responsible for managing multiple local agents and routing requests

- Line 157: `        self.local_agents = {}  # did -> LocalAgent实例`
  - Translation:         self.local_agents = {}  # did -> LocalAgent instance

- Line 161: `        """注册一个本地智能体"""`
  - Translation:         """Register a local agent"""

- Line 163: `        self.logger.debug(f"已注册智能体到多智能体路由: {agent.id}")`
  - Translation:         self.logger.debug(f"Agent registered to multi-agent router: {agent.id}")

- Line 167: `        """获取指定DID的本地智能体"""`
  - Translation:         """Get the local agent for the specified DID"""

- Line 171: `        """路由请求到对应的本地智能体"""`
  - Translation:         Route the request to the corresponding local agent

- Line 176: `            if hasattr(self.local_agents[resp_did].handle_request, "__call__"):  # 确保 `handle_request` 可调用`
  - Translation:             if hasattr(self.local_agents[resp_did].handle_request, "__call__"):  # Ensure `handle_request` is callable

- Line 178: `                # 将agent实例 挂载到request.state 方便在处理中引用`
  - Translation:                 # Mount the agent instance to request.state for convenient reference during processing.

- Line 181: `                        f"成功路由到{resp_agent.id}的处理函数, 请求数据为{request_data}\n"`
  - Translation:                         f"Successfully routed to the handler function of {resp_agent.id}, request data is {request_data}\n"

- Line 182: `                        f"完整请求为 url: {request.url} \n"`
  - Translation:                         f"Complete request is url: {request.url} \n"

- Line 186: `                self.logger.error(f"{resp_did} 的 `handle_request` 不是一个可调用对象")`
  - Translation:                 self.logger.error(f"The `handle_request` of {resp_did} is not a callable object")

- Line 187: `                raise TypeError(f"{resp_did} 的 `handle_request` 不是一个可调用对象")`
  - Translation:                 raise TypeError(f"`handle_request` of {resp_did} is not a callable object")

- Line 189: `            self.logger.error(f"智能体路由器未找到本地智能体注册的调用方法: {resp_did}")`
  - Translation:             self.logger.error(f"Agent router could not find the local agent registration call method: {resp_did}")

- Line 190: `            raise ValueError(f"未找到本地智能体: {resp_did}")`
  - Translation:             raise ValueError(f"Local agent not found: {resp_did}")

- Line 195: `        """获取所有本地智能体"""`
  - Translation:         """Get all local agents"""

- Line 217: `            logger.info(f"api封装器发送参数 {kwargs_str}到{business_func.__name__}")`
  - Translation:             logger.info(f"API wrapper sends parameters {kwargs_str} to {business_func.__name__}")

