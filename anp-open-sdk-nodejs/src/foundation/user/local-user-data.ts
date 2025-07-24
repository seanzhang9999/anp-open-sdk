/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';
import { 
  LocalUserDataOptions, 
  DIDDocument, 
  AgentConfig, 
  PasswordPaths,
  HostedInfo,
  Contact,
  TokenInfo,
  FileNotFoundError,
  DEFAULT_CONFIG
} from '../types';

/**
 * 本地用户数据类
 * 基于Python版本的LocalUserData实现，包含密钥内存缓存、联系人管理等功能
 */
export class LocalUserData {
  // 基础属性
  public readonly folderName: string;
  public readonly agentCfg: AgentConfig;
  public readonly didDocument: DIDDocument;
  public readonly passwordPaths: PasswordPaths;
  public readonly did: string;
  private _name?: string;
  public readonly uniqueId: string;
  public readonly userDir: string;
  public readonly didDocPath: string;
  public readonly keyId: string;

  // 文件路径
  public readonly didPrivateKeyFilePath: string;
  public readonly didPublicKeyFilePath: string;
  public readonly jwtPrivateKeyFilePath: string;
  public readonly jwtPublicKeyFilePath: string;

  // 托管DID属性
  public readonly isHostedDid: boolean;
  public readonly parentDid?: string;
  public readonly hostedInfo?: HostedInfo;

  // Token管理
  private tokenToRemoteDict: Map<string, TokenInfo> = new Map();
  private tokenFromRemoteDict: Map<string, TokenInfo> = new Map();

  // 联系人管理
  private contacts: Map<string, Contact> = new Map();

  // 内存中的密钥对象（私有，通过方法访问）
  private didPrivateKey?: crypto.KeyObject;
  private jwtPrivateKey?: crypto.KeyObject;
  private jwtPublicKey?: crypto.KeyObject;

  constructor(options: LocalUserDataOptions) {
    this.folderName = options.folderName;
    this.agentCfg = options.agentCfg;
    this.didDocument = options.didDocument;
    this.passwordPaths = options.passwordPaths;
    this.userDir = options.userFolderPath;
    this.didDocPath = options.didDocPath;

    // 解析基础属性
    this.did = this.didDocument.id;
    this._name = this.agentCfg.name;
    this.uniqueId = this.agentCfg.unique_id;
    this.keyId = this.parseKeyIdFromDidDoc() || DEFAULT_CONFIG.USER_DID_KEY_ID;

    // 设置文件路径
    this.didPrivateKeyFilePath = this.passwordPaths.did_private_key_file_path;
    this.didPublicKeyFilePath = this.passwordPaths.did_public_key_file_path;
    this.jwtPrivateKeyFilePath = this.passwordPaths.jwt_private_key_file_path;
    this.jwtPublicKeyFilePath = this.passwordPaths.jwt_public_key_file_path;

    // 托管DID相关属性
    this.isHostedDid = this.folderName.startsWith('user_hosted_');
    this.parentDid = this.isHostedDid ? this.agentCfg.hosted_config?.parent_did : undefined;
    this.hostedInfo = this.isHostedDid ? this.parseHostedInfoFromName(this.folderName) : undefined;

    // 自动加载密钥到内存
    this.loadKeysToMemory().catch(error => {
      console.warn(`为用户 ${this._name} 加载密钥到内存时失败:`, error);
    });
  }

  /**
   * 从DID文档中解析key_id
   */
  private parseKeyIdFromDidDoc(): string | undefined {
    // 优先使用key_id字段
    if (this.didDocument.key_id) {
      return this.didDocument.key_id;
    }

    // 从verificationMethod中提取
    if (this.didDocument.verificationMethod && this.didDocument.verificationMethod.length > 0) {
      const keyId = this.didDocument.verificationMethod[0].id.split('#').pop();
      if (keyId) {
        return keyId;
      }
    }

    return undefined;
  }

  /**
   * 从文件夹名称解析托管信息
   */
  private parseHostedInfoFromName(folderName: string): HostedInfo | undefined {
    if (folderName.startsWith('user_hosted_')) {
      // 解析格式: user_hosted_open_localhost_9527_b9b6b73772c692db
      const remainder = folderName.substring(12); // 移除 'user_hosted_'
      const parts = remainder.split('_');
      
      if (parts.length >= 2) {
        // 重新组合host部分，处理包含下划线的域名
        let host = parts[0];
        let portIndex = 1;
        
        // 查找端口号（数字）的位置
        while (portIndex < parts.length && isNaN(parseInt(parts[portIndex], 10))) {
          host += '.' + parts[portIndex];
          portIndex++;
        }
        
        if (portIndex < parts.length) {
          const port = parseInt(parts[portIndex], 10);
          const didSuffix = portIndex + 1 < parts.length ? parts[portIndex + 1] : undefined;
          
          return {
            host,
            port,
            did_suffix: didSuffix,
          };
        }
      }
    }
    return undefined;
  }

  /**
   * 加载密钥文件到内存
   * 基于Python版本的_load_keys_to_memory方法
   */
  private async loadKeysToMemory(): Promise<void> {
    try {
      // 加载DID私钥
      if (await this.fileExists(this.didPrivateKeyFilePath)) {
        const keyData = await fs.readFile(this.didPrivateKeyFilePath);
        this.didPrivateKey = crypto.createPrivateKey(keyData);
      }

      // 加载JWT私钥
      if (await this.fileExists(this.jwtPrivateKeyFilePath)) {
        const keyData = await fs.readFile(this.jwtPrivateKeyFilePath);
        this.jwtPrivateKey = crypto.createPrivateKey(keyData);
      }

      // 加载JWT公钥
      if (await this.fileExists(this.jwtPublicKeyFilePath)) {
        const keyData = await fs.readFile(this.jwtPublicKeyFilePath);
        this.jwtPublicKey = crypto.createPublicKey(keyData);
      }
    } catch (error) {
      throw new Error(`加载密钥到内存失败: ${error}`);
    }
  }

  /**
   * 检查文件是否存在
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  // ============================================================================
  // 公共访问方法
  // ============================================================================

  /**
   * 获取DID
   */
  public getDid(): string {
    return this.did;
  }

  /**
   * 获取用户名
   */
  public get name(): string | undefined {
    return this._name;
  }

  /**
   * 设置用户名
   */
  public setName(name: string): void {
    this._name = name;
  }

  /**
   * 获取私钥文件路径
   */
  public getPrivateKeyPath(): string {
    return this.didPrivateKeyFilePath;
  }

  /**
   * 获取公钥文件路径
   */
  public getPublicKeyPath(): string {
    return this.didPublicKeyFilePath;
  }

  /**
   * 获取内存中的DID私钥
   */
  public getDidPrivateKey(): crypto.KeyObject | undefined {
    return this.didPrivateKey;
  }

  /**
   * 获取内存中的JWT私钥
   */
  public getJwtPrivateKey(): crypto.KeyObject | undefined {
    return this.jwtPrivateKey;
  }

  /**
   * 获取内存中的JWT公钥
   */
  public getJwtPublicKey(): crypto.KeyObject | undefined {
    return this.jwtPublicKey;
  }

  // ============================================================================
  // Token管理方法
  // ============================================================================

  /**
   * 获取发送给远程的Token
   */
  public getTokenToRemote(remoteDid: string): TokenInfo | undefined {
    return this.tokenToRemoteDict.get(remoteDid);
  }

  /**
   * 存储发送给远程的Token
   */
  public storeTokenToRemote(remoteDid: string, token: string, expiresInSeconds: number): void {
    const now = new Date();
    const expiresAt = new Date(now.getTime() + expiresInSeconds * 1000);
    
    const tokenInfo: TokenInfo = {
      token,
      created_at: now.toISOString(),
      expires_at: expiresAt.toISOString(),
      is_revoked: false,
      req_did: remoteDid,
    };
    
    this.tokenToRemoteDict.set(remoteDid, tokenInfo);
  }

  /**
   * 获取从远程接收的Token
   */
  public getTokenFromRemote(remoteDid: string): TokenInfo | undefined {
    return this.tokenFromRemoteDict.get(remoteDid);
  }

  /**
   * 存储从远程接收的Token
   */
  public storeTokenFromRemote(remoteDid: string, token: string): void {
    const now = new Date();
    
    const tokenInfo: TokenInfo = {
      token,
      created_at: now.toISOString(),
      req_did: remoteDid,
    };
    
    this.tokenFromRemoteDict.set(remoteDid, tokenInfo);
  }

  /**
   * 撤销发送给远程的Token
   */
  public revokeTokenToRemote(remoteDid: string): boolean {
    const tokenInfo = this.tokenToRemoteDict.get(remoteDid);
    if (tokenInfo) {
      tokenInfo.is_revoked = true;
      return true;
    }
    return false;
  }

  // ============================================================================
  // 联系人管理方法
  // ============================================================================

  /**
   * 添加联系人
   */
  public addContact(contact: Contact): void {
    if (contact.did) {
      const now = new Date().toISOString();
      const contactWithTimestamp: Contact = {
        ...contact,
        created_at: contact.created_at || now,
        updated_at: now,
      };
      this.contacts.set(contact.did, contactWithTimestamp);
    }
  }

  /**
   * 获取联系人
   */
  public getContact(remoteDid: string): Contact | undefined {
    return this.contacts.get(remoteDid);
  }

  /**
   * 列出所有联系人
   */
  public listContacts(): Contact[] {
    return Array.from(this.contacts.values());
  }

  /**
   * 删除联系人
   */
  public removeContact(remoteDid: string): boolean {
    return this.contacts.delete(remoteDid);
  }

  /**
   * 更新联系人
   */
  public updateContact(remoteDid: string, updates: Partial<Contact>): boolean {
    const existingContact = this.contacts.get(remoteDid);
    if (existingContact) {
      const updatedContact: Contact = {
        ...existingContact,
        ...updates,
        did: remoteDid, // 确保DID不被覆盖
        updated_at: new Date().toISOString(),
      };
      this.contacts.set(remoteDid, updatedContact);
      return true;
    }
    return false;
  }

  // ============================================================================
  // 工具方法
  // ============================================================================

  /**
   * 转换为字典格式
   */
  public toDict(): Record<string, any> {
    return {
      folder_name: this.folderName,
      did: this.did,
      name: this._name,
      unique_id: this.uniqueId,
      user_dir: this.userDir,
      key_id: this.keyId,
      is_hosted_did: this.isHostedDid,
      parent_did: this.parentDid,
      hosted_info: this.hostedInfo,
      contacts_count: this.contacts.size,
      tokens_to_remote_count: this.tokenToRemoteDict.size,
      tokens_from_remote_count: this.tokenFromRemoteDict.size,
    };
  }

  /**
   * 验证用户数据完整性
   */
  public async validateIntegrity(): Promise<{
    valid: boolean;
    errors: string[];
  }> {
    const errors: string[] = [];

    // 验证基本属性
    if (!this.did) {
      errors.push('DID is missing');
    }

    if (!this.uniqueId) {
      errors.push('Unique ID is missing');
    }

    // 验证DID和配置一致性
    if (this.did !== this.agentCfg.did) {
      errors.push(`DID mismatch: ${this.did} !== ${this.agentCfg.did}`);
    }

    if (!this.did.includes(this.uniqueId)) {
      errors.push(`Unique ID not found in DID: ${this.uniqueId}`);
    }

    // 验证文件存在性
    const requiredFiles = [
      { path: this.didDocPath, name: 'DID document' },
      { path: this.didPrivateKeyFilePath, name: 'DID private key' },
      { path: this.jwtPrivateKeyFilePath, name: 'JWT private key' },
    ];

    for (const file of requiredFiles) {
      if (!(await this.fileExists(file.path))) {
        errors.push(`${file.name} file not found: ${file.path}`);
      }
    }

    // 验证托管DID特殊属性
    if (this.isHostedDid) {
      if (!this.parentDid) {
        errors.push('Hosted DID missing parent_did');
      }
      
      if (!this.hostedInfo) {
        errors.push('Hosted DID missing hosted_info');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * 刷新密钥缓存
   */
  public async refreshKeyCache(): Promise<void> {
    await this.loadKeysToMemory();
  }

  /**
   * 获取统计信息
   */
  public getStats(): Record<string, any> {
    return {
      did: this.did,
      name: this._name,
      is_hosted: this.isHostedDid,
      contacts_count: this.contacts.size,
      active_tokens_to_remote: Array.from(this.tokenToRemoteDict.values())
        .filter(token => !token.is_revoked).length,
      tokens_from_remote: this.tokenFromRemoteDict.size,
      has_did_private_key: !!this.didPrivateKey,
      has_jwt_private_key: !!this.jwtPrivateKey,
      has_jwt_public_key: !!this.jwtPublicKey,
    };
  }
}

/**
 * 静态工厂方法
 */
export class LocalUserDataFactory {
  /**
   * 从目录创建LocalUserData实例
   */
  static async fromDirectory(userDirectory: string): Promise<LocalUserData> {
    const folderName = path.basename(userDirectory);
    
    // 读取必需文件
    const didDocPath = path.join(userDirectory, 'did_document.json');
    const agentCfgPath = path.join(userDirectory, 'agent_cfg.yaml');
    
    try {
      const [didDocContent, agentCfgContent] = await Promise.all([
        fs.readFile(didDocPath, 'utf-8'),
        fs.readFile(agentCfgPath, 'utf-8'),
      ]);

      const didDocument: DIDDocument = JSON.parse(didDocContent);
      
      // 解析YAML配置
      const yaml = require('yaml');
      const agentCfg: AgentConfig = yaml.parse(agentCfgContent);

      // 构建密钥路径
      const keyId = didDocument.key_id || 
        didDocument.verificationMethod?.[0]?.id.split('#').pop() || 
        DEFAULT_CONFIG.USER_DID_KEY_ID;

      const passwordPaths: PasswordPaths = {
        did_private_key_file_path: path.join(userDirectory, `${keyId}_private.pem`),
        did_public_key_file_path: path.join(userDirectory, `${keyId}_public.pem`),
        jwt_private_key_file_path: path.join(userDirectory, 'private_key.pem'),
        jwt_public_key_file_path: path.join(userDirectory, 'public_key.pem'),
      };

      const options: LocalUserDataOptions = {
        folderName,
        agentCfg,
        didDocument,
        didDocPath,
        passwordPaths,
        userFolderPath: userDirectory,
      };

      return new LocalUserData(options);
    } catch (error) {
      throw new FileNotFoundError(`Failed to create LocalUserData from directory ${userDirectory}: ${error}`);
    }
  }
}