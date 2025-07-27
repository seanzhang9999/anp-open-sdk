/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { DidTool } from '../../foundation/did';
import { AuthInitiator } from '../../foundation/auth';
import { ANPUser } from '../../foundation/user';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('AgentMessageCaller');

export interface MessageCallOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

export interface MessageCallResult {
  success: boolean;
  data?: any;
  error?: string;
  statusCode?: number;
  headers?: Record<string, string>;
}

/**
 * Agent消息发送服务
 * 对应Python版本的agent_message_p2p.py
 */
export class AgentMessageCaller {
  private authInitiator: AuthInitiator;
  private callerDid: string;

  constructor(privateKey: string, callerDid: string) {
    this.authInitiator = new AuthInitiator();
    this.callerDid = callerDid;
  }

  /**
   * 发送消息给目标Agent
   * 对应Python版本的agent_msg_post函数
   */
  public async sendMessage(
    targetDid: string,
    content: string,
    messageType: string = 'text',
    options: MessageCallOptions = {}
  ): Promise<MessageCallResult> {
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

      // 构建URL参数
      const urlParams = new URLSearchParams({
        req_did: this.callerDid,
        resp_did: targetDid
      });

      // URL编码目标Agent路径
      const targetAgentPath = encodeURIComponent(targetDid);

      // 构建消息数据
      const messageData = {
        req_did: this.callerDid,
        message_type: messageType,
        content: content
      };

      // 使用统一路由：/agent/api/{did}/message/post（与Python版本一致）
      const url = `http://${host}:${port}/agent/api/${targetAgentPath}/message/post?${urlParams.toString()}`;

      logger.debug(`📨 发送消息到Agent: ${url}`);
      logger.debug(`📨 消息内容: ${content}`);

      // 使用AuthInitiator发送认证请求
      const result = await this.authInitiator.sendAuthenticatedRequest(
        this.callerDid,
        targetDid,
        url,
        'POST',
        messageData,
        options.headers
      );

      if (result.is_auth_pass) {
        // 解析响应数据
        let responseData = {};
        if (result.response) {
          try {
            responseData = JSON.parse(result.response);
          } catch (error) {
            logger.warn('响应数据解析失败，使用原始响应');
            responseData = { raw_response: result.response };
          }
        }

        return {
          success: true,
          data: responseData,
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
      logger.error('Agent消息发送失败:', error);
      
      return {
        success: false,
        error: error.message || 'Message sending failed',
        statusCode: error.response?.status
      };
    }
  }

  /**
   * 批量发送消息给多个Agent
   */
  public async sendMessageToMultiple(
    targetDids: string[],
    content: string,
    messageType: string = 'text',
    options: MessageCallOptions = {}
  ): Promise<Record<string, MessageCallResult>> {
    const results: Record<string, MessageCallResult> = {};
    
    // 并发发送
    const promises = targetDids.map(async (did) => {
      const result = await this.sendMessage(did, content, messageType, options);
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
          error: response.reason?.message || 'Message sending failed'
        };
      }
    }

    return results;
  }

  /**
   * 发送群组消息
   */
  public async sendGroupMessage(
    groupId: string,
    targetDids: string[],
    content: string,
    messageType: string = 'group_message',
    options: MessageCallOptions = {}
  ): Promise<Record<string, MessageCallResult>> {
    const groupContent = {
      group_id: groupId,
      content: content,
      sender: this.callerDid,
      timestamp: new Date().toISOString()
    };

    return await this.sendMessageToMultiple(
      targetDids,
      JSON.stringify(groupContent),
      messageType,
      options
    );
  }

  /**
   * 重试机制的消息发送
   */
  public async sendMessageWithRetry(
    targetDid: string,
    content: string,
    messageType: string = 'text',
    options: MessageCallOptions = {}
  ): Promise<MessageCallResult> {
    const retries = options.retries || 3;
    let lastError: string = '';

    for (let i = 0; i < retries; i++) {
      const result = await this.sendMessage(targetDid, content, messageType, options);
      
      if (result.success) {
        return result;
      }
      
      lastError = result.error || 'Unknown error';
      logger.warn(`消息发送失败 (第${i + 1}次尝试): ${lastError}`);
      
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

  /**
   * 发送系统通知消息
   */
  public async sendSystemNotification(
    targetDid: string,
    notificationType: string,
    payload: any,
    options: MessageCallOptions = {}
  ): Promise<MessageCallResult> {
    const systemMessage = {
      type: 'system_notification',
      notification_type: notificationType,
      payload: payload,
      sender: this.callerDid,
      timestamp: new Date().toISOString()
    };

    return await this.sendMessage(
      targetDid,
      JSON.stringify(systemMessage),
      'system',
      options
    );
  }

  /**
   * 发送心跳消息
   */
  public async sendHeartbeat(
    targetDid: string,
    options: MessageCallOptions = {}
  ): Promise<MessageCallResult> {
    const heartbeatMessage = {
      type: 'heartbeat',
      sender: this.callerDid,
      timestamp: new Date().toISOString()
    };

    return await this.sendMessage(
      targetDid,
      JSON.stringify(heartbeatMessage),
      'heartbeat',
      { ...options, timeout: 5000 }
    );
  }
}

/**
 * 全局消息发送函数 - 对应Python版本的agent_msg_post
 */
export async function agentMsgPost(
  callerAgent: string,
  targetAgent: string,
  content: string,
  messageType: string = 'text'
): Promise<any> {
  try {
    // 获取调用者用户对象
    const callerUser = await ANPUser.fromDid(callerAgent);
    
    // 创建消息发送器
    const messageCaller = new AgentMessageCaller(
      callerUser.jwtPrivateKeyPath, // 简化版，实际应该读取私钥内容
      callerAgent
    );

    // 发送消息
    const result = await messageCaller.sendMessage(targetAgent, content, messageType);

    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error || '消息发送失败');
    }

  } catch (error) {
    logger.error(`Agent消息发送失败: ${error}`);
    throw error;
  }
}

/**
 * 响应数据转换函数 - 对应Python版本的response_to_dict
 */
export async function responseToDict(response: any): Promise<any> {
  if (typeof response === 'string') {
    try {
      return JSON.parse(response);
    } catch (error) {
      return { raw_response: response };
    }
  } else if (typeof response === 'object' && response !== null) {
    return response;
  } else {
    return { value: response };
  }
}
