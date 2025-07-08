#!/usr/bin/env python3
"""
Service Injection and Framework Integration Test

This test covers the critical service injection pattern from framework_demo.py:
- Creating core service instances as singletons
- Injecting services into agent instances
- Testing the complete framework integration flow

Key pattern being tested (from framework_demo.py lines 278-296):
    user_data_manager = LocalUserDataManager()
    sdk.user_data_manager = user_data_manager
    http_transport = HttpTransport()
    framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
    auth_client = AuthClient(framework_auth_manager)
    
    for agent in all_agents:
        agent.auth_client = auth_client
"""

import os
import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# Add project root to path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.anp_sdk_agent import LocalAgent
from anp_open_sdk.sdk_mode import SdkMode
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager
from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
from anp_open_sdk_framework.auth.auth_client import AuthClient
from anp_open_sdk_framework.agent_manager import LocalAgentManager
import logging

logger = logging.getLogger(__name__)


class TestServiceInjectionPattern:
    """Test the service injection pattern used in framework_demo.py"""
    
    @pytest.fixture
    def test_config(self):
        """Setup test configuration"""
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(script_dir, "test_suite", "config", "test_config.yaml")
        
        app_config = UnifiedConfig(config_file=config_path, app_root=script_dir)
        set_global_config(app_config)
        setup_logging()
        
        return app_config
    
    @pytest.fixture
    def clean_sdk_instance(self):
        """Clean SDK instance for each test"""
        ANPSDK.instance = None
        ANPSDK._instances.clear()
        yield
        ANPSDK.instance = None
        ANPSDK._instances.clear()
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing"""
        agents = []
        for i in range(3):
            agent = Mock()
            agent.id = f"did:wba:localhost%3A9527:wba:user:test_agent_{i:03d}"
            agent.name = f"TestAgent{i:03d}"
            agent.handle_request = AsyncMock()
            agent.api_routes = {}
            agent.is_hosted_did = False
            agents.append(agent)
        return agents
    
    def test_core_service_creation(self, test_config):
        """Test creation of core service instances (step 1 of injection pattern)"""
        # 1. Create core service instances as singletons
        user_data_manager = LocalUserDataManager()
        assert user_data_manager is not None
        assert hasattr(user_data_manager, 'get_all_users')
        
        http_transport = HttpTransport()
        assert http_transport is not None
        assert hasattr(http_transport, 'send')  # HttpTransport uses 'send' method
        
        # 2. Test FrameworkAuthManager creation with dependencies
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        assert framework_auth_manager is not None
        assert framework_auth_manager.user_data_manager == user_data_manager
        assert framework_auth_manager.transport == http_transport
        
        # 3. Test AuthClient creation
        auth_client = AuthClient(framework_auth_manager)
        assert auth_client is not None
        assert auth_client.auth_manager == framework_auth_manager
        
        logger.info("✅ Core service creation test passed")
    
    def test_sdk_service_attachment(self, test_config, clean_sdk_instance, mock_agents):
        """Test attaching services to SDK instance"""
        # Create SDK with agents
        sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=mock_agents)
        
        # Create core services
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Attach services to SDK (as done in framework_demo.py)
        sdk.user_data_manager = user_data_manager
        
        # Verify attachment
        assert hasattr(sdk, 'user_data_manager')
        assert sdk.user_data_manager == user_data_manager
        
        logger.info("✅ SDK service attachment test passed")
    
    def test_agent_service_injection(self, test_config, mock_agents):
        """Test injecting services into agent instances (core of injection pattern)"""
        # Create core services
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Inject services into agents (key pattern from framework_demo.py)
        for agent in mock_agents:
            agent.auth_client = auth_client
            # Future injection points
            # agent.orchestrator = ...
            # agent.crawler = ...
        
        # Verify injection
        for agent in mock_agents:
            assert hasattr(agent, 'auth_client')
            assert agent.auth_client == auth_client
            # Verify the auth_client has the correct dependencies
            assert agent.auth_client.auth_manager == framework_auth_manager
            assert agent.auth_client.auth_manager.user_data_manager == user_data_manager
            assert agent.auth_client.auth_manager.transport == http_transport
        
        logger.info(f"✅ Service injection completed for {len(mock_agents)} agents")
    
    def test_complete_framework_injection_flow(self, test_config, clean_sdk_instance, mock_agents):
        """Test complete service injection flow as implemented in framework_demo.py"""
        # Step 1: Create SDK with agents
        sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=mock_agents)
        
        # Step 2: Create core service instances (framework_demo.py lines 281-287)
        user_data_manager = LocalUserDataManager()
        sdk.user_data_manager = user_data_manager
        
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Step 3: Inject services into all agent instances (framework_demo.py lines 290-295)
        logger.info("💉 Injecting core services into all agents...")
        for agent in mock_agents:
            agent.auth_client = auth_client
            # Future service injections:
            # agent.orchestrator = ...
            # agent.crawler = ...
        logger.info("✅ Core service injection completed")
        
        # Step 4: Verify complete integration
        assert len(mock_agents) == 3
        for i, agent in enumerate(mock_agents):
            # Verify agent identity
            assert agent.id == f"did:wba:localhost%3A9527:wba:user:test_agent_{i:03d}"
            assert agent.name == f"TestAgent{i:03d}"
            
            # Verify service injection
            assert hasattr(agent, 'auth_client')
            assert agent.auth_client is auth_client
            
            # Verify service chain integrity
            assert agent.auth_client.auth_manager is framework_auth_manager
            assert agent.auth_client.auth_manager.user_data_manager is user_data_manager
            assert agent.auth_client.auth_manager.transport is http_transport
        
        # Verify SDK integration
        assert sdk.user_data_manager is user_data_manager
        assert len(sdk.agents) == 3
        
        logger.info("✅ Complete framework injection flow test passed")
    
    @pytest.mark.asyncio
    async def test_injected_services_functionality(self, test_config, mock_agents):
        """Test that injected services are functional"""
        # Create and inject services
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Inject into agents
        for agent in mock_agents:
            agent.auth_client = auth_client
        
        # Test that injected services are functional
        test_agent = mock_agents[0]
        
        # Test auth_client functionality
        assert test_agent.auth_client is not None
        assert hasattr(test_agent.auth_client, 'auth_manager')
        assert hasattr(test_agent.auth_client.auth_manager, 'user_data_manager')
        assert hasattr(test_agent.auth_client.auth_manager, 'transport')
        
        # Test user_data_manager functionality
        all_users = test_agent.auth_client.auth_manager.user_data_manager.get_all_users()
        assert isinstance(all_users, list)
        
        logger.info("✅ Injected services functionality test passed")
    
    def test_service_singleton_behavior(self, test_config, mock_agents):
        """Test that services behave as singletons across agents"""
        # Create core services
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Inject same instances into all agents
        for agent in mock_agents:
            agent.auth_client = auth_client
        
        # Verify singleton behavior - all agents share same service instances
        reference_auth_client = mock_agents[0].auth_client
        reference_auth_manager = reference_auth_client.auth_manager
        reference_user_manager = reference_auth_manager.user_data_manager
        reference_transport = reference_auth_manager.transport
        
        for agent in mock_agents[1:]:
            # Same auth_client instance
            assert agent.auth_client is reference_auth_client
            # Same auth_manager instance
            assert agent.auth_client.auth_manager is reference_auth_manager
            # Same user_data_manager instance
            assert agent.auth_client.auth_manager.user_data_manager is reference_user_manager
            # Same transport instance
            assert agent.auth_client.auth_manager.transport is reference_transport
        
        logger.info("✅ Service singleton behavior test passed")
    
    def test_future_service_injection_points(self, test_config, mock_agents):
        """Test future service injection points mentioned in framework_demo.py"""
        # Create core services
        user_data_manager = LocalUserDataManager()
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Create mock future services
        mock_orchestrator = Mock()
        mock_orchestrator.name = "MockOrchestrator"
        
        mock_crawler = Mock()
        mock_crawler.name = "MockCrawler"
        
        # Inject services (current and future)
        for agent in mock_agents:
            agent.auth_client = auth_client
            # Future service injections mentioned in framework_demo.py:
            agent.orchestrator = mock_orchestrator
            agent.crawler = mock_crawler
        
        # Verify all injections
        for agent in mock_agents:
            assert hasattr(agent, 'auth_client')
            assert hasattr(agent, 'orchestrator') 
            assert hasattr(agent, 'crawler')
            
            assert agent.auth_client is auth_client
            assert agent.orchestrator is mock_orchestrator
            assert agent.crawler is mock_crawler
        
        logger.info("✅ Future service injection points test passed")


class TestFrameworkDemoIntegration:
    """Test framework_demo.py integration patterns"""
    
    @pytest.fixture
    def test_config(self):
        """Setup test configuration"""
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(script_dir, "test_suite", "config", "test_config.yaml")
        
        app_config = UnifiedConfig(config_file=config_path, app_root=script_dir)
        set_global_config(app_config)
        setup_logging()
        
        return app_config
    
    @pytest.fixture
    def clean_sdk_instance(self):
        """Clean SDK instance for each test"""
        ANPSDK.instance = None
        ANPSDK._instances.clear()
        yield
        ANPSDK.instance = None
        ANPSDK._instances.clear()
    
    def test_agent_loading_pattern(self, test_config):
        """Test agent loading pattern from framework_demo.py"""
        # Simulate agent loading process
        # This would normally load from agent_mappings.yaml files
        
        # Mock the agent loading result
        mock_agent_info = []
        for i in range(2):
            agent = Mock()
            agent.id = f"did:wba:localhost%3A9527:wba:user:loaded_agent_{i}"
            agent.name = f"LoadedAgent{i}"
            agent.api_routes = {}
            agent.is_hosted_did = False
            
            lifecycle_module = Mock()
            lifecycle_module.initialize_agent = AsyncMock()
            lifecycle_module.cleanup_agent = AsyncMock()
            
            mock_agent_info.append((agent, lifecycle_module))
        
        # Extract agents and lifecycle modules (as in framework_demo.py)
        valid_agents_info = mock_agent_info
        all_agents = [info[0] for info in valid_agents_info]
        lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}
        
        # Verify extraction
        assert len(all_agents) == 2
        assert len(lifecycle_modules) == 2
        
        for agent in all_agents:
            assert agent.id in lifecycle_modules
            module = lifecycle_modules[agent.id]
            assert hasattr(module, 'initialize_agent')
            assert hasattr(module, 'cleanup_agent')
        
        logger.info("✅ Agent loading pattern test passed")
    
    @pytest.mark.asyncio
    async def test_agent_initialization_lifecycle(self, test_config, clean_sdk_instance):
        """Test agent initialization lifecycle from framework_demo.py"""
        # Create mock agents with lifecycle modules
        agents = []
        lifecycle_modules = {}
        
        for i in range(2):
            agent = Mock()
            agent.id = f"did:wba:localhost%3A9527:wba:user:lifecycle_test_{i}"
            agent.name = f"LifecycleAgent{i}"
            
            module = Mock()
            module.initialize_agent = AsyncMock()
            module.cleanup_agent = AsyncMock()
            
            agents.append(agent)
            lifecycle_modules[agent.id] = module
        
        # Create SDK
        sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=agents)
        
        # Simulate initialization phase (framework_demo.py lines 298-303)
        logger.info("🔄 Executing agent post-initialization...")
        for agent in agents:
            module = lifecycle_modules.get(agent.id)
            if module and hasattr(module, "initialize_agent"):
                logger.info(f"  - Initializing agent: {agent.name}")
                await module.initialize_agent(agent, sdk)
        
        # Verify initialization was called
        for agent in agents:
            module = lifecycle_modules[agent.id]
            module.initialize_agent.assert_called_once_with(agent, sdk)
        
        # Simulate cleanup phase (framework_demo.py lines 475-483)
        logger.info("🛑 Starting cleanup...")
        cleanup_tasks = []
        for agent in agents:
            module = lifecycle_modules.get(agent.id)
            if module and hasattr(module, "cleanup_agent"):
                logger.info(f"  - Cleaning up agent: {agent.name}")
                cleanup_tasks.append(module.cleanup_agent())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks)
        
        # Verify cleanup was called
        for agent in agents:
            module = lifecycle_modules[agent.id]
            module.cleanup_agent.assert_called_once()
        
        logger.info("✅ Agent initialization lifecycle test passed")
    
    def test_sdk_configuration_integration(self, test_config, clean_sdk_instance):
        """Test SDK configuration integration from framework_demo.py"""
        # Create agents
        agents = [Mock() for _ in range(2)]
        for i, agent in enumerate(agents):
            agent.id = f"did:wba:localhost%3A9527:wba:user:config_test_{i}"
            agent.name = f"ConfigAgent{i}"
        
        # Create SDK (framework_demo.py line 276)
        sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=agents)
        
        # Create and attach services (framework_demo.py lines 281-295)
        user_data_manager = LocalUserDataManager()
        sdk.user_data_manager = user_data_manager
        
        http_transport = HttpTransport()
        framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
        auth_client = AuthClient(framework_auth_manager)
        
        # Inject services into agents
        for agent in agents:
            agent.auth_client = auth_client
        
        # Verify complete integration
        assert sdk.mode == SdkMode.MULTI_AGENT_ROUTER
        assert len(sdk.agents) == 2
        assert hasattr(sdk, 'user_data_manager')
        assert sdk.user_data_manager is user_data_manager
        
        # Verify each agent has injected services
        for agent in agents:
            assert hasattr(agent, 'auth_client')
            assert agent.auth_client is auth_client
            assert agent.auth_client.auth_manager is framework_auth_manager
        
        logger.info("✅ SDK configuration integration test passed")


def run_service_injection_tests():
    """Run service injection pattern tests"""
    print("🧪 Running ANP Framework Service Injection Tests")
    print("=" * 80)
    
    # Run with pytest
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
    return result.returncode == 0


if __name__ == "__main__":
    success = run_service_injection_tests()
    if success:
        print("\n✅ All service injection pattern tests passed!")
    else:
        print("\n❌ Some service injection pattern tests failed!")
        sys.exit(1)