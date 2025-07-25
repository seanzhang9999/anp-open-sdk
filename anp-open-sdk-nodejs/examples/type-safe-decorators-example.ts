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
  groupEventMethod,
  createAgent,
  createSharedAgent,
  agentApi,
  agentMessageHandler,
  AgentManager,
  GlobalMessageManager
} from '../src/runtime/decorators/type-safe-decorators';
import { getLogger } from '../src/foundation/utils';

const logger = getLogger('TypeSafeDecoratorsExample');

/**
 * 使用类型安全装饰器创建Agent - 完全复现Python版本功能
 */
async function createAgentsWithTypeSafeDecorators(): Promise<any[]> {
  logger.debug("🤖 使用类型安全装饰器创建Agent...");

  const codeAgents: any[] = [];
  
  try {
    // 使用类型安全装饰器创建计算器Agent
    @agentClass({
      name: "类型安全计算器",
      description: "提供基本的计算功能",
      did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
      shared: false
    })
    class CalculatorAgent {
      @classApi("/add", { 
        description: "加法计算API",
        methods: ["POST"],
        parameters: {
          a: { type: "number", description: "第一个数字" },
          b: { type: "number", description: "第二个数字" }
        },
        returns: "计算结果对象"
      })
      async addApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数
        const params = requestData.params || {};
        const a = params.a || 0;
        const b = params.b || 0;
        const result = a + b;
        logger.debug(`🔢 计算: ${a} + ${b} = ${result}`);
        return { result, operation: "add", inputs: [a, b] };
      }
      
      @classApi("/multiply", {
        description: "乘法计算API",
        methods: ["POST"]
      })
      async multiplyApi(requestData: any, request: any): Promise<any> {
        // 从params中获取参数
        const params = requestData.params || {};
        const a = params.a || 1;
        const b = params.b || 1;
        const result = a * b;
        logger.debug(`🔢 计算: ${a} × ${b} = ${result}`);
        return { result, operation: "multiply", inputs: [a, b] };
      }
      
      @classMessageHandler("text", {
        description: "处理文本消息"
      })
      async handleCalcMessage(msgData: any): Promise<any> {
        const content = msgData.content || '';
        logger.debug(`💬 类型安全计算器收到消息: ${content}`);
        
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
        
        return { reply: `类型安全计算器收到: ${content}。支持格式如 '5 + 3'` };
      }

      @groupEventMethod("calc_group", "join")
      async handleGroupJoin(groupId: string, eventType: string, eventData: any): Promise<any> {
        logger.debug(`👥 计算器群组事件: ${groupId}/${eventType}`);
        return { message: "欢迎加入计算器群组!", groupId, eventType };
      }
    }
    
    // 实例化计算器Agent
    const calcAgent = new CalculatorAgent().agent;
    codeAgents.push(calcAgent);
    logger.debug("✅ 创建类型安全计算器Agent成功");
    
    // 使用类型安全装饰器创建天气Agent
    @agentClass({
      name: "类型安全天气",
      description: "提供天气信息服务",
      did: "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",
      shared: true,
      prefix: "/weather",
      primaryAgent: true
    })
    class WeatherAgent {
      @classApi("/current", {
        description: "获取当前天气API",
        parameters: {
          city: { type: "string", description: "城市名称", default: "北京" }
        }
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
        description: "获取天气预报API",
        parameters: {
          city: { type: "string", description: "城市名称" },
          days: { type: "number", description: "预报天数", default: 3 }
        }
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
        logger.debug(`💬 类型安全天气Agent收到消息: ${content}`);
        
        if (content.includes('天气')) {
          return { reply: `天气查询服务已收到: ${content}。可以查询任何城市的天气信息。` };
        }
        
        return { reply: `类型安全天气Agent收到: ${content}` };
      }

      @groupEventMethod(undefined, "weather_alert")
      async handleWeatherAlert(groupId: string, eventType: string, eventData: any): Promise<any> {
        logger.debug(`🌦️ 天气预警事件: ${groupId}/${eventType}`);
        return { message: "天气预警已处理", alert: eventData };
      }
    }

    // 实例化天气Agent
    const weatherAgent = new WeatherAgent().agent;
    codeAgents.push(weatherAgent);
    logger.debug("✅ 创建类型安全天气Agent成功");
    
    // 使用函数式方法创建助手Agent（共享DID，非主Agent）
    const assistantAgent = createSharedAgent(
      "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",  // 使用相同的DID
      "类型安全助手",
      "/assistant",
      false  // primary_agent = false
    );

    // 注册API - 使用函数式装饰器
    const helpApiHandler = agentApi(assistantAgent, "/help")(
      async function helpApi(requestData: any, request: any) {
        // 从params中获取参数
        const params = requestData.params || {};
        const topic = params.topic || 'general';
        
        const helpInfo: Record<string, string> = {
          "general": "我是类型安全助手，可以提供各种帮助信息",
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

    // 注册消息处理器
    const assistantMessageHandler = agentMessageHandler(assistantAgent, "help")(
      async function handleHelpMessage(msgData: any) {
        const content = msgData.content || '';
        logger.debug(`💬 类型安全助手收到帮助消息: ${content}`);
        return { reply: `助手收到帮助请求: ${content}` };
      }
    );

    codeAgents.push(assistantAgent);
    logger.debug("✅ 创建类型安全助手Agent成功");
    
  } catch (error) {
    logger.error(`❌ 创建类型安全Agent失败: ${error}`);
    console.trace(error);
  }
  
  return codeAgents;
}

/**
 * 主函数 - 演示类型安全装饰器的使用
 */
async function main() {
  logger.debug("🚀 Starting Type-Safe Decorators Demo...");
  
  // 清除之前的Agent注册记录
  AgentManager.clearAllAgents();
  GlobalMessageManager.clearHandlers();
  logger.debug("🧹 已清除之前的Agent注册记录");
  
  const allAgents: any[] = [];
  
  // 用类型安全装饰器生成Agent
  const typeSafeAgents = await createAgentsWithTypeSafeDecorators();
  allAgents.push(...typeSafeAgents);
  
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
  for (const handler of handlers) {
    logger.debug(`  💬 ${handler.did}:${handler.msgType} <- ${handler.agentName}`);
  }

  // 调试：检查Agent的API路由注册情况
  logger.debug("\n🔍 调试：检查Agent的API路由注册情况...");
  for (const agent of allAgents) {
    if (agent.anpUser) {
      logger.debug(`Agent: ${agent.name}`);
      logger.debug(`  DID: ${agent.anpUser.id}`);
      logger.debug(`  API路由数量: ${agent.anpUser.apiRoutes.size}`);
      for (const [path, handler] of agent.anpUser.apiRoutes) {
        const handlerName = handler.name || 'unknown';
        logger.debug(`    - ${path}: ${handlerName}`);
      }
    }
  }
  
  logger.debug("\n🎉 类型安全装饰器演示完成!");
  logger.debug("\n📝 类型安全装饰器的优势:");
  logger.debug("  ✅ 编译时类型检查");
  logger.debug("  ✅ 完整的IDE智能提示");
  logger.debug("  ✅ 避免运行时类型错误");
  logger.debug("  ✅ 与Python版本功能完全对等");
}

// 如果这个文件被直接运行
if (require.main === module) {
  main().catch(console.error);
}

export { createAgentsWithTypeSafeDecorators, main };