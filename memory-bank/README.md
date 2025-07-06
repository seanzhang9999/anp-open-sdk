# ANP Open SDK Memory Bank

This Memory Bank contains comprehensive documentation about the ANP Open SDK project to enable effective understanding and continuation across development sessions.

## File Structure

### Core Files (Required)
1. **[projectbrief.md](./projectbrief.md)** - Foundation document defining project scope, goals, and components
2. **[productContext.md](./productContext.md)** - Why the project exists, problems it solves, and user experience goals
3. **[systemPatterns.md](./systemPatterns.md)** - Technical architecture, design patterns, and component relationships
4. **[techContext.md](./techContext.md)** - Technology stack, development setup, and tool usage patterns
5. **[activeContext.md](./activeContext.md)** - Current work focus, recent changes, and active decisions
6. **[progress.md](./progress.md)** - What works, what's left to build, and current status

## Quick Reference

### Project Overview
ANP Open SDK is a powerful toolkit for building decentralized agent networks based on the ANP (Agent Network Protocol). It provides a layered architecture from low-level protocols to high-level plugin frameworks.

### Current Status
- **Stability**: Beta Quality (70% complete)
- **Core SDK**: ~80% complete, working DID authentication and agent communication
- **Framework**: ~60% complete, missing UnifiedOrchestrator implementation
- **Production Readiness**: Not ready, needs monitoring and performance optimization

### Key Architecture
```
Developer Applications
├── anp_open_sdk_framework (High-level Framework)
│   ├── UnifiedOrchestrator (Missing - Critical)
│   ├── UnifiedCrawler (Basic implementation)
│   ├── UnifiedCaller (Partial implementation)
│   └── Plugin System (Basic implementation)
└── anp_open_sdk (Core SDK)
    ├── Agent Management (Working)
    ├── DID Authentication (Working)
    ├── FastAPI Integration (Working)
    └── Configuration System (Working)
```

### Immediate Priorities
1. Complete UnifiedOrchestrator implementation
2. Enhance error handling and retry mechanisms
3. Add performance optimizations and monitoring
4. Improve documentation and developer tools

### Technology Stack
- **Language**: Python 3.8+
- **Web Framework**: FastAPI
- **Async**: AsyncIO throughout
- **Config**: YAML with Pydantic validation
- **Auth**: DID-based cryptographic verification
- **Communication**: HTTP/HTTPS with agent-to-agent protocols

## Usage Guidelines

### For New Sessions
1. Read all core files to understand project context
2. Check activeContext.md for current work focus
3. Review progress.md for implementation status
4. Identify next steps based on priorities

### For Updates
Update relevant files when:
- Discovering new project patterns
- After implementing significant changes
- When context needs clarification
- When explicitly requested with "update memory bank"

### For Development
- Follow async-first design patterns
- Use decorator-driven configuration
- Maintain type safety with Pydantic
- Document architectural decisions
- Test incrementally with existing demos

## Key Contacts and Resources

### Documentation
- Design Blueprint: `docs/ANP_Open_SDK_Framework_Core_Design_Blueprint.md`
- README: `readme.md`
- Migration Guide: `anp_open_sdk_framework/MIGRATION_GUIDE.md`

### Demo and Examples
- Core SDK Demo: `demo_anp_open_sdk/anp_demo_main.py`
- Framework Demo: `demo_anp_open_sdk_framework/framework_demo.py`
- User Service: `demo_anp_user_service/`

### Testing
- Test Suite: `test/test_anpsdk_all.py`
- Integration Tests: `test/test_auth_integration.py`
- Configuration Tests: `test/test_unified_config.py`

## Memory Bank Maintenance

This Memory Bank should be updated regularly to reflect the current state of the project. Key triggers for updates:

1. **Major architectural changes**
2. **Completion of significant features**
3. **Discovery of new patterns or insights**
4. **Changes in project priorities or direction**
5. **Explicit request: "update memory bank"**

The Memory Bank is the primary source of truth for understanding this project across development sessions. Keep it accurate, comprehensive, and up-to-date.
