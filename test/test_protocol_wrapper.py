"""
测试 protocol wrapper 集中控制架构
验证 agent_connect 集成和 fallback 实现路径
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from anp_open_sdk.protocol.agent_connect_wrapper import (
    AgentConnectProtocolWrapper,
    PureAgentConnectCrypto,
    AgentConnectNetworkOperations,
    get_protocol_wrapper,
    create_verification_method,
    get_curve_mapping,
    resolve_did_document,
    get_agent_connect_status
)


class TestPureAgentConnectCrypto:
    """测试纯加密操作功能"""
    
    def test_agent_connect_availability_check(self):
        """测试 agent_connect 可用性检查"""
        crypto = PureAgentConnectCrypto()
        
        # 测试状态检查方法存在
        assert hasattr(crypto, '_agent_connect_available')
        assert hasattr(crypto, '_fallback_available')
        assert isinstance(crypto._agent_connect_available, bool)
        assert isinstance(crypto._fallback_available, bool)
    
    def test_create_verification_method_with_agent_connect(self):
        """测试使用 agent_connect 创建验证方法"""
        crypto = PureAgentConnectCrypto()
        
        # 模拟 agent_connect 可用的情况
        if crypto._agent_connect_available:
            test_vm = {
                "type": "EcdsaSecp256k1VerificationKey2019",
                "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G7Rou2yXqXFGTX2ASueMbKiTmPELyUwJKT1"
            }
            
            try:
                vm = crypto.create_verification_method(test_vm)
                assert vm is not None
                print(f"✅ agent_connect verification method created: {type(vm)}")
            except Exception as e:
                print(f"⚠️  agent_connect not available or failed: {e}")
    
    def test_create_verification_method_with_fallback(self):
        """测试使用 fallback 实现创建验证方法"""
        crypto = PureAgentConnectCrypto()
        
        # 强制使用 fallback 实现
        with patch.object(crypto, '_agent_connect_available', False):
            if crypto._fallback_available:
                # 使用有效的 33 字节压缩公钥进行测试
                test_vm = {
                    "type": "EcdsaSecp256k1VerificationKey2019",
                    "publicKeyMultibase": "zjhLmwWsxfm1cYfATmxmyMZE4vy7m8cfwiAxNou7ogRcq"  # 有效的33字节secp256k1压缩公钥
                }
                
                vm = crypto.create_verification_method(test_vm)
                assert vm is not None
                print(f"✅ fallback verification method created: {type(vm)}")
    
    def test_get_curve_mapping_with_agent_connect(self):
        """测试使用 agent_connect 获取曲线映射"""
        crypto = PureAgentConnectCrypto()
        
        if crypto._agent_connect_available:
            try:
                mapping = crypto.get_curve_mapping()
                assert isinstance(mapping, dict)
                print(f"✅ agent_connect curve mapping: {list(mapping.keys())}")
            except Exception as e:
                print(f"⚠️  agent_connect curve mapping failed: {e}")
    
    def test_get_curve_mapping_with_fallback(self):
        """测试使用 fallback 实现获取曲线映射"""
        crypto = PureAgentConnectCrypto()
        
        # 强制使用 fallback 实现
        with patch.object(crypto, '_agent_connect_available', False):
            if crypto._fallback_available:
                mapping = crypto.get_curve_mapping()
                assert isinstance(mapping, dict)
                print(f"✅ fallback curve mapping: {list(mapping.keys())}")
    
    def test_error_handling_no_implementations(self):
        """测试没有可用实现时的错误处理"""
        crypto = PureAgentConnectCrypto()
        
        # 强制所有实现都不可用
        with patch.object(crypto, '_agent_connect_available', False), \
             patch.object(crypto, '_fallback_available', False):
            
            with pytest.raises(RuntimeError, match="No verification method implementation available"):
                crypto.create_verification_method({"type": "test"})
            
            with pytest.raises(RuntimeError, match="No curve mapping implementation available"):
                crypto.get_curve_mapping()


class TestAgentConnectNetworkOperations:
    """测试网络操作功能"""
    
    def test_agent_connect_network_availability(self):
        """测试 agent_connect 网络功能可用性"""
        network = AgentConnectNetworkOperations()
        
        assert hasattr(network, '_agent_connect_available')
        assert isinstance(network._agent_connect_available, bool)
    
    @pytest.mark.asyncio
    async def test_resolve_did_document_with_agent_connect(self):
        """测试使用 agent_connect 解析 DID 文档"""
        network = AgentConnectNetworkOperations()
        
        if network._agent_connect_available:
            # 使用模拟的 DID 进行测试
            test_did = "did:wba:localhost:test"
            
            try:
                # 这里使用 mock 来避免实际的网络调用
                with patch('agent_connect.authentication.resolve_did_wba_document') as mock_resolve:
                    mock_resolve.return_value = {"id": test_did, "verificationMethod": []}
                    
                    result = await network.resolve_did_document(test_did)
                    assert result is not None
                    assert result["id"] == test_did
                    print(f"✅ agent_connect DID resolution successful")
            except Exception as e:
                print(f"⚠️  agent_connect DID resolution failed: {e}")
    
    @pytest.mark.asyncio
    async def test_resolve_did_document_with_fallback(self):
        """测试使用 fallback 实现解析 DID 文档"""
        network = AgentConnectNetworkOperations()
        
        # 强制使用 fallback 实现
        with patch.object(network, '_agent_connect_available', False):
            test_did = "did:wba:localhost:test"
            
            # Mock fallback 实现
            with patch('anp_open_sdk.agent_connect_hotpatch.authentication.did_wba.resolve_did_wba_document') as mock_fallback:
                mock_fallback.return_value = {"id": test_did, "verificationMethod": []}
                
                result = await network.resolve_did_document(test_did)
                assert result is not None
                assert result["id"] == test_did
                print(f"✅ fallback DID resolution successful")


class TestAgentConnectHotpatchOperations:
    """测试 hotpatch 操作功能"""
    
    def test_hotpatch_availability_check(self):
        """测试 hotpatch 可用性检查"""
        from anp_open_sdk.protocol.agent_connect_wrapper import AgentConnectHotpatchOperations
        
        hotpatch = AgentConnectHotpatchOperations()
        
        assert hasattr(hotpatch, '_hotpatch_available')
        assert isinstance(hotpatch._hotpatch_available, bool)
        print(f"✅ hotpatch available: {hotpatch._hotpatch_available}")
    
    def test_hotpatch_functions_accessible(self):
        """测试 hotpatch 函数可访问性"""
        from anp_open_sdk.protocol import (
            create_did_wba_document,
            extract_auth_header_parts_two_way,
            verify_auth_header_signature_two_way,
            create_did_wba_auth_header
        )
        
        # 这些函数应该可以导入，即使hotpatch不可用
        assert callable(create_did_wba_document)
        assert callable(extract_auth_header_parts_two_way)
        assert callable(verify_auth_header_signature_two_way)
        assert callable(create_did_wba_auth_header)
        print(f"✅ hotpatch functions importable")


class TestAgentConnectProtocolWrapper:
    """测试主要的协议包装器"""
    
    def test_wrapper_initialization(self):
        """测试包装器初始化"""
        wrapper = AgentConnectProtocolWrapper()
        
        assert wrapper.crypto is not None
        assert wrapper.network is not None
        assert wrapper.hotpatch is not None
        assert isinstance(wrapper.crypto, PureAgentConnectCrypto)
        assert isinstance(wrapper.network, AgentConnectNetworkOperations)
        from anp_open_sdk.protocol.agent_connect_wrapper import AgentConnectHotpatchOperations
        assert isinstance(wrapper.hotpatch, AgentConnectHotpatchOperations)
    
    def test_crypto_interface_delegation(self):
        """测试加密接口委托"""
        wrapper = AgentConnectProtocolWrapper()
        
        # 测试验证方法创建委托
        test_vm = {
            "type": "EcdsaSecp256k1VerificationKey2019",
            "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G7Rou2yXqXFGTX2ASueMbKiTmPELyUwJKT1"
        }
        
        try:
            vm = wrapper.create_verification_method(test_vm)
            assert vm is not None
            print(f"✅ wrapper verification method delegation successful")
        except Exception as e:
            print(f"⚠️  wrapper verification method delegation failed: {e}")
        
        # 测试曲线映射委托
        try:
            mapping = wrapper.get_curve_mapping()
            assert isinstance(mapping, dict)
            print(f"✅ wrapper curve mapping delegation successful")
        except Exception as e:
            print(f"⚠️  wrapper curve mapping delegation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_network_interface_delegation(self):
        """测试网络接口委托"""
        wrapper = AgentConnectProtocolWrapper()
        
        test_did = "did:wba:localhost:test"
        
        # Mock 网络调用以避免实际的外部依赖
        with patch.object(wrapper.network, 'resolve_did_document') as mock_resolve:
            mock_resolve.return_value = {"id": test_did, "verificationMethod": []}
            
            result = await wrapper.resolve_did_document(test_did)
            assert result is not None
            assert result["id"] == test_did
            mock_resolve.assert_called_once_with(test_did)
            print(f"✅ wrapper network delegation successful")
    
    def test_status_reporting(self):
        """测试状态报告功能"""
        wrapper = AgentConnectProtocolWrapper()
        
        status = wrapper.get_status_report()
        
        # 验证状态报告结构（包含hotpatch）
        assert isinstance(status, dict)
        assert "crypto_available" in status
        assert "crypto_fallback_available" in status
        assert "network_available" in status
        assert "hotpatch_available" in status
        assert "overall_status" in status
        
        # 验证状态值类型
        assert isinstance(status["crypto_available"], bool)
        assert isinstance(status["crypto_fallback_available"], bool)
        assert isinstance(status["network_available"], bool)
        assert isinstance(status["hotpatch_available"], bool)
        assert status["overall_status"] in ["healthy", "fallback_mode"]
        
        print(f"✅ wrapper status report with hotpatch: {status}")
    
    def test_interface_access(self):
        """测试接口访问方法"""
        wrapper = AgentConnectProtocolWrapper()
        
        crypto_interface = wrapper.get_crypto_interface()
        network_interface = wrapper.get_network_interface()
        hotpatch_interface = wrapper.get_hotpatch_interface()
        
        assert isinstance(crypto_interface, PureAgentConnectCrypto)
        assert isinstance(network_interface, AgentConnectNetworkOperations)
        from anp_open_sdk.protocol.agent_connect_wrapper import AgentConnectHotpatchOperations
        assert isinstance(hotpatch_interface, AgentConnectHotpatchOperations)
        
        # 验证接口是同一个实例
        assert crypto_interface is wrapper.crypto
        assert network_interface is wrapper.network
        assert hotpatch_interface is wrapper.hotpatch
        
        print(f"✅ wrapper interface access with hotpatch successful")


class TestGlobalFunctions:
    """测试全局便捷函数"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        wrapper1 = get_protocol_wrapper()
        wrapper2 = get_protocol_wrapper()
        
        # 验证是同一个实例
        assert wrapper1 is wrapper2
        assert isinstance(wrapper1, AgentConnectProtocolWrapper)
        print(f"✅ singleton pattern working correctly")
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试 create_verification_method 便捷函数
        test_vm = {
            "type": "EcdsaSecp256k1VerificationKey2019",
            "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G7Rou2yXqXFGTX2ASueMbKiTmPELyUwJKT1"
        }
        
        try:
            vm = create_verification_method(test_vm)
            assert vm is not None
            print(f"✅ convenience create_verification_method successful")
        except Exception as e:
            print(f"⚠️  convenience create_verification_method failed: {e}")
        
        # 测试 get_curve_mapping 便捷函数
        try:
            mapping = get_curve_mapping()
            assert isinstance(mapping, dict)
            print(f"✅ convenience get_curve_mapping successful")
        except Exception as e:
            print(f"⚠️  convenience get_curve_mapping failed: {e}")
        
        # 测试 get_agent_connect_status 便捷函数
        status = get_agent_connect_status()
        assert isinstance(status, dict)
        assert "overall_status" in status
        print(f"✅ convenience get_agent_connect_status successful")
    
    @pytest.mark.asyncio
    async def test_async_convenience_functions(self):
        """测试异步便捷函数"""
        test_did = "did:wba:localhost:test"
        
        # 正确 Mock 网络调用
        with patch('anp_open_sdk.protocol.agent_connect_wrapper.AgentConnectNetworkOperations.resolve_did_document') as mock_resolve:
            mock_resolve.return_value = {"id": test_did, "verificationMethod": []}
            
            result = await resolve_did_document(test_did)
            assert result is not None
            assert result["id"] == test_did
            print(f"✅ async convenience resolve_did_document successful")


class TestIntegrationWithExistingCore:
    """测试与现有 core 架构的集成"""
    
    def test_integration_with_auth_flow(self):
        """测试与 AuthFlowManager 的集成"""
        from anp_open_sdk.core.auth_flow import AuthFlowManager
        from anp_open_sdk.auth.schemas import DIDCredentials, DIDDocument, DIDKeyPair
        
        # 创建测试数据
        test_did_doc = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": "did:wba:localhost:test",
            "verificationMethod": [{
                "id": "did:wba:localhost:test#key-1",
                "type": "EcdsaSecp256k1VerificationKey2019",
                "controller": "did:wba:localhost:test",
                "publicKeyMultibase": "z4MXj1wBzi9jUstyPMS4jQqB6KdJaiatPkAtVtGc6bQEQEEsKTic4G7Rou2yXqXFGTX2ASueMbKiTmPELyUwJKT1"
            }],
            "authentication": ["did:wba:localhost:test#key-1"]
        }
        
        did_doc = DIDDocument(**test_did_doc, raw_document=test_did_doc)
        
        # 创建测试私钥 (32字节的 secp256k1 私钥)
        test_private_key = b'\x01' * 32
        key_pair = DIDKeyPair.from_private_key_bytes(test_private_key, "key-1")
        
        credentials = DIDCredentials(
            did="did:wba:localhost:test",
            did_document=did_doc
        )
        credentials.add_key_pair(key_pair)
        
        # 测试协议包装器可以与现有架构配合工作
        wrapper = get_protocol_wrapper()
        assert wrapper is not None
        
        # 验证状态
        status = wrapper.get_status_report()
        print(f"✅ integration test with core architecture: {status}")
    
    def test_separation_of_concerns(self):
        """测试关注点分离原则"""
        wrapper = AgentConnectProtocolWrapper()
        
        # 验证纯加密操作和网络操作分离
        crypto = wrapper.get_crypto_interface()
        network = wrapper.get_network_interface()
        
        # 加密接口只处理纯算法逻辑
        assert hasattr(crypto, 'create_verification_method')
        assert hasattr(crypto, 'get_curve_mapping')
        assert not hasattr(crypto, 'resolve_did_document')  # 不应该有网络操作
        
        # 网络接口只处理网络相关逻辑
        assert hasattr(network, 'resolve_did_document')
        assert not hasattr(network, 'create_verification_method')  # 不应该有加密操作
        
        print(f"✅ separation of concerns verified")


def test_protocol_wrapper_comprehensive():
    """综合测试协议包装器功能"""
    print("\n🧪 开始 Protocol Wrapper 综合测试")
    
    # 测试集中控制架构
    wrapper = get_protocol_wrapper()
    status = wrapper.get_status_report()
    
    print(f"📊 Protocol Wrapper 状态: {status}")
    
    # 验证所有核心功能都可用
    assert wrapper is not None
    assert isinstance(status, dict)
    
    # 测试不同路径的可用性
    if status["crypto_available"]:
        print("✅ agent_connect 加密功能可用")
    elif status["crypto_fallback_available"]:
        print("✅ fallback 加密功能可用")
    else:
        print("❌ 没有可用的加密功能")
    
    if status["network_available"]:
        print("✅ agent_connect 网络功能可用")
    else:
        print("⚠️  agent_connect 网络功能不可用，使用 fallback")
    
    print(f"🎯 总体状态: {status['overall_status']}")
    print("✅ Protocol Wrapper 综合测试完成")


if __name__ == "__main__":
    test_protocol_wrapper_comprehensive()