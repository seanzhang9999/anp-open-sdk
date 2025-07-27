/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { getLogger } from '../../foundation/utils';

const logger = getLogger('GlobalMessageManager');

export interface MessageHandler {
  did: string;
  msgType: string;
  handler: Function;
  agentName: string;
  registeredAt: Date;
}

export interface GroupAgent {
  id: string;
  name: string;
  port: number;
  metadata: Record<string, any>;
  joinedAt: Date;
}

export interface Message {
  type: string;
  content: any;
  senderId: string;
  groupId: string;
  timestamp: number;
  metadata: Record<string, any>;
}

/**
 * 群组运行器基类
 */
export abstract class GroupRunner {
  protected agents: Map<string, GroupAgent> = new Map();
  protected listeners: Map<string, any> = new Map(); // 在实际实现中应该是Queue类型
  public readonly createdAt: Date;

  constructor(public readonly groupId: string) {
    this.createdAt = new Date();
  }

  /**
   * Agent加入群组时的处理，返回是否允许加入
   */
  async onAgentJoin(agent: GroupAgent): Promise<boolean> {
    return true;
  }

  /**
   * Agent离开群组时的处理
   */
  async onAgentLeave(agent: GroupAgent): Promise<void> {
    // 默认实现为空
  }

  /**
   * 处理群组消息，返回响应消息（可选）
   */
  async onMessage(message: Message): Promise<Message | null> {
    return null;
  }

  /**
   * 检查是否为群组成员
   */
  isMember(agentId: string): boolean {
    return this.agents.has(agentId);
  }

  /**
   * 获取所有成员
   */
  getMembers(): GroupAgent[] {
    return Array.from(this.agents.values());
  }

  /**
   * 移除成员
   */
  async removeMember(agentId: string): Promise<boolean> {
    if (this.agents.has(agentId)) {
      const agent = this.agents.get(agentId)!;
      await this.onAgentLeave(agent);
      this.agents.delete(agentId);
      return true;
    }
    return false;
  }

  /**
   * 注册事件监听器
   */
  registerListener(agentId: string, listener: any): void {
    this.listeners.set(agentId, listener);
  }

  /**
   * 注销事件监听器
   */
  unregisterListener(agentId: string): void {
    this.listeners.delete(agentId);
  }

  /**
   * 广播消息给所有监听器
   */
  async broadcastMessage(message: Record<string, any>): Promise<void> {
    for (const listener of this.listeners.values()) {
      try {
        // 在实际实现中，这里应该是向队列发送消息
        if (listener && typeof listener.send === 'function') {
          await listener.send(message);
        }
      } catch (error) {
        logger.error(`广播消息失败: ${error}`);
      }
    }
  }
}

/**
 * 全局群组管理器
 */
export class GlobalGroupManager {
  // 类级别的群组注册表
  private static groups: Map<string, GroupRunner> = new Map();
  private static groupPatterns: Map<string, typeof GroupRunner> = new Map();
  private static groupStats: Map<string, any> = new Map();

  /**
   * 注册群组运行器
   */
  static registerRunner(groupId: string, runnerClass: typeof GroupRunner, urlPattern?: string): void {
    if (this.groups.has(groupId)) {
      logger.warn(`群组 ${groupId} 已存在，将被覆盖`);
    }

    // 创建运行器实例
    const runner = new (runnerClass as any)(groupId);
    this.groups.set(groupId, runner);

    // 注册URL模式（如果提供）
    if (urlPattern) {
      this.groupPatterns.set(urlPattern, runnerClass);
    }

    // 初始化统计信息
    this.groupStats.set(groupId, {
      createdAt: new Date().toISOString(),
      memberCount: 0,
      messageCount: 0,
      lastActivity: null
    });

    logger.debug(`✅ 群组运行器注册成功: ${groupId}`);
  }

  /**
   * 注销群组运行器
   */
  static unregisterRunner(groupId: string): void {
    if (this.groups.has(groupId)) {
      this.groups.delete(groupId);
      this.groupStats.delete(groupId);
      logger.debug(`🗑️ 群组运行器已注销: ${groupId}`);
    }
  }

  /**
   * 获取群组运行器
   */
  static getRunner(groupId: string): GroupRunner | null {
    return this.groups.get(groupId) || null;
  }

  /**
   * 列出所有群组ID
   */
  static listGroups(): string[] {
    return Array.from(this.groups.keys());
  }

  /**
   * 获取群组统计信息
   */
  static getGroupStats(groupId?: string): Record<string, any> {
    if (groupId) {
      return this.groupStats.get(groupId) || {};
    }
    return Object.fromEntries(this.groupStats);
  }

  /**
   * 更新群组活动统计
   */
  static updateGroupActivity(groupId: string, activityType: string = 'message'): void {
    const stats = this.groupStats.get(groupId);
    if (stats) {
      stats.lastActivity = new Date().toISOString();
      if (activityType === 'message') {
        stats.messageCount += 1;
      }
    }
  }

  /**
   * 清除所有群组（主要用于测试）
   */
  static clearGroups(): void {
    this.groups.clear();
    this.groupPatterns.clear();
    this.groupStats.clear();
    logger.debug("清除所有群组");
  }

  /**
   * 路由群组请求
   */
  static async routeGroupRequest(
    did: string,
    groupId: string,
    requestType: string,
    requestData: Record<string, any>,
    request?: any
  ): Promise<any> {
    // 获取群组运行器
    const runner = this.getRunner(groupId);
    if (!runner) {
      return { status: 'error', message: `群组不存在: ${groupId}` };
    }

    // 更新活动统计
    this.updateGroupActivity(groupId, requestType);

    // 根据请求类型处理
    switch (requestType) {
      case 'join':
        return await this.handleGroupJoin(runner, requestData);
      case 'leave':
        return await this.handleGroupLeave(runner, requestData);
      case 'message':
        return await this.handleGroupMessage(runner, requestData);
      case 'connect':
        return await this.handleGroupConnect(runner, requestData);
      case 'members':
        return await this.handleGroupMembers(runner, requestData);
      default:
        return { status: 'error', message: `未知的群组请求类型: ${requestType}` };
    }
  }

  /**
   * 处理加入群组请求
   */
  private static async handleGroupJoin(runner: GroupRunner, requestData: Record<string, any>): Promise<any> {
    const reqDid = requestData.req_did;
    const groupAgent: GroupAgent = {
      id: reqDid,
      name: requestData.name || reqDid,
      port: requestData.port || 0,
      metadata: requestData.metadata || {},
      joinedAt: new Date()
    };

    const allowed = await runner.onAgentJoin(groupAgent);
    if (allowed) {
      runner['agents'].set(reqDid, groupAgent);
      return { status: 'success', message: 'Joined group', groupId: runner.groupId };
    } else {
      return { status: 'error', message: 'Join request rejected' };
    }
  }

  /**
   * 处理离开群组请求
   */
  private static async handleGroupLeave(runner: GroupRunner, requestData: Record<string, any>): Promise<any> {
    const reqDid = requestData.req_did;
    if (runner['agents'].has(reqDid)) {
      const groupAgent = runner['agents'].get(reqDid)!;
      await runner.onAgentLeave(groupAgent);
      runner['agents'].delete(reqDid);
      return { status: 'success', message: 'Left group' };
    } else {
      return { status: 'error', message: 'Not a member of this group' };
    }
  }

  /**
   * 处理群组消息
   */
  private static async handleGroupMessage(runner: GroupRunner, requestData: Record<string, any>): Promise<any> {
    const reqDid = requestData.req_did;
    if (!runner.isMember(reqDid)) {
      return { status: 'error', message: 'Not a member of this group' };
    }

    const message: Message = {
      type: 'TEXT',
      content: requestData.content,
      senderId: reqDid,
      groupId: runner.groupId,
      timestamp: Date.now(),
      metadata: requestData.metadata || {}
    };

    const response = await runner.onMessage(message);
    if (response) {
      return { status: 'success', response };
    }
    return { status: 'success' };
  }

  /**
   * 处理群组连接请求（SSE）
   */
  private static async handleGroupConnect(runner: GroupRunner, requestData: Record<string, any>): Promise<any> {
    const reqDid = requestData.req_did;
    if (!runner.isMember(reqDid)) {
      return { status: 'error', message: 'Not a member of this group' };
    }

    // 在实际实现中，这里应该返回一个流式响应
    // 目前返回一个占位符
    return { status: 'success', message: 'Connected to group stream' };
  }

  /**
   * 处理群组成员管理
   */
  private static async handleGroupMembers(runner: GroupRunner, requestData: Record<string, any>): Promise<any> {
    const action = requestData.action || 'list';

    switch (action) {
      case 'list':
        const members = runner.getMembers().map(agent => ({
          id: agent.id,
          name: agent.name,
          port: agent.port,
          metadata: agent.metadata,
          joinedAt: agent.joinedAt.toISOString()
        }));
        return { status: 'success', members };

      case 'add':
        const agentId = requestData.agent_id;
        const groupAgent: GroupAgent = {
          id: agentId,
          name: requestData.name || agentId,
          port: requestData.port || 0,
          metadata: requestData.metadata || {},
          joinedAt: new Date()
        };
        const allowed = await runner.onAgentJoin(groupAgent);
        if (allowed) {
          runner['agents'].set(agentId, groupAgent);
          return { status: 'success', message: 'Member added' };
        }
        return { status: 'error', message: 'Add member rejected' };

      case 'remove':
        const targetAgentId = requestData.agent_id;
        const success = await runner.removeMember(targetAgentId);
        if (success) {
          return { status: 'success', message: 'Member removed' };
        }
        return { status: 'error', message: 'Member not found' };

      default:
        return { status: 'error', message: `Unknown action: ${action}` };
    }
  }
}

/**
 * 全局消息处理管理器
 */
export class GlobalMessageManager {
  // 类级别的消息处理器注册表
  private static handlers: Map<string, Map<string, MessageHandler>> = new Map();
  private static handlerConflicts: Array<Record<string, any>> = [];

  /**
   * 注册消息处理器
   */
  static registerHandler(did: string, msgType: string, handler: Function, agentName: string): boolean {
    // 初始化DID的处理器表
    if (!this.handlers.has(did)) {
      this.handlers.set(did, new Map());
    }

    const didHandlers = this.handlers.get(did)!;

    // 检查消息类型冲突
    if (didHandlers.has(msgType)) {
      const existingHandler = didHandlers.get(msgType)!;
      const conflictInfo = {
        did,
        msgType,
        existingAgent: existingHandler.agentName,
        newAgent: agentName,
        conflictTime: new Date().toISOString(),
        action: 'ignored'
      };
      this.handlerConflicts.push(conflictInfo);

      logger.warn(`⚠️  消息处理器冲突: ${did}:${msgType}`);
      logger.warn(`   现有Agent: ${existingHandler.agentName}`);
      logger.warn(`   新Agent: ${agentName}`);
      logger.warn(`   🔧 使用第一个注册的处理器，忽略后续注册`);
      return false;
    }

    // 注册新处理器
    const messageHandler: MessageHandler = {
      did,
      msgType,
      handler,
      agentName,
      registeredAt: new Date()
    };
    didHandlers.set(msgType, messageHandler);

    logger.debug(`💬 全局消息处理器注册: ${did}:${msgType} <- ${agentName}`);
    return true;
  }

  /**
   * 获取消息处理器
   */
  static getHandler(did: string, msgType: string): Function | null {
    const didHandlers = this.handlers.get(did);
    if (didHandlers && didHandlers.has(msgType)) {
      return didHandlers.get(msgType)!.handler;
    }
    return null;
  }

  /**
   * 列出消息处理器信息
   */
  static listHandlers(did?: string): Array<Record<string, any>> {
    const handlers: Array<Record<string, any>> = [];

    if (did) {
      // 列出特定DID的处理器
      const didHandlers = this.handlers.get(did);
      if (didHandlers) {
        for (const handler of didHandlers.values()) {
          handlers.push({
            did: handler.did,
            msgType: handler.msgType,
            agentName: handler.agentName,
            registeredAt: handler.registeredAt.toISOString(),
            handlerName: handler.handler.name || 'unknown'
          });
        }
      }
    } else {
      // 列出所有处理器
      for (const didHandlers of this.handlers.values()) {
        for (const handler of didHandlers.values()) {
          handlers.push({
            did: handler.did,
            msgType: handler.msgType,
            agentName: handler.agentName,
            registeredAt: handler.registeredAt.toISOString(),
            handlerName: handler.handler.name || 'unknown'
          });
        }
      }
    }

    return handlers;
  }

  /**
   * 获取冲突记录
   */
  static getConflicts(): Array<Record<string, any>> {
    return [...this.handlerConflicts];
  }

  /**
   * 清除消息处理器（主要用于测试）
   */
  static clearHandlers(did?: string): void {
    if (did) {
      if (this.handlers.has(did)) {
        this.handlers.delete(did);
        logger.debug(`清除DID ${did} 的所有消息处理器`);
      }
    } else {
      this.handlers.clear();
      this.handlerConflicts.length = 0;
      logger.debug("清除所有消息处理器");
    }
  }

  /**
   * 获取消息处理器统计信息
   */
  static getStats(): Record<string, any> {
    let totalHandlers = 0;
    const handlersPerDid: Record<string, number> = {};

    for (const [did, didHandlers] of this.handlers) {
      const count = didHandlers.size;
      totalHandlers += count;
      handlersPerDid[did] = count;
    }

    return {
      totalHandlers,
      didCount: this.handlers.size,
      conflictCount: this.handlerConflicts.length,
      handlersPerDid
    };
  }
}
