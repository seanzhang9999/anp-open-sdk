/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { AuthInitiator, getAuthInitiator, resetAuthInitiator } from '../../src/foundation/auth/auth-initiator';
import { getUserDataManager } from '../../src/foundation/user';
import { LocalUserData } from '../../src/foundation/user/local-user-data';
import * as path from 'path';

// Mock HTTP requests
const mockHttpResponse = {
  status: 200,
  headers: { 'authorization': 'Bearer test-token' },
  data: { success: true }
};

// Mock getUserDataManager
jest.mock('../../src/foundation/user', () => ({
  getUserDataManager: jest.fn()
}));

describe('AuthInitiator', () => {
  let authInitiator: AuthInitiator;
  let mockUserDataManager: any;
  let mockUserData: any;

  beforeEach(() => {
    // Reset the global instance
    resetAuthInitiator();
    authInitiator = new AuthInitiator();

    // Setup mock user data
    mockUserData = {
      didDocPath: path.join(__dirname, '../data/test-did.json'),
      passwordPaths: {
        did_private_key_file_path: path.join(__dirname, '../data/test-private-key.pem')
      }
    };

    mockUserDataManager = {
      getUserData: jest.fn().mockReturnValue(mockUserData)
    };

    (getUserDataManager as jest.Mock).mockReturnValue(mockUserDataManager);
  });

  afterEach(() => {
    jest.clearAllMocks();
    resetAuthInitiator();
  });

  describe('sendAuthenticatedRequest', () => {
    it('should handle successful two-way authentication', async () => {
      // Mock successful HTTP response with token
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockResolvedValue({
          status: 200,
          headers: { 
            'authorization': JSON.stringify({
              access_token: 'test-token',
              resp_did_auth_header: {
                Authorization: 'DIDWba did="did:wba:target.example.com", nonce="abc123", timestamp="2024-01-01T00:00:00.000Z", resp_did="did:wba:caller.example.com", verification_method="key-1", signature="test-sig"'
              }
            })
          },
          data: { success: true }
        });

      // Mock DID document resolution
      const mockResolveDidDocument = jest.spyOn(authInitiator as any, 'resolveDidDocumentInsecurely')
        .mockResolvedValue({
          id: 'did:wba:target.example.com',
          verificationMethod: [{
            id: 'did:wba:target.example.com#key-1',
            type: 'EcdsaSecp256k1VerificationKey2019',
            controller: 'did:wba:target.example.com',
            publicKeyJwk: {
              kty: 'EC',
              crv: 'secp256k1',
              x: 'test-x',
              y: 'test-y'
            }
          }]
        });

      // Mock signature verification
      const mockVerifyTimestamp = jest.spyOn(authInitiator as any, 'verifyTimestamp')
        .mockReturnValue(true);

      const result = await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api',
        'GET',
        undefined,
        undefined,
        true // use two-way auth
      );

      expect(result.status).toBe(200);
      expect(result.is_auth_pass).toBe(true);
      expect(result.info).toContain('DID双向认证成功');
      expect(mockSendHttpRequest).toHaveBeenCalled();
    });

    it('should fallback to single-way authentication when two-way fails', async () => {
      let callCount = 0;
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockImplementation(() => {
          callCount++;
          if (callCount === 1) {
            // First call (two-way) returns 401
            return Promise.resolve({
              status: 401,
              headers: {},
              data: { error: 'Unauthorized' }
            });
          } else {
            // Second call (single-way) returns 200 with token
            return Promise.resolve({
              status: 200,
              headers: { 'authorization': 'Bearer test-token' },
              data: { success: true }
            });
          }
        });

      const result = await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api',
        'GET',
        undefined,
        undefined,
        true // start with two-way auth
      );

      expect(result.status).toBe(200);
      expect(result.is_auth_pass).toBe(true);
      expect(result.info).toContain('单向认证成功');
      expect(mockSendHttpRequest).toHaveBeenCalledTimes(2);
    });

    it('should handle authentication failure', async () => {
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockResolvedValue({
          status: 401,
          headers: {},
          data: { error: 'Unauthorized' }
        });

      const result = await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api',
        'GET',
        undefined,
        undefined,
        true
      );

      expect(result.status).toBe(401);
      expect(result.is_auth_pass).toBe(false);
      expect(result.info).toContain('双向和单向认证均返回401/403');
    });

    it('should handle network errors gracefully', async () => {
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockRejectedValue(new Error('Network error'));

      const result = await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api'
      );

      expect(result.status).toBe(500);
      expect(result.is_auth_pass).toBe(false);
      expect(result.info).toContain('请求中发生错误');
    });
  });

  describe('parseTokenFromResponse', () => {
    it('should parse Bearer token correctly', () => {
      const responseHeaders = {
        'authorization': 'Bearer test-token-123'
      };

      const result = (authInitiator as any).parseTokenFromResponse(responseHeaders);

      expect(result.authValue).toBe('单向认证');
      expect(result.token).toBe('test-token-123');
    });

    it('should parse JSON token with two-way auth correctly', () => {
      const responseHeaders = {
        'authorization': JSON.stringify({
          access_token: 'test-token-456',
          resp_did_auth_header: {
            Authorization: 'DIDWba test-header'
          }
        })
      };

      const result = (authInitiator as any).parseTokenFromResponse(responseHeaders);

      expect(result.authValue).toBe('双向认证');
      expect(result.token).toBe('test-token-456');
    });

    it('should handle missing authorization header', () => {
      const responseHeaders = {};

      const result = (authInitiator as any).parseTokenFromResponse(responseHeaders);

      expect(result.authValue).toBe('没有Auth头');
      expect(result.token).toBeNull();
    });

    it('should handle invalid JSON in authorization header', () => {
      const responseHeaders = {
        'authorization': 'invalid-json-{'
      };

      const result = (authInitiator as any).parseTokenFromResponse(responseHeaders);

      expect(result.authValue).toBe('JSON解析AuthToken失败');
      expect(result.token).toBeNull();
    });
  });

  describe('verifyTimestamp', () => {
    it('should accept valid recent timestamp', () => {
      const now = Math.floor(Date.now() / 1000);
      const recentTimestamp = (now - 60).toString(); // 1 minute ago

      const result = (authInitiator as any).verifyTimestamp(recentTimestamp);

      expect(result).toBe(true);
    });

    it('should reject old timestamp', () => {
      const now = Math.floor(Date.now() / 1000);
      const oldTimestamp = (now - 400).toString(); // 6+ minutes ago

      const result = (authInitiator as any).verifyTimestamp(oldTimestamp);

      expect(result).toBe(false);
    });

    it('should reject future timestamp', () => {
      const now = Math.floor(Date.now() / 1000);
      const futureTimestamp = (now + 400).toString(); // 6+ minutes in future

      const result = (authInitiator as any).verifyTimestamp(futureTimestamp);

      expect(result).toBe(false);
    });

    it('should handle invalid timestamp format', () => {
      const invalidTimestamp = 'not-a-number';

      const result = (authInitiator as any).verifyTimestamp(invalidTimestamp);

      expect(result).toBe(false);
    });
  });

  describe('buildWbaAuthHeader', () => {
    it('should build single-way auth header when use_two_way_auth is false', async () => {
      const context = {
        caller_did: 'did:wba:caller.example.com',
        target_did: 'did:wba:target.example.com',
        request_url: 'https://test.example.com/api',
        method: 'GET',
        custom_headers: {},
        json_data: undefined,
        use_two_way_auth: false
      };

      // Mock DIDWbaAuthClient
      const mockAuthClient = {
        getAuthHeader: jest.fn().mockResolvedValue({
          'Authorization': 'DIDWba single-way-header',
          'X-DID-Caller': 'did:wba:caller.example.com'
        }),
        getAuthHeaderTwoWay: jest.fn()
      };

      // Mock the auth client creation
      jest.spyOn(authInitiator as any, 'authClients', 'get')
        .mockReturnValue(new Map([['did:wba:caller.example.com', mockAuthClient]]));

      const result = await (authInitiator as any).buildWbaAuthHeader(context);

      expect(mockAuthClient.getAuthHeader).toHaveBeenCalledWith(context.request_url);
      expect(mockAuthClient.getAuthHeaderTwoWay).not.toHaveBeenCalled();
      expect(result['Authorization']).toBe('DIDWba single-way-header');
    });

    it('should build two-way auth header when use_two_way_auth is true', async () => {
      const context = {
        caller_did: 'did:wba:caller.example.com',
        target_did: 'did:wba:target.example.com',
        request_url: 'https://test.example.com/api',
        method: 'GET',
        custom_headers: {},
        json_data: undefined,
        use_two_way_auth: true
      };

      // Mock DIDWbaAuthClient
      const mockAuthClient = {
        getAuthHeader: jest.fn(),
        getAuthHeaderTwoWay: jest.fn().mockResolvedValue({
          'Authorization': 'DIDWba two-way-header',
          'X-DID-Caller': 'did:wba:caller.example.com'
        })
      };

      // Mock the auth client creation
      jest.spyOn(authInitiator as any, 'authClients', 'get')
        .mockReturnValue(new Map([['did:wba:caller.example.com', mockAuthClient]]));

      const result = await (authInitiator as any).buildWbaAuthHeader(context);

      expect(mockAuthClient.getAuthHeaderTwoWay).toHaveBeenCalledWith(
        context.request_url,
        context.target_did
      );
      expect(mockAuthClient.getAuthHeader).not.toHaveBeenCalled();
      expect(result['Authorization']).toBe('DIDWba two-way-header');
    });

    it('should throw error when user data not found', async () => {
      mockUserDataManager.getUserData.mockReturnValue(null);

      const context = {
        caller_did: 'did:wba:nonexistent.example.com',
        target_did: 'did:wba:target.example.com',
        request_url: 'https://test.example.com/api',
        use_two_way_auth: false
      };

      await expect(
        (authInitiator as any).buildWbaAuthHeader(context)
      ).rejects.toThrow('Could not find user data for DID');
    });
  });

  describe('Global Instance Management', () => {
    it('should return same instance from getAuthInitiator', () => {
      const instance1 = getAuthInitiator();
      const instance2 = getAuthInitiator();

      expect(instance1).toBe(instance2);
      expect(instance1).toBeInstanceOf(AuthInitiator);
    });

    it('should reset global instance', () => {
      const instance1 = getAuthInitiator();
      resetAuthInitiator();
      const instance2 = getAuthInitiator();

      expect(instance1).not.toBe(instance2);
      expect(instance2).toBeInstanceOf(AuthInitiator);
    });
  });

  describe('Cache Management', () => {
    it('should clear auth client cache', () => {
      // Add some mock clients to cache
      const mockClient = { mock: 'client' };
      (authInitiator as any).authClients.set('test-did', mockClient);

      expect((authInitiator as any).authClients.size).toBe(1);

      authInitiator.clearCache();

      expect((authInitiator as any).authClients.size).toBe(0);
    });
  });

  describe('HTTP Request Handling', () => {
    it('should handle different HTTP methods', async () => {
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockResolvedValue(mockHttpResponse);

      // Test POST request
      await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api',
        'POST',
        { data: 'test' }
      );

      expect(mockSendHttpRequest).toHaveBeenCalledWith(
        'https://test.example.com/api',
        expect.objectContaining({
          method: 'POST',
          json: { data: 'test' }
        })
      );
    });

    it('should merge custom headers with auth headers', async () => {
      const mockSendHttpRequest = jest.spyOn(authInitiator as any, 'sendHttpRequest')
        .mockResolvedValue(mockHttpResponse);

      const customHeaders = {
        'X-Custom-Header': 'custom-value',
        'Content-Type': 'application/custom'
      };

      await authInitiator.sendAuthenticatedRequest(
        'did:wba:caller.example.com',
        'did:wba:target.example.com',
        'https://test.example.com/api',
        'GET',
        undefined,
        customHeaders
      );

      expect(mockSendHttpRequest).toHaveBeenCalledWith(
        'https://test.example.com/api',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Custom-Header': 'custom-value',
            'Content-Type': 'application/json' // Should be overridden by auth headers
          })
        })
      );
    });
  });
});