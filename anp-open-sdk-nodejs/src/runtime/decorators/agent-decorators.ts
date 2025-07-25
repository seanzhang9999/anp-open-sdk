/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Agent, AgentOptions } from '../core/agent';
import { AgentManager } from '../core/agent-manager';
import { ANPUser } from '@foundation/user';
import { getUserDataManager } from '@foundation/user';
import { getLogger } from '@foundation/utils';

const logger = getLogger('AgentDecorators');

// ===== DID 获取工具函数 =====

/**
 * 根据用户名获取 DID 字符串
 */
export function getUserByName(name: string): string {
  const userDataManager = getUserDataManager();
  const userData = userDataManager.getUserDataByName(name);
  if (!userData) {
    throw new Error(`找不到名称为 '${name}' 的用户`);
  }
  return userData.did;
}

/**
 * 获取第一个可用用户的 DID
 */
export function getFirstAvailableUser(): string {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  if (!allUsers || allUsers.length === 0) {
    throw new Error("系统中没有可用的用户");
  }
  return allUsers[0].did;
}

/**
 * 根据索引获取用户 DID
 */
export function getUserByIndex(index: number = 0): string {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  if (!allUsers || allUsers.length === 0) {
    throw new Error("系统中没有可用的用户");
  }
  
  if (index < 0 || index >= allUsers.length) {
    throw new Error(`索引 ${index} 超出范围 (0-${allUsers.length - 1})`);
  }
  
  return allUsers[index].did;
}

/**
 * 列出所有可用用户的信息
 */
export function listAvailableUsers(): Array<{ name: string; did: string }> {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  return allUsers.map(user => ({ name: user.name || user.did, did: user.did }));
}

// ===== 面向对象风格装饰器 =====

export interface AgentClassOptions {
  name: string;
  description?: string;
  version?: string;
  tags?: string[];
  did?: string;
  shared?: boolean;
  prefix?: string;
  primaryAgent?: boolean;
}

/**
 * Agent 类装饰器，用于创建和注册 Agent
 */
export function agentClass(options: AgentClassOptions) {
  return function <T extends { new (...args: any[]): {} }>(constructor: T) {
    return class extends constructor {
      public _agent!: Agent;
      public _tags: string[];

      constructor(...args: any[]) {
        super(...args);
        this._tags = options.tags || [];
        this.initializeAgent();
      }

      public initializeAgent(): void {
        // 获取 DID
        let userDid = options.did;
        if (!userDid) {
          // 如果没有提供 DID，使用第一个可用用户
          userDid = getFirstAvailableUser();
        }

        // 创建 ANPUser
        const anpUser = ANPUser.fromDid(userDid);

        // 创建 Agent
        this._agent = AgentManager.createAgent(anpUser, {
          name: options.name,
          shared: options.shared || false,
          prefix: options.prefix,
          primaryAgent: options.primaryAgent || false
        });

        // 注册已定义的方法
        this.registerMethods();

        logger.debug(`✅ Agent '${options.name}' 已创建 (DID: ${userDid})`);
      }

      public registerMethods(): void {
        // 查找所有标记了装饰器的方法
        const prototype = Object.getPrototypeOf(this);
        const propertyNames = Object.getOwnPropertyNames(prototype);

        for (const propertyName of propertyNames) {
          if (propertyName.startsWith('_') || propertyName === 'constructor') {
            continue;
          }

          const descriptor = Object.getOwnPropertyDescriptor(prototype, propertyName);
          if (!descriptor || typeof descriptor.value !== 'function') {
            continue;
          }

          const method = descriptor.value;

          // 检查API装饰器
          if ((method as any)._apiPath) {
            const path = (method as any)._apiPath;
            logger.debug(`  - 注册 API: ${path} -> ${propertyName}`);

            // 创建绑定的处理器
            const boundHandler = method.bind(this);
            this._agent.apiRoutes.set(path, boundHandler);
          }

          // 检查消息处理器装饰器
          if ((method as any)._messageType) {
            const msgType = (method as any)._messageType;
            logger.debug(`  - 注册消息处理器: ${msgType} -> ${propertyName}`);

            // 创建绑定的处理器
            const boundHandler = method.bind(this);
            this._agent.messageHandlers.set(msgType, boundHandler);
          }

          // 检查群组事件处理器装饰器
          if ((method as any)._groupEventInfo) {
            const groupInfo = (method as any)._groupEventInfo;
            const groupId = groupInfo.groupId;
            const eventType = groupInfo.eventType;
            logger.debug(`  - 注册群组事件处理器: ${groupId || 'all'}/${eventType || 'all'} -> ${propertyName}`);

            // 创建绑定的处理器
            const boundHandler = method.bind(this);
            const key = `${groupId || '*'}:${eventType || '*'}`;
            if (!this._agent.groupEventHandlers.has(key)) {
              this._agent.groupEventHandlers.set(key, []);
            }
            this._agent.groupEventHandlers.get(key)!.push(boundHandler);
          }
        }
      }

      get agent(): Agent {
        return this._agent;
      }

      get tags(): string[] {
        return this._tags;
      }
    };
  };
}

/**
 * 类方法API装饰器
 */
export function classApi(
  path: string,
  options?: {
    methods?: string[];
    description?: string;
    parameters?: Record<string, any>;
    returns?: string;
    autoWrap?: boolean;
  }
) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    // 设置API路径
    descriptor.value._apiPath = path;
    descriptor.value._isClassMethod = true;

    // 设置能力元数据
    const capabilityMeta = {
      name: propertyKey,
      description: options?.description || descriptor.value.__doc__ || `API: ${path}`,
      publishAs: "expose_api",
      parameters: options?.parameters || {},
      returns: options?.returns || "object"
    };
    descriptor.value._capabilityMeta = capabilityMeta;

    logger.debug(`🔗 API装饰器应用: ${path} -> ${propertyKey}`);
    return descriptor;
  };
}

/**
 * 类方法消息处理器装饰器
 */
export function classMessageHandler(
  msgType: string,
  options?: {
    description?: string;
    autoWrap?: boolean;
  }
) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    // 设置消息类型
    descriptor.value._messageType = msgType;

    // 设置能力元数据（如果提供了描述）
    if (options?.description) {
      const capabilityMeta = {
        name: propertyKey,
        description: options.description || descriptor.value.__doc__ || `消息处理器: ${msgType}`,
        publishAs: "message_handler"
      };
      descriptor.value._capabilityMeta = capabilityMeta;
    }

    logger.debug(`💬 消息处理器装饰器应用: ${msgType} -> ${propertyKey}`);
    return descriptor;
  };
}

/**
 * 群组事件处理器装饰器
 */
export function groupEventMethod(groupId?: string, eventType?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    descriptor.value._groupEventInfo = {
      groupId,
      eventType
    };

    logger.debug(`✅ 群组事件处理器装饰器应用: ${groupId || 'all'}/${eventType || 'all'} -> ${propertyKey}`);
    return descriptor;
  };
}

// ===== 函数式风格工厂函数 =====

/**
 * 从DID字符串创建Agent实例
 */
export function createAgent(
  didStr: string,
  name: string,
  options?: {
    shared?: boolean;
    prefix?: string;
    primaryAgent?: boolean;
  }
): Agent {
  const anpUser = ANPUser.fromDid(didStr);
  return AgentManager.createAgent(anpUser, {
    name,
    shared: options?.shared || false,
    prefix: options?.prefix,
    primaryAgent: options?.primaryAgent || true
  });
}

/**
 * 从用户名创建Agent实例
 */
export function createAgentFromName(
  userName: string,
  agentName: string,
  options?: {
    shared?: boolean;
    prefix?: string;
    primaryAgent?: boolean;
  }
): Agent {
  const didStr = getUserByName(userName);
  return createAgent(didStr, agentName, options);
}

/**
 * 创建共享DID的Agent实例
 */
export function createSharedAgent(
  didStr: string,
  name: string,
  prefix: string,
  primaryAgent: boolean = false
): Agent {
  return createAgent(didStr, name, {
    shared: true,
    prefix,
    primaryAgent
  });
}

// ===== 函数式风格装饰器适配函数 =====

/**
 * 函数式API装饰器
 */
export function agentApi(
  agent: Agent,
  path: string,
  options?: {
    methods?: string[];
    description?: string;
    autoWrap?: boolean;
  }
) {
  return function (func: Function) {
    // 设置能力元数据（如果提供了描述）
    if (options?.description) {
      const capabilityMeta = {
        name: func.name,
        description: options.description || func.toString() || `API: ${path}`,
        publishAs: "expose_api"
      };
      (func as any)._capabilityMeta = capabilityMeta;
    }

    // 注册到Agent的API路由
    agent.apiRoutes.set(path, func);
    logger.debug(`🔗 函数式API注册: ${path} -> ${func.name}`);

    return func;
  };
}

/**
 * 函数式消息处理器装饰器
 */
export function agentMessageHandler(
  agent: Agent,
  msgType: string,
  options?: {
    description?: string;
    autoWrap?: boolean;
  }
) {
  return function (func: Function) {
    // 设置能力元数据（如果提供了描述）
    if (options?.description) {
      const capabilityMeta = {
        name: func.name,
        description: options.description || func.toString() || `消息处理器: ${msgType}`,
        publishAs: "message_handler"
      };
      (func as any)._capabilityMeta = capabilityMeta;
    }

    // 注册到Agent的消息处理器
    agent.messageHandlers.set(msgType, func);
    logger.debug(`💬 函数式消息处理器注册: ${msgType} -> ${func.name}`);

    return func;
  };
}

/**
 * 注册群组事件处理函数
 */
export function registerGroupEventHandler(
  agent: Agent,
  groupId?: string,
  eventType?: string
) {
  return function (func: Function) {
    const key = `${groupId || '*'}:${eventType || '*'}`;
    if (!agent.groupEventHandlers.has(key)) {
      agent.groupEventHandlers.set(key, []);
    }
    agent.groupEventHandlers.get(key)!.push(func);

    logger.debug(`✅ 函数式群组事件处理器注册: ${groupId || 'all'}/${eventType || 'all'} -> ${func.name}`);
    return func;
  };
}

/**
 * 通用能力装饰器（类方法版本）
 */
export function classCapability(options: {
  name?: string;
  description?: string;
  inputSchema?: any;
  outputSchema?: any;
  tags?: string[];
  publishAs?: 'api' | 'message' | 'group_event' | 'local_method' | 'multiple';
  path?: string;
  msgType?: string;
  groupId?: string;
  eventType?: string;
  autoWrap?: boolean;
}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;

    // 设置能力元数据
    const capabilityMeta = {
      name: options.name || propertyKey,
      description: options.description || method.__doc__ || `能力: ${options.name || propertyKey}`,
      inputSchema: options.inputSchema || {},
      outputSchema: options.outputSchema || {},
      tags: options.tags || [],
      publishAs: options.publishAs || 'api'
    };
    method._capabilityMeta = capabilityMeta;

    // 根据发布方式设置额外属性
    if (['api', 'multiple'].includes(options.publishAs || 'api') && options.path) {
      method._apiPath = options.path;
    }

    if (['message', 'multiple'].includes(options.publishAs || 'api') && options.msgType) {
      method._messageType = options.msgType;
    }

    if (['group_event', 'multiple'].includes(options.publishAs || 'api')) {
      method._groupEventInfo = {
        groupId: options.groupId,
        eventType: options.eventType
      };
    }

    logger.debug(`🎯 能力装饰器应用: ${propertyKey} (${options.publishAs || 'api'})`);
    return descriptor;
  };
}

/**
 * 通用能力装饰器（函数版本）
 */
export function agentCapability(
  agent: Agent,
  options: {
    name?: string;
    description?: string;
    inputSchema?: any;
    outputSchema?: any;
    tags?: string[];
    publishAs?: 'api' | 'message' | 'group_event' | 'local_method' | 'multiple';
    path?: string;
    msgType?: string;
    groupId?: string;
    eventType?: string;
    autoWrap?: boolean;
  }
) {
  return function (func: Function) {
    // 设置能力元数据
    const capabilityMeta = {
      name: options.name || func.name,
      description: options.description || func.toString() || `能力: ${options.name || func.name}`,
      inputSchema: options.inputSchema || {},
      outputSchema: options.outputSchema || {},
      tags: options.tags || [],
      publishAs: options.publishAs || 'api'
    };
    (func as any)._capabilityMeta = capabilityMeta;

    // 根据发布方式注册
    if (['api', 'multiple'].includes(options.publishAs || 'api') && options.path) {
      agent.apiRoutes.set(options.path, func);
    }

    if (['message', 'multiple'].includes(options.publishAs || 'api') && options.msgType) {
      agent.messageHandlers.set(options.msgType, func);
    }

    if (['group_event', 'multiple'].includes(options.publishAs || 'api')) {
      const key = `${options.groupId || '*'}:${options.eventType || '*'}`;
      if (!agent.groupEventHandlers.has(key)) {
        agent.groupEventHandlers.set(key, []);
      }
      agent.groupEventHandlers.get(key)!.push(func);
    }

    logger.debug(`🎯 函数式能力注册: ${func.name} (${options.publishAs || 'api'})`);
    return func;
  };
}