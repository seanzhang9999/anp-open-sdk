/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { ServicePointManager, ServicePointRequest, ServicePointResponse } from './service-point-manager';
import { getLogger } from '@foundation/utils';

const logger = getLogger('ServicePointRouter');

export interface RouteHandler {
  (request: ServicePointRequest): Promise<ServicePointResponse>;
}

export interface RouteDefinition {
  method: string;
  pattern: string;
  handler: RouteHandler;
  requireAuth?: boolean;
  description?: string;
}

export interface MiddlewareFunction {
  (request: ServicePointRequest, next: () => Promise<ServicePointResponse>): Promise<ServicePointResponse>;
}

/**
 * 服务点路由器
 * 提供灵活的路由配置和中间件支持
 */
export class ServicePointRouter {
  private routes: RouteDefinition[] = [];
  private middlewares: MiddlewareFunction[] = [];
  private servicePointManager: ServicePointManager;

  constructor() {
    this.servicePointManager = new ServicePointManager();
    this.setupDefaultRoutes();
  }

  /**
   * 添加路由
   */
  addRoute(route: RouteDefinition): void {
    this.routes.push(route);
    logger.debug(`添加路由: ${route.method} ${route.pattern}`);
  }

  /**
   * 添加中间件
   */
  addMiddleware(middleware: MiddlewareFunction): void {
    this.middlewares.push(middleware);
    logger.debug('添加中间件');
  }

  /**
   * 处理请求
   */
  async handleRequest(request: ServicePointRequest): Promise<ServicePointResponse> {
    try {
      // 应用中间件
      return await this.applyMiddlewares(request, async () => {
        // 查找匹配的路由
        const matchedRoute = this.findMatchingRoute(request);
        
        if (matchedRoute) {
          logger.debug(`匹配路由: ${matchedRoute.method} ${matchedRoute.pattern}`);
          return await matchedRoute.handler(request);
        }

        // 如果没有匹配的自定义路由，使用默认的ServicePointManager
        return await this.servicePointManager.handleRequest(request);
      });

    } catch (error) {
      logger.error(`路由处理失败: ${error}`);
      return this.createErrorResponse(500, `路由处理错误: ${error}`);
    }
  }

  /**
   * 应用中间件
   */
  private async applyMiddlewares(
    request: ServicePointRequest,
    finalHandler: () => Promise<ServicePointResponse>
  ): Promise<ServicePointResponse> {
    let index = 0;

    const next = async (): Promise<ServicePointResponse> => {
      if (index >= this.middlewares.length) {
        return await finalHandler();
      }

      const middleware = this.middlewares[index++];
      return await middleware(request, next);
    };

    return await next();
  }

  /**
   * 查找匹配的路由
   */
  private findMatchingRoute(request: ServicePointRequest): RouteDefinition | null {
    for (const route of this.routes) {
      if (this.matchRoute(request, route)) {
        return route;
      }
    }
    return null;
  }

  /**
   * 检查路由是否匹配
   */
  private matchRoute(request: ServicePointRequest, route: RouteDefinition): boolean {
    // 检查HTTP方法
    if (route.method !== '*' && route.method.toUpperCase() !== request.method.toUpperCase()) {
      return false;
    }

    // 检查路径模式
    return this.matchPattern(request.path, route.pattern);
  }

  /**
   * 模式匹配
   */
  private matchPattern(path: string, pattern: string): boolean {
    try {
      // 将路径模式转换为正则表达式
      const regexPattern = pattern
        .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // 转义特殊字符
        .replace(/\\\*/g, '.*') // 将 \* 替换为 .*
        .replace(/:\w+/g, '[^/]+'); // 将 :param 替换为 [^/]+
      
      const regex = new RegExp(`^${regexPattern}$`);
      return regex.test(path);
    } catch (error) {
      logger.warn(`模式匹配失败: pattern=${pattern}, path=${path}, error=${error}`);
      return false;
    }
  }

  /**
   * 设置默认路由
   */
  private setupDefaultRoutes(): void {
    // 添加一些常用的路由快捷方法
    this.addRoute({
      method: 'GET',
      pattern: '/api/info',
      handler: async (request) => {
        return this.createResponse(200, {
          name: 'ANP ServicePoint',
          version: '1.0.0',
          description: 'ANP服务端点处理器',
          endpoints: this.getEndpointList(),
          timestamp: new Date().toISOString()
        });
      },
      description: 'API信息端点'
    });

    this.addRoute({
      method: 'GET',
      pattern: '/api/routes',
      handler: async (request) => {
        return this.createResponse(200, {
          routes: this.routes.map(route => ({
            method: route.method,
            pattern: route.pattern,
            requireAuth: route.requireAuth || false,
            description: route.description
          }))
        });
      },
      description: '路由列表端点'
    });
  }

  /**
   * 获取端点列表
   */
  private getEndpointList(): string[] {
    return [
      'GET /health - 健康检查',
      'GET /status - 状态检查',
      'GET /wba/{user}/{file} - DID文档和Agent文件',
      'GET /publisher/agents - 智能体列表',
      'GET /publisher/stats - 智能体统计',
      'POST /host/did - 创建托管DID',
      'GET /host/dids - 托管DID列表',
      'POST /auth/verify - 认证验证',
      'GET /auth/exempt/rules - 豁免规则列表',
      'GET /api/info - API信息',
      'GET /api/routes - 路由列表'
    ];
  }

  /**
   * 便捷方法：添加GET路由
   */
  get(pattern: string, handler: RouteHandler, options?: { requireAuth?: boolean; description?: string }): void {
    this.addRoute({
      method: 'GET',
      pattern,
      handler,
      requireAuth: options?.requireAuth,
      description: options?.description
    });
  }

  /**
   * 便捷方法：添加POST路由
   */
  post(pattern: string, handler: RouteHandler, options?: { requireAuth?: boolean; description?: string }): void {
    this.addRoute({
      method: 'POST',
      pattern,
      handler,
      requireAuth: options?.requireAuth,
      description: options?.description
    });
  }

  /**
   * 便捷方法：添加PUT路由
   */
  put(pattern: string, handler: RouteHandler, options?: { requireAuth?: boolean; description?: string }): void {
    this.addRoute({
      method: 'PUT',
      pattern,
      handler,
      requireAuth: options?.requireAuth,
      description: options?.description
    });
  }

  /**
   * 便捷方法：添加DELETE路由
   */
  delete(pattern: string, handler: RouteHandler, options?: { requireAuth?: boolean; description?: string }): void {
    this.addRoute({
      method: 'DELETE',
      pattern,
      handler,
      requireAuth: options?.requireAuth,
      description: options?.description
    });
  }

  /**
   * 添加CORS中间件
   */
  addCorsMiddleware(options?: {
    origin?: string | string[];
    methods?: string[];
    headers?: string[];
  }): void {
    this.addMiddleware(async (request, next) => {
      const response = await next();
      
      // 添加CORS头
      response.headers['Access-Control-Allow-Origin'] = 
        Array.isArray(options?.origin) ? options.origin.join(', ') : (options?.origin || '*');
      response.headers['Access-Control-Allow-Methods'] = 
        options?.methods?.join(', ') || 'GET, POST, PUT, DELETE, OPTIONS';
      response.headers['Access-Control-Allow-Headers'] = 
        options?.headers?.join(', ') || 'Content-Type, Authorization, X-Requested-With';

      return response;
    });
  }

  /**
   * 添加日志中间件
   */
  addLoggingMiddleware(): void {
    this.addMiddleware(async (request, next) => {
      const startTime = Date.now();
      logger.info(`${request.method} ${request.path} - 开始处理`);
      
      const response = await next();
      
      const duration = Date.now() - startTime;
      logger.info(`${request.method} ${request.path} - ${response.status} (${duration}ms)`);
      
      return response;
    });
  }

  /**
   * 添加速率限制中间件
   */
  addRateLimitMiddleware(options: {
    windowMs: number;
    maxRequests: number;
  }): void {
    const requestCounts = new Map<string, { count: number; resetTime: number }>();

    this.addMiddleware(async (request, next) => {
      const clientId = request.headers['x-forwarded-for'] || request.headers['x-real-ip'] || 'unknown';
      const now = Date.now();
      
      const clientData = requestCounts.get(clientId);
      
      if (!clientData || now > clientData.resetTime) {
        requestCounts.set(clientId, {
          count: 1,
          resetTime: now + options.windowMs
        });
      } else {
        clientData.count++;
        
        if (clientData.count > options.maxRequests) {
          return this.createErrorResponse(429, '请求过于频繁，请稍后再试');
        }
      }

      return await next();
    });
  }

  /**
   * 创建成功响应
   */
  private createResponse(status: number, data: any): ServicePointResponse {
    return {
      status,
      headers: {
        'Content-Type': 'application/json',
        'X-Powered-By': 'ANP-ServicePoint-Router'
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
        'X-Powered-By': 'ANP-ServicePoint-Router'
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

  /**
   * 获取所有路由信息
   */
  getRoutes(): RouteDefinition[] {
    return [...this.routes];
  }

  /**
   * 清除所有路由
   */
  clearRoutes(): void {
    this.routes = [];
    this.setupDefaultRoutes();
  }

  /**
   * 清除所有中间件
   */
  clearMiddlewares(): void {
    this.middlewares = [];
  }
}