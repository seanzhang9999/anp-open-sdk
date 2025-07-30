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
  GlobalMessageManager
} from '../src/runtime/decorators/type-safe-decorators';
import { agentApi } from '../src/runtime/decorators/simple-decorators';
import { ANPUser } from '../src/foundation';
import { getLogger } from '../src/foundation';
import { loadGlobalConfig } from '../src/foundation/config';
import { getUserDataManager } from '../src/foundation/user';
import { AgentApiCaller } from '../src/runtime/services/agent-api-caller';
import { agentMsgPost as agentMsgPostService } from '../src/runtime/services/agent-message-caller';
import { AnpServer } from '../src/server/express/anp-server';
import { fixFlowAnpAgentRoutes } from '../src/runtime/decorators/fix-api-routes';
import { AgentConfigLoader } from '@runtime/core/agent-config-loader';

const logger = getLogger('FlowAnpAgent');

/**
 * 等待用户输入
 */
async function waitForUserInput(): Promise<void> {
  return new Promise((resolve) => {
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.on('data', () => {
      process.stdin.setRawMode(false);
      process.stdin.pause();
      resolve();
    });
  });
}

/**
 * Agent API调用函数 - 模拟Python版本的agent_api_call_post
 */
async function agentApiCallPost(
  callerAgent: string,
  targetAgent: string,
  apiPath: string,
  params: any = {}
): Promise<any> {
  try {
    // 获取调用者的私钥（简化版，实际应该从用户数据中获取）
    const userDataManager = getUserDataManager();
    const callerUserData = userDataManager.getUserData(callerAgent);
    if (!callerUserData) {
      throw new Error(`找不到调用者用户数据: ${callerAgent}`);
    }

    // 创建API调用器
    const apiCaller = new AgentApiCaller(
      callerUserData.jwtPrivateKeyFilePath, // 简化版，实际应该读取私钥内容
      callerAgent
    );

    // 构建请求数据
    const requestData = {
      type: 'api_call',
      path: apiPath,
      params: params,
      req_did: callerAgent,
      timestamp: new Date().toISOString()
    };

    // 调用API - 修复：直接使用具体的API路径，而不是统一的/wba/agent/request
    const result = await apiCaller.callAgentApi(
      targetAgent,
      apiPath,  // 直接使用传入的apiPath，如 '/add', '/weather/current' 等
      requestData
    );

    if (result.success) {
      return result.data;
    } else {
      throw new Error(result.error || 'API调用失败');
    }

  } catch (error) {
    logger.error(`Agent API调用失败: ${error}`);
    throw error;
  }
}

/**
 * Agent消息发送函数 - 使用新的消息服务
 */
async function agentMsgPost(
  callerAgent: string,
  targetAgent: string,
  content: string,
  messageType: string = 'text'
): Promise<any> {
  return await agentMsgPostService(callerAgent, targetAgent, content, messageType);
}

/**
 * 创建代码生成的Agent - 完整复现Python版本功能
 * 使用方案C+A组合：装饰器模式 + 函数式API
 */
async function createAgentsWithCode(): Promise<any[]> {
  logger.debug("🤖 创建代码生成的Agent...");

  const codeAgents: any[] = [];
  
  try {
    // ===== 方案C：使用装饰器创建计算器Agent =====
    @agentClass({
      name: "代码生成计算器",
      description: "提供基本的计算功能",
      did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
      shared: false
    })
    class CalculatorAgent {
      @classApi("/add", {
        description: "加法计算API"
      })
      async addApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数 - 修复参数解析逻辑
        logger.debug(`🔍 收到的requestData:`, JSON.stringify(requestData, null, 2));
        
        // 参数可能在body.params中
        const params = requestData.body?.params || requestData.params || {};
        const a = params.a || 0;
        const b = params.b || 0;
        const result = a + b;
        logger.info(`🔢 计算: ${a} + ${b} = ${result}`);
        return { result, operation: "add", inputs: [a, b] };
      }
      
      @classApi("/multiply", {
        description: "乘法计算API"
      })
      async multiplyApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数 - 修复参数解析逻辑
        logger.debug(`🔍 收到的requestData:`, JSON.stringify(requestData, null, 2));
        
        // 参数可能在body.params中
        const params = requestData.body?.params || requestData.params || {};
        const a = params.a || 1;
        const b = params.b || 1;
        const result = a * b;
        logger.debug(`🔢 计算: ${a} × ${b} = ${result}`);
        return { result, operation: "multiply", inputs: [a, b] };
      }
      
      @classMessageHandler("text")
      async handleCalcMessage(msgData: any): Promise<any> {
        const content = msgData.content || '';
        logger.debug(`💬 代码生成计算器收到消息: ${content}`);
        
        // 简单的计算解析
        if (content.includes('+')) {
          try {
            const parts = content.split('+');
            if (parts.length === 2) {
              const a = parseFloat(parts[0].trim());
              const b = parseFloat(parts[1].trim());
              const result = a + b;
              return { reply: `计算结果: ${a} + ${b} = ${result}` };
            }
          } catch (error) {
            // 忽略解析错误
          }
        }
        
        return { reply: `代码生成计算器收到: ${content}。支持格式如 '5 + 3'` };
      }
    }
    
    // 实例化计算器Agent
    const calcAgentInstance = new (CalculatorAgent as any)();
    const calcAgent = calcAgentInstance.agent;
    codeAgents.push(calcAgent);
    logger.debug("✅ 创建代码生成计算器Agent成功");
    
    // ===== 方案C：使用装饰器创建天气Agent =====
    @agentClass({
      name: "代码生成天气",
      description: "提供天气信息服务",
      did: "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",
      shared: true,
      prefix: "/weather",
      primaryAgent: true
    })
    class WeatherAgent {
      @classApi("/current", {
        description: "获取当前天气API"
      })
      async weatherCurrentApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数
        const params = requestData.params || {};
        const city = params.city || '北京';
        // 模拟天气数据
        const weatherData = {
          city,
          temperature: "22°C",
          condition: "晴天",
          humidity: "65%",
          wind: "微风"
        };
        logger.debug(`🌤️ 查询天气: ${city} - ${weatherData.condition}`);
        return weatherData;
      }
      
      @classApi("/forecast", {
        description: "获取天气预报API"
      })
      async weatherForecastApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数
        const params = requestData.params || {};
        const city = params.city || '北京';
        const days = params.days || 3;
        
        const forecast: any[] = [];
        const conditions = ["晴天", "多云", "小雨"];
        for (let i = 0; i < days; i++) {
          forecast.push({
            date: `2024-01-${(15 + i).toString().padStart(2, '0')}`,
            condition: conditions[i % conditions.length],
            high: `${20 + i}°C`,
            low: `${10 + i}°C`
          });
        }
        
        const result = { city, forecast };
        logger.debug(`🌤️ 查询${days}天预报: ${city}`);
        return result;
      }
      
      @classMessageHandler("text")
      async handleWeatherMessage(msgData: any): Promise<any> {
        const content = msgData.content || '';
        logger.debug(`💬 代码生成天气Agent收到消息: ${content}`);
        
        if (content.includes('天气')) {
          return { reply: `天气查询服务已收到: ${content}。可以查询任何城市的天气信息。` };
        }
        
        return { reply: `代码生成天气Agent收到: ${content}` };
      }
    }

    // 实例化天气Agent
    const weatherAgentInstance = new (WeatherAgent as any)();
    const weatherAgent = weatherAgentInstance.agent;
    codeAgents.push(weatherAgent);
    logger.debug("✅ 创建代码生成天气Agent成功");
    
    // ===== 方案A：使用函数式API创建助手Agent（共享DID，非主Agent）=====
    const assistantAgent = await createSharedAgent({
      name: "代码生成助手",
      did: "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",  // 使用相同的DID
      prefix: "/assistant",
      primaryAgent: false  // primary_agent = false
    });

    // 使用agentApi注册API
    agentApi(assistantAgent, "/help")(
      async function helpApi(requestData: any, request: any) {
        // 从params中获取参数
        const params = requestData.params || {};
        const topic = params.topic || 'general';
        
        const helpInfo: Record<string, string> = {
          "general": "我是代码生成助手，可以提供各种帮助信息",
          "weather": "天气相关帮助：使用 /weather/current 查询当前天气",
          "calc": "计算相关帮助：使用 /add 或 /multiply 进行计算"
        };
        
        const response = {
          topic,
          help: helpInfo[topic] || helpInfo["general"],
          available_topics: Object.keys(helpInfo)
        };
        
        logger.debug(`❓ 提供帮助: ${topic}`);
        return response;
      }
    );

    codeAgents.push(assistantAgent);
    logger.debug("✅ 创建代码生成助手Agent成功");
    
  } catch (error) {
    logger.error(`❌ 创建代码生成Agent失败: ${error}`);
    console.trace(error);
  }
  
  return codeAgents;
}

/**
 * 解析命令行参数
 */
function parseCommandLineArgs(): { waitForInput: boolean } {
  const args = process.argv.slice(2);
  return {
    waitForInput: args.includes('--wait') || args.includes('-w') || args.includes('keeprunning')
  };
}

/**
 * 主函数 - 演示Agent系统的使用
 */
async function main() {
  // 解析命令行参数
  const { waitForInput } = parseCommandLineArgs();
  debugger;
  logger.debug("🚀 Starting Agent System Demo...");
  logger.debug(`🔧 等待用户输入模式: ${waitForInput ? '开启' : '关闭'}`);
  
  // 🔧 步骤1：初始化配置系统（参考Python版本）
  logger.debug("🔧 初始化配置系统...");
  try {
    await loadGlobalConfig();
    logger.debug("✅ 配置系统初始化成功");
  } catch (error) {
    logger.error(`❌ 配置系统初始化失败: ${error}`);
    // 继续运行，使用默认配置
  }
  
  // 🔧 步骤2：预加载用户数据（参考Python版本）
  logger.debug("🔧 预加载用户数据...");
  try {
    const userDataManager = getUserDataManager();
    await userDataManager.initialize();
    const userCount = userDataManager.getAllUsers().length;
    logger.debug(`✅ 用户数据预加载成功，共加载 ${userCount} 个用户`);
  } catch (error) {
    logger.error(`❌ 用户数据预加载失败: ${error}`);
    // 继续运行，但可能会有用户数据找不到的问题
  }
  
  // 清除之前的Agent注册记录
  AgentManager.clearAllAgents();
  GlobalMessageManager.clearHandlers();
  logger.debug("🧹 已清除之前的Agent注册记录");
  
  const allAgents: any[] = [];

  // 1. 加载配置文件定义的 agents
  const configLoader = new AgentConfigLoader();
  const configAgents = await configLoader.loadAllAgents();
  allAgents.push(...configAgents);
  logger.debug(`✅ 从配置文件加载了 ${configAgents.length} 个 agents`);

  // 2. 加载代码定义的 agents（保持现有功能）
  const codeGeneratedAgents = await createAgentsWithCode();
  allAgents.push(...codeGeneratedAgents);
  
  if (!allAgents.length) {
    logger.debug("No agents were created. Exiting.");
    return;
  }
  
  // 显示Agent管理器状态
  logger.debug("\n📊 Agent管理器状态:");
  const agentsInfo = AgentManager.listAgents();
  for (const [did, agentDict] of Object.entries(agentsInfo)) {
    logger.debug(`  DID: ${did}共有${Object.keys(agentDict).length}个agent`);
    for (const [agentName, agentInfo] of Object.entries(agentDict)) {
      const mode = agentInfo.shared ? "共享" : "独占";
      const primary = agentInfo.primaryAgent ? " (主)" : "";
      const prefix = agentInfo.prefix ? ` prefix:${agentInfo.prefix}` : "";
      logger.debug(`    - ${agentName}: ${mode}${primary}${prefix}`);
    }
  }

  // 显示全局消息管理器状态
  logger.debug("\n💬 全局消息管理器状态:");
  const handlers = GlobalMessageManager.listHandlers();
  for (const [msgType, count] of Object.entries(handlers)) {
    logger.debug(`  💬 ${msgType}: ${count} handlers`);
  }

  // 调试：检查Agent的API路由注册情况
  logger.debug("\n🔍 调试：检查Agent的API路由注册情况...");
  const registeredAgents = AgentManager.getAllAgents();
  for (const agent of registeredAgents) {
    if (agent && agent.anpUser) {
      logger.debug(`Agent: ${agent.name}`);
      logger.debug(`  DID: ${agent.anpUser.id}`);
      logger.debug(`  API路由数量: ${agent.apiRoutes.size}`);
      for (const [path, handler] of agent.apiRoutes) {
        const handlerName = handler.name || 'unknown';
        logger.debug(`    - ${path}: ${handlerName}`);
      }
    } else {
      logger.debug(`⚠️  发现无效的Agent对象: ${agent?.name || 'unknown'}`);
    }
  }
  
  // 🚀 步骤3：启动ANP服务器（参考Python版本）
  logger.debug("\n✅ All agents created with new system. Creating server instance...");
  const server = new AnpServer({
    host: 'localhost',
    port: 9527,
    enableCors: true,
    enableAuth: true,
    enableLogging: true
  });

  // 注册所有Agent到服务器
  server.registerAgents(allAgents);
  
  // 注释掉API路由修复调用，让装饰器系统正常工作
  // logger.debug("🔧 修复API路由注册问题...");
  // const calcAgent = allAgents.find(a => a.name.includes("计算器"));
  // const weatherAgent = allAgents.find(a => a.name.includes("天气"));
  // const assistantAgent = allAgents.find(a => a.name.includes("助手"));
  // fixFlowAnpAgentRoutes(calcAgent, weatherAgent, assistantAgent);
  
  logger.debug("⏳ 等待服务器启动 localhost:9527 ...");
  await server.start();
  logger.debug("✅ 服务器就绪，开始执行任务。");

  // 测试新Agent系统功能
  await testNewAgentSystem(allAgents);
  
  // 根据命令行参数决定是否等待用户输入
  if (waitForInput) {
    logger.debug("\n🔥 Demo completed. Press Enter to stop server...");
    await waitForUserInput();
  } else {
    logger.debug("\n🔥 Demo completed. Stopping server automatically...");
  }
  
  // 停止服务器
  await server.stop();
  logger.debug("\n🎉 Agent系统演示完成!");
  
  // 确保程序在非等待模式下自动退出
  if (!waitForInput) {
    process.exit(0);
  }
}

/**
 * 测试新Agent系统功能 - 对应Python版本的test_new_agent_system
 */
async function testNewAgentSystem(agents: any[]): Promise<void> {
  logger.debug("\n🧪 开始测试新Agent系统功能...");
  
  // 找到不同类型的Agent
  let calcAgent: any = null;
  let weatherAgent: any = null;
  let assistantAgent: any = null;
  
  for (const agent of agents) {
    if (agent && agent.name) {
      if (agent.name.includes("计算器")) {
        calcAgent = agent;
      } else if (agent.name.includes("天气")) {
        weatherAgent = agent;
      } else if (agent.name.includes("助手")) {
        assistantAgent = agent;
      }
    } else {
      logger.debug(`⚠️  发现无效的Agent对象: ${agent}`);
    }
  }
  
  // 基础测试
  logger.debug("\n🔍 基础功能测试...");
  
  // 测试1: 计算器API调用
  let calcApiSuccess = false;
  if (calcAgent) {
    logger.info("\n🔧 测试计算器Agent API调用...");
    try {
      const calcDid = calcAgent.anpUser.id;
      const result = await agentApiCallPost(
        "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
        calcDid,
        "/add",
        { a: 15, b: 25 }
      );
      logger.info(`✅ 计算器API调用成功: ${JSON.stringify(result)}`);
      calcApiSuccess = true;
    } catch (error) {
      logger.info(`❌ 计算器API调用失败: ${error}`);
    }
  }

  // 从allAgents数组中查找配置文件加载的Calculator Agent
  // 从配置文件加载的agents中获取Calculator Agent
  const allRegisteredAgents = AgentManager.getAllAgents();
  const calcAgentFromPath = allRegisteredAgents.find(agent =>
    agent && agent.name === "Calculator Agent JS"
  );
  if (calcAgentFromPath) {
    calcApiSuccess = false;

    logger.info("\n🔧 测试目录加载计算器Agent API调用...");
    try {
      const calcDid = calcAgentFromPath.anpUser.id;
      logger.info(`📋 目录加载计算器Agent DID: ${calcDid}`);

      const result = await agentApiCallPost(
        "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d", // 调用者DID
        calcDid, // 目标Agent DID
        "/calculator-js/add", // API路径
        { a: 25, b: 25 } // 参数
      );
      logger.info(`✅ 目录加载计算器API调用成功: ${JSON.stringify(result)}`);
      calcApiSuccess = true;
    } catch (error) {
      logger.info(`❌ 目录加载计算器API调用失败: ${error}`);
    }
  } else {
    logger.info("❌ 未找到目录加载的Calculator Agent JS");
  }
  
  // 测试2: 消息发送
  let msgSuccess = false;
  if (weatherAgent) {
    logger.info("\n📨 测试天气Agent消息发送...");
    try {
      const weatherDid = weatherAgent.anpUser.id;
      const result = await agentMsgPost(
        "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
        weatherDid,
        "请问今天北京的天气怎么样？",
        "text"
      );
      logger.info(`✅ 天气Agent消息发送成功: ${JSON.stringify(result)}`);
      msgSuccess = true;
    } catch (error) {
      logger.info(`❌ 天气Agent消息发送失败: ${error}`);
    }
  }
  
  // 测试3: 共享DID API调用
  let sharedApiSuccess = false;
  if (weatherAgent && assistantAgent) {
    logger.info("\n🔗 测试共享DID API调用...");
    try {
      // 调用天气API
      const weatherDid = weatherAgent.anpUser.id;
      const weatherResult = await agentApiCallPost(
        "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
        weatherDid,
        "/weather/current",
        { city: "上海" }
      );
      logger.info(`✅ 天气API调用成功: ${JSON.stringify(weatherResult)}`);
      
      // 调用助手API
      const assistantDid = assistantAgent.anpUser.id;
      const helpResult = await agentApiCallPost(
        "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
        assistantDid,
        "/assistant/help",
        { topic: "weather" }
      );
      logger.info(`✅ 助手API调用成功: ${JSON.stringify(helpResult)}`);
      sharedApiSuccess = true;
      
    } catch (error) {
      logger.info(`❌ 共享DID API调用失败: ${error}`);
    }
  }
  
  // 测试4: 冲突检测
  let conflictTestSuccess = false;
  logger.info("\n⚠️  测试冲突检测...");
  try {
    // 尝试创建冲突的Agent
    const testUserDid = "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1";
    
    // 获取用户数据管理器并创建ANPUser对象
    const userDataManager = getUserDataManager();
    const testUserData = userDataManager.getUserData(testUserDid);
    
    if (testUserData) {
      const testAnpUser = new ANPUser(testUserData);
      
      // 先创建一个Agent
      logger.info(`创建第一个Agent: ${testUserDid}`);
      const firstAgent = AgentManager.createAgent(testAnpUser, {
        name: "第一个测试Agent",
        shared: false
      });
      
      // 尝试创建第二个Agent，这应该失败，因为DID已被独占使用
      logger.info(`尝试创建冲突Agent: ${testUserDid}`);
      try {
        const conflictAgent = AgentManager.createAgent(testAnpUser, {
          name: "冲突测试Agent",
          shared: false
        });
        logger.error("❌ 冲突检测失败：应该阻止创建冲突Agent");
      } catch (conflictError: any) {
        logger.info(`✅ 冲突检测成功: ${conflictError.message}`);
        conflictTestSuccess = true;
      }
    } else {
      logger.info(`❌ 冲突检测失败: 测试用户数据不存在，无法创建Agent`);
    }
    
  } catch (error: any) {
    logger.info(`✅ 冲突检测成功: ${error.message}`);
    conflictTestSuccess = true;
  }
  
  // 测试结果总结
  logger.debug("\n📊 测试结果总结:");
  logger.info(`  🔧 计算器API调用: ${calcApiSuccess ? '✅ 成功' : '❌ 失败'}`);
  logger.info(`  📨 消息发送: ${msgSuccess ? '✅ 成功' : '❌ 失败'}`);
  logger.info(`  🔗 共享DID API调用: ${sharedApiSuccess ? '✅ 成功' : '❌ 失败'}`);
  logger.info(`  ⚠️  冲突检测: ${conflictTestSuccess ? '✅ 成功' : '❌ 失败'}`);
  
  const successCount = [calcApiSuccess, msgSuccess, sharedApiSuccess, conflictTestSuccess].filter(Boolean).length;
  const totalCount = 4;
  
  if (successCount === totalCount) {
    logger.info(`\n🎉 所有测试通过! (${successCount}/${totalCount}) 架构重构验证成功!`);
  } else {
    logger.info(`\n⚠️  部分测试失败 (${successCount}/${totalCount})，需要进一步调试`);
  }
  
  logger.debug("\n🎉 新Agent系统测试完成!");
}

// 如果这个文件被直接运行
if (require.main === module) {
  main().catch(console.error);
}

export { createAgentsWithCode, main, testNewAgentSystem };
