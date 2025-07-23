/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { URL } from 'url';
import { DIDDocument, SignCallback } from './types';
import { DIDWbaAuth } from './did-wba';
import { getLogger } from '@foundation/utils';

const logger = getLogger('DIDWbaAuthClient');

export interface TokenInfo {
  token: string;
  expiresAt: number;
}

export class DIDWbaAuthClient {
  private didDocument: DIDDocument | null = null;
  private privateKey: crypto.KeyObject | null = null;
  private authHeaders: Map<string, Record<string, string>> = new Map();
  private tokens: Map<string, TokenInfo> = new Map();

  constructor(
    private didDocumentPath: string,
    private privateKeyPath: string
  ) {
    this.loadCredentials();
    logger.info('DIDWbaAuthClient initialized');
  }

  /**
   * Load DID document and private key from files
   */
  private async loadCredentials(): Promise<void> {
    try {
      // Load DID document
      if (fs.existsSync(this.didDocumentPath)) {
        const didDocContent = fs.readFileSync(this.didDocumentPath, 'utf8');
        this.didDocument = JSON.parse(didDocContent);
        logger.debug('DID document loaded successfully');
      } else {
        logger.warn(`DID document not found: ${this.didDocumentPath}`);
      }

      // Load private key
      if (fs.existsSync(this.privateKeyPath)) {
        const privateKeyPem = fs.readFileSync(this.privateKeyPath, 'utf8');
        this.privateKey = crypto.createPrivateKey(privateKeyPem);
        logger.debug('Private key loaded successfully');
      } else {
        logger.warn(`Private key not found: ${this.privateKeyPath}`);
      }
    } catch (error) {
      logger.error('Failed to load credentials:', error);
      throw error;
    }
  }

  /**
   * Get domain from server URL
   */
  private getDomain(serverUrl: string): string {
    try {
      const url = new URL(serverUrl);
      return url.hostname;
    } catch (error) {
      logger.error(`Invalid server URL: ${serverUrl}`);
      throw new Error(`Invalid server URL: ${serverUrl}`);
    }
  }

  /**
   * Create sign callback using loaded private key
   */
  private createSignCallback(): SignCallback {
    if (!this.privateKey) {
      throw new Error('Private key not loaded');
    }

    return async (data: Uint8Array): Promise<Uint8Array> => {
      try {
        const signature = crypto.sign('sha256', data, this.privateKey!);
        return new Uint8Array(signature);
      } catch (error) {
        logger.error('Signing failed:', error);
        throw error;
      }
    };
  }

  /**
   * Generate new authentication header
   */
  private async generateNewAuthHeader(serverUrl: string): Promise<Record<string, string>> {
    if (!this.didDocument) {
      throw new Error('DID document not loaded');
    }

    const domain = this.getDomain(serverUrl);
    const signCallback = this.createSignCallback();
    
    try {
      const authHeader = await DIDWbaAuth.generateAuthHeader(
        this.didDocument,
        domain,
        signCallback
      );

      return {
        'Authorization': authHeader,
        'X-DID-Caller': this.didDocument.id
      };
    } catch (error) {
      logger.error('Failed to generate auth header:', error);
      throw error;
    }
  }

  /**
   * Get authentication headers for server URL
   */
  public async getAuthHeader(
    serverUrl: string, 
    forceNew: boolean = false
  ): Promise<Record<string, string>> {
    
    const domain = this.getDomain(serverUrl);

    // Check if we have cached headers and they're still valid
    if (!forceNew && this.authHeaders.has(domain)) {
      const cached = this.authHeaders.get(domain)!;
      
      // Check if we have a valid token
      const tokenInfo = this.tokens.get(domain);
      if (tokenInfo && Date.now() < tokenInfo.expiresAt) {
        logger.debug(`Using cached auth header for domain: ${domain}`);
        return {
          ...cached,
          'Authorization': `Bearer ${tokenInfo.token}`
        };
      }
    }

    // Generate new auth header
    logger.debug(`Generating new auth header for domain: ${domain}`);
    const authHeaders = await this.generateNewAuthHeader(serverUrl);
    
    // Cache the headers
    this.authHeaders.set(domain, authHeaders);
    
    return authHeaders;
  }

  /**
   * Update token from server response
   */
  public updateToken(serverUrl: string, responseHeaders: Record<string, string>): string | null {
    const domain = this.getDomain(serverUrl);
    
    // Look for token in various header formats
    const tokenHeader = responseHeaders['x-auth-token'] || 
                       responseHeaders['X-Auth-Token'] ||
                       responseHeaders['authorization']?.replace(/^Bearer\s+/i, '');

    if (tokenHeader) {
      // Default token expiry (30 minutes)
      const expiresAt = Date.now() + (30 * 60 * 1000);
      
      // Check for explicit expiry header
      const expiryHeader = responseHeaders['x-token-expires'] || 
                          responseHeaders['X-Token-Expires'];
      
      let finalExpiresAt = expiresAt;
      if (expiryHeader) {
        const expiryTime = new Date(expiryHeader).getTime();
        if (!isNaN(expiryTime)) {
          finalExpiresAt = expiryTime;
        }
      }

      this.tokens.set(domain, {
        token: tokenHeader,
        expiresAt: finalExpiresAt
      });

      logger.debug(`Token updated for domain: ${domain}, expires: ${new Date(finalExpiresAt)}`);
      return tokenHeader;
    }

    return null;
  }

  /**
   * Clear token for domain
   */
  public clearToken(serverUrl: string): void {
    const domain = this.getDomain(serverUrl);
    this.tokens.delete(domain);
    this.authHeaders.delete(domain);
    logger.debug(`Token cleared for domain: ${domain}`);
  }

  /**
   * Clear all tokens and cached headers
   */
  public clearAllTokens(): void {
    this.tokens.clear();
    this.authHeaders.clear();
    logger.debug('All tokens and cached headers cleared');
  }

  /**
   * Get current DID
   */
  public getDid(): string | null {
    return this.didDocument?.id || null;
  }

  /**
   * Check if credentials are loaded
   */
  public isReady(): boolean {
    return !!(this.didDocument && this.privateKey);
  }

  /**
   * Get token info for domain
   */
  public getTokenInfo(serverUrl: string): TokenInfo | null {
    const domain = this.getDomain(serverUrl);
    return this.tokens.get(domain) || null;
  }

  /**
   * Verify if token is still valid
   */
  public isTokenValid(serverUrl: string): boolean {
    const tokenInfo = this.getTokenInfo(serverUrl);
    return tokenInfo ? Date.now() < tokenInfo.expiresAt : false;
  }

  /**
   * Refresh credentials from disk
   */
  public async refreshCredentials(): Promise<void> {
    await this.loadCredentials();
    this.clearAllTokens(); // Clear cached tokens since credentials changed
    logger.info('Credentials refreshed from disk');
  }

  /**
   * Get statistics about cached tokens
   */
  public getStats(): {
    totalDomains: number;
    validTokens: number;
    expiredTokens: number;
  } {
    const now = Date.now();
    let validTokens = 0;
    let expiredTokens = 0;

    for (const tokenInfo of this.tokens.values()) {
      if (now < tokenInfo.expiresAt) {
        validTokens++;
      } else {
        expiredTokens++;
      }
    }

    return {
      totalDomains: this.tokens.size,
      validTokens,
      expiredTokens
    };
  }
}