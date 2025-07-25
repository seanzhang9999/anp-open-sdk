/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

// 导出所有装饰器和工具函数
export {
  // DID 获取工具函数
  getUserByName,
  getFirstAvailableUser,
  getUserByIndex,
  listAvailableUsers,
  
  // 面向对象风格装饰器
  agentClass,
  classApi,
  classMessageHandler,
  groupEventMethod,
  
  // 函数式风格工厂函数
  createAgent,
  createAgentFromName,
  createSharedAgent,
  
  // 函数式风格装饰器
  agentApi,
  agentMessageHandler,
  registerGroupEventHandler,
  
  // 通用能力装饰器
  classCapability,
  agentCapability
} from './agent-decorators';

export type {
  AgentClassOptions
} from './agent-decorators';

// 为了兼容性，提供别名
export { classApi as api } from './agent-decorators';
export { classMessageHandler as messageHandler } from './agent-decorators';
export { groupEventMethod as groupEventHandler } from './agent-decorators';