/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

// 导出核心类
export { Agent } from './core/agent';
export { AgentManager } from './core/agent-manager';
export { GlobalMessageManager, GlobalGroupManager, GroupRunner } from './core/global-message-manager';

// 导出类型
export type { 
  AgentOptions,
  ApiRoute,
  MessageHandler,
  GroupEventHandler
} from './core/agent';

export type {
  AgentInfo,
  AgentSearchRecord,
  AgentContactInfo,
  SessionRecord,
  ApiCallRecord
} from './core/agent-manager';

// 导出函数式Agent创建方法（推荐）
export {
  createAgentWithConfig,
  createCalculatorAgent,
  createWeatherAgent,
  createAgentSystem,
  createAgentsWithCode,
  GlobalMessageManager as FunctionalGlobalMessageManager,
  type AgentConfig,
  type ApiHandlerConfig,
  type MessageHandlerConfig,
  type GroupEventHandlerConfig
} from './decorators/functional-approach';

// 导出类型安全装饰器（实验性）
export {
  classApi,
  classMessageHandler,
  groupEventMethod,
  agentClass,
  getApiPath,
  getApiOptions,
  getMessageType,
  getMessageOptions,
  getGroupEventInfo,
  isClassMethod,
  createAgent,
  createSharedAgent,
  // 导出别名
  classApi as agentApi,
  classMessageHandler as agentMessageHandler,
  type ApiDecoratorOptions,
  type MessageHandlerOptions,
  type AgentClassOptions
} from './decorators/simple-decorators';

// 导出装饰器（原有的，可能有编译问题）
// export * from './decorators';

// 导出核心模块
export * from './core';