# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ANP Open SDK is a powerful toolkit for building decentralized agent networks based on the ANP (Agent Network Protocol) core protocol. It provides a layered architecture from low-level protocol to high-level plugin framework for agent network development.

### Key Components

1. **anp_open_sdk** (Core SDK) - Protocol encapsulation, DID user management, LLM-driven agents, FastAPI integration
2. **anp_open_sdk_framework** (Advanced Framework) - Plugin architecture for rapid agent development  
3. **anp_user_extension/anp_user_service** - User-facing examples and services

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
poetry install
python -m ensurepip --upgrade
python -m pip install --upgrade pip
ensurepip install agent_connect

# On Windows, may need to add root directory to PYTHONPATH
$env:PYTHONPATH += ";d:\seanwork\anp-open-sdk"
```

### Configuration
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your OPENAI_API_KEY, OPENAI_API_MODEL_NAME, OPENAI_API_BASE_URL
```

### Running Tests
```bash
# Run all tests
python test/test_anpsdk_all.py

# Run specific tests
python test/test_auth_integration.py
python test/test_auth_refactor.py
python test/test_auth_simple.py
python test/test_memory_auth.py
python test/test_unified_config.py
```

### Running Demos
```bash
# Run core SDK demo
python anp_open_sdk_demo/anp_demo_main.py

# Check agent DID bindings (creates DIDs if needed)
python anp_open_sdk_framework_demo/agent_user_binding.py

# Start agent network on port 9527
python anp_open_sdk_framework_demo/framework_demo.py

# Start second server on port 9528 (keep 9527 running)
python anp_open_sdk_framework_demo/agent_user_binding.py --config anp_open_sdk_framework_demo_agent_9528_unified_config.yaml
python anp_open_sdk_framework_demo/framework_demo.py --config anp_open_sdk_framework_demo_agent_9528_unified_config.yaml
```

### User Extension (Chrome Plugin)
```bash
cd anp_user_extension
npm install
npm run build
```

### User Service Backend
```bash
cd anp_user_service
python main.py
```

## Architecture Overview

### Core Classes and Files

- **anp_open_sdk/anp_sdk.py** - Main ANPSDK class with multi-mode support
- **anp_open_sdk/anp_sdk_agent.py** - LocalAgent class for agent instances
- **anp_open_sdk_framework/agent_manager.py** - LocalAgentManager for loading agents from YAML configs
- **anp_open_sdk/auth/** - Authentication and DID management
- **anp_open_sdk/service/** - Routers, publishers, and interaction services

### Agent Plugin System

Agents are defined using YAML configuration files in `data_user/localhost_XXXX/agents_config/`:
- **agent_mappings.yaml** - Agent configuration (name, DID, API endpoints)
- **agent_handlers.py** - Business logic handlers  
- **agent_register.py** - Optional custom registration logic

### Configuration System

- **unified_config.default.yaml** - Configuration template
- **UnifiedConfig class** - Centralized configuration management with environment variable mapping
- Supports `{APP_ROOT}` placeholder for dynamic path resolution

### Multi-Server Architecture

The framework supports running multiple agent servers (9527, 9528) that can communicate cross-server through DID authentication.

### Key Integration Points

1. **Agent Loading**: `LocalAgentManager.load_agent_from_module()` loads agents from YAML configs
2. **API Registration**: `wrap_business_handler()` wraps agent handlers for FastAPI
3. **Local Methods**: `@local_method` decorator registers methods for local API calls
4. **Cross-Agent Communication**: Agents can call each other's APIs locally or over network

## Development Patterns

### Creating New Agents
1. Create directory under `data_user/localhost_XXXX/agents_config/agent_name/`
2. Add `agent_mappings.yaml` with agent config
3. Implement `agent_handlers.py` with business logic
4. Optional: Add `agent_register.py` for custom registration

### Testing Workflow
Always run tests after making changes:
```bash
python test/test_anpsdk_all.py
```

### Local Method Pattern
Use `@local_method` decorator to expose agent methods for inter-agent calls:
```python
from anp_open_sdk_framework.local_methods.local_methods_decorators import local_method

@local_method
def my_api_method(param1: str) -> dict:
    return {"result": param1}
```

### Configuration Management
Access global config using:
```python
from anp_open_sdk.config import get_global_config
config = get_global_config()
```

## File Structure Notes

- `anp_open_sdk/` - Core SDK implementation
- `anp_open_sdk_demo/` - Demo and test modules  
- `anp_open_sdk_framework/` - Advanced framework layer
- `anp_open_sdk_framework_demo/` - Framework usage examples
- `data_user/` - Agent configurations and user data
- `test/` - Unit tests and integration tests
- Configuration files use YAML format with environment variable support