/**
 * Copyright 2024 ANP Open SDK Authors
 * 
 * Node.js版本的本地方法装饰器系统
 * 对标Python的local_methods_decorators.py
 */

import * as fs from 'fs';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('LocalMethodsDecorators');

// 方法信息接口
export interface LocalMethodInfo {
  name: string;
  description: string;
  tags: string[];
  signature: string;
  parameters: Record<string, {
    type: string;
    default?: any;
    required: boolean;
  }>;
  agentDid: string | null;
  agentName: string | null;
  module: string;
  isAsync: boolean;
}

// 全局注册表，存储所有本地方法信息
export const LOCAL_METHODS_REGISTRY: Map<string, LocalMethodInfo> = new Map();

/**
 * 本地方法装饰器
 * 
 * @param description 方法描述
 * @param tags 方法标签
 */
export function localMethod(description: string = "", tags: string[] = []) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor): void {
    const method = descriptor.value;
    
    if (!method || typeof method !== 'function') {
      throw new Error(`@localMethod can only be applied to methods`);
    }

    // 获取函数签名信息
    const signature = method.toString();
    
    // 解析参数信息
    const parameters: Record<string, any> = {};
    const paramNames = extractParameterNames(method);
    
    paramNames.forEach(paramName => {
      if (paramName !== 'this') {
        parameters[paramName] = {
          type: 'any', // TypeScript运行时无法获取精确类型
          default: undefined,
          required: true
        };
      }
    });

    // 存储方法信息
    const methodInfo: LocalMethodInfo = {
      name: propertyKey,
      description: description || method.__doc__ || "",
      tags: tags || [],
      signature: signature,
      parameters: parameters,
      agentDid: null,  // 稍后注册时填入
      agentName: null,
      module: target.constructor.name,
      isAsync: method.constructor.name === 'AsyncFunction'
    };

    // 标记函数并存储信息
    method._isLocalMethod = true;
    method._methodInfo = methodInfo;

    logger.debug(`🏷️ 标记本地方法: ${target.constructor.name}.${propertyKey}`);
  };
}

/**
 * 将标记的本地方法注册到agent，并更新全局注册表
 * 
 * @param agent Agent实例
 * @param moduleOrDict 模块或方法字典
 */
export function registerLocalMethodsToAgent(agent: any, moduleOrDict: any): number {
  let items: [string, any][];
  
  if (moduleOrDict && typeof moduleOrDict === 'object' && moduleOrDict.constructor === Object) {
    // 普通对象
    items = Object.entries(moduleOrDict);
  } else if (moduleOrDict && moduleOrDict.prototype) {
    // 类
    items = Object.getOwnPropertyNames(moduleOrDict.prototype)
      .filter(name => name !== 'constructor')
      .map(name => [name, moduleOrDict.prototype[name]]);
  } else if (moduleOrDict && typeof moduleOrDict === 'object') {
    // 实例对象
    items = Object.getOwnPropertyNames(Object.getPrototypeOf(moduleOrDict))
      .filter(name => name !== 'constructor')
      .map(name => [name, moduleOrDict[name]]);
  } else {
    throw new Error("moduleOrDict must be an object, class, or instance");
  }

  let registeredCount = 0;
  
  for (const [name, obj] of items) {
    if (typeof obj === 'function' && obj._isLocalMethod) {
      // 注册到agent - 绑定this到agent实例
      const boundMethod = obj.bind(agent);
      boundMethod._isLocalMethod = true;
      boundMethod._methodInfo = obj._methodInfo;
      
      // 如果agent没有这个方法，则添加
      if (!agent[name]) {
        agent[name] = boundMethod;
      }

      // 更新全局注册表
      const methodInfo = { ...obj._methodInfo };
      methodInfo.agentDid = agent.anpUserId || agent.anpUser?.id || 'unknown';
      methodInfo.agentName = agent.name || 'unknown';

      // 使用module作为唯一标识，避免共享DID冲突
      const methodKey = `${methodInfo.module}::${name}`;
      
      // 检测冲突
      if (LOCAL_METHODS_REGISTRY.has(methodKey)) {
        const existingInfo = LOCAL_METHODS_REGISTRY.get(methodKey)!;
        logger.warn(`⚠️  方法键冲突检测: ${methodKey}`);
        logger.warn(`   现有: ${existingInfo.agentName} (${existingInfo.agentDid})`);
        logger.warn(`   新的: ${agent.name} (${methodInfo.agentDid})`);
        logger.warn(`   🔧 覆盖现有方法`);
      }

      LOCAL_METHODS_REGISTRY.set(methodKey, methodInfo);

      registeredCount++;
      logger.info(`✅ 已注册本地方法: ${agent.name}.${name}`);
    }
  }

  logger.info(`📝 共注册了 ${registeredCount} 个本地方法到 ${agent.name || 'Agent'}`);
  return registeredCount;
}

/**
 * 提取函数参数名称
 * 
 * @param func 函数
 * @returns 参数名称数组
 */
function extractParameterNames(func: Function): string[] {
  const funcStr = func.toString();
  
  // 匹配函数参数
  const match = funcStr.match(/(?:function[^(]*\(([^)]*)\)|(?:^|\s)([^(]*)\s*=>|\(([^)]*)\)\s*=>)/);
  
  if (!match) return [];
  
  const params = (match[1] || match[2] || match[3] || '').trim();
  if (!params) return [];
  
  return params.split(',')
    .map(param => param.trim().split(/\s+/)[0].replace(/[=:].*/g, ''))
    .filter(param => param && param !== '');
}

/**
 * 获取所有已注册的本地方法
 */
export function getAllLocalMethods(): LocalMethodInfo[] {
  return Array.from(LOCAL_METHODS_REGISTRY.values());
}

/**
 * 清空全局注册表（主要用于测试）
 */
export function clearLocalMethodsRegistry(): void {
  LOCAL_METHODS_REGISTRY.clear();
  logger.debug('🧹 已清空本地方法注册表');
}

/**
 * 获取注册表统计信息
 */
export function getRegistryStats(): {
  totalMethods: number;
  byAgent: Record<string, number>;
  byModule: Record<string, number>;
  byTags: Record<string, number>;
} {
  const stats = {
    totalMethods: LOCAL_METHODS_REGISTRY.size,
    byAgent: {} as Record<string, number>,
    byModule: {} as Record<string, number>,
    byTags: {} as Record<string, number>
  };

  for (const methodInfo of LOCAL_METHODS_REGISTRY.values()) {
    // 按Agent统计
    const agentName = methodInfo.agentName || 'unknown';
    stats.byAgent[agentName] = (stats.byAgent[agentName] || 0) + 1;

    // 按模块统计
    const moduleName = methodInfo.module || 'unknown';
    stats.byModule[moduleName] = (stats.byModule[moduleName] || 0) + 1;

    // 按标签统计
    methodInfo.tags.forEach(tag => {
      stats.byTags[tag] = (stats.byTags[tag] || 0) + 1;
    });
  }

  return stats;
}