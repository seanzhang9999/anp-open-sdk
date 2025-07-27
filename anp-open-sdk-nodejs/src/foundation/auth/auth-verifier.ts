/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as jwt from 'jsonwebtoken';
import {
  AuthenticationContext,
  AuthResult,
  AuthHeaderParts,
  NonceInfo,
  AuthResponse,
  BearerTokenPayload,
  DIDDocument,
  TokenInfo
} from '../types';
import { DIDWbaAuth } from '../did';
import { getUserDataManager } from '../user';
import { getLogger } from '../utils';

const logger = getLogger('AuthVerifier');

/**
 * 认证验证器 - 对应Python版本的auth_verifier.py
 * 提供完整的请求认证验证功能，包括Bearer token和DID认证
 */
export class AuthVerifier {
  private validServerNonces: Map<string, NonceInfo> = new Map();
  private nonceExpireMinutes: number = 5;

  constructor() {
    // 定期清理过期的nonce
    setInterval(() => {
      this.cleanupExpiredNonces();
    }, 60000); // 每分钟清理一次
  }

  /**
   * 验证认证请求 - 对应Python的_authenticate_request
   */
  async authenticateRequest(request: any): Promise<{
    success: boolean | string;
    message: string;
    result: any;
  }> {
    try {
      // 提取Authorization头
      const authHeader = this.extractAuthHeader(request);
      if (!authHeader) {
        return {
          success: false,
          message: 'Missing Authorization header',
          result: {}
        };
      }

      // 检查是否是Bearer token
      if (authHeader.startsWith('Bearer ')) {
        const reqDid = this.extractReqDid(request);
        const targetDid = this.extractTargetDid(request);
        
        if (!reqDid || !targetDid) {
          return {
            success: false,
            message: 'Missing req_did or resp_did for Bearer token',
            result: {}
          };
        }

        try {
          const result = await this.verifyBearerToken(authHeader, reqDid, targetDid);
          return {
            success: true,
            message: 'Bearer token verified',
            result
          };
        } catch (error) {
          logger.debug(`Bearer认证失败: ${error}`);
          return {
            success: false,
            message: `Bearer token verification failed: ${error}`,
            result: {}
          };
        }
      }

      // DID认证流程
      const { reqDid, targetDid } = this.extractDidFromAuthHeader(authHeader);
      if (!reqDid) {
        return {
          success: false,
          message: 'Cannot extract caller DID from authorization header',
          result: {}
        };
      }

      let useTwoWayAuth = true;
      let finalTargetDid = targetDid;

      if (!targetDid) {
        useTwoWayAuth = false;
        // 尝试从查询参数获取resp_did
        finalTargetDid = this.extractTargetDidFromQuery(request);
      }

      if (!finalTargetDid) {
        return {
          success: 'NotSupport',
          message: 'Cannot accept request that do not mention resp_did and cannot infer from URL',
          result: {}
        };
      }

      // 检查托管DID
      if (finalTargetDid.includes(':hostuser:')) {
        return {
          success: 'NotSupport',
          message: 'Cannot accept request to hosted DID',
          result: {}
        };
      }

      // 构建认证上下文
      const context: AuthenticationContext = {
        caller_did: reqDid,
        target_did: finalTargetDid,
        request_url: this.extractRequestUrl(request),
        method: request.method || 'GET',
        custom_headers: this.extractHeaders(request),
        use_two_way_auth: useTwoWayAuth,
        domain: this.extractDomain(request)
      };

      // 验证WBA认证头
      const { success, result } = await this.verifyWbaHeader(authHeader, context);
      
      if (success) {
        if (!result) {
          return {
            success: false,
            message: 'auth passed but result is None',
            result: {}
          };
        }

        // 处理不同类型的结果
        if (Array.isArray(result)) {
          return {
            success: true,
            message: 'auth passed',
            result: result.length > 0 && typeof result[0] === 'object' ? result[0] : { result }
          };
        } else if (typeof result === 'string') {
          return {
            success: true,
            message: 'auth passed',
            result: { result }
          };
        } else if (typeof result === 'object') {
          return {
            success: true,
            message: 'auth passed',
            result
          };
        } else {
          return {
            success: false,
            message: `auth passed but unexpected result type ${typeof result}`,
            result: { error: `unexpected result type: ${typeof result}`, result }
          };
        }
      } else {
        return {
          success: false,
          message: 'auth failed',
          result: typeof result === 'string' ? { error: result } : result || { error: 'unknown error' }
        };
      }

    } catch (error) {
      logger.error(`认证验证失败: ${error}`);
      return {
        success: false,
        message: `Authentication verification failed: ${error}`,
        result: {}
      };
    }
  }

  /**
   * 验证WBA认证头 - 对应Python的_verify_wba_header
   */
  private async verifyWbaHeader(authHeader: string, context: AuthenticationContext): Promise<{
    success: boolean;
    result: any;
  }> {
    try {
      logger.debug(`验证WBA头 - URL: ${context.request_url}, Header: ${authHeader}`);

      let headerParts: AuthHeaderParts;
      let isTwoWayAuth = context.use_two_way_auth;

      if (context.use_two_way_auth) {
        // 尝试解析双向认证
        try {
          headerParts = this.extractAuthHeaderPartsTwoWay(authHeader);
        } catch (error) {
          return { success: false, result: `Authentication parsing failed as two way header: ${error}` };
        }
      } else {
        // 回退到标准认证
        try {
          headerParts = this.extractAuthHeaderPartsStandard(authHeader);
          isTwoWayAuth = false;
        } catch (error) {
          return { success: false, result: `Authentication parsing failed as one way header: ${error}` };
        }
      }

      logger.debug(`WBA头解析通过: 双向模式: ${isTwoWayAuth}`);

      // 验证时间戳
      if (!this.verifyTimestamp(headerParts.timestamp)) {
        return { success: false, result: 'Invalid timestamp' };
      }

      // 验证nonce防重放
      if (!this.isValidServerNonce(headerParts.nonce)) {
        logger.debug(`Invalid or expired nonce: ${headerParts.nonce}`);
        return { success: false, result: `Invalid nonce: ${headerParts.nonce}` };
      }

      logger.debug(`服务器nonce验证通过: ${headerParts.nonce}`);

      // 解析DID文档
      let didDocument: DIDDocument | null = null;
      if (this.isInsecurelyResolvable(headerParts.did)) {
        logger.debug(`DID ${headerParts.did} 匹配不安全模式，使用本地解析`);
        didDocument = await this.resolveDidDocumentInsecurely(headerParts.did);
      } else {
        logger.debug(`DID ${headerParts.did} 不匹配不安全模式，使用标准方法解析`);
        try {
          const resolvedDoc = await DIDWbaAuth.resolveDidWbaDocument(headerParts.did);
          // 类型转换以匹配我们的DIDDocument接口
          didDocument = resolvedDoc as any;
        } catch (error) {
          return { success: false, result: `Failed to resolve DID document: ${error}` };
        }
      }

      if (!didDocument) {
        return { success: false, result: 'Failed to resolve DID document' };
      }

      // 验证签名
      try {
        const result = await DIDWbaAuth.verifyAuthHeaderSignature(
          authHeader,
          didDocument,
          context.domain || 'localhost'
        );

        if (!result.valid) {
          return { success: false, result: `Invalid signature: ${result.message}` };
        }
      } catch (error) {
        return { success: false, result: `Error verifying signature: ${error}` };
      }

      logger.debug('签名验证通过');

      // 生成WBA认证响应
      const responseHeader = await this.generateWbaAuthResponse(
        headerParts.did,
        isTwoWayAuth || false,
        headerParts.resp_did || context.target_did
      );

      logger.debug(`返回认证头: ${JSON.stringify(responseHeader)}`);

      return { success: true, result: responseHeader };

    } catch (error) {
      return { success: false, result: `Exception in verify_response: ${error}` };
    }
  }

  /**
   * 验证Bearer token - 对应Python的_verify_bearer_token
   */
  private async verifyBearerToken(authHeader: string, reqDid: string, respDid: string): Promise<any> {
    try {
      // 移除Bearer前缀
      const token = authHeader.startsWith('Bearer ') ? authHeader.substring(7) : authHeader;

      const userDataManager = getUserDataManager();
      const respUserData = userDataManager.getUserData(respDid);

      if (!respUserData) {
        throw new Error(`Cannot find user data for resp_did: ${respDid}`);
      }

      // TODO: 实现token存储和验证逻辑
      // 目前使用JWT公钥验证
      const publicKey = respUserData.getJwtPublicKey();
      if (!publicKey) {
        throw new Error('Failed to load JWT public key');
      }

      // 解码和验证token
      const payload = jwt.verify(token, publicKey, { algorithms: ['RS256'] }) as BearerTokenPayload;

      // 检查必需字段
      const requiredFields = ['req_did', 'resp_did', 'exp'];
      for (const field of requiredFields) {
        if (!(field in payload)) {
          throw new Error(`Token missing required field: ${field}`);
        }
      }

      // 验证DID匹配
      if (payload.req_did !== reqDid) {
        throw new Error('req_did mismatch');
      }
      if (payload.resp_did !== respDid) {
        throw new Error('resp_did mismatch');
      }

      // 验证过期时间
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp < now) {
        throw new Error('Token expired');
      }

      logger.debug(`Bearer token验证通过: ${reqDid} -> ${respDid}`);

      return {
        access_token: token,
        token_type: 'bearer',
        req_did: reqDid,
        resp_did: respDid
      };

    } catch (error) {
      logger.debug(`JWT验证错误: ${error}`);
      throw new Error(`Invalid token: ${error}`);
    }
  }

  /**
   * 生成WBA认证响应 - 对应Python的_generate_wba_auth_response
   */
  private async generateWbaAuthResponse(did: string, isTwoWayAuth: boolean, respDid: string): Promise<any> {
    try {
      const userDataManager = getUserDataManager();
      const respUserData = userDataManager.getUserData(respDid);

      if (!respUserData) {
        throw new Error(`Cannot find user data for resp_did: ${respDid}`);
      }

      // 生成访问令牌
      const tokenExpiration = 30 * 60; // 30分钟
      const payload: BearerTokenPayload = {
        req_did: did,
        resp_did: respDid,
        exp: Math.floor(Date.now() / 1000) + tokenExpiration,
        iat: Math.floor(Date.now() / 1000),
        comments: 'open for req_did'
      };

      const privateKey = respUserData.getJwtPrivateKey();
      if (!privateKey) {
        throw new Error('Failed to load JWT private key');
      }
      
      const accessToken = jwt.sign(payload, privateKey, { algorithm: 'RS256' });

      // TODO: 存储token到联系人管理器
      // respUserData.contactManager.storeTokenToRemote(did, accessToken, tokenExpiration);

      // 如果是双向认证，生成响应认证头
      let respDidAuthHeader = null;
      if (respDid && respDid !== '没收到') {
        try {
          // TODO: 实现响应认证头生成
          // 目前返回简化版本
          respDidAuthHeader = {
            Authorization: `DIDWba resp_header_placeholder`
          };
        } catch (error) {
          logger.debug(`生成响应认证头失败: ${error}`);
        }
      }

      if (isTwoWayAuth) {
        return [{
          access_token: accessToken,
          token_type: 'bearer',
          req_did: did,
          resp_did: respDid,
          resp_did_auth_header: respDidAuthHeader
        }];
      } else {
        return `bearer ${accessToken}`;
      }

    } catch (error) {
      logger.error(`生成WBA认证响应失败: ${error}`);
      throw error;
    }
  }

  /**
   * 验证服务器nonce - 对应Python的is_valid_server_nonce
   */
  private isValidServerNonce(nonce: string): boolean {
    const currentTime = new Date();
    
    // 清理过期的nonce
    this.cleanupExpiredNonces();

    // 检查nonce是否已被使用
    if (this.validServerNonces.has(nonce)) {
      logger.warn(`Nonce已被使用: ${nonce}`);
      return false;
    }

    // 标记nonce为已使用
    this.validServerNonces.set(nonce, {
      nonce,
      created_at: currentTime,
      used: true
    });

    logger.debug(`Nonce接受并标记为已使用: ${nonce}`);
    return true;
  }

  /**
   * 清理过期的nonce
   */
  private cleanupExpiredNonces(): void {
    const currentTime = new Date();
    const expiredNonces: string[] = [];

    for (const [nonce, info] of this.validServerNonces.entries()) {
      const timeDiff = currentTime.getTime() - info.created_at.getTime();
      if (timeDiff > this.nonceExpireMinutes * 60 * 1000) {
        expiredNonces.push(nonce);
      }
    }

    for (const nonce of expiredNonces) {
      this.validServerNonces.delete(nonce);
    }
  }

  /**
   * 验证时间戳 - 支持ISO格式和Unix时间戳格式
   * 兼容Node.js生成的毫秒精度（2024-01-01T00:00:00.000Z）和Python生成的秒精度（2024-01-01T00:00:00Z）
   */
  private verifyTimestamp(timestamp: string): boolean {
    try {
      let requestTime: Date;
      
      // 尝试解析ISO格式时间戳
      if (timestamp.includes('T') && (timestamp.includes('Z') || timestamp.includes('+') || timestamp.includes('-'))) {
        requestTime = new Date(timestamp);
        if (isNaN(requestTime.getTime())) {
          logger.error(`无效的ISO时间戳格式: ${timestamp}`);
          return false;
        }
      } else {
        // 尝试解析Unix时间戳（秒或毫秒）
        const timestampNum = parseInt(timestamp, 10);
        if (isNaN(timestampNum)) {
          logger.error(`无效的时间戳格式: ${timestamp}`);
          return false;
        }
        
        // 判断是秒还是毫秒（毫秒时间戳通常大于10^12）
        if (timestampNum > 1000000000000) {
          requestTime = new Date(timestampNum); // 毫秒
        } else {
          requestTime = new Date(timestampNum * 1000); // 秒转毫秒
        }
      }
      
      const now = new Date();
      const diffMinutes = Math.abs(now.getTime() - requestTime.getTime()) / (1000 * 60);
      
      // 允许5分钟的时间差
      const isValid = diffMinutes <= 5;
      
      if (!isValid) {
        logger.debug(`时间戳验证失败: 请求时间=${requestTime.toISOString()}, 当前时间=${now.toISOString()}, 时间差=${diffMinutes.toFixed(2)}分钟`);
      } else {
        logger.debug(`时间戳验证通过: 请求时间=${requestTime.toISOString()}, 时间差=${diffMinutes.toFixed(2)}分钟`);
      }
      
      return isValid;
    } catch (error) {
      logger.error(`时间戳验证失败: ${error}`);
      return false;
    }
  }

  /**
   * 检查DID是否可以不安全地解析
   */
  private isInsecurelyResolvable(did: string): boolean {
    const insecurePatterns = [
      'did:wba:localhost:*',
      'did:wba:localhost%3A*'
    ];

    return insecurePatterns.some(pattern => {
      const regex = new RegExp(pattern.replace(/\*/g, '.*'));
      return regex.test(did);
    });
  }

  /**
   * 本地DID文档解析 - 对应Python版本的_resolve_did_document_insecurely
   */
  private async resolveDidDocumentInsecurely(did: string): Promise<DIDDocument | null> {
    try {
      logger.debug(`🔍 开始解析本地DID文档: ${did}`);
      
      const parts = did.split(':');
      if (parts.length < 5 || parts[0] !== 'did' || parts[1] !== 'wba') {
        logger.debug(`❌ 无效的DID格式: ${did}`);
        return null;
      }

      let hostname = parts[2];
      if (hostname.includes('%3A')) {
        hostname = decodeURIComponent(hostname);
      }

      const pathSegments = parts.slice(3);
      const userId = pathSegments[pathSegments.length - 1];
      const userDir = pathSegments[pathSegments.length - 2];

      const httpUrl = `http://${hostname}/wba/${userDir}/${userId}/did.json`;
      logger.debug(`📡 准备从HTTP端点获取DID文档: ${httpUrl}`);

      // 实现HTTP请求获取DID文档 - 对应Python版本的aiohttp实现
      try {
        const response = await fetch(httpUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          // 设置超时时间
          signal: AbortSignal.timeout(10000) // 10秒超时
        });

        logger.debug(`📡 HTTP请求状态: ${response.status} ${response.statusText}`);

        if (response.status === 200) {
          const didDocument = await response.json();
          logger.debug(`✅ 成功通过DID标识解析的${httpUrl}获取${did}的DID文档`);
          logger.debug(`📄 DID文档内容: ${JSON.stringify(didDocument, null, 2)}`);
          return didDocument as DIDDocument;
        } else {
          logger.debug(`❌ DID本地解析器地址${httpUrl}获取失败，状态码: ${response.status}`);
          return null;
        }
      } catch (fetchError: any) {
        logger.debug(`❌ HTTP请求失败: ${fetchError.message}`);
        if (fetchError.name === 'TimeoutError') {
          logger.debug(`⏰ 请求超时: ${httpUrl}`);
        } else if (fetchError.code === 'ECONNREFUSED') {
          logger.debug(`🔌 连接被拒绝: ${httpUrl}`);
        } else if (fetchError.code === 'ENOTFOUND') {
          logger.debug(`🌐 域名解析失败: ${httpUrl}`);
        }
        return null;
      }

    } catch (error) {
      logger.debug(`❌ 解析DID文档时出错: ${error}`);
      return null;
    }
  }

  // ============================================================================
  // 辅助方法 - 从请求中提取信息
  // ============================================================================

  private extractAuthHeader(request: any): string | null {
    return request.headers?.authorization || 
           request.headers?.Authorization || 
           request.META?.HTTP_AUTHORIZATION || 
           null;
  }

  private extractReqDid(request: any): string | null {
    return request.headers?.req_did || 
           request.headers?.['req-did'] || 
           null;
  }

  private extractTargetDid(request: any): string | null {
    return request.headers?.resp_did || 
           request.headers?.['resp-did'] || 
           null;
  }

  private extractTargetDidFromQuery(request: any): string | null {
    return request.query?.resp_did || 
           request.queryParams?.resp_did || 
           '';
  }

  private extractRequestUrl(request: any): string {
    return request.url || request.originalUrl || '';
  }

  private extractHeaders(request: any): Record<string, string> {
    return request.headers || {};
  }

  private extractDomain(request: any): string {
    return request.hostname || request.host || 'localhost';
  }

  private extractDidFromAuthHeader(authHeader: string): { reqDid: string | null; targetDid: string | null } {
    try {
      const parts = DIDWbaAuth.extractAuthHeaderParts(authHeader);
      return {
        reqDid: parts.did,
        targetDid: parts.respDid || null
      };
    } catch (error) {
      return { reqDid: null, targetDid: null };
    }
  }

  private extractAuthHeaderPartsTwoWay(authHeader: string): AuthHeaderParts {
    // TODO: 实现双向认证头解析
    // 目前使用标准解析
    return this.extractAuthHeaderPartsStandard(authHeader);
  }

  private extractAuthHeaderPartsStandard(authHeader: string): AuthHeaderParts {
    const parts = DIDWbaAuth.extractAuthHeaderParts(authHeader);
    return {
      did: parts.did,
      nonce: parts.nonce,
      timestamp: parts.timestamp,
      keyid: parts.verificationMethod,
      signature: parts.signature,
      resp_did: parts.respDid
    };
  }
  /**
   * 验证认证请求 - 为中间件提供的适配器方法
   * 兼容原有的verifyAuthRequest接口
   */
  async verifyAuthRequest(authHeader: string, request?: any): Promise<AuthResult> {
    try {
      // 构建请求对象，如果没有提供request参数
      const requestObj = request || {
        headers: { authorization: authHeader },
        method: 'POST',
        path: '/',
        query: {},
        hostname: 'localhost'
      };

      // 调用现有的authenticateRequest方法
      const result = await this.authenticateRequest(requestObj);

      // 转换返回格式以匹配AuthResult接口
      if (result.success === true) {
        return {
          success: true,
          caller_did: this.extractCallerDidFromResult(result.result),
          payload: result.result
        };
      } else {
        return {
          success: false,
          error: result.message || 'Authentication failed'
        };
      }

    } catch (error) {
      logger.error(`认证适配器错误: ${error}`);
      return {
        success: false,
        error: `Authentication adapter error: ${error}`
      };
    }
  }

  /**
   * 从认证结果中提取调用者DID
   */
  private extractCallerDidFromResult(result: any): string | undefined {
    if (typeof result === 'object' && result) {
      // 尝试从不同的字段中提取DID
      return result.req_did || result.caller_did || result.did;
    }
    return undefined;
  }
}

// 全局认证验证器实例
let _authVerifier: AuthVerifier | null = null;

/**
 * 获取全局认证验证器实例
 */
export function getAuthVerifier(): AuthVerifier {
  if (_authVerifier === null) {
    _authVerifier = new AuthVerifier();
  }
  return _authVerifier;
}

/**
 * 重置全局认证验证器实例（主要用于测试）
 */
export function resetAuthVerifier(): void {
  _authVerifier = null;
}