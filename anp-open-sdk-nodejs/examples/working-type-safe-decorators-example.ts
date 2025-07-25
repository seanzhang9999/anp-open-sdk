/**
 * 类型安全装饰器完整工作示例
 * 展示如何正确使用TypeScript装饰器系统
 */

import {
  agentClass,
  classApi,
  classMessageHandler,
  groupEventMethod,
  createAgent,
  createSharedAgent,
  createAgentsWithCode,
  GlobalMessageManager,
  AgentManager,
  type AgentClassOptions,
  type ApiDecoratorOptions,
  type MessageHandlerOptions
} from '../src/runtime/decorators/type-safe-decorators';
import { getLogger } from '@foundation/utils';

const logger = getLogger('TypeSafeDecoratorsExample');

// ===== 示例1: 类装饰器方式 =====

@agentClass({
  name: "计算器Agent",
  description: "提供基本数学计算功能",
  did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
  shared: false,
  primaryAgent: true
})
class CalculatorAgent {
  @classApi("/add", { 
    description: "加法计算API",
    methods: ["POST"],
    parameters: { a: "number", b: "number" },
    returns: "计算结果对象"
  })
  async addApi(requestData: any, request: any): Promise<any> {
    const params = requestData.params || {};
    const a = params.a || 0;
    const b = params.b || 0;
    logger.debug(`执行加法: ${a} + ${b}`);
    return { result: a + b, operation: "add" };
  }

  @classApi("/multiply", { 
    description: "乘法计算API",
    methods: ["POST"]
  })
  async multiplyApi(requestData: any, request: any): Promise<any> {
    const params = requestData.params || {};
    const a = params.a || 1;
    const b = params.b || 1;
    logger.debug(`执行乘法: ${a} * ${b}`);
    return { result: a * b, operation: "multiply" };
  }

  @classMessageHandler("text", { 
    description: "处理文本消息",
    autoWrap: true
  })
  async handleTextMessage(msgData: any): Promise<any> {
    const content = msgData.content || "";
    logger.debug(`处理文本消息: ${content}`);
    
    // 简单的计算器命令解析
    const match = content.match(/(\d+)\s*([+\-*/])\s*(\d+)/);
    if (match) {
      const [, a, op, b] = match;
      const numA = parseInt(a);
      const numB = parseInt(b);
      
      let result: number;
      switch (op) {
        case '+': result = numA + numB; break;
        case '-': result = numA - numB; break;
        case '*': result = numA * numB; break;
        case '/': result = numA / numB; break;
        default: result = 0;
      }
      
      return { reply: `计算结果: ${numA} ${op} ${numB} = ${result}` };
    }
    
    return { reply: `收到消息: ${content}` };
  }

  @groupEventMethod("calc_group", "join")
  async handleGroupJoin(eventData: any): Promise<void> {
    logger.debug(`用户加入计算群组: ${JSON.stringify(eventData)}`);
    // 处理群组加入事件
  }
}

@agentClass({
  name: "天气Agent", 
  description: "提供天气查询服务",
  did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
  shared: true,
  prefix: "weather",
  primaryAgent: false
})
class WeatherAgent {
  @classApi("/current", { 
    description: "获取当前天气",
    methods: ["GET", "POST"],
    parameters: { city: "string" }
  })
  async getCurrentWeather(requestData: any, request: any): Promise<any> {
    const params = requestData.params || {};
    const city = params.city || "北京";
    logger.debug(`查询${city}当前天气`);
    
    // 模拟天气数据
    return {
      city,
      temperature: Math.floor(Math.random() * 30) + 5,
      weather: ["晴", "多云", "阴", "小雨"][Math.floor(Math.random() * 4)],
      humidity: Math.floor(Math.random() * 50) + 30,
      timestamp: new Date().toISOString()
    };
  }

  @classApi("/forecast", { 
    description: "获取天气预报",
    methods: ["GET", "POST"],
    parameters: { city: "string", days: "number" }
  })
  async getWeatherForecast(requestData: any, request: any): Promise<any> {
    const params = requestData.params || {};
    const city = params.city || "北京";
    const days = params.days || 3;
    logger.debug(`查询${city}未来${days}天天气预报`);
    
    // 模拟预报数据
    const forecast = [];
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      forecast.push({
        date: date.toISOString().split('T')[0],
        temperature: Math.floor(Math.random() * 30) + 5,
        weather: ["晴", "多云", "阴", "小雨"][Math.floor(Math.random() * 4)]
      });
    }
    
    return { city, forecast };
  }

  @classMessageHandler("text")
  async handleWeatherQuery(msgData: any): Promise<any> {
    const content = msgData.content || "";
    logger.debug(`处理天气查询: ${content}`);
    
    if (content.includes("天气")) {
      const cityMatch = content.match(/(.+?)天气/);
      const city = cityMatch ? cityMatch[1] : "北京";
      
      return {
        reply: `${city}今天天气晴朗，温度25°C，湿度60%`
      };
    }
    
    return { reply: "请询问天气相关问题" };
  }

  @groupEventMethod(undefined, "weather_alert")
  async handleWeatherAlert(eventData: any): Promise<void> {
    logger.debug(`收到天气预警: ${JSON.stringify(eventData)}`);
    // 处理天气预警事件
  }
}

// ===== 示例2: 函数式创建方式 =====

async function createFunctionalAgents(): Promise<void> {
  logger.debug("=== 函数式Agent创建示例 ===");
  
  // 创建独占Agent
  const assistantAgent = createAgent({
    name: "智能助手",
    description: "通用智能助手",
    did: "did:wba:localhost%3A9527:wba:user:another_user",
    shared: false,
    primaryAgent: true
  });
  
  // 手动注册API处理器
  assistantAgent.apiRoutes.set("/help", async (requestData: any, request: any) => {
    return {
      message: "我是智能助手，可以帮助您解决各种问题",
      features: ["问答", "计算", "天气查询", "任务管理"],
      usage: "直接发送消息或调用API接口"
    };
  });
  
  // 手动注册消息处理器
  assistantAgent.messageHandlers.set("help", async (msgData: any) => {
    return {
      reply: "您好！我是智能助手，有什么可以帮助您的吗？",
      commands: ["/help - 显示帮助", "/status - 查看状态"]
    };
  });
  
  logger.debug(`✅ 创建助手Agent: ${assistantAgent.name}`);
  
  // 创建共享Agent
  const sharedAgent = createSharedAgent({
    name: "共享服务",
    description: "提供共享服务功能", 
    did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    prefix: "shared",
    primaryAgent: false
  });
  
  logger.debug(`✅ 创建共享Agent: ${sharedAgent.name}`);
}

// ===== 示例3: 批量创建Agent系统 =====

async function createAgentSystem(): Promise<void> {
  logger.debug("=== 批量Agent系统创建示例 ===");
  
  // 定义Agent配置字典（模拟Python的agent_dict）
  const agentDict = {
    "计算器服务": {
      description: "数学计算服务",
      shared: false,
      primaryAgent: true,
      did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
      version: "1.0.0",
      tags: ["math", "calculator"]
    },
    "天气服务": {
      description: "天气查询服务",
      shared: true,
      prefix: "weather",
      primaryAgent: false,
      did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
      version: "1.0.0", 
      tags: ["weather", "forecast"]
    },
    "翻译服务": {
      description: "多语言翻译服务",
      shared: true,
      prefix: "translate",
      primaryAgent: false,
      did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
      version: "1.0.0",
      tags: ["translate", "language"]
    }
  };
  
  // 使用createAgentsWithCode创建Agent系统
  const { agents, manager } = await createAgentsWithCode(
    agentDict,
    "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973"
  );
  
  logger.debug(`✅ 批量创建完成，共${agents.length}个Agent`);
  
  // 显示Agent统计信息
  const stats = manager.getStats();
  logger.debug("Agent系统统计:", stats);
}

// ===== 示例4: 全局消息管理器使用 =====

function demonstrateGlobalMessageManager(): void {
  logger.debug("=== 全局消息管理器示例 ===");
  
  // 清除现有处理器
  GlobalMessageManager.clearHandlers();
  
  // 添加全局消息处理器
  GlobalMessageManager.addHandler("system", async (msgData: any) => {
    logger.debug(`系统消息处理: ${JSON.stringify(msgData)}`);
  });
  
  GlobalMessageManager.addHandler("user", async (msgData: any) => {
    logger.debug(`用户消息处理: ${JSON.stringify(msgData)}`);
  });
  
  // 列出所有处理器
  const handlerStats = GlobalMessageManager.listHandlers();
  logger.debug("消息处理器统计:", handlerStats);
  
  // 获取特定类型的处理器
  const systemHandlers = GlobalMessageManager.getHandlers("system");
  logger.debug(`系统消息处理器数量: ${systemHandlers.length}`);
}

// ===== 主函数 =====

async function main(): Promise<void> {
  try {
    logger.debug("🚀 开始类型安全装饰器示例");
    
    // 1. 类装饰器方式
    logger.debug("\n=== 类装饰器方式 ===");
    const calcAgent = new CalculatorAgent().agent;
    const weatherAgent = new WeatherAgent().agent;
    
    logger.debug(`计算器Agent: ${calcAgent.name}`);
    logger.debug(`天气Agent: ${weatherAgent.name}`);
    
    // 2. 函数式创建方式
    await createFunctionalAgents();
    
    // 3. 批量创建Agent系统
    await createAgentSystem();
    
    // 4. 全局消息管理器
    demonstrateGlobalMessageManager();
    
    // 5. 显示最终统计
    logger.debug("\n=== 最终统计 ===");
    const finalStats = AgentManager.getStats();
    logger.debug("Agent管理器统计:", finalStats);
    
    const allAgents = AgentManager.getAllAgentInstances();
    logger.debug(`总Agent数量: ${allAgents.length}`);
    
    for (const agent of allAgents) {
      logger.debug(`  - ${agent.name} (DID: ${agent.anpUser.id})`);
    }
    
    logger.debug("✅ 类型安全装饰器示例完成");
    
  } catch (error) {
    logger.error("❌ 示例执行失败:", error);
    throw error;
  }
}

// 导出主函数供测试使用
export { main as runTypeSafeDecoratorsExample };

// 如果直接运行此文件
if (require.main === module) {
  main().catch(console.error);
}