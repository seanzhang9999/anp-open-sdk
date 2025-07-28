/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs';
import * as path from 'path';
import { DomainManager, getDomainManager, resetDomainManager } from '../../src/foundation/domain';
import { DEFAULT_CONFIG } from '../../src/foundation/types';

describe('DomainManager', () => {
  let domainManager: DomainManager;

  beforeEach(() => {
    resetDomainManager();
    domainManager = new DomainManager();
  });

  afterEach(() => {
    resetDomainManager();
  });

  describe('构造函数和初始化', () => {
    test('应该正确创建DomainManager实例', () => {
      expect(domainManager).toBeInstanceOf(DomainManager);
    });

    test('应该有默认的支持域名列表', () => {
      const supported = domainManager.supportedDomains;
      expect(supported).toBeDefined();
      expect(typeof supported).toBe('object');
      expect(supported['localhost']).toBe(DEFAULT_CONFIG.DEFAULT_PORT);
    });
  });

  describe('parseHostHeader', () => {
    test('应该正确解析标准的host:port格式', () => {
      const result = domainManager.parseHostHeader('localhost:9527');
      expect(result).toEqual({ host: 'localhost', port: 9527 });
    });

    test('应该正确解析只有域名的格式', () => {
      const result = domainManager.parseHostHeader('localhost');
      expect(result).toEqual({ host: 'localhost', port: 80 });
    });

    test('应该正确解析IPv6地址格式', () => {
      const result = domainManager.parseHostHeader('[::1]:9527');
      expect(result).toEqual({ host: '::1', port: 9527 });
    });

    test('应该正确解析只有IPv6地址的格式', () => {
      const result = domainManager.parseHostHeader('[::1]');
      expect(result).toEqual({ host: '::1', port: 80 });
    });

    test('应该处理空的host头', () => {
      const result = domainManager.parseHostHeader('');
      expect(result).toEqual({
        host: DEFAULT_CONFIG.DEFAULT_HOST,
        port: DEFAULT_CONFIG.DEFAULT_PORT
      });
    });

    test('应该处理无效的端口号', () => {
      const result = domainManager.parseHostHeader('localhost:invalid');
      expect(result).toEqual({ host: 'localhost', port: 80 });
    });

    test('应该处理复杂的域名', () => {
      const result = domainManager.parseHostHeader('user.service.localhost:8080');
      expect(result).toEqual({ host: 'user.service.localhost', port: 8080 });
    });
  });

  describe('isSupportedDomain', () => {
    test('应该识别支持的域名', () => {
      expect(domainManager.isSupportedDomain('localhost')).toBe(true);
      expect(domainManager.isSupportedDomain('127.0.0.1')).toBe(true);
      expect(domainManager.isSupportedDomain('::1')).toBe(true);
    });

    test('应该识别支持的域名和端口组合', () => {
      expect(domainManager.isSupportedDomain('localhost', DEFAULT_CONFIG.DEFAULT_PORT)).toBe(true);
    });

    test('应该识别不支持的域名', () => {
      expect(domainManager.isSupportedDomain('example.com')).toBe(false);
      expect(domainManager.isSupportedDomain('malicious.site')).toBe(false);
    });

    test('应该支持.localhost子域名', () => {
      expect(domainManager.isSupportedDomain('test.localhost')).toBe(true);
      expect(domainManager.isSupportedDomain('api.service.localhost')).toBe(true);
    });

    test('应该检查端口匹配', () => {
      expect(domainManager.isSupportedDomain('localhost', 9999)).toBe(false);
    });
  });

  describe('getDataPathForDomain', () => {
    test('应该生成正确的数据路径', () => {
      const path = domainManager.getDataPathForDomain('localhost', 9527, false);
      expect(path).toBe('data_user/localhost_9527');
    });

    test('应该处理带点的域名', () => {
      const path = domainManager.getDataPathForDomain('user.localhost', 9527, false);
      expect(path).toBe('data_user/user_localhost_9527');
    });

    test('应该处理IPv6地址', () => {
      const path = domainManager.getDataPathForDomain('::1', 9527, false);
      expect(path).toBe('data_user/__1_9527');
    });

    test('应该处理复杂域名', () => {
      const path = domainManager.getDataPathForDomain('api.service.localhost', 8080, false);
      expect(path).toBe('data_user/api_service_localhost_8080');
    });
    
    test('应该根据参数返回绝对路径', () => {
      const absolutePath = domainManager.getDataPathForDomain('localhost', 9527, true);
      expect(absolutePath).toBe(path.resolve(process.cwd(), 'data_user/localhost_9527'));
    });
  });

  describe('getDomainConfig', () => {
    test('应该返回支持域名的配置', () => {
      // 修改 getDataPathForDomain 的调用，确保返回相对路径
      const originalGetDataPathForDomain = domainManager.getDataPathForDomain;
      domainManager.getDataPathForDomain = function(domain, port) {
        return originalGetDataPathForDomain.call(this, domain, port, false);
      };
      
      const config = domainManager.getDomainConfig('localhost');
      expect(config).toEqual({
        domain: 'localhost',
        supported: true,
        port: DEFAULT_CONFIG.DEFAULT_PORT,
        data_path: `data_user/localhost_${DEFAULT_CONFIG.DEFAULT_PORT}`
      });
      
      // 恢复原始方法
      domainManager.getDataPathForDomain = originalGetDataPathForDomain;
    });

    test('应该返回不支持域名的配置', () => {
      // 修改 getDataPathForDomain 的调用，确保返回相对路径
      const originalGetDataPathForDomain = domainManager.getDataPathForDomain;
      domainManager.getDataPathForDomain = function(domain, port) {
        return originalGetDataPathForDomain.call(this, domain, port, false);
      };
      
      const config = domainManager.getDomainConfig('example.com');
      expect(config).toEqual({
        domain: 'example.com',
        supported: false,
        port: 80,
        data_path: 'data_user/example_com_80'
      });
      
      // 恢复原始方法
      domainManager.getDataPathForDomain = originalGetDataPathForDomain;
    });

    test('应该缓存配置结果', () => {
      const config1 = domainManager.getDomainConfig('localhost');
      const config2 = domainManager.getDomainConfig('localhost');
      expect(config1).toBe(config2); // 应该是同一个对象引用
    });
  });

  describe('getAllDataPaths', () => {
    test('应该返回所有数据路径', () => {
      const paths = domainManager.getAllDataPaths('localhost', 9527, false);
      
      expect(paths).toHaveProperty('base_path');
      expect(paths).toHaveProperty('user_did_path');
      expect(paths).toHaveProperty('user_hosted_path');
      expect(paths).toHaveProperty('agents_cfg_path');
      expect(paths).toHaveProperty('hosted_did_queue');
      expect(paths).toHaveProperty('hosted_did_results');
      
      expect(paths.base_path).toBe('data_user/localhost_9527');
      expect(paths.user_did_path).toBe(path.join('data_user/localhost_9527', 'anp_users'));
      expect(paths.user_hosted_path).toBe(path.join('data_user/localhost_9527', 'anp_users_hosted'));
      expect(paths.agents_cfg_path).toBe(path.join('data_user/localhost_9527', 'agents_config'));
    });

    test('应该为不同域名生成不同路径', () => {
      const paths1 = domainManager.getAllDataPaths('localhost', 9527, false);
      const paths2 = domainManager.getAllDataPaths('user.localhost', 9527, false);
      
      expect(paths1.base_path).not.toBe(paths2.base_path);
      expect(paths1.user_did_path).not.toBe(paths2.user_did_path);
    });
    
    test('应该根据参数返回绝对路径', () => {
      const paths = domainManager.getAllDataPaths('localhost', 9527, true);
      const expectedBasePath = path.resolve(process.cwd(), 'data_user/localhost_9527');
      
      expect(paths.base_path).toBe(expectedBasePath);
      expect(paths.user_did_path).toBe(path.join(expectedBasePath, 'anp_users'));
    });
  });

  describe('ensureDomainDirectories', () => {
    const testDomain = 'test.localhost';
    const testPort = 9999;
    
    afterEach(() => {
      // 清理测试目录
      const paths = domainManager.getAllDataPaths(testDomain, testPort, true);
      try {
        if (fs.existsSync(paths.base_path)) {
          fs.rmSync(paths.base_path, { recursive: true, force: true });
        }
      } catch (error) {
        // 忽略清理错误
      }
    });

    test('应该成功创建目录结构', () => {
      const result = domainManager.ensureDomainDirectories(testDomain, testPort);
      expect(result).toBe(true);
      
      const paths = domainManager.getAllDataPaths(testDomain, testPort);
      expect(fs.existsSync(paths.user_did_path)).toBe(true);
      expect(fs.existsSync(paths.user_hosted_path)).toBe(true);
      expect(fs.existsSync(paths.agents_cfg_path)).toBe(true);
    });

    test('应该处理已存在的目录', () => {
      // 第一次创建
      domainManager.ensureDomainDirectories(testDomain, testPort);
      
      // 第二次创建应该也成功
      const result = domainManager.ensureDomainDirectories(testDomain, testPort);
      expect(result).toBe(true);
    });
  });

  describe('getHostPortFromRequest', () => {
    test('应该从request.headers.host提取信息', () => {
      const request = {
        headers: { host: 'localhost:9527' }
      };
      
      const result = domainManager.getHostPortFromRequest(request);
      expect(result).toEqual({ host: 'localhost', port: 9527 });
    });

    test('应该从request.headers.Host提取信息', () => {
      const request = {
        headers: { Host: 'user.localhost:8080' }
      };
      
      const result = domainManager.getHostPortFromRequest(request);
      expect(result).toEqual({ host: 'user.localhost', port: 8080 });
    });

    test('应该从request.url提取信息', () => {
      const request = {
        url: 'http://api.localhost:3000/test'
      };
      
      const result = domainManager.getHostPortFromRequest(request);
      expect(result).toEqual({ host: 'api.localhost', port: 3000 });
    });

    test('应该处理Django风格的META', () => {
      const request = {
        META: { HTTP_HOST: 'service.localhost:7777' }
      };
      
      const result = domainManager.getHostPortFromRequest(request);
      expect(result).toEqual({ host: 'service.localhost', port: 7777 });
    });

    test('应该返回默认值当无法提取时', () => {
      const request = {};
      
      const result = domainManager.getHostPortFromRequest(request);
      expect(result).toEqual({
        host: DEFAULT_CONFIG.DEFAULT_HOST,
        port: DEFAULT_CONFIG.DEFAULT_PORT
      });
    });
  });

  describe('validateDomainAccess', () => {
    test('应该验证支持的域名', () => {
      const result = domainManager.validateDomainAccess('localhost', DEFAULT_CONFIG.DEFAULT_PORT);
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    test('应该拒绝不支持的域名', () => {
      const result = domainManager.validateDomainAccess('malicious.com', 80);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('不支持的域名');
    });

    test('应该拒绝端口不匹配的域名', () => {
      const result = domainManager.validateDomainAccess('localhost', 9999);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('不支持的域名');
    });
  });

  describe('getDomainStats', () => {
    test('应该返回域名统计信息', () => {
      const stats = domainManager.getDomainStats();
      
      expect(stats).toHaveProperty('supported_domains');
      expect(stats).toHaveProperty('domains');
      expect(stats).toHaveProperty('cache_size');
      expect(stats).toHaveProperty('domain_status');
      
      expect(typeof stats.supported_domains).toBe('number');
      expect(Array.isArray(stats.domains)).toBe(true);
      expect(typeof stats.cache_size).toBe('number');
      expect(typeof stats.domain_status).toBe('object');
    });

    test('应该包含默认支持的域名', () => {
      const stats = domainManager.getDomainStats();
      
      expect(stats.supported_domains).toBeGreaterThan(0);
      expect(stats.domains).toContain('localhost');
    });

    test('应该反映缓存大小变化', () => {
      const stats1 = domainManager.getDomainStats();
      const initialCacheSize = stats1.cache_size;
      
      // 触发缓存
      domainManager.getDomainConfig('test.domain');
      
      const stats2 = domainManager.getDomainStats();
      expect(stats2.cache_size).toBe(initialCacheSize + 1);
    });
  });

  describe('缓存管理', () => {
    test('clearCache应该清除所有缓存', () => {
      // 触发缓存
      domainManager.getDomainConfig('test.domain');
      const stats1 = domainManager.getDomainStats();
      expect(stats1.cache_size).toBeGreaterThan(0);
      
      // 清除缓存
      domainManager.clearCache();
      const stats2 = domainManager.getDomainStats();
      expect(stats2.cache_size).toBe(0);
    });
  });

  describe('域名管理', () => {
    test('addSupportedDomain应该添加新的支持域名', () => {
      const testDomain = 'new.test.com';
      const testPort = 8888;
      
      expect(domainManager.isSupportedDomain(testDomain, testPort)).toBe(false);
      
      domainManager.addSupportedDomain(testDomain, testPort);
      expect(domainManager.isSupportedDomain(testDomain, testPort)).toBe(true);
    });

    test('removeSupportedDomain应该移除支持的域名', () => {
      const testDomain = 'remove.test.com';
      const testPort = 7777;
      
      domainManager.addSupportedDomain(testDomain, testPort);
      expect(domainManager.isSupportedDomain(testDomain, testPort)).toBe(true);
      
      domainManager.removeSupportedDomain(testDomain);
      expect(domainManager.isSupportedDomain(testDomain, testPort)).toBe(false);
    });

    test('添加和移除域名应该清除相关缓存', () => {
      const testDomain = 'cache.test.com';
      const testPort = 6666;
      
      // 触发缓存
      domainManager.getDomainConfig(testDomain);
      let stats = domainManager.getDomainStats();
      const initialCacheSize = stats.cache_size;
      
      // 添加域名应该清除缓存
      domainManager.addSupportedDomain(testDomain, testPort);
      stats = domainManager.getDomainStats();
      expect(stats.cache_size).toBeLessThan(initialCacheSize);
    });
  });

  describe('全局实例管理', () => {
    test('getDomainManager应该返回单例实例', () => {
      const instance1 = getDomainManager();
      const instance2 = getDomainManager();
      expect(instance1).toBe(instance2);
    });

    test('resetDomainManager应该重置全局实例', () => {
      const instance1 = getDomainManager();
      resetDomainManager();
      const instance2 = getDomainManager();
      expect(instance1).not.toBe(instance2);
    });
  });

  describe('边界情况和错误处理', () => {
    test('应该处理特殊字符的域名', () => {
      const specialDomains = [
        'test-domain.localhost',
        'test_domain.localhost',
        'test123.localhost'
      ];
      
      specialDomains.forEach(domain => {
        const path = domainManager.getDataPathForDomain(domain, 9527, false);
        expect(path).toBeTruthy();
        expect(path).toMatch(/^data_user\/[a-zA-Z0-9_-]+_9527$/);
      });
    });

    test('应该处理极端端口号', () => {
      const extremePorts = [1, 65535, 0];
      
      extremePorts.forEach(port => {
        const result = domainManager.parseHostHeader(`localhost:${port}`);
        expect(result.port).toBe(port);
      });
    });

    test('应该处理空字符串和null值', () => {
      expect(() => domainManager.parseHostHeader('')).not.toThrow();
      expect(() => domainManager.isSupportedDomain('')).not.toThrow();
      expect(() => domainManager.getDataPathForDomain('', 80)).not.toThrow();
    });
  });
});