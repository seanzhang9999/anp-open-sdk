# ANP Open SDK End-to-End DID Authentication Test Suite

## Overview

This test suite provides a clean, extracted implementation of the DID (Decentralized Identifier) authentication flow from the ANP Open SDK Framework. It's designed for test-driven development and verification of the authentication system.

## Files Created

### 1. Core Test Suite (`test_e2e_did_auth.py`)
A comprehensive pytest-based test suite that includes:
- **E2EDIDAuthTestHelper**: Helper class for setting up test environments
- **TestE2EDIDAuthentication**: Main test class with fixtures and test methods
- Utilities for creating test agents, DID documents, and authentication contexts

### 2. Real Integration Tests (`test_real_integration.py`)
Integration tests that work with actual DID documents and keys:
- **RealIntegrationTestHelper**: Helper for discovering existing test agents
- **TestRealDIDAuthentication**: Tests using real cryptographic material
- Discovery and validation of existing agent data

### 3. Simple Test Runner (`simple_test_runner.py`)
A standalone test runner that doesn't require pytest infrastructure:
- Direct execution without external dependencies
- Clear output showing each test step
- Suitable for CI/CD pipelines and debugging

### 4. Test Configuration (`test_config.yaml`)
Minimal configuration file for testing:
- Basic ANP SDK settings
- Test-specific paths and parameters
- Authentication method configuration

## Key Components Extracted

### From `framework_demo.py`:
```python
# DID Loading and SDK Setup
user_data_manager = LocalUserDataManager()
http_transport = HttpTransport()
framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
auth_client = AuthClient(framework_auth_manager)

# Agent injection pattern
for agent in agents:
    agent.auth_client = auth_client
```

### From `agent_handlers.py`:
```python
# Authentication flow pattern
status, response_data, msg, success = await self.auth_client.authenticated_request(
    caller_agent=self.id,
    target_agent=target_did,
    request_url=target_url
)
```

### From debugging session:
```python
# Fixed signature verification flow
from anp_open_sdk.auth_methods.wba.implementation import PureWBADIDSigner
from anp_open_sdk.auth.schemas import AuthenticationContext, DIDCredentials

# Proper DID document instantiation
did_doc = DIDDocument(**did_doc_raw, raw_document=did_doc_raw)

# Service domain consistency
service_domain = self._get_domain(context.request_url)
```

## Usage

### Quick Test
```bash
python simple_test_runner.py
```

### Full Pytest Suite
```bash
pip install pytest
python -m pytest test_e2e_did_auth.py -v
```

### Real Integration Tests
```bash
python -m pytest test_real_integration.py -v
```

## Test Flow

The test suite verifies the complete DID authentication pipeline:

1. **Agent Discovery**: Finds available test agents from data directories
2. **DID Document Loading**: Validates DID document structure and content
3. **Auth Components Setup**: Creates and configures authentication managers
4. **Authentication Context**: Creates proper request contexts for authentication
5. **Signature Components**: Tests cryptographic signature creation and verification

## Test Data Structure

```
test/data_user/localhost_9527/anp_users/
├── test_agent_001/
│   ├── did_document.json
│   └── private_key.txt
└── test_agent_002/
    ├── did_document.json
    └── private_key.txt
```

Each agent directory contains:
- **did_document.json**: Complete DID document with verification methods and services
- **private_key.txt**: Private key for cryptographic operations

## Key Authentication Flow

1. **Context Creation**:
   ```python
   context = AuthenticationContext(
       caller_did=caller_agent.id,
       target_did=target_agent.id,
       request_url="http://localhost:9527/endpoint",
       method="POST",
       use_two_way_auth=True
   )
   ```

2. **Header Generation**:
   ```python
   signer = PureWBADIDSigner()
   header_builder = PureWBAAuthHeaderBuilder(signer)
   auth_headers = header_builder.build_auth_header(context, credentials)
   ```

3. **Request Execution**:
   ```python
   response = await auth_client.authenticated_request(
       caller_agent=caller_did,
       target_agent=target_did,
       request_url=url
   )
   ```

## Integration Points

This test suite can be used for:

- **Test-Driven Development**: Write tests first, then implement features
- **Regression Testing**: Ensure authentication changes don't break existing functionality
- **CI/CD Pipelines**: Automated testing of authentication components
- **Debugging**: Isolated testing of authentication flow components
- **Documentation**: Living examples of how to use the authentication system

## Dependencies

- **anp_open_sdk**: Core SDK components
- **anp_open_sdk_framework**: Framework layer components
- **pytest** (optional): For advanced test features
- **Standard library**: json, os, sys, asyncio, tempfile

## Debugging Features

The test suite includes extensive logging and error reporting:
- Step-by-step execution tracking
- Detailed error messages with stack traces
- Validation of each component in the authentication pipeline
- Clear success/failure indicators

## Configuration

The test configuration supports:
- Custom host/port settings
- Authentication method selection
- Test data directory paths
- Logging level configuration

This test suite provides a solid foundation for developing and testing DID-based authentication systems in the ANP Open SDK ecosystem.