/**
 * 函数式Agent创建完整示例
 * 避免装饰器问题，使用纯函数式API
 */

import {
  createAgentWithConfig,
  createCalculatorAgent,
  createWeatherAgent,
  createAgentSystem,
  createAgentsWithCode,
  GlobalMessageManager,
  AgentManager,
  type AgentConfig,
  type ApiHandlerConfig,
  type MessageHandlerConfig,
  type GroupEventHandlerConfig
} from '../src/runtime/decorators/functional-approach';

// 模拟logger
const logger = {
  debug: (msg: string, ...args: any[]) => console.log(`[DEBUG] ${msg}`, ...args),
  info: (msg: string, ...args: any[]) => console.log(`[INFO] ${msg}`, ...args),
  error: (msg: string, ...args: any[]) => console.error(`[ERROR] ${msg}`, ...args)
};

// ===== 示例1: 使用预定义的Agent创建函数 =====

function demonstratePrebuiltAgents(): void {
  logger.debug("=== 预定义Agent示例 ===");
  
  // 创建计算器Agent
  const calcAgent = createCalculatorAgent();
  logger.debug(`✅ 创建计算器Agent: ${calcAgent.name}`);
  logger.debug(`   API路由数量: ${calcAgent.apiRoutes.size}`);
  logger.debug(`   消息处理器数量: ${calcAgent.messageHandlers.size}`);
  
  // 创建天气Agent
  const weatherAgent = createWeatherAgent();
  logger.debug(`✅ 创建天气Agent: ${weatherAgent.name}`);
  logger.debug(`   API路由数量: ${weatherAgent.apiRoutes.size}`);
  logger.debug(`   消息处理器数量: ${weatherAgent.messageHandlers.size}`);
}

// ===== 示例2: 使用配置对象创建自定义Agent =====

function demonstrateCustomAgentCreation(): void {
  logger.debug("=== 自定义Agent创建示例 ===");
  
  // 定义智能助手Agent配置
  const assistantConfig: AgentConfig = {
    name: "智能助手",
    description: "通用智能助手服务",
    did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    shared: false,
    primaryAgent: true,
    version: "1.0.0",
    tags: ["assistant", "ai", "helper"],
    
    // API处理器配置
    apiHandlers: [
      {
        path: "/help",
        handler: async (requestData: any, request: any) => {
          return {
            message: "我是智能助手，可以帮助您解决各种问题",
            features: ["问答", "计算", "天气查询", "任务管理"],
            usage: "直接发送消息或调用API接口",
            version: "1.0.0"
          };
        },
        options: {
          description: "获取帮助信息",
          methods: ["GET", "POST"],
          returns: "帮助信息对象"
        }
      },
      {
        path: "/status",
        handler: async (requestData: any, request: any) => {
          const stats = AgentManager.getStats();
          return {
            status: "运行中",
            uptime: Date.now(),
            agentStats: stats,
            systemInfo: {
              nodeVersion: process.version,
              platform: process.platform,
              memory: process.memoryUsage()
            }
          };
        },
        options: {
          description: "获取系统状态",
          methods: ["GET"]
        }
      }
    ],
    
    // 消息处理器配置
    messageHandlers: [
      {
        messageType: "help",
        handler: async (msgData: any) => {
          return {
            reply: "您好！我是智能助手，有什么可以帮助您的吗？",
            commands: [
              "/help - 显示帮助",
              "/status - 查看状态",
              "计算 - 发送数学表达式进行计算",
              "天气 - 询问天气信息"
            ]
          };
        },
        options: {
          description: "处理帮助请求",
          autoWrap: true
        }
      },
      {
        messageType: "text",
        handler: async (msgData: any) => {
          const content = msgData.content || "";
          
          // 智能回复逻辑
          if (content.includes("你好") || content.includes("hello")) {
            return { reply: "您好！很高兴为您服务！" };
          }
          
          if (content.includes("时间")) {
            return { reply: `当前时间是: ${new Date().toLocaleString()}` };
          }
          
          if (content.includes("帮助")) {
            return { 
              reply: "我可以帮助您进行计算、查询天气、回答问题等。请告诉我您需要什么帮助？" 
            };
          }
          
          return { 
            reply: `收到您的消息: "${content}"。如需帮助，请发送"帮助"。` 
          };
        }
      }
    ],
    
    // 群组事件处理器配置
    groupEventHandlers: [
      {
        groupId: "assistant_group",
        eventType: "join",
        handler: async (eventData: any) => {
          logger.debug(`新用户加入助手群组: ${JSON.stringify(eventData)}`);
          // 可以发送欢迎消息等
        }
      },
      {
        eventType: "system_alert",
        handler: async (eventData: any) => {
          logger.debug(`收到系统警报: ${JSON.stringify(eventData)}`);
          // 处理系统级别的警报
        }
      }
    ]
  };
  
  // 创建智能助手Agent
  const assistantAgent = createAgentWithConfig(assistantConfig);
  logger.debug(`✅ 创建智能助手Agent: ${assistantAgent.name}`);
  logger.debug(`   DID: ${assistantAgent.anpUser.id}`);
  logger.debug(`   API路由: ${Array.from(assistantAgent.apiRoutes.keys()).join(', ')}`);
  logger.debug(`   消息类型: ${Array.from(assistantAgent.messageHandlers.keys()).join(', ')}`);
}

// ===== 示例3: 批量创建Agent系统 =====

async function demonstrateBatchAgentCreation(): Promise<void> {
  logger.debug("=== 批量Agent创建示例 ===");
  
  // 定义多个Agent的配置
  const agentConfigs = {
    "数据分析Agent": {
      description: "提供数据分析和可视化服务",
      shared: true,
      prefix: "data",
      primaryAgent: false,
      tags: ["data", "analysis", "visualization"],
      apiHandlers: [
        {
          path: "/analyze",
          handler: async (requestData: any, request: any) => {
            const data = requestData.data || [];
            return {
              summary: {
                count: data.length,
                average: data.reduce((a: number, b: number) => a + b, 0) / data.length || 0,
                max: Math.max(...data),
                min: Math.min(...data)
              },
              timestamp: new Date().toISOString()
            };
          },
          options: {
            description: "分析数据集",
            methods: ["POST"],
            parameters: { data: "number[]" }
          }
        }
      ]
    },
    
    "文件管理Agent": {
      description: "提供文件操作和管理服务",
      shared: true,
      prefix: "file",
      primaryAgent: false,
      tags: ["file", "storage", "management"],
      apiHandlers: [
        {
          path: "/list",
          handler: async (requestData: any, request: any) => {
            const path = requestData.path || "/";
            return {
              path,
              files: [
                { name: "document1.txt", size: 1024, type: "file" },
                { name: "folder1", size: 0, type: "directory" },
                { name: "image.png", size: 2048, type: "file" }
              ],
              timestamp: new Date().toISOString()
            };
          },
          options: {
            description: "列出目录内容",
            methods: ["GET", "POST"],
            parameters: { path: "string" }
          }
        }
      ]
    },
    
    "通知Agent": {
      description: "提供消息通知和推送服务",
      shared: false,
      primaryAgent: false,
      tags: ["notification", "messaging", "push"],
      messageHandlers: [
        {
          messageType: "notification",
          handler: async (msgData: any) => {
            const { title, content, priority } = msgData;
            logger.info(`📢 通知: ${title} - ${content} (优先级: ${priority || 'normal'})`);
            return { 
              reply: "通知已处理",
              notificationId: `notif_${Date.now()}`
            };
          }
        }
      ]
    }
  };
  
  // 批量创建Agent
  const { agents, manager } = await createAgentSystem(
    agentConfigs,
    "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973"
  );
  
  logger.debug(`✅ 批量创建完成，共创建${agents.length}个Agent:`);
  for (const agent of agents) {
    logger.debug(`   - ${agent.name} (API: ${agent.apiRoutes.size}, 消息: ${agent.messageHandlers.size})`);
  }
  
  // 显示系统统计
  const stats = manager.getStats();
  logger.debug("系统统计:", stats);
}

// ===== 示例4: 兼容Python版本的创建方式 =====

async function demonstratePythonCompatibleCreation(): Promise<void> {
  logger.debug("=== Python兼容创建示例 ===");
  
  // 模拟Python版本的agent_dict
  const agentDict = {
    "计算器服务": {
      description: "数学计算服务",
      shared: false,
      primaryAgent: true,
      version: "1.0.0",
      tags: ["math", "calculator"]
    },
    "天气服务": {
      description: "天气查询服务",
      shared: true,
      prefix: "weather",
      primaryAgent: false,
      version: "1.0.0",
      tags: ["weather", "forecast"]
    },
    "翻译服务": {
      description: "多语言翻译服务",
      shared: true,
      prefix: "translate",
      primaryAgent: false,
      version: "1.0.0",
      tags: ["translate", "language"]
    }
  };
  
  // 使用createAgentsWithCode创建（兼容Python版本）
  const { agents, manager } = await createAgentsWithCode(
    agentDict,
    "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973"
  );
  
  logger.debug(`✅ Python兼容创建完成，共${agents.length}个Agent`);
  
  // 显示详细信息
  const agentList = manager.listAgents();
  for (const [did, agentMap] of Object.entries(agentList)) {
    logger.debug(`DID: ${did}`);
    for (const [agentName, agentInfo] of Object.entries(agentMap)) {
      const mode = agentInfo.shared ? "共享" : "独占";
      const primary = agentInfo.primaryAgent ? " (主)" : "";
      const prefix = agentInfo.prefix ? ` prefix:${agentInfo.prefix}` : "";
      logger.debug(`  - ${agentName}: ${mode}${primary}${prefix}`);
    }
  }
}

// ===== 示例5: 全局消息管理器 =====

function demonstrateGlobalMessageManager(): void {
  logger.debug("=== 全局消息管理器示例 ===");
  
  // 清除现有处理器
  GlobalMessageManager.clearHandlers();
  
  // 添加全局消息处理器
  GlobalMessageManager.addHandler("system", async (msgData: any) => {
    logger.debug(`🔧 系统消息处理: ${JSON.stringify(msgData)}`);
  });
  
  GlobalMessageManager.addHandler("user", async (msgData: any) => {
    logger.debug(`👤 用户消息处理: ${JSON.stringify(msgData)}`);
  });
  
  GlobalMessageManager.addHandler("error", async (msgData: any) => {
    logger.error(`❌ 错误消息处理: ${JSON.stringify(msgData)}`);
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
    logger.debug("🚀 开始函数式Agent创建示例");
    
    // 1. 预定义Agent示例
    demonstratePrebuiltAgents();
    
    // 2. 自定义Agent创建
    demonstrateCustomAgentCreation();
    
    // 3. 批量创建Agent系统
    await demonstrateBatchAgentCreation();
    
    // 4. Python兼容创建方式
    await demonstratePythonCompatibleCreation();
    
    // 5. 全局消息管理器
    demonstrateGlobalMessageManager();
    
    // 6. 最终统计
    logger.debug("\n=== 最终系统统计 ===");
    const finalStats = AgentManager.getStats();
    logger.debug("Agent管理器统计:", finalStats);
    
    const allAgents = AgentManager.getAllAgentInstances();
    logger.debug(`总Agent数量: ${allAgents.length}`);
    
    for (const agent of allAgents) {
      logger.debug(`  - ${agent.name} (DID: ${agent.anpUser.id})`);
    }
    
    logger.debug("✅ 函数式Agent创建示例完成");
    
  } catch (error) {
    logger.error("❌ 示例执行失败:", error);
    throw error;
  }
}

// 导出主函数供测试使用
export { main as runFunctionalApproachExample };

// 如果直接运行此文件
if (require.main === module) {
  main().catch(console.error);
}