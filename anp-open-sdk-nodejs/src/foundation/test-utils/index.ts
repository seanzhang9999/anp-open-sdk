/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as path from 'path';
import * as fs from 'fs/promises';
import * as yaml from 'yaml';
import { 
  DIDDocument, 
  AgentConfig, 
  AgentDescription,
  LocalUserDataOptions,
  AgentMappingConfig 
} from '../types';

/**
 * 测试工具类 - 基于真实data_user数据
 */
export class TestDataHelper {
  private static readonly DATA_USER_PATH = path.resolve(process.cwd(), '..', 'data_user');
  
  /**
   * 测试域名配置
   */
  static readonly TEST_DOMAINS = {
    LOCALHOST: 'localhost_9527',
    OPEN_LOCALHOST: 'open_localhost_9527',
    SERVICE_LOCALHOST: 'service_localhost_9527',
    TEST_LOCAL: 'test1_local_8001',
    USER_LOCALHOST: 'user_localhost_9527',
  } as const;

  /**
   * 测试用户配置
   */
  static readonly TEST_USERS = {
    REGULAR_USER_1: 'user_27c0b1d11180f973',
    REGULAR_USER_2: 'user_28cddee0fade0258', 
    REGULAR_USER_3: 'user_3ea884878ea5fbb1',
    REGULAR_USER_4: 'user_5fea49e183c6c211',
    REGULAR_USER_5: 'user_e0959abab6fc3c3d',
    HOSTED_USER_1: 'user_hosted_open_localhost_9527_b9b6b73772c692db',
    HOSTED_USER_2: 'user_hosted_agent-did.com_80_',
  } as const;

  /**
   * 测试Agent配置
   */
  static readonly TEST_AGENTS = {
    CALCULATOR: 'agent_caculator',
    LLM: 'agent_llm',
    ORCHESTRATOR: 'orchestrator_agent',
    AGENT_001: 'agent_001',
    AGENT_002: 'agent_002',
  } as const;

  /**
   * 获取数据用户根路径
   */
  static getDataUserPath(): string {
    return this.DATA_USER_PATH;
  }

  /**
   * 获取域名数据路径
   */
  static getDomainPath(domain: keyof typeof TestDataHelper.TEST_DOMAINS): string {
    return path.join(this.DATA_USER_PATH, this.TEST_DOMAINS[domain]);
  }

  /**
   * 获取用户数据路径
   */
  static getUserPath(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): string {
    const domainPath = this.getDomainPath(domain);
    const userFolder = this.TEST_USERS[user];
    
    if (userFolder.startsWith('user_hosted_')) {
      return path.join(domainPath, 'anp_users', userFolder);
    } else {
      return path.join(domainPath, 'anp_users', userFolder);
    }
  }

  /**
   * 获取Agent配置路径
   */
  static getAgentConfigPath(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    agent: keyof typeof TestDataHelper.TEST_AGENTS
  ): string {
    return path.join(this.getDomainPath(domain), 'agents_config_py', this.TEST_AGENTS[agent]);
  }

  /**
   * 读取真实的DID文档
   */
  static async readDIDDocument(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): Promise<DIDDocument> {
    const userPath = this.getUserPath(domain, user);
    const didDocPath = path.join(userPath, 'did_document.json');
    
    try {
      const content = await fs.readFile(didDocPath, 'utf-8');
      return JSON.parse(content) as DIDDocument;
    } catch (error) {
      throw new Error(`Failed to read DID document from ${didDocPath}: ${error}`);
    }
  }

  /**
   * 读取真实的Agent配置
   */
  static async readAgentConfig(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): Promise<AgentConfig> {
    const userPath = this.getUserPath(domain, user);
    const configPath = path.join(userPath, 'agent_cfg.yaml');
    
    try {
      const content = await fs.readFile(configPath, 'utf-8');
      return yaml.parse(content) as AgentConfig;
    } catch (error) {
      throw new Error(`Failed to read agent config from ${configPath}: ${error}`);
    }
  }

  /**
   * 读取真实的Agent描述
   */
  static async readAgentDescription(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): Promise<AgentDescription> {
    const userPath = this.getUserPath(domain, user);
    const adPath = path.join(userPath, 'ad.json');
    
    try {
      const content = await fs.readFile(adPath, 'utf-8');
      return JSON.parse(content) as AgentDescription;
    } catch (error) {
      throw new Error(`Failed to read agent description from ${adPath}: ${error}`);
    }
  }

  /**
   * 读取Agent映射配置
   */
  static async readAgentMappingConfig(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    agent: keyof typeof TestDataHelper.TEST_AGENTS
  ): Promise<AgentMappingConfig> {
    const agentPath = this.getAgentConfigPath(domain, agent);
    const mappingPath = path.join(agentPath, 'agent_mappings.yaml');
    
    try {
      const content = await fs.readFile(mappingPath, 'utf-8');
      return yaml.parse(content) as AgentMappingConfig;
    } catch (error) {
      throw new Error(`Failed to read agent mapping from ${mappingPath}: ${error}`);
    }
  }

  /**
   * 检查文件是否存在
   */
  static async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取用户的所有密钥文件路径
   */
  static getUserKeyPaths(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): {
    didPrivateKey: string;
    didPublicKey: string;
    jwtPrivateKey: string;
    jwtPublicKey: string;
  } {
    const userPath = this.getUserPath(domain, user);
    
    return {
      didPrivateKey: path.join(userPath, 'key-1_private.pem'),
      didPublicKey: path.join(userPath, 'key-1_public.pem'),
      jwtPrivateKey: path.join(userPath, 'private_key.pem'),
      jwtPublicKey: path.join(userPath, 'public_key.pem'),
    };
  }

  /**
   * 创建LocalUserDataOptions用于测试
   */
  static async createLocalUserDataOptions(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): Promise<LocalUserDataOptions> {
    const userPath = this.getUserPath(domain, user);
    const userFolder = this.TEST_USERS[user];
    
    const [agentCfg, didDocument] = await Promise.all([
      this.readAgentConfig(domain, user),
      this.readDIDDocument(domain, user),
    ]);

    const keyPaths = this.getUserKeyPaths(domain, user);
    
    return {
      folderName: userFolder,
      agentCfg,
      didDocument,
      didDocPath: path.join(userPath, 'did_document.json'),
      passwordPaths: {
        did_private_key_file_path: keyPaths.didPrivateKey,
        did_public_key_file_path: keyPaths.didPublicKey,
        jwt_private_key_file_path: keyPaths.jwtPrivateKey,
        jwt_public_key_file_path: keyPaths.jwtPublicKey,
      },
      userFolderPath: userPath,
    };
  }

  /**
   * 验证数据完整性
   */
  static async validateUserData(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS,
    user: keyof typeof TestDataHelper.TEST_USERS
  ): Promise<{
    valid: boolean;
    missing: string[];
    errors: string[];
  }> {
    const userPath = this.getUserPath(domain, user);
    const missing: string[] = [];
    const errors: string[] = [];

    // 检查必需文件
    const requiredFiles = [
      'did_document.json',
      'agent_cfg.yaml',
    ];

    for (const file of requiredFiles) {
      const filePath = path.join(userPath, file);
      if (!(await this.fileExists(filePath))) {
        missing.push(file);
      }
    }

    // 检查密钥文件
    const keyPaths = this.getUserKeyPaths(domain, user);
    for (const [keyType, keyPath] of Object.entries(keyPaths)) {
      if (!(await this.fileExists(keyPath))) {
        missing.push(`${keyType}: ${path.basename(keyPath)}`);
      }
    }

    // 验证文件内容
    if (missing.length === 0) {
      try {
        const didDoc = await this.readDIDDocument(domain, user);
        const agentCfg = await this.readAgentConfig(domain, user);
        
        // 验证DID一致性
        if (didDoc.id !== agentCfg.did) {
          errors.push(`DID mismatch: ${didDoc.id} !== ${agentCfg.did}`);
        }
        
        // 验证unique_id一致性
        if (!didDoc.id.includes(agentCfg.unique_id)) {
          errors.push(`Unique ID not found in DID: ${agentCfg.unique_id}`);
        }
      } catch (error) {
        errors.push(`Validation error: ${error}`);
      }
    }

    return {
      valid: missing.length === 0 && errors.length === 0,
      missing,
      errors,
    };
  }

  /**
   * 获取所有可用的测试用户列表
   */
  static async getAvailableUsers(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS
  ): Promise<string[]> {
    const domainPath = this.getDomainPath(domain);
    const usersPath = path.join(domainPath, 'anp_users');
    
    try {
      const entries = await fs.readdir(usersPath, { withFileTypes: true });
      return entries
        .filter(entry => entry.isDirectory())
        .filter(entry => entry.name.startsWith('user_'))
        .map(entry => entry.name);
    } catch (error) {
      console.warn(`Failed to read users from ${usersPath}: ${error}`);
      return [];
    }
  }

  /**
   * 获取所有可用的Agent配置列表
   */
  static async getAvailableAgents(
    domain: keyof typeof TestDataHelper.TEST_DOMAINS
  ): Promise<string[]> {
    const domainPath = this.getDomainPath(domain);
    const agentsPath = path.join(domainPath, 'agents_config_py');
    
    try {
      const entries = await fs.readdir(agentsPath, { withFileTypes: true });
      return entries
        .filter(entry => entry.isDirectory())
        .map(entry => entry.name);
    } catch (error) {
      console.warn(`Failed to read agents from ${agentsPath}: ${error}`);
      return [];
    }
  }
}

/**
 * 测试断言工具
 */
export class TestAssertions {
  /**
   * 断言DID格式正确
   */
  static assertValidDID(did: string): void {
    if (!did.startsWith('did:wba:')) {
      throw new Error(`Invalid DID format: ${did}`);
    }
  }

  /**
   * 断言用户数据完整性
   */
  static assertUserDataIntegrity(
    didDoc: DIDDocument,
    agentCfg: AgentConfig
  ): void {
    if (didDoc.id !== agentCfg.did) {
      throw new Error(`DID mismatch: ${didDoc.id} !== ${agentCfg.did}`);
    }
    
    if (!didDoc.id.includes(agentCfg.unique_id)) {
      throw new Error(`Unique ID not found in DID: ${agentCfg.unique_id}`);
    }
  }

  /**
   * 断言托管DID格式
   */
  static assertHostedDID(did: string, expectedHost: string): void {
    this.assertValidDID(did);
    
    if (!did.includes('hostuser')) {
      throw new Error(`Not a hosted DID: ${did}`);
    }
    
    if (!did.includes(expectedHost.replace('.', '.'))) {
      throw new Error(`DID does not contain expected host ${expectedHost}: ${did}`);
    }
  }
}