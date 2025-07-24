/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as https from 'https';
import * as http from 'http';
import { URL } from 'url';
import {
  AuthenticationContext,
  AuthenticatedRequestResult,
  HttpRequestOptions,
  HttpResponse,
  AuthResult,
  DIDDocument,
  TokenInfo
} from '../types';
import { DIDWbaAuth, DIDWbaAuthClient } from '../did';
import { getUserDataManager } from '../user';
import { getLogger } from '../utils';

const logger = getLogger('AuthInitiator');

/**
 * 认证发起器 - 对应Python版本的auth_initiator.py
 * 提供完整的认证请求流程，包括token管理和DID认证
 */
export class AuthInitiator {
  private authClients: Map<string, DIDWbaAuthClient> = new Map();

  /**
   * 发送认证请求 - 对应Python的send_authenticated_request
   * 自动优先使用本地token，否则走DID认证，token失效自动fallback
   */
  async sendAuthenticatedRequest(
    callerDid: string,
    targetDid: string,
    requestUrl: string,
    method: string = 'GET',
    jsonData?: any,
    customHeaders?: Record<string, string>,
    useTwoWayAuth: boolean = true
  ): Promise<AuthenticatedRequestResult> {
    try {
      // 暂时屏蔽token分支，直接使用DID认证
      // TODO: 实现token优先逻辑
      
      const result = await this.executeWbaAuthFlow(
        callerDid,
        targetDid,
        requestUrl,
        method,
        jsonData,
        customHeaders,
        useTwoWayAuth
      );

      logger.info(`Request: ${requestUrl}, Status: ${result.status}, Auth: ${result.is_auth_pass}, Info: ${result.info}`);
      return result;

    } catch (error) {
      logger.error(`认证请求过程中发生错误: ${error}`);
      return {
        status: 500,
        response: '',
        info: `请求中发生错误: ${error}`,
        is_auth_pass: false
      };
    }
  }

  /**
   * 执行WBA认证流程 - 对应Python的_execute_wba_auth_flow
   */
  private async executeWbaAuthFlow(
    callerDid: string,
    targetDid: string,
    requestUrl: string,
    method: string = 'GET',
    jsonData?: any,
    customHeaders?: Record<string, string>,
    useTwoWayAuth: boolean = true
  ): Promise<AuthenticatedRequestResult> {
    const context: AuthenticationContext = {
      caller_did: callerDid,
      target_did: targetDid,
      request_url: requestUrl,
      method,
      custom_headers: customHeaders || {},
      json_data: jsonData,
      use_two_way_auth: useTwoWayAuth
    };

    try {
      // 首次尝试双向认证
      let { status, responseHeaders, responseData } = await this.sendWbaHttpRequest(context);

      if (status === 401 || status === 403) {
        // 双向认证失败，尝试单向认证
        context.use_two_way_auth = false;
        const fallbackResult = await this.sendWbaHttpRequest(context);
        status = fallbackResult.status;
        responseHeaders = fallbackResult.responseHeaders;
        responseData = fallbackResult.responseData;

        if (status === 200) {
          const { authValue, token } = this.parseTokenFromResponse(responseHeaders);
          if (token) {
            if (authValue === '单向认证') {
              await this.storeTokenFromRemote(callerDid, targetDid, token);
              return {
                status,
                response: JSON.stringify(responseData),
                info: `单向认证成功! 已保存 ${targetDid} 颁发的token`,
                is_auth_pass: true
              };
            } else {
              return {
                status,
                response: JSON.stringify(responseData),
                info: '返回200，但是token单向认证失败，可能是其他认证token，认证失败',
                is_auth_pass: false
              };
            }
          } else {
            return {
              status,
              response: JSON.stringify(responseData),
              info: '返回200，没有token，可能是无认证页面',
              is_auth_pass: true
            };
          }
        } else if (status === 401 || status === 403) {
          return {
            status,
            response: JSON.stringify(responseData),
            info: '双向和单向认证均返回401/403，认证失败',
            is_auth_pass: false
          };
        }
      } else if (status === 200) {
        // 双向认证成功
        const { authValue, token } = this.parseTokenFromResponse(responseHeaders);
        if (token) {
          const authHeader = responseHeaders['authorization'];
          if (authHeader && await this.verifyResponseAuthHeader(authHeader)) {
            await this.storeTokenFromRemote(callerDid, targetDid, token);
            return {
              status,
              response: JSON.stringify(responseData),
              info: `DID双向认证成功! 已保存 ${targetDid} 颁发的token`,
              is_auth_pass: true
            };
          } else {
            return {
              status,
              response: JSON.stringify(responseData),
              info: '返回200，返回token，但是resp_did返回认证验证失败!',
              is_auth_pass: false
            };
          }
        } else {
          return {
            status,
            response: JSON.stringify(responseData),
            info: '返回200，无token，可能是无认证页面',
            is_auth_pass: true
          };
        }
      }

      return {
        status,
        response: JSON.stringify(responseData),
        info: `未处理的状态码: ${status}`,
        is_auth_pass: false
      };

    } catch (error) {
      logger.error(`WBA认证流程错误: ${error}`);
      return {
        status: 500,
        response: '',
        info: `认证过程中发生错误: ${error}`,
        is_auth_pass: false
      };
    }
  }

  /**
   * 发送WBA HTTP请求 - 对应Python的_send_wba_http_request
   */
  private async sendWbaHttpRequest(context: AuthenticationContext): Promise<{
    status: number;
    responseHeaders: Record<string, string>;
    responseData: any;
  }> {
    try {
      // 构建认证头
      const authHeaders = await this.buildWbaAuthHeader(context);
      
      // 合并头部
      const mergedHeaders = {
        ...context.custom_headers,
        ...authHeaders,
        'Content-Type': 'application/json'
      };

      // 发送HTTP请求
      const response = await this.sendHttpRequest(
        context.request_url,
        {
          method: context.method || 'GET',
          headers: mergedHeaders,
          json: context.json_data
        }
      );

      return {
        status: response.status,
        responseHeaders: response.headers,
        responseData: response.data
      };

    } catch (error) {
      logger.error(`发送WBA HTTP请求错误: ${error}`);
      throw error;
    }
  }

  /**
   * 构建WBA认证头 - 对应Python的_build_wba_auth_header
   */
  private async buildWbaAuthHeader(context: AuthenticationContext): Promise<Record<string, string>> {
    const userDataManager = getUserDataManager();
    const userData = userDataManager.getUserData(context.caller_did);
    
    if (!userData) {
      throw new Error(`Could not find user data for DID: ${context.caller_did}`);
    }

    // 获取或创建认证客户端
    let authClient = this.authClients.get(context.caller_did);
    if (!authClient) {
      authClient = new DIDWbaAuthClient(
        userData.didDocPath,
        userData.passwordPaths.did_private_key_file_path
      );
      this.authClients.set(context.caller_did, authClient);
    }

    // 根据认证类型选择相应的方法
    if (context.use_two_way_auth) {
      // 双向认证
      return await authClient.getAuthHeaderTwoWay(context.request_url, context.target_did);
    } else {
      // 单向认证
      return await authClient.getAuthHeader(context.request_url);
    }
  }

  /**
   * 解析响应中的token - 对应Python的_parse_token_from_response
   */
  private parseTokenFromResponse(responseHeaders: Record<string, string>): {
    authValue: string;
    token: string | null;
  } {
    const authHeader = responseHeaders['authorization'];
    if (!authHeader) {
      return { authValue: '没有Auth头', token: null };
    }

    // 检查Bearer格式
    const bearerMatch = authHeader.match(/^bearer\s+(.+)$/i);
    if (bearerMatch) {
      logger.debug('获得单向认证令牌，兼容无双向认证的服务');
      return { authValue: '单向认证', token: bearerMatch[1] };
    }

    // 尝试解析JSON格式
    try {
      const authData = JSON.parse(authHeader);
      if (typeof authData === 'object' && authData !== null) {
        const token = authData.access_token;
        const didAuthHeader = authData.resp_did_auth_header?.Authorization;
        
        if (didAuthHeader && token) {
          return { authValue: '双向认证', token };
        } else {
          return { authValue: 'AuthDict无法识别', token: null };
        }
      }
    } catch (error) {
      logger.error('JSON解析AuthToken失败:', error);
    }

    return { authValue: 'JSON解析AuthToken失败', token: null };
  }

  /**
   * 验证响应认证头 - 对应Python的_verify_response_auth_header
   */
  private async verifyResponseAuthHeader(authValue: string): Promise<boolean> {
    try {
      // 处理JSON格式的auth_value
      let actualAuthHeader = authValue;
      if (authValue.startsWith('{') && authValue.endsWith('}')) {
        try {
          const authJson = JSON.parse(authValue);
          if (authJson.resp_did_auth_header?.Authorization) {
            actualAuthHeader = authJson.resp_did_auth_header.Authorization;
          }
        } catch (error) {
          // 如果不是有效的JSON，保持原样
        }
      }

      // 尝试解析为双向认证头
      let headerParts;
      let isTwoWayAuth = false;
      try {
        headerParts = DIDWbaAuth.extractAuthHeaderPartsTwoWay(actualAuthHeader);
        isTwoWayAuth = true;
      } catch (error) {
        // 如果双向认证解析失败，尝试单向认证
        try {
          headerParts = DIDWbaAuth.extractAuthHeaderParts(actualAuthHeader);
          isTwoWayAuth = false;
        } catch (fallbackError) {
          logger.error('AuthHeader格式错误');
          return false;
        }
      }

      if (!headerParts) {
        logger.error('AuthHeader格式错误');
        return false;
      }

      const { did, timestamp } = headerParts;
      
      // 验证时间戳
      if (!this.verifyTimestamp(timestamp)) {
        return false;
      }

      // 解析DID文档
      const didDocument = await this.resolveDidDocumentInsecurely(did);
      if (!didDocument) {
        logger.error('Failed to resolve DID document');
        return false;
      }

      // 验证签名
      const serviceDomain = 'virtual.WBAback';
      let result;
      
      if (isTwoWayAuth) {
        result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
          actualAuthHeader,
          didDocument,
          serviceDomain
        );
      } else {
        result = await DIDWbaAuth.verifyAuthHeaderSignature(
          actualAuthHeader,
          didDocument,
          serviceDomain
        );
      }

      logger.debug(`签名验证结果: ${result.valid}, 消息: ${result.message}`);
      return result.valid;

    } catch (error) {
      logger.error(`验证签名时出错: ${error}`);
      return false;
    }
  }

  /**
   * 本地DID文档解析 - 对应Python的_resolve_did_document_insecurely
   */
  private async resolveDidDocumentInsecurely(did: string): Promise<DIDDocument | null> {
    try {
      const parts = did.split(':');
      if (parts.length < 5 || parts[0] !== 'did' || parts[1] !== 'wba') {
        logger.debug(`无效的DID格式: ${did}`);
        return null;
      }

      // 提取主机名和端口
      let hostname = parts[2];
      if (hostname.includes('%3A')) {
        hostname = decodeURIComponent(hostname);
      }

      const pathSegments = parts.slice(3);
      const userId = pathSegments[pathSegments.length - 1];
      const userDir = pathSegments[pathSegments.length - 2];

      const httpUrl = `http://${hostname}/wba/${userDir}/${userId}/did.json`;

      // 发送HTTP请求获取DID文档
      try {
        const response = await this.sendHttpRequest(httpUrl, { method: 'GET' });
        if (response.status === 200) {
          logger.debug(`通过DID标识解析的${httpUrl}获取${did}的DID文档`);
          return response.data as DIDDocument;
        } else {
          logger.debug(`did本地解析器地址${httpUrl}获取失败，状态码: ${response.status}`);
          return null;
        }
      } catch (error) {
        logger.debug(`解析DID文档时出错: ${error}`);
        return null;
      }

    } catch (error) {
      logger.debug(`解析DID文档时出错: ${error}`);
      return null;
    }
  }

  /**
   * 存储远程token
   */
  private async storeTokenFromRemote(callerDid: string, targetDid: string, token: string): Promise<void> {
    try {
      const userDataManager = getUserDataManager();
      const userData = userDataManager.getUserData(callerDid);
      
      if (userData) {
        // TODO: 实现token存储逻辑
        // userData.contactManager.storeTokenFromRemote(targetDid, token);
        logger.debug(`已为 ${callerDid} 存储来自 ${targetDid} 的token`);
      }
    } catch (error) {
      logger.error(`存储token失败: ${error}`);
    }
  }

  /**
   * 验证时间戳
   */
  private verifyTimestamp(timestamp: string): boolean {
    try {
      const timestampNum = parseInt(timestamp, 10);
      const now = Math.floor(Date.now() / 1000);
      const diff = Math.abs(now - timestampNum);
      
      // 允许5分钟的时间差
      return diff <= 300;
    } catch (error) {
      logger.error(`时间戳验证失败: ${error}`);
      return false;
    }
  }

  /**
   * 发送HTTP请求的通用方法
   */
  private async sendHttpRequest(url: string, options: HttpRequestOptions): Promise<HttpResponse> {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const isHttps = parsedUrl.protocol === 'https:';
      const httpModule = isHttps ? https : http;

      const requestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (isHttps ? 443 : 80),
        path: parsedUrl.pathname + parsedUrl.search,
        method: options.method || 'GET',
        headers: options.headers || {}
      };

      const req = httpModule.request(requestOptions, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const responseData = data ? JSON.parse(data) : {};
            resolve({
              status: res.statusCode || 0,
              headers: res.headers as Record<string, string>,
              data: responseData
            });
          } catch (error) {
            resolve({
              status: res.statusCode || 0,
              headers: res.headers as Record<string, string>,
              data: { text: data }
            });
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      // 发送请求体
      if (options.json) {
        req.write(JSON.stringify(options.json));
      } else if (options.body) {
        req.write(options.body);
      }

      req.end();
    });
  }

  /**
   * 清理认证客户端缓存
   */
  clearCache(): void {
    this.authClients.clear();
  }
}

// 全局认证发起器实例
let _authInitiator: AuthInitiator | null = null;

/**
 * 获取全局认证发起器实例
 */
export function getAuthInitiator(): AuthInitiator {
  if (_authInitiator === null) {
    _authInitiator = new AuthInitiator();
  }
  return _authInitiator;
}

/**
 * 重置全局认证发起器实例（主要用于测试）
 */
export function resetAuthInitiator(): void {
  _authInitiator = null;
}