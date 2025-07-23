/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as path from 'path';

export interface UserData {
  did: string;
  name?: string;
  userDir: string;
  didDocPath: string;
  didPrivateKeyFilePath: string;
  jwtPrivateKeyFilePath: string;
  jwtPublicKeyFilePath: string;
  isHostedDid: boolean;
  parentDid?: string;
  hostedInfo?: any;
}

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
      const parsed = this.parseDidHostPort(this.id);
      if (parsed) {
        this.host = parsed.host;
        this.port = parsed.port;
      }
    }
  }

  private parseDidHostPort(did: string): { host: string; port: number } | null {
    // 简化的DID解析逻辑，需要根据实际DID格式实现
    try {
      const match = did.match(/did:wba:(.+?)_(\d+)_/);
      if (match) {
        return {
          host: match[1],
          port: parseInt(match[2], 10)
        };
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

export class ANPUser {
  private static instances = new Map<string, ANPUser>();

  public userData: UserData;
  public id: string;
  public name: string;
  public userDir: string;
  public agentType: string;
  public keyId: string;
  
  // File paths
  public didDocumentPath: string;
  public privateKeyPath: string;
  public jwtPrivateKeyPath: string;
  public jwtPublicKeyPath: string;
  
  // WebSocket and SSE connections
  private wsConnections: Map<string, any> = new Map();
  private sseClients: Set<any> = new Set();
  
  // Hosted DID properties
  public isHostedDid: boolean;
  public parentDid?: string;
  public hostedInfo?: any;
  
  // Group related
  public groupQueues: Map<string, Map<string, any>> = new Map();
  public groupMembers: Map<string, Set<string>> = new Map();

  constructor(userData: UserData, name: string = "未命名", agentType: string = "personal") {
    this.userData = userData;
    this.userDir = userData.userDir;
    
    if (name === "未命名") {
      this.name = userData.name || `未命名智能体${userData.did}`;
    } else {
      this.name = name;
    }
    
    this.id = userData.did;
    this.agentType = agentType;
    
    // Cache instance
    if (!ANPUser.instances.has(this.id)) {
      ANPUser.instances.set(this.id, this);
      console.debug(`🆕 缓存ANPUser实例: ${this.id}`);
    } else {
      console.debug(`🔄 ANPUser实例已存在于缓存中: ${this.id}`);
    }
    
    // Set key ID (would need config integration)
    this.keyId = "key-1"; // Default, should come from config
    
    // Set file paths
    this.didDocumentPath = userData.didDocPath;
    this.privateKeyPath = userData.didPrivateKeyFilePath;
    this.jwtPrivateKeyPath = userData.jwtPrivateKeyFilePath;
    this.jwtPublicKeyPath = userData.jwtPublicKeyFilePath;
    
    // Hosted DID properties
    this.isHostedDid = userData.isHostedDid;
    this.parentDid = userData.parentDid;
    this.hostedInfo = userData.hostedInfo;
  }

  public static getInstance(did: string): ANPUser | undefined {
    return ANPUser.instances.get(did);
  }

  public static getAllInstances(): ANPUser[] {
    return Array.from(ANPUser.instances.values());
  }

  public async sendMessage(targetDid: string, message: any): Promise<any> {
    // Message sending implementation
    throw new Error("sendMessage not yet implemented");
  }

  public async callApi(targetDid: string, endpoint: string, payload: any): Promise<any> {
    // API call implementation  
    throw new Error("callApi not yet implemented");
  }

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

  public toDict(): Record<string, any> {
    return {
      id: this.id,
      name: this.name,
      agentType: this.agentType,
      userDir: this.userDir,
      isHostedDid: this.isHostedDid,
      parentDid: this.parentDid
    };
  }
}