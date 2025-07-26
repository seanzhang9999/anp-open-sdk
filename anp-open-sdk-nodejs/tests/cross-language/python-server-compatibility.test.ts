/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import axios from 'axios';
import { AgentApiCaller } from '../../src/runtime/services/agent-api-caller';
import { LocalUserDataManager } from '../../src/foundation/user/local-user-data-manager';
import { getLogger } from '../../src/foundation/utils';
import { testReporter } from './test-reporter';

const logger = getLogger('PythonServerCompatibilityTest');

// 测试用户DID常量
const TEST_CALLER_DID = "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d";
const TEST_TARGET_DID = "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973";

// 测试数据
const testCases = [
  { a: 15, b: 25, expected: 40 },
  { a: 0, b: 0, expected: 0 },
  { a: -5, b: 10, expected: 5 },
  { a: 1.5, b: 2.5, expected: 4.0 }
];

/**
 * 便捷的API调用函数，模拟Python版本的agent_api_call_post
 */
export async function agentApiCallPost(options: {
  callerAgent: string;
  targetAgent: string;
  apiPath: string;
  params: any;
}): Promise<{
  success: boolean;
  data?: any;
  error?: string;
  statusCode?: number;
}> {
  try {
    // 加载调用者的私钥
    const userDataManager = LocalUserDataManager.getInstance();
    await userDataManager.initialize();
    const callerUserData = userDataManager.getUserData(options.callerAgent);
    
    if (!callerUserData) {
      return {
        success: false,
        error: `无法加载调用者用户数据: ${options.callerAgent}`
      };
    }

    // 获取私钥
    const privateKey = callerUserData.getDidPrivateKey();
    if (!privateKey) {
      return {
        success: false,
        error: `无法获取调用者私钥: ${options.callerAgent}`
      };
    }

    // 将KeyObject转换为PEM格式字符串
    const privateKeyPem = privateKey.export({ type: 'pkcs8', format: 'pem' }) as string;

    // 创建API调用器
    const apiCaller = new AgentApiCaller(privateKeyPem, options.callerAgent);
    
    // 构建正确的ANP协议URL格式
    // 格式: /agent/api/{target_agent_encoded}{api_path}?req_did={caller_did}&resp_did={target_did}
    const targetAgentEncoded = encodeURIComponent(options.targetAgent);
    const urlParams = new URLSearchParams({
      req_did: options.callerAgent,
      resp_did: options.targetAgent
    });
    
    const apiUrl = `/agent/api/${targetAgentEncoded}${options.apiPath}?${urlParams.toString()}`;
    
    // 调用API，使用POST方法并传递params作为请求体
    const result = await apiCaller.callAgentApi(
      options.targetAgent,
      apiUrl,
      { params: options.params },
      { method: 'POST' }
    );

    return result;
  } catch (error: any) {
    logger.error('agentApiCallPost失败:', error);
    return {
      success: false,
      error: error.message || 'API调用失败'
    };
  }
}

/**
 * 检查Python flow_anp_agent服务器是否运行
 */
async function checkPythonFlowServer(): Promise<boolean> {
  try {
    // 尝试连接flow_anp_agent服务器
    const response = await axios.get('http://localhost:9527/', {
      timeout: 5000,
      validateStatus: () => true // 接受所有状态码
    });
    // 200, 404, 401都表示服务器在运行
    return response.status === 200 || response.status === 404 || response.status === 401;
  } catch (error: any) {
    logger.debug('Python flow_anp_agent服务器连接检查失败:', error.message);
    return false;
  }
}

/**
 * 显示Python flow_anp_agent服务器启动指导
 */
function showPythonFlowServerGuide(): void {
  console.warn(`
⚠️  Python flow_anp_agent服务器未运行在localhost:9527

请先启动Python服务器：
PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py

跳过跨语言兼容性测试...
  `);
}

describe('Python Server Compatibility Tests', () => {
  let serverRunning = false;
  const apiCallResults: any[] = [];

  beforeAll(async () => {
    serverRunning = await checkPythonFlowServer();
    
    if (!serverRunning) {
      showPythonFlowServerGuide();
      return;
    }
    
    console.log('✅ Python flow_anp_agent服务器运行正常，开始跨语言兼容性测试');
    
    // 记录关键验证点
    testReporter.recordKeyValidations();
  });

  afterAll(() => {
    if (serverRunning) {
      // 生成并显示测试摘要报告
      const summaryReport = testReporter.generateSummaryReport();
      console.log(summaryReport);
      
      // 生成API调用详细报告
      if (apiCallResults.length > 0) {
        const apiReport = testReporter.generateApiCallReport(apiCallResults);
        console.log(apiReport);
      }
    }
  });

  describe('服务器连接测试', () => {
    test('should connect to Python lite server', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const isConnected = await checkPythonFlowServer();
      expect(isConnected).toBe(true);
    });

    test('should verify test user data exists', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const userDataManager = LocalUserDataManager.getInstance();
      await userDataManager.initialize();
      
      // 验证调用者用户数据
      const callerData = userDataManager.getUserData(TEST_CALLER_DID);
      expect(callerData).toBeDefined();
      expect(callerData?.getDidPrivateKey()).toBeDefined();
      
      // 验证目标用户数据
      const targetData = userDataManager.getUserData(TEST_TARGET_DID);
      expect(targetData).toBeDefined();
      expect(targetData?.getDidPrivateKey()).toBeDefined();
    });
  });

  describe('基础API调用测试', () => {
    test('should call Python server API successfully', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        testReporter.recordTest({
          testName: 'should call Python server API successfully',
          success: false,
          error: 'Python服务器未运行'
        });
        return;
      }

      const startTime = Date.now();
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 15, b: 25 }
      });
      const duration = Date.now() - startTime;
      
      // 记录API调用结果
      apiCallResults.push({
        testCase: 'Basic API Call (15+25)',
        ...result,
        duration
      });
      
      logger.info('API调用结果:', result);
      
      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      // 验证计算结果
      let testSuccess = false;
      if (result.success && result.data) {
        const actualResult = result.data.result !== undefined ? result.data.result : result.data;
        expect(actualResult).toBe(40);
        testSuccess = true;
      }

      // 记录测试结果
      testReporter.recordTest({
        testName: 'should call Python server API successfully',
        success: testSuccess,
        duration,
        details: result
      });
    });
    
    test('should handle multiple test cases', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      for (const testCase of testCases) {
        const result = await agentApiCallPost({
          callerAgent: TEST_CALLER_DID,
          targetAgent: TEST_TARGET_DID,
          apiPath: "/add",
          params: { a: testCase.a, b: testCase.b }
        });
        
        expect(result.success).toBe(true);
        
        if (result.success && result.data) {
          const actualResult = result.data.result !== undefined ? result.data.result : result.data;
          expect(actualResult).toBe(testCase.expected);
        }
      }
    });
  });

  describe('认证兼容性测试', () => {
    test('should authenticate with Python server using Node.js generated headers', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 测试Node.js生成的认证头能被Python服务器接受
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 1, b: 1 }
      });
      
      // 如果认证失败，result.success应该为false
      expect(result.success).toBe(true);
      
      if (result.success) {
        logger.info('✅ Node.js认证头与Python服务器兼容');
      }
    });
    
    test('should handle timestamp format compatibility', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 验证时间戳格式兼容性
      // Node.js: 2025-01-01T00:00:00.000Z
      // Python: 2025-01-01T00:00:00Z
      // 修复后的代码应该能处理两种格式
      
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 100, b: 200 }
      });
      
      expect(result.success).toBe(true);
      
      if (result.success) {
        logger.info('✅ 时间戳格式兼容性验证通过');
      }
    });

    test('should handle DID bidirectional authentication', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 测试DID双向认证的跨语言互操作
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 50, b: 75 }
      });
      
      expect(result.success).toBe(true);
      expect(result.statusCode).toBe(200);
      
      if (result.success) {
        logger.info('✅ DID双向认证跨语言互操作验证通过');
      }
    });
  });

  describe('数据格式兼容性测试', () => {
    test('should handle JSON serialization/deserialization compatibility', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 测试复杂数据结构
      const complexParams = {
        a: 10.5,
        b: 20.7,
        metadata: {
          operation: "addition",
          timestamp: new Date().toISOString(),
          precision: "double"
        }
      };
      
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: complexParams
      });
      
      expect(result.success).toBe(true);
      
      if (result.success && result.data) {
        const expectedResult = complexParams.a + complexParams.b;
        const actualResult = result.data.result !== undefined ? result.data.result : result.data;
        expect(Math.abs(actualResult - expectedResult)).toBeLessThan(0.001);
      }
    });

    test('should handle different data types', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const dataTypeTests = [
        { a: 0, b: 0, type: 'zero' },
        { a: -10, b: 10, type: 'negative_positive' },
        { a: 999999, b: 1, type: 'large_number' },
        { a: 0.1, b: 0.2, type: 'decimal' }
      ];
      
      for (const test of dataTypeTests) {
        const result = await agentApiCallPost({
          callerAgent: TEST_CALLER_DID,
          targetAgent: TEST_TARGET_DID,
          apiPath: "/add",
          params: { a: test.a, b: test.b }
        });
        
        expect(result.success).toBe(true);
        
        if (result.success && result.data) {
          const expectedResult = test.a + test.b;
          const actualResult = result.data.result !== undefined ? result.data.result : result.data;
          
          if (test.type === 'decimal') {
            expect(Math.abs(actualResult - expectedResult)).toBeLessThan(0.001);
          } else {
            expect(actualResult).toBe(expectedResult);
          }
        }
      }
    });

    test('should handle special characters and Unicode', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 测试包含特殊字符的参数（如果API支持）
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { 
          a: 42, 
          b: 58,
          note: "测试中文字符 & special chars: !@#$%^&*()"
        }
      });
      
      // 即使有特殊字符，基本的数学运算应该仍然工作
      expect(result.success).toBe(true);
      
      if (result.success && result.data) {
        const actualResult = result.data.result || result.data;
        expect(actualResult).toBe(100);
      }
    });
  });

  describe('错误处理测试', () => {
    test('should handle invalid parameters gracefully', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: "invalid", b: "data" }
      });
      
      // 根据Python服务器的实现，这可能成功（类型转换）或失败
      // 我们主要验证不会崩溃
      expect(result).toBeDefined();
      expect(typeof result.success).toBe('boolean');
      
      if (!result.success) {
        expect(result.error).toBeDefined();
        logger.info('✅ 无效参数错误处理正常:', result.error);
      }
    });
    
    test('should handle authentication failures', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const result = await agentApiCallPost({
        callerAgent: "did:wba:localhost%3A9527:wba:user:invalid",
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 1, b: 1 }
      });
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      logger.info('✅ 认证失败错误处理正常:', result.error);
    });

    test('should handle non-existent endpoints', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/nonexistent",
        params: { test: "data" }
      });
      
      expect(result.success).toBe(false);
      expect(result.statusCode).toBeDefined();
      logger.info('✅ 不存在端点错误处理正常:', result.error);
    });

    test('should handle network timeouts gracefully', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 使用极短的超时时间来模拟超时
      const userDataManager = LocalUserDataManager.getInstance();
      await userDataManager.initialize();
      const callerUserData = userDataManager.getUserData(TEST_CALLER_DID);
      
      if (callerUserData) {
        const privateKey = callerUserData.getDidPrivateKey();
        if (!privateKey) {
          throw new Error('无法获取私钥');
        }
        const privateKeyPem = privateKey.export({ type: 'pkcs8', format: 'pem' }) as string;
        const apiCaller = new AgentApiCaller(privateKeyPem, TEST_CALLER_DID);
        
        const result = await apiCaller.callAgentApi(
          TEST_TARGET_DID,
          "/add",
          { a: 1, b: 1 },
          { timeout: 1 } // 1ms超时，几乎肯定会超时
        );
        
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        logger.info('✅ 网络超时错误处理正常:', result.error);
      }
    });
  });

  describe('性能验证测试', () => {
    test('should have reasonable response time', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        testReporter.recordTest({
          testName: 'should have reasonable response time',
          success: false,
          error: 'Python服务器未运行'
        });
        return;
      }

      const startTime = Date.now();
      
      const result = await agentApiCallPost({
        callerAgent: TEST_CALLER_DID,
        targetAgent: TEST_TARGET_DID,
        apiPath: "/add",
        params: { a: 10, b: 20 }
      });
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      // 记录API调用结果
      apiCallResults.push({
        testCase: 'Performance Test (10+20)',
        ...result,
        duration: responseTime
      });
      
      expect(result.success).toBe(true);
      expect(responseTime).toBeLessThan(5000); // 5秒内响应
      
      logger.info(`✅ 响应时间: ${responseTime}ms`);

      // 记录测试结果
      testReporter.recordTest({
        testName: 'should have reasonable response time',
        success: result.success && responseTime < 5000,
        duration: responseTime,
        details: { responseTime, result }
      });
    });

    test('should handle concurrent requests', async () => {
      if (!serverRunning) {
        console.log('⏭️  跳过测试：Python服务器未运行');
        return;
      }

      // 并发发送多个请求
      const concurrentRequests = Array.from({ length: 5 }, (_, i) => 
        agentApiCallPost({
          callerAgent: TEST_CALLER_DID,
          targetAgent: TEST_TARGET_DID,
          apiPath: "/add",
          params: { a: i, b: i + 1 }
        })
      );
      
      const results = await Promise.all(concurrentRequests);
      
      // 验证所有请求都成功
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        if (result.success && result.data) {
          const expectedResult = index + (index + 1);
          const actualResult = result.data.result || result.data;
          expect(actualResult).toBe(expectedResult);
        }
      });
      
      logger.info('✅ 并发请求处理正常');
    });
  });
});