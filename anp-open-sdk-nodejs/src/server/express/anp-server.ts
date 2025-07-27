/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import express, { Application, Request, Response } from 'express';
import { Agent } from '../../runtime/core/agent';
import { AgentManager } from '../../runtime/core/agent-manager';
import { 
  createAuthMiddleware, 
  corsMiddleware, 
  requestLogMiddleware 
} from '../../servicepoint/middleware';
import { AuthVerifier } from '../../foundation/auth';
import { getGlobalConfig } from '../../foundation/config';
import { getLogger } from '../../foundation/utils';
import { DIDServiceHandler } from '../../servicepoint/handlers/did-service-handler';
import { DomainManager } from '../../foundation/domain';

const logger = getLogger('AnpServer');

export interface ServerConfig {
  host?: string;
  port?: number;
  enableCors?: boolean;
  enableAuth?: boolean;
  enableLogging?: boolean;
}

export class AnpServer {
  private app: Application;
  private server: any;
  private authVerifier: AuthVerifier;
  private config: ServerConfig;

  constructor(config: ServerConfig = {}) {
    this.config = {
      host: config.host || 'localhost',
      port: config.port || 9527,
      enableCors: config.enableCors ?? true,
      enableAuth: config.enableAuth ?? true,
      enableLogging: config.enableLogging ?? true,
      ...config
    };

    this.app = express();
    this.authVerifier = new AuthVerifier();
    
    this.setupMiddleware();
    this.setupRoutes();
    
    logger.info(`AnpServer配置: ${JSON.stringify(this.config)}`);
  }

  /**
   * 设置中间件
   */
  private setupMiddleware(): void {
    // 基础中间件
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // CORS中间件
    if (this.config.enableCors) {
      this.app.use(corsMiddleware());
    }

    // 请求日志中间件
    if (this.config.enableLogging) {
      this.app.use(requestLogMiddleware());
    }

    // 认证中间件
    if (this.config.enableAuth) {
      const authMiddleware = createAuthMiddleware(this.authVerifier);
      this.app.use(authMiddleware.middleware());
    }
  }

  /**
   * 设置路由
   */
  private setupRoutes(): void {
    // DID服务路由 - 必须在认证中间件之前或者豁免认证
    this.setupDIDRoutes();

    // 添加路由调试日志中间件
    this.app.use((req: Request, res: Response, next) => {
      logger.debug(`🔍 [路由调试] ${req.method} ${req.path} - 查找匹配的路由`);
      if (req.path.startsWith('/agent/api/')) {
        logger.warn(`⚠️ [路由调试] 检测到 /agent/api/ 路径请求，但当前没有对应的路由配置！`);
        logger.warn(`⚠️ [路由调试] 请求详情: ${req.method} ${req.path}`);
        logger.warn(`⚠️ [路由调试] 查询参数: ${JSON.stringify(req.query)}`);
      }
      next();
    });

    // 健康检查端点
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
      });
    });

    // Agent状态端点
    this.app.get('/agents', (req: Request, res: Response) => {
      const agents = AgentManager.listAgents();
      res.json(agents);
    });

    // Agent详情端点
    this.app.get('/agents/:did', (req: Request, res: Response) => {
      const { did } = req.params;
      
      // 智能DID解码：解码一次后如果包含 %3A，就停止解码
      let decodedDid = decodeURIComponent(did);
      if (decodedDid.includes('%3A')) {
        // 使用包含 %3A 的格式，这与Agent注册时的格式一致
        logger.debug(`🔍 Agent详情 - 原始DID: ${did}, 解码后(包含%3A): ${decodedDid}`);
      } else {
        logger.debug(`🔍 Agent详情 - 原始DID: ${did}, 完全解码后: ${decodedDid}`);
      }
      
      const agent = AgentManager.getAgentByDid(decodedDid);
      
      if (!agent) {
        return res.status(404).json({ error: 'Agent not found' });
      }

      res.json(agent.toDict());
    });

    // Agent API调用端点
    this.app.all('/agents/:did/*', async (req: Request, res: Response) => {
      const { did } = req.params;
      const path = '/' + req.params[0];
      
      // 智能DID解码：解码一次后如果包含 %3A，就停止解码
      let decodedDid = decodeURIComponent(did);
      if (decodedDid.includes('%3A')) {
        // 使用包含 %3A 的格式，这与Agent注册时的格式一致
        logger.debug(`🔍 Agent API调用 - 原始DID: ${did}, 解码后(包含%3A): ${decodedDid}`);
      } else {
        logger.debug(`🔍 Agent API调用 - 原始DID: ${did}, 完全解码后: ${decodedDid}`);
      }
      
      const agent = AgentManager.getAgentByDid(decodedDid);
      
      if (!agent) {
        return res.status(404).json({ error: 'Agent not found' });
      }

      try {
        const requestData = {
          type: 'api_call',
          path: path,
          method: req.method,
          headers: req.headers,
          body: req.body,
          query: req.query,
          req_did: (req as any).auth?.callerDid || 'anonymous'
        };

        const response = await agent.handleRequest((req as any).auth?.callerDid || 'anonymous', requestData, req);
        
        if (response && typeof response === 'object' && 'status' in response) {
          res.status(response.status);
          if (response.headers) {
            Object.entries(response.headers).forEach(([key, value]) => {
              res.setHeader(key, String(value));
            });
          }
          res.json(response.body);
        } else {
          res.json(response);
        }

      } catch (error) {
        logger.error(`Agent API调用失败: ${did}${path}:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // 添加 /agent/api/ 路径支持 - 修复404错误
    this.setupAgentApiRoutes();

    // 动态路由处理（基于Agent prefix）
    this.app.all('*', async (req: Request, res: Response) => {
      const agent = AgentManager.findAgentByPathPrefix(req.path);
      
      if (!agent) {
        return res.status(404).json({ error: 'Route not found' });
      }

      try {
        const prefixLength = agent.prefix ? agent.prefix.length : 0;
        const requestData = {
          type: 'api_call',
          path: req.path.substring(prefixLength),
          method: req.method,
          headers: req.headers,
          body: req.body,
          query: req.query,
          req_did: (req as any).auth?.callerDid || 'anonymous'
        };

        const response = await agent.handleRequest((req as any).auth?.callerDid || 'anonymous', requestData, req);
        
        if (response && typeof response === 'object' && 'status' in response) {
          res.status(response.status);
          if (response.headers) {
            Object.entries(response.headers).forEach(([key, value]) => {
              res.setHeader(key, String(value));
            });
          }
          res.json(response.body);
        } else {
          res.json(response);
        }

      } catch (error) {
        logger.error(`动态路由处理失败: ${req.path}:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });
  }

  /**
   * 设置DID服务路由
   */
  private setupDIDRoutes(): void {
    const domainManager = new DomainManager();

    // DID文档端点: /wba/user/{user_id}/did.json
    this.app.get('/wba/user/:userId/did.json', async (req: Request, res: Response) => {
      try {
        const { userId } = req.params;
        const host = req.hostname || 'localhost';
        const port = this.config.port || 9527;

        logger.debug(`DID文档请求: userId=${userId}, host=${host}, port=${port}`);

        const result = await DIDServiceHandler.getDidDocument(userId, host, port);
        
        if (result.success) {
          res.json(result.data);
        } else {
          logger.warn(`DID文档获取失败: ${result.error}`);
          res.status(404).json({ error: result.error });
        }
      } catch (error) {
        logger.error(`DID文档端点错误:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Agent描述端点: /wba/user/{user_id}/ad.json
    this.app.get('/wba/user/:userId/ad.json', async (req: Request, res: Response) => {
      try {
        const { userId } = req.params;
        const host = req.hostname || 'localhost';
        const port = this.config.port || 9527;

        logger.debug(`Agent描述请求: userId=${userId}, host=${host}, port=${port}`);

        const result = await DIDServiceHandler.getAgentDescription(userId, host, port);
        
        if (result.success) {
          res.json(result.data);
        } else {
          logger.warn(`Agent描述获取失败: ${result.error}`);
          res.status(404).json({ error: result.error });
        }
      } catch (error) {
        logger.error(`Agent描述端点错误:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Agent YAML文件端点: /wba/user/{resp_did}/{yaml_file_name}.yaml
    this.app.get('/wba/user/:respDid/:yamlFileName.yaml', async (req: Request, res: Response) => {
      try {
        const { respDid, yamlFileName } = req.params;
        const host = req.hostname || 'localhost';
        const port = this.config.port || 9527;

        logger.debug(`Agent YAML请求: respDid=${respDid}, yamlFileName=${yamlFileName}, host=${host}, port=${port}`);

        const result = await DIDServiceHandler.getAgentYamlFile(respDid, yamlFileName, host, port);
        
        if (result.success) {
          res.setHeader('Content-Type', 'application/x-yaml');
          res.send(result.data);
        } else {
          logger.warn(`Agent YAML获取失败: ${result.error}`);
          res.status(404).json({ error: result.error });
        }
      } catch (error) {
        logger.error(`Agent YAML端点错误:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    // Agent JSON文件端点: /wba/user/{resp_did}/{json_file_name}.json
    this.app.get('/wba/user/:respDid/:jsonFileName.json', async (req: Request, res: Response) => {
      try {
        const { respDid, jsonFileName } = req.params;
        const host = req.hostname || 'localhost';
        const port = this.config.port || 9527;

        logger.debug(`Agent JSON请求: respDid=${respDid}, jsonFileName=${jsonFileName}, host=${host}, port=${port}`);

        const result = await DIDServiceHandler.getAgentJsonFile(respDid, jsonFileName, host, port);
        
        if (result.success) {
          res.json(result.data);
        } else {
          logger.warn(`Agent JSON获取失败: ${result.error}`);
          res.status(404).json({ error: result.error });
        }
      } catch (error) {
        logger.error(`Agent JSON端点错误:`, error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    logger.info('DID服务路由已注册');
  }

  /**
   * 设置Agent API路由 - 修复 /agent/api/ 路径404错误
   */
  private setupAgentApiRoutes(): void {
    // Agent API通用路由: /agent/api/{did}/{subpath}
    this.app.all('/agent/api/:did/*', async (req: Request, res: Response) => {
      const { did } = req.params;
      const subpath = req.params[0] || '';
      const fullPath = '/' + subpath;
      
      logger.debug(`🔄 处理Agent API请求: /agent/api/${did}${fullPath}`);
      
      // 智能DID解码：解码一次后如果包含 %3A，就停止解码
      let decodedDid = decodeURIComponent(did);
      
      // 如果解码后包含 %3A，说明这是正确的格式，不需要进一步解码
      if (decodedDid.includes('%3A')) {
        // 使用包含 %3A 的格式，这与Agent注册时的格式一致
        logger.debug(`🔍 原始DID参数: ${did}`);
        logger.debug(`🔍 解码后的DID (包含%3A): ${decodedDid}`);
      } else {
        // 如果解码后不包含 %3A，使用解码后的结果
        logger.debug(`🔍 原始DID参数: ${did}`);
        logger.debug(`🔍 完全解码后的DID: ${decodedDid}`);
      }
      
      // 调试：列出所有已注册的Agent DID
      const allAgents = AgentManager.getAllAgents();
      logger.debug(`🔍 已注册的Agent数量: ${allAgents.length}`);
      for (const agent of allAgents) {
        logger.debug(`🔍 已注册Agent DID: ${agent.anpUser.id}`);
      }
      
      const agent = AgentManager.getAgentByDid(decodedDid);
      
      if (!agent) {
        logger.warn(`❌ Agent未找到: ${decodedDid}`);
        return res.status(404).json({
          error: 'Agent not found',
          did: decodedDid,
          originalDid: did
        });
      }

      try {
        const callerDid = (req as any).auth?.callerDid || req.query.req_did || 'anonymous';
        
        const requestData = {
          type: 'api_call',
          path: fullPath,
          method: req.method,
          headers: req.headers,
          body: req.body,
          query: req.query,
          req_did: callerDid
        };

        logger.debug(`📤 发送请求到Agent: ${decodedDid}, 路径: ${fullPath}, 调用者: ${callerDid}`);
        
        const response = await agent.handleRequest(callerDid, requestData, req);
        
        if (response && typeof response === 'object' && 'status' in response) {
          res.status(response.status);
          if (response.headers) {
            Object.entries(response.headers).forEach(([key, value]) => {
              res.setHeader(key, String(value));
            });
          }
          res.json(response.body);
        } else {
          res.json(response);
        }

        logger.debug(`✅ Agent API请求处理成功: ${decodedDid}${fullPath}`);

      } catch (error) {
        logger.error(`❌ Agent API请求处理失败: ${decodedDid}${fullPath}:`, error);
        res.status(500).json({
          error: 'Internal server error',
          message: error instanceof Error ? error.message : String(error)
        });
      }
    });

    // 特定的add端点路由: /agent/api/{did}/add
    this.app.all('/agent/api/:did/add', async (req: Request, res: Response) => {
      const { did } = req.params;
      
      logger.debug(`🔄 处理Agent连接添加请求: /agent/api/${did}/add`);
      
      // 智能DID解码：解码一次后如果包含 %3A，就停止解码
      let decodedDid = decodeURIComponent(did);
      
      // 如果解码后包含 %3A，说明这是正确的格式，不需要进一步解码
      if (decodedDid.includes('%3A')) {
        // 使用包含 %3A 的格式，这与Agent注册时的格式一致
        logger.debug(`🔍 Agent连接添加 - 原始DID: ${did}, 解码后(包含%3A): ${decodedDid}`);
      } else {
        // 如果解码后不包含 %3A，使用解码后的结果
        logger.debug(`🔍 Agent连接添加 - 原始DID: ${did}, 完全解码后: ${decodedDid}`);
      }
      const agent = AgentManager.getAgentByDid(decodedDid);
      
      if (!agent) {
        logger.warn(`❌ Agent未找到 (add请求): ${decodedDid}`);
        return res.status(404).json({
          error: 'Agent not found for add request',
          did: decodedDid,
          originalDid: did
        });
      }

      try {
        const callerDid = (req as any).auth?.callerDid || req.query.req_did || 'anonymous';
        const respDid = req.query.resp_did || decodedDid;
        
        const requestData = {
          type: 'agent_connect',
          action: 'add',
          method: req.method,
          headers: req.headers,
          body: req.body,
          query: req.query,
          req_did: callerDid,
          resp_did: respDid
        };

        logger.debug(`📤 发送连接添加请求到Agent: ${decodedDid}, 调用者: ${callerDid}, 响应者: ${respDid}`);
        
        const response = await agent.handleRequest(callerDid, requestData, req);
        
        // 返回成功响应
        res.json({
          success: true,
          action: 'add',
          req_did: callerDid,
          resp_did: respDid,
          data: response
        });

        logger.debug(`✅ Agent连接添加请求处理成功: ${decodedDid}`);

      } catch (error) {
        logger.error(`❌ Agent连接添加请求处理失败: ${decodedDid}:`, error);
        res.status(500).json({
          error: 'Agent connect add failed',
          message: error instanceof Error ? error.message : String(error)
        });
      }
    });

    logger.info('Agent API路由已注册 (/agent/api/)');
  }

  /**
   * 注册Agent
   */
  public registerAgent(agent: Agent): void {
    // Agent已经通过AgentManager.createAgent创建并注册，这里只是日志记录
    logger.info(`Agent注册到服务器: ${agent.name} (${agent.anpUser.id})`);
  }

  /**
   * 批量注册Agent
   */
  public registerAgents(agents: Agent[]): void {
    agents.forEach(agent => this.registerAgent(agent));
  }

  /**
   * 注册DID文档到认证验证器
   * TODO: 实现DID文档注册功能
   */
  public registerDIDDocument(did: string, didDocument: any): void {
    // AuthVerifier 目前不支持直接注册DID文档
    // 这个功能需要在未来版本中实现
    logger.info(`DID文档注册请求: ${did} (暂未实现)`);
  }

  /**
   * 获取Express应用实例
   */
  public getExpressApp(): Application {
    return this.app;
  }

  /**
   * 启动服务器
   */
  public async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const port = this.config.port!; // 使用非空断言，因为构造函数中已经设置了默认值
        const host = this.config.host!; // 使用非空断言，因为构造函数中已经设置了默认值
        
        this.server = this.app.listen(port, host, () => {
          logger.info(`🚀 ANP服务器启动成功: http://${host}:${port}`);
          resolve();
        });

        this.server.on('error', (error: any) => {
          logger.error('服务器启动失败:', error);
          reject(error);
        });
      } catch (error) {
        logger.error('服务器启动错误:', error);
        reject(error);
      }
    });
  }

  /**
   * 停止服务器
   */
  public async stop(): Promise<void> {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          logger.info('ANP服务器已停止');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }

  /**
   * 优雅关闭
   */
  public async gracefulShutdown(): Promise<void> {
    logger.info('开始优雅关闭服务器...');
    
    // 停止接受新连接
    await this.stop();
    
    // 给正在处理的请求一些时间完成
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    logger.info('服务器优雅关闭完成');
  }

  /**
   * 获取服务器统计信息
   */
  public getStats(): {
    config: ServerConfig;
    agents: number;
    uptime: number;
  } {
    return {
      config: this.config,
      agents: AgentManager.getAllAgents().length,
      uptime: process.uptime()
    };
  }
}
