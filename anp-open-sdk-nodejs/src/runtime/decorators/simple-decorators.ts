/**
 * 简化的类型安全装饰器实现
 * 解决TypeScript装饰器签名问题
 */

import { Agent, AgentOptions } from '../core/agent';
import { AgentManager } from '../core/agent-manager';
import { ANPUser } from '../../foundation/user';
import { getUserDataManager } from '../../foundation/user';

// ===== 元数据符号定义 =====
const API_PATH_SYMBOL = Symbol('apiPath');
const API_OPTIONS_SYMBOL = Symbol('apiOptions');
const MESSAGE_TYPE_SYMBOL = Symbol('messageType');
const MESSAGE_OPTIONS_SYMBOL = Symbol('messageOptions');
const GROUP_EVENT_SYMBOL = Symbol('groupEvent');
const IS_CLASS_METHOD_SYMBOL = Symbol('isClassMethod');

// ===== 类型定义 =====
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

// ===== 简化的装饰器实现 =====

/**
 * API装饰器 - 使用标准的方法装饰器签名
 */
export function classApi(path: string, options: ApiDecoratorOptions = {}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    if (method && typeof method === 'function') {
      // 使用Symbol存储元数据
      method[API_PATH_SYMBOL] = path;
      method[API_OPTIONS_SYMBOL] = options;
      method[IS_CLASS_METHOD_SYMBOL] = true;
    }
    // 不返回任何值，保持原方法不变
  };
}

/**
 * 消息处理器装饰器
 */
export function classMessageHandler(msgType: string, options: MessageHandlerOptions = {}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    if (method && typeof method === 'function') {
      method[MESSAGE_TYPE_SYMBOL] = msgType;
      method[MESSAGE_OPTIONS_SYMBOL] = options;
    }
  };
}

/**
 * 群组事件处理器装饰器
 */
export function groupEventMethod(groupId?: string, eventType?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    if (method && typeof method === 'function') {
      method[GROUP_EVENT_SYMBOL] = { groupId, eventType };
    }
  };
}

/**
 * Agent类装饰器
 */
export function agentClass(options: AgentClassOptions) {
  return function <T extends new (...args: any[]) => any>(constructor: T) {
    return class extends constructor {
      public _agent!: Agent;
      public _agentOptions = options;

      constructor(...args: any[]) {
        super(...args);
        this.initializeAgent();
      }

      private initializeAgent(): void {
        // 获取DID
        let userDid = options.did;
        if (!userDid) {
          userDid = getFirstAvailableUser();
        }

        // 创建ANPUser - 使用同步版本
        const anpUser = ANPUser.fromDidSync(userDid);

        // 创建Agent
        this._agent = AgentManager.createAgent(anpUser, {
          name: options.name,
          shared: options.shared || false,
          prefix: options.prefix,
          primaryAgent: options.primaryAgent || false
        });

        // 注册方法
        this.registerMethods();
      }

      private registerMethods(): void {
        const prototype = Object.getPrototypeOf(this);
        const propertyNames = Object.getOwnPropertyNames(prototype);

        for (const propertyName of propertyNames) {
          if (propertyName === 'constructor' || propertyName.startsWith('_')) {
            continue;
          }

          const descriptor = Object.getOwnPropertyDescriptor(prototype, propertyName);
          if (!descriptor || typeof descriptor.value !== 'function') {
            continue;
          }

          const method = descriptor.value;

          // 检查API装饰器
          if (method[API_PATH_SYMBOL]) {
            const apiPath = method[API_PATH_SYMBOL];
            const boundHandler = method.bind(this);
            this._agent.apiRoutes.set(apiPath, boundHandler);
          }

          // 检查消息处理器装饰器
          if (method[MESSAGE_TYPE_SYMBOL]) {
            const messageType = method[MESSAGE_TYPE_SYMBOL];
            const boundHandler = method.bind(this);
            this._agent.messageHandlers.set(messageType, boundHandler);
          }

          // 检查群组事件处理器装饰器
          if (method[GROUP_EVENT_SYMBOL]) {
            const { groupId, eventType } = method[GROUP_EVENT_SYMBOL];
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
    } as T;
  };
}

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

// ===== 工具函数 =====
function getFirstAvailableUser(): string {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  if (!allUsers || allUsers.length === 0) {
    throw new Error("系统中没有可用的用户");
  }
  return allUsers[0].did;
}

/**
 * 创建单个Agent实例
 */
export function createAgent(options: AgentClassOptions): Agent {
  let userDid = options.did;
  if (!userDid) {
    userDid = getFirstAvailableUser();
  }

  const anpUser = ANPUser.fromDidSync(userDid);
  return AgentManager.createAgent(anpUser, {
    name: options.name,
    shared: options.shared || false,
    prefix: options.prefix,
    primaryAgent: options.primaryAgent || false
  });
}


/**
 * 全局消息管理器
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
}

/**
 * 创建带代码的Agent系统
 */
export async function createAgentsWithCode(
  agentDict: Record<string, any>,
  userDid?: string
): Promise<{ agents: Agent[], manager: typeof AgentManager }> {
  const agents: Agent[] = [];
  
  for (const [agentName, agentInfo] of Object.entries(agentDict)) {
    const agent = createAgent({
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
  
  return {
    agents,
    manager: AgentManager
  };
}

// ===== Python兼容的函数式API =====

/**
 * 创建共享Agent - 兼容Python的create_shared_agent
 */
export function createSharedAgent(
  didStr: string,
  name: string,
  prefix: string,
  primaryAgent: boolean
): Agent {
  const anpUser = ANPUser.fromDidSync(didStr);
  return AgentManager.createAgent(anpUser, {
    name,
    shared: true,
    prefix,
    primaryAgent
  });
}

/**
 * Agent API装饰器函数 - 兼容Python的@agent_api
 */
export function agentApi(agent: Agent, path: string) {
  return function(handler: Function) {
    agent.apiRoutes.set(path, handler);
    return handler;
  };
}

// ===== 导出别名 =====
export { classApi as api };
export { classMessageHandler as messageHandler };
export { classMessageHandler as agentMessageHandler };
export { groupEventMethod as groupEventHandler };
export { agentClass as agent_class };
export { AgentManager };
