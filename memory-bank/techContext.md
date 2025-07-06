# Technical Context - ANP Open SDK

## Technology Stack

### Core Technologies

**Python 3.8+**
- Primary development language
- Async/await support for concurrent operations
- Rich ecosystem for networking and cryptography

**FastAPI**
- Modern web framework for API development
- Automatic OpenAPI documentation generation
- Built-in support for async operations and type hints
- Used for agent HTTP services

**Pydantic**
- Data validation and settings management
- Type-safe configuration parsing
- JSON schema generation for API documentation

**Cryptography Libraries**
- `cryptography` package for DID signature verification
- Support for various cryptographic algorithms
- Secure key generation and management

### Development Dependencies

**Poetry**
- Dependency management and packaging
- Virtual environment management
- Build and publish automation

**AsyncIO**
- Core async programming support
- Event loop management
- Concurrent task execution

**HTTPX**
- Modern HTTP client for agent-to-agent communication
- Async support and connection pooling
- HTTP/2 support for improved performance

## Development Setup

### Environment Requirements

```bash
# Python version
Python 3.8 or higher

# Package manager
Poetry (recommended) or pip

# Environment variables
OPENAI_API_KEY=your_openai_key
OPENAI_API_MODEL_NAME=gpt-4
OPENAI_API_BASE_URL=https://api.openai.com/v1
```

### Installation Process

```bash
# 1. Clone repository
git clone https://github.com/seanzhang9999/anp-open-sdk.git
cd anp-open-sdk

# 2. Setup environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# 3. Install dependencies
poetry install
# or pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run tests
python test/test_anpsdk_all.py
```

### Project Structure

```
anp-open-sdk/
├── anp_open_sdk/              # Core SDK
│   ├── auth/                  # Authentication system
│   ├── config/                # Configuration management
│   ├── service/               # Core services
│   └── utils/                 # Utilities
├── anp_open_sdk_framework/    # Framework layer
│   ├── local_methods/         # Local method system
│   ├── unified_caller.py      # Unified calling interface
│   └── unified_crawler.py     # Resource discovery
├── demo_anp_open_sdk/         # Core SDK demos
├── demo_anp_open_sdk_framework/ # Framework demos
├── demo_anp_user_service/     # User service examples
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── test/                      # Test suite
└── memory-bank/               # Project memory bank
```

## Technical Constraints

### Performance Requirements

- **Response Time**: Sub-second for simple agent-to-agent calls
- **Throughput**: Support for hundreds of concurrent agent connections
- **Memory Usage**: Efficient memory management for long-running services
- **Network Efficiency**: Connection pooling and reuse

### Security Constraints

- **Authentication**: All agent communications must be authenticated
- **Encryption**: Sensitive data must be encrypted in transit
- **Key Management**: Secure storage and rotation of cryptographic keys
- **Input Validation**: All inputs must be validated and sanitized

### Compatibility Requirements

- **Python Versions**: Support Python 3.8+
- **Operating Systems**: Cross-platform (Windows, macOS, Linux)
- **Network Protocols**: HTTP/HTTPS with potential for WebSocket support
- **Configuration Formats**: YAML and JSON support

## Dependencies

### Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
pydantic = "^2.5.0"
httpx = "^0.25.0"
cryptography = "^41.0.0"
pyyaml = "^6.0"
```

### Development Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
flake8 = "^6.0.0"
mypy = "^1.7.0"
```

### Optional Dependencies

- **OpenAI**: For LLM-powered agents
- **Anthropic**: Alternative LLM provider
- **Redis**: For distributed caching (future)
- **PostgreSQL**: For persistent storage (future)

## Tool Usage Patterns

### Configuration Management

**Unified Configuration System**
- YAML-based configuration files
- Environment variable overrides
- Type-safe configuration parsing with Pydantic
- Hierarchical configuration inheritance

**Example Configuration**:
```yaml
anp_sdk:
  host: "localhost"
  port: 9527
  debug_mode: true
  
agents:
  - name: "calculator"
    module: "agents.calculator"
    config_path: "agents_config/calculator/"
```

### Logging and Debugging

**Structured Logging**
- JSON-formatted logs for production
- Human-readable logs for development
- Configurable log levels per component
- Distributed tracing support (planned)

**Debug Mode Features**
- Detailed request/response logging
- Performance timing information
- Agent interaction visualization
- Hot reload for development

### Testing Strategy

**Unit Tests**
- Individual component testing
- Mock external dependencies
- Async test support with pytest-asyncio

**Integration Tests**
- End-to-end agent communication
- Multi-agent workflow testing
- Authentication and authorization testing

**Performance Tests**
- Load testing for agent networks
- Memory usage profiling
- Network latency measurement

### Deployment Patterns

**Development Deployment**
- Single-process multi-agent setup
- Hot reload for rapid development
- Local file-based storage
- Debug logging enabled

**Production Deployment**
- Multi-process agent distribution
- Container-based deployment (Docker)
- External storage backends
- Structured logging and monitoring

### Code Quality Tools

**Formatting and Linting**
- Black for code formatting
- Flake8 for style checking
- MyPy for type checking
- Pre-commit hooks for consistency

**Documentation**
- Automatic API documentation via FastAPI
- Sphinx for comprehensive documentation
- Code examples and tutorials
- Architecture decision records (ADRs)

## Development Workflow

### Feature Development

1. **Branch Creation**: Feature branches from main
2. **Development**: Local development with hot reload
3. **Testing**: Unit and integration tests
4. **Code Review**: Pull request review process
5. **Integration**: Merge to main after approval

### Release Process

1. **Version Bumping**: Semantic versioning
2. **Changelog**: Automated changelog generation
3. **Testing**: Full test suite execution
4. **Packaging**: Poetry build and publish
5. **Documentation**: Update documentation and examples

### Monitoring and Observability

**Metrics Collection**
- Agent performance metrics
- Network communication statistics
- Error rates and response times
- Resource usage monitoring

**Health Checks**
- Agent availability monitoring
- Service dependency checks
- Network connectivity validation
- Configuration validation
