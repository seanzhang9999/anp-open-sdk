/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import axios from 'axios';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('AgentServiceHandler');

export interface GroupRequest {
  did: string;
  groupId: string;
  action: string;
  requestData: Record<string, any>;
  queryParams?: Record<string, string>;
}

export interface GroupResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export class AgentServiceHandler {
  /**
   * 处理群组相关请求的核心逻辑
   */
  public static async processGroupRequest(request: GroupRequest): Promise<GroupResponse> {
    const { did, groupId, action, requestData } = request;
    
    try {
      logger.debug(`🔄 处理群组${action}请求: ${did}/${groupId}`);

      switch (action) {
        case 'join':
          return await this.handleGroupJoin(did, groupId, requestData);
        case 'leave':
          return await this.handleGroupLeave(did, groupId, requestData);
        case 'message':
          return await this.handleGroupMessage(did, groupId, requestData);
        case 'connect':
          return await this.handleGroupConnect(did, groupId, requestData);
        case 'members':
          return await this.handleGroupMembers(did, groupId, requestData);
        default:
          return {
            success: false,
            error: `Unsupported group action: ${action}`
          };
      }
    } catch (error) {
      logger.error(`群组${action}请求处理失败:`, error);
      return {
        success: false,
        error: `Group ${action} request failed: ${error}`
      };
    }
  }

  private static async handleGroupJoin(did: string, groupId: string, data: Record<string, any>): Promise<GroupResponse> {
    // 实现群组加入逻辑
    logger.info(`处理群组加入请求: ${did} -> ${groupId}`);
    return {
      success: true,
      data: { action: 'joined', groupId, did }
    };
  }

  private static async handleGroupLeave(did: string, groupId: string, data: Record<string, any>): Promise<GroupResponse> {
    // 实现群组离开逻辑
    logger.info(`处理群组离开请求: ${did} -> ${groupId}`);
    return {
      success: true,
      data: { action: 'left', groupId, did }
    };
  }

  private static async handleGroupMessage(did: string, groupId: string, data: Record<string, any>): Promise<GroupResponse> {
    // 实现群组消息逻辑
    logger.info(`处理群组消息请求: ${did} -> ${groupId}`);
    return {
      success: true,
      data: { action: 'message_sent', groupId, did, messageId: Date.now() }
    };
  }

  private static async handleGroupConnect(did: string, groupId: string, data: Record<string, any>): Promise<GroupResponse> {
    // 实现群组连接逻辑
    logger.info(`处理群组连接请求: ${did} -> ${groupId}`);
    return {
      success: true,
      data: { action: 'connected', groupId, did }
    };
  }

  private static async handleGroupMembers(did: string, groupId: string, data: Record<string, any>): Promise<GroupResponse> {
    // 实现群组成员查询逻辑
    logger.info(`处理群组成员查询: ${did} -> ${groupId}`);
    return {
      success: true,
      data: { 
        action: 'members_list', 
        groupId, 
        members: [did] // 简化返回
      }
    };
  }

  /**
   * 处理单个Agent请求
   */
  public static async processAgentRequest(
    targetDid: string,
    endpoint: string,
    payload: Record<string, any>
  ): Promise<GroupResponse> {
    try {
      logger.debug(`🔄 处理Agent请求: ${targetDid}${endpoint}`);
      logger.debug(`📦 请求payload:`, JSON.stringify(payload, null, 2));
      
      // 导入AgentManager来获取Agent
      const { getAgentManager } = await import('../../runtime/core');
      const agentManager = getAgentManager();
      
      // 根据DID查找目标Agent
      const targetAgent = agentManager.getAgentByDid(targetDid);
      if (!targetAgent) {
        logger.error(`❌ 未找到目标Agent: ${targetDid}`);
        return {
          success: false,
          error: `Target agent not found: ${targetDid}`
        };
      }
      
      logger.debug(`✅ 找到目标Agent: ${targetAgent.name}`);
      
      // 查找API路由处理器
      const apiHandler = targetAgent.apiRoutes.get(endpoint);
      if (!apiHandler) {
        logger.error(`❌ 未找到API路由: ${endpoint}`);
        logger.debug(`可用的API路由:`, Array.from(targetAgent.apiRoutes.keys()));
        return {
          success: false,
          error: `API endpoint not found: ${endpoint}`
        };
      }
      
      logger.debug(`✅ 找到API处理器: ${apiHandler.name}`);
      
      // 调用API处理器
      // 注意：这里的payload就是完整的请求数据，包含params等信息
      const result = await apiHandler.call(targetAgent, payload, {
        endpoint,
        targetDid,
        timestamp: new Date().toISOString()
      });
      
      logger.debug(`✅ API调用成功，结果:`, JSON.stringify(result, null, 2));
      
      return {
        success: true,
        data: result
      };
    } catch (error) {
      logger.error('Agent请求处理失败:', error);
      return {
        success: false,
        error: `Agent request failed: ${error}`
      };
    }
  }

  /**
   * 转发请求到transformer server
   */
  public static async forwardToTransformerServer(
    serverUrl: string,
    path: string,
    method: string = 'POST',
    data?: any,
    params?: Record<string, string>
  ): Promise<GroupResponse> {
    try {
      logger.debug(`🔄 转发请求到transformer_server: ${serverUrl}${path}`);
      
      const response = await axios({
        method,
        url: `${serverUrl}${path}`,
        data,
        params
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      logger.error('转发到transformer_server失败:', error);
      return {
        success: false,
        error: `Transformer server request failed: ${error}`
      };
    }
  }
}