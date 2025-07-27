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
      const agent = AgentManager.getAgentByDid(did);
      
      if (!agent) {
        return res.status(404).json({ error: 'Agent not found' });
      }

      res.json(agent.toDict());
    });

    // Agent API调用端点
    this.app.all('/agents/:did/*', async (req: Request, res: Response) => {
      const { did } = req.params;
      const path = '/' + req.params[0];
      
      const agent = AgentManager.getAgentByDid(did);
      
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
