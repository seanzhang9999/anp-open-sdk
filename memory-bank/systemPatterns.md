# System Patterns - ANP Open SDK

## Architecture Overview

The ANP Open SDK follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│     Developer Applications         │  ← User Code
├─────────────────────────────────────┤
│   anp_open_sdk_framework           │  ← High-level Framework
│   - UnifiedOrchestrator             │
│   - UnifiedCrawler                  │
│   - UnifiedCaller                   │
│   - Plugin System                   │
├─────────────────────────────────────┤
│   anp_open_sdk (Core)              │  ← Core SDK
│   - Agent Management               │
│   - DID Authentication             │
│   - Protocol Implementation        │
│   - FastAPI Integration            │
└─────────────────────────────────────┘
```

## Key Design Patterns

### 1. Layered Architecture Pattern

**Core Principle**: Each layer only depends on layers below it, never above.

- **Core SDK Layer**: Provides fundamental capabilities (DID, auth, networking)
- **Framework Layer**: Builds on core to provide high-level abstractions
- **Application Layer**: Uses framework for business logic

**Benefits**:
- Clear separation of concerns
- Independent testing and development
- Flexible deployment options

### 2. Plugin Architecture Pattern

**Implementation**: Decorator-based plugin registration

```python
@expose_api(path="/calculate", auth_mode="did")
async def calculate(a: float, b: float) -> float:
    return a + b
```

**Components**:
- **PluginLoader**: Scans and loads agent plugins
- **MethodRegistry**: Maintains registry of available methods
- **MetadataExtractor**: Extracts method metadata from decorators

### 3. Execution Trio Pattern

**Three Levels of Interaction**:

1. **UnifiedCaller**: Single, stateless API calls
2. **UnifiedCrawler**: Resource discovery and search
3. **UnifiedOrchestrator**: Complex, stateful task orchestration

**Relationships**:
- Orchestrator uses Crawler for resource discovery
- Orchestrator uses Caller for individual step execution
- Each component can be used independently

### 4. DID-Based Identity Pattern

**Components**:
- **DID Creation**: `did:wba:host:port:dir:user_type:unique_id`
- **Authentication**: Cryptographic signature verification
- **Authorization**: Method-level permission control

**Flow**:
```
Request → Extract DID → Verify Signature → Check Permissions → Execute
```

## Component Relationships

### Core SDK Components

1. **ANPSDK Class**
   - Central orchestrator for the entire system
   - Manages agent lifecycle and routing
   - Integrates with FastAPI for HTTP services

2. **Agent Management**
   - `LocalAgent`: Agents running in current process
   - `RemoteAgent`: Agents running on other nodes
   - Agent discovery and registration

3. **Authentication System**
   - DID-based identity management
   - Signature verification
   - Permission checking middleware

4. **Configuration System**
   - Unified configuration management
   - Environment-specific settings
   - Runtime configuration updates

### Framework Components

1. **UnifiedCaller**
   - Handles both local method calls and remote API calls
   - Automatic target detection (local vs remote)
   - Error handling and retry logic

2. **UnifiedCrawler**
   - Agent and service discovery
   - Resource indexing and search
   - Health monitoring

3. **UnifiedOrchestrator**
   - Multi-step task execution
   - State management for complex workflows
   - Interruption and continuation support

4. **Plugin System**
   - Automatic plugin discovery
   - Decorator-based method registration
   - Metadata-driven configuration

## Critical Implementation Paths

### 1. Agent-to-Agent Communication

```
Caller Agent → Authentication → Target Agent → Method Execution → Response
```

**Key Steps**:
1. DID resolution and target identification
2. Request signing with caller's private key
3. Network transport (HTTP/HTTPS)
4. Signature verification at target
5. Method execution and response

### 2. Plugin Loading and Registration

```
Startup → Scan Plugin Dirs → Load Python Modules → Extract Metadata → Register Methods
```

**Key Steps**:
1. Configuration-driven directory scanning
2. Dynamic Python module loading
3. Decorator metadata extraction
4. Method registration in local and/or remote registries

### 3. Task Orchestration

```
Goal → Resource Discovery → Plan Generation → Step Execution → State Management
```

**Key Steps**:
1. Task goal analysis and decomposition
2. Resource discovery via UnifiedCrawler
3. Execution plan generation
4. Sequential/parallel step execution via UnifiedCaller
5. State persistence and continuation support

## Design Decisions

### 1. Async-First Architecture

**Decision**: All I/O operations are asynchronous
**Rationale**: Better performance for network-heavy agent communications
**Implementation**: `asyncio` throughout, `async/await` patterns

### 2. Decorator-Based Configuration

**Decision**: Use Python decorators for method registration
**Rationale**: Clean, declarative syntax that's familiar to Python developers
**Implementation**: Metadata stored as function attributes

### 3. DID-Based Identity

**Decision**: Use Decentralized Identifiers for agent identity
**Rationale**: Enables truly decentralized networks without central authority
**Implementation**: Custom DID method `did:wba:...`

### 4. FastAPI Integration

**Decision**: Use FastAPI for HTTP services
**Rationale**: Modern, fast, automatic API documentation, type hints
**Implementation**: Dynamic route registration based on agent methods

### 5. Configuration-Driven Behavior

**Decision**: All behavior controlled by configuration files
**Rationale**: Flexibility for different deployment scenarios
**Implementation**: YAML configuration with type-safe parsing

## Performance Considerations

### 1. Connection Pooling

- HTTP connection reuse for agent-to-agent calls
- Configurable pool sizes and timeouts

### 2. Caching Strategies

- Agent discovery results caching
- Method metadata caching
- Configuration caching

### 3. Async Optimization

- Non-blocking I/O for all network operations
- Concurrent execution where possible
- Proper resource cleanup

## Security Patterns

### 1. Zero-Trust Architecture

- Every request must be authenticated
- No implicit trust between agents
- Cryptographic verification required

### 2. Principle of Least Privilege

- Method-level permission control
- Configurable access policies
- Audit logging for all access attempts

### 3. Defense in Depth

- Multiple layers of security (network, application, method)
- Input validation at all boundaries
- Secure defaults in configuration
