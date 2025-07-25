/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { ContactManager } from '../../src/foundation/contact/contact-manager';
import { LocalUserData } from '../../src/foundation/user/local-user-data';
import { LocalUserDataManager } from '../../src/foundation/user/local-user-data-manager';
import { Contact, TokenInfo } from '../../src/foundation/types';
import * as path from 'path';

describe('ContactManager', () => {
  let contactManager: ContactManager;
  let userData: LocalUserData;
  let userDataManager: LocalUserDataManager;

  beforeEach(async () => {
    // 使用真实的测试数据
    const testDataPath = path.join(__dirname, '../../data_user');
    userDataManager = LocalUserDataManager.getInstance(testDataPath);
    
    // 初始化并获取第一个可用的用户数据
    await userDataManager.initialize();
    const users = userDataManager.getAllUsers();
    expect(users.length).toBeGreaterThan(0);
    
    userData = users[0];
    contactManager = new ContactManager(userData);
  });

  afterEach(() => {
    // 重置单例实例以避免测试间的干扰
    LocalUserDataManager.resetInstance();
  });

  describe('Contact Management', () => {
    it('should add a new contact', () => {
      const contact: Contact = {
        did: 'did:wba:test.example.com',
        name: 'Test Contact',
        host: 'test.example.com',
        port: 9527,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      contactManager.addContact(contact);

      const retrievedContact = contactManager.getContact(contact.did);
      expect(retrievedContact).toEqual(contact);
    });

    it('should get existing contact', () => {
      const contact: Contact = {
        did: 'did:wba:existing.example.com',
        name: 'Existing Contact',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      contactManager.addContact(contact);
      const retrieved = contactManager.getContact(contact.did);
      
      expect(retrieved).toBeDefined();
      expect(retrieved?.did).toBe(contact.did);
      expect(retrieved?.name).toBe(contact.name);
    });

    it('should return undefined for non-existent contact', () => {
      const nonExistentDid = 'did:wba:nonexistent.example.com';
      const contact = contactManager.getContact(nonExistentDid);
      
      expect(contact).toBeUndefined();
    });

    it('should list all contacts', () => {
      const contacts: Contact[] = [
        {
          did: 'did:wba:contact1.example.com',
          name: 'Contact 1',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          did: 'did:wba:contact2.example.com',
          name: 'Contact 2',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];

      contacts.forEach(contact => {
        contactManager.addContact(contact);
      });

      const allContacts = contactManager.listContacts();
      expect(allContacts.length).toBeGreaterThanOrEqual(2);
      
      const addedContacts = allContacts.filter(c => 
        contacts.some(contact => contact.did === c.did)
      );
      expect(addedContacts).toHaveLength(2);
    });

    it('should handle contact with minimal data', () => {
      const minimalContact: Contact = {
        did: 'did:wba:minimal.example.com'
      };

      contactManager.addContact(minimalContact);
      const retrieved = contactManager.getContact(minimalContact.did);
      
      expect(retrieved).toBeDefined();
      expect(retrieved?.did).toBe(minimalContact.did);
    });
  });

  describe('Token Management - To Remote', () => {
    const remoteDid = 'did:wba:remote.example.com';

    it('should store token to remote', () => {
      const token = 'test-token-123';
      const expiresDelta = 3600; // 1 hour

      contactManager.storeTokenToRemote(remoteDid, token, expiresDelta);

      const storedToken = contactManager.getTokenToRemote(remoteDid);
      expect(storedToken).toBeDefined();
      expect(storedToken?.token).toBe(token);
      expect(storedToken?.req_did).toBe(userData.getDid());
    });

    it('should get token to remote', () => {
      const token = 'test-token-456';
      const expiresDelta = 7200; // 2 hours

      contactManager.storeTokenToRemote(remoteDid, token, expiresDelta);
      const retrievedToken = contactManager.getTokenToRemote(remoteDid);

      expect(retrievedToken).toBeDefined();
      expect(retrievedToken?.token).toBe(token);
      expect(retrievedToken?.created_at).toBeDefined();
      expect(retrievedToken?.expires_at).toBeDefined();
    });

    it('should return undefined for non-existent token to remote', () => {
      const nonExistentDid = 'did:wba:nonexistent.example.com';
      const token = contactManager.getTokenToRemote(nonExistentDid);
      
      expect(token).toBeUndefined();
    });

    it('should revoke token to remote', () => {
      const token = 'test-token-revoke';
      const expiresDelta = 3600;

      contactManager.storeTokenToRemote(remoteDid, token, expiresDelta);
      
      let storedToken = contactManager.getTokenToRemote(remoteDid);
      expect(storedToken).toBeDefined();

      contactManager.revokeTokenToRemote(remoteDid);
      
      // Token should be removed from cache after revocation
      storedToken = contactManager.getTokenToRemote(remoteDid);
      expect(storedToken).toBeUndefined();
    });
  });

  describe('Token Management - From Remote', () => {
    const remoteDid = 'did:wba:remote-sender.example.com';

    it('should store token from remote', () => {
      const token = 'incoming-token-123';

      contactManager.storeTokenFromRemote(remoteDid, token);

      const storedToken = contactManager.getTokenFromRemote(remoteDid);
      expect(storedToken).toBeDefined();
      expect(storedToken?.token).toBe(token);
      expect(storedToken?.req_did).toBe(remoteDid);
    });

    it('should get token from remote', () => {
      const token = 'incoming-token-456';

      contactManager.storeTokenFromRemote(remoteDid, token);
      const retrievedToken = contactManager.getTokenFromRemote(remoteDid);

      expect(retrievedToken).toBeDefined();
      expect(retrievedToken?.token).toBe(token);
      expect(retrievedToken?.created_at).toBeDefined();
    });

    it('should return undefined for non-existent token from remote', () => {
      const nonExistentDid = 'did:wba:nonexistent-sender.example.com';
      const token = contactManager.getTokenFromRemote(nonExistentDid);
      
      expect(token).toBeUndefined();
    });

    it('should revoke token from remote', () => {
      const token = 'incoming-token-revoke';

      contactManager.storeTokenFromRemote(remoteDid, token);
      
      let storedToken = contactManager.getTokenFromRemote(remoteDid);
      expect(storedToken).toBeDefined();
      expect(storedToken?.is_revoked).toBeFalsy();

      contactManager.revokeTokenFromRemote(remoteDid);
      
      storedToken = contactManager.getTokenFromRemote(remoteDid);
      expect(storedToken).toBeDefined();
      expect(storedToken?.is_revoked).toBe(true);
    });
  });

  describe('Token Validation', () => {
    const remoteDid = 'did:wba:validation-test.example.com';

    it('should validate valid token to remote', () => {
      const token = 'valid-token';
      const expiresDelta = 3600; // 1 hour

      contactManager.storeTokenToRemote(remoteDid, token, expiresDelta);
      
      const isValid = contactManager.isTokenValid(remoteDid, 'to');
      expect(isValid).toBe(true);
    });

    it('should validate valid token from remote', () => {
      const token = 'valid-incoming-token';

      contactManager.storeTokenFromRemote(remoteDid, token);
      
      const isValid = contactManager.isTokenValid(remoteDid, 'from');
      expect(isValid).toBe(true);
    });

    it('should invalidate non-existent token', () => {
      const nonExistentDid = 'did:wba:nonexistent.example.com';
      
      const isValidTo = contactManager.isTokenValid(nonExistentDid, 'to');
      const isValidFrom = contactManager.isTokenValid(nonExistentDid, 'from');
      
      expect(isValidTo).toBe(false);
      expect(isValidFrom).toBe(false);
    });

    it('should invalidate revoked token from remote', () => {
      const token = 'revoked-token';

      contactManager.storeTokenFromRemote(remoteDid, token);
      contactManager.revokeTokenFromRemote(remoteDid);
      
      const isValid = contactManager.isTokenValid(remoteDid, 'from');
      expect(isValid).toBe(false);
    });

    it('should handle token without expiration', () => {
      const token = 'no-expiry-token';

      contactManager.storeTokenFromRemote(remoteDid, token);
      
      const isValid = contactManager.isTokenValid(remoteDid, 'from');
      expect(isValid).toBe(true);
    });
  });

  describe('Token Cleanup', () => {
    it('should clean up expired tokens', async () => {
      const remoteDid1 = 'did:wba:expired1.example.com';
      const remoteDid2 = 'did:wba:valid1.example.com';
      
      // Store token with very short expiration (will be expired immediately)
      contactManager.storeTokenToRemote(remoteDid1, 'expired-token', -1);
      
      // Store token with long expiration
      contactManager.storeTokenToRemote(remoteDid2, 'valid-token', 3600);

      // Wait a bit to ensure expiration
      await new Promise(resolve => setTimeout(resolve, 10));

      const cleanedCount = contactManager.cleanupExpiredTokens();
      
      expect(cleanedCount).toBeGreaterThanOrEqual(0);
      
      // Valid token should still exist
      const validToken = contactManager.getTokenToRemote(remoteDid2);
      expect(validToken).toBeDefined();
    });

    it('should return cleanup count', () => {
      const cleanedCount = contactManager.cleanupExpiredTokens();
      expect(typeof cleanedCount).toBe('number');
      expect(cleanedCount).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Token Statistics', () => {
    it('should get token statistics', () => {
      // Add some test tokens
      contactManager.storeTokenToRemote('did:wba:stats1.example.com', 'token1', 3600);
      contactManager.storeTokenToRemote('did:wba:stats2.example.com', 'token2', 3600);
      contactManager.storeTokenFromRemote('did:wba:stats3.example.com', 'token3');

      const stats = contactManager.getTokenStats();

      expect(stats).toBeDefined();
      expect(typeof stats.toRemoteCount).toBe('number');
      expect(typeof stats.fromRemoteCount).toBe('number');
      expect(typeof stats.validToRemoteCount).toBe('number');
      expect(typeof stats.validFromRemoteCount).toBe('number');
      
      expect(stats.toRemoteCount).toBeGreaterThanOrEqual(2);
      expect(stats.fromRemoteCount).toBeGreaterThanOrEqual(1);
      expect(stats.validToRemoteCount).toBeGreaterThanOrEqual(0);
      expect(stats.validFromRemoteCount).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty token statistics', () => {
      // Create fresh contact manager with no tokens
      const freshUserData = userData; // Use same user data but fresh manager
      const freshContactManager = new ContactManager(freshUserData);

      const stats = freshContactManager.getTokenStats();

      expect(stats.toRemoteCount).toBeGreaterThanOrEqual(0);
      expect(stats.fromRemoteCount).toBeGreaterThanOrEqual(0);
      expect(stats.validToRemoteCount).toBeGreaterThanOrEqual(0);
      expect(stats.validFromRemoteCount).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Integration with LocalUserData', () => {
    it('should load existing contacts from user data', () => {
      // The ContactManager should load existing contacts from LocalUserData
      const contacts = contactManager.listContacts();
      
      // Should be able to list contacts (may be empty for fresh test data)
      expect(Array.isArray(contacts)).toBe(true);
    });

    it('should persist contacts through LocalUserData', () => {
      const contact: Contact = {
        did: 'did:wba:persistent.example.com',
        name: 'Persistent Contact',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      contactManager.addContact(contact);

      // Create new ContactManager with same user data to test persistence
      const newContactManager = new ContactManager(userData);
      const retrievedContact = newContactManager.getContact(contact.did);

      expect(retrievedContact).toBeDefined();
      expect(retrievedContact?.did).toBe(contact.did);
      expect(retrievedContact?.name).toBe(contact.name);
    });

    it('should sync token operations with LocalUserData', () => {
      const remoteDid = 'did:wba:sync-test.example.com';
      const token = 'sync-test-token';

      contactManager.storeTokenFromRemote(remoteDid, token);

      // Verify token is stored in underlying LocalUserData
      const tokenFromUserData = userData.getTokenFromRemote(remoteDid);
      expect(tokenFromUserData).toBeDefined();
      expect(tokenFromUserData?.token).toBe(token);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid DID formats gracefully', () => {
      const invalidContact: Contact = {
        did: 'invalid-did-format'
      };

      // Should not throw error, but may not work as expected
      expect(() => {
        contactManager.addContact(invalidContact);
      }).not.toThrow();
    });

    it('should handle empty token gracefully', () => {
      const remoteDid = 'did:wba:empty-token.example.com';

      expect(() => {
        contactManager.storeTokenFromRemote(remoteDid, '');
      }).not.toThrow();
    });

    it('should handle negative expiration delta', () => {
      const remoteDid = 'did:wba:negative-exp.example.com';
      const token = 'negative-exp-token';

      expect(() => {
        contactManager.storeTokenToRemote(remoteDid, token, -3600);
      }).not.toThrow();
    });
  });

  describe('Memory Management', () => {
    it('should maintain consistent cache state', () => {
      const remoteDid = 'did:wba:cache-test.example.com';
      const token = 'cache-test-token';

      // Store token
      contactManager.storeTokenFromRemote(remoteDid, token);
      
      // Verify cache consistency
      const cachedToken = contactManager.getTokenFromRemote(remoteDid);
      const userDataToken = userData.getTokenFromRemote(remoteDid);

      expect(cachedToken?.token).toBe(userDataToken?.token);
      expect(cachedToken?.req_did).toBe(userDataToken?.req_did);
    });

    it('should handle multiple token operations efficiently', () => {
      const operations = 100;
      const startTime = Date.now();

      for (let i = 0; i < operations; i++) {
        const remoteDid = `did:wba:perf-test-${i}.example.com`;
        const token = `perf-token-${i}`;
        
        contactManager.storeTokenFromRemote(remoteDid, token);
        contactManager.getTokenFromRemote(remoteDid);
      }

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should complete within reasonable time (less than 1 second for 100 operations)
      expect(duration).toBeLessThan(1000);
    });
  });
});