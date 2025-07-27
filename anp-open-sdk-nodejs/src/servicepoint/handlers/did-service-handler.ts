/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { DomainManager } from '../../foundation/domain';
import { findUserByDid } from '../../foundation/did';
import { getLogger } from '../../foundation/utils';

const logger = getLogger('DIDServiceHandler');

export interface DIDServiceResponse {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * DID服务处理器
 * 对应Python版本的did_service_handler.py
 */
export class DIDServiceHandler {
  
  /**
   * 格式化用户ID为标准DID格式
   */
  public static formatDidFromUserId(userId: string, host: string, port: number): string {
    const decodedUserId = decodeURIComponent(userId);

    if (decodedUserId.startsWith("did:wba")) {
      // 处理已经是DID格式的情况
      if (!decodedUserId.includes('%3A')) {
        const parts = decodedUserId.split(":");
        if (parts.length > 4 && !isNaN(parseInt(parts[3]))) {
          return parts.slice(0, 3).join(':') + '%3A' + parts.slice(3).join(':');
        } else {
          return decodedUserId;
        }
      } else {
        return decodedUserId;
      }
    } else if (decodedUserId.length === 16) { // unique_id
      if (port === 80 || port === 443) {
        return `did:wba:${host}:wba:user:${decodedUserId}`;
      } else {
        return `did:wba:${host}%3A${port}:wba:user:${decodedUserId}`;
      }
    } else {
      return "not_did_wba";
    }
  }

  /**
   * 获取DID文档
   */
  public static async getDidDocument(userId: string, host: string, port: number): Promise<DIDServiceResponse> {
    try {
      // 获取域名管理器
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 确保域名目录存在
      domainManager.ensureDomainDirectories(host, port);

      // 使用动态路径替换硬编码路径
      const paths = domainManager.getAllDataPaths(host, port);
      const didPath = path.join(paths.user_did_path, `user_${userId}`, 'did_document.json');

      logger.debug(`查找DID文档: ${didPath} (域名: ${host}:${port})`);

      try {
        await fs.access(didPath);
      } catch {
        return { 
          success: false, 
          error: `DID document not found for user ${userId} in domain ${host}:${port}` 
        };
      }

      const didDocumentContent = await fs.readFile(didPath, 'utf-8');
      const didDocument = JSON.parse(didDocumentContent);
      
      logger.debug(`成功加载DID文档: ${userId} from ${host}:${port}`);
      return { success: true, data: didDocument };

    } catch (error) {
      logger.error(`Error loading DID document: ${error}`);
      return { success: false, error: `Error loading DID document: ${error}` };
    }
  }

  /**
   * 获取智能体描述文档
   */
  public static async getAgentDescription(userId: string, host: string, port: number): Promise<DIDServiceResponse> {
    try {
      // 获取域名管理器
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 格式化DID
      const respDid = this.formatDidFromUserId(userId, host, port);

      // 查找用户
      const userResult = await findUserByDid(respDid);
      if (!userResult.success || !userResult.userDir) {
        return { success: false, error: `DID ${respDid} not found` };
      }

      // 使用动态路径获取用户目录
      const paths = domainManager.getAllDataPaths(host, port);
      const userFullPath = path.join(paths.user_did_path, userResult.userDir);

      // 从文件系统读取ad.json
      const adJsonPath = path.join(userFullPath, "ad.json");

      try {
        await fs.access(adJsonPath);
        const adJsonContent = await fs.readFile(adJsonPath, 'utf-8');
        const adJson = JSON.parse(adJsonContent);
        return { success: true, data: adJson };
      } catch (error) {
        logger.error(`读取ad.json失败: ${error}`);
        return { success: false, error: `ad.json not found for DID ${respDid}` };
      }

    } catch (error) {
      logger.error(`获取智能体描述失败: ${error}`);
      return { success: false, error: `获取智能体描述失败: ${error}` };
    }
  }

  /**
   * 获取智能体YAML文件
   */
  public static async getAgentYamlFile(
    respDid: string, 
    yamlFileName: string, 
    host: string, 
    port: number
  ): Promise<DIDServiceResponse> {
    try {
      // 获取域名管理器
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 格式化DID
      const formattedDid = this.formatDidFromUserId(respDid, host, port);

      // 查找用户
      const userResult = await findUserByDid(formattedDid);
      if (!userResult.success || !userResult.userDir) {
        return { success: false, error: "User not found" };
      }

      // 使用动态路径
      const paths = domainManager.getAllDataPaths(host, port);
      const yamlPath = path.join(paths.user_did_path, userResult.userDir, `${yamlFileName}.yaml`);

      try {
        await fs.access(yamlPath);
        const yamlContent = await fs.readFile(yamlPath, 'utf-8');
        return { success: true, data: yamlContent };
      } catch {
        return { success: false, error: "OpenAPI YAML not found" };
      }

    } catch (error) {
      logger.error(`读取YAML文件失败: ${error}`);
      return { success: false, error: `读取YAML文件失败: ${error}` };
    }
  }

  /**
   * 获取智能体JSON文件
   */
  public static async getAgentJsonFile(
    respDid: string, 
    jsonFileName: string, 
    host: string, 
    port: number
  ): Promise<DIDServiceResponse> {
    try {
      // 获取域名管理器
      const domainManager = new DomainManager();

      // 验证域名访问权限
      const validation = domainManager.validateDomainAccess(host, port);
      if (!validation.valid) {
        logger.warn(`域名访问被拒绝: ${host}:${port} - ${validation.error}`);
        return { success: false, error: validation.error };
      }

      // 格式化DID
      const formattedDid = this.formatDidFromUserId(respDid, host, port);

      // 查找用户
      const userResult = await findUserByDid(formattedDid);
      if (!userResult.success || !userResult.userDir) {
        return { success: false, error: "User not found" };
      }

      // 使用动态路径
      const paths = domainManager.getAllDataPaths(host, port);
      const jsonPath = path.join(paths.user_did_path, userResult.userDir, `${jsonFileName}.json`);

      try {
        await fs.access(jsonPath);
        const jsonContent = await fs.readFile(jsonPath, 'utf-8');
        const jsonData = JSON.parse(jsonContent);
        return { success: true, data: jsonData };
      } catch {
        return { success: false, error: "JSON file not found" };
      }

    } catch (error) {
      logger.error(`读取JSON文件失败: ${error}`);
      return { success: false, error: `读取JSON文件失败: ${error}` };
    }
  }
}