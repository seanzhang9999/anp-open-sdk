/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { LocalUserData } from './local-user-data';
import { LocalUserDataManager, getUserDataManager } from './local-user-data-manager';
import { ContactManager } from '../contact/contact-manager';
import { DIDDocument, Contact, DEFAULT_CONFIG } from '../types';

/**
 * 远程ANP用户类
 * 对应Python版本的RemoteANPUser
 */
export class RemoteANPUser {
  public id: string;
  public name?: string;
  public host?: string;
  public port?: number;
  public extra: Record<string, any>;

  constructor(id: string, name?: string, host?: string, port?: number, extra: Record<string, any> = {}) {
    this.id = id;
    this.name = name;
    this.host = host;
    this.port = port;
    this.extra = extra;

    // 如果提供了DID但没有host/port，尝试解析
    if (this.id && (!this.host || !this.port)) {
      const parsed = this.parseWbaDidHostPort(this.id);
      if (parsed) {
        this.host = parsed.host;
        this.port = parsed.port;
      }
    }
  }

  /**
   * 解析WBA DID的host和port
   * 对应Python版本的parse_wba_did_host_port
   */
  private parseWbaDidHostPort(did: string): { host: string; port: number } | null {
    try {
      // 解析格式: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
      const parts = did.split(':');
      if (parts.length >= 3 && parts[0] === 'did' && parts[1] === 'wba') {
        const hostPart = parts[2];
        
        if (hostPart.includes('%3A')) {
          // 包含端口的情况
          const [encodedHost, portStr] = hostPart.split('%3A');
          const host = decodeURIComponent(encodedHost);
          const port = parseInt(portStr, 10);
          return { host, port: isNaN(port) ? 80 : port };
        } else {
          // 不包含端口，使用默认端口
          const host = decodeURIComponent(hostPart);
          return { host, port: 80 };
        }
      }
    } catch (error) {
      console.warn('Failed to parse DID host/port:', error);
    }
    return null;
  }

  public toDict(): Record<string, any> {
    return {
      did: this.id,
      name: this.name,
      host: this.host,
      port: this.port,
      ...this.extra
    };
  }
}

/**
 * 本地智能体类
 * 对应Python版本的ANPUser，代表当前用户的DID身份
 */
export class ANPUser {
  // 类级别的实例缓存，确保同一个DID只有一个ANPUser实例
  private static instances = new Map<string, ANPUser>();

  public userData: LocalUserData;
  public id: string;
  public name: string;
  public userDir: string;
  public agentType: string;
  public keyId: string;
  
  // 文件路径
  public didDocumentPath: string;
  public privateKeyPath: string;
  public jwtPrivateKeyPath: string;
  public jwtPublicKeyPath: string;
  
  // WebSocket和SSE连接
  private wsConnections: Map<string, any> = new Map();
  private sseClients: Set<any> = new Set();
  
  // 托管DID属性
  public isHostedDid: boolean;
  public parentDid?: string;
  public hostedInfo?: any;
  
  // 群组相关属性
  public groupQueues: Map<string, Map<string, any>> = new Map();
  public groupMembers: Map<string, Set<string>> = new Map();

  // 联系人管理器
  public contactManager: ContactManager;

  // 为了向后兼容，添加API路由和消息处理器属性
  public apiRoutes: Map<string, Function> = new Map();
  public messageHandlers: Map<string, Function> = new Map();

  constructor(userData: LocalUserData, name: string = "未命名", agentType: string = "personal") {
    this.userData = userData;
    this.userDir = userData.userDir;
    
    if (name === "未命名") {
      this.name = userData.name || `未命名智能体${userData.did}`;
    } else {
      this.name = name;
    }
    
    this.id = userData.did;
    this.agentType = agentType;
    
    // 将实例添加到缓存中（如果还没有的话）
    if (!ANPUser.instances.has(this.id)) {
      ANPUser.instances.set(this.id, this);
      console.debug(`🆕 缓存ANPUser实例 (直接构造): ${this.id}`);
    } else {
      console.debug(`🔄 ANPUser实例已存在于缓存中: ${this.id}`);
    }
    
    // 设置key ID
    this.keyId = DEFAULT_CONFIG.USER_DID_KEY_ID;
    
    // 设置文件路径
    this.didDocumentPath = userData.didDocPath;
    this.privateKeyPath = userData.didPrivateKeyFilePath;
    this.jwtPrivateKeyPath = userData.jwtPrivateKeyFilePath;
    this.jwtPublicKeyPath = userData.jwtPublicKeyFilePath;
    
    // 托管DID属性
    this.isHostedDid = userData.isHostedDid;
    this.parentDid = userData.parentDid;
    this.hostedInfo = userData.hostedInfo;

    // 初始化联系人管理器
    this.contactManager = new ContactManager(this.userData);
  }

  /**
   * 从DID创建ANPUser实例
   * 对应Python版本的from_did类方法
   */
  public static fromDid(did: string, name: string = "未命名", agentType: string = "personal"): ANPUser {
    // 检查实例缓存
    if (ANPUser.instances.has(did)) {
      console.debug(`🔄 复用ANPUser实例: ${did}`);
      return ANPUser.instances.get(did)!;
    }
    
    const userDataManager = getUserDataManager();
    let userData = userDataManager.getUserData(did);
    
    if (!userData) {
      // 尝试刷新用户数据
      console.debug(`用户 ${did} 不在内存中，尝试刷新用户数据...`);
      userDataManager.scanAndLoadNewUsers();
      // 再次尝试获取
      userData = userDataManager.getUserData(did);
      if (!userData) {
        // 如果还是找不到，抛出异常
        throw new Error(`未找到 DID 为 '${did}' 的用户数据。请检查您的用户目录和配置文件。`);
      }
    }
    
    if (name === "未命名") {
      name = userData.name || "未命名";
    }
    
    // 创建新实例并缓存
    const instance = new ANPUser(userData, name, agentType);
    ANPUser.instances.set(did, instance);
    console.debug(`🆕 创建并缓存ANPUser实例: ${did}`);
    return instance;
  }

  /**
   * 获取缓存的实例
   */
  public static getInstance(did: string): ANPUser | undefined {
    return ANPUser.instances.get(did);
  }

  /**
   * 获取所有实例
   */
  public static getAllInstances(): ANPUser[] {
    return Array.from(ANPUser.instances.values());
  }

  /**
   * 获取用户目录
   */
  public getHostDids(): string {
    return this.userDir;
  }

  // ============================================================================
  // 联系人和Token管理方法（委托给ContactManager）
  // ============================================================================

  public getTokenToRemote(remoteDid: string, hostedDid?: string): any {
    return this.contactManager.getTokenToRemote(remoteDid);
  }

  public storeTokenFromRemote(remoteDid: string, token: string, hostedDid?: string): void {
    this.contactManager.storeTokenFromRemote(remoteDid, token);
  }

  public getTokenFromRemote(remoteDid: string, hostedDid?: string): any {
    return this.contactManager.getTokenFromRemote(remoteDid);
  }

  public revokeTokenToRemote(remoteDid: string, hostedDid?: string): void {
    this.contactManager.revokeTokenToRemote(remoteDid);
  }

  public addContact(remoteAgent: RemoteANPUser | Contact): void {
    let contact: Contact;
    if (remoteAgent instanceof RemoteANPUser) {
      contact = remoteAgent.toDict() as Contact;
    } else if (typeof remoteAgent === 'object' && 'toDict' in remoteAgent) {
      contact = (remoteAgent as any).toDict();
    } else {
      contact = {
        did: (remoteAgent as any).id || (remoteAgent as Contact).did,
        host: (remoteAgent as any).host,
        port: (remoteAgent as any).port,
        name: (remoteAgent as any).name
      };
    }
    this.contactManager.addContact(contact);
  }

  public getContact(remoteDid: string): Contact | undefined {
    return this.contactManager.getContact(remoteDid);
  }

  public listContacts(): Contact[] {
    return this.contactManager.listContacts();
  }

  // ============================================================================
  // 托管DID相关方法
  // ============================================================================

  /**
   * 异步申请托管DID（第一步：提交申请）
   * 对应Python版本的request_hosted_did_async
   */
  public async requestHostedDidAsync(targetHost: string, targetPort: number = 9527): Promise<{
    success: boolean;
    requestId: string;
    error: string;
  }> {
    try {
      if (!this.userData.didDocument) {
        return { success: false, requestId: "", error: "当前用户没有DID文档" };
      }
      
      // 构建申请请求
      const requestData = {
        did_document: this.userData.didDocument,
        requester_did: this.userData.didDocument.id,
        callback_info: {
          client_host: 'localhost', // 可以配置
          client_port: 9527
        }
      };
      
      // 发送申请请求
      const targetUrl = `http://${targetHost}:${targetPort}/wba/hosted-did/request`;
      
      // 使用fetch发送请求
      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const result: any = await response.json();
        if (result.success) {
          const requestId = result.request_id;
          console.debug(`托管DID申请已提交: ${requestId}`);
          return { success: true, requestId, error: "" };
        } else {
          const errorMsg = result.message || '申请失败';
          return { success: false, requestId: "", error: errorMsg };
        }
      } else {
        const errorMsg = `申请请求失败: HTTP ${response.status}`;
        console.error(errorMsg);
        return { success: false, requestId: "", error: errorMsg };
      }
      
    } catch (error) {
      const errorMsg = `申请托管DID失败: ${error}`;
      console.error(errorMsg);
      return { success: false, requestId: "", error: errorMsg };
    }
  }

  /**
   * 检查托管DID处理结果（第二步：检查结果）
   * 对应Python版本的check_hosted_did_results
   */
  public async checkHostedDidResults(): Promise<{
    success: boolean;
    results: any[];
    error: string;
  }> {
    try {
      if (!this.userData.didDocument) {
        return { success: false, results: [], error: "当前用户没有DID文档" };
      }
      
      // 从自己的DID中提取ID
      const didParts = this.userData.didDocument.id.split(':');
      const requesterId = didParts[didParts.length - 1] || "";
      
      if (!requesterId) {
        return { success: false, results: [], error: "无法从DID中提取用户ID" };
      }
      
      // 检查结果（可以检查多个托管服务）
      const allResults: any[] = [];
      
      // 这里可以配置多个托管服务地址
      const targetServices = [
        { host: "localhost", port: 9527 },
        { host: "open.localhost", port: 9527 },
        // 可以添加更多托管服务
      ];
      
      for (const { host: targetHost, port: targetPort } of targetServices) {
        try {
          const checkUrl = `http://${targetHost}:${targetPort}/wba/hosted-did/check/${requesterId}`;
          
          const response = await fetch(checkUrl);
          
          if (response.ok) {
            const result: any = await response.json();
            if (result.success && result.results) {
              for (const res of result.results) {
                res.source_host = targetHost;
                res.source_port = targetPort;
              }
              allResults.push(...result.results);
            }
          }
          
        } catch (error) {
          console.warn(`检查托管服务 ${targetHost}:${targetPort} 失败: ${error}`);
        }
      }
      
      return { success: true, results: allResults, error: "" };
      
    } catch (error) {
      const errorMsg = `检查托管DID结果失败: ${error}`;
      console.error(errorMsg);
      return { success: false, results: [], error: errorMsg };
    }
  }

  /**
   * 处理托管DID结果
   * 对应Python版本的process_hosted_did_results
   */
  public async processHostedDidResults(results: any[]): Promise<number> {
    let processedCount = 0;
    
    for (const result of results) {
      try {
        if (result.success && result.hosted_did_document) {
          const hostedDidDoc = result.hosted_did_document;
          const sourceHost = result.source_host || 'unknown';
          const sourcePort = result.source_port || 9527;
          
          // 使用现有的createHostedDid方法
          const { success, userData: hostedResult } = await this.createHostedDid(
            sourceHost, sourcePort.toString(), hostedDidDoc
          );
          
          if (success) {
            // 确认收到结果
            await this.acknowledgeHostedDidResult(
              result.result_id || '', sourceHost, sourcePort
            );
            
            console.debug(`托管DID已保存: ${hostedResult?.id}`);
            console.debug(`托管DID ID: ${hostedDidDoc.id}`);
            processedCount++;
          } else {
            console.error(`保存托管DID失败: ${hostedResult}`);
          }
        } else {
          console.warn(`托管DID申请失败: ${result.error_message || '未知错误'}`);
        }
        
      } catch (error) {
        console.error(`处理托管DID结果失败: ${error}`);
      }
    }
    
    return processedCount;
  }

  /**
   * 确认收到托管DID结果
   */
  private async acknowledgeHostedDidResult(resultId: string, sourceHost: string, sourcePort: number): Promise<void> {
    try {
      if (!resultId) {
        return;
      }
      
      const ackUrl = `http://${sourceHost}:${sourcePort}/wba/hosted-did/acknowledge/${resultId}`;
      
      const response = await fetch(ackUrl, { method: 'POST' });
      if (response.ok) {
        console.debug(`已确认托管DID结果: ${resultId}`);
      } else {
        console.warn(`确认托管DID结果失败: ${response.status}`);
      }
      
    } catch (error) {
      console.warn(`确认托管DID结果时出错: ${error}`);
    }
  }

  /**
   * 轮询托管DID结果
   * 对应Python版本的poll_hosted_did_results
   */
  public async pollHostedDidResults(interval: number = 30, maxPolls: number = 20): Promise<number> {
    let totalProcessed = 0;
    
    for (let i = 0; i < maxPolls; i++) {
      try {
        const { success, results, error } = await this.checkHostedDidResults();
        
        if (success && results.length > 0) {
          const processed = await this.processHostedDidResults(results);
          totalProcessed += processed;
          
          if (processed > 0) {
            console.debug(`轮询第${i + 1}次: 处理了${processed}个托管DID结果`);
          }
        }
        
        if (i < maxPolls - 1) { // 不是最后一次
          await new Promise(resolve => setTimeout(resolve, interval * 1000));
        }
        
      } catch (error) {
        console.error(`轮询托管DID结果失败: ${error}`);
        await new Promise(resolve => setTimeout(resolve, interval * 1000));
      }
    }
    
    return totalProcessed;
  }

  /**
   * 创建一个托管DID
   * 对应Python版本的create_hosted_did
   */
  public async createHostedDid(host: string, port: string, didDocument: DIDDocument): Promise<{
    success: boolean;
    userData?: ANPUser;
    error?: string;
  }> {
    const manager = getUserDataManager();
    const result = await manager.createHostedUser(
      this.userData,
      host,
      port,
      didDocument
    );
    
    if (result.success && result.userData) {
      // 使用缓存机制创建ANPUser实例
      const hostedDid = result.userData.did;
      if (ANPUser.instances.has(hostedDid)) {
        console.debug(`🔄 复用ANPUser实例 (托管DID): ${hostedDid}`);
        return { success: true, userData: ANPUser.instances.get(hostedDid) };
      }
      
      // 创建新实例并缓存
      const instance = new ANPUser(result.userData);
      ANPUser.instances.set(hostedDid, instance);
      console.debug(`🆕 创建并缓存ANPUser实例 (托管DID): ${hostedDid}`);
      return { success: true, userData: instance };
    }
    
    return { success: false, error: result.error };
  }

  // ============================================================================
  // 连接管理方法
  // ============================================================================

  public addWsConnection(connectionId: string, connection: any): void {
    this.wsConnections.set(connectionId, connection);
  }

  public removeWsConnection(connectionId: string): void {
    this.wsConnections.delete(connectionId);
  }

  public addSseClient(client: any): void {
    this.sseClients.add(client);
  }

  public removeSseClient(client: any): void {
    this.sseClients.delete(client);
  }

  // ============================================================================
  // 工具方法
  // ============================================================================

  public toDict(): Record<string, any> {
    return {
      id: this.id,
      name: this.name,
      agentType: this.agentType,
      userDir: this.userDir,
      isHostedDid: this.isHostedDid,
      parentDid: this.parentDid,
      hostedInfo: this.hostedInfo
    };
  }

  /**
   * 析构函数，确保在对象销毁时释放资源
   */
  public destroy(): void {
    try {
      for (const [id, ws] of this.wsConnections.entries()) {
        console.debug(`LocalAgent ${this.id} 销毁时存在未关闭的WebSocket连接: ${id}`);
      }
      this.wsConnections.clear();
      this.sseClients.clear();
      console.debug(`LocalAgent ${this.id} 资源已释放`);
    } catch (error) {
      // 忽略错误
    }
  }
}