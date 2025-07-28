/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Agent } from '../core/agent';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('FixApiRoutes');

/**
 * 修复API路由注册问题的工具函数
 * 用于在Agent创建后手动注册API路由
 */
export function registerApiRoutes(agent: Agent, apiRoutes: Array<{path: string, handler: Function}>) {
  logger.debug(`🔧 开始为Agent '${agent.name}' 手动注册API路由...`);
  
  for (const { path, handler } of apiRoutes) {
    // 计算完整路径（考虑前缀）
    const fullPath = agent.prefix ? `${agent.prefix}${path}` : path;
    
    // 注册到Agent的路由表
    agent.apiRoutes.set(fullPath, handler);
    
    logger.debug(`  ✅ 注册API路由: ${fullPath} -> ${handler.name || 'anonymous'}`);
  }
  
  logger.debug(`🔧 API路由注册完成，共注册 ${apiRoutes.length} 个路由`);
  
  // 打印当前所有路由
  logger.debug(`📊 Agent '${agent.name}' 当前所有API路由:`);
  for (const [path, handler] of agent.apiRoutes) {
    logger.debug(`  - ${path}: ${handler.name || 'anonymous'}`);
  }
}

/**
 * 修复装饰器类API路由注册问题
 * 用于从类实例中提取API方法并注册到Agent
 */
export function registerClassApiRoutes(agent: Agent, classInstance: any) {
  logger.debug(`🔧 开始从类实例 ${classInstance.constructor.name} 注册API路由到Agent '${agent.name}'...`);
  
  // 获取原型
  const prototype = Object.getPrototypeOf(classInstance);
  // 获取所有属性名
  const propertyNames = Object.getOwnPropertyNames(prototype);
  
  const apiRoutes: Array<{path: string, handler: Function}> = [];
  
  // 遍历所有方法
  for (const propertyName of propertyNames) {
    if (propertyName === 'constructor') continue;
    
    const descriptor = Object.getOwnPropertyDescriptor(prototype, propertyName);
    if (!descriptor || typeof descriptor.value !== 'function') continue;
    
    const method = descriptor.value;
    
    // 检查方法名是否包含"Api"
    if (propertyName.includes('Api')) {
      // 从方法名推断API路径
      const path = '/' + propertyName.replace('Api', '').toLowerCase();
      
      // 绑定方法到实例
      const boundHandler = method.bind(classInstance);
      
      apiRoutes.push({ path, handler: boundHandler });
      logger.debug(`  🔍 从方法名推断API路径: ${propertyName} -> ${path}`);
    }
  }
  
  // 注册所有找到的API路由
  registerApiRoutes(agent, apiRoutes);
}

/**
 * 修复flow-anp-agent.ts中的API路由注册问题
 */
export function fixFlowAnpAgentRoutes(calcAgent: any, weatherAgent: any, assistantAgent: any) {
  logger.debug(`🔧 开始修复flow-anp-agent.ts中的API路由注册问题...`);
  
  // 修复计算器Agent的API路由
  if (calcAgent) {
    registerApiRoutes(calcAgent, [
      { path: '/add', handler: async function addApi(requestData: any) {
        const params = requestData.params || {};
        const a = params.a || 0;
        const b = params.b || 0;
        const result = a + b;
        logger.debug(`🔢 计算: ${a} + ${b} = ${result}`);
        return { result, operation: "add", inputs: [a, b] };
      }},
      { path: '/multiply', handler: async function multiplyApi(requestData: any) {
        const params = requestData.params || {};
        const a = params.a || 1;
        const b = params.b || 1;
        const result = a * b;
        logger.debug(`🔢 计算: ${a} × ${b} = ${result}`);
        return { result, operation: "multiply", inputs: [a, b] };
      }}
    ]);
  }
  
  // 修复天气Agent的API路由
  if (weatherAgent) {
    // 获取天气Agent的前缀
    const prefix = weatherAgent.prefix || '';
    logger.debug(`🔍 天气Agent前缀: "${prefix}"`);
    
    registerApiRoutes(weatherAgent, [
      { path: '/current', handler: async function weatherCurrentApi(requestData: any) {
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
      }},
      { path: '/forecast', handler: async function weatherForecastApi(requestData: any) {
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
      }}
    ]);
    
    // 单独注册消息处理路由，不带前缀
    weatherAgent.apiRoutes.set('/message/post', async function handleWeatherMessage(requestData: any) {
      const content = requestData.content || '';
      logger.debug(`💬 代码生成天气Agent收到消息: ${content}`);
      
      if (content.includes('天气')) {
        return { reply: `天气查询服务已收到: ${content}。可以查询任何城市的天气信息。` };
      }
      
      return { reply: `代码生成天气Agent收到: ${content}` };
    });
    
    logger.debug(`✅ 天气Agent消息处理路由注册成功: /message/post`);
  }
  
  // 修复助手Agent的API路由
  if (assistantAgent) {
    // 直接注册路由，不使用registerApiRoutes函数，避免前缀问题
    assistantAgent.apiRoutes.set('/assistant/help', async function helpApi(requestData: any) {
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
    });
    
    logger.debug(`✅ 助手Agent API路由注册成功: /assistant/help`);
  }
  
  logger.debug(`✅ API路由修复完成!`);
}