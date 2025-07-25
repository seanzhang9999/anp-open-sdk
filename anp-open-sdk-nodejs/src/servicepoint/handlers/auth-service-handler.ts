/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { DomainManager } from '@foundation/domain';
import { AuthVerifier } from '@foundation/auth';
import { getLogger } from '@foundation/utils';

const logger = getLogger('AuthServiceHandler');

export interface AuthServiceResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export interface AuthRequest {
  token?: string;
  headers?: Record<string, string>;
  method?: string;
  path?: string;
}

export interface AuthResult {
  authenticated: boolean;
  userId?: string;
  did?: string;
  error?: string;
  tokenValid?: boolean;
  permissions?: string[];
}

/**
 * 认证服务处理器
 * 对应Python版本的auth_service_handler.py
 */
export class AuthServiceHandler {

  /**
   * 处理认证请求
   */
  public static async handleAuthRequest(
    authRequest: AuthRequest, 
    host: string, 
    port: number
  ): Promise<AuthServiceResponse> {
    try {
      // 验证域名访问权限
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 提取认证信息
      const authInfo = this.extractAuthInfo(authRequest);
      if (!authInfo.token) {
        return {
          success: true,
          data: {
            authenticated: false,
            error: 'No authentication token provided'
          }
        };
      }

      // 验证token
      const authResult = await this.verifyAuthToken(authInfo.token, host, port);
      
      return { success: true, data: authResult };

    } catch (error) {
      logger.error(`认证请求处理失败: ${error}`);
      return { success: false, error: `认证请求处理失败: ${error}` };
    }
  }

  /**
   * 从请求中提取认证信息
   */
  private static extractAuthInfo(authRequest: AuthRequest): { token?: string; method?: string } {
    let token: string | undefined;

    // 从Authorization头提取token
    if (authRequest.headers?.authorization) {
      const authHeader = authRequest.headers.authorization;
      if (authHeader.startsWith('Bearer ')) {
        token = authHeader.substring(7);
      } else if (authHeader.startsWith('Token ')) {
        token = authHeader.substring(6);
      } else {
        token = authHeader;
      }
    }

    // 从直接的token字段提取
    if (!token && authRequest.token) {
      token = authRequest.token;
    }

    // 从其他可能的头部提取
    if (!token && authRequest.headers) {
      const headers = authRequest.headers;
      token = headers['x-auth-token'] || 
             headers['X-Auth-Token'] || 
             headers['x-access-token'] || 
             headers['X-Access-Token'];
    }

    return {
      token,
      method: authRequest.method
    };
  }

  /**
   * 验证认证token
   */
  private static async verifyAuthToken(token: string, host: string, port: number): Promise<AuthResult> {
    try {
      // 使用AuthVerifier验证token
      const authVerifier = new AuthVerifier();
      
      // 构造模拟请求对象用于验证
      const mockRequest = {
        headers: {
          authorization: `Bearer ${token}`
        },
        method: 'POST',
        url: '/auth/verify'
      };

      const verificationResult = await authVerifier.authenticateRequest(mockRequest);

      if (!verificationResult.success || verificationResult.success === 'NotSupport') {
        return {
          authenticated: false,
          tokenValid: false,
          error: verificationResult.message || 'Token verification failed'
        };
      }

      // 从结果中提取用户信息
      const result = verificationResult.result;
      const userId = result?.req_did;
      const did = result?.req_did;

      // 检查是否有访问令牌
      const hasValidToken = result?.access_token || result?.token_type === 'bearer';

      return {
        authenticated: true,
        tokenValid: hasValidToken,
        userId,
        did,
        permissions: ['read', 'write'] // 默认权限
      };

    } catch (error) {
      logger.error(`Token验证失败: ${error}`);
      return {
        authenticated: false,
        tokenValid: false,
        error: `Token验证失败: ${error}`
      };
    }
  }

  /**
   * 检查用户权限
   */
  public static async checkUserPermissions(
    userId: string, 
    requiredPermissions: string[], 
    host: string, 
    port: number
  ): Promise<AuthServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      // TODO: 实现权限检查逻辑
      // 这里应该查询用户的权限信息
      const userPermissions = await this.getUserPermissions(userId, host, port);

      const hasAllPermissions = requiredPermissions.every(permission => 
        userPermissions.includes(permission)
      );

      return {
        success: true,
        data: {
          userId,
          hasPermissions: hasAllPermissions,
          userPermissions,
          requiredPermissions
        }
      };

    } catch (error) {
      logger.error(`权限检查失败: ${error}`);
      return { success: false, error: `权限检查失败: ${error}` };
    }
  }

  /**
   * 获取用户权限列表
   */
  private static async getUserPermissions(userId: string, host: string, port: number): Promise<string[]> {
    try {
      // TODO: 从数据库或配置文件中获取用户权限
      // 暂时返回默认权限
      return ['read', 'write'];
    } catch (error) {
      logger.warn(`获取用户权限失败: ${error}`);
      return [];
    }
  }

  /**
   * 生成认证响应头
   */
  public static generateAuthHeaders(authResult: AuthResult): Record<string, string> {
    const headers: Record<string, string> = {};

    if (authResult.authenticated) {
      headers['X-Auth-Status'] = 'authenticated';
      if (authResult.userId) {
        headers['X-User-ID'] = authResult.userId;
      }
      if (authResult.did) {
        headers['X-User-DID'] = authResult.did;
      }
      if (authResult.permissions && authResult.permissions.length > 0) {
        headers['X-User-Permissions'] = authResult.permissions.join(',');
      }
    } else {
      headers['X-Auth-Status'] = 'unauthenticated';
      if (authResult.error) {
        headers['X-Auth-Error'] = authResult.error;
      }
    }

    return headers;
  }

  /**
   * 验证API密钥
   */
  public static async verifyApiKey(apiKey: string, host: string, port: number): Promise<AuthServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      // TODO: 实现API密钥验证逻辑
      // 这里应该查询有效的API密钥
      const isValidApiKey = await this.checkApiKeyValidity(apiKey, host, port);

      return {
        success: true,
        data: {
          valid: isValidApiKey,
          apiKey: isValidApiKey ? apiKey : undefined
        }
      };

    } catch (error) {
      logger.error(`API密钥验证失败: ${error}`);
      return { success: false, error: `API密钥验证失败: ${error}` };
    }
  }

  /**
   * 检查API密钥有效性
   */
  private static async checkApiKeyValidity(apiKey: string, host: string, port: number): Promise<boolean> {
    try {
      // TODO: 实现实际的API密钥验证逻辑
      // 暂时返回简单的验证结果
      return apiKey.length >= 32 && apiKey.startsWith('anp_');
    } catch (error) {
      logger.warn(`API密钥验证失败: ${error}`);
      return false;
    }
  }
}