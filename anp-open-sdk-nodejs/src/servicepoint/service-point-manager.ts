/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import {
  DIDServiceHandler,
  PublisherServiceHandler,
  AuthServiceHandler,
  HostServiceHandler,
  AuthExemptHandler
} from './handlers';
import { DomainManager } from '../foundation/domain';
import { getLogger } from '../foundation/utils';

const logger = getLogger('ServicePointManager');

export interface ServicePointRequest {
  path: string;
  method: string;
  headers: Record<string, string>;
  body?: any;
  query?: Record<string, string>;
  host: string;
  port: number;
}

export interface ServicePointResponse {
  status: number;
  headers: Record<string, string>;
  body: any;
  success: boolean;
  error?: string;
}

/**
 * 服务点管理器
 * 统一管理所有服务端点的请求处理
 */
export class ServicePointManager {
  private domainManager: DomainManager;

  constructor() {
    this.domainManager = new DomainManager();
  }

  /**
   * 处理服务点请求
   */
  async handleRequest(request: ServicePointRequest): Promise<ServicePointResponse> {
    try {
      logger.debug(`处理服务点请求: ${request.method} ${request.path}`);

      // 验证域名访问权限
      const validation = this.domainManager.validateDomainAccess(request.host, request.port);
      if (!validation.valid) {
        return this.createErrorResponse(403, validation.error || '域名访问被拒绝');
      }

      // 检查认证豁免
      const exemptCheck = await AuthExemptHandler.checkAuthExemption({
        path: request.path,
        method: request.method,
        host: request.host,
        port: request.port
      });

      let isAuthenticated = false;
      let authResult: any = null;

      // 如果不豁免认证，进行认证检查
      if (!exemptCheck.success || !exemptCheck.data?.exempt) {
        const authResponse = await AuthServiceHandler.handleAuthRequest(
          {
            headers: request.headers,
            method: request.method,
            path: request.path
          },
          request.host,
          request.port
        );

        if (authResponse.success && authResponse.data?.authenticated) {
          isAuthenticated = true;
          authResult = authResponse.data;
        } else {
          return this.createErrorResponse(401, '认证失败');
        }
      } else {
        logger.debug(`请求豁免认证: ${request.path}`);
      }

      // 路由到具体的处理器
      return await this.routeRequest(request, isAuthenticated, authResult);

    } catch (error) {
      logger.error(`服务点请求处理失败: ${error}`);
      return this.createErrorResponse(500, `内部服务器错误: ${error}`);
    }
  }

  /**
   * 路由请求到具体的处理器
   */
  private async routeRequest(
    request: ServicePointRequest,
    isAuthenticated: boolean,
    authResult: any
  ): Promise<ServicePointResponse> {
    const { path, method, host, port } = request;

    try {
      // DID服务路由
      if (path.includes('/wba/') && path.endsWith('/did.json')) {
        const userId = this.extractUserIdFromPath(path);
        const result = await DIDServiceHandler.getDidDocument(userId, host, port);
        return this.createResponse(result.success ? 200 : 404, result);
      }

      // Agent描述路由
      if (path.includes('/wba/') && path.endsWith('/ad.json')) {
        const userId = this.extractUserIdFromPath(path);
        const result = await DIDServiceHandler.getAgentDescription(userId, host, port);
        return this.createResponse(result.success ? 200 : 404, result);
      }

      // Agent YAML文件路由
      if (path.includes('/wba/') && path.endsWith('.yaml')) {
        const userId = this.extractUserIdFromPath(path);
        const fileName = this.extractFileNameFromPath(path);
        const result = await DIDServiceHandler.getAgentYamlFile(userId, fileName, host, port);
        return this.createResponse(result.success ? 200 : 404, result);
      }

      // Agent JSON文件路由
      if (path.includes('/wba/') && path.endsWith('.json') && !path.endsWith('/did.json') && !path.endsWith('/ad.json')) {
        const userId = this.extractUserIdFromPath(path);
        const fileName = this.extractFileNameFromPath(path);
        const result = await DIDServiceHandler.getAgentJsonFile(userId, fileName, host, port);
        return this.createResponse(result.success ? 200 : 404, result);
      }

      // 发布者服务路由
      if (path.startsWith('/publisher/')) {
        return await this.handlePublisherRequest(request);
      }

      // 主机服务路由
      if (path.startsWith('/host/')) {
        if (!isAuthenticated) {
          return this.createErrorResponse(401, '主机服务需要认证');
        }
        return await this.handleHostRequest(request);
      }

      // 认证服务路由
      if (path.startsWith('/auth/')) {
        return await this.handleAuthRequest(request);
      }

      // 健康检查
      if (path === '/health' && method === 'GET') {
        return this.createResponse(200, { status: 'healthy', timestamp: new Date().toISOString() });
      }

      // 状态检查
      if (path === '/status' && method === 'GET') {
        const domainStats = this.domainManager.getDomainStats();
        return this.createResponse(200, { 
          status: 'running', 
          domain: `${host}:${port}`,
          stats: domainStats,
          timestamp: new Date().toISOString() 
        });
      }

      // 未找到路由
      return this.createErrorResponse(404, '未找到请求的资源');

    } catch (error) {
      logger.error(`路由请求失败: ${error}`);
      return this.createErrorResponse(500, `路由处理错误: ${error}`);
    }
  }

  /**
   * 处理发布者服务请求
   */
  private async handlePublisherRequest(request: ServicePointRequest): Promise<ServicePointResponse> {
    const { path, method, host, port } = request;

    if (path === '/publisher/agents' && method === 'GET') {
      const result = await PublisherServiceHandler.getPublishedAgents(host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    if (path === '/publisher/stats' && method === 'GET') {
      const result = await PublisherServiceHandler.getAgentStatistics(host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    if (path.startsWith('/publisher/agent/') && method === 'GET') {
      const did = path.replace('/publisher/agent/', '');
      const result = await PublisherServiceHandler.checkAgentAvailability(did, host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    return this.createErrorResponse(404, '未找到发布者服务端点');
  }

  /**
   * 处理主机服务请求
   */
  private async handleHostRequest(request: ServicePointRequest): Promise<ServicePointResponse> {
    const { path, method, body, host, port } = request;

    if (path === '/host/did' && method === 'POST') {
      const hostedDidRequest = {
        did: body?.did,
        requestType: 'create' as const,
        userData: body?.userData,
        metadata: body?.metadata
      };
      const result = await HostServiceHandler.handleHostedDidRequest(hostedDidRequest, host, port);
      return this.createResponse(result.success ? 200 : 400, result);
    }

    if (path.startsWith('/host/did/') && method === 'GET') {
      const did = path.replace('/host/did/', '');
      const result = await HostServiceHandler.getHostedDidStatus(did, host, port);
      return this.createResponse(result.success ? 200 : 404, result);
    }

    if (path === '/host/dids' && method === 'GET') {
      const result = await HostServiceHandler.getAllHostedDids(host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    if (path === '/host/queue/process' && method === 'POST') {
      const result = await HostServiceHandler.processHostedDidQueue(host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    return this.createErrorResponse(404, '未找到主机服务端点');
  }

  /**
   * 处理认证服务请求
   */
  private async handleAuthRequest(request: ServicePointRequest): Promise<ServicePointResponse> {
    const { path, method, body, headers, host, port } = request;

    if (path === '/auth/verify' && method === 'POST') {
      const authRequest = {
        token: body?.token,
        headers,
        method,
        path
      };
      const result = await AuthServiceHandler.handleAuthRequest(authRequest, host, port);
      return this.createResponse(result.success ? 200 : 401, result);
    }

    if (path === '/auth/exempt/check' && method === 'POST') {
      const exemptRequest = {
        path: body?.path,
        method: body?.method,
        host,
        port
      };
      const result = await AuthExemptHandler.checkAuthExemption(exemptRequest);
      return this.createResponse(result.success ? 200 : 400, result);
    }

    if (path === '/auth/exempt/rules' && method === 'GET') {
      const result = await AuthExemptHandler.getAllExemptRules(host, port);
      return this.createResponse(result.success ? 200 : 500, result);
    }

    return this.createErrorResponse(404, '未找到认证服务端点');
  }

  /**
   * 从路径中提取用户ID
   */
  private extractUserIdFromPath(path: string): string {
    const parts = path.split('/');
    // 路径格式: /wba/user/userId/file.ext
    if (parts.length >= 4 && parts[1] === 'wba') {
      return parts[3]; // userId
    }
    return '';
  }

  /**
   * 从路径中提取文件名
   */
  private extractFileNameFromPath(path: string): string {
    const parts = path.split('/');
    const fileName = parts[parts.length - 1];
    // 移除扩展名
    return fileName.replace(/\.[^/.]+$/, '');
  }

  /**
   * 创建成功响应
   */
  private createResponse(status: number, data: any): ServicePointResponse {
    return {
      status,
      headers: {
        'Content-Type': 'application/json',
        'X-Powered-By': 'ANP-ServicePoint'
      },
      body: data,
      success: status >= 200 && status < 300
    };
  }

  /**
   * 创建错误响应
   */
  private createErrorResponse(status: number, error: string): ServicePointResponse {
    return {
      status,
      headers: {
        'Content-Type': 'application/json',
        'X-Powered-By': 'ANP-ServicePoint'
      },
      body: {
        success: false,
        error,
        timestamp: new Date().toISOString()
      },
      success: false,
      error
    };
  }
}