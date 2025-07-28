/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { Router, Request, Response } from 'express';
import { getAgentManager } from '../../runtime/core';
import { AgentServiceHandler } from '../../servicepoint/handlers';
import { getLogger } from '../../foundation/utils';
import { formatDidFromUrl } from '../../foundation/did/did-url-formatter';

const logger = getLogger('AnpRouters');

/**
 * 创建Agent相关路由
 */
export function createAgentRoutes(): Router {
  const router = Router();

  // 获取所有Agent列表
  router.get('/', (req: Request, res: Response) => {
    try {
      const agentManager = getAgentManager();
      const agents = agentManager.listAgents();
      res.json({
        success: true,
        data: agents,
        count: Object.keys(agents).length
      });
    } catch (error) {
      logger.error('获取Agent列表失败:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get agents list'
      });
    }
  });

  // 获取特定Agent信息
  router.get('/:did', (req: Request, res: Response) => {
    try {
      const { did } = req.params;
      
      // 使用统一的DID格式化函数
      const normalizedDid = formatDidFromUrl(did);
      logger.debug(`🔍 [Router] 获取Agent信息 - 原始DID: ${did}, 格式化后: ${normalizedDid}`);
      
      const agentManager = getAgentManager();
      const agent = agentManager.getAgentByDid(normalizedDid);
      
      if (!agent) {
        return res.status(404).json({
          success: false,
          error: 'Agent not found'
        });
      }

      res.json({
        success: true,
        data: agent.toDict()
      });
    } catch (error) {
      logger.error('获取Agent信息失败:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get agent info'
      });
    }
  });

  // 调用Agent API
  router.all('/:did/*', async (req: Request, res: Response) => {
    try {
      const { did } = req.params;
      const endpoint = '/' + req.params[0];
      
      // 使用统一的DID格式化函数
      const normalizedDid = formatDidFromUrl(did);
      logger.debug(`🔍 [Router] Agent API调用 - 原始DID: ${did}, 格式化后: ${normalizedDid}`);
      
      const result = await AgentServiceHandler.processAgentRequest(
        normalizedDid,
        endpoint,
        req.body
      );

      if (result.success) {
        res.json(result);
      } else {
        res.status(400).json(result);
      }
    } catch (error) {
      logger.error('Agent API调用失败:', error);
      res.status(500).json({
        success: false,
        error: 'Agent API call failed'
      });
    }
  });

  return router;
}

/**
 * 创建消息相关路由
 */
export function createMessageRoutes(): Router {
  const router = Router();

  // 接收消息
  router.post('/receive', async (req: Request, res: Response) => {
    try {
      const { targetDid, messageType, payload } = req.body;
      const callerDid = (req as any).auth?.callerDid;
      
      if (!targetDid || !messageType || !payload) {
        return res.status(400).json({
          success: false,
          error: 'Missing required fields: targetDid, messageType, payload'
        });
      }

      const agentManager = getAgentManager();
      const targetAgent = agentManager.getAgentByDid(targetDid);
      
      if (!targetAgent) {
        return res.status(404).json({
          success: false,
          error: 'Target agent not found'
        });
      }

      const result = await targetAgent.handleMessage(messageType, {
        ...payload,
        sender: callerDid,
        timestamp: new Date().toISOString()
      });

      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      logger.error('处理消息失败:', error);
      res.status(500).json({
        success: false,
        error: 'Message processing failed'
      });
    }
  });

  // 发送消息
  router.post('/send', async (req: Request, res: Response) => {
    try {
      const { targetDid, messageType, payload } = req.body;
      const callerDid = (req as any).auth?.callerDid;
      
      if (!targetDid || !messageType) {
        return res.status(400).json({
          success: false,
          error: 'Missing required fields: targetDid, messageType'
        });
      }

      // 这里应该实现实际的消息发送逻辑
      // 可能需要通过网络发送到其他节点
      
      res.json({
        success: true,
        data: {
          messageId: Date.now().toString(),
          sender: callerDid,
          target: targetDid,
          messageType,
          timestamp: new Date().toISOString()
        }
      });
    } catch (error) {
      logger.error('发送消息失败:', error);
      res.status(500).json({
        success: false,
        error: 'Message sending failed'
      });
    }
  });

  return router;
}

/**
 * 创建群组相关路由
 */
export function createGroupRoutes(): Router {
  const router = Router();

  // 群组操作
  router.post('/:groupId/:action', async (req: Request, res: Response) => {
    try {
      const { groupId, action } = req.params;
      const callerDid = (req as any).auth?.callerDid;
      
      if (!callerDid) {
        return res.status(401).json({
          success: false,
          error: 'Authentication required'
        });
      }

      const result = await AgentServiceHandler.processGroupRequest({
        did: callerDid,
        groupId,
        action,
        requestData: req.body,
        queryParams: req.query as Record<string, string>
      });

      if (result.success) {
        res.json(result);
      } else {
        res.status(400).json(result);
      }
    } catch (error) {
      logger.error('群组操作失败:', error);
      res.status(500).json({
        success: false,
        error: 'Group operation failed'
      });
    }
  });

  return router;
}

/**
 * 创建DID相关路由
 */
export function createDidRoutes(): Router {
  const router = Router();

  // 获取DID文档
  router.get('/:did', async (req: Request, res: Response) => {
    try {
      const { did } = req.params;
      
      // 使用统一的DID格式化函数
      const normalizedDid = formatDidFromUrl(did);
      logger.debug(`🔍 [Router] 获取DID文档 - 原始DID: ${did}, 格式化后: ${normalizedDid}`);
      
      const agentManager = getAgentManager();
      const agent = agentManager.getAgentByDid(normalizedDid);
      
      if (!agent) {
        return res.status(404).json({
          success: false,
          error: 'DID not found'
        });
      }

      // 返回DID文档（如果Agent有的话）
      // 这里需要实现从Agent获取DID文档的逻辑
      res.json({
        success: true,
        data: {
          '@context': [
            'https://www.w3.org/ns/did/v1',
            'https://w3id.org/security/suites/secp256k1-2019/v1'
          ],
          id: did,
          // 其他DID文档字段...
        }
      });
    } catch (error) {
      logger.error('获取DID文档失败:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get DID document'
      });
    }
  });

  return router;
}

/**
 * 创建发布者相关路由
 */
export function createPublisherRoutes(): Router {
  const router = Router();

  // 发布Agent信息
  router.get('/agents', (req: Request, res: Response) => {
    try {
      const agentManager = getAgentManager();
      const agents = agentManager.getAllAgents().map(agent => ({
        did: agent.anpUser.id,
        name: agent.name,
        apis: agent.getApis().map(api => ({
          path: api.path,
          method: api.method,
          description: api.description,
          public: api.public
        })),
        messageHandlers: agent.getMessageHandlers().map(handler => handler.eventType),
        groupEventHandlers: agent.getGroupEventHandlers().map(handler => handler.eventType)
      }));

      res.json({
        success: true,
        data: agents,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('获取发布者信息失败:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get publisher info'
      });
    }
  });

  return router;
}