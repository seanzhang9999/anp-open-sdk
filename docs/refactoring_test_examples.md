# ANP Open SDK 重构测试代码示例

本文档提供了重构过程中具体的测试代码示例，帮助开发者理解如何编写有效的测试来保证重构质量。

## 1. 基线测试示例

### 1.1 当前认证流程基线测试

```python
# test/baseline/test_authentication_baseline.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from anp_open_sdk.auth.auth_client import agent_auth_request
from anp_open_sdk.anp_sdk_agent import LocalAgent

class TestAuthenticationBaseline:
    """认证流程基线测试 - 记录重构前的行为"""
    
    @pytest.fixture
    def sample_did_data(self):
        """测试用的DID数据"""
        return {
            "caller_did": "did:wba:localhost%3A9527:wba:user:test_caller",
            "target_did": "did:wba:localhost%3A9528:wba:user:test_target",
            "request_url": "http://localhost:9528/api/test"
        }
    
    @pytest.mark.asyncio
    async def test_successful_authentication_flow(self, sample_did_data):
        """测试成功的认证流程"""
        with patch('aiohttp.ClientSession') as mock_session:
            # 模拟成功的HTTP响应
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json.return_value = asyncio.coroutine(
                lambda: {"access_token": "test_token", "token_type": "bearer"}
            )()
            mock_response.headers = {"Authorization": "Bearer test_token"}
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # 执行认证请求
            status, response_data, message, success = await agent_auth_request(
                caller_agent=sample_did_data["caller_did"],
                target_agent=sample_did_data["target_did"],
                request_url=sample_did_data["request_url"],
                method="POST",
                json_data={"test": "data"}
            )
            
            # 验证基线行为
            assert status == 200
            assert success is True
            assert "test_token" in str(response_data)
            
    @pytest.mark.asyncio
    async def test_authentication_failure_scenarios(self, sample_did_data):
        """测试认证失败场景"""
        failure_scenarios = [
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (500, "Internal Server Error")
        ]
        
        for status_code, error_message in failure_scenarios:
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = MagicMock()
                mock_response.status = status_code
                mock_response.text.return_value = asyncio.coroutine(
                    lambda: error_message
                )()
                
                mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
                
                status, response_data, message, success = await agent_auth_request(
                    caller_agent=sample_did_data["caller_did"],
                    target_agent=sample_did_data["target_did"],
                    request_url=sample_did_data["request_url"]
                )
                
                # 记录失败场景的基线行为
                assert status == status_code
                assert success is False
                assert error_message in str(response_data)

    def test_local_agent_creation_baseline(self):
        """测试LocalAgent创建的基线行为"""
        # 这个测试记录当前LocalAgent的创建行为
        # 重构后需要保持相同的外部接口
        try:
            agent = LocalAgent.from_did("did:wba:localhost%3A9527:wba:user:test")
            
            # 记录当前的属性和方法
            expected_attributes = ['id', 'name', 'user_data', 'contact_manager']
            for attr in expected_attributes:
                assert hasattr(agent, attr), f"LocalAgent应该有{attr}属性"
                
            expected_methods = ['expose_api', 'register_message_handler', 'handle_request']
            for method in expected_methods:
                assert hasattr(agent, method), f"LocalAgent应该有{method}方法"
                assert callable(getattr(agent, method)), f"{method}应该是可调用的"
                
        except Exception as e:
            # 记录当前的异常行为
            pytest.fail(f"LocalAgent创建失败: {e}")
```

### 1.2 文件操作基线测试

```python
# test/baseline/test_file_operations_baseline.py
import pytest
import tempfile
import json
from pathlib import Path
from anp_open_sdk.auth.auth_server import LocalFileDIDResolver

class TestFileOperationsBaseline:
    """文件操作基线测试"""
    
    @pytest.fixture
    def temp_did_document(self):
        """创建临时DID文档"""
        did_doc = {
            "id": "did:wba:localhost%3A8000:test:user:12345678",
            "verificationMethod": [{
                "id": "did:wba:localhost%3A8000:test:user:12345678#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": "did:wba:localhost%3A8000:test:user:12345678",
                "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(did_doc, f)
            temp_path = f.name
            
        yield temp_path, did_doc
        
        # 清理
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_local_file_did_resolver_baseline(self, temp_did_document):
        """测试本地文件DID解析器的基线行为"""
        temp_path, expected_doc = temp_did_document
        
        # 模拟LocalAgent.from_did的行为
        with patch('anp_open_sdk.anp_sdk_agent.LocalAgent.from_did') as mock_from_did:
            mock_agent = MagicMock()
            mock_agent.did_document_path = temp_path
            mock_from_did.return_value = mock_agent
            
            resolver = LocalFileDIDResolver()
            result = await resolver.resolve_did_document(expected_doc["id"])
            
            # 验证基线行为
            assert result is not None
            assert result.id == expected_doc["id"]
            assert len(result.verificationMethod) == 1
            assert result.verificationMethod[0]["type"] == "Ed25519VerificationKey2020"
```

## 2. 单元测试示例

### 2.1 纯认证器测试

```python
# test/unit/sdk/test_pure_wba_authenticator.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from anp_open_sdk.auth.pure_wba_authenticator import PureWBADIDAuthenticator
from anp_open_sdk.auth.schemas import AuthenticationContext, DIDCredentials, DIDDocument, DIDKeyPair
from anp_open_sdk.core.base_transport import RequestContext, ResponseContext

class TestPureWBADIDAuthenticator:
    """纯WBA认证器测试"""
    
    @pytest.fixture
    def mock_resolver(self):
        """模拟DID解析器"""
        resolver = Mock()
        resolver.resolve_did_document = AsyncMock()
        resolver.supports_did_method = Mock(return_value=True)
        return resolver
    
    @pytest.fixture
    def mock_transport(self):
        """模拟传输层"""
        transport = Mock()
        transport.send = AsyncMock()
        return transport
    
    @pytest.fixture
    def mock_signer(self):
        """模拟签名器"""
        signer = Mock()
        signer.sign_payload = Mock(return_value="mock_signature")
        signer.verify_signature = Mock(return_value=True)
        return signer
    
    @pytest.fixture
    def mock_header_builder(self):
        """模拟认证头构建器"""
        builder = Mock()
        builder.build_auth_header = Mock(return_value={
            "Authorization": "DID-WBA-V1-ED25519 did=\"test_did\",nonce=\"test_nonce\",timestamp=\"2024-01-01T00:00:00Z\",signature=\"test_signature\""
        })
        return builder
    
    @pytest.fixture
    def authenticator(self, mock_resolver, mock_transport, mock_signer, mock_header_builder):
        """创建纯认证器实例"""
        return PureWBADIDAuthenticator(
            resolver=mock_resolver,
            transport=mock_transport,
            signer=mock_signer,
            header_builder=mock_header_builder
        )
    
    @pytest.fixture
    def sample_context(self):
        """示例认证上下文"""
        return AuthenticationContext(
            caller_did="did:wba:localhost%3A8000:test:caller:12345678",
            target_did="did:wba:localhost%3A8000:test:target:87654321",
            request_url="http://localhost:8000/api/test",
            method="POST",
            json_data={"test": "data"},
            use_two_way_auth=True
        )
    
    @pytest.fixture
    def sample_credentials(self):
        """示例DID凭证"""
        did_doc = DIDDocument(
            id="did:wba:localhost%3A8000:test:caller:12345678",
            verificationMethod=[{
                "id": "did:wba:localhost%3A8000:test:caller:12345678#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": "did:wba:localhost%3A8000:test:caller:12345678",
                "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
            }],
            raw_document={}
        )
        
        key_pair = DIDKeyPair(
            key_id="key-1",
            private_key=b"mock_private_key",
            public_key=b"mock_public_key"
        )
        
        return DIDCredentials(
            did="did:wba:localhost%3A8000:test:caller:12345678",
            did_document=did_doc,
            key_pairs={"key-1": key_pair}
        )
    
    @pytest.mark.asyncio
    async def test_authenticate_request_success(
        self, 
        authenticator, 
        sample_context, 
        sample_credentials,
        mock_transport,
        mock_header_builder
    ):
        """测试成功的认证请求"""
        # 设置传输层返回成功响应
        mock_transport.send.return_value = ResponseContext(
            status_code=200,
            headers={"Authorization": "Bearer success_token"},
            json_data={"result": "success"}
        )
        
        # 执行认证
        success, message, data = await authenticator.authenticate_request(
            sample_context, 
            sample_credentials
        )
        
        # 验证结果
        assert success is True
        assert "success_token" in message
        assert data["result"] == "success"
        
        # 验证调用
        mock_header_builder.build_auth_header.assert_called_once_with(
            sample_context, 
            sample_credentials
        )
        mock_transport.send.assert_called_once()
        
        # 验证传输请求的内容
        call_args = mock_transport.send.call_args[0][0]
        assert isinstance(call_args, RequestContext)
        assert call_args.method == "POST"
        assert call_args.url == "http://localhost:8000/api/test"
        assert "Authorization" in call_args.headers
    
    @pytest.mark.asyncio
    async def test_authenticate_request_network_error(
        self,
        authenticator,
        sample_context,
        sample_credentials,
        mock_transport
    ):
        """测试网络错误场景"""
        # 设置传输层抛出异常
        mock_transport.send.side_effect = Exception("Network error")
        
        # 执行认证
        success, message, data = await authenticator.authenticate_request(
            sample_context,
            sample_credentials
        )
        
        # 验证错误处理
        assert success is False
        assert "Network error" in message
        assert "error" in data
    
    @pytest.mark.asyncio
    async def test_authenticate_request_invalid_credentials(
        self,
        authenticator,
        sample_context,
        mock_header_builder
    ):
        """测试无效凭证场景"""
        # 设置认证头构建器抛出异常
        mock_header_builder.build_auth_header.side_effect = ValueError("Invalid credentials")
        
        invalid_credentials = DIDCredentials(
            did="invalid:did",
            did_document=None,
            key_pairs={}
        )
        
        # 执行认证
        success, message, data = await authenticator.authenticate_request(
            sample_context,
            invalid_credentials
        )
        
        # 验证错误处理
        assert success is False
        assert "Invalid credentials" in message
    
    def test_authenticator_initialization(self, mock_resolver, mock_transport, mock_signer, mock_header_builder):
        """测试认证器初始化"""
        authenticator = PureWBADIDAuthenticator(
            resolver=mock_resolver,
            transport=mock_transport,
            signer=mock_signer,
            header_builder=mock_header_builder
        )
        
        assert authenticator.resolver == mock_resolver
        assert authenticator.transport == mock_transport
        assert authenticator.signer == mock_signer
        assert authenticator.header_builder == mock_header_builder
    
    def test_authenticator_initialization_missing_dependencies(self):
        """测试缺少依赖的初始化"""
        with pytest.raises(TypeError):
            PureWBADIDAuthenticator()  # 缺少必需参数
```

### 2.2 接口契约测试

```python
# test/unit/interfaces/test_interface_contracts.py
import pytest
from abc import ABC, abstractmethod
from anp_open_sdk.core.base_transport import BaseTransport, RequestContext, ResponseContext
from anp_open_sdk.auth.did_auth_base import BaseDIDResolver, BaseDIDAuthenticator

class TestInterfaceContracts:
    """接口契约测试"""
    
    def test_base_transport_interface_definition(self):
        """测试BaseTransport接口定义"""
        # 验证是抽象基类
        assert issubclass(BaseTransport, ABC)
        
        # 验证抽象方法
        assert hasattr(BaseTransport, 'send')
        assert BaseTransport.send.__isabstractmethod__
        
        # 验证方法签名
        import inspect
        sig = inspect.signature(BaseTransport.send)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'request' in params
    
    def test_base_did_resolver_interface_definition(self):
        """测试BaseDIDResolver接口定义"""
        assert issubclass(BaseDIDResolver, ABC)
        
        # 验证抽象方法
        required_methods = ['resolve_did_document', 'supports_did_method']
        for method_name in required_methods:
            assert hasattr(BaseDIDResolver, method_name)
            method = getattr(BaseDIDResolver, method_name)
            assert method.__isabstractmethod__
    
    def test_request_context_data_class(self):
        """测试RequestContext数据类"""
        context = RequestContext(
            method="POST",
            url="http://example.com",
            headers={"Content-Type": "application/json"},
            json_data={"test": "data"}
        )
        
        assert context.method == "POST"
        assert context.url == "http://example.com"
        assert context.headers["Content-Type"] == "application/json"
        assert context.json_data["test"] == "data"
    
    def test_response_context_data_class(self):
        """测试ResponseContext数据类"""
        context = ResponseContext(
            status_code=200,
            headers={"Content-Type": "application/json"},
            json_data={"result": "success"}
        )
        
        assert context.status_code == 200
        assert context.headers["Content-Type"] == "application/json"
        assert context.json_data["result"] == "success"
    
    def test_interface_implementation_requirements(self):
        """测试接口实现要求"""
        # 创建一个不完整的实现
        class IncompleteTransport(BaseTransport):
            pass  # 没有实现send方法
        
        # 验证不能实例化不完整的实现
        with pytest.raises(TypeError):
            IncompleteTransport()
        
        # 创建完整的实现
        class CompleteTransport(BaseTransport):
            async def send(self, request: RequestContext) -> ResponseContext:
                return ResponseContext(
                    status_code=200,
                    headers={},
                    json_data={}
                )
        
        # 验证可以实例化完整的实现
        transport = CompleteTransport()
        assert isinstance(transport, BaseTransport)
```

## 3. 集成测试示例

### 3.1 层间集成测试

```python
# test/integration/test_sdk_framework_integration.py
import pytest
from unittest.mock import patch, MagicMock
from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager

class TestSDKFrameworkIntegration:
    """SDK和框架层集成测试"""
    
    @pytest.fixture
    def mock_user_data_manager(self):
        """模拟用户数据管理器"""
        manager = MagicMock(spec=LocalUserDataManager)
        
        # 模拟用户数据
        mock_user_data = MagicMock()
        mock_user_data.get_did.return_value = "did:wba:localhost%3A8000:test:user:12345678"
        mock_user_data.get_memory_credentials.return_value = MagicMock()
        
        manager.get_user_data.return_value = mock_user_data
        return manager
    
    @pytest.fixture
    def mock_http_transport(self):
        """模拟HTTP传输"""
        transport = MagicMock(spec=HttpTransport)
        return transport
    
    @pytest.fixture
    def framework_auth_manager(self, mock_user_data_manager, mock_http_transport):
        """创建框架认证管理器"""
        return FrameworkAuthManager(
            user_data_manager=mock_user_data_manager,
            transport=mock_http_transport
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_authentication_flow(
        self,
        framework_auth_manager,
        mock_http_transport,
        mock_user_data_manager
    ):
        """端到端认证流程测试"""
        # 设置HTTP传输返回成功响应
        from anp_open_sdk.core.base_transport import ResponseContext
        mock_http_transport.send.return_value = ResponseContext(
            status_code=200,
            headers={"Authorization": "Bearer test_token"},
            json_data={"result": "success"}
        )
        
        # 执行认证请求
        result = await framework_auth_manager.authenticated_request(
            caller_agent="did:wba:localhost%3A8000:test:caller:12345678",
            target_agent="did:wba:localhost%3A8000:test:target:87654321",
            request_url="http://localhost:8000/api/test",
            method="POST",
            json_data={"test": "data"}
        )
        
        # 验证结果
        assert result is not None
        status, response_data, message, success = result
        assert status == 200
        assert success is True
        assert "test_token" in str(response_data)
        
        # 验证调用链
        mock_user_data_manager.get_user_data.assert_called()
        mock_http_transport.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_with_missing_user_data(
        self,
        framework_auth_manager,
        mock_user_data_manager
    ):
        """测试用户数据缺失的认证"""
        # 设置用户数据管理器返回None
        mock_user_data_manager.get_user_data.return_value = None
        
        # 执行认证请求
        result = await framework_auth_manager.authenticated_request(
            caller_agent="did:wba:localhost%3A8000:test:nonexistent:12345678",
            target_agent="did:wba:localhost%3A8000:test:target:87654321",
            request_url="http://localhost:8000/api/test"
        )
        
        # 验证错误处理
        assert result is not None
        status, response_data, message, success = result
        assert status == 500
        assert success is False
        assert "用户数据" in message or "user data" in message.lower()
    
    def test_framework_components_integration(
        self,
        mock_user_data_manager,
        mock_http_transport
    ):
        """测试框架组件集成"""
        # 验证组件可以正确组装
        auth_manager = FrameworkAuthManager(
            user_data_manager=mock_user_data_manager,
            transport=mock_http_transport
        )
        
        assert auth_manager.user_data_manager == mock_user_data_manager
        assert auth_manager.transport == mock_http_transport
        
        # 验证组件接口兼容性
        assert hasattr(mock_user_data_manager, 'get_user_data')
        assert hasattr(mock_http_transport, 'send')
```

### 3.2 向后兼容性测试

```python
# test/integration/test_backward_compatibility.py
import pytest
import warnings
from unittest.mock import patch, MagicMock
from anp_open_sdk.auth.auth_client import agent_auth_request

class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_deprecated_auth_client_functionality(self):
        """测试废弃的auth_client功能"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 模拟框架组件
            with patch('anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data.LocalUserDataManager') as mock_manager_class:
                with patch('anp_open_sdk_framework.adapter_transport.http_transport.HttpTransport') as mock_transport_class:
                    with patch('anp_open_sdk_framework.adapter_auth.framework_auth.FrameworkAuthManager') as mock_auth_class:
                        with patch('anp_open_sdk_framework.auth.auth_client.AuthClient') as mock_client_class:
                            
                            # 设置mock返回值
                            mock_client = MagicMock()
                            mock_client.authenticated_request.return_value = (200, {"result": "success"}, "Success", True)
                            mock_client_class.return_value = mock_client
                            
                            # 调用废弃的函数
                            result = await agent_auth_request(
                                caller_agent="did:wba:localhost%3A8000:test:caller:12345678",
                                target_agent="did:wba:localhost%3A8000:test:target:87654321",
                                request_url="http://localhost:8000/api/test",
                                method="POST",
                                json_data={"test": "data"}
                            )
                            
                            # 验证警告被触发
                            assert len(w) >= 1
                            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
                            assert len(deprecation_warnings) >= 1
                            assert "deprecated" in str(deprecation_warnings[0].message).lower()
                            
                            # 验证功能仍然工作
                            assert result is not None
                            status, response_data, message, success = result
                            assert status == 200
                            assert success is True
                            assert response_data["result"] == "success"
    
    def test_api_interface_compatibility(self):
        """测试API接口兼容性"""
        # 验证重要的类和函数仍然可以导入
        try:
            from anp_open_sdk.anp_sdk_agent import LocalAgent, RemoteAgent
            from anp_open_sdk.auth.auth_client import agent_auth_request
            from anp_open_sdk.auth.auth_server import AgentAuthServer
            from anp_open_sdk.contact_manager import ContactManager
        except ImportError as e:
            pytest.fail(f"重要的API无法导入: {e}")
        
        # 验证类的基本接口
        assert hasattr(LocalAgent, 'from_did')
        assert hasattr(LocalAgent, 'expose_api')
        assert hasattr(LocalAgent, 'register_message_handler')
        
        assert hasattr(RemoteAgent, 'to_dict')
        
        assert callable(agent_auth_request)
    
    @pytest.mark.asyncio
    async def test_configuration_compatibility(self):
        """测试配置兼容性"""
        # 验证配置系统仍然工作
        try:
            from anp_open_sdk.config import get_global_config
            config = get_global_config()
            
            # 验证重要的配置项仍然存在
            assert hasattr(config, 'anp_sdk')
            assert hasattr(config.anp_sdk, 'user_did_path')
            assert hasattr(config.anp_sdk, 'jwt_algorithm')
            
        except Exception as e:
            pytest.fail(f"配置系统不兼容: {e}")
```

## 4. 性能测试示例

### 4.1 性能回归测试

```python
# test/performance/test_performance_regression.py
import pytest
import time
import asyncio
import statistics
from unittest.mock import patch, MagicMock
from anp_open_sdk.auth.auth_client import agent_auth_request

class TestPerformanceRegression:
    """性能回归测试"""
    
    @pytest.fixture
    def performance_test_data(self):
        """性能测试数据"""
        return {
            "caller_did": "did:wba:localhost%3A8000:test:caller:12345678",
            "target_did": "did:wba:localhost%3A8000:test:target:87654321",
            "request_url": "http://localhost:8000/api/test",
            "test_data": {"test": "performance_data"}
        }
    
    @pytest.mark.asyncio
    async def test_authentication_latency(self, performance_test_data):
        """测试认证延迟"""
        with patch('anp_open_sdk_framework.auth.auth_client.AuthClient') as mock_client_class:
            # 模拟快速响应
            mock_client = MagicMock()
            mock_client.authenticated_request.return_value = (200, {"result": "success"}, "Success", True)
            mock_client_class.return_value = mock_client
            
            # 执行多次测试并测量时间
            latencies = []
            for _ in range(10):
                start_time = time.time()
                
                await agent_auth_request(
                    caller_agent=performance_test_data["caller_did"],
                    target_agent=performance_test_data["target_did"],
                    request_url=performance_test_data["request_url"],
                    json_data=performance_test_data["test_data"]
                )
                
                end_time = time.time()
                latencies.append(end_time - start_time)
            
            # 分析性能指标
            avg_latency = statistics.mean(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            # 性能断言（根据实际需求调整阈值）
            assert avg_latency < 0.1, f"平均延迟过高: {avg_latency:.3f}s"
            assert max_latency < 0.2, f"最大延迟过高: {max_latency:.3f}s"
            
            print(f"性能指标 - 平均: {avg_latency:.3f}s, 最大: {max_latency:.3f}s, 最小: {min_latency:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_throughput(self, performance_test_data):
        """测试并发认证吞吐量"""
        with patch('anp_open_sdk_framework.auth.auth_client.AuthClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.authenticated_request.return_value = (200, {"result": "success"}, "Success", True)
            mock_client_class.return_value = mock_client
            
            # 并发测试
            concurrent_requests = 20
            start_time = time.time()
            
            tasks = []
            for i in range(concurrent_requests):
                task = agent_auth_request(
                    caller_agent=f"{performance_test_data['caller_did']}_{i}",
                    target_agent=performance_test_data["target_did"],
                    request_url=performance_test_data["request_url"],
                    json_data=performance_test_data["test_data"]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # 分析结果
            successful_requests = sum(1 for result in results if not isinstance(result, Exception))
            total_time = end_time - start_time
            throughput = successful_requests / total_time
            
            # 性能断言
            assert successful_requests == concurrent_requests, f"部分请求失败: {successful_requests}/{concurrent_requests}"
            assert throughput > 50, f"吞吐量过低: {throughput:.2f} requests/second"
            
            print(f"并发性能 - 成功请求: {successful_requests}, 总时间: {total_time:.3f}s, 吞吐量: {throughput:.2f} req/s")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, performance_test_data):
        """测试内存使用稳定性"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with patch('anp_open_sdk_framework.auth.auth_client.AuthClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.authenticated_request.return_value = (200, {"result": "success"}, "Success", True)
            mock_client_class.return_value = mock_client
            
            # 执行大量请求
            for i in range(100):
                await agent_auth_request(
                    caller_agent=f"{performance_test_data['caller_did']}_{i}",
                    target_agent=performance_test_data["target_did"],
                    request_url=performance_test_data["request_url"],
                    json_data=performance_test_data["test_data"]
                )
                
                # 每10次请求检查一次内存
                if i % 10 == 0:
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    
                    # 内存增长不应超过50MB
                    assert memory_increase < 50 * 1024 * 1024, f"内存泄漏检测: 增长了 {memory_increase / 1024 / 1024:.2f}MB"
        
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        print(f"内存使用 - 初始: {initial_memory / 1024 / 1024:.2f}MB, 最终: {final_memory / 1024 / 1024:.2f}MB, 增长: {total_increase / 1024 / 1024:.2f}MB")
```

## 5. 测试工具和辅助函数

### 5.1 测试数据工厂

```python
# test/utils/test_data_factory.py
import secrets
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from anp_open_sdk.auth.schemas import DIDDocument, DIDCredentials, DIDKeyPair, AuthenticationContext

class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_test_did(
        host: str = "localhost",
        port: int = 8000,
        path: str = "test",
        user_type: str = "user",
        unique_id: Optional[str] = None
    ) -> str:
        """创建测试用DID"""
        if unique_id is None:
            unique_id = secrets.token_hex(8)
        
        return f"did:wba:{host}%3A{port}:{path}:{user_type}:{unique_id}"
    
    @staticmethod
    def create_test_did_document(did: str) -> DIDDocument:
        """创建测试用DID文档"""
        verification_method = {
            "id": f"{did}#key-1",
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        }
        
        raw_document = {
            "id": did,
            "verificationMethod": [verification_method],
            "authentication": [verification_method["id"]],
            "assertionMethod": [verification_method["id"]]
        }
        
        return DIDDocument(
            id=did,
            verificationMethod=[verification_method],
            authentication=[verification_method["id"]],
            assertionMethod=[verification_method["id"]],
            raw_document=raw_document
        )
    
    @staticmethod
    def create_test_key_pair(key_id: str = "key-1") -> DIDKeyPair:
        """创建测试用密钥对"""
        # 这里使用模拟的密钥数据，实际测试中应该使用真实的密钥生成
        return DIDKeyPair(
            key_id=key_id,
            private_key=b"mock_private_key_32_bytes_long_test",
            public_key=b"mock_public_key_32_bytes_long_test"
        )
    
    @staticmethod
    def create_test_credentials(did: str) -> DIDCredentials:
        """创建测试用凭证"""
        did_document = TestDataFactory.create_test_did_document(did)
        key_pair = TestDataFactory.create_test_key_pair()
        
        return DIDCredentials(
            did=did,
            did_document=did_document,
            key_pairs={"key-1": key_pair}
        )
    
    @staticmethod
    def create_test_auth_context(
        caller_did: Optional[str] = None,
        target_did: Optional[str] = None,
        request_url: str = "http://localhost:8000/api/test",
        method: str = "POST",
        use_two_way_auth: bool = True
    ) -> AuthenticationContext:
        """创建测试用认证上下文"""
        if caller_did is None:
            caller_did = TestDataFactory.create_test_did(port=8001, unique_id="caller123")
        
        if target_did is None:
            target_did = TestDataFactory.create_test_did(port=8002, unique_id="target456")
        
        return AuthenticationContext(
            caller_did=caller_did,
            target_did=target_did,
            request_url=request_url,
            method=method,
            json_data={"test": "data"},
            use_two_way_auth=use_two_way_auth,
            domain="localhost"
        )
    
    @staticmethod
    def create_test_response_data(
        status_code: int = 200,
        include_token: bool = True,
        include_auth_header: bool = False
    ) -> Dict[str, Any]:
        """创建测试用响应数据"""
        response_data = {
            "result": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if include_token:
            response_data["access_token"] = f"test_token_{secrets.token_hex(8)}"
            response_data["token_type"] = "bearer"
        
        if include_auth_header:
            response_data["resp_did_auth_header"] = {
                "Authorization": "DID-WBA-V1-ED25519 did=\"test_did\",nonce=\"test_nonce\",timestamp=\"2024-01-01T00:00:00Z\",signature=\"test_signature\""
            }
        
        return response_data
```

### 5.2 Mock助手

```python
# test/utils/mock_helpers.py
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Any, Dict, Optional
from anp_open_sdk.core.base_transport import ResponseContext
from anp_open_sdk.auth.schemas import DIDDocument

class MockHelpers:
    """Mock助手类"""
    
    @staticmethod
    def create_mock_transport(
        status_code: int = 200,
        response_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """创建模拟传输层"""
        transport = Mock()
        
        if response_data is None:
            response_data = {"result": "success"}
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
        
        transport.send = AsyncMock(return_value=ResponseContext(
            status_code=status_code,
            headers=headers,
            json_data=response_data
        ))
        
        return transport
    
    @staticmethod
    def create_mock_resolver(did_documents: Optional[Dict[str, DIDDocument]] = None):
        """创建模拟DID解析器"""
        resolver = Mock()
        
        if did_documents is None:
            did_documents = {}
        
        async def mock_resolve(did: str) -> Optional[DIDDocument]:
            return did_documents.get(did)
        
        resolver.resolve_did_document = AsyncMock(side_effect=mock_resolve)
        resolver.supports_did_method = Mock(return_value=True)
        
        return resolver
    
    @staticmethod
    def create_mock_user_data_manager(user_data_map: Optional[Dict[str, Any]] = None):
        """创建模拟用户数据管理器"""
        manager = Mock()
        
        if user_data_map is None:
            user_data_map = {}
        
        def mock_get_user_data(did: str):
            return user_data_map.get(did)
        
        manager.get_user_data = Mock(side_effect=mock_get_user_data)
        manager.get_all_users = Mock(return_value=list(user_data_map.values()))
        
        return manager
    
    @staticmethod
    def create_mock_auth_server(verify_result: tuple = (True, "Success", None)):
        """创建模拟认证服务器"""
        auth_server = Mock()
        auth_server.verify_request = AsyncMock(return_value=verify_result)
        return auth_server
    
    @staticmethod
    def setup_aiohttp_mock(mock_session, responses: list):
        """设置aiohttp模拟"""
        mock_responses = []
        
        for response_config in responses:
            mock_response = MagicMock()
            mock_response.status = response_config.get('status', 200)
            mock_response.headers = response_config.get('headers', {})
            
            if 'json_data' in response_config:
                mock_response.json = AsyncMock(return_value=response_config['json_data'])
            
            if 'text_data' in response_config:
                mock_response.text = AsyncMock(return_value=response_config['text_data'])
            
            mock_responses.append(mock_response)
        
        # 设置session的上下文管理器
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.side_effect = mock_responses
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.side_effect = mock_responses
```

这些测试示例提供了全面的测试覆盖，确保重构过程中的质量和稳定性。每个测试都有明确的目的和验证点，帮助开发者理解如何编写有效的测试来支持重构工作。
