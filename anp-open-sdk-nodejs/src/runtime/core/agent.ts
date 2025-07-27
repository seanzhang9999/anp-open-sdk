/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { ANPUser } from '../../foundation/user';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('Agent');

export interface ApiRoute {
  path: string;
  handler: Function;
  methods?: string[];
}

export interface MessageHandler {
  type: string;
  handler: Function;
}

export interface GroupEventHandler {
  groupId?: string;
  eventType?: string;
  handler: Function;
}

export interface AgentOptions {
  name: string;
  shared?: boolean;
  prefix?: string;
  primaryAgent?: boolean;
}

/**
 * Agent类 - 功能载体，通过装饰器发布API和消息处理功能
 * 
 * 这个类承担了从ANPUser迁移过来的功能：
 * 1. API暴露功能 (api装饰器)
 * 2. 消息处理器注册 (message_handler装饰器)
 * 3. 群组事件处理 (group_event_handler装饰器)
 * 4. 请求处理核心逻辑 (handleRequest方法)
 */
export class Agent {
  public readonly anpUser: ANPUser;
  public readonly name: string;
  public readonly shared: boolean;
  public readonly prefix?: string;
  public readonly primaryAgent: boolean;
  public readonly createdAt: Date;
  
  // 为了向后兼容性，添加id属性
  public readonly anpUserId: string;
  
  // 功能注册表 - 从ANPUser迁移过来
  public readonly apiRoutes: Map<string, Function> = new Map();
  public readonly messageHandlers: Map<string, Function> = new Map();
  public readonly groupEventHandlers: Map<string, Function[]> = new Map();
  public readonly groupGlobalHandlers: Array<{ eventType?: string; handler: Function }> = [];

  constructor(anpUser: ANPUser, options: AgentOptions) {
    this.anpUser = anpUser;
    this.name = options.name;
    this.shared = options.shared || false;
    this.prefix = options.prefix;
    this.primaryAgent = options.primaryAgent || false;
    this.createdAt = new Date();
    
    // 为了向后兼容性，添加id属性
    this.anpUserId = anpUser.id;
    
    logger.debug(`✅ Agent创建成功: ${this.name}`);
    logger.debug(`   DID: ${anpUser.id} (${this.shared ? '共享' : '独占'})`);
    if (this.prefix) {
      logger.debug(`   Prefix: ${this.prefix}`);
    }
    if (this.primaryAgent) {
      logger.debug(`   主Agent: 是`);
    }
  }

  /**
   * API装饰器，用于注册API处理函数
   */
  api(path: string, methods: string[] = ['GET', 'POST']) {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
      const handler = descriptor.value;
      
      // 计算完整路径
      const fullPath = this.prefix ? `${this.prefix}${path}` : path;
      
      // 注册到Agent的路由表
      this.apiRoutes.set(fullPath, handler);
      
      // 注册到ANPUser的API路由系统
      if (!this.anpUser.apiRoutes.has(fullPath)) {
        this.anpUser.apiRoutes.set(fullPath, handler);
      } else {
        const existingHandler = this.anpUser.apiRoutes.get(fullPath);
        if (existingHandler !== handler) {
          logger.warn(`⚠️  API路径冲突: ${fullPath}`);
          logger.warn(`   现有处理器: ${existingHandler?.name || 'unknown'}`);
          logger.warn(`   新处理器: ${handler?.name || 'unknown'} (来自 ${this.name})`);
          logger.warn(`   🔧 覆盖现有处理器`);
        }
        this.anpUser.apiRoutes.set(fullPath, handler);
      }
      
      logger.debug(`🔗 API注册成功: ${this.anpUserId}${fullPath} <- ${this.name}`);
      return descriptor;
    };
  }

  /**
   * 消息处理器装饰器，用于注册消息处理函数
   */
  messageHandler(msgType: string) {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
      const handler = descriptor.value;
      
      // 检查消息处理权限
      if (!this.canHandleMessage()) {
        const errorMsg = this.getMessagePermissionError();
        logger.error(`❌ 消息处理器注册失败: ${errorMsg}`);
        throw new Error(errorMsg);
      }
      
      // 注册到Agent的消息处理器表
      this.messageHandlers.set(msgType, handler);
      
      // 注册到全局消息管理器
      // TODO: 实现GlobalMessageManager
      
      logger.debug(`💬 消息处理器注册成功: ${this.anpUserId}:${msgType} <- ${this.name}`);
      return descriptor;
    };
  }

  /**
   * 群组事件处理器装饰器，用于注册群组事件处理函数
   */
  groupEventHandler(groupId?: string, eventType?: string) {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
      const handler = descriptor.value;
      
      if (groupId === undefined && eventType === undefined) {
        this.groupGlobalHandlers.push({ handler });
      } else if (groupId === undefined) {
        this.groupGlobalHandlers.push({ eventType, handler });
      } else {
        const key = `${groupId}:${eventType || '*'}`;
        if (!this.groupEventHandlers.has(key)) {
          this.groupEventHandlers.set(key, []);
        }
        this.groupEventHandlers.get(key)!.push(handler);
      }
      
      logger.debug(`✅ 注册群组事件处理器: Agent ${this.name}, 群组 ${groupId || 'all'}, 事件 ${eventType || 'all'}`);
      return descriptor;
    };
  }

  /**
   * 检查是否可以处理消息
   */
  private canHandleMessage(): boolean {
    if (!this.shared) {
      // 独占模式：自动有消息处理权限
      return true;
    } else {
      // 共享模式：只有主Agent可以处理消息
      return this.primaryAgent;
    }
  }

  /**
   * 获取消息权限错误信息
   */
  private getMessagePermissionError(): string {
    if (this.shared && !this.primaryAgent) {
      return (
        `Agent '${this.name}' 无消息处理权限\n` +
        `原因: 共享DID模式下，只有主Agent可以处理消息\n` +
        `当前状态: shared=${this.shared}, primaryAgent=${this.primaryAgent}\n` +
        `解决方案: 设置 primaryAgent=true 或使用独占DID`
      );
    } else {
      return "未知的消息权限错误";
    }
  }

  /**
   * 获取群组事件处理器
   */
  private getGroupEventHandlers(groupId: string, eventType: string): Function[] {
    const handlers: Function[] = [];
    
    // 添加全局处理器
    for (const { eventType: et, handler } of this.groupGlobalHandlers) {
      if (et === undefined || et === eventType) {
        handlers.push(handler);
      }
    }
    
    // 添加特定处理器
    const specificKey = `${groupId}:${eventType}`;
    const wildcardKey = `${groupId}:*`;
    
    if (this.groupEventHandlers.has(specificKey)) {
      handlers.push(...this.groupEventHandlers.get(specificKey)!);
    }
    if (this.groupEventHandlers.has(wildcardKey)) {
      handlers.push(...this.groupEventHandlers.get(wildcardKey)!);
    }
    
    return handlers;
  }

  /**
   * 分发群组事件
   */
  async dispatchGroupEvent(groupId: string, eventType: string, eventData: any): Promise<void> {
    const handlers = this.getGroupEventHandlers(groupId, eventType);
    
    for (const handler of handlers) {
      try {
        const result = handler.call(this, groupId, eventType, eventData);
        if (result && typeof result.then === 'function') {
          await result;
        }
      } catch (error) {
        logger.error(`群组事件处理器出错: ${error}`);
      }
    }
  }

  /**
   * 请求处理核心逻辑
   * 
   * 统一的API调用和消息处理入口
   */
  async handleRequest(reqDid: string, requestData: Record<string, any>, request: any): Promise<any> {
    const reqType = requestData.type;
    
    // 群组消息处理
    if (['group_message', 'group_connect', 'group_members'].includes(reqType)) {
      const handler = this.messageHandlers.get(reqType);
      if (handler) {
        try {
          const result = await this.callHandler(handler, requestData);
          if (typeof result === 'object' && result !== null && 'anp_result' in result) {
            return result;
          }
          return { anp_result: result };
        } catch (error) {
          logger.error(`Group message handling error: ${error}`);
          return { anp_result: { status: 'error', message: String(error) } };
        }
      } else {
        return { anp_result: { status: 'error', message: `No handler for group type: ${reqType}` } };
      }
    }
    
    // API调用处理
    if (reqType === 'api_call') {
      const apiPath = requestData.path;
      
      logger.debug(`🔍 Agent ${this.name} 查找API路径: ${apiPath}`);
      logger.debug(`🔍 Agent ${this.name} 当前所有API路由:`);
      for (const [routePath, routeHandler] of this.apiRoutes) {
        logger.debug(`   - ${routePath}: ${routeHandler.name || 'unknown'}`);
      }
      
      const handler = this.apiRoutes.get(apiPath);
      logger.debug(`🔍 Agent ${this.name} API${apiPath} 对应处理器: ${handler?.name || 'none'}`);
      
      if (handler) {
        try {
          const result = await this.callHandler(handler, requestData, request);
          
          if (typeof result === 'object' && result !== null) {
            const statusCode = (result as any).status_code || 200;
            delete (result as any).status_code;
            
            return {
              status: statusCode,
              headers: { 'Content-Type': 'application/json' },
              body: result
            };
          } else {
            return result;
          }
        } catch (error) {
          logger.error(`API调用错误: ${error}`);
          return {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
            body: { status: 'error', error_message: String(error) }
          };
        }
      } else {
        return {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
          body: { status: 'error', message: `未找到API: ${apiPath}` }
        };
      }
    }
    
    // 消息处理
    else if (reqType === 'message') {
      const msgType = requestData.message_type || '*';
      const handler = this.messageHandlers.get(msgType) || this.messageHandlers.get('*');
      
      if (handler) {
        try {
          const result = await this.callMessageHandler(handler, requestData, request);
          if (typeof result === 'object' && result !== null && 'anp_result' in result) {
            return result;
          }
          return { anp_result: result };
        } catch (error) {
          logger.error(`消息处理错误: ${error}`);
          return { anp_result: { status: 'error', message: String(error) } };
        }
      } else {
        return { anp_result: { status: 'error', message: `未找到消息处理器: ${msgType}` } };
      }
    } else {
      return { anp_result: { status: 'error', message: '未知的请求类型' } };
    }
  }

  /**
   * 调用处理器，自动适配参数格式
   */
  private async callHandler(handler: Function, requestData: any, request?: any): Promise<any> {
    // 检查处理器参数
    const paramCount = handler.length;
    
    if (paramCount === 0) {
      return await handler.call(this);
    } else if (paramCount === 1) {
      return await handler.call(this, requestData);
    } else {
      return await handler.call(this, requestData, request);
    }
  }

  /**
   * 调用消息处理器，自动适配参数格式
   */
  private async callMessageHandler(handler: Function, requestData: any, request?: any): Promise<any> {
    // 构造消息内容
    const msgContent = {
      content: requestData.content || '',
      message_type: requestData.message_type || 'text',
      sender: requestData.req_did || '',
      timestamp: requestData.timestamp || new Date().toISOString(),
    };

    const paramCount = handler.length;
    
    if (paramCount === 0) {
      return await handler.call(this);
    } else if (paramCount === 1) {
      return await handler.call(this, msgContent);
    } else {
      return await handler.call(this, msgContent, request);
    }
  }

  /**
   * 转换为字典格式
   */
  toDict(): Record<string, any> {
    return {
      name: this.name,
      did: this.anpUser.id,
      shared: this.shared,
      prefix: this.prefix,
      primaryAgent: this.primaryAgent,
      createdAt: this.createdAt.toISOString(),
      apiCount: this.apiRoutes.size,
      messageHandlerCount: this.messageHandlers.size,
      groupEventHandlerCount: this.groupEventHandlers.size + this.groupGlobalHandlers.length
    };
  }

  toString(): string {
    return `Agent(name='${this.name}', did='${this.anpUser.id}', shared=${this.shared})`;
  }
}
