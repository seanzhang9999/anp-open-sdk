/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import axios from 'axios';
import { DidTool } from '../../foundation/did';
import { AuthInitiator } from '../../foundation/auth';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('AgentApiCaller');

export interface ApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

export interface ApiCallResult {
  success: boolean;
  data?: any;
  error?: string;
  statusCode?: number;
  headers?: Record<string, string>;
}

export class AgentApiCaller {
  private authInitiator: AuthInitiator;
  private callerDid: string;

  constructor(privateKey: string, callerDid: string) {
    this.authInitiator = new AuthInitiator();
    this.callerDid = callerDid;
  }

  /**
   * 调用其他Agent的API
   */
  public async callAgentApi(
    targetDid: string,
    endpoint: string,
    payload?: any,
    options: ApiCallOptions = {}
  ): Promise<ApiCallResult> {
    try {
      // 解析目标DID获取host和port
      const didComponents = DidTool.parseWbaDidHostPort(targetDid);
      if (!didComponents) {
        return {
          success: false,
          error: `Invalid DID format: ${targetDid}`
        };
      }

      const { host, port } = didComponents;
      const method = options.method || 'POST';
      
      // 按照Python版本的格式构建URL: /agent/api/{target_agent_path}{api_path}?{url_params}
      // 注意：不要对已经包含 %3A 的DID进行二次编码，这会导致服务器端解码问题
      let targetAgentPath = targetDid;
      if (!targetDid.includes('%3A')) {
        // 只有当DID不包含 %3A 时才进行编码
        targetAgentPath = encodeURIComponent(targetDid);
      }
      
      const urlParams = new URLSearchParams({
        req_did: this.callerDid,
        resp_did: targetDid
      });
      const url = `http://${host}:${port}/agent/api/${targetAgentPath}${endpoint}?${urlParams.toString()}`;

      logger.debug(`🔗 调用Agent API: ${method} ${url}`);
      logger.debug(`📍 URL构建详情: host=${host}, port=${port}, targetAgentPath=${targetAgentPath}, endpoint=${endpoint}`);
      logger.debug(`🔍 原始DID: ${targetDid}, 处理后的DID路径: ${targetAgentPath}`);
      logger.debug(`📋 请求payload: ${JSON.stringify(payload, null, 2)}`);

      // 使用AuthInitiator发送认证请求
      const result = await this.authInitiator.sendAuthenticatedRequest(
        this.callerDid,
        targetDid,
        url,
        method,
        payload,
        options.headers
      );

      if (result.is_auth_pass) {
        return {
          success: true,
          data: result.response ? JSON.parse(result.response) : {},
          statusCode: result.status,
          headers: {}
        };
      } else {
        return {
          success: false,
          error: result.info || 'Authentication failed',
          statusCode: result.status
        };
      }

    } catch (error: any) {
      logger.error('Agent API调用失败:', error);
      
      return {
        success: false,
        error: error.message || 'API call failed',
        statusCode: error.response?.status
      };
    }
  }

  /**
   * 发送消息给其他Agent
   */
  public async sendMessage(
    targetDid: string,
    messageType: string,
    payload: any,
    options: ApiCallOptions = {}
  ): Promise<ApiCallResult> {
    const messagePayload = {
      type: messageType,
      payload,
      timestamp: new Date().toISOString(),
      sender: this.callerDid
    };

    return await this.callAgentApi(
      targetDid,
      '/msg/receive',
      messagePayload,
      options
    );
  }

  /**
   * 批量调用多个Agent的相同API
   */
  public async callMultipleAgents(
    targetDids: string[],
    endpoint: string,
    payload?: any,
    options: ApiCallOptions = {}
  ): Promise<Record<string, ApiCallResult>> {
    const results: Record<string, ApiCallResult> = {};
    
    // 并发调用
    const promises = targetDids.map(async (did) => {
      const result = await this.callAgentApi(did, endpoint, payload, options);
      return { did, result };
    });

    const responses = await Promise.allSettled(promises);
    
    for (const response of responses) {
      if (response.status === 'fulfilled') {
        results[response.value.did] = response.value.result;
      } else {
        // 处理rejected的情况
        const did = 'unknown';
        results[did] = {
          success: false,
          error: response.reason?.message || 'Request failed'
        };
      }
    }

    return results;
  }

  /**
   * 获取Agent的能力描述（API列表等）
   */
  public async getAgentCapabilities(targetDid: string): Promise<ApiCallResult> {
    return await this.callAgentApi(targetDid, '/capabilities', undefined, {
      method: 'GET'
    });
  }

  /**
   * 健康检查
   */
  public async healthCheck(targetDid: string): Promise<ApiCallResult> {
    return await this.callAgentApi(targetDid, '/health', undefined, {
      method: 'GET',
      timeout: 5000
    });
  }

  /**
   * 重试机制的API调用
   */
  public async callWithRetry(
    targetDid: string,
    endpoint: string,
    payload?: any,
    options: ApiCallOptions = {}
  ): Promise<ApiCallResult> {
    const retries = options.retries || 3;
    let lastError: string = '';

    for (let i = 0; i < retries; i++) {
      const result = await this.callAgentApi(targetDid, endpoint, payload, options);
      
      if (result.success) {
        return result;
      }
      
      lastError = result.error || 'Unknown error';
      logger.warn(`API调用失败 (第${i + 1}次尝试): ${lastError}`);
      
      // 最后一次尝试失败后不再等待
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // 递增延迟
      }
    }

    return {
      success: false,
      error: `All ${retries} retry attempts failed. Last error: ${lastError}`
    };
  }
}
