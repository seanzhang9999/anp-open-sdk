# ANP Open SDK - Project Brief

## Project Overview

ANP Open SDK is a powerful toolkit designed to help developers quickly build, deploy, and manage decentralized agent networks based on the ANP (Agent Network Protocol) core protocol. It provides a layered architecture from low-level protocols to high-level plugin frameworks, greatly simplifying the development process of agent networks.

## Core Mission

**The core goal of ANP Open SDK is to enable agent network developers to quickly and efficiently build ANP agent networks based on the `agent_connect` core protocol**, promoting the prosperity of an ecosystem composed of interoperable, intelligent, and decentralized agents.

## Project Scope

### Primary Components

1. **anp_open_sdk (Core SDK Layer)**
   - Protocol encapsulation of ANP core protocol `agent_connect`
   - DID (Decentralized Identifier) user management
   - LLM-driven intelligent agents
   - FastAPI service integration
   - Authentication middleware

2. **anp_open_sdk_framework (Advanced Framework Layer)**
   - Plugin-based architecture
   - Hybrid service capabilities (API + LLM services)
   - Flexible deployment options
   - Unified execution trio: Orchestrator, Crawler, Caller

3. **anp_user_extension/anp_user_service (User-side Examples)**
   - Chrome extension client
   - Supporting backend services
   - Development starting point for custom ANP user applications

## Key Goals

- **Developer-Friendly**: Enable rapid construction and deployment of feature-rich agent nodes
- **Intelligent Orchestration**: Support complex, multi-round collaborative tasks through UnifiedOrchestrator
- **Network Evolution**: Transform from a simple "service calling network" to a true "agent collaboration network"

## Current Status

The project is in active development with:
- Working core SDK with DID authentication
- Framework layer with unified caller/crawler components
- Demo implementations showing agent-to-agent communication
- Plugin-based agent configuration system
- Multi-agent router capabilities

## Planned Refactoring

A major refactoring is planned to:
- Clearly separate Core SDK and Framework layers
- Implement the "Execution Trio" (Orchestrator, Crawler, Caller)
- Add plugin-driven method management
- Enhance metadata-driven dynamic authentication
- Improve developer experience and system scalability

## Success Metrics

- Ease of agent development and deployment
- Network interoperability and scalability
- Developer adoption and community growth
- Performance and reliability of agent communications
