/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import 'reflect-metadata';
import { 
  agentClass, 
  classApi, 
  classMessageHandler, 
  createAgent,
  createSharedAgent,
  AgentManager,
  GlobalMessageManager,
  getApiPath,
  getApiOptions
} from './src/runtime/decorators/type-safe-decorators';
import { getLogger } from './src/foundation';

const logger = getLogger('DebugApiRoutes');

// 测试装饰器注册
@agentClass({
  name: "测试计算器",
  description: "测试API路由注册",
  did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
  shared: false
})
class TestCalculatorAgent {
  @classApi("/add", {
    description: "加法计算API"
  })
  async addApi(requestData: any, request: any): Promise<any> {
    const params = requestData.params || {};
    const a = params.a || 0;
    const b = params.b || 0;
    const result = a + b;
    return { result, operation: "add", inputs: [a, b] };
  }
}

// 测试函数
async function testDecorators() {
  logger.info("开始测试装饰器API路由注册...");
  
  // 创建实例
  const calcInstance = new (TestCalculatorAgent as any)();
  const agent = calcInstance.agent;
  
  // 检查API路由
  logger.info(`Agent: ${agent.name}`);
  logger.info(`DID: ${agent.anpUser.id}`);
  logger.info(`API路由数量: ${agent.apiRoutes.size}`);
  
  // 检查原型链上的方法
  const prototype = Object.getPrototypeOf(calcInstance);
  const propertyNames = Object.getOwnPropertyNames(prototype);
  
  logger.info("原型链上的方法:");
  for (const propertyName of propertyNames) {
    if (propertyName.startsWith('_') || propertyName === 'constructor') {
      continue;
    }
    
    const descriptor = Object.getOwnPropertyDescriptor(prototype, propertyName);
    if (!descriptor || typeof descriptor.value !== 'function') {
      continue;
    }
    
    const method = descriptor.value;
    const apiPath = getApiPath(method);
    const apiOptions = getApiOptions(method);
    
    logger.info(`  - ${propertyName}: ${apiPath ? `API路径=${apiPath}` : '非API方法'}`);
    if (apiOptions) {
      logger.info(`    选项: ${JSON.stringify(apiOptions)}`);
    }
  }
  
  // 检查已注册的路由
  logger.info("已注册的API路由:");
  for (const [path, handler] of agent.apiRoutes) {
    const handlerName = handler.name || 'unknown';
    logger.info(`  - ${path}: ${handlerName}`);
  }
  
  // 检查装饰器元数据
  logger.info("检查装饰器元数据:");
  const addApiMethod = (prototype as any).addApi;
  if (addApiMethod) {
    const apiPath = getApiPath(addApiMethod);
    logger.info(`  - addApi方法的API路径: ${apiPath || '未找到'}`);
  } else {
    logger.info("  - 未找到addApi方法");
  }
}

// 运行测试
testDecorators().catch(console.error);