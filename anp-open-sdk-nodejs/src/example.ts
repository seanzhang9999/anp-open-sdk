/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import 'reflect-metadata';
import { AnpServer } from './server';
import { Agent, getAgentManager } from './runtime';
import { ANPUser } from './foundation';
import { api, messageHandler, groupEventHandler } from '@runtime/decorators';
import { loadGlobalConfig } from '@foundation/config';

// 示例Agent类 - 继承自Agent
class ExampleAgent extends Agent {
  constructor(anpUser: ANPUser, name: string) {
    super({
      anpUser,
      name,
      shared: true,
      prefix: '/example',
      primaryAgent: true
    });
  }

  @api('/hello', { method: 'GET', description: '简单问候' })
  async sayHello(context: any) {
    return {
      message: `Hello from ${this.name}!`,
      did: this.anpUser.id,
      timestamp: new Date().toISOString()
    };
  }

  @api('/calculate', { method: 'POST', description: '计算器功能' })
  async calculate(context: any) {
    const { a, b, operation } = context.body;
    
    if (typeof a !== 'number' || typeof b !== 'number') {
      throw new Error('Invalid numbers provided');
    }

    let result: number;
    switch (operation) {
      case 'add':
        result = a + b;
        break;
      case 'subtract':
        result = a - b;
        break;
      case 'multiply':
        result = a * b;
        break;
      case 'divide':
        result = b !== 0 ? a / b : NaN;
        break;
      default:
        throw new Error('Unsupported operation');
    }

    return {
      result,
      operation,
      operands: [a, b],
      timestamp: new Date().toISOString()
    };
  }

  @messageHandler('greeting')
  async handleGreeting(payload: any) {
    return {
      response: `Hello ${payload.name}, I'm ${this.name}`,
      timestamp: new Date().toISOString()
    };
  }

  @groupEventHandler('join')
  async handleGroupJoin(payload: any) {
    return {
      message: `Welcome to the group!`,
      groupId: payload.groupId,
      member: payload.did
    };
  }
}

async function main() {
  try {
    // 加载配置
    await loadGlobalConfig();
    
    // 创建示例用户数据
    const userData = {
      did: 'did:wba:localhost_9527_example',
      name: 'Example Agent',
      userDir: './data_user/example',
      didDocPath: './data_user/example/did_document.json',
      didPrivateKeyFilePath: './data_user/example/private_key.pem',
      jwtPrivateKeyFilePath: './data_user/example/jwt_private_key.pem',
      jwtPublicKeyFilePath: './data_user/example/jwt_public_key.pem',
      isHostedDid: false
    };

    // 创建ANPUser
    const anpUser = new ANPUser(userData, 'Example Agent');
    
    // 创建示例Agent（已经继承自Agent）
    const agent = new ExampleAgent(anpUser, 'Example Agent');

    // 注册Agent到AgentManager
    const agentManager = getAgentManager();
    agentManager.registerAgent(agent);

    // 创建服务器
    const server = new AnpServer({
      host: 'localhost',
      port: 9527,
      enableCors: true,
      enableAuth: false, // 示例中禁用认证
      enableLogging: true
    });

    // 注意：不需要重复注册到server，server会通过agentManager获取Agent

    // 启动服务器
    await server.start();

    console.log('🎉 ANP开发服务器启动成功!');
    console.log('📋 可用的API端点:');
    console.log('  - GET  http://localhost:9527/health');
    console.log('  - GET  http://localhost:9527/agents');
    console.log('  - GET  http://localhost:9527/example/hello');
    console.log('  - POST http://localhost:9527/example/calculate');
    console.log('');
    console.log('📝 测试计算器API:');
    console.log('  curl -X POST http://localhost:9527/example/calculate \\');
    console.log('    -H "Content-Type: application/json" \\');
    console.log('    -d \'{"a": 10, "b": 5, "operation": "add"}\'');

    // 处理优雅关闭
    process.on('SIGINT', async () => {
      console.log('\n🛑 接收到关闭信号，开始优雅关闭...');
      await server.gracefulShutdown();
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ 服务器启动失败:', error);
    process.exit(1);
  }
}

// 如果这个文件被直接运行
if (require.main === module) {
  main().catch(console.error);
}

export { main as startExampleServer };
