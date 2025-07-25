/**
 * 函数式Agent创建方法
 * 避免TypeScript装饰器的复杂性，提供简洁的API
 */

import { Agent, AgentOptions } from '../core/agent';
import { AgentManager } from '../core/agent-manager';
import { ANPUser } from '@foundation/user';
import { getUserDataManager } from '@foundation/user';

// ===== 类型定义 =====
export interface ApiHandlerConfig {
  path: string;
  handler: (requestData: any, request: any) => Promise<any>;
  options?: {
    methods?: string[];
    description?: string;
    parameters?: Record<string, any>;
    returns?: string;
  };
}

export interface MessageHandlerConfig {
  messageType: string;
  handler: (msgData: any) => Promise<any>;
  options?: {
    description?: string;
    autoWrap?: boolean;
  };
}

export interface GroupEventHandlerConfig {
  groupId?: string;
  eventType?: string;
  handler: (eventData: any) => Promise<void>;
}

export interface AgentConfig {
  name: string;
  description?: string;
  version?: string;
  tags?: string[];
  did?: string;
  shared?: boolean;
  prefix?: string;
  primaryAgent?: boolean;
  apiHandlers?: ApiHandlerConfig[];
  messageHandlers?: MessageHandlerConfig[];
  groupEventHandlers?: GroupEventHandlerConfig[];
}

// ===== 核心Agent创建函数 =====

/**
 * 创建Agent的核心函数
 */
export function createAgentWithConfig(config: AgentConfig): Agent {
  // 获取DID
  let userDid = config.did;
  if (!userDid) {
    userDid = getFirstAvailableUser();
  }

  // 创建ANPUser
  const anpUser = ANPUser.fromDid(userDid);

  // 创建Agent
  const agent = AgentManager.createAgent(anpUser, {
    name: config.name,
    shared: config.shared || false,
    prefix: config.prefix,
    primaryAgent: config.primaryAgent || false
  });

  // 注册API处理器
  if (config.apiHandlers) {
    for (const apiConfig of config.apiHandlers) {
      agent.apiRoutes.set(apiConfig.path, apiConfig.handler);
    }
  }

  // 注册消息处理器
  if (config.messageHandlers) {
    for (const msgConfig of config.messageHandlers) {
      agent.messageHandlers.set(msgConfig.messageType, msgConfig.handler);
    }
  }

  // 注册群组事件处理器
  if (config.groupEventHandlers) {
    for (const groupConfig of config.groupEventHandlers) {
      const key = `${groupConfig.groupId || '*'}:${groupConfig.eventType || '*'}`;
      if (!agent.groupEventHandlers.has(key)) {
        agent.groupEventHandlers.set(key, []);
      }
      agent.groupEventHandlers.get(key)!.push(groupConfig.handler);
    }
  }

  return agent;
}

/**
 * 创建计算器Agent示例
 */
export function createCalculatorAgent(): Agent {
  return createAgentWithConfig({
    name: "计算器Agent",
    description: "提供基本数学计算功能",
    did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    shared: false,
    primaryAgent: true,
    apiHandlers: [
      {
        path: "/add",
        handler: async (requestData: any, request: any) => {
          const params = requestData.params || {};
          const a = params.a || 0;
          const b = params.b || 0;
          return { result: a + b, operation: "add" };
        },
        options: {
          description: "加法计算API",
          methods: ["POST"],
          parameters: { a: "number", b: "number" }
        }
      },
      {
        path: "/multiply",
        handler: async (requestData: any, request: any) => {
          const params = requestData.params || {};
          const a = params.a || 1;
          const b = params.b || 1;
          return { result: a * b, operation: "multiply" };
        },
        options: {
          description: "乘法计算API",
          methods: ["POST"]
        }
      }
    ],
    messageHandlers: [
      {
        messageType: "text",
        handler: async (msgData: any) => {
          const content = msgData.content || "";
          
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
        },
        options: {
          description: "处理文本消息",
          autoWrap: true
        }
      }
    ],
    groupEventHandlers: [
      {
        groupId: "calc_group",
        eventType: "join",
        handler: async (eventData: any) => {
          console.log(`用户加入计算群组: ${JSON.stringify(eventData)}`);
        }
      }
    ]
  });
}

/**
 * 创建天气Agent示例
 */
export function createWeatherAgent(): Agent {
  return createAgentWithConfig({
    name: "天气Agent",
    description: "提供天气查询服务",
    did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    shared: true,
    prefix: "weather",
    primaryAgent: false,
    apiHandlers: [
      {
        path: "/current",
        handler: async (requestData: any, request: any) => {
          const params = requestData.params || {};
          const city = params.city || "北京";
          
          return {
            city,
            temperature: Math.floor(Math.random() * 30) + 5,
            weather: ["晴", "多云", "阴", "小雨"][Math.floor(Math.random() * 4)],
            humidity: Math.floor(Math.random() * 50) + 30,
            timestamp: new Date().toISOString()
          };
        },
        options: {
          description: "获取当前天气",
          methods: ["GET", "POST"],
          parameters: { city: "string" }
        }
      },
      {
        path: "/forecast",
        handler: async (requestData: any, request: any) => {
          const params = requestData.params || {};
          const city = params.city || "北京";
          const days = params.days || 3;
          
          const forecast: any[] = [];
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
        },
        options: {
          description: "获取天气预报",
          methods: ["GET", "POST"],
          parameters: { city: "string", days: "number" }
        }
      }
    ],
    messageHandlers: [
      {
        messageType: "text",
        handler: async (msgData: any) => {
          const content = msgData.content || "";
          
          if (content.includes("天气")) {
            const cityMatch = content.match(/(.+?)天气/);
            const city = cityMatch ? cityMatch[1] : "北京";
            
            return {
              reply: `${city}今天天气晴朗，温度25°C，湿度60%`
            };
          }
          
          return { reply: "请询问天气相关问题" };
        }
      }
    ],
    groupEventHandlers: [
      {
        eventType: "weather_alert",
        handler: async (eventData: any) => {
          console.log(`收到天气预警: ${JSON.stringify(eventData)}`);
        }
      }
    ]
  });
}

/**
 * 批量创建Agent系统
 */
export async function createAgentSystem(
  agentConfigs: Record<string, Partial<AgentConfig>>,
  defaultDid?: string
): Promise<{ agents: Agent[], manager: typeof AgentManager }> {
  const agents: Agent[] = [];
  
  for (const [agentName, partialConfig] of Object.entries(agentConfigs)) {
    const fullConfig: AgentConfig = {
      name: agentName,
      did: defaultDid || partialConfig.did,
      ...partialConfig
    };
    
    const agent = createAgentWithConfig(fullConfig);
    agents.push(agent);
  }
  
  return {
    agents,
    manager: AgentManager
  };
}

/**
 * 全局消息管理器（简化版）
 */
export class GlobalMessageManager {
  private static instance: GlobalMessageManager;
  private messageHandlers = new Map<string, Function[]>();

  static getInstance(): GlobalMessageManager {
    if (!GlobalMessageManager.instance) {
      GlobalMessageManager.instance = new GlobalMessageManager();
    }
    return GlobalMessageManager.instance;
  }

  static addHandler(messageType: string, handler: Function): void {
    const instance = GlobalMessageManager.getInstance();
    if (!instance.messageHandlers.has(messageType)) {
      instance.messageHandlers.set(messageType, []);
    }
    instance.messageHandlers.get(messageType)!.push(handler);
  }

  static getHandlers(messageType: string): Function[] {
    const instance = GlobalMessageManager.getInstance();
    return instance.messageHandlers.get(messageType) || [];
  }

  static clearHandlers(): void {
    const instance = GlobalMessageManager.getInstance();
    instance.messageHandlers.clear();
  }

  static listHandlers(): Record<string, number> {
    const instance = GlobalMessageManager.getInstance();
    const result: Record<string, number> = {};
    for (const [messageType, handlers] of instance.messageHandlers) {
      result[messageType] = handlers.length;
    }
    return result;
  }
}

// ===== 工具函数 =====
function getFirstAvailableUser(): string {
  const userDataManager = getUserDataManager();
  const allUsers = userDataManager.getAllUsers();
  if (!allUsers || allUsers.length === 0) {
    throw new Error("系统中没有可用的用户");
  }
  return allUsers[0].did;
}

// ===== 导出 =====
export { AgentManager };

/**
 * 创建带代码的Agent系统（兼容Python版本）
 */
export async function createAgentsWithCode(
  agentDict: Record<string, any>,
  userDid?: string
): Promise<{ agents: Agent[], manager: typeof AgentManager }> {
  const agentConfigs: Record<string, Partial<AgentConfig>> = {};
  
  for (const [agentName, agentInfo] of Object.entries(agentDict)) {
    agentConfigs[agentName] = {
      description: agentInfo.description,
      shared: agentInfo.shared || false,
      prefix: agentInfo.prefix,
      primaryAgent: agentInfo.primaryAgent || false,
      version: agentInfo.version,
      tags: agentInfo.tags,
      did: userDid || agentInfo.did
    };
  }
  
  return createAgentSystem(agentConfigs, userDid);
}