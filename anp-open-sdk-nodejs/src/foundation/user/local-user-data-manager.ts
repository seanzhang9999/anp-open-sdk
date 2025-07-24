/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'yaml';
import { LocalUserData, LocalUserDataFactory } from './local-user-data';
import { 
  DIDDocument, 
  AgentConfig, 
  ConflictInfo,
  UserNotFoundError,
  FileNotFoundError,
  DEFAULT_CONFIG
} from '../types';

/**
 * 本地用户数据管理器
 * 基于Python版本的LocalUserDataManager实现，提供单例模式的用户数据管理
 */
export class LocalUserDataManager {
  private static instance: LocalUserDataManager;
  
  // 用户数据索引
  private usersByDid: Map<string, LocalUserData> = new Map();
  private usersByName: Map<string, LocalUserData> = new Map();
  private usersByHostPort: Map<string, Map<string, LocalUserData>> = new Map();
  
  // 冲突信息
  private conflictingUsers: ConflictInfo[] = [];
  
  // 配置
  private userDir: string;
  private initialized: boolean = false;

  private constructor(userDir?: string) {
    // 默认使用相对于当前工作目录的data_user路径
    this.userDir = userDir || path.resolve(process.cwd(), '..', 'data_user');
  }

  /**
   * 获取单例实例
   */
  public static getInstance(userDir?: string): LocalUserDataManager {
    if (!LocalUserDataManager.instance) {
      LocalUserDataManager.instance = new LocalUserDataManager(userDir);
    }
    return LocalUserDataManager.instance;
  }

  /**
   * 重置单例实例（主要用于测试）
   */
  public static resetInstance(): void {
    LocalUserDataManager.instance = null as any;
  }

  /**
   * 初始化管理器
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    await this.loadAllUsers();
    this.initialized = true;
  }

  /**
   * 扫描并加载所有用户数据
   * 基于Python版本的load_all_users方法
   */
  public async loadAllUsers(): Promise<void> {
    console.log(`开始从 ${this.userDir} 加载所有用户数据...`);

    // 清空现有索引
    this.usersByDid.clear();
    this.usersByName.clear();
    this.usersByHostPort.clear();
    this.conflictingUsers = [];

    // 检查用户目录是否存在
    try {
      await fs.access(this.userDir);
    } catch (error) {
      console.warn(`用户目录不存在: ${this.userDir}`);
      this.initialized = true; // 即使目录不存在也标记为已初始化
      return;
    }

    // 扫描所有域名目录
    const domainDirs = await this.scanDomainDirectories();
    
    for (const domainDir of domainDirs) {
      await this.loadUsersFromDomain(domainDir);
    }

    // 输出加载结果
    if (this.conflictingUsers.length > 0) {
      console.warn(`发现 ${this.conflictingUsers.length} 个用户名冲突，请检查并解决`);
      for (const conflict of this.conflictingUsers) {
        console.warn(`  - 域名端口 ${conflict.host}:${conflict.port} 下的用户名 '${conflict.name}' 有冲突`);
      }
    }

    console.log(`加载完成，共 ${this.usersByDid.size} 个用户数据进入内存。`);
    this.initialized = true; // 标记为已初始化
  }

  /**
   * 扫描域名目录
   */
  private async scanDomainDirectories(): Promise<string[]> {
    const domainDirs: string[] = [];
    
    try {
      const entries = await fs.readdir(this.userDir, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith('.')) {
          domainDirs.push(path.join(this.userDir, entry.name));
        }
      }
    } catch (error) {
      console.error(`扫描域名目录失败: ${error}`);
    }

    return domainDirs;
  }

  /**
   * 从域名目录加载用户
   */
  private async loadUsersFromDomain(domainPath: string): Promise<void> {
    const usersPath = path.join(domainPath, 'anp_users');
    
    try {
      await fs.access(usersPath);
    } catch {
      // anp_users目录不存在，跳过
      return;
    }

    try {
      const entries = await fs.readdir(usersPath, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.isDirectory() && 
            (entry.name.startsWith('user_') || entry.name.startsWith('user_hosted_'))) {
          const userPath = path.join(usersPath, entry.name);
          await this.loadSingleUser(userPath);
        }
      }
    } catch (error) {
      console.error(`从域名目录加载用户失败 ${domainPath}: ${error}`);
    }
  }

  /**
   * 加载单个用户到内存
   */
  public async loadSingleUser(userFolderPath: string): Promise<LocalUserData | null> {
    const folderName = path.basename(userFolderPath);

    try {
      // 检查必要文件
      const cfgPath = path.join(userFolderPath, 'agent_cfg.yaml');
      const didDocPath = path.join(userFolderPath, 'did_document.json');

      const [cfgExists, didDocExists] = await Promise.all([
        this.fileExists(cfgPath),
        this.fileExists(didDocPath)
      ]);

      if (!cfgExists || !didDocExists) {
        console.warn(`跳过不完整的用户目录 (缺少cfg或did_doc): ${folderName}`);
        return null;
      }

      // 使用工厂方法创建用户数据
      const userData = await LocalUserDataFactory.fromDirectory(userFolderPath);
      
      // 添加到内存索引
      this.addUserToMemory(userData);
      
      console.log(`成功加载用户: ${userData.did}`);
      return userData;

    } catch (error) {
      console.error(`加载单个用户失败 (${folderName}): ${error}`);
      return null;
    }
  }

  /**
   * 将用户添加到内存索引中
   */
  private addUserToMemory(userData: LocalUserData): void {
    // 添加到DID索引
    this.usersByDid.set(userData.did, userData);

    // 添加到名称索引
    if (userData.name) {
      this.usersByName.set(userData.name, userData);
    }

    // 添加到域名端口索引
    const { host, port } = this.parseDidHostPort(userData.did);
    if (host && port && userData.name) {
      const hostPortKey = `${host}:${port}`;
      
      if (!this.usersByHostPort.has(hostPortKey)) {
        this.usersByHostPort.set(hostPortKey, new Map());
      }
      
      const hostPortUsers = this.usersByHostPort.get(hostPortKey)!;
      
      // 检查同一域名端口下是否有重名
      if (hostPortUsers.has(userData.name)) {
        const existingUser = hostPortUsers.get(userData.name)!;
        console.error(`用户名冲突: 域名端口 ${host}:${port} 下已存在同名用户 '${userData.name}'`);
        console.error(`冲突用户 DID: ${existingUser.did} 和 ${userData.did}`);
        
        // 记录冲突
        this.conflictingUsers.push({
          name: userData.name,
          host,
          port,
          users: [existingUser.did, userData.did]
        });
      }
      
      // 添加到域名端口索引
      hostPortUsers.set(userData.name, userData);
    }

    console.debug(`用户 ${userData.did} 已添加到内存索引`);
  }

  /**
   * 从DID中解析域名和端口
   */
  private parseDidHostPort(did: string): { host: string | null; port: number | null } {
    try {
      // 解析格式: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
      const parts = did.split(':');
      if (parts.length >= 3 && parts[0] === 'did' && parts[1] === 'wba') {
        const hostPart = parts[2]; // 不要解码，保持原始格式
        
        if (hostPart.includes('%3A')) {
          // 包含端口的情况
          const [encodedHost, portStr] = hostPart.split('%3A');
          const host = decodeURIComponent(encodedHost);
          const port = parseInt(portStr, 10);
          return { host, port: isNaN(port) ? null : port };
        } else {
          // 不包含端口，使用默认端口
          const host = decodeURIComponent(hostPart);
          return { host, port: 80 };
        }
      }
    } catch (error) {
      console.warn(`解析DID域名端口失败: ${did}, 错误: ${error}`);
    }
    
    return { host: null, port: null };
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
  // 公共查询方法
  // ============================================================================

  /**
   * 通过DID获取用户数据
   */
  public getUserData(did: string): LocalUserData | undefined {
    return this.usersByDid.get(did);
  }

  /**
   * 通过用户名获取用户数据
   */
  public getUserDataByName(name: string): LocalUserData | undefined {
    return this.usersByName.get(name);
  }

  /**
   * 获取所有用户数据
   */
  public getAllUsers(): LocalUserData[] {
    return Array.from(this.usersByDid.values());
  }

  /**
   * 通过域名端口获取用户列表
   */
  public getUsersByDomain(host: string, port: number): LocalUserData[] {
    const hostPortKey = `${host}:${port}`;
    const hostPortUsers = this.usersByHostPort.get(hostPortKey);
    
    if (hostPortUsers) {
      return Array.from(hostPortUsers.values());
    }
    
    return [];
  }

  /**
   * 检查用户名是否已被使用
   */
  public isUsernameTaken(name: string, host: string, port: number): boolean {
    const hostPortKey = `${host}:${port}`;
    const hostPortUsers = this.usersByHostPort.get(hostPortKey);
    
    return hostPortUsers ? hostPortUsers.has(name) : false;
  }

  /**
   * 获取冲突用户信息
   */
  public getConflictingUsers(): ConflictInfo[] {
    return [...this.conflictingUsers];
  }

  // ============================================================================
  // 用户管理方法
  // ============================================================================

  /**
   * 创建托管DID用户
   */
  public async createHostedUser(
    parentUserData: LocalUserData,
    host: string,
    port: string,
    didDocument: DIDDocument
  ): Promise<{ success: boolean; userData?: LocalUserData; error?: string }> {
    try {
      const didId = didDocument.id;
      const didSuffix = this.extractDidSuffix(didId);
      
      // 构建托管用户目录路径
      const originalUserDir = path.dirname(parentUserData.userDir);
      const cleanHost = host.replace(/\./g, '_').replace(/:/g, '_');
      const hostedDirName = `user_hosted_${cleanHost}_${port}_${didSuffix}`;
      const hostedDirPath = path.join(originalUserDir, hostedDirName);

      // 创建目录
      await fs.mkdir(hostedDirPath, { recursive: true });

      // 复制密钥文件
      const keyFiles = ['key-1_private.pem', 'key-1_public.pem', 'private_key.pem', 'public_key.pem'];
      for (const keyFile of keyFiles) {
        const srcPath = path.join(parentUserData.userDir, keyFile);
        const destPath = path.join(hostedDirPath, keyFile);
        
        try {
          await fs.copyFile(srcPath, destPath);
        } catch (error) {
          console.warn(`复制密钥文件失败 ${keyFile}: ${error}`);
        }
      }

      // 保存DID文档
      const didDocPath = path.join(hostedDirPath, 'did_document.json');
      await fs.writeFile(didDocPath, JSON.stringify(didDocument, null, 2), 'utf-8');

      // 创建Agent配置
      const agentCfg: AgentConfig = {
        did: didId,
        unique_id: didSuffix,
        name: `hosted_${parentUserData.name}_${host}_${port}`,
        type: 'hosted',
        hosted_config: {
          parent_did: parentUserData.did,
          host,
          port: parseInt(port, 10),
          created_at: new Date().toISOString(),
          purpose: `对外托管服务 - ${host}:${port}`
        }
      };

      const configPath = path.join(hostedDirPath, 'agent_cfg.yaml');
      await fs.writeFile(configPath, yaml.stringify(agentCfg), 'utf-8');

      // 动态加载新用户到内存
      const newUserData = await this.loadSingleUser(hostedDirPath);
      
      if (newUserData) {
        console.debug(`托管DID创建并加载到内存成功: ${hostedDirName}`);
        return { success: true, userData: newUserData };
      } else {
        return { success: false, error: '创建托管DID后加载失败' };
      }

    } catch (error) {
      console.error(`创建托管DID失败: ${error}`);
      return { success: false, error: `创建托管DID失败: ${error}` };
    }
  }

  /**
   * 从DID中提取后缀
   */
  private extractDidSuffix(did: string): string {
    const parts = did.split(':');
    return parts[parts.length - 1] || 'unknown_id';
  }

  /**
   * 扫描并加载新用户
   */
  public async scanAndLoadNewUsers(): Promise<void> {
    const currentDids = new Set(this.usersByDid.keys());
    const foundDids = new Set<string>();

    // 重新扫描所有域名目录
    const domainDirs = await this.scanDomainDirectories();
    
    for (const domainDir of domainDirs) {
      const usersPath = path.join(domainDir, 'anp_users');
      
      try {
        await fs.access(usersPath);
        const entries = await fs.readdir(usersPath, { withFileTypes: true });
        
        for (const entry of entries) {
          if (entry.isDirectory() && 
              (entry.name.startsWith('user_') || entry.name.startsWith('user_hosted_'))) {
            
            const userPath = path.join(usersPath, entry.name);
            const didDocPath = path.join(userPath, 'did_document.json');
            
            try {
              const didDocContent = await fs.readFile(didDocPath, 'utf-8');
              const didDoc: DIDDocument = JSON.parse(didDocContent);
              const did = didDoc.id;
              
              if (did) {
                foundDids.add(did);
                
                // 如果是新用户，加载到内存
                if (!currentDids.has(did)) {
                  console.log(`发现新用户: ${did}`);
                  await this.loadSingleUser(userPath);
                }
              }
            } catch (error) {
              console.error(`扫描用户目录时出错 (${entry.name}): ${error}`);
            }
          }
        }
      } catch {
        // anp_users目录不存在，跳过
        continue;
      }
    }

    // 检查是否有用户被删除
    const deletedDids = Array.from(currentDids).filter(did => !foundDids.has(did));
    for (const did of deletedDids) {
      console.log(`用户已被删除: ${did}`);
      this.removeUserFromMemory(did);
    }
  }

  /**
   * 从内存中移除用户
   */
  private removeUserFromMemory(did: string): void {
    const userData = this.usersByDid.get(did);
    if (userData) {
      // 从DID索引中移除
      this.usersByDid.delete(did);

      // 从名称索引中移除
      if (userData.name) {
        this.usersByName.delete(userData.name);
      }

      // 从域名端口索引中移除
      const { host, port } = this.parseDidHostPort(did);
      if (host && port && userData.name) {
        const hostPortKey = `${host}:${port}`;
        const hostPortUsers = this.usersByHostPort.get(hostPortKey);
        if (hostPortUsers) {
          hostPortUsers.delete(userData.name);
        }
      }

      console.debug(`用户 ${did} 已从内存索引中移除`);
    }
  }

  /**
   * 重新加载所有用户数据
   */
  public async reloadAllUsers(): Promise<void> {
    console.log("重新加载所有用户数据...");
    await this.loadAllUsers();
    console.log(`重新加载完成，当前共有 ${this.usersByDid.size} 个用户`);
  }

  /**
   * 刷新指定用户的数据
   */
  public async refreshUser(did: string): Promise<LocalUserData | null> {
    const userData = this.usersByDid.get(did);
    if (!userData) {
      console.warn(`用户 ${did} 不在内存中，无法刷新`);
      return null;
    }

    // 重新加载用户数据
    return await this.loadSingleUser(userData.userDir);
  }

  /**
   * 解决用户名冲突
   */
  public async resolveUsernameConflict(did: string, newName: string): Promise<boolean> {
    const userData = this.usersByDid.get(did);
    if (!userData) {
      console.error(`找不到DID为 ${did} 的用户`);
      return false;
    }

    const { host, port } = this.parseDidHostPort(did);
    if (!host || !port) {
      console.error(`无法从DID ${did} 解析出域名和端口`);
      return false;
    }

    // 检查新名称是否可用
    if (this.isUsernameTaken(newName, host, port)) {
      console.error(`新用户名 '${newName}' 在域名端口 ${host}:${port} 下已存在`);
      return false;
    }

    try {
      // 更新配置文件
      const cfgPath = path.join(userData.userDir, 'agent_cfg.yaml');
      const cfgContent = await fs.readFile(cfgPath, 'utf-8');
      const cfg: AgentConfig = yaml.parse(cfgContent);
      
      const oldName = cfg.name;
      cfg.name = newName;
      
      await fs.writeFile(cfgPath, yaml.stringify(cfg), 'utf-8');

      // 更新内存中的索引
      const hostPortKey = `${host}:${port}`;
      const hostPortUsers = this.usersByHostPort.get(hostPortKey);
      
      if (hostPortUsers && oldName) {
        hostPortUsers.delete(oldName);
        hostPortUsers.set(newName, userData);
      }

      if (oldName) {
        this.usersByName.delete(oldName);
      }
      this.usersByName.set(newName, userData);

      // 更新LocalUserData实例的name属性
      userData.setName(newName);

      console.log(`已将用户 ${did} 的名称从 '${oldName}' 更新为 '${newName}'`);
      return true;

    } catch (error) {
      console.error(`更新用户名失败: ${error}`);
      return false;
    }
  }

  // ============================================================================
  // 统计和调试方法
  // ============================================================================

  /**
   * 获取统计信息
   */
  public getStats(): Record<string, any> {
    return {
      total_users: this.usersByDid.size,
      users_by_name: this.usersByName.size,
      domain_ports: this.usersByHostPort.size,
      conflicting_users: this.conflictingUsers.length,
      user_dir: this.userDir,
      initialized: this.initialized
    };
  }

  /**
   * 获取用户目录路径
   */
  public getUserDir(): string {
    return this.userDir;
  }

  /**
   * 检查是否已初始化
   */
  public isInitialized(): boolean {
    return this.initialized;
  }
}

/**
 * 获取全局用户数据管理器实例的便捷函数
 */
export function getUserDataManager(userDir?: string): LocalUserDataManager {
  return LocalUserDataManager.getInstance(userDir);
}