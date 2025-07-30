/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Agent, AgentOptions } from '../core/agent';
import { AgentManager } from '../core/agent-manager';
import { ANPUser } from '../../foundation/user';
import { getUserDataManager } from '../../foundation/user';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('TypeSafeDecorators');

// ===== 类型安全的装饰器接口定义 =====

export interface ApiDecoratorOptions {
  methods?: string[];
  description?: string;
  parameters?: Record<string, any>;
  returns?: string;
  autoWrap?: boolean;
}

export interface MessageHandlerOptions {
  description?: string;
  autoWrap?: boolean;
}

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

// ===== 类型安全的方法装饰器 =====

/**
 * 类型安全的API装饰器
 * 使用void返回类型，避免类型冲突
 */
export function classApi(path: string, options?: ApiDecoratorOptions) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor): void {
    // 在方法上设置元数据，而不是修改返回类型
    const method = descriptor.value;
    if (method) {
      // 使用Symbol作为元数据键，避免命名冲突
      (method as any)[API_PATH_SYMBOL] = path;
      (method as any)[API_OPTIONS_SYMBOL] = options || {};
      (method as any)[IS_CLASS_METHOD_SYMBOL] = true;
      
      logger.debug(`🔗 API装饰器应用: ${path} -> ${propertyKey}`);
    }
  };
}

/**
 * 类型安全的消息处理器装饰器
 */
export function classMessageHandler(msgType: string, options?: MessageHandlerOptions) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor): void {
    const method = descriptor.value;
    if (method) {
      (method as any)[MESSAGE_TYPE_SYMBOL] = msgType;
      (method as any)[MESSAGE_OPTIONS_SYMBOL] = options || {};
      
      logger.debug(`💬 消息处理器装饰器应用: ${msgType} -> ${propertyKey}`);
    }
  };
}

/**
 * 类型安全的群组事件处理器装饰器
 */
export function groupEventMethod(groupId?: string, eventType?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor): void {
    const method = descriptor.value;
    if (method) {
      (method as any)[GROUP_EVENT_SYMBOL] = { groupId, eventType };
      
      logger.debug(`✅ 群组事件处理器装饰器应用: ${groupId || 'all'}/${eventType || 'all'} -> ${propertyKey}`);
    }
  };
}

// ===== 元数据符号定义 =====
const API_PATH_SYMBOL = Symbol('apiPath');
const API_OPTIONS_SYMBOL = Symbol('apiOptions');
const MESSAGE_TYPE_SYMBOL = Symbol('messageType');
const MESSAGE_OPTIONS_SYMBOL = Symbol('messageOptions');
const GROUP_EVENT_SYMBOL = Symbol('groupEvent');
const IS_CLASS_METHOD_SYMBOL = Symbol('isClassMethod');

// ===== 元数据访问工具函数 =====
export function getApiPath(method: any): string | undefined {
  return method[API_PATH_SYMBOL];
}

export function getApiOptions(method: any): ApiDecoratorOptions | undefined {
  return method[API_OPTIONS_SYMBOL];
}

export function getMessageType(method: any): string | undefined {
  return method[MESSAGE_TYPE_SYMBOL];
}

export function getMessageOptions(method: any): MessageHandlerOptions | undefined {
  return method[MESSAGE_OPTIONS_SYMBOL];
}

export function getGroupEventInfo(method: any): { groupId?: string; eventType?: string } | undefined {
  return method[GROUP_EVENT_SYMBOL];
}

export function isClassMethod(method: any): boolean {
  return !!method[IS_CLASS_METHOD_SYMBOL];
}

// ===== 类型安全的类装饰器 =====

/**
 * 类型安全的Agent类装饰器
 * 使用类型参数确保返回正确的类型
 */
export function agentClass<T extends new (...args: any[]) => any>(options: AgentClassOptions) {
  return function (constructor: T): T {
    // 创建增强的类，保持原有类型
    class AgentClass extends constructor {
      public _agent!: Agent;
      public _tags: string[];

      constructor(...args: any[]) {
        super(...args);
        this._tags = options.tags || [];
        // 同步初始化Agent
        this.initializeAgentSync();
      }

      public initializeAgentSync(): void {
        // 获取 DID
        let userDid = options.did;
        if (!userDid) {
          // 如果没有提供 DID，使用第一个可用用户
          userDid = getFirstAvailableUser();
        }

        // 同步创建 ANPUser（从缓存中获取）
        const anpUser = ANPUser.fromDidSync(userDid);

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

      public async initializeAgent(): Promise<void> {
        // 保留异步版本以备后用
        this.initializeAgentSync();
      }

      public registerMethods(): void {
        logger.debug(`🔍 开始注册 Agent '${options.name}' 的方法...`);
        
        // 查找所有标记了装饰器的方法 - 需要遍历整个原型链
        let currentProto = Object.getPrototypeOf(this);
        const allPropertyNames = new Set<string>();
        
        // 遍历原型链，收集所有方法名
        while (currentProto && currentProto !== Object.prototype) {
          const propertyNames = Object.getOwnPropertyNames(currentProto);
          propertyNames.forEach(name => allPropertyNames.add(name));
          currentProto = Object.getPrototypeOf(currentProto);
        }
        
        logger.debug(`🔍 找到 ${allPropertyNames.size} 个属性/方法`);

        for (const propertyName of allPropertyNames) {
          if (propertyName.startsWith('_') || propertyName === 'constructor') {
            continue;
          }

          // 尝试从实例和原型链中查找方法
          let method: any = null;
          let currentObj: any = this;
          
          while (currentObj && !method) {
            const descriptor = Object.getOwnPropertyDescriptor(currentObj, propertyName);
            if (descriptor && typeof descriptor.value === 'function') {
              method = descriptor.value;
              break;
            }
            currentObj = Object.getPrototypeOf(currentObj);
          }
          
          if (!method) {
            continue;
          }

          // 检查API装饰器
          const apiPath = getApiPath(method);
          if (apiPath) {
            // 计算完整路径 - 考虑Agent前缀
            const fullPath = this._agent.prefix ? `${this._agent.prefix}${apiPath}` : apiPath;
            logger.debug(`  ✅ 注册 API: ${fullPath} -> ${propertyName} (原始路径: ${apiPath})`);
            const boundHandler = method.bind(this);
            this._agent.apiRoutes.set(fullPath, boundHandler);
          }

          // 检查消息处理器装饰器
          const messageType = getMessageType(method);
          if (messageType) {
            logger.debug(`  ✅ 注册消息处理器: ${messageType} -> ${propertyName}`);
            const boundHandler = method.bind(this);
            this._agent.messageHandlers.set(messageType, boundHandler);
          }

          // 检查群组事件处理器装饰器
          const groupEventInfo = getGroupEventInfo(method);
          if (groupEventInfo) {
            const { groupId, eventType } = groupEventInfo;
            logger.debug(`  ✅ 注册群组事件处理器: ${groupId || 'all'}/${eventType || 'all'} -> ${propertyName}`);
            
            const boundHandler = method.bind(this);
            const key = `${groupId || '*'}:${eventType || '*'}`;
            if (!this._agent.groupEventHandlers.has(key)) {
              this._agent.groupEventHandlers.set(key, []);
            }
            this._agent.groupEventHandlers.get(key)!.push(boundHandler);
          }
        }
        
        logger.debug(`🔍 注册完成，Agent '${options.name}' 共有 ${this._agent.apiRoutes.size} 个API路由`);
      }

      get agent(): Agent {
        return this._agent;
      }

      get tags(): string[] {
        return this._tags;
      }
    }

    // 返回增强的类，保持原有类型
    return AgentClass as T;
  };
}

// ===== 工具函数 =====

/**
 * 获取第一个可用用户的 DID
 */
function getFirstAvailableUser(): string {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  if (!allUsers || allUsers.length === 0) {
    throw new Error("系统中没有可用的用户");
  }
  return allUsers[0].did;
}

// ===== 创建Agent的工厂函数 =====

/**
 * 创建单个Agent实例
 */
export async function createAgent(options: AgentClassOptions): Promise<Agent> {
  // 获取 DID
  let userDid = options.did;
  if (!userDid) {
    userDid = getFirstAvailableUser();
  }

  // 创建 ANPUser
  const anpUser = await ANPUser.fromDid(userDid);

  // 创建 Agent
  const agent = AgentManager.createAgent(anpUser, {
    name: options.name,
    shared: options.shared || false,
    prefix: options.prefix,
    primaryAgent: options.primaryAgent || false
  });

  logger.debug(`✅ Agent '${options.name}' 已创建 (DID: ${userDid})`);
  return agent;
}

/**
 * 创建共享Agent实例
 */
export async function createSharedAgent(options: Omit<AgentClassOptions, 'shared'>): Promise<Agent> {
  return await createAgent({ ...options, shared: true });
}

/**
 * 全局消息管理器（简化版）
 */
export class GlobalMessageManager {
  private static instance: GlobalMessageManager;
  private messageHandlers = new Map<string, Function[]>();

  static getInstance(): GlobalMessageManager {
    if (!GlobalMessageManager.instance) {
      GlobalMessageManager.instance = new GlobalMessageManager();
    }
    return GlobalMessageManager.instance;
  }

  static addHandler(messageType: string, handler: Function): void {
    const instance = GlobalMessageManager.getInstance();
    if (!instance.messageHandlers.has(messageType)) {
      instance.messageHandlers.set(messageType, []);
    }
    instance.messageHandlers.get(messageType)!.push(handler);
  }

  static getHandlers(messageType: string): Function[] {
    const instance = GlobalMessageManager.getInstance();
    return instance.messageHandlers.get(messageType) || [];
  }

  static clearHandlers(): void {
    const instance = GlobalMessageManager.getInstance();
    instance.messageHandlers.clear();
  }

  static listHandlers(): Record<string, number> {
    const instance = GlobalMessageManager.getInstance();
    const result: Record<string, number> = {};
    for (const [messageType, handlers] of instance.messageHandlers) {
      result[messageType] = handlers.length;
    }
    return result;
  }

  addHandler(messageType: string, handler: Function): void {
    GlobalMessageManager.addHandler(messageType, handler);
  }

  getHandlers(messageType: string): Function[] {
    return GlobalMessageManager.getHandlers(messageType);
  }
}

/**
 * 创建带代码的Agent系统（复制Python功能）
 */
export async function createAgentsWithCode(
  agentDict: Record<string, any>,
  userDid?: string
): Promise<{ agents: Agent[], manager: AgentManager }> {
  const agents: Agent[] = [];
  
  logger.debug(`开始创建Agent系统...`);
  logger.debug(`  DID: ${userDid || '使用默认用户'}`);
  logger.debug(`  共有${Object.keys(agentDict).length}个agent`);
  
  for (const [agentName, agentInfo] of Object.entries(agentDict)) {
    const mode = agentInfo.shared ? "共享" : "独占";
    const primary = agentInfo.primaryAgent ? " (主)" : "";
    const prefix = agentInfo.prefix ? ` prefix:${agentInfo.prefix}` : "";
    
    logger.debug(`  - ${agentName}: ${mode}${primary}${prefix}`);
    
    // 创建Agent
    const agent = await createAgent({
      name: agentName,
      did: userDid || agentInfo.did,
      shared: agentInfo.shared || false,
      prefix: agentInfo.prefix,
      primaryAgent: agentInfo.primaryAgent || false,
      description: agentInfo.description,
      version: agentInfo.version,
      tags: agentInfo.tags
    });
    
    agents.push(agent);
  }
  
  logger.debug(`✅ Agent系统创建完成，共创建${agents.length}个Agent`);
  
  return {
    agents,
    manager: AgentManager
  };
}

// ===== 导出兼容性别名 =====
export { classApi as api };
export { classApi as agentApi };
export { classMessageHandler as messageHandler };
export { classMessageHandler as agentMessageHandler };
export { groupEventMethod as groupEventHandler };
export { agentClass as agent_class };

// 导出AgentManager以供示例使用
export { AgentManager };
