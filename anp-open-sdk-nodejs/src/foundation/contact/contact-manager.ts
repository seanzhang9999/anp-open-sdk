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

import { LocalUserData } from '../user/local-user-data';
import { Contact, TokenInfo } from '../types';

/**
 * 联系人管理器
 * 提供独立的联系人服务，包括联系人管理和token管理
 */
export class ContactManager {
  private userData: LocalUserData;
  private contacts: Map<string, Contact> = new Map(); // did -> contact
  private tokenToRemote: Map<string, TokenInfo> = new Map(); // did -> token
  private tokenFromRemote: Map<string, TokenInfo> = new Map(); // did -> token

  constructor(userData: LocalUserData) {
    this.userData = userData;
    this.loadContacts();
  }

  /**
   * 加载联系人和token信息到缓存
   */
  private loadContacts(): void {
    // 加载联系人列表
    const contacts = this.userData.listContacts();
    for (const contact of contacts) {
      this.contacts.set(contact.did, contact);
      
      // 加载对应的token信息
      const tokenTo = this.userData.getTokenToRemote(contact.did);
      if (tokenTo) {
        this.tokenToRemote.set(contact.did, tokenTo);
      }
      
      const tokenFrom = this.userData.getTokenFromRemote(contact.did);
      if (tokenFrom) {
        this.tokenFromRemote.set(contact.did, tokenFrom);
      }
    }
  }

  /**
   * 添加联系人
   */
  addContact(contact: Contact): void {
    this.contacts.set(contact.did, contact);
    this.userData.addContact(contact);
  }

  /**
   * 获取联系人
   */
  getContact(did: string): Contact | undefined {
    return this.contacts.get(did);
  }

  /**
   * 列出所有联系人
   */
  listContacts(): Contact[] {
    return Array.from(this.contacts.values());
  }

  /**
   * 存储发送给远程的token
   */
  storeTokenToRemote(remoteDid: string, token: string, expiresDelta: number): void {
    this.userData.storeTokenToRemote(remoteDid, token, expiresDelta);
    const tokenInfo = this.userData.getTokenToRemote(remoteDid);
    if (tokenInfo) {
      this.tokenToRemote.set(remoteDid, tokenInfo);
    }
  }

  /**
   * 获取发送给远程的token
   */
  getTokenToRemote(remoteDid: string): TokenInfo | undefined {
    return this.tokenToRemote.get(remoteDid);
  }

  /**
   * 存储从远程接收的token
   */
  storeTokenFromRemote(remoteDid: string, token: string): void {
    this.userData.storeTokenFromRemote(remoteDid, token);
    const tokenInfo = this.userData.getTokenFromRemote(remoteDid);
    if (tokenInfo) {
      this.tokenFromRemote.set(remoteDid, tokenInfo);
    }
  }

  /**
   * 获取从远程接收的token
   */
  getTokenFromRemote(remoteDid: string): TokenInfo | undefined {
    return this.tokenFromRemote.get(remoteDid);
  }

  /**
   * 撤销发送给远程的token
   */
  revokeTokenToRemote(remoteDid: string): void {
    this.userData.revokeTokenToRemote(remoteDid);
    this.tokenToRemote.delete(remoteDid);
  }

  /**
   * 撤销从远程接收的token
   */
  revokeTokenFromRemote(targetDid: string): void {
    const tokenInfo = this.tokenFromRemote.get(targetDid);
    if (tokenInfo) {
      tokenInfo.is_revoked = true;
      this.tokenFromRemote.set(targetDid, tokenInfo);
    }
  }

  /**
   * 检查token是否有效
   */
  isTokenValid(remoteDid: string, direction: 'to' | 'from'): boolean {
    const tokenMap = direction === 'to' ? this.tokenToRemote : this.tokenFromRemote;
    const tokenInfo = tokenMap.get(remoteDid);
    
    if (!tokenInfo || tokenInfo.is_revoked) {
      return false;
    }

    // 检查过期时间（如果有）
    if (tokenInfo.expires_at) {
      const now = new Date();
      const expiresAt = new Date(tokenInfo.expires_at);
      return now < expiresAt;
    }

    return true;
  }

  /**
   * 清理过期的token
   */
  cleanupExpiredTokens(): number {
    let cleanedCount = 0;
    const now = new Date();

    // 清理发送给远程的过期token
    for (const [did, tokenInfo] of this.tokenToRemote.entries()) {
      if (tokenInfo.expires_at) {
        const expiresAt = new Date(tokenInfo.expires_at);
        if (now >= expiresAt) {
          this.tokenToRemote.delete(did);
          cleanedCount++;
        }
      }
    }

    // 清理从远程接收的过期token（如果有过期时间）
    for (const [did, tokenInfo] of this.tokenFromRemote.entries()) {
      if (tokenInfo.expires_at) {
        const expiresAt = new Date(tokenInfo.expires_at);
        if (now >= expiresAt) {
          this.tokenFromRemote.delete(did);
          cleanedCount++;
        }
      }
    }

    return cleanedCount;
  }

  /**
   * 获取token统计信息
   */
  getTokenStats(): {
    toRemoteCount: number;
    fromRemoteCount: number;
    validToRemoteCount: number;
    validFromRemoteCount: number;
  } {
    let validToRemoteCount = 0;
    let validFromRemoteCount = 0;

    for (const [did] of this.tokenToRemote.entries()) {
      if (this.isTokenValid(did, 'to')) {
        validToRemoteCount++;
      }
    }

    for (const [did] of this.tokenFromRemote.entries()) {
      if (this.isTokenValid(did, 'from')) {
        validFromRemoteCount++;
      }
    }

    return {
      toRemoteCount: this.tokenToRemote.size,
      fromRemoteCount: this.tokenFromRemote.size,
      validToRemoteCount,
      validFromRemoteCount
    };
  }
}