/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { DomainManager } from '../../foundation/domain';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('PublisherServiceHandler');

export interface PublisherServiceResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export interface AgentInfo {
  did: string;
  name: string;
  domain: string;
  isHosted: boolean;
}

/**
 * 发布者服务处理器
 * 对应Python版本的publisher_service_handler.py
 */
export class PublisherServiceHandler {
  
  /**
   * 获取已发布的智能体列表
   */
  public static async getPublishedAgents(host: string, port: number): Promise<PublisherServiceResponse> {
    try {
      // 获取域名管理器
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 获取所有智能体实例
      const allAgents = await this.getAllAgentInstances();

      // 处理智能体信息
      const publicAgents: AgentInfo[] = [];
      const seenDids = new Set<string>(); // 用于跟踪已经添加的did

      for (const agent of allAgents) {
        // 尝试获取agent的did
        let did = "unknown";
        if (agent.anpUserId) {
          did = agent.anpUserId;
        } else if (agent.anpUser?.id) {
          did = agent.anpUser.id;
        } else if (agent.id) {
          did = agent.id;
        }

        // 如果did已经添加过，则跳过
        if (seenDids.has(did)) {
          continue;
        }

        // 添加did到集合
        seenDids.add(did);

        const agentInfo: AgentInfo = {
          did,
          name: agent.name || "unknown",
          domain: `${host}:${port}`,
          isHosted: agent.isHostedDid || false
        };
        publicAgents.push(agentInfo);
      }

      // 添加域名统计信息
      const domainStats = domainManager.getDomainStats();

      // 构建结果
      const result = {
        agents: publicAgents,
        count: publicAgents.length,
        domain: `${host}:${port}`,
        domainStats,
        supportedDomains: Object.keys(domainManager.supportedDomains)
      };

      return { success: true, data: result };

    } catch (error) {
      logger.error(`获取智能体列表失败: ${error}`);
      return { success: false, error: `获取智能体列表失败: ${error}` };
    }
  }

  /**
   * 获取所有智能体实例
   * 这里需要与runtime层集成，暂时返回模拟数据
   */
  private static async getAllAgentInstances(): Promise<any[]> {
    try {
      // TODO: 与AgentManager集成
      // const { AgentManager } = await import('@runtime/agent-manager');
      // return AgentManager.getAllAgentInstances();
      
      // 暂时返回模拟数据
      return [
        {
          id: 'did:wba:localhost%3A9527:wba:user:example1',
          anpUserId: 'did:wba:localhost%3A9527:wba:user:example1',
          name: 'Example Agent 1',
          isHostedDid: false
        },
        {
          id: 'did:wba:localhost%3A9527:wba:user:example2',
          anpUserId: 'did:wba:localhost%3A9527:wba:user:example2',
          name: 'Example Agent 2',
          isHostedDid: true
        }
      ];
    } catch (error) {
      logger.warn(`获取智能体实例失败，返回空列表: ${error}`);
      return [];
    }
  }

  /**
   * 获取智能体统计信息
   */
  public static async getAgentStatistics(host: string, port: number): Promise<PublisherServiceResponse> {
    try {
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      const allAgents = await this.getAllAgentInstances();
      
      const stats = {
        totalAgents: allAgents.length,
        hostedAgents: allAgents.filter(agent => agent.isHostedDid).length,
        regularAgents: allAgents.filter(agent => !agent.isHostedDid).length,
        domain: `${host}:${port}`,
        lastUpdated: new Date().toISOString()
      };

      return { success: true, data: stats };

    } catch (error) {
      logger.error(`获取智能体统计信息失败: ${error}`);
      return { success: false, error: `获取智能体统计信息失败: ${error}` };
    }
  }

  /**
   * 检查智能体是否可用
   */
  public static async checkAgentAvailability(did: string, host: string, port: number): Promise<PublisherServiceResponse> {
    try {
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      const allAgents = await this.getAllAgentInstances();
      const agent = allAgents.find(a => 
        a.id === did || a.anpUserId === did || a.anpUser?.id === did
      );

      if (!agent) {
        return { 
          success: true, 
          data: { 
            available: false, 
            did, 
            reason: 'Agent not found' 
          } 
        };
      }

      return { 
        success: true, 
        data: { 
          available: true, 
          did, 
          name: agent.name,
          isHosted: agent.isHostedDid || false
        } 
      };

    } catch (error) {
      logger.error(`检查智能体可用性失败: ${error}`);
      return { success: false, error: `检查智能体可用性失败: ${error}` };
    }
  }
}