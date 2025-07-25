/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

/**
 * ServicePoint模块使用示例
 * 展示如何使用各种服务处理器和路由器
 */

import {
  DIDServiceHandler,
  PublisherServiceHandler,
  AuthServiceHandler,
  HostServiceHandler,
  AuthExemptHandler
} from './handlers';

// 直接从文件导入管理器和路由器
import { ServicePointManager } from './service-point-manager';
import { ServicePointRouter } from './service-point-router';

// 直接从文件导入类型
import type { ServicePointRequest } from './service-point-manager';
import type { RouteDefinition } from './service-point-router';

/**
 * 基本使用示例
 */
async function basicUsageExample() {
  console.log('=== ServicePoint基本使用示例 ===');

  // 1. 使用ServicePointManager处理请求
  const manager = new ServicePointManager();
  
  const request = {
    path: '/health',
    method: 'GET',
    headers: {},
    host: 'localhost',
    port: 9527
  };

  const response = await manager.handleRequest(request);
  console.log('健康检查响应:', response);

  // 2. 获取DID文档
  const didResponse = await DIDServiceHandler.getDidDocument(
    'example_user',
    'localhost',
    9527
  );
  console.log('DID文档响应:', didResponse);

  // 3. 获取智能体列表
  const agentsResponse = await PublisherServiceHandler.getPublishedAgents(
    'localhost',
    9527
  );
  console.log('智能体列表:', agentsResponse);

  // 4. 检查认证豁免
  const exemptResponse = await AuthExemptHandler.checkAuthExemption({
    path: '/health',
    method: 'GET',
    host: 'localhost',
    port: 9527
  });
  console.log('认证豁免检查:', exemptResponse);
}

/**
 * 路由器使用示例
 */
async function routerUsageExample() {
  console.log('\n=== ServicePoint路由器使用示例 ===');

  const router = new ServicePointRouter();

  // 添加自定义路由
  router.get('/custom/hello', async (request: ServicePointRequest) => {
    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: { message: 'Hello from custom route!' },
      success: true
    };
  }, { description: '自定义问候端点' });

  // 添加需要认证的路由
  router.post('/custom/secure', async (request: ServicePointRequest) => {
    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: { message: 'This is a secure endpoint', data: request.body },
      success: true
    };
  }, { requireAuth: true, description: '安全端点' });

  // 添加中间件
  router.addLoggingMiddleware();
  router.addCorsMiddleware({
    origin: ['http://localhost:3000', 'http://localhost:8080'],
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    headers: ['Content-Type', 'Authorization']
  });

  // 测试自定义路由
  const customRequest = {
    path: '/custom/hello',
    method: 'GET',
    headers: {},
    host: 'localhost',
    port: 9527
  };

  const customResponse = await router.handleRequest(customRequest);
  console.log('自定义路由响应:', customResponse);

  // 获取所有路由信息
  const routes = router.getRoutes();
  console.log('所有路由:', routes.map((r: RouteDefinition) => `${r.method} ${r.pattern}`));
}

/**
 * 认证服务示例
 */
async function authServiceExample() {
  console.log('\n=== 认证服务使用示例 ===');

  // 模拟认证请求
  const authRequest = {
    token: 'sample_bearer_token',
    headers: {
      'authorization': 'Bearer sample_bearer_token'
    },
    method: 'POST',
    path: '/api/secure'
  };

  const authResponse = await AuthServiceHandler.handleAuthRequest(
    authRequest,
    'localhost',
    9527
  );
  console.log('认证响应:', authResponse);

  // 检查API密钥
  const apiKeyResponse = await AuthServiceHandler.verifyApiKey(
    'anp_sample_api_key_12345678901234567890',
    'localhost',
    9527
  );
  console.log('API密钥验证:', apiKeyResponse);
}

/**
 * 主机服务示例
 */
async function hostServiceExample() {
  console.log('\n=== 主机服务使用示例 ===');

  // 创建托管DID请求
  const hostedDidRequest = {
    did: 'did:wba:localhost%3A9527:wba:hostuser:example',
    requestType: 'create' as const,
    userData: {
      name: 'Example Hosted User',
      description: 'This is an example hosted DID'
    },
    metadata: {
      createdBy: 'system',
      purpose: 'example'
    }
  };

  const createResponse = await HostServiceHandler.handleHostedDidRequest(
    hostedDidRequest,
    'localhost',
    9527
  );
  console.log('创建托管DID响应:', createResponse);

  // 获取托管DID状态
  const statusResponse = await HostServiceHandler.getHostedDidStatus(
    hostedDidRequest.did,
    'localhost',
    9527
  );
  console.log('托管DID状态:', statusResponse);

  // 获取所有托管DID
  const allHostedResponse = await HostServiceHandler.getAllHostedDids(
    'localhost',
    9527
  );
  console.log('所有托管DID:', allHostedResponse);
}

/**
 * 豁免规则管理示例
 */
async function exemptRulesExample() {
  console.log('\n=== 认证豁免规则管理示例 ===');

  // 获取所有豁免规则
  const rulesResponse = await AuthExemptHandler.getAllExemptRules(
    'localhost',
    9527
  );
  console.log('所有豁免规则:', rulesResponse);

  // 测试路径匹配
  const testPaths = [
    { path: '/health', method: 'GET' },
    { path: '/wba/user/example/did.json', method: 'GET' },
    { path: '/api/secure', method: 'POST' },
    { path: '/publisher/agents', method: 'GET' }
  ];

  for (const testPath of testPaths) {
    const testResponse = await AuthExemptHandler.testExemptRule(
      testPath.path,
      testPath.method,
      'localhost',
      9527
    );
    console.log(`路径 ${testPath.path} (${testPath.method}):`, testResponse.data?.result);
  }

  // 批量检查
  const batchRequests = testPaths.map(tp => ({
    path: tp.path,
    method: tp.method,
    host: 'localhost',
    port: 9527
  }));

  const batchResponse = await AuthExemptHandler.batchCheckExemption(batchRequests);
  console.log('批量豁免检查:', batchResponse);
}

/**
 * 运行所有示例
 */
async function runAllExamples() {
  try {
    await basicUsageExample();
    await routerUsageExample();
    await authServiceExample();
    await hostServiceExample();
    await exemptRulesExample();
    
    console.log('\n=== 所有示例运行完成 ===');
  } catch (error) {
    console.error('示例运行失败:', error);
  }
}

// 如果直接运行此文件，执行示例
if (require.main === module) {
  runAllExamples();
}

export {
  basicUsageExample,
  routerUsageExample,
  authServiceExample,
  hostServiceExample,
  exemptRulesExample,
  runAllExamples
};