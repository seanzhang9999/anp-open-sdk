/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import { SignJWT, jwtVerify, importPKCS8, importSPKI } from 'jose';

export interface AuthenticationContext {
  callerDid: string;
  targetDid: string;
  requestUrl: string;
  method?: string;
  timestamp?: Date;
  nonce?: string;
  customHeaders?: Record<string, string>;
  jsonData?: Record<string, any>;
  useTwoWayAuth?: boolean;
  domain?: string;
}

export interface DidComponents {
  method: string;
  identifier: string;
  host?: string;
  port?: number;
  path?: string;
}

export class DidTool {
  /**
   * 解析WBA DID中的host和port
   */
  public static parseWbaDidHostPort(did: string): { host: string; port: number } | null {
    try {
      // 支持两种格式:
      // 1. did:wba:host_port_identifier (旧格式)
      // 2. did:wba:localhost%3A9527:wba:user:identifier (新格式，URL编码)
      
      // 先尝试新格式 (URL编码格式)
      const urlEncodedMatch = did.match(/^did:wba:([^:]+)%3A(\d+):/);
      if (urlEncodedMatch) {
        return {
          host: decodeURIComponent(urlEncodedMatch[1]),
          port: parseInt(urlEncodedMatch[2], 10)
        };
      }
      
      // 再尝试旧格式
      const oldFormatMatch = did.match(/^did:wba:(.+?)_(\d+)_(.+)$/);
      if (oldFormatMatch) {
        return {
          host: oldFormatMatch[1],
          port: parseInt(oldFormatMatch[2], 10)
        };
      }
    } catch (error) {
      console.warn('Failed to parse WBA DID:', error);
    }
    return null;
  }

  /**
   * 解析DID格式
   */
  public static parseDid(did: string): DidComponents | null {
    try {
      const parts = did.split(':');
      if (parts.length < 3 || parts[0] !== 'did') {
        return null;
      }

      const components: DidComponents = {
        method: parts[1],
        identifier: parts.slice(2).join(':')
      };

      // 对于WBA方法，解析host/port
      if (components.method === 'wba') {
        const hostPort = this.parseWbaDidHostPort(did);
        if (hostPort) {
          components.host = hostPort.host;
          components.port = hostPort.port;
        }
      }

      return components;
    } catch (error) {
      console.warn('Failed to parse DID:', error);
      return null;
    }
  }

  /**
   * 生成随机nonce
   */
  public static generateNonce(): string {
    return crypto.randomBytes(16).toString('hex');
  }

  /**
   * 创建JWT认证token
   */
  public static async createAuthToken(
    privateKey: string,
    context: AuthenticationContext
  ): Promise<string> {
    try {
      const key = await importPKCS8(privateKey, 'RS256');
      
      const payload: any = {
        iss: context.callerDid,
        aud: context.targetDid,
        sub: context.requestUrl,
        method: context.method || 'GET',
        nonce: context.nonce || this.generateNonce(),
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 300 // 5分钟过期
      };

      if (context.jsonData) {
        payload.data = context.jsonData;
      }

      return await new SignJWT(payload)
        .setProtectedHeader({ alg: 'RS256' })
        .sign(key);
    } catch (error) {
      throw new Error(`Failed to create auth token: ${error}`);
    }
  }

  /**
   * 验证JWT认证token
   */
  public static async verifyAuthToken(
    token: string,
    publicKey: string,
    expectedAudience?: string
  ): Promise<any> {
    try {
      const key = await importSPKI(publicKey, 'RS256');
      
      const { payload } = await jwtVerify(token, key, {
        audience: expectedAudience
      });

      return payload;
    } catch (error) {
      throw new Error(`Failed to verify auth token: ${error}`);
    }
  }

  /**
   * 生成DID
   */
  public static generateDid(method: string, host: string, port: number, identifier?: string): string {
    if (method === 'wba') {
      const id = identifier || crypto.randomBytes(8).toString('hex');
      return `did:wba:${host}_${port}_${id}`;
    }
    
    throw new Error(`Unsupported DID method: ${method}`);
  }

  /**
   * 验证DID格式
   */
  public static isValidDid(did: string): boolean {
    return /^did:[a-z0-9]+:.+/.test(did);
  }

  /**
   * 提取认证header中的组件
   */
  public static extractAuthHeaderParts(authHeader: string): Record<string, string> {
    const parts: Record<string, string> = {};
    
    // 简化的header解析
    const matches = authHeader.matchAll(/(\w+)="([^"]+)"/g);
    for (const match of matches) {
      parts[match[1]] = match[2];
    }
    
    return parts;
  }

  /**
   * 构建认证header
   */
  public static buildAuthHeader(params: Record<string, string>): string {
    const parts = Object.entries(params)
      .map(([key, value]) => `${key}="${value}"`)
      .join(', ');
    
    return `DID-Auth ${parts}`;
  }
}

/**
 * 查找用户通过DID
 */
export async function findUserByDid(did: string): Promise<{
  success: boolean;
  didDocument?: any;
  userDir?: string;
  error?: string;
}> {
  try {
    const { LocalUserDataManager } = await import('../user/local-user-data-manager');
    const userDataManager = LocalUserDataManager.getInstance();
    
    // 确保已初始化
    if (!userDataManager.isInitialized()) {
      await userDataManager.initialize();
    }
    
    const userData = userDataManager.getUserData(did);
    if (userData) {
      return {
        success: true,
        didDocument: userData.didDocument,
        userDir: userData.folderName
      };
    }
    
    return {
      success: false,
      error: `User with DID ${did} not found`
    };
  } catch (error) {
    return {
      success: false,
      error: `Error finding user: ${error}`
    };
  }
}