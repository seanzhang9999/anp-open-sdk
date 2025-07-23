/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Agent, AgentConfig } from './agent';
import { ANPUser } from '@foundation/user';
import { getLogger } from '@foundation/utils';

const logger = getLogger('AgentManager');

export class AgentManager {
  private static instance: AgentManager;
  private agents: Map<string, Agent> = new Map();
  private agentsByName: Map<string, Agent> = new Map();

  private constructor() {}

  public static getInstance(): AgentManager {
    if (!AgentManager.instance) {
      AgentManager.instance = new AgentManager();
    }
    return AgentManager.instance;
  }

  /**
   * 注册Agent
   */
  public registerAgent(agent: Agent): void {
    const did = agent.anpUser.id;
    const name = agent.name;

    // 检查DID是否已注册
    if (this.agents.has(did)) {
      logger.warn(`DID ${did} 已有注册的Agent，将被替换`);
    }

    // 检查名称是否已注册
    if (this.agentsByName.has(name)) {
      logger.warn(`名称 ${name} 已有注册的Agent，将被替换`);
    }

    this.agents.set(did, agent);
    this.agentsByName.set(name, agent);

    logger.info(`✅ Agent注册成功: ${name} (DID: ${did})`);
  }

  /**
   * 根据DID获取Agent
   */
  public getAgentByDid(did: string): Agent | undefined {
    return this.agents.get(did);
  }

  /**
   * 根据名称获取Agent
   */
  public getAgentByName(name: string): Agent | undefined {
    return this.agentsByName.get(name);
  }

  /**
   * 获取所有Agent
   */
  public getAllAgents(): Agent[] {
    return Array.from(this.agents.values());
  }

  /**
   * 获取所有Agent的基本信息
   */
  public getAllAgentInfo(): Array<{ name: string; did: string; shared: boolean }> {
    return this.getAllAgents().map(agent => ({
      name: agent.name,
      did: agent.anpUser.id,
      shared: agent.shared
    }));
  }

  /**
   * 移除Agent
   */
  public removeAgent(did: string): boolean {
    const agent = this.agents.get(did);
    if (!agent) {
      return false;
    }

    this.agents.delete(did);
    this.agentsByName.delete(agent.name);

    logger.info(`🗑️ Agent移除成功: ${agent.name} (DID: ${did})`);
    return true;
  }

  /**
   * 根据路径前缀查找Agent
   */
  public findAgentByPathPrefix(path: string): Agent | undefined {
    for (const agent of this.agents.values()) {
      if (agent.prefix && path.startsWith(agent.prefix)) {
        return agent;
      }
    }
    return undefined;
  }

  /**
   * 获取主要Agent（primaryAgent为true的Agent）
   */
  public getPrimaryAgent(): Agent | undefined {
    for (const agent of this.agents.values()) {
      if (agent.primaryAgent) {
        return agent;
      }
    }
    return undefined;
  }

  /**
   * 获取共享Agent列表
   */
  public getSharedAgents(): Agent[] {
    return this.getAllAgents().filter(agent => agent.shared);
  }

  /**
   * 检查Agent是否存在
   */
  public hasAgent(did: string): boolean {
    return this.agents.has(did);
  }

  /**
   * 检查Agent名称是否存在
   */
  public hasAgentName(name: string): boolean {
    return this.agentsByName.has(name);
  }

  /**
   * 清空所有Agent
   */
  public clear(): void {
    const count = this.agents.size;
    this.agents.clear();
    this.agentsByName.clear();
    logger.info(`🧹 已清空 ${count} 个Agent`);
  }

  /**
   * 获取Agent统计信息
   */
  public getStats(): {
    total: number;
    shared: number;
    primary: number;
    withPrefix: number;
  } {
    const agents = this.getAllAgents();
    return {
      total: agents.length,
      shared: agents.filter(a => a.shared).length,
      primary: agents.filter(a => a.primaryAgent).length,
      withPrefix: agents.filter(a => a.prefix).length
    };
  }

  /**
   * 创建并注册Agent的便捷方法
   */
  public createAndRegisterAgent(config: AgentConfig): Agent {
    const agent = new Agent(config);
    this.registerAgent(agent);
    return agent;
  }

  /**
   * 批量注册Agent
   */
  public registerAgents(agents: Agent[]): void {
    for (const agent of agents) {
      this.registerAgent(agent);
    }
  }

  /**
   * 根据DID列表获取Agent列表
   */
  public getAgentsByDids(dids: string[]): Agent[] {
    const agents: Agent[] = [];
    for (const did of dids) {
      const agent = this.getAgentByDid(did);
      if (agent) {
        agents.push(agent);
      }
    }
    return agents;
  }

  /**
   * 导出所有Agent的配置信息
   */
  public exportAgentConfigs(): Record<string, any> {
    const configs: Record<string, any> = {};
    
    for (const [did, agent] of this.agents) {
      configs[did] = agent.toDict();
    }
    
    return configs;
  }
}

// 导出单例实例的便捷访问函数
export function getAgentManager(): AgentManager {
  return AgentManager.getInstance();
}