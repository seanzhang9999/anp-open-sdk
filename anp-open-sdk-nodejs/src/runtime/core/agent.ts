/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { ANPUser } from '@foundation/user';
import { getLogger } from '@foundation/utils';
import { 
  DecoratorMetadataExtractor, 
  ApiMetadata, 
  MessageHandlerMetadata, 
  GroupEventHandlerMetadata 
} from '../decorators';

const logger = getLogger('Agent');

export interface AgentConfig {
  anpUser: ANPUser;
  name: string;
  shared?: boolean;
  prefix?: string;
  primaryAgent?: boolean;
}

export interface RequestContext {
  method: string;
  path: string;
  headers: Record<string, string>;
  body?: any;
  query?: Record<string, string>;
  callerDid?: string;
}

export interface ResponseContext {
  statusCode: number;
  headers: Record<string, string>;
  body: any;
}

export class Agent {
  public anpUser: ANPUser;
  public name: string;
  public shared: boolean;
  public prefix: string;
  public primaryAgent: boolean;
  
  // API和消息处理器注册表
  private apiRegistry: Map<string, ApiMetadata> = new Map();
  private messageHandlers: Map<string, MessageHandlerMetadata> = new Map();
  private groupEventHandlers: Map<string, GroupEventHandlerMetadata> = new Map();
  
  // WebSocket连接管理
  private wsConnections: Map<string, any> = new Map();
  private sseClients: Set<any> = new Set();

  constructor(config: AgentConfig) {
    this.anpUser = config.anpUser;
    this.name = config.name;
    this.shared = config.shared ?? false;
    this.prefix = config.prefix ?? '';
    this.primaryAgent = config.primaryAgent ?? false;

    // 初始化时扫描装饰器
    this.scanDecorators();
    
    logger.info(`🤖 Agent初始化完成: ${this.name} (DID: ${this.anpUser.id})`);
  }

  /**
   * 扫描类上的装饰器并注册API和处理器
   */
  private scanDecorators(): void {
    const constructor = this.constructor;
    
    // 扫描API装饰器
    const apis = DecoratorMetadataExtractor.getApiMetadata(constructor);
    for (const api of apis) {
      // 保持原始路径，不添加prefix（prefix在路由层处理）
      const key = `${api.method}:${api.path}`;
      this.apiRegistry.set(key, api);
      logger.debug(`注册API: ${key} -> ${api.methodName}`);
    }
    
    // 扫描消息处理器
    const messageHandlers = DecoratorMetadataExtractor.getMessageHandlerMetadata(constructor);
    for (const handler of messageHandlers) {
      this.messageHandlers.set(handler.eventType, handler);
      logger.debug(`注册消息处理器: ${handler.eventType} -> ${handler.methodName}`);
    }
    
    // 扫描群组事件处理器
    const groupHandlers = DecoratorMetadataExtractor.getGroupEventHandlerMetadata(constructor);
    for (const handler of groupHandlers) {
      this.groupEventHandlers.set(handler.eventType, handler);
      logger.debug(`注册群组事件处理器: ${handler.eventType} -> ${handler.methodName}`);
    }
  }

  /**
   * 处理HTTP请求
   */
  public async handleRequest(context: RequestContext): Promise<ResponseContext> {
    try {
      const key = `${context.method}:${context.path}`;
      const api = this.apiRegistry.get(key);
      
      if (!api) {
        return {
          statusCode: 404,
          headers: { 'Content-Type': 'application/json' },
          body: { error: `API not found: ${key}` }
        };
      }

      // 检查方法是否存在
      const method = (this as any)[api.methodName];
      if (typeof method !== 'function') {
        return {
          statusCode: 500,
          headers: { 'Content-Type': 'application/json' },
          body: { error: `Handler method not found: ${api.methodName}` }
        };
      }

      // 调用方法
      const result = await method.call(this, context);
      
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: result
      };
      
    } catch (error) {
      logger.error(`请求处理失败: ${context.method} ${context.path}:`, error);
      return {
        statusCode: 500,
        headers: { 'Content-Type': 'application/json' },
        body: { error: 'Internal server error' }
      };
    }
  }

  /**
   * 处理消息
   */
  public async handleMessage(eventType: string, payload: any): Promise<any> {
    try {
      const handler = this.messageHandlers.get(eventType);
      
      if (!handler) {
        logger.warn(`未找到消息处理器: ${eventType}`);
        return { error: `No message handler for: ${eventType}` };
      }

      const method = (this as any)[handler.methodName];
      if (typeof method !== 'function') {
        throw new Error(`Handler method not found: ${handler.methodName}`);
      }

      return await method.call(this, payload);
      
    } catch (error) {
      logger.error(`消息处理失败: ${eventType}:`, error);
      throw error;
    }
  }

  /**
   * 处理群组事件
   */
  public async handleGroupEvent(eventType: string, payload: any): Promise<any> {
    try {
      const handler = this.groupEventHandlers.get(eventType);
      
      if (!handler) {
        logger.warn(`未找到群组事件处理器: ${eventType}`);
        return { error: `No group event handler for: ${eventType}` };
      }

      const method = (this as any)[handler.methodName];
      if (typeof method !== 'function') {
        throw new Error(`Handler method not found: ${handler.methodName}`);
      }

      return await method.call(this, payload);
      
    } catch (error) {
      logger.error(`群组事件处理失败: ${eventType}:`, error);
      throw error;
    }
  }

  /**
   * 获取所有API定义
   */
  public getApis(): ApiMetadata[] {
    return Array.from(this.apiRegistry.values());
  }

  /**
   * 获取所有消息处理器
   */
  public getMessageHandlers(): MessageHandlerMetadata[] {
    return Array.from(this.messageHandlers.values());
  }

  /**
   * 获取所有群组事件处理器
   */
  public getGroupEventHandlers(): GroupEventHandlerMetadata[] {
    return Array.from(this.groupEventHandlers.values());
  }

  /**
   * 添加WebSocket连接
   */
  public addWsConnection(connectionId: string, connection: any): void {
    this.wsConnections.set(connectionId, connection);
    logger.debug(`添加WebSocket连接: ${connectionId}`);
  }

  /**
   * 移除WebSocket连接
   */
  public removeWsConnection(connectionId: string): void {
    this.wsConnections.delete(connectionId);
    logger.debug(`移除WebSocket连接: ${connectionId}`);
  }

  /**
   * 添加SSE客户端
   */
  public addSseClient(client: any): void {
    this.sseClients.add(client);
    logger.debug('添加SSE客户端');
  }

  /**
   * 移除SSE客户端
   */
  public removeSseClient(client: any): void {
    this.sseClients.delete(client);
    logger.debug('移除SSE客户端');
  }

  /**
   * 向所有WebSocket连接广播消息
   */
  public broadcastToWs(message: any): void {
    for (const [connectionId, connection] of this.wsConnections) {
      try {
        if (connection && connection.readyState === 1) { // WebSocket.OPEN
          connection.send(JSON.stringify(message));
        }
      } catch (error) {
        logger.error(`广播到WebSocket ${connectionId} 失败:`, error);
        this.removeWsConnection(connectionId);
      }
    }
  }

  /**
   * 向所有SSE客户端广播消息
   */
  public broadcastToSse(message: any): void {
    for (const client of this.sseClients) {
      try {
        client.write(`data: ${JSON.stringify(message)}\n\n`);
      } catch (error) {
        logger.error('广播到SSE客户端失败:', error);
        this.removeSseClient(client);
      }
    }
  }

  /**
   * 转换为字典格式（用于序列化）
   */
  public toDict(): Record<string, any> {
    return {
      name: this.name,
      did: this.anpUser.id,
      shared: this.shared,
      prefix: this.prefix,
      primaryAgent: this.primaryAgent,
      apis: this.getApis(),
      messageHandlers: this.getMessageHandlers().map(h => h.eventType),
      groupEventHandlers: this.getGroupEventHandlers().map(h => h.eventType)
    };
  }
}
