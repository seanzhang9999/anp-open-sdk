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

# Install dependencies (Poetry required)
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
python anp_open_sdk_framework_demo/agent_user_binding.py --config unified_config_anp_open_sdk_framework_demo_agent_9528.yaml
python anp_open_sdk_framework_demo/framework_demo.py --config unified_config_anp_open_sdk_framework_demo_agent_9528.yaml
```

### User Extension (Chrome Plugin)
```bash
cd demo_anp_user_service/anp_user_extension
npm install
npm run build
```

### User Service Backend
```bash
cd demo_anp_user_service
python main.py
```

### No Linting/Formatting Tools
This project currently has no automated linting, formatting, or code quality tools configured. Development relies on manual code review and IDE defaults.

## Architecture Overview

ANP Open SDK follows a layered architecture with clear separation of concerns across three main layers:

### Core Architecture Layers

1. **Core SDK Layer** (`anp_open_sdk/`) - Protocol encapsulation, DID management, authentication
2. **Framework Layer** (`anp_open_sdk_framework/`) - Plugin architecture for rapid agent development  
3. **Application Layer** - Demo applications, user services, and extensions

### Key Classes and Files

**Main Orchestration:**
- **anp_open_sdk/anp_sdk.py** - Central ANPSDK class with 5 operational modes (multi-agent router, DID server, self-service, WebSocket proxy)
- **anp_open_sdk/anp_sdk_agent.py** - LocalAgent class for individual agent instances with DID-based identity
- **anp_open_sdk_framework/agent_manager.py** - LocalAgentManager for YAML-based agent loading and OpenAPI generation

**Authentication & Security:**
- **anp_open_sdk/auth/** - DID-based authentication system with WBA implementation, JWT tokens, contact management
- **anp_open_sdk/auth/did_auth_wba.py** - Web-Based Authentication implementation
- **anp_open_sdk/auth/auth_server.py** - Central authentication orchestrator

**Service & Routing:**
- **anp_open_sdk/service/router/** - Multi-agent request routing, DID resolution, business handler wrapping
- **anp_open_sdk/service/publisher/** - DID publishing and agent registration services
- **anp_open_sdk/service/interaction/** - Group management, P2P messaging, tool integration

### Agent Plugin System

Agents use a flexible plugin architecture with three loading patterns:

**Configuration Files** (`data_user/localhost_XXXX/agents_config/`):
- **agent_mappings.yaml** - Agent configuration (name, DID, API endpoints)
- **agent_handlers.py** - Business logic handlers  
- **agent_register.py** - Optional custom registration logic

**Loading Patterns:**
1. **Self-registration** - Agents register themselves via `agent_register.py`
2. **Initialization-based** - Framework calls `initialize_agent()` function
3. **Configuration-driven** - YAML mapping to handler functions with automatic wrapping

### Configuration System

**UnifiedConfig Architecture** - Centralized YAML-based configuration with advanced features:
- **unified_config.default.yaml** - Configuration template with environment variable mapping
- **UnifiedConfig class** - Type inference, validation, and nested access via `ConfigNode` objects
- **Path placeholder resolution** - `{APP_ROOT}` automatically resolves to project root directory
- **Environment variable integration** - Direct mapping from YAML keys to `.env` file variables
- **Secrets management** - Protected access patterns for sensitive configuration data

**Configuration Hierarchy:**
```
unified_config.yaml
├── anp_sdk (core SDK settings)
├── llm (language model configuration) 
├── mail (email backend configuration)
├── env_mapping (environment variable mappings)
└── secrets (protected configuration access)
```

### Multi-Server Architecture & Communication Flow

**Deployment Flexibility** - Framework supports multiple operational modes and deployment patterns:
- **Multi-agent servers** (default ports 9527, 9528) with cross-server DID-based authentication
- **Five SDK modes** via `SdkMode` enum for different deployment scenarios
- **Local vs. networked** agent communication with transparent routing

**Agent Communication Flow:**
```
Client Request → FastAPI Middleware → DID/JWT Auth → Agent Router → LocalAgent → Business Logic
                     ↓                    ↓               ↓            ↓
            CORS/Security        Token Verification   DID Resolution   Method Invocation
```

**DID-Based Identity System:**
- **Decentralized identifiers** for secure agent-to-agent communication
- **Self-sovereign identity** with local cryptographic key management  
- **Contact management** with token storage and relationship tracking
- **Cross-network discovery** and authentication

### Key Integration Points & Design Patterns

**Agent Loading & Registration:**
1. **Agent Loading**: `LocalAgentManager.load_agent_from_module()` loads agents from YAML configs
2. **API Registration**: `wrap_business_handler()` wraps agent handlers for FastAPI with parameter extraction
3. **Local Methods**: `@local_method` decorator registers methods for inter-agent API calls
4. **Cross-Agent Communication**: Agents communicate via DID resolution and token-based authentication

**Core Design Patterns:**
- **Plugin Architecture** - Decorator-based registration (`@local_method`, `@expose_api`) with module-based loading
- **Event-Driven Architecture** - Group event handlers, message routing, WebSocket/SSE real-time communication  
- **Singleton with Multi-Instance** - ANPSDK class supports multiple instances on different ports
- **Middleware Pattern** - Authentication, CORS, and request preprocessing via FastAPI middleware

## File Structure & Development Patterns

### Project Structure
- `anp_open_sdk/` - Core SDK implementation (protocol, auth, routing)
- `anp_open_sdk_demo/` - Core SDK demo and examples  
- `anp_open_sdk_framework/` - Advanced framework layer (plugin architecture)
- `anp_open_sdk_framework_demo/` - Framework usage examples and main demo entry point
- `demo_anp_user_service/` - User-facing services and Chrome extension
- `data_user/` - Runtime agent configurations, DID storage, and user data
- `test/` - Unit tests and integration tests
- `scripts/` - Development and deployment scripts

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

- `anp_open_sdk/` - Core SDK implementation (protocol, auth, routing)
- `anp_open_sdk_demo/` - Core SDK demo and examples  
- `anp_open_sdk_framework/` - Advanced framework layer (plugin architecture)
- `anp_open_sdk_framework_demo/` - Framework usage examples and main demo entry point
- `demo_anp_user_service/` - User-facing services and Chrome extension
- `data_user/` - Runtime agent configurations, DID storage, and user data
- `test/` - Unit tests and integration tests
- `scripts/` - Development and deployment scripts

**Configuration files use YAML format with environment variable support and automatic path resolution.**