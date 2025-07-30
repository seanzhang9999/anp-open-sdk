/**
 * Copyright 2024 ANP Open SDK Authors
 * 
 * Local Methods 系统测试
 */

import 'reflect-metadata';
import {
  localMethod,
  registerLocalMethodsToAgent,
  LocalMethodsCaller,
  LocalMethodsDocGenerator,
  clearLocalMethodsRegistry,
  LOCAL_METHODS_REGISTRY
} from '../../src/runtime/local-service';

// 测试Agent类
class TestAgent {
  public name = 'TestAgent';
  public anpUserId = 'test-did';
  private counter = 0;

  @localMethod("简单加法", ["math", "test"])
  add(a: number, b: number): number {
    this.counter++;
    return a + b;
  }

  @localMethod("字符串处理", ["string", "test"])
  processString(str: string): string {
    this.counter++;
    return str.toUpperCase();
  }

  @localMethod("异步方法", ["async", "test"])
  async asyncMethod(delay: number): Promise<string> {
    this.counter++;
    await new Promise(resolve => setTimeout(resolve, delay));
    return `Delayed for ${delay}ms`;
  }

  @localMethod("获取计数器", ["utility"])
  getCounter(): number {
    return this.counter;
  }

  // 非装饰器方法，不应该被注册
  normalMethod(): string {
    return "normal";
  }
}

class SecondTestAgent {
  public name = 'SecondTestAgent';
  public anpUserId = 'second-test-did';

  @localMethod("乘法运算", ["math", "second"])
  multiply(a: number, b: number): number {
    return a * b;
  }

  @localMethod("字符串反转", ["string", "second"])
  reverseString(str: string): string {
    return str.split('').reverse().join('');
  }
}

describe('Local Methods System', () => {
  let testAgent: TestAgent;
  let secondAgent: SecondTestAgent;
  let caller: LocalMethodsCaller;
  let docGenerator: LocalMethodsDocGenerator;

  beforeEach(() => {
    // 清空注册表
    clearLocalMethodsRegistry();
    
    // 创建测试实例
    testAgent = new TestAgent();
    secondAgent = new SecondTestAgent();
    caller = new LocalMethodsCaller();
    docGenerator = new LocalMethodsDocGenerator();
  });

  afterEach(() => {
    // 清理注册表
    clearLocalMethodsRegistry();
  });

  describe('装饰器功能', () => {
    test('应该正确标记本地方法', () => {
      expect((testAgent.add as any)._isLocalMethod).toBe(true);
      expect((testAgent.processString as any)._isLocalMethod).toBe(true);
      expect((testAgent.asyncMethod as any)._isLocalMethod).toBe(true);
      expect((testAgent.normalMethod as any)._isLocalMethod).toBeUndefined();
    });

    test('应该保存方法元数据', () => {
      const addMethodInfo = (testAgent.add as any)._methodInfo;
      expect(addMethodInfo).toBeDefined();
      expect(addMethodInfo.name).toBe('add');
      expect(addMethodInfo.description).toBe('简单加法');
      expect(addMethodInfo.tags).toEqual(['math', 'test']);
      expect(addMethodInfo.isAsync).toBe(false);

      const asyncMethodInfo = (testAgent.asyncMethod as any)._methodInfo;
      expect(asyncMethodInfo.isAsync).toBe(true);
    });
  });

  describe('注册功能', () => {
    test('应该能够注册Agent的本地方法', () => {
      const registeredCount = registerLocalMethodsToAgent(testAgent, TestAgent);
      
      expect(registeredCount).toBe(4); // add, processString, asyncMethod, getCounter
      expect(LOCAL_METHODS_REGISTRY.size).toBe(4);
      
      // 检查注册表中的条目
      const addMethod = LOCAL_METHODS_REGISTRY.get('TestAgent::add');
      expect(addMethod).toBeDefined();
      expect(addMethod?.agentDid).toBe('test-did');
      expect(addMethod?.agentName).toBe('TestAgent');
    });

    test('应该能够注册多个Agent', () => {
      registerLocalMethodsToAgent(testAgent, TestAgent);
      registerLocalMethodsToAgent(secondAgent, SecondTestAgent);
      
      expect(LOCAL_METHODS_REGISTRY.size).toBe(6); // 4 + 2
      
      const multiplyMethod = LOCAL_METHODS_REGISTRY.get('SecondTestAgent::multiply');
      expect(multiplyMethod).toBeDefined();
      expect(multiplyMethod?.agentDid).toBe('second-test-did');
    });

    test('应该处理方法冲突', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      registerLocalMethodsToAgent(testAgent, TestAgent);
      registerLocalMethodsToAgent(testAgent, TestAgent); // 重复注册
      
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('调用功能', () => {
    beforeEach(() => {
      registerLocalMethodsToAgent(testAgent, TestAgent);
      registerLocalMethodsToAgent(secondAgent, SecondTestAgent);
    });

    test('应该能够通过方法键调用方法', async () => {
      const result = await caller.callMethodByKey('TestAgent::add', 5, 3);
      expect(result).toBe(8);
      
      const counter = await caller.callMethodByKey('TestAgent::getCounter');
      expect(counter).toBe(1);
    });

    test('应该能够调用异步方法', async () => {
      const result = await caller.callMethodByKey('TestAgent::asyncMethod', 10);
      expect(result).toBe('Delayed for 10ms');
    });

    test('应该能够通过搜索调用方法', async () => {
      const result = await caller.callMethodBySearch('加法', 10, 20);
      expect(result).toBe(30);
    });

    test('搜索到多个方法时应该抛出错误', async () => {
      await expect(caller.callMethodBySearch('string')).rejects.toThrow('找到多个匹配的方法');
    });

    test('未找到方法时应该抛出错误', async () => {
      await expect(caller.callMethodByKey('NonExistent::method')).rejects.toThrow('未找到方法');
    });

    test('应该能够批量调用方法', async () => {
      const calls = [
        { methodKey: 'TestAgent::add', args: [1, 2] },
        { methodKey: 'SecondTestAgent::multiply', args: [3, 4] },
        { methodKey: 'TestAgent::processString', args: ['hello'] }
      ];

      const results = await caller.callMultipleMethods(calls);
      
      expect(results).toHaveLength(3);
      expect(results[0].success).toBe(true);
      expect(results[0].result).toBe(3);
      expect(results[1].result).toBe(12);
      expect(results[2].result).toBe('HELLO');
    });

    test('应该能够并发调用方法', async () => {
      const calls = [
        { methodKey: 'TestAgent::add', args: [1, 1] },
        { methodKey: 'SecondTestAgent::multiply', args: [2, 2] }
      ];

      const results = await caller.callMethodsConcurrently(calls);
      
      expect(results).toHaveLength(2);
      expect(results.every(r => r.success)).toBe(true);
    });
  });

  describe('搜索和文档功能', () => {
    beforeEach(() => {
      registerLocalMethodsToAgent(testAgent, TestAgent);
      registerLocalMethodsToAgent(secondAgent, SecondTestAgent);
    });

    test('应该能够按关键词搜索方法', () => {
      const results = docGenerator.searchMethods({ keyword: 'math' });
      expect(results).toHaveLength(2); // add, multiply
      
      const mathMethods = results.map(r => r.methodName);
      expect(mathMethods).toContain('add');
      expect(mathMethods).toContain('multiply');
    });

    test('应该能够按Agent名称搜索方法', () => {
      const results = docGenerator.searchMethods({ agentName: 'TestAgent' });
      expect(results).toHaveLength(4);
    });

    test('应该能够按标签搜索方法', () => {
      const results = docGenerator.searchMethods({ tags: ['string'] });
      expect(results).toHaveLength(2); // processString, reverseString
    });

    test('应该能够精确搜索', () => {
      const results = docGenerator.searchMethods({ keyword: 'math', exact: true });
      expect(results).toHaveLength(0); // 没有方法名或描述精确等于"math"
    });

    test('应该能够获取按Agent分组的方法', () => {
      const methodsByAgent = docGenerator.getMethodsByAgent();
      
      expect(methodsByAgent['TestAgent']).toHaveLength(4);
      expect(methodsByAgent['SecondTestAgent']).toHaveLength(2);
    });

    test('应该能够获取按标签分组的方法', () => {
      const methodsByTag = docGenerator.getMethodsByTag();
      
      expect(methodsByTag['math']).toHaveLength(2);
      expect(methodsByTag['string']).toHaveLength(2);
      expect(methodsByTag['test']).toHaveLength(3);
    });

    test('应该能够生成统计摘要', () => {
      const summary = docGenerator.generateSummary();
      
      expect(summary.totalMethods).toBe(6);
      expect(summary.totalAgents).toBe(2);
      expect(summary.asyncMethods).toBe(1);
      expect(summary.syncMethods).toBe(5);
      expect(summary.methodsPerAgent['TestAgent']).toBe(4);
      expect(summary.methodsPerAgent['SecondTestAgent']).toBe(2);
    });
  });

  describe('调用器统计功能', () => {
    beforeEach(() => {
      registerLocalMethodsToAgent(testAgent, TestAgent);
      registerLocalMethodsToAgent(secondAgent, SecondTestAgent);
    });

    test('应该能够获取系统统计信息', () => {
      const stats = caller.getStats();
      
      expect(stats.totalMethods).toBe(6);
      expect(stats.availableAgents).toContain('TestAgent');
      expect(stats.availableAgents).toContain('SecondTestAgent');
      expect(stats.availableTags).toContain('math');
      expect(stats.availableTags).toContain('string');
    });

    test('应该能够按Agent列出方法', () => {
      const testAgentMethods = caller.listMethodsByAgent('TestAgent');
      expect(testAgentMethods).toHaveLength(4);
    });

    test('应该能够按标签列出方法', () => {
      const mathMethods = caller.listMethodsByTag('math');
      expect(mathMethods).toHaveLength(2);
    });

    test('应该能够检查方法是否存在', () => {
      expect(caller.hasMethod('TestAgent::add')).toBe(true);
      expect(caller.hasMethod('NonExistent::method')).toBe(false);
    });

    test('应该能够获取方法详细信息', () => {
      const methodInfo = caller.getMethodInfo('TestAgent::add');
      
      expect(methodInfo).toBeDefined();
      expect(methodInfo?.name).toBe('add');
      expect(methodInfo?.description).toBe('简单加法');
      expect(methodInfo?.tags).toEqual(['math', 'test']);
    });
  });

  describe('错误处理', () => {
    test('装饰器应该只能应用于方法', () => {
      expect(() => {
        class InvalidClass {
          @localMethod("测试")
          property: string = "test";
        }
      }).toThrow();
    });

    test('调用不存在的Agent方法应该抛出错误', async () => {
      // 注册方法但不提供对应的Agent实例
      registerLocalMethodsToAgent(testAgent, TestAgent);
      
      // 模拟AgentManager.getAgent返回null
      const originalGetAgent = require('../../src/runtime/core/agent-manager').AgentManager.getAgent;
      require('../../src/runtime/core/agent-manager').AgentManager.getAgent = jest.fn().mockReturnValue(null);
      
      await expect(caller.callMethodByKey('TestAgent::add', 1, 2)).rejects.toThrow('未找到agent');
      
      // 恢复原方法
      require('../../src/runtime/core/agent-manager').AgentManager.getAgent = originalGetAgent;
    });
  });

  describe('文档生成', () => {
    beforeEach(() => {
      registerLocalMethodsToAgent(testAgent, TestAgent);
    });

    test('应该能够生成JSON文档', () => {
      const doc = LocalMethodsDocGenerator.generateMethodsDoc();
      
      expect(doc.total_methods).toBe(4);
      expect(doc.methods).toBeDefined();
      expect(doc.generated_by).toBe('ANP Node.js SDK');
    });

    test('应该能够生成Markdown文档', () => {
      const markdown = docGenerator.generateMarkdownDoc();
      
      expect(markdown).toContain('# ANP 本地方法文档');
      expect(markdown).toContain('## 📊 统计摘要');
      expect(markdown).toContain('## 🤖 按Agent分组');
      expect(markdown).toContain('TestAgent');
    });
  });
});