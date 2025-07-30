/**
 * Copyright 2024 ANP Open SDK Authors
 * 
 * 本地方法调用器
 * 对标Python的local_methods_caller.py
 */

import { LOCAL_METHODS_REGISTRY, LocalMethodInfo } from './local-methods-decorators';
import { LocalMethodsDocGenerator, MethodSearchResult } from './local-methods-doc';
import { AgentManager } from '../core/agent-manager';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('LocalMethodsCaller');

/**
 * 本地方法调用器
 */
export class LocalMethodsCaller {
  private docGenerator: LocalMethodsDocGenerator;

  constructor() {
    this.docGenerator = new LocalMethodsDocGenerator();
  }

  /**
   * 通过搜索关键词找到方法并调用
   * 
   * @param searchKeyword 搜索关键词
   * @param args 方法参数
   * @returns 调用结果
   */
  async callMethodBySearch(searchKeyword: string, ...args: any[]): Promise<any> {
    // 搜索方法
    const results = this.docGenerator.searchMethods({ keyword: searchKeyword });

    if (!results.length) {
      throw new Error(`未找到包含关键词 '${searchKeyword}' 的方法`);
    }

    if (results.length > 1) {
      const methodList = results.map((r: MethodSearchResult) => `${r.agentName}.${r.methodName}`);
      throw new Error(`找到多个匹配的方法: ${methodList.join(', ')}，请使用更具体的关键词`);
    }

    // 调用找到的方法
    const methodInfo = results[0];
    return await this.callMethodByKey(methodInfo.methodKey, ...args);
  }

  /**
   * 通过方法键调用方法
   * 
   * @param methodKey 方法键 (格式: module::method_name)
   * @param args 方法参数
   * @returns 调用结果
   */
  async callMethodByKey(methodKey: string, ...args: any[]): Promise<any> {
    // 获取方法信息
    const methodInfo = this.docGenerator.getMethodInfo(methodKey);
    if (!methodInfo) {
      // 提供更详细的错误信息
      const availableKeys = Array.from(LOCAL_METHODS_REGISTRY.keys());
      const errorMessage = [
        `未找到方法: ${methodKey}`,
        `可用的方法键:`,
        ...availableKeys.slice(0, 10).map(key => `  - ${key}`),
        ...(availableKeys.length > 10 ? [`  ... 还有 ${availableKeys.length - 10} 个`] : [])
      ].join('\n');
      
      throw new Error(errorMessage);
    }

    // 获取目标agent
    const targetAgent = AgentManager.getAgent(methodInfo.agentDid!, methodInfo.agentName!);
    if (!targetAgent) {
      throw new Error(`未找到agent: ${methodInfo.agentDid}`);
    }

    // 获取方法
    const methodName = methodInfo.name;
    const targetAgentAny = targetAgent as any;
    if (!targetAgentAny[methodName] || typeof targetAgentAny[methodName] !== 'function') {
      throw new Error(`Agent ${methodInfo.agentName} 没有方法 ${methodName}`);
    }

    const method = targetAgentAny[methodName];

    // 调用方法
    logger.info(`🚀 调用方法: ${methodInfo.agentName}.${methodName}`);
    
    try {
      if (methodInfo.isAsync) {
        return await method(...args);
      } else {
        return method(...args);
      }
    } catch (error) {
      logger.error(`❌ 方法调用失败: ${methodKey}`, error);
      throw error;
    }
  }

  /**
   * 批量调用多个方法
   * 
   * @param calls 调用配置数组
   * @returns 调用结果数组
   */
  async callMultipleMethods(calls: Array<{
    methodKey: string;
    args: any[];
  }>): Promise<Array<{
    methodKey: string;
    success: boolean;
    result?: any;
    error?: string;
  }>> {
    const results: Array<{
      methodKey: string;
      success: boolean;
      result?: any;
      error?: string;
    }> = [];

    for (const call of calls) {
      try {
        const result = await this.callMethodByKey(call.methodKey, ...call.args);
        results.push({
          methodKey: call.methodKey,
          success: true,
          result
        });
      } catch (error) {
        results.push({
          methodKey: call.methodKey,
          success: false,
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    return results;
  }

  /**
   * 并发调用多个方法
   * 
   * @param calls 调用配置数组
   * @returns 调用结果数组
   */
  async callMethodsConcurrently(calls: Array<{
    methodKey: string;
    args: any[];
  }>): Promise<Array<{
    methodKey: string;
    success: boolean;
    result?: any;
    error?: string;
  }>> {
    const promises = calls.map(async (call) => {
      try {
        const result = await this.callMethodByKey(call.methodKey, ...call.args);
        return {
          methodKey: call.methodKey,
          success: true,
          result
        };
      } catch (error) {
        return {
          methodKey: call.methodKey,
          success: false,
          error: error instanceof Error ? error.message : String(error)
        };
      }
    });

    return Promise.all(promises);
  }

  /**
   * 列出所有可用的本地方法
   * 
   * @returns 方法信息数组
   */
  listAllMethods(): LocalMethodInfo[] {
    return Array.from(LOCAL_METHODS_REGISTRY.values());
  }

  /**
   * 按Agent列出方法
   * 
   * @param agentName Agent名称
   * @returns 方法信息数组
   */
  listMethodsByAgent(agentName: string): LocalMethodInfo[] {
    return Array.from(LOCAL_METHODS_REGISTRY.values())
      .filter(method => method.agentName === agentName);
  }

  /**
   * 按标签列出方法
   * 
   * @param tag 标签
   * @returns 方法信息数组
   */
  listMethodsByTag(tag: string): LocalMethodInfo[] {
    return Array.from(LOCAL_METHODS_REGISTRY.values())
      .filter(method => method.tags.includes(tag));
  }

  /**
   * 获取方法详细信息
   * 
   * @param methodKey 方法键
   * @returns 方法信息
   */
  getMethodInfo(methodKey: string): LocalMethodInfo | null {
    return LOCAL_METHODS_REGISTRY.get(methodKey) || null;
  }

  /**
   * 检查方法是否存在
   * 
   * @param methodKey 方法键
   * @returns 是否存在
   */
  hasMethod(methodKey: string): boolean {
    return LOCAL_METHODS_REGISTRY.has(methodKey);
  }

  /**
   * 获取调用统计信息
   */
  getStats(): {
    totalMethods: number;
    availableAgents: string[];
    availableTags: string[];
    methodsByAgent: Record<string, number>;
  } {
    const methods = Array.from(LOCAL_METHODS_REGISTRY.values());
    const agentCounts: Record<string, number> = {};
    const tagsSet = new Set<string>();

    methods.forEach(method => {
      const agentName = method.agentName || 'unknown';
      agentCounts[agentName] = (agentCounts[agentName] || 0) + 1;
      method.tags.forEach(tag => tagsSet.add(tag));
    });

    return {
      totalMethods: methods.length,
      availableAgents: Object.keys(agentCounts),
      availableTags: Array.from(tagsSet),
      methodsByAgent: agentCounts
    };
  }
}

// 导出单例实例
export const localMethodsCaller = new LocalMethodsCaller();