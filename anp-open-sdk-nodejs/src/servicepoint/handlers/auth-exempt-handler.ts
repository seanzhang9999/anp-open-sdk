/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { DomainManager } from '../../foundation/domain';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('AuthExemptHandler');

export interface AuthExemptResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export interface ExemptRule {
  pattern: string;
  method?: string;
  description?: string;
  enabled: boolean;
}

export interface ExemptCheckRequest {
  path: string;
  method: string;
  host: string;
  port: number;
}

/**
 * 认证豁免处理器
 * 对应Python版本的auth_exempt_handler.py
 * 处理无需认证的路径和请求
 */
export class AuthExemptHandler {
  
  // 默认的认证豁免规则
  private static readonly DEFAULT_EXEMPT_RULES: ExemptRule[] = [
    {
      pattern: '/health',
      method: 'GET',
      description: '健康检查端点',
      enabled: true
    },
    {
      pattern: '/status',
      method: 'GET',
      description: '状态检查端点',
      enabled: true
    },
    {
      pattern: '/wba/*/did.json',
      description: 'DID文档获取',
      enabled: true
    },
    {
      pattern: '/wba/*/ad.json',
      description: 'Agent描述文档获取',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface.yaml',
      description: 'API接口YAML文档',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface.json',
      description: 'API接口JSON文档',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface_nj.yaml',
      description: 'Node.js运行时API接口YAML文档',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface_nj.json',
      description: 'Node.js运行时API接口JSON文档',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface_py.yaml',
      description: 'Python运行时API接口YAML文档',
      enabled: true
    },
    {
      pattern: '/wba/*/api_interface_py.json',
      description: 'Python运行时API接口JSON文档',
      enabled: true
    },
    {
      pattern: '/wba/*/ad_nj.json',
      description: 'Node.js运行时Agent描述文档',
      enabled: true
    },
    {
      pattern: '/wba/*/ad_py.json',
      description: 'Python运行时Agent描述文档',
      enabled: true
    },
    {
      pattern: '/publisher/agents',
      method: 'GET',
      description: '公开的智能体列表',
      enabled: true
    },
    {
      pattern: '/publisher/stats',
      method: 'GET',
      description: '智能体统计信息',
      enabled: true
    },
    {
      pattern: '/favicon.ico',
      method: 'GET',
      description: '网站图标',
      enabled: true
    },
    {
      pattern: '/robots.txt',
      method: 'GET',
      description: '爬虫规则文件',
      enabled: true
    }
  ];

  /**
   * 检查请求是否豁免认证
   */
  public static async checkAuthExemption(request: ExemptCheckRequest): Promise<AuthExemptResponse> {
    try {
      // 验证域名访问权限
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(request.host, request.port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${request.host}:${request.port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 获取豁免规则
      const exemptRules = await this.getExemptRules(request.host, request.port);

      // 检查是否匹配豁免规则
      const matchedRule = this.findMatchingRule(request.path, request.method, exemptRules);

      if (matchedRule) {
        logger.debug(`请求匹配豁免规则: ${request.path} ${request.method} -> ${matchedRule.pattern}`);
        return {
          success: true,
          data: {
            exempt: true,
            rule: matchedRule,
            path: request.path,
            method: request.method
          }
        };
      }

      return {
        success: true,
        data: {
          exempt: false,
          path: request.path,
          method: request.method,
          message: '请求需要认证'
        }
      };

    } catch (error) {
      logger.error(`认证豁免检查失败: ${error}`);
      return { success: false, error: `认证豁免检查失败: ${error}` };
    }
  }

  /**
   * 获取豁免规则列表
   */
  private static async getExemptRules(host: string, port: number): Promise<ExemptRule[]> {
    try {
      // TODO: 从配置文件或数据库加载自定义豁免规则
      // 目前返回默认规则
      return this.DEFAULT_EXEMPT_RULES.filter(rule => rule.enabled);
    } catch (error) {
      logger.warn(`获取豁免规则失败，使用默认规则: ${error}`);
      return this.DEFAULT_EXEMPT_RULES.filter(rule => rule.enabled);
    }
  }

  /**
   * 查找匹配的豁免规则
   */
  private static findMatchingRule(path: string, method: string, rules: ExemptRule[]): ExemptRule | null {
    for (const rule of rules) {
      // 检查HTTP方法匹配
      if (rule.method && rule.method.toLowerCase() !== method.toLowerCase()) {
        continue;
      }

      // 检查路径模式匹配
      if (this.matchPattern(path, rule.pattern)) {
        return rule;
      }
    }

    return null;
  }

  /**
   * 模式匹配函数
   * 支持通配符 * 和 ?
   */
  private static matchPattern(text: string, pattern: string): boolean {
    try {
      // 将通配符模式转换为正则表达式
      const regexPattern = pattern
        .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // 转义特殊字符
        .replace(/\\\*/g, '.*') // 将 \* 替换为 .*
        .replace(/\\\?/g, '.'); // 将 \? 替换为 .
      
      const regex = new RegExp(`^${regexPattern}$`, 'i'); // 不区分大小写
      return regex.test(text);
    } catch (error) {
      logger.warn(`模式匹配失败: pattern=${pattern}, text=${text}, error=${error}`);
      return false;
    }
  }

  /**
   * 添加自定义豁免规则
   */
  public static async addExemptRule(
    rule: ExemptRule,
    host: string,
    port: number
  ): Promise<AuthExemptResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      // TODO: 实现规则持久化存储
      // 目前只是验证规则格式
      if (!rule.pattern || rule.pattern.trim() === '') {
        return { success: false, error: '规则模式不能为空' };
      }

      logger.info(`添加豁免规则: ${rule.pattern} ${rule.method || 'ALL'}`);

      return {
        success: true,
        data: {
          message: '豁免规则添加成功',
          rule
        }
      };

    } catch (error) {
      logger.error(`添加豁免规则失败: ${error}`);
      return { success: false, error: `添加豁免规则失败: ${error}` };
    }
  }

  /**
   * 移除豁免规则
   */
  public static async removeExemptRule(
    pattern: string,
    method: string | undefined,
    host: string,
    port: number
  ): Promise<AuthExemptResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      // TODO: 实现规则移除逻辑
      logger.info(`移除豁免规则: ${pattern} ${method || 'ALL'}`);

      return {
        success: true,
        data: {
          message: '豁免规则移除成功',
          pattern,
          method
        }
      };

    } catch (error) {
      logger.error(`移除豁免规则失败: ${error}`);
      return { success: false, error: `移除豁免规则失败: ${error}` };
    }
  }

  /**
   * 获取所有豁免规则
   */
  public static async getAllExemptRules(host: string, port: number): Promise<AuthExemptResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      const rules = await this.getExemptRules(host, port);

      return {
        success: true,
        data: {
          rules,
          count: rules.length,
          domain: `${host}:${port}`
        }
      };

    } catch (error) {
      logger.error(`获取豁免规则失败: ${error}`);
      return { success: false, error: `获取豁免规则失败: ${error}` };
    }
  }

  /**
   * 测试路径是否匹配豁免规则
   */
  public static async testExemptRule(
    testPath: string,
    testMethod: string,
    host: string,
    port: number
  ): Promise<AuthExemptResponse> {
    try {
      const request: ExemptCheckRequest = {
        path: testPath,
        method: testMethod,
        host,
        port
      };

      const result = await this.checkAuthExemption(request);

      return {
        success: true,
        data: {
          testPath,
          testMethod,
          result: result.data,
          message: result.data?.exempt ? '路径匹配豁免规则' : '路径需要认证'
        }
      };

    } catch (error) {
      logger.error(`测试豁免规则失败: ${error}`);
      return { success: false, error: `测试豁免规则失败: ${error}` };
    }
  }

  /**
   * 批量检查多个路径的豁免状态
   */
  public static async batchCheckExemption(
    requests: ExemptCheckRequest[]
  ): Promise<AuthExemptResponse> {
    try {
      const results: any[] = [];

      for (const request of requests) {
        const result = await this.checkAuthExemption(request);
        results.push({
          path: request.path,
          method: request.method,
          exempt: result.success ? result.data?.exempt : false,
          error: result.error
        });
      }

      const exemptCount = results.filter(r => r.exempt).length;

      return {
        success: true,
        data: {
          results,
          total: results.length,
          exemptCount,
          authRequiredCount: results.length - exemptCount
        }
      };

    } catch (error) {
      logger.error(`批量检查豁免状态失败: ${error}`);
      return { success: false, error: `批量检查豁免状态失败: ${error}` };
    }
  }

  /**
   * 验证豁免规则格式
   */
  public static validateExemptRule(rule: ExemptRule): { valid: boolean; error?: string } {
    try {
      // 检查必需字段
      if (!rule.pattern || rule.pattern.trim() === '') {
        return { valid: false, error: '规则模式不能为空' };
      }

      // 检查模式是否是有效的正则表达式模式
      try {
        const regexPattern = rule.pattern
          .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
          .replace(/\\\*/g, '.*')
          .replace(/\\\?/g, '.');
        new RegExp(`^${regexPattern}$`);
      } catch (error) {
        return { valid: false, error: `无效的模式格式: ${error}` };
      }

      // 检查HTTP方法
      if (rule.method) {
        const validMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'];
        if (!validMethods.includes(rule.method.toUpperCase())) {
          return { valid: false, error: `无效的HTTP方法: ${rule.method}` };
        }
      }

      return { valid: true };

    } catch (error) {
      return { valid: false, error: `规则验证失败: ${error}` };
    }
  }
}