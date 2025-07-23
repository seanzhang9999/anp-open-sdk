/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import { DIDDocument, DIDWbaAuth, DIDWbaAuthClient, VerifyResult } from '../did';
import { getLogger } from '../utils';

const logger = getLogger('Auth');

export interface AuthResult {
  success: boolean;
  callerDid?: string;
  error?: string;
  payload?: any;
}

export class AuthInitiator {
  private authClient: DIDWbaAuthClient;

  constructor(didDocumentPath: string, privateKeyPath: string) {
    this.authClient = new DIDWbaAuthClient(didDocumentPath, privateKeyPath);
  }

  /**
   * 为HTTP请求添加认证header
   */
  public async addAuthHeader(
    targetDid: string,
    url: string,
    method: string = 'GET',
    headers: Record<string, string> = {},
    body?: any
  ): Promise<Record<string, string>> {
    try {
      const authHeaders = await this.authClient.getAuthHeader(url);
      
      return {
        ...headers,
        ...authHeaders,
        'X-DID-Target': targetDid,
        'Content-Type': 'application/json'
      };
    } catch (error) {
      logger.error('Failed to add auth header:', error);
      throw error;
    }
  }

  /**
   * 更新token从响应头
   */
  public updateToken(serverUrl: string, responseHeaders: Record<string, string>): string | null {
    return this.authClient.updateToken(serverUrl, responseHeaders);
  }

  /**
   * 获取当前DID
   */
  public getDid(): string | null {
    return this.authClient.getDid();
  }

  /**
   * 检查是否准备就绪
   */
  public isReady(): boolean {
    return this.authClient.isReady();
  }
}

export class AuthVerifier {
  private didDocuments: Map<string, DIDDocument> = new Map();

  /**
   * 注册DID文档
   */
  public registerDIDDocument(did: string, didDocument: DIDDocument): void {
    this.didDocuments.set(did, didDocument);
    logger.debug(`Registered DID document for: ${did}`);
  }

  /**
   * 批量注册DID文档
   */
  public registerDIDDocuments(documents: Record<string, DIDDocument>): void {
    for (const [did, doc] of Object.entries(documents)) {
      this.registerDIDDocument(did, doc);
    }
  }

  /**
   * 验证认证请求
   */
  public async verifyAuthRequest(
    authHeader: string, 
    serviceDomain: string,
    expectedDid?: string
  ): Promise<AuthResult> {
    
    try {
      // 检查是否为DIDWba格式
      if (!authHeader.startsWith('DIDWba ')) {
        return { success: false, error: 'Invalid auth header format' };
      }

      // 解析认证头获取DID
      const parts = DIDWbaAuth.extractAuthHeaderParts(authHeader);
      const callerDid = parts.did;

      // 检查是否为期望的DID
      if (expectedDid && callerDid !== expectedDid) {
        return { 
          success: false, 
          error: `Unexpected caller DID: ${callerDid}, expected: ${expectedDid}` 
        };
      }

      // 获取对应的DID文档
      let didDocument = this.didDocuments.get(callerDid);
      
      if (!didDocument) {
        // 尝试动态解析DID文档
        try {
          didDocument = await DIDWbaAuth.resolveDidWbaDocument(callerDid);
          this.registerDIDDocument(callerDid, didDocument);
        } catch (error) {
          return { 
            success: false, 
            error: `Failed to resolve DID document for ${callerDid}: ${error}` 
          };
        }
      }

      // 验证签名
      const result: VerifyResult = await DIDWbaAuth.verifyAuthHeaderSignature(
        authHeader,
        didDocument,
        serviceDomain
      );

      return {
        success: result.valid,
        callerDid: result.valid ? callerDid : undefined,
        payload: result.payload,
        error: result.valid ? undefined : result.message
      };

    } catch (error) {
      logger.error('Auth verification error:', error);
      return {
        success: false,
        error: `Auth verification failed: ${error}`
      };
    }
  }

  /**
   * 检查DID是否已注册
   */
  public hasDID(did: string): boolean {
    return this.didDocuments.has(did);
  }

  /**
   * 获取已注册的DID列表
   */
  public getRegisteredDIDs(): string[] {
    return Array.from(this.didDocuments.keys());
  }

  /**
   * 清理过期的DID文档缓存
   */
  public clearCache(): void {
    this.didDocuments.clear();
    logger.debug('DID document cache cleared');
  }
}

export class AuthManager {
  private initiator: AuthInitiator | null = null;
  private verifier: AuthVerifier;

  constructor(didDocumentPath?: string, privateKeyPath?: string) {
    if (didDocumentPath && privateKeyPath) {
      this.initiator = new AuthInitiator(didDocumentPath, privateKeyPath);
    }
    this.verifier = new AuthVerifier();
  }

  public getInitiator(): AuthInitiator {
    if (!this.initiator) {
      throw new Error('AuthInitiator not initialized. Provide didDocumentPath and privateKeyPath.');
    }
    return this.initiator;
  }

  public getVerifier(): AuthVerifier {
    return this.verifier;
  }

  /**
   * 为其他DID注册DID文档
   */
  public registerPeerDIDDocument(did: string, didDocument: DIDDocument): void {
    this.verifier.registerDIDDocument(did, didDocument);
  }

  /**
   * 批量注册DID文档
   */
  public registerPeerDIDDocuments(documents: Record<string, DIDDocument>): void {
    this.verifier.registerDIDDocuments(documents);
  }
}