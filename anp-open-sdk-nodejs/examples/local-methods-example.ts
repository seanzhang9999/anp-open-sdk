/**
 * Copyright 2024 ANP Open SDK Authors
 * 
 * Node.js版本的local_method使用示例
 * 完全对标Python的实现
 */

import 'reflect-metadata';
import {
  localMethod,
  registerLocalMethodsToAgent,
  LocalMethodsCaller,
  LocalMethodsDocGenerator
} from '../src/runtime/local-service';
import { agentClass } from '../src/runtime/decorators';
import { loadGlobalConfig } from '../src/foundation/config';
import { getLogger } from '../src/foundation/utils';

const logger = getLogger('LocalMethodsExample');

/**
 * 计算器Agent - 演示local_method的使用
 */
@agentClass({
  name: "CalculatorAgent",
  did: "did:wba:localhost%3A3000:wba:user:calc_001"
})
class CalculatorAgent {
  private precision: number = 2;
  private history: string[] = [];

  @localMethod("计算两数之和", ["math", "basic", "arithmetic"])
  add(a: number, b: number): number {
    const result = Number((a + b).toFixed(this.precision));
    this.history.push(`add(${a}, ${b}) = ${result}`);
    logger.info(`✅ 执行加法: ${a} + ${b} = ${result}`);
    return result;
  }

  @localMethod("计算两数之积", ["math", "basic", "arithmetic"]) 
  multiply(a: number, b: number): number {
    const result = Number((a * b).toFixed(this.precision));
    this.history.push(`multiply(${a}, ${b}) = ${result}`);
    logger.info(`✅ 执行乘法: ${a} * ${b} = ${result}`);
    return result;
  }

  @localMethod("计算两数之差", ["math", "basic"])
  subtract(a: number, b: number): number {
    const result = Number((a - b).toFixed(this.precision));
    this.history.push(`subtract(${a}, ${b}) = ${result}`);
    logger.info(`✅ 执行减法: ${a} - ${b} = ${result}`);
    return result;
  }

  @localMethod("获取计算历史记录", ["history", "query"])
  getHistory(): string[] {
    logger.info(`📋 返回计算历史，共 ${this.history.length} 条记录`);
    return [...this.history];
  }

  @localMethod("设置计算精度", ["config", "utility"])
  setPrecision(precision: number): void {
    const oldPrecision = this.precision;
    this.precision = precision;
    this.history.push(`setPrecision(${precision})`);
    logger.info(`🔧 精度设置从 ${oldPrecision} 更改为 ${precision}`);
  }

  @localMethod("清空计算历史", ["utility", "reset"])
  clearHistory(): number {
    const count = this.history.length;
    this.history = [];
    logger.info(`🧹 已清空 ${count} 条历史记录`);
    return count;
  }

  @localMethod("异步获取汇率", ["async", "api", "finance"])
  async fetchExchangeRate(fromCurrency: string, toCurrency: string): Promise<number> {
    // 模拟异步API调用
    await new Promise(resolve => setTimeout(resolve, 100));
    const rate = Math.random() * 10 + 1;
    this.history.push(`fetchExchangeRate(${fromCurrency}, ${toCurrency}) = ${rate}`);
    logger.info(`💱 获取汇率: ${fromCurrency} -> ${toCurrency} = ${rate}`);
    return Number(rate.toFixed(4));
  }

  @localMethod("批量计算", ["batch", "utility"])
  batchCalculate(operations: Array<{op: string, a: number, b: number}>): Array<{input: any, result: number}> {
    const results: Array<{input: any, result: number}> = [];
    
    operations.forEach(({op, a, b}) => {
      let result: number;
      switch(op) {
        case 'add':
          result = this.add(a, b);
          break;
        case 'multiply':
          result = this.multiply(a, b);
          break;
        case 'subtract':
          result = this.subtract(a, b);
          break;
        default:
          result = 0;
      }
      results.push({ input: {op, a, b}, result });
    });
    
    logger.info(`📊 批量计算完成，处理了 ${operations.length} 个操作`);
    return results;
  }
}

/**
 * 字符串处理Agent - 演示多Agent场景
 */
@agentClass({
  name: "StringAgent", 
  did: "did:wba:localhost%3A3000:wba:user:string_001"
})
class StringAgent {
  private processedCount: number = 0;

  @localMethod("反转字符串", ["string", "utility"])
  reverse(str: string): string {
    this.processedCount++;
    const result = str.split('').reverse().join('');
    logger.info(`🔄 字符串反转: "${str}" -> "${result}"`);
    return result;
  }

  @localMethod("转换为大写", ["string", "transform"])
  toUpperCase(str: string): string {
    this.processedCount++;
    const result = str.toUpperCase();
    logger.info(`🔠 转换大写: "${str}" -> "${result}"`);
    return result;
  }

  @localMethod("计算字符串长度", ["string", "analysis"])
  getLength(str: string): number {
    this.processedCount++;
    logger.info(`📏 字符串长度: "${str}" = ${str.length}`);
    return str.length;
  }

  @localMethod("获取处理统计", ["stats", "query"])
  getStats(): {processedCount: number, timestamp: string} {
    return {
      processedCount: this.processedCount,
      timestamp: new Date().toISOString()
    };
  }

  @localMethod("异步字符串验证", ["async", "validation"])
  async validateString(str: string, minLength: number = 1): Promise<{valid: boolean, message: string}> {
    // 模拟异步验证
    await new Promise(resolve => setTimeout(resolve, 50));
    
    this.processedCount++;
    const valid = str.length >= minLength;
    const message = valid ? "字符串验证通过" : `字符串长度不足，最少需要 ${minLength} 个字符`;
    
    logger.info(`✅ 字符串验证: "${str}" -> ${valid ? 'PASS' : 'FAIL'}`);
    return { valid, message };
  }
}

/**
 * 主要演示函数
 */
async function main() {
  try {
    // 加载配置
    await loadGlobalConfig();
    
    logger.info("🚀 开始 Local Method 系统演示");
    
    // 1. 创建Agent实例
    logger.info("\n📌 步骤1: 创建Agent实例");
    const calcAgent = new CalculatorAgent();
    const stringAgent = new StringAgent();
    
    // 2. 注册本地方法
    logger.info("\n📌 步骤2: 注册本地方法");
    const calcRegistered = registerLocalMethodsToAgent((calcAgent as any).agent, CalculatorAgent);
    const stringRegistered = registerLocalMethodsToAgent((stringAgent as any).agent, StringAgent);
    
    logger.info(`✅ CalculatorAgent 注册了 ${calcRegistered} 个本地方法`);
    logger.info(`✅ StringAgent 注册了 ${stringRegistered} 个本地方法`);
    
    // 3. 创建调用器
    logger.info("\n📌 步骤3: 创建调用器");
    const caller = new LocalMethodsCaller();
    
    // 4. 直接调用方法
    logger.info("\n📌 步骤4: 直接调用方法");
    const sum = await caller.callMethodByKey("CalculatorAgent::add", 10.555, 20.333);
    logger.info(`🔢 直接调用结果: ${sum}`);
    
    const product = await caller.callMethodByKey("CalculatorAgent::multiply", 3, 4);
    logger.info(`🔢 直接调用结果: ${product}`);
    
    // 5. 通过搜索调用
    logger.info("\n📌 步骤5: 通过搜索调用");
    const reverseResult = await caller.callMethodBySearch("反转", "Hello World");
    logger.info(`🔍 搜索调用结果: ${reverseResult}`);
    
    const upperResult = await caller.callMethodBySearch("大写", "hello node.js");
    logger.info(`🔍 搜索调用结果: ${upperResult}`);
    
    // 6. 异步方法调用
    logger.info("\n📌 步骤6: 异步方法调用");
    const exchangeRate = await caller.callMethodByKey("CalculatorAgent::fetchExchangeRate", "USD", "CNY");
    logger.info(`💱 异步调用结果: ${exchangeRate}`);
    
    const validation = await caller.callMethodByKey("StringAgent::validateString", "测试字符串", 5);
    logger.info(`✅ 异步验证结果:`, validation);
    
    // 7. 批量调用
    logger.info("\n📌 步骤7: 批量调用");
    const batchOps = [
      {op: 'add', a: 1, b: 2},
      {op: 'multiply', a: 3, b: 4},
      {op: 'subtract', a: 10, b: 3}
    ];
    const batchResults = await caller.callMethodByKey("CalculatorAgent::batchCalculate", batchOps);
    logger.info(`📊 批量调用结果:`, batchResults);
    
    // 8. 并发调用
    logger.info("\n📌 步骤8: 并发调用");
    const concurrentCalls = [
      { methodKey: "CalculatorAgent::add", args: [100, 200] },
      { methodKey: "StringAgent::reverse", args: ["concurrent"] },
      { methodKey: "StringAgent::getLength", args: ["测试并发"] },
      { methodKey: "CalculatorAgent::multiply", args: [5, 6] }
    ];
    
    const concurrentResults = await caller.callMethodsConcurrently(concurrentCalls);
    logger.info(`⚡ 并发调用结果:`);
    concurrentResults.forEach(result => {
      logger.info(`  - ${result.methodKey}: ${result.success ? result.result : result.error}`);
    });
    
    // 9. 查询历史和统计
    logger.info("\n📌 步骤9: 查询历史和统计");
    const history = await caller.callMethodByKey("CalculatorAgent::getHistory");
    logger.info(`📋 计算历史 (${history.length} 条):`);
    history.forEach((entry: string, index: number) => {
      logger.info(`  ${index + 1}. ${entry}`);
    });
    
    const stringStats = await caller.callMethodByKey("StringAgent::getStats");
    logger.info(`📊 字符串处理统计:`, stringStats);
    
    // 10. 搜索和文档功能
    logger.info("\n📌 步骤10: 搜索和文档功能");
    const docGen = new LocalMethodsDocGenerator();
    
    const mathMethods = docGen.searchMethods({ keyword: "math" });
    logger.info(`🔍 数学相关方法 (${mathMethods.length} 个):`);
    mathMethods.forEach(method => {
      logger.info(`  - ${method.methodName}: ${method.description}`);
    });
    
    const asyncMethods = docGen.searchMethods({ tags: ["async"] });
    logger.info(`⚡ 异步方法 (${asyncMethods.length} 个):`);
    asyncMethods.forEach(method => {
      logger.info(`  - ${method.methodName}: ${method.description}`);
    });
    
    // 11. 生成文档
    logger.info("\n📌 步骤11: 生成文档");
    const docPath = "./local_methods_doc.json";
    LocalMethodsDocGenerator.generateMethodsDoc(docPath);
    
    const markdownPath = "./local_methods_doc.md";
    docGen.generateMarkdownDoc(markdownPath);
    
    // 12. 统计信息
    logger.info("\n📌 步骤12: 系统统计");
    const stats = caller.getStats();
    logger.info(`📊 系统统计:`);
    logger.info(`  - 总方法数: ${stats.totalMethods}`);
    logger.info(`  - 可用Agent: ${stats.availableAgents.join(', ')}`);
    logger.info(`  - 可用标签: ${stats.availableTags.join(', ')}`);
    logger.info(`  - 每个Agent的方法数:`, stats.methodsByAgent);
    
    logger.info("\n🎉 Local Method 系统演示完成！");
    
  } catch (error) {
    logger.error("❌ 演示过程中出现错误:", error);
  }
}

// 运行演示
main().catch(error => {
  logger.error("❌ 主函数执行失败:", error);
  process.exit(1);
});