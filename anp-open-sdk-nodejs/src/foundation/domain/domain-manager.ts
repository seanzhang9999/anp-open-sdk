/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as path from 'path';
import * as fs from 'fs';
import { URL } from 'url';
import {
  DomainConfig,
  DomainPaths,
  SupportedDomains,
  DomainStats,
  DomainStatus,
  HostPortPair,
  DomainValidationResult,
  DomainNotSupportedError,
  DEFAULT_CONFIG
} from '../types';

/**
 * 域名管理器 - 处理多域名路由和数据路径分配
 * 
 * 提供基于Host头的多域名路由和数据路径管理功能
 */
export class DomainManager {
  private _supportedDomains: SupportedDomains | null = null;
  private _domainConfigCache: Map<string, DomainConfig> = new Map();

  constructor() {
    // 初始化时不加载配置，延迟到首次使用
  }

  /**
   * 获取支持的域名列表
   */
  get supportedDomains(): SupportedDomains {
    if (this._supportedDomains === null) {
      // 在实际项目中，这里应该从配置文件加载
      // 目前使用默认配置
      this._supportedDomains = {
        'localhost': DEFAULT_CONFIG.DEFAULT_PORT,
        'user.localhost': DEFAULT_CONFIG.DEFAULT_PORT,
        'service.localhost': DEFAULT_CONFIG.DEFAULT_PORT,
        '127.0.0.1': DEFAULT_CONFIG.DEFAULT_PORT,
        '::1': DEFAULT_CONFIG.DEFAULT_PORT
      };
    }
    return this._supportedDomains;
  }

  /**
   * 解析Host头，提取域名和端口
   * 
   * @param hostHeader HTTP Host头的值，如 "user.localhost:9527"
   * @returns 域名和端口的元组
   */
  parseHostHeader(hostHeader: string): HostPortPair {
    if (!hostHeader) {
      return this.getDefaultHostPort();
    }

    try {
      // 处理IPv6地址的情况
      if (hostHeader.startsWith('[')) {
        // IPv6格式: [::1]:9527
        if (hostHeader.includes(']:')) {
          const lastColonIndex = hostHeader.lastIndexOf(']:');
          const host = hostHeader.substring(1, lastColonIndex);
          const portStr = hostHeader.substring(lastColonIndex + 2);
          const port = parseInt(portStr, 10);
          return { host, port: isNaN(port) ? 80 : port };
        } else {
          // 只有IPv6地址，没有端口
          const host = hostHeader.substring(1, hostHeader.length - 1);
          return { host, port: 80 };
        }
      } else {
        // IPv4或域名格式
        if (hostHeader.includes(':')) {
          const lastColonIndex = hostHeader.lastIndexOf(':');
          const host = hostHeader.substring(0, lastColonIndex);
          const portStr = hostHeader.substring(lastColonIndex + 1);
          const port = parseInt(portStr, 10);
          
          // 检查是否是有效端口号
          if (isNaN(port)) {
            // 端口无效，返回host部分和默认端口
            return { host, port: 80 };
          }
          
          return { host, port };
        } else {
          return { host: hostHeader, port: 80 };
        }
      }
    } catch (error) {
      console.warn(`解析Host头失败: ${hostHeader}, 错误: ${error}`);
      return this.getDefaultHostPort();
    }
  }

  /**
   * 获取默认的主机和端口
   */
  private getDefaultHostPort(): HostPortPair {
    return {
      host: DEFAULT_CONFIG.DEFAULT_HOST,
      port: DEFAULT_CONFIG.DEFAULT_PORT
    };
  }

  /**
   * 检查域名是否被支持
   * 
   * @param domain 域名
   * @param port 端口（可选）
   * @returns 是否支持该域名
   */
  isSupportedDomain(domain: string, port?: number): boolean {
    try {
      const supported = this.supportedDomains;
      
      if (domain in supported) {
        if (port === undefined) {
          return true;
        }
        return supported[domain] === port;
      }
      
      // 默认支持localhost相关域名
      return domain === 'localhost' || 
             domain === '127.0.0.1' || 
             domain === '::1' || 
             domain.endsWith('.localhost');
    } catch (error) {
      console.error(`检查域名支持时出错: ${error}`);
      return domain === 'localhost' || 
             domain === '127.0.0.1' || 
             domain === '::1' || 
             domain.endsWith('.localhost');
    }
  }

  /**
   * 获取指定域名的数据路径
   *
   * @param domain 域名
   * @param port 端口
   * @param useAbsolutePath 是否使用绝对路径（默认为true）
   * @returns 数据路径，如 "data_user/user_localhost_9527/"
   */
  public getDataPathForDomain(domain: string, port: number, useAbsolutePath: boolean = true): string {
    // 标准化域名（移除特殊字符）
    const safeDomain = this.getSafeDomainString(domain);
    
    // 构建相对路径
    const relativePath = `${DEFAULT_CONFIG.DATA_USER_DIR}/${safeDomain}_${port}`;
    
    if (!useAbsolutePath) {
      return relativePath;
    }
    
    // 🔧 修复路径构建逻辑：
    // 检查当前工作目录，如果在子目录中运行，需要向上查找正确的data_user目录
    const currentDir = process.cwd();
    
    // 检查是否在anp-open-sdk-nodejs子目录中运行
    let basePath: string;
    if (currentDir.endsWith('anp-open-sdk-nodejs')) {
      // 在子目录中运行，需要向上一级查找data_user
      basePath = path.resolve(currentDir, '..', relativePath);
    } else {
      // 在根目录中运行，直接使用当前目录
      basePath = path.resolve(currentDir, relativePath);
    }
    
    return basePath;
  }
  
  /**
   * 获取安全的域名字符串（移除特殊字符）
   *
   * @param domain 域名
   * @returns 安全的域名字符串
   * @private
   */
  private getSafeDomainString(domain: string): string {
    return domain.replace(/\./g, '_').replace(/:/g, '_');
  }

  /**
   * 获取域名的配置信息
   * 
   * @param domain 域名
   * @returns 域名配置
   */
  getDomainConfig(domain: string): DomainConfig {
    const cacheKey = domain;
    if (this._domainConfigCache.has(cacheKey)) {
      return this._domainConfigCache.get(cacheKey)!;
    }

    const supported = this.supportedDomains;
    const port = supported[domain] || 80;
    
    const config: DomainConfig = {
      domain,
      supported: domain in supported,
      port,
      data_path: this.getDataPathForDomain(domain, port)
    };

    this._domainConfigCache.set(cacheKey, config);
    return config;
  }

  /**
   * 获取指定域名的所有数据路径
   *
   * @param domain 域名
   * @param port 端口
   * @param useAbsolutePath 是否使用绝对路径（默认为true）
   * @returns 包含各种数据路径的对象
   */
  getAllDataPaths(domain: string, port: number, useAbsolutePath: boolean = true): DomainPaths {
    const basePath = this.getDataPathForDomain(domain, port, useAbsolutePath);
    
    return {
      base_path: basePath,
      user_did_path: path.join(basePath, 'anp_users'),
      user_hosted_path: path.join(basePath, 'anp_users_hosted'),
      agents_cfg_path: path.join(basePath, 'agents_config'),
      hosted_did_queue: path.join(basePath, 'hosted_did_queue'),
      hosted_did_results: path.join(basePath, 'hosted_did_results')
    };
  }

  /**
   * 确保域名对应的目录结构存在
   * 
   * @param domain 域名
   * @param port 端口
   * @returns 是否成功创建目录
   */
  ensureDomainDirectories(domain: string, port: number): boolean {
    try {
      const paths = this.getAllDataPaths(domain, port);
      
      // 创建所有必要的目录
      for (const [pathName, pathValue] of Object.entries(paths)) {
        if (pathName !== 'base_path' && pathValue) {
          fs.mkdirSync(pathValue, { recursive: true });
          console.debug(`确保目录存在: ${pathValue}`);
        }
      }
      
      return true;
    } catch (error) {
      console.error(`创建域名目录失败: ${error}`);
      return false;
    }
  }

  /**
   * 从HTTP请求中提取主机和端口信息
   * 
   * @param request HTTP请求对象
   * @returns 主机和端口
   */
  getHostPortFromRequest(request: any): HostPortPair {
    try {
      // 尝试从Host头获取
      let hostHeader: string | undefined;
      
      if (request.headers && request.headers.host) {
        hostHeader = request.headers.host;
      } else if (request.headers && request.headers.Host) {
        hostHeader = request.headers.Host;
      } else if (request.META && request.META.HTTP_HOST) {
        // Django风格
        hostHeader = request.META.HTTP_HOST;
      }
      
      if (hostHeader) {
        return this.parseHostHeader(hostHeader);
      }
      
      // 回退到请求URL
      if (request.url) {
        try {
          const parsed = new URL(request.url);
          const host = parsed.hostname || 'localhost';
          const port = parsed.port ? parseInt(parsed.port, 10) : 80;
          return { host, port };
        } catch {
          // URL解析失败，继续到默认值
        }
      }
      
      // 最后的回退
      return this.getDefaultHostPort();
    } catch (error) {
      console.warn(`从请求中提取主机端口失败: ${error}`);
      return this.getDefaultHostPort();
    }
  }

  /**
   * 验证域名访问权限
   * 
   * @param domain 域名
   * @param port 端口
   * @returns 验证结果
   */
  validateDomainAccess(domain: string, port: number): DomainValidationResult {
    if (!this.isSupportedDomain(domain, port)) {
      return {
        valid: false,
        error: `不支持的域名: ${domain}:${port}`
      };
    }

    // 在实际项目中，这里可以添加更多的安全检查
    // 例如检查不安全的域名模式等

    return { valid: true };
  }

  /**
   * 简单的模式匹配（支持*通配符）
   * 
   * @param text 要匹配的文本
   * @param pattern 模式字符串
   * @returns 是否匹配
   */
  private matchPattern(text: string, pattern: string): boolean {
    // 将通配符模式转换为正则表达式
    const regexPattern = pattern
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // 转义特殊字符
      .replace(/\\\*/g, '.*'); // 将 \* 替换为 .*
    
    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(text);
  }

  /**
   * 获取域名使用统计信息
   * 
   * @returns 统计信息
   */
  getDomainStats(): DomainStats {
    try {
      const supported = this.supportedDomains;
      const domains = Object.keys(supported);
      
      const stats: DomainStats = {
        supported_domains: domains.length,
        domains,
        cache_size: this._domainConfigCache.size,
        domain_status: {}
      };
      
      // 检查各域名的数据目录状态
      for (const [domain, port] of Object.entries(supported)) {
        const paths = this.getAllDataPaths(domain, port);
        const domainKey = `${domain}:${port}`;
        
        stats.domain_status[domainKey] = {
          base_exists: fs.existsSync(paths.base_path),
          users_exists: fs.existsSync(paths.user_did_path),
          agents_exists: fs.existsSync(paths.agents_cfg_path)
        };
      }
      
      return stats;
    } catch (error) {
      console.error(`获取域名统计失败: ${error}`);
      return {
        supported_domains: 0,
        domains: [],
        cache_size: this._domainConfigCache.size,
        domain_status: {}
      };
    }
  }

  /**
   * 清除配置缓存
   */
  clearCache(): void {
    this._domainConfigCache.clear();
    this._supportedDomains = null;
  }

  /**
   * 添加支持的域名
   * 
   * @param domain 域名
   * @param port 端口
   */
  addSupportedDomain(domain: string, port: number): void {
    const supported = this.supportedDomains;
    supported[domain] = port;
    
    // 清除相关缓存
    this._domainConfigCache.delete(domain);
  }

  /**
   * 移除支持的域名
   * 
   * @param domain 域名
   */
  removeSupportedDomain(domain: string): void {
    const supported = this.supportedDomains;
    delete supported[domain];
    
    // 清除相关缓存
    this._domainConfigCache.delete(domain);
  }
}

// 全局域名管理器实例
let _domainManager: DomainManager | null = null;

/**
 * 获取全局域名管理器实例
 * 
 * @returns 域名管理器实例
 */
export function getDomainManager(): DomainManager {
  if (_domainManager === null) {
    _domainManager = new DomainManager();
  }
  return _domainManager;
}

/**
 * 重置全局域名管理器实例（主要用于测试）
 */
export function resetDomainManager(): void {
  _domainManager = null;
}