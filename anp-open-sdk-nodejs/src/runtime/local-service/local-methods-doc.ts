/**
 * Copyright 2024 ANP Open SDK Authors
 * 
 * 本地方法文档生成器
 * 对标Python的local_methods_doc.py
 */

import * as fs from 'fs';
import * as path from 'path';
import { LOCAL_METHODS_REGISTRY, LocalMethodInfo } from './local-methods-decorators';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('LocalMethodsDoc');

/**
 * 搜索结果接口
 */
export interface MethodSearchResult {
  methodKey: string;
  agentDid: string;
  agentName: string;
  methodName: string;
  description: string;
  signature: string;
  tags: string[];
}

/**
 * 搜索选项接口
 */
export interface SearchOptions {
  keyword?: string;
  agentName?: string;
  tags?: string[];
  exact?: boolean;
}

/**
 * 本地方法文档生成器
 */
export class LocalMethodsDocGenerator {
  
  /**
   * 生成所有本地方法的文档
   * 
   * @param outputPath 输出文件路径
   * @returns 文档对象
   */
  static generateMethodsDoc(outputPath: string = "local_methods_doc.json"): any {
    const doc = {
      generated_at: new Date().toISOString(),
      generated_by: "ANP Node.js SDK",
      current_directory: process.cwd(),
      total_methods: LOCAL_METHODS_REGISTRY.size,
      methods: Object.fromEntries(LOCAL_METHODS_REGISTRY)
    };

    // 确保输出目录存在
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // 保存到文件
    fs.writeFileSync(outputPath, JSON.stringify(doc, null, 2), 'utf-8');

    logger.info(`📚 已生成本地方法文档: ${outputPath}`);
    return doc;
  }

  /**
   * 搜索本地方法
   * 
   * @param options 搜索选项
   * @returns 搜索结果数组
   */
  searchMethods(options: SearchOptions = {}): MethodSearchResult[] {
    const results: MethodSearchResult[] = [];
    const { keyword = "", agentName = "", tags = [], exact = false } = options;

    for (const [methodKey, methodInfo] of LOCAL_METHODS_REGISTRY) {
      let matches = true;

      // 关键词匹配
      if (keyword) {
        const keywordLower = keyword.toLowerCase();
        const nameMatch = methodInfo.name.toLowerCase().includes(keywordLower);
        const descMatch = methodInfo.description.toLowerCase().includes(keywordLower);
        const tagMatch = methodInfo.tags.some(tag => tag.toLowerCase().includes(keywordLower));
        
        if (exact) {
          matches = matches && (
            methodInfo.name.toLowerCase() === keywordLower ||
            methodInfo.description.toLowerCase() === keywordLower ||
            methodInfo.tags.some(tag => tag.toLowerCase() === keywordLower)
          );
        } else {
          matches = matches && (nameMatch || descMatch || tagMatch);
        }
      }

      // Agent名称匹配
      if (agentName && methodInfo.agentName) {
        if (exact) {
          matches = matches && methodInfo.agentName.toLowerCase() === agentName.toLowerCase();
        } else {
          matches = matches && methodInfo.agentName.toLowerCase().includes(agentName.toLowerCase());
        }
      }

      // 标签匹配
      if (tags.length > 0) {
        if (exact) {
          matches = matches && tags.every(tag => methodInfo.tags.includes(tag));
        } else {
          matches = matches && tags.some(tag => 
            methodInfo.tags.some(methodTag => methodTag.toLowerCase().includes(tag.toLowerCase()))
          );
        }
      }

      if (matches) {
        results.push({
          methodKey,
          agentDid: methodInfo.agentDid || 'unknown',
          agentName: methodInfo.agentName || 'unknown',
          methodName: methodInfo.name,
          description: methodInfo.description,
          signature: methodInfo.signature,
          tags: methodInfo.tags
        });
      }
    }

    return results;
  }

  /**
   * 获取指定方法的详细信息
   * 
   * @param methodKey 方法键
   * @returns 方法信息
   */
  getMethodInfo(methodKey: string): LocalMethodInfo | null {
    return LOCAL_METHODS_REGISTRY.get(methodKey) || null;
  }

  /**
   * 按Agent分组的方法列表
   * 
   * @returns 按Agent分组的方法字典
   */
  getMethodsByAgent(): Record<string, MethodSearchResult[]> {
    const result: Record<string, MethodSearchResult[]> = {};

    for (const [methodKey, methodInfo] of LOCAL_METHODS_REGISTRY) {
      const agentName = methodInfo.agentName || 'unknown';
      
      if (!result[agentName]) {
        result[agentName] = [];
      }

      result[agentName].push({
        methodKey,
        agentDid: methodInfo.agentDid || 'unknown',
        agentName: methodInfo.agentName || 'unknown',
        methodName: methodInfo.name,
        description: methodInfo.description,
        signature: methodInfo.signature,
        tags: methodInfo.tags
      });
    }

    return result;
  }

  /**
   * 按标签分组的方法列表
   * 
   * @returns 按标签分组的方法字典
   */
  getMethodsByTag(): Record<string, MethodSearchResult[]> {
    const result: Record<string, MethodSearchResult[]> = {};

    for (const [methodKey, methodInfo] of LOCAL_METHODS_REGISTRY) {
      methodInfo.tags.forEach(tag => {
        if (!result[tag]) {
          result[tag] = [];
        }

        result[tag].push({
          methodKey,
          agentDid: methodInfo.agentDid || 'unknown',
          agentName: methodInfo.agentName || 'unknown',
          methodName: methodInfo.name,
          description: methodInfo.description,
          signature: methodInfo.signature,
          tags: methodInfo.tags
        });
      });
    }

    return result;
  }

  /**
   * 生成方法摘要统计
   * 
   * @returns 统计信息
   */
  generateSummary(): {
    totalMethods: number;
    totalAgents: number;
    totalTags: number;
    methodsPerAgent: Record<string, number>;
    methodsPerTag: Record<string, number>;
    asyncMethods: number;
    syncMethods: number;
  } {
    const agentCounts: Record<string, number> = {};
    const tagCounts: Record<string, number> = {};
    const agents = new Set<string>();
    const tags = new Set<string>();
    let asyncCount = 0;
    let syncCount = 0;

    for (const methodInfo of LOCAL_METHODS_REGISTRY.values()) {
      // 统计Agent
      const agentName = methodInfo.agentName || 'unknown';
      agents.add(agentName);
      agentCounts[agentName] = (agentCounts[agentName] || 0) + 1;

      // 统计标签
      methodInfo.tags.forEach(tag => {
        tags.add(tag);
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });

      // 统计异步/同步
      if (methodInfo.isAsync) {
        asyncCount++;
      } else {
        syncCount++;
      }
    }

    return {
      totalMethods: LOCAL_METHODS_REGISTRY.size,
      totalAgents: agents.size,
      totalTags: tags.size,
      methodsPerAgent: agentCounts,
      methodsPerTag: tagCounts,
      asyncMethods: asyncCount,
      syncMethods: syncCount
    };
  }

  /**
   * 生成Markdown文档
   * 
   * @param outputPath 输出文件路径
   * @returns Markdown内容
   */
  generateMarkdownDoc(outputPath?: string): string {
    const summary = this.generateSummary();
    const methodsByAgent = this.getMethodsByAgent();
    
    let markdown = `# ANP 本地方法文档\n\n`;
    markdown += `生成时间: ${new Date().toISOString()}\n\n`;
    
    // 摘要信息
    markdown += `## 📊 统计摘要\n\n`;
    markdown += `- **总方法数**: ${summary.totalMethods}\n`;
    markdown += `- **总Agent数**: ${summary.totalAgents}\n`;
    markdown += `- **总标签数**: ${summary.totalTags}\n`;
    markdown += `- **异步方法**: ${summary.asyncMethods}\n`;
    markdown += `- **同步方法**: ${summary.syncMethods}\n\n`;

    // 按Agent列出方法
    markdown += `## 🤖 按Agent分组\n\n`;
    
    for (const [agentName, methods] of Object.entries(methodsByAgent)) {
      markdown += `### ${agentName}\n\n`;
      
      methods.forEach(method => {
        markdown += `#### \`${method.methodName}\`\n\n`;
        markdown += `- **描述**: ${method.description || '无'}\n`;
        markdown += `- **标签**: ${method.tags.join(', ') || '无'}\n`;
        markdown += `- **方法键**: \`${method.methodKey}\`\n`;
        markdown += `- **Agent DID**: \`${method.agentDid}\`\n\n`;
        markdown += `\`\`\`typescript\n${method.signature}\n\`\`\`\n\n`;
      });
    }

    // 保存到文件（如果指定了路径）
    if (outputPath) {
      const outputDir = path.dirname(outputPath);
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      fs.writeFileSync(outputPath, markdown, 'utf-8');
      logger.info(`📝 已生成Markdown文档: ${outputPath}`);
    }

    return markdown;
  }

  /**
   * 实例方法：搜索方法（兼容性）
   */
  searchMethods_instance(options: SearchOptions = {}): MethodSearchResult[] {
    return this.searchMethods(options);
  }

  /**
   * 实例方法：获取方法信息（兼容性）
   */
  getMethodInfo_instance(methodKey: string): LocalMethodInfo | null {
    return this.getMethodInfo(methodKey);
  }
}