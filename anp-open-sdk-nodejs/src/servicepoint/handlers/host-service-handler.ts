/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as path from 'path';
import * as fs from 'fs';
import { DomainManager } from '@foundation/domain';
import { getUserDataManager } from '@foundation/user';
import { getLogger } from '@foundation/utils';

const logger = getLogger('HostServiceHandler');

export interface HostServiceResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export interface HostedDidRequest {
  did: string;
  requestType: 'create' | 'update' | 'delete' | 'status';
  userData?: any;
  metadata?: Record<string, any>;
}

export interface HostedDidStatus {
  did: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  error?: string;
}

/**
 * 主机服务处理器
 * 对应Python版本的host_service_handler.py
 * 处理托管DID的创建、管理和状态查询
 */
export class HostServiceHandler {

  /**
   * 处理托管DID请求
   */
  public static async handleHostedDidRequest(
    request: HostedDidRequest,
    host: string,
    port: number
  ): Promise<HostServiceResponse> {
    try {
      // 验证域名访问权限
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 根据请求类型处理
      switch (request.requestType) {
        case 'create':
          return await this.createHostedDid(request, host, port);
        case 'update':
          return await this.updateHostedDid(request, host, port);
        case 'delete':
          return await this.deleteHostedDid(request, host, port);
        case 'status':
          return await this.getHostedDidStatus(request.did, host, port);
        default:
          return { success: false, error: `不支持的请求类型: ${request.requestType}` };
      }

    } catch (error) {
      logger.error(`托管DID请求处理失败: ${error}`);
      return { success: false, error: `托管DID请求处理失败: ${error}` };
    }
  }

  /**
   * 创建托管DID
   */
  private static async createHostedDid(
    request: HostedDidRequest,
    host: string,
    port: number
  ): Promise<HostServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const paths = domainManager.getAllDataPaths(host, port);

      // 确保托管DID队列目录存在
      const queuePath = paths.hosted_did_queue || path.join(paths.base_path, 'hosted_did_queue');
      if (!fs.existsSync(queuePath)) {
        fs.mkdirSync(queuePath, { recursive: true });
      }

      // 生成请求ID
      const requestId = this.generateRequestId();
      const queueFilePath = path.join(queuePath, `${requestId}.json`);

      // 创建托管DID请求记录
      const hostedDidRecord = {
        requestId,
        did: request.did,
        requestType: 'create',
        status: 'pending',
        userData: request.userData,
        metadata: request.metadata || {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        host: `${host}:${port}`
      };

      // 写入队列文件
      fs.writeFileSync(queueFilePath, JSON.stringify(hostedDidRecord, null, 2));

      logger.info(`托管DID创建请求已排队: ${request.did}, 请求ID: ${requestId}`);

      return {
        success: true,
        data: {
          requestId,
          did: request.did,
          status: 'pending',
          message: '托管DID创建请求已提交，正在处理中'
        }
      };

    } catch (error) {
      logger.error(`创建托管DID失败: ${error}`);
      return { success: false, error: `创建托管DID失败: ${error}` };
    }
  }

  /**
   * 更新托管DID
   */
  private static async updateHostedDid(
    request: HostedDidRequest,
    host: string,
    port: number
  ): Promise<HostServiceResponse> {
    try {
      // 检查托管DID是否存在
      const existingStatus = await this.getHostedDidStatus(request.did, host, port);
      if (!existingStatus.success) {
        return { success: false, error: '托管DID不存在' };
      }

      const domainManager = new DomainManager();
      const paths = domainManager.getAllDataPaths(host, port);

      // 生成更新请求ID
      const requestId = this.generateRequestId();
      const queuePath = paths.hosted_did_queue || path.join(paths.base_path, 'hosted_did_queue');
      const queueFilePath = path.join(queuePath, `${requestId}.json`);

      // 创建更新请求记录
      const updateRecord = {
        requestId,
        did: request.did,
        requestType: 'update',
        status: 'pending',
        userData: request.userData,
        metadata: request.metadata || {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        host: `${host}:${port}`
      };

      fs.writeFileSync(queueFilePath, JSON.stringify(updateRecord, null, 2));

      logger.info(`托管DID更新请求已排队: ${request.did}, 请求ID: ${requestId}`);

      return {
        success: true,
        data: {
          requestId,
          did: request.did,
          status: 'pending',
          message: '托管DID更新请求已提交，正在处理中'
        }
      };

    } catch (error) {
      logger.error(`更新托管DID失败: ${error}`);
      return { success: false, error: `更新托管DID失败: ${error}` };
    }
  }

  /**
   * 删除托管DID
   */
  private static async deleteHostedDid(
    request: HostedDidRequest,
    host: string,
    port: number
  ): Promise<HostServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const paths = domainManager.getAllDataPaths(host, port);

      // 生成删除请求ID
      const requestId = this.generateRequestId();
      const queuePath = paths.hosted_did_queue || path.join(paths.base_path, 'hosted_did_queue');
      const queueFilePath = path.join(queuePath, `${requestId}.json`);

      // 创建删除请求记录
      const deleteRecord = {
        requestId,
        did: request.did,
        requestType: 'delete',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        host: `${host}:${port}`
      };

      fs.writeFileSync(queueFilePath, JSON.stringify(deleteRecord, null, 2));

      logger.info(`托管DID删除请求已排队: ${request.did}, 请求ID: ${requestId}`);

      return {
        success: true,
        data: {
          requestId,
          did: request.did,
          status: 'pending',
          message: '托管DID删除请求已提交，正在处理中'
        }
      };

    } catch (error) {
      logger.error(`删除托管DID失败: ${error}`);
      return { success: false, error: `删除托管DID失败: ${error}` };
    }
  }

  /**
   * 获取托管DID状态
   */
  public static async getHostedDidStatus(
    did: string,
    host: string,
    port: number
  ): Promise<HostServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const paths = domainManager.getAllDataPaths(host, port);

      // 检查托管用户目录
      const hostedUserPath = paths.user_hosted_path;
      if (!fs.existsSync(hostedUserPath)) {
        return { success: false, error: '托管DID不存在' };
      }

      // 查找托管DID的状态文件
      const statusFiles = this.findHostedDidFiles(did, hostedUserPath);
      if (statusFiles.length === 0) {
        return { success: false, error: '托管DID不存在' };
      }

      // 读取最新的状态信息
      const latestStatusFile = statusFiles[statusFiles.length - 1];
      const statusData = JSON.parse(fs.readFileSync(latestStatusFile, 'utf8'));

      const status: HostedDidStatus = {
        did,
        status: statusData.status || 'unknown',
        created_at: statusData.created_at || '',
        updated_at: statusData.updated_at || '',
        error: statusData.error
      };

      return { success: true, data: status };

    } catch (error) {
      logger.error(`获取托管DID状态失败: ${error}`);
      return { success: false, error: `获取托管DID状态失败: ${error}` };
    }
  }

  /**
   * 获取所有托管DID列表
   */
  public static async getAllHostedDids(host: string, port: number): Promise<HostServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      const paths = domainManager.getAllDataPaths(host, port);
      const hostedUserPath = paths.user_hosted_path;

      if (!fs.existsSync(hostedUserPath)) {
        return { success: true, data: { hostedDids: [], count: 0 } };
      }

      // 扫描托管用户目录
      const hostedDids: any[] = [];
      const userDirs = fs.readdirSync(hostedUserPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);

      for (const userDir of userDirs) {
        const userPath = path.join(hostedUserPath, userDir);
        const didFiles = fs.readdirSync(userPath)
          .filter(file => file.endsWith('.json'));

        for (const didFile of didFiles) {
          try {
            const didFilePath = path.join(userPath, didFile);
            const didData = JSON.parse(fs.readFileSync(didFilePath, 'utf8'));
            
            hostedDids.push({
              did: didData.did || didFile.replace('.json', ''),
              userDir,
              status: didData.status || 'active',
              created_at: didData.created_at,
              updated_at: didData.updated_at
            });
          } catch (error) {
            logger.warn(`读取托管DID文件失败: ${didFile}, 错误: ${error}`);
          }
        }
      }

      return {
        success: true,
        data: {
          hostedDids,
          count: hostedDids.length,
          domain: `${host}:${port}`
        }
      };

    } catch (error) {
      logger.error(`获取托管DID列表失败: ${error}`);
      return { success: false, error: `获取托管DID列表失败: ${error}` };
    }
  }

  /**
   * 处理托管DID队列
   * 这个方法应该由后台任务定期调用
   */
  public static async processHostedDidQueue(host: string, port: number): Promise<HostServiceResponse> {
    try {
      const domainManager = new DomainManager();
      const paths = domainManager.getAllDataPaths(host, port);

      const queuePath = paths.hosted_did_queue || path.join(paths.base_path, 'hosted_did_queue');
      if (!fs.existsSync(queuePath)) {
        return { success: true, data: { processed: 0, message: '队列为空' } };
      }

      // 获取队列中的所有请求
      const queueFiles = fs.readdirSync(queuePath)
        .filter(file => file.endsWith('.json'))
        .sort(); // 按文件名排序，确保按时间顺序处理

      let processedCount = 0;
      const results: any[] = [];

      for (const queueFile of queueFiles) {
        try {
          const queueFilePath = path.join(queuePath, queueFile);
          const requestData = JSON.parse(fs.readFileSync(queueFilePath, 'utf8'));

          // 处理请求
          const result = await this.processHostedDidQueueItem(requestData, host, port);
          results.push(result);

          if (result.success) {
            // 移动到结果目录
            const resultsPath = paths.hosted_did_results || path.join(paths.base_path, 'hosted_did_results');
            await this.moveToResults(queueFilePath, requestData, resultsPath);
            processedCount++;
          }

        } catch (error) {
          logger.error(`处理队列项失败: ${queueFile}, 错误: ${error}`);
        }
      }

      return {
        success: true,
        data: {
          processed: processedCount,
          total: queueFiles.length,
          results
        }
      };

    } catch (error) {
      logger.error(`处理托管DID队列失败: ${error}`);
      return { success: false, error: `处理托管DID队列失败: ${error}` };
    }
  }

  /**
   * 处理单个队列项
   */
  private static async processHostedDidQueueItem(requestData: any, host: string, port: number): Promise<any> {
    try {
      // TODO: 实现实际的托管DID处理逻辑
      // 这里应该包括：
      // 1. 创建DID文档
      // 2. 生成密钥对
      // 3. 设置用户数据结构
      // 4. 更新状态

      logger.info(`处理托管DID请求: ${requestData.did}, 类型: ${requestData.requestType}`);

      // 模拟处理延迟
      await new Promise(resolve => setTimeout(resolve, 100));

      return {
        success: true,
        requestId: requestData.requestId,
        did: requestData.did,
        status: 'completed',
        message: '托管DID处理完成'
      };

    } catch (error) {
      return {
        success: false,
        requestId: requestData.requestId,
        did: requestData.did,
        status: 'failed',
        error: `处理失败: ${error}`
      };
    }
  }

  /**
   * 将处理完成的请求移动到结果目录
   */
  private static async moveToResults(queueFilePath: string, requestData: any, resultsPath: string): Promise<void> {
    try {
      if (!fs.existsSync(resultsPath)) {
        fs.mkdirSync(resultsPath, { recursive: true });
      }

      const fileName = path.basename(queueFilePath);
      const resultFilePath = path.join(resultsPath, fileName);

      // 更新状态和时间戳
      requestData.status = 'completed';
      requestData.updated_at = new Date().toISOString();

      // 写入结果文件
      fs.writeFileSync(resultFilePath, JSON.stringify(requestData, null, 2));

      // 删除队列文件
      fs.unlinkSync(queueFilePath);

    } catch (error) {
      logger.error(`移动结果文件失败: ${error}`);
      throw error;
    }
  }

  /**
   * 查找托管DID相关文件
   */
  private static findHostedDidFiles(did: string, hostedUserPath: string): string[] {
    const files: string[] = [];
    
    try {
      if (!fs.existsSync(hostedUserPath)) {
        return files;
      }

      const userDirs = fs.readdirSync(hostedUserPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);

      for (const userDir of userDirs) {
        const userPath = path.join(hostedUserPath, userDir);
        const didFiles = fs.readdirSync(userPath)
          .filter(file => file.includes(did) || file.endsWith('.json'))
          .map(file => path.join(userPath, file));
        
        files.push(...didFiles);
      }

    } catch (error) {
      logger.warn(`查找托管DID文件失败: ${error}`);
    }

    return files;
  }

  /**
   * 生成请求ID
   */
  private static generateRequestId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `hosted_${timestamp}_${random}`;
  }
}