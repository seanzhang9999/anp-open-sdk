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
   * 支持智能文件选择：优先返回Node.js版本，回退到原始文件或Python版本
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

      // 智能文件选择：优先Node.js版本，然后原始文件，最后Python版本
      const adFileOptions = [
        'ad_nj.json',    // Node.js版本优先
        'ad.json',       // 原始文件作为回退
        'ad_py.json'     // Python版本作为最后回退
      ];

      for (const filename of adFileOptions) {
        const adFilePath = path.join(userFullPath, filename);
        try {
          await fs.access(adFilePath);
          const adFileContent = await fs.readFile(adFilePath, 'utf-8');
          const adData = JSON.parse(adFileContent);
          
          logger.debug(`成功读取Agent描述文档: ${filename} for DID ${respDid}`);
          return { success: true, data: adData };
        } catch (error) {
          // 继续尝试下一个文件选项
          logger.debug(`Agent描述文档 ${filename} 不存在，尝试下一个选项`);
          continue;
        }
      }

      // 所有选项都失败
      logger.error(`所有Agent描述文档选项都不存在 for DID ${respDid}`);
      return { success: false, error: `Agent description not found for DID ${respDid}` };

    } catch (error) {
      logger.error(`获取智能体描述失败: ${error}`);
      return { success: false, error: `获取智能体描述失败: ${error}` };
    }
  }

  /**
   * 获取智能体YAML文件
   * 支持智能文件选择：优先返回Node.js版本，回退到原始文件或Python版本
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
      const userFullPath = path.join(paths.user_did_path, userResult.userDir);

      // 智能文件选择：优先Node.js版本，然后原始文件，最后Python版本
      const yamlFileOptions = [
        `${yamlFileName}_nj.yaml`,    // Node.js版本优先
        `${yamlFileName}.yaml`,       // 原始文件作为回退
        `${yamlFileName}_py.yaml`     // Python版本作为最后回退
      ];

      for (const filename of yamlFileOptions) {
        const yamlPath = path.join(userFullPath, filename);
        try {
          await fs.access(yamlPath);
          const yamlContent = await fs.readFile(yamlPath, 'utf-8');
          
          logger.debug(`成功读取YAML文件: ${filename} for DID ${formattedDid}`);
          return { success: true, data: yamlContent };
        } catch (error) {
          // 继续尝试下一个文件选项
          logger.debug(`YAML文件 ${filename} 不存在，尝试下一个选项`);
          continue;
        }
      }

      // 所有选项都失败
      logger.error(`所有YAML文件选项都不存在: ${yamlFileName} for DID ${formattedDid}`);
      return { success: false, error: `YAML file ${yamlFileName} not found` };

    } catch (error) {
      logger.error(`读取YAML文件失败: ${error}`);
      return { success: false, error: `读取YAML文件失败: ${error}` };
    }
  }

  /**
   * 获取智能体JSON文件
   * 支持智能文件选择：优先返回Node.js版本，回退到原始文件或Python版本
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
      const userFullPath = path.join(paths.user_did_path, userResult.userDir);

      // 智能文件选择：优先Node.js版本，然后原始文件，最后Python版本
      const jsonFileOptions = [
        `${jsonFileName}_nj.json`,    // Node.js版本优先
        `${jsonFileName}.json`,       // 原始文件作为回退
        `${jsonFileName}_py.json`     // Python版本作为最后回退
      ];

      for (const filename of jsonFileOptions) {
        const jsonPath = path.join(userFullPath, filename);
        try {
          await fs.access(jsonPath);
          const jsonContent = await fs.readFile(jsonPath, 'utf-8');
          const jsonData = JSON.parse(jsonContent);
          
          logger.debug(`成功读取JSON文件: ${filename} for DID ${formattedDid}`);
          return { success: true, data: jsonData };
        } catch (error) {
          // 继续尝试下一个文件选项
          logger.debug(`JSON文件 ${filename} 不存在，尝试下一个选项`);
          continue;
        }
      }

      // 所有选项都失败
      logger.error(`所有JSON文件选项都不存在: ${jsonFileName} for DID ${formattedDid}`);
      return { success: false, error: `JSON file ${jsonFileName} not found` };

    } catch (error) {
      logger.error(`读取JSON文件失败: ${error}`);
      return { success: false, error: `读取JSON文件失败: ${error}` };
    }
  }
}