/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import axios from 'axios';
import { DidTool } from '@foundation/did';
import { AuthInitiator } from '@foundation/auth';
import { getLogger } from '@foundation/utils';

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

  constructor(privateKey: string, callerDid: string) {
    this.authInitiator = new AuthInitiator(privateKey, callerDid);
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
      const url = `http://${host}:${port}${endpoint}`;

      logger.debug(`🔗 调用Agent API: ${method} ${url}`);

      // 创建认证header
      const authHeaders = await this.authInitiator.addAuthHeader(
        targetDid,
        url,
        method,
        options.headers || {},
        payload
      );

      // 发送请求
      const response = await axios({
        method,
        url,
        data: payload,
        headers: authHeaders,
        timeout: options.timeout || 30000
      });

      return {
        success: true,
        data: response.data,
        statusCode: response.status,
        headers: response.headers as Record<string, string>
      };

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
      sender: this.authInitiator['did'] // 访问私有属性
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