/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { Agent, AgentOptions } from './agent';
import { ANPUser } from '../../foundation/user';
import { getUserDataManager } from '../../foundation/user';
import { getLogger } from '../../foundation/utils';

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
    
    logger.debug(`🔧 [AgentManager] 创建Agent: ${name}, DID: ${did}, 共享模式: ${shared}`);
    logger.debug(`🔧 [AgentManager] 当前注册的DID列表:`);
    for (const registeredDid of this.didUsageRegistry.keys()) {
      logger.debug(`🔧 [AgentManager]   - ${registeredDid}`);
    }
    
    if (!shared) {
      // 独占模式：检查DID是否已被使用
      if (this.didUsageRegistry.has(did)) {
        const existingAgents = Array.from(this.didUsageRegistry.get(did)!.keys());
        logger.error(`❌ DID独占冲突: ${did} 已被Agent '${existingAgents[0]}' 使用`);
        logger.error(`解决方案:`);
        logger.error(`  1. 使用不同的DID`);
        logger.error(`  2. 设置 shared=true 进入共享模式`);
        
        throw new Error(
          `❌ DID独占冲突: ${did} 已被Agent '${existingAgents[0]}' 使用\n` +
          `解决方案:\n` +
          `  1. 使用不同的DID\n` +
          `  2. 设置 shared=true 进入共享模式`
        );
      }
    } else if (shared) {
      // 共享模式：检查prefix和主Agent
      if (!prefix) {
        logger.error(`❌ 共享模式必须提供 prefix 参数 (Agent: ${name})`);
        throw new Error(`❌ 共享模式必须提供 prefix 参数 (Agent: ${name})`);
      }

      if (this.didUsageRegistry.has(did)) {
        const existingAgents = this.didUsageRegistry.get(did)!;

        // 检查prefix冲突
        for (const [agentName, agentInfo] of existingAgents) {
          if (agentInfo.prefix === prefix) {
            logger.error(`❌ Prefix冲突: ${prefix} 已被Agent '${agentName}' 使用`);
            throw new Error(`❌ Prefix冲突: ${prefix} 已被Agent '${agentName}' 使用`);
          }
        }

        // 检查主Agent冲突
        if (primaryAgent) {
          for (const [agentName, agentInfo] of existingAgents) {
            if (agentInfo.primaryAgent) {
              logger.error(`❌ 主Agent冲突: DID ${did} 的主Agent已被 '${agentName}' 占用`);
              logger.error(`解决方案:`);
              logger.error(`  1. 设置 primaryAgent=false`);
              logger.error(`  2. 修改现有主Agent配置`);
              
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
    logger.debug(`🔍 [AgentManager] 查找Agent: ${did}`);
    logger.debug(`🔍 [AgentManager] 当前注册的DID列表:`);
    for (const registeredDid of this.didUsageRegistry.keys()) {
      logger.debug(`🔍 [AgentManager]   - ${registeredDid}`);
    }
    
    const agentsInfo = this.getAgentInfo(did) as Map<string, AgentInfo> | null;
    if (!agentsInfo || agentsInfo.size === 0) {
      logger.debug(`🔍 [AgentManager] Agent未找到: ${did}`);
      return null;
    }

    // 返回第一个Agent实例
    const firstAgent = agentsInfo.values().next().value;
    logger.debug(`🔍 [AgentManager] Agent找到: ${did}, 名称: ${firstAgent?.agent?.name}`);
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
   * 根据路径前缀查找Agent
   */
  static findAgentByPathPrefix(path: string): Agent | null {
    logger.debug(`🔍 [AgentManager] 根据路径前缀查找Agent: ${path}`);
    
    // 提取路径的最后部分，用于更精确的匹配
    const pathSegments = path.split('/');
    const lastSegments = pathSegments.slice(-2).join('/');
    logger.debug(`🔍 [AgentManager] 路径最后部分: /${lastSegments}`);
    
    // 特殊处理 /assistant/help 路径
    if (path.endsWith('/assistant/help') || path.endsWith('/help')) {
      logger.debug(`🔍 [AgentManager] 检测到特殊路径: ${path}`);
      
      // 查找所有共享DID的Agent
      for (const [did, agentsMap] of this.didUsageRegistry.entries()) {
        for (const [agentName, agentInfo] of agentsMap.entries()) {
          if (agentInfo.shared && agentInfo.prefix === '/assistant') {
            logger.debug(`✅ [AgentManager] 找到匹配的助手Agent: ${agentName}, 前缀: ${agentInfo.prefix}`);
            return agentInfo.agent;
          }
        }
      }
    }
    
    // 常规路径前缀匹配 - 先尝试匹配最长前缀
    const matchedAgents: {agent: Agent, prefixLength: number}[] = [];
    
    for (const [did, agentsMap] of this.didUsageRegistry.entries()) {
      logger.debug(`🔍 [AgentManager] 检查DID: ${did}`);
      
      for (const [agentName, agentInfo] of agentsMap.entries()) {
        if (agentInfo.prefix) {
          // 检查路径是否包含前缀
          if (path.includes(agentInfo.prefix)) {
            logger.debug(`✅ [AgentManager] 找到匹配的Agent: ${agentName}, 前缀: ${agentInfo.prefix}`);
            matchedAgents.push({
              agent: agentInfo.agent,
              prefixLength: agentInfo.prefix.length
            });
          } else {
            logger.debug(`❌ [AgentManager] 前缀不匹配: ${agentName}, 前缀: ${agentInfo.prefix}, 路径: ${path}`);
          }
        }
      }
    }
    
    // 如果找到多个匹配的Agent，返回前缀最长的那个
    if (matchedAgents.length > 0) {
      matchedAgents.sort((a, b) => b.prefixLength - a.prefixLength);
      logger.debug(`✅ [AgentManager] 选择最佳匹配Agent，前缀长度: ${matchedAgents[0].prefixLength}`);
      return matchedAgents[0].agent;
    }
    
    logger.debug(`❌ [AgentManager] 未找到匹配路径前缀的Agent: ${path}`);
    return null;
  }

  /**
   * 获取所有Agent实例（别名方法，用于兼容）
   */
  static getAllAgents(): Agent[] {
    return this.getAllAgentInstances();
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

  /**
   * 为指定的Agent生成并保存接口文档
   * 对标Python版本的generate_and_save_agent_interfaces方法
   */
  static async generateAndSaveAgentInterfaces(agent: Agent): Promise<void> {
    logger.debug(`开始为Agent '${agent.name}' (${agent.anpUser.id}) 生成接口文档...`);

    const did = agent.anpUser.id;
    const userDataManager = getUserDataManager();
    const userData = userDataManager.getUserData(did);
    
    if (!userData) {
      logger.error(`无法找到DID '${did}' 的用户数据，无法保存接口文档`);
      return;
    }

    const userFullPath = userData.userDir;

    try {
      // 1. 生成并保存OpenAPI YAML文件（Node.js版本）
      await this.generateAndSaveOpenApiYaml(did, userFullPath);

      // 2. 生成并保存JSON-RPC文件（Node.js版本）
      await this.generateAndSaveJsonRpc(did, userFullPath);

      // 3. 生成并保存Agent Description文件（Node.js版本）
      await this.generateAndSaveAgentDescription(did, userFullPath);

      logger.debug(`✅ 为DID '${did}' 生成接口文档完成`);
    } catch (error) {
      logger.error(`为DID '${did}' 生成接口文档失败: ${error}`);
      throw error;
    }
  }

  /**
   * 生成并保存OpenAPI YAML文件
   */
  private static async generateAndSaveOpenApiYaml(did: string, userFullPath: string): Promise<void> {
    try {
      const openApiData = this.generateOpenApiByDid(did);
      await this.saveInterfaceFile(
        userFullPath,
        openApiData,
        'api_interface_nj.yaml', // Node.js版本使用_nj后缀
        'YAML'
      );
      logger.debug(`✅ 为DID '${did}' 生成OpenAPI YAML文件成功`);
    } catch (error) {
      logger.error(`为DID '${did}' 生成OpenAPI YAML文件失败: ${error}`);
      throw error;
    }
  }

  /**
   * 生成并保存JSON-RPC文件
   */
  private static async generateAndSaveJsonRpc(did: string, userFullPath: string): Promise<void> {
    try {
      const jsonRpcData = {
        jsonrpc: '2.0',
        info: {
          title: `DID ${did} JSON-RPC Interface`,
          version: '0.1.0',
          description: `Methods offered by DID ${did}`,
          runtime: 'nodejs' // 添加运行时标识
        },
        methods: [] as any[]
      };

      // 获取该DID关联的所有Agent信息
      const agentsInfo = this.getAgentInfo(did) as Map<string, AgentInfo> | null;
      if (!agentsInfo) {
        logger.warn(`无法找到DID '${did}' 关联的Agent，生成空的JSON-RPC文件`);
      } else {
        // 遍历所有Agent，获取它们的API路由
        for (const [agentName, agentInfo] of agentsInfo) {
          const agent = agentInfo.agent;
          const prefix = agentInfo.prefix;

          // 收集所有其他Agent的prefix，用于独占模式判断
          const otherPrefixes = Array.from(agentsInfo.values())
            .filter(info => info !== agentInfo && info.prefix)
            .map(info => info.prefix!);

          // 获取该Agent的API路由
          const apiRoutes = this.getAgentApiRoutes(agent, prefix, otherPrefixes);

          for (const [path, handler] of Object.entries(apiRoutes)) {
            const fullPath = path;
            const methodName = fullPath.replace(/^\//, '').replace(/\//g, '.');

            // 从处理函数获取参数信息
            const params = this.extractHandlerParams(handler);

            // 获取处理函数的文档字符串作为摘要
            const summary = (handler as any).__doc__ || `${agent.name}的${path}接口`;

            // 创建方法对象
            const methodObj = {
              name: methodName,
              summary: summary,
              description: `由 ${agent.name} 提供的服务`,
              params: params,
              tags: [agent.name],
              meta: {
                openapi: '3.0.0',
                info: { title: `${agent.name} API`, version: '1.0.0' },
                httpMethod: 'POST',
                endpoint: fullPath,
                runtime: 'nodejs'
              }
            };

            jsonRpcData.methods.push(methodObj);
            logger.debug(`  - 添加JSON-RPC方法: ${methodName} <- ${fullPath}`);
          }
        }
      }

      await this.saveInterfaceFile(
        userFullPath,
        jsonRpcData,
        'api_interface_nj.json', // Node.js版本使用_nj后缀
        'JSON'
      );
      logger.debug(`✅ 为DID '${did}' 生成JSON-RPC文件成功`);
    } catch (error) {
      logger.error(`为DID '${did}' 生成JSON-RPC文件失败: ${error}`);
      throw error;
    }
  }

  /**
   * 生成并保存Agent Description文件
   */
  private static async generateAndSaveAgentDescription(did: string, userFullPath: string): Promise<void> {
    try {
      const agentsInfo = this.getAgentInfo(did) as Map<string, AgentInfo> | null;
      if (!agentsInfo) {
        logger.error(`无法找到DID '${did}' 关联的Agent，无法生成ad.json`);
        return;
      }

      // 确定主Agent（如果有）
      let primaryAgent = null;
      for (const [agentName, agentInfo] of agentsInfo) {
        if (agentInfo.primaryAgent) {
          primaryAgent = agentInfo.agent;
          break;
        }
      }

      // 如果没有主Agent，使用第一个Agent
      if (!primaryAgent && agentsInfo.size > 0) {
        const firstAgentInfo = agentsInfo.values().next().value;
        if (firstAgentInfo) {
          primaryAgent = firstAgentInfo.agent;
        }
      }

      // 从DID解析主机和端口
      const { host, port } = this.parseDidHostPort(did);
      const hostPort = port ? `${host}:${port}` : host;

      // 基本ad.json结构
      const adJson = {
        '@context': {
          '@vocab': 'https://schema.org/',
          'did': 'https://w3id.org/did#',
          'ad': 'https://agent-network-protocol.com/ad#'
        },
        '@type': 'ad:AgentDescription',
        'name': `DID Services for ${did}`,
        'owner': {
          'name': `${did} 的拥有者`,
          '@id': did
        },
        'description': `Services provided by DID ${did}`,
        'version': '0.1.0',
        'created_at': new Date().toISOString(),
        'runtime': 'nodejs',
        'security_definitions': {
          'didwba_sc': {
            'scheme': 'didwba',
            'in': 'header',
            'name': 'Authorization'
          }
        },
        'ad:interfaces': [] as any[]
      };

      // 添加标准接口
      const interfaces = [];
      const encodedDid = encodeURIComponent(did);

      interfaces.push(
        {
          '@type': 'ad:NaturalLanguageInterface',
          'protocol': 'YAML',
          'url': `http://${hostPort}/wba/user/${encodedDid}/nlp_interface_nj.yaml`,
          'description': 'Node.js运行时的自然语言交互接口OpenAPI YAML文件'
        },
        {
          '@type': 'ad:StructuredInterface',
          'protocol': 'YAML',
          'url': `http://${hostPort}/wba/user/${encodedDid}/api_interface_nj.yaml`,
          'description': 'Node.js运行时的智能体YAML描述接口调用方法'
        },
        {
          '@type': 'ad:StructuredInterface',
          'protocol': 'JSON',
          'url': `http://${hostPort}/wba/user/${encodedDid}/api_interface_nj.json`,
          'description': 'Node.js运行时的智能体JSON-RPC描述接口调用方法'
        }
      );

      // 聚合所有Agent的API路由
      for (const [agentName, agentInfo] of agentsInfo) {
        const agent = agentInfo.agent;
        const prefix = agentInfo.prefix;

        // 收集所有其他Agent的prefix，用于独占模式判断
        const otherPrefixes = Array.from(agentsInfo.values())
          .filter(info => info !== agentInfo && info.prefix)
          .map(info => info.prefix!);

        // 获取该Agent的API路由
        const apiRoutes = this.getAgentApiRoutes(agent, prefix, otherPrefixes);

        for (const [path, handler] of Object.entries(apiRoutes)) {
          const fullPath = path;
          const handlerName = (handler as any).name || 'unknown';
          
          interfaces.push({
            '@type': 'ad:StructuredInterface',
            'protocol': 'HTTP',
            'name': fullPath.replace(/\//g, '_').replace(/^_/, ''),
            'url': `/agent/api/${did}${fullPath}`,
            'description': `${agent.name} API路径 ${fullPath} 的端点 (处理器: ${handlerName})`
          });
        }
      }

      // 去重逻辑
      const seenUrls = new Set<string>();
      const uniqueInterfaces = interfaces.filter(interfaceItem => {
        const url = interfaceItem.url;
        if (seenUrls.has(url)) {
          return false;
        }
        seenUrls.add(url);
        return true;
      });

      adJson['ad:interfaces'] = uniqueInterfaces;

      await this.saveInterfaceFile(
        userFullPath,
        adJson,
        'ad_nj.json', // Node.js版本使用_nj后缀
        'JSON'
      );
      logger.debug(`✅ 为DID '${did}' 生成Agent Description文件成功`);
    } catch (error) {
      logger.error(`为DID '${did}' 生成Agent Description文件失败: ${error}`);
      throw error;
    }
  }

  /**
   * 根据DID生成OpenAPI规范
   */
  private static generateOpenApiByDid(did: string): any {
    const openApi = {
      openapi: '3.0.0',
      info: {
        title: `DID ${did} API`,
        version: '1.0.0',
        description: `所有与DID ${did} 关联的服务接口`,
        'x-runtime': 'nodejs'
      },
      paths: {} as any
    };

    // 获取与该DID关联的所有Agent
    const agentsInfo = this.getAgentInfo(did) as Map<string, AgentInfo> | null;
    if (!agentsInfo) {
      logger.warn(`无法找到DID '${did}' 关联的Agent，生成空的OpenAPI规范`);
      return openApi;
    }

    // 遍历所有Agent，获取它们的API路由
    for (const [agentName, agentInfo] of agentsInfo) {
      const agent = agentInfo.agent;
      const prefix = agentInfo.prefix;

      // 收集所有其他Agent的prefix，用于独占模式判断
      const otherPrefixes = Array.from(agentsInfo.values())
        .filter(info => info !== agentInfo && info.prefix)
        .map(info => info.prefix!);

      // 获取该Agent的API路由
      const apiRoutes = this.getAgentApiRoutes(agent, prefix, otherPrefixes);

      for (const [path, handler] of Object.entries(apiRoutes)) {
        const fullPath = path;

        // 从处理函数获取参数信息
        const params = this.extractHandlerParams(handler);
        const properties: Record<string, any> = {};
        
        for (const [name, info] of Object.entries(params)) {
          properties[name] = { type: 'string' };
        }

        // 获取处理函数的文档字符串作为摘要
        const summary = (handler as any).__doc__ || `${agent.name}的${path}接口`;

        // 添加到OpenAPI规范
        openApi.paths[fullPath] = {
          post: {
            summary: summary,
            description: `由 ${agent.name} 提供的服务`,
            tags: [agent.name],
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: properties
                  }
                }
              }
            },
            responses: {
              '200': {
                description: '返回结果',
                content: {
                  'application/json': {
                    schema: { type: 'object' }
                  }
                }
              }
            }
          }
        };
      }
    }

    return openApi;
  }

  /**
   * 获取Agent的API路由
   */
  private static getAgentApiRoutes(agent: Agent, prefix?: string, otherPrefixes: string[] = []): Record<string, Function> {
    const apiRoutes: Record<string, Function> = {};

    // 从agent.apiRoutes获取路由（如果存在）
    if (agent.apiRoutes) {
      for (const [path, handler] of Object.entries(agent.apiRoutes)) {
        // 检查路径是否属于当前Agent（通过prefix匹配）
        if (prefix && path.startsWith(prefix)) {
          // 这才是属于当前Agent的路由
          apiRoutes[path] = handler;
        } else if (!prefix && !otherPrefixes.some(p => path.startsWith(p))) {
          // 独占模式的路由，且不以其他Agent的prefix开头
          apiRoutes[path] = handler;
        }
      }
    }

    return apiRoutes;
  }

  /**
   * 从处理函数提取参数信息
   */
  private static extractHandlerParams(handler: Function): Record<string, any> {
    const params: Record<string, any> = {};
    
    try {
      // 获取函数字符串
      const funcStr = handler.toString();
      
      // 匹配参数列表
      const match = funcStr.match(/\(([^)]*)\)/);
      if (match && match[1]) {
        const paramStr = match[1];
        const paramList = paramStr.split(',').map(p => p.trim());
        
        for (const param of paramList) {
          if (param && !param.includes('request') && !param.includes('this')) {
            const paramName = param.split(':')[0].trim();
            if (paramName) {
              params[paramName] = { type: 'Any' };
            }
          }
        }
      }
    } catch (error) {
      logger.debug(`提取函数参数失败: ${error}`);
    }

    return params;
  }

  /**
   * 保存接口文件
   */
  private static async saveInterfaceFile(
    userFullPath: string,
    interfaceData: any,
    filename: string,
    fileType: 'JSON' | 'YAML'
  ): Promise<void> {
    const filePath = path.join(userFullPath, filename);
    
    // 确保目录存在
    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });

    let content: string;
    if (fileType === 'JSON') {
      content = JSON.stringify(interfaceData, null, 2);
    } else {
      content = yaml.stringify(interfaceData);
    }

    await fs.promises.writeFile(filePath, content, 'utf-8');
    logger.debug(`接口文件${filename}已保存在: ${filePath}`);
  }

  /**
   * 从DID中解析域名和端口
   */
  private static parseDidHostPort(did: string): { host: string; port: number | null } {
    try {
      // 解析格式: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
      const parts = did.split(':');
      if (parts.length >= 3 && parts[0] === 'did' && parts[1] === 'wba') {
        const hostPart = parts[2];
        
        if (hostPart.includes('%3A')) {
          // 包含端口的情况
          const [encodedHost, portStr] = hostPart.split('%3A');
          const host = decodeURIComponent(encodedHost);
          const port = parseInt(portStr, 10);
          return { host, port: isNaN(port) ? null : port };
        } else {
          // 不包含端口，使用默认端口
          const host = decodeURIComponent(hostPart);
          return { host, port: 80 };
        }
      }
    } catch (error) {
      logger.warn(`解析DID域名端口失败: ${did}, 错误: ${error}`);
    }
    
    return { host: 'localhost', port: 9527 };
  }
}

/**
 * 获取AgentManager实例（兼容性函数）
 * 返回AgentManager类的引用，用于与现有代码兼容
 */
export function getAgentManager(): typeof AgentManager {
  return AgentManager;
}
