/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Request, Response, NextFunction } from 'express';
import { getGlobalConfig } from '../../foundation/config';
import { AuthVerifier, AuthResult } from '../../foundation/auth';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('AuthMiddleware');

export interface AuthExemptConfig {
  exemptPaths: string[];
}

export class AuthExemptHandler {
  private static exemptPaths: string[] = [];

  public static initialize(config?: AuthExemptConfig): void {
    try {
      if (config) {
        this.exemptPaths = config.exemptPaths;
      } else {
        const globalConfig = getGlobalConfig();
        this.exemptPaths = globalConfig.authMiddleware.exemptPaths;
      }
      logger.debug(`初始化认证豁免路径: ${this.exemptPaths.join(', ')}`);
    } catch (error) {
      logger.warn('无法加载认证豁免配置，使用默认配置');
      this.exemptPaths = ['/', '/health', '/docs'];
    }
  }

  /**
   * 检查路径是否豁免认证
   */
  public static isExempt(path: string): boolean {
    // 检查是否在豁免路径列表中
    for (const exemptPath of this.exemptPaths) {
      // 根路径的精确匹配
      if (exemptPath === "/" && path === "/") {
        return true;
      }
      // 其他路径的精确匹配
      else if (path === exemptPath) {
        return true;
      }
      // 以斜杠结尾的路径的目录匹配
      else if (exemptPath !== '/' && exemptPath.endsWith('/') && path.startsWith(exemptPath)) {
        return true;
      }
      // 通配符匹配
      else if (exemptPath.includes('*')) {
        if (this.matchPattern(path, exemptPath)) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * 简单的通配符匹配
   */
  private static matchPattern(str: string, pattern: string): boolean {
    const regexPattern = pattern
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // 转义特殊字符
      .replace(/\\\*/g, '.*'); // 将 \* 替换为 .*
    
    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(str);
  }
}

export class AuthMiddleware {
  private verifier: AuthVerifier;

  constructor(verifier: AuthVerifier) {
    this.verifier = verifier;
  }

  /**
   * Express中间件函数
   */
  public middleware() {
    return async (req: Request, res: Response, next: NextFunction) => {
      try {
        // 检查是否豁免认证
        if (AuthExemptHandler.isExempt(req.path)) {
          logger.debug(`路径豁免认证: ${req.path}`);
          return next();
        }

        // 获取Authorization header
        const authHeader = req.headers.authorization;
        if (!authHeader) {
          return res.status(401).json({
            error: 'Missing authorization header',
            code: 'AUTH_MISSING'
          });
        }

        // 验证认证
        const result: AuthResult = await this.verifier.verifyAuthRequest(authHeader);
        
        if (!result.success) {
          logger.warn(`认证失败: ${result.error}`);
          return res.status(401).json({
            error: result.error,
            code: 'AUTH_FAILED'
          });
        }

        // 将认证信息添加到请求对象
        (req as any).auth = {
          callerDid: result.caller_did,
          payload: result.payload
        };

        logger.debug(`认证成功: ${result.caller_did}`);
        next();

      } catch (error) {
        logger.error('认证中间件错误:', error);
        res.status(500).json({
          error: 'Authentication middleware error',
          code: 'AUTH_ERROR'
        });
      }
    };
  }
}

/**
 * 创建认证中间件的工厂函数
 */
export function createAuthMiddleware(verifier: AuthVerifier): AuthMiddleware {
  // 初始化豁免处理器
  AuthExemptHandler.initialize();
  
  return new AuthMiddleware(verifier);
}

/**
 * CORS中间件
 */
export function corsMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-DID-Caller, X-DID-Target');

    if (req.method === 'OPTIONS') {
      res.sendStatus(200);
    } else {
      next();
    }
  };
}

/**
 * 请求日志中间件
 */
export function requestLogMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();
    
    res.on('finish', () => {
      const duration = Date.now() - start;
      const callerDid = (req as any).auth?.callerDid || 'anonymous';
      
      logger.info(`${req.method} ${req.path} - ${res.statusCode} - ${duration}ms - ${callerDid}`);
    });
    
    next();
  };
}
