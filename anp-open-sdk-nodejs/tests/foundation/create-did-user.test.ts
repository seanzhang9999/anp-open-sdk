/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { createDidUser, CreateUserInput, CreateDidUserOptions } from '../../src/foundation/user/create-did-user';
import { LocalUserDataManager } from '../../src/foundation/user/local-user-data-manager';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('DID User Creation Tools', () => {
  let tempDir: string;
  let userDataManager: LocalUserDataManager;

  beforeEach(async () => {
    // Create temporary directory for test files
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'did-user-test-'));
    
    // Initialize manager with temp directory
    userDataManager = LocalUserDataManager.getInstance(tempDir);
    await userDataManager.initialize();
  });

  afterEach(async () => {
    // Clean up temporary files
    if (tempDir) {
      await fs.rm(tempDir, { recursive: true, force: true });
    }
    
    // Reset singleton instances
    LocalUserDataManager.resetInstance();
  });

  describe('createDidUser', () => {
    it('should create a new DID user successfully', async () => {
      const userInput: CreateUserInput = {
        name: 'test-user',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();
      expect(result?.id).toContain('did:wba:');
      expect(result?.id).toContain(`${userInput.host}%3A${userInput.port}`);
      expect(result?.verificationMethod).toHaveLength(1);
      expect(result?.authentication).toHaveLength(1);
      expect(result?.service).toHaveLength(1);
    });

    it('should create user with proper directory structure', async () => {
      const userInput: CreateUserInput = {
        name: 'structure-test',
        host: 'example.com',
        port: 8080,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();

      // Check that user directory was created
      const expectedUserDir = path.join(tempDir, userInput.host, 'anp_users');
      expect(await directoryExists(expectedUserDir)).toBe(true);

      // Find the created user directory
      const userDirs = await fs.readdir(expectedUserDir);
      const userDir = userDirs.find(dir => dir.startsWith('user_'));
      expect(userDir).toBeDefined();

      const fullUserPath = path.join(expectedUserDir, userDir!);
      expect(await fileExists(path.join(fullUserPath, 'agent_cfg.yaml'))).toBe(true);
      expect(await fileExists(path.join(fullUserPath, 'did_document.json'))).toBe(true);
      expect(await fileExists(path.join(fullUserPath, 'key-1_private.pem'))).toBe(true);
      expect(await fileExists(path.join(fullUserPath, 'key-1_public.pem'))).toBe(true);
      expect(await fileExists(path.join(fullUserPath, 'private_key.pem'))).toBe(true);
      expect(await fileExists(path.join(fullUserPath, 'public_key.pem'))).toBe(true);
    });

    it('should generate unique DIDs for different users', async () => {
      const userInput1: CreateUserInput = {
        name: 'user1',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const userInput2: CreateUserInput = {
        name: 'user2',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result1 = await createDidUser(userInput1, options);
      const result2 = await createDidUser(userInput2, options);

      expect(result1).not.toBeNull();
      expect(result2).not.toBeNull();
      expect(result1?.id).not.toBe(result2?.id);
    });

    it('should handle missing required fields', async () => {
      const incompleteInput = {
        name: 'test',
        host: 'localhost'
        // Missing port, dir, type
      } as CreateUserInput;

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(incompleteInput, options);

      expect(result).toBeNull();
    });

    it('should create user with proper agent configuration', async () => {
      const userInput: CreateUserInput = {
        name: 'config-test',
        host: 'test.example.com',
        port: 3000,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();

      // Find and read the agent config file
      const userDir = await findUserDirectory(tempDir, userInput.host);
      expect(userDir).toBeDefined();

      const agentCfgPath = path.join(userDir!, 'agent_cfg.yaml');
      expect(await fileExists(agentCfgPath)).toBe(true);

      const yaml = require('yaml');
      const agentCfgContent = await fs.readFile(agentCfgPath, 'utf-8');
      const agentCfg = yaml.parse(agentCfgContent);

      expect(agentCfg.name).toBe(userInput.name);
      expect(agentCfg.type).toBe(userInput.type);
      expect(agentCfg.did).toBe(result?.id);
      expect(agentCfg.unique_id).toBeDefined();
    });

    it('should create user with valid DID document', async () => {
      const userInput: CreateUserInput = {
        name: 'did-doc-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();
      expect(result?.['@context']).toContain('https://www.w3.org/ns/did/v1');
      expect(result?.verificationMethod).toHaveLength(1);
      expect(result?.authentication).toHaveLength(1);
      expect(result?.service).toHaveLength(1);
      expect(result?.key_id).toBe('key-1');

      const verificationMethod = result?.verificationMethod[0];
      expect(verificationMethod?.id).toBe('#key-1');
      expect(verificationMethod?.type).toBe('EcdsaSecp256k1VerificationKey2019');
      expect(verificationMethod?.publicKeyJwk.kid).toBe('key-1');
    });

    it('should register user with LocalUserDataManager', async () => {
      const userInput: CreateUserInput = {
        name: 'registration-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();

      // Reload users to ensure the new user is loaded
      await userDataManager.loadAllUsers();

      // Verify user is registered in manager
      const registeredUser = userDataManager.getUserData(result!.id);
      expect(registeredUser).toBeDefined();
      expect(registeredUser?.name).toBe(userInput.name);
    });

    it('should handle username conflicts', async () => {
      const userInput1: CreateUserInput = {
        name: 'conflict-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const userInput2: CreateUserInput = {
        name: 'conflict-test', // Same name
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const result1 = await createDidUser(userInput1, options);
      const result2 = await createDidUser(userInput2, options);

      expect(result1).not.toBeNull();
      expect(result2).not.toBeNull();

      // The second user should have a modified name
      const userDirs = await findAllUserDirectories(tempDir, userInput1.host);
      expect(userDirs.length).toBe(2);

      const agentCfg1 = await readAgentConfig(userDirs[0]);
      const agentCfg2 = await readAgentConfig(userDirs[1]);

      // 确保我们有两个不同的配置
      const configs = [agentCfg1, agentCfg2];
      const originalConfig = configs.find(cfg => cfg.name === 'conflict-test');
      const modifiedConfig = configs.find(cfg => cfg.name !== 'conflict-test');

      expect(originalConfig).toBeDefined();
      expect(modifiedConfig).toBeDefined();
      expect(modifiedConfig.name).toContain('conflict-test');
    });

    it('should create user with hex-based unique ID by default', async () => {
      const userInput: CreateUserInput = {
        name: 'hex-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir,
        didHex: true
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();

      // Check that the DID contains a hex ID
      const didParts = result!.id.split(':');
      const lastPart = didParts[didParts.length - 1];
      expect(lastPart).toMatch(/^[a-f0-9]+$/); // Should be hex
      expect(lastPart.length).toBe(16); // 8 bytes = 16 hex chars
    });

    it('should create user without hex ID when disabled', async () => {
      const userInput: CreateUserInput = {
        name: 'no-hex-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      const options: CreateDidUserOptions = {
        userDidPath: tempDir,
        didHex: false
      };

      const result = await createDidUser(userInput, options);

      expect(result).not.toBeNull();

      // Check that the DID doesn't contain a hex ID
      const expectedDid = `did:wba:${userInput.host}%3A${userInput.port}:${encodeURIComponent(userInput.dir)}:${encodeURIComponent(userInput.type)}:${encodeURIComponent(userInput.name)}`;
      expect(result!.id).toBe(expectedDid);
    });
  });

  describe('Integration Tests', () => {
    it('should create multiple users without conflicts', async () => {
      const users: CreateUserInput[] = [
        { name: 'user1', host: 'localhost', port: 9527, dir: 'wba', type: 'user' },
        { name: 'user2', host: 'localhost', port: 9528, dir: 'wba', type: 'user' },
        { name: 'user3', host: 'example.com', port: 8080, dir: 'wba', type: 'user' }
      ];

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      const results = await Promise.all(
        users.map(user => createDidUser(user, options))
      );

      // All should succeed
      results.forEach(result => {
        expect(result).not.toBeNull();
      });

      // All should have unique DIDs
      const dids = results.map(r => r!.id);
      const uniqueDids = new Set(dids);
      expect(uniqueDids.size).toBe(dids.length);
    });

    it('should handle concurrent user creation', async () => {
      const concurrentOperations = Array.from({ length: 5 }, (_, i) => {
        const userInput: CreateUserInput = {
          name: `concurrent-user-${i}`,
          host: 'localhost',
          port: 9527 + i,
          dir: 'wba',
          type: 'user'
        };

        const options: CreateDidUserOptions = {
          userDidPath: tempDir,
          didHex: false  // 禁用hex格式，使DID包含用户名
        };

        return createDidUser(userInput, options);
      });

      const results = await Promise.all(concurrentOperations);

      // All should succeed
      results.forEach((result, index) => {
        expect(result).not.toBeNull();
        expect(result?.id).toContain(`concurrent-user-${index}`);
      });

      // Reload users and verify all are registered
      await userDataManager.loadAllUsers();
      const allUsers = userDataManager.getAllUsers();
      expect(allUsers.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Error Handling', () => {
    it('should handle file system errors gracefully', async () => {
      const userInput: CreateUserInput = {
        name: 'fs-error-test',
        host: 'localhost',
        port: 9527,
        dir: 'wba',
        type: 'user'
      };

      // Try to create user in non-existent directory
      const options: CreateDidUserOptions = {
        userDidPath: '/non/existent/path'
      };

      const result = await createDidUser(userInput, options);

      // Should handle the error gracefully
      expect(result).toBeNull();
    });

    it('should validate required fields', async () => {
      const invalidInputs = [
        { host: 'localhost', port: 9527, dir: 'wba', type: 'user' }, // Missing name
        { name: 'test', port: 9527, dir: 'wba', type: 'user' }, // Missing host
        { name: 'test', host: 'localhost', dir: 'wba', type: 'user' }, // Missing port
        { name: 'test', host: 'localhost', port: 9527, type: 'user' }, // Missing dir
        { name: 'test', host: 'localhost', port: 9527, dir: 'wba' } // Missing type
      ];

      const options: CreateDidUserOptions = {
        userDidPath: tempDir
      };

      for (const input of invalidInputs) {
        const result = await createDidUser(input as unknown as CreateUserInput, options);
        expect(result).toBeNull();
      }
    });
  });
});

// Helper functions
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function directoryExists(dirPath: string): Promise<boolean> {
  try {
    const stat = await fs.stat(dirPath);
    return stat.isDirectory();
  } catch {
    return false;
  }
}

async function findUserDirectory(basePath: string, host: string): Promise<string | null> {
  try {
    const hostPath = path.join(basePath, host, 'anp_users');
    const entries = await fs.readdir(hostPath);
    const userDir = entries.find(entry => entry.startsWith('user_'));
    return userDir ? path.join(hostPath, userDir) : null;
  } catch {
    return null;
  }
}

async function findAllUserDirectories(basePath: string, host: string): Promise<string[]> {
  try {
    const hostPath = path.join(basePath, host, 'anp_users');
    const entries = await fs.readdir(hostPath);
    const userDirs = entries.filter(entry => entry.startsWith('user_'));
    return userDirs.map(dir => path.join(hostPath, dir));
  } catch {
    return [];
  }
}

async function readAgentConfig(userDir: string): Promise<any> {
  const yaml = require('yaml');
  const agentCfgPath = path.join(userDir, 'agent_cfg.yaml');
  const content = await fs.readFile(agentCfgPath, 'utf-8');
  return yaml.parse(content);
}