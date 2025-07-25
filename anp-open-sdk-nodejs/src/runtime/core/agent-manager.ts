/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs';
import * as path from 'path';
import { Agent, AgentOptions } from './agent';
import { ANPUser } from '@foundation/user';
import { getLogger } from '@foundation/utils';

const logger = getLogger('AgentManager');

export interface AgentInfo {
  agent: Agent;
  shared: boolean;
  prefix?: string;
  primaryAgent: boolean;
  createdAt: string;
}

export interface AgentSearchRecord {
  timestamp: string;
  searcherDid: string;
  query: string;
  results: string[];
  resultCount: number;
}

export interface AgentContactInfo {
  did: string;
  name?: string;
  description?: string;
  tags?: string[];
  firstContact: string;
  lastContact: string;
  interactionCount: number;
}

export interface SessionRecord {
  sessionId: string;
  reqDid: string;
  respDid: string;
  startTime: string;
  endTime?: string;
  messages: any[];
  status: 'active' | 'closed';
}

export interface ApiCallRecord {
  timestamp: string;
  callerDid: string;
  targetDid: string;
  apiPath: string;
  method: string;
  params: any;
  responseStatus?: string;
  durationMs: number;
  success: boolean;
}

/**
 * Agent联系人通讯录
 */
export class AgentContactBook {
  private contacts: Map<string, AgentContactInfo> = new Map();

  constructor(private ownerDid: string) {}

  addContact(did: string, name?: string, description: string = '', tags: string[] = []): void {
    if (!this.contacts.has(did)) {
      this.contacts.set(did, {
        did,
        name: name || did.split(':').pop() || did,
        description,
        tags,
        firstContact: new Date().toISOString(),
        lastContact: new Date().toISOString(),
        interactionCount: 1
      });
    } else {
      this.updateInteraction(did);
    }
  }

  updateInteraction(did: string): void {
    const contact = this.contacts.get(did);
    if (contact) {
      contact.lastContact = new Date().toISOString();
      contact.interactionCount += 1;
    }
  }

  getContacts(tag?: string): AgentContactInfo[] {
    const allContacts = Array.from(this.contacts.values());
    if (tag) {
      return allContacts.filter(contact => contact.tags?.includes(tag));
    }
    return allContacts;
  }
}

/**
 * 会话记录管理器
 */
export class SessionRecordManager {
  private sessions: Map<string, SessionRecord> = new Map();

  createSession(reqDid: string, respDid: string): string {
    const sessionId = `${reqDid}_${respDid}_${Date.now()}`;
    this.sessions.set(sessionId, {
      sessionId,
      reqDid,
      respDid,
      startTime: new Date().toISOString(),
      messages: [],
      status: 'active'
    });
    return sessionId;
  }

  addMessage(sessionId: string, message: any): void {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.messages.push({
        timestamp: new Date().toISOString(),
        content: message,
        direction: message.sender === session.reqDid ? 'outgoing' : 'incoming'
      });
    }
  }

  closeSession(sessionId: string): void {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.endTime = new Date().toISOString();
      session.status = 'closed';
    }
  }

  getActiveSessions(): SessionRecord[] {
    return Array.from(this.sessions.values()).filter(s => s.status === 'active');
  }
}

/**
 * API调用记录管理器
 */
export class ApiCallRecordManager {
  private apiCalls: ApiCallRecord[] = [];

  recordApiCall(
    callerDid: string,
    targetDid: string,
    apiPath: string,
    method: string,
    params: any,
    response: any,
    durationMs: number
  ): void {
    this.apiCalls.push({
      timestamp: new Date().toISOString(),
      callerDid,
      targetDid,
      apiPath,
      method,
      params,
      responseStatus: response?.status,
      durationMs,
      success: response?.status === 'success'
    });
  }

  getRecentCalls(limit: number = 20): ApiCallRecord[] {
    return this.apiCalls.slice(-limit);
  }
}

/**
 * 统一的Agent管理器 - 负责Agent创建、注册和冲突管理
 */
export class AgentManager {
  // 类级别的DID使用注册表
  private static didUsageRegistry: Map<string, Map<string, AgentInfo>> = new Map();
  
  // 统计和记录管理器
  private static searchRecords: AgentSearchRecord[] = [];
  private static contactBooks: Map<string, AgentContactBook> = new Map();
  private static sessionManager = new SessionRecordManager();
  private static apiCallManager = new ApiCallRecordManager();

  /**
   * 统一的Agent创建接口
   */
  static createAgent(anpUser: ANPUser, options: AgentOptions): Agent {
    const did = anpUser.id;
    const { name, shared = false, prefix, primaryAgent = false } = options;

    if (!shared) {
      // 独占模式：检查DID是否已被使用
      if (this.didUsageRegistry.has(did)) {
        const existingAgents = Array.from(this.didUsageRegistry.get(did)!.keys());
        throw new Error(
          `❌ DID独占冲突: ${did} 已被Agent '${existingAgents[0]}' 使用\n` +
          `解决方案:\n` +
          `  1. 使用不同的DID\n` +
          `  2. 设置 shared=true 进入共享模式`
        );
      }
    } else {
      // 共享模式：检查prefix和主Agent
      if (!prefix) {
        throw new Error(`❌ 共享模式必须提供 prefix 参数 (Agent: ${name})`);
      }

      if (this.didUsageRegistry.has(did)) {
        const existingAgents = this.didUsageRegistry.get(did)!;

        // 检查prefix冲突
        for (const [agentName, agentInfo] of existingAgents) {
          if (agentInfo.prefix === prefix) {
            throw new Error(`❌ Prefix冲突: ${prefix} 已被Agent '${agentName}' 使用`);
          }
        }

        // 检查主Agent冲突
        if (primaryAgent) {
          for (const [agentName, agentInfo] of existingAgents) {
            if (agentInfo.primaryAgent) {
              throw new Error(
                `❌ 主Agent冲突: DID ${did} 的主Agent已被 '${agentName}' 占用\n` +
                `解决方案:\n` +
                `  1. 设置 primaryAgent=false\n` +
                `  2. 修改现有主Agent配置`
              );
            }
          }
        }
      }
    }

    // 创建Agent
    const agent = new Agent(anpUser, options);

    // 注册使用记录
    if (!this.didUsageRegistry.has(did)) {
      this.didUsageRegistry.set(did, new Map());
    }

    this.didUsageRegistry.get(did)!.set(name, {
      agent,
      shared,
      prefix,
      primaryAgent,
      createdAt: new Date().toISOString()
    });

    logger.debug(`✅ Agent创建成功: ${name}`);
    logger.debug(`   DID: ${did} (${shared ? '共享' : '独占'})`);
    if (prefix) {
      logger.debug(`   Prefix: ${prefix}`);
    }
    if (primaryAgent) {
      logger.debug(`   主Agent: 是`);
    }

    return agent;
  }

  /**
   * 获取Agent信息
   */
  static getAgentInfo(did: string, agentName?: string): AgentInfo | Map<string, AgentInfo> | null {
    if (!this.didUsageRegistry.has(did)) {
      return null;
    }

    const agents = this.didUsageRegistry.get(did)!;
    if (agentName) {
      return agents.get(agentName) || null;
    } else {
      return agents;
    }
  }

  /**
   * 获取Agent实例
   */
  static getAgent(did: string, agentName: string): Agent | null {
    const info = this.getAgentInfo(did, agentName) as AgentInfo | null;
    return info?.agent || null;
  }

  /**
   * 根据DID获取Agent实例（如果有多个，返回第一个）
   */
  static getAgentByDid(did: string): Agent | null {
    const agentsInfo = this.getAgentInfo(did) as Map<string, AgentInfo> | null;
    if (!agentsInfo || agentsInfo.size === 0) {
      return null;
    }

    // 返回第一个Agent实例
    const firstAgent = agentsInfo.values().next().value;
    return firstAgent?.agent || null;
  }

  /**
   * 获取所有Agent实例
   */
  static getAllAgentInstances(): Agent[] {
    const agents: Agent[] = [];
    for (const agentsMap of this.didUsageRegistry.values()) {
      for (const agentInfo of agentsMap.values()) {
        agents.push(agentInfo.agent);
      }
    }
    return agents;
  }

  /**
   * 列出所有Agent信息
   */
  static listAgents(): Record<string, Record<string, Omit<AgentInfo, 'agent'>>> {
    const result: Record<string, Record<string, Omit<AgentInfo, 'agent'>>> = {};
    
    for (const [did, agents] of this.didUsageRegistry) {
      result[did] = {};
      for (const [agentName, agentInfo] of agents) {
        // 不包含agent实例，避免序列化问题
        result[did][agentName] = {
          shared: agentInfo.shared,
          prefix: agentInfo.prefix,
          primaryAgent: agentInfo.primaryAgent,
          createdAt: agentInfo.createdAt
        };
      }
    }
    return result;
  }

  /**
   * 移除Agent
   */
  static removeAgent(did: string, agentName: string): boolean {
    if (this.didUsageRegistry.has(did)) {
      const agents = this.didUsageRegistry.get(did)!;
      if (agents.has(agentName)) {
        agents.delete(agentName);

        // 如果该DID下没有Agent了，删除DID记录
        if (agents.size === 0) {
          this.didUsageRegistry.delete(did);
        }

        logger.debug(`🗑️  Agent已移除: ${agentName} (DID: ${did})`);
        return true;
      }
    }
    return false;
  }

  /**
   * 清除所有Agent（主要用于测试）
   */
  static clearAllAgents(): void {
    this.didUsageRegistry.clear();
    logger.debug("清除所有Agent注册记录");
  }

  /**
   * 记录搜索行为
   */
  static recordSearch(searcherDid: string, query: string, results: string[]): void {
    this.searchRecords.push({
      timestamp: new Date().toISOString(),
      searcherDid,
      query,
      results,
      resultCount: results.length
    });
  }

  /**
   * 获取最近的搜索记录
   */
  static getRecentSearches(limit: number = 10): AgentSearchRecord[] {
    return this.searchRecords.slice(-limit);
  }

  /**
   * 获取或创建联系人通讯录
   */
  static getContactBook(ownerDid: string): AgentContactBook {
    if (!this.contactBooks.has(ownerDid)) {
      this.contactBooks.set(ownerDid, new AgentContactBook(ownerDid));
    }
    return this.contactBooks.get(ownerDid)!;
  }

  /**
   * 获取会话管理器
   */
  static getSessionManager(): SessionRecordManager {
    return this.sessionManager;
  }

  /**
   * 获取API调用记录管理器
   */
  static getApiCallManager(): ApiCallRecordManager {
    return this.apiCallManager;
  }

  /**
   * 注册Agent到管理器（为了向后兼容）
   */
  static registerAgent(agent: Agent): void {
    // Agent已经在创建时自动注册，这里只是为了兼容性
    logger.debug(`Agent已注册: ${agent.name} (DID: ${agent.anpUser.id})`);
  }

  /**
   * 生成Agent统计信息
   */
  static getStats(): Record<string, any> {
    const totalAgents = this.getAllAgentInstances().length;
    const didCount = this.didUsageRegistry.size;
    const sharedDidCount = Array.from(this.didUsageRegistry.values())
      .filter(agents => agents.size > 1).length;

    return {
      totalAgents,
      didCount,
      sharedDidCount,
      searchRecords: this.searchRecords.length,
      contactBooks: this.contactBooks.size,
      activeSessions: this.sessionManager.getActiveSessions().length,
      recentApiCalls: this.apiCallManager.getRecentCalls().length
    };
  }
}