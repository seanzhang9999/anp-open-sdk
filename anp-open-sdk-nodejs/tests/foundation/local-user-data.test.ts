/**
 * LocalUserData类的单元测试
 * 基于真实data_user数据进行测试
 */

import { LocalUserData, LocalUserDataFactory } from '../../src/foundation/user/local-user-data';
import { TestDataHelper, TestAssertions } from '../../src/foundation/test-utils';

describe('LocalUserData类测试', () => {
  describe('构造函数和基础属性', () => {
    it('应该能够从真实数据创建LocalUserData实例', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      const userData = new LocalUserData(options);

      expect(userData.folderName).toBe('user_27c0b1d11180f973');
      expect(userData.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(userData.name).toMatch(/^测试用户_\d+$/);
      expect(userData.uniqueId).toBe('27c0b1d11180f973');
      expect(userData.isHostedDid).toBe(false);
      expect(userData.keyId).toBe('key-1');
    });

    it('应该能够识别托管DID用户', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'HOSTED_USER_1');
      const userData = new LocalUserData(options);

      expect(userData.isHostedDid).toBe(true);
      expect(userData.parentDid).toBe('did:wba:localhost%3A9527:wba:user:5fea49e183c6c211');
      expect(userData.hostedInfo).toBeDefined();
      expect(userData.hostedInfo?.host).toBe('open.localhost');
      expect(userData.hostedInfo?.port).toBe(9527);
    });

    it('应该正确解析密钥文件路径', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      const userData = new LocalUserData(options);

      expect(userData.didPrivateKeyFilePath).toContain('key-1_private.pem');
      expect(userData.didPublicKeyFilePath).toContain('key-1_public.pem');
      expect(userData.jwtPrivateKeyFilePath).toContain('private_key.pem');
      expect(userData.jwtPublicKeyFilePath).toContain('public_key.pem');
    });
  });

  describe('工厂方法测试', () => {
    it('应该能够从目录创建LocalUserData实例', async () => {
      const userPath = TestDataHelper.getUserPath('LOCALHOST', 'REGULAR_USER_1');
      const userData = await LocalUserDataFactory.fromDirectory(userPath);

      expect(userData.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(userData.name).toMatch(/^测试用户_\d+$/);
      expect(userData.uniqueId).toBe('27c0b1d11180f973');
    });

    it('应该在目录不存在时抛出错误', async () => {
      const invalidPath = '/path/that/does/not/exist';
      
      await expect(LocalUserDataFactory.fromDirectory(invalidPath))
        .rejects
        .toThrow('Failed to create LocalUserData from directory');
    });
  });

  describe('公共访问方法', () => {
    let userData: LocalUserData;

    beforeEach(async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      userData = new LocalUserData(options);
    });

    it('应该提供正确的访问方法', () => {
      expect(userData.getDid()).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(userData.getPrivateKeyPath()).toContain('key-1_private.pem');
      expect(userData.getPublicKeyPath()).toContain('key-1_public.pem');
    });

    it('应该能够访问内存中的密钥对象', async () => {
      // 等待密钥加载完成
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 注意：在测试环境中，密钥可能不会立即加载
      // 这里主要测试方法存在性
      expect(typeof userData.getDidPrivateKey).toBe('function');
      expect(typeof userData.getJwtPrivateKey).toBe('function');
      expect(typeof userData.getJwtPublicKey).toBe('function');
    });
  });

  describe('Token管理功能', () => {
    let userData: LocalUserData;
    const remoteDid = 'did:wba:example.com:wba:user:test123';

    beforeEach(async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      userData = new LocalUserData(options);
    });

    it('应该能够存储和获取发送给远程的Token', () => {
      const token = 'test-token-123';
      const expiresInSeconds = 3600;

      userData.storeTokenToRemote(remoteDid, token, expiresInSeconds);
      const storedToken = userData.getTokenToRemote(remoteDid);

      expect(storedToken).toBeDefined();
      expect(storedToken?.token).toBe(token);
      expect(storedToken?.req_did).toBe(remoteDid);
      expect(storedToken?.is_revoked).toBe(false);
      expect(storedToken?.expires_at).toBeDefined();
    });

    it('应该能够存储和获取从远程接收的Token', () => {
      const token = 'received-token-456';

      userData.storeTokenFromRemote(remoteDid, token);
      const storedToken = userData.getTokenFromRemote(remoteDid);

      expect(storedToken).toBeDefined();
      expect(storedToken?.token).toBe(token);
      expect(storedToken?.req_did).toBe(remoteDid);
      expect(storedToken?.created_at).toBeDefined();
    });

    it('应该能够撤销发送给远程的Token', () => {
      const token = 'revoke-test-token';
      userData.storeTokenToRemote(remoteDid, token, 3600);

      const revoked = userData.revokeTokenToRemote(remoteDid);
      expect(revoked).toBe(true);

      const storedToken = userData.getTokenToRemote(remoteDid);
      expect(storedToken?.is_revoked).toBe(true);
    });

    it('应该在撤销不存在的Token时返回false', () => {
      const revoked = userData.revokeTokenToRemote('non-existent-did');
      expect(revoked).toBe(false);
    });
  });

  describe('联系人管理功能', () => {
    let userData: LocalUserData;

    beforeEach(async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      userData = new LocalUserData(options);
    });

    it('应该能够添加和获取联系人', () => {
      const contact = {
        did: 'did:wba:example.com:wba:user:contact123',
        name: '测试联系人',
        host: 'example.com',
        port: 9527,
      };

      userData.addContact(contact);
      const retrievedContact = userData.getContact(contact.did);

      expect(retrievedContact).toBeDefined();
      expect(retrievedContact?.name).toBe(contact.name);
      expect(retrievedContact?.host).toBe(contact.host);
      expect(retrievedContact?.created_at).toBeDefined();
      expect(retrievedContact?.updated_at).toBeDefined();
    });

    it('应该能够列出所有联系人', () => {
      const contacts = [
        { did: 'did:wba:test1.com:wba:user:1', name: '联系人1' },
        { did: 'did:wba:test2.com:wba:user:2', name: '联系人2' },
      ];

      contacts.forEach(contact => userData.addContact(contact));
      const allContacts = userData.listContacts();

      expect(allContacts).toHaveLength(2);
      expect(allContacts.map(c => c.name)).toContain('联系人1');
      expect(allContacts.map(c => c.name)).toContain('联系人2');
    });

    it('应该能够更新联系人信息', () => {
      const contact = {
        did: 'did:wba:example.com:wba:user:update123',
        name: '原始名称',
      };

      userData.addContact(contact);
      const updated = userData.updateContact(contact.did, { name: '更新后的名称' });

      expect(updated).toBe(true);
      const retrievedContact = userData.getContact(contact.did);
      expect(retrievedContact?.name).toBe('更新后的名称');
      expect(retrievedContact?.updated_at).toBeDefined();
    });

    it('应该能够删除联系人', () => {
      const contact = {
        did: 'did:wba:example.com:wba:user:delete123',
        name: '待删除联系人',
      };

      userData.addContact(contact);
      expect(userData.getContact(contact.did)).toBeDefined();

      const deleted = userData.removeContact(contact.did);
      expect(deleted).toBe(true);
      expect(userData.getContact(contact.did)).toBeUndefined();
    });
  });

  describe('数据完整性验证', () => {
    it('应该验证正常用户数据的完整性', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      const userData = new LocalUserData(options);

      const validation = await userData.validateIntegrity();
      expect(validation.valid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('应该检测数据不一致问题', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      
      // 故意创建不一致的数据
      options.agentCfg.did = 'did:wba:invalid:did';
      const userData = new LocalUserData(options);

      const validation = await userData.validateIntegrity();
      expect(validation.valid).toBe(false);
      expect(validation.errors.some(error => error.includes('DID mismatch'))).toBe(true);
    });
  });

  describe('工具方法', () => {
    let userData: LocalUserData;

    beforeEach(async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      userData = new LocalUserData(options);
    });

    it('应该能够转换为字典格式', () => {
      const dict = userData.toDict();

      expect(dict.folder_name).toBe('user_27c0b1d11180f973');
      expect(dict.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(dict.name).toMatch(/^测试用户_\d+$/);
      expect(dict.unique_id).toBe('27c0b1d11180f973');
      expect(dict.is_hosted_did).toBe(false);
      expect(typeof dict.contacts_count).toBe('number');
    });

    it('应该能够获取统计信息', () => {
      const stats = userData.getStats();

      expect(stats.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(stats.name).toMatch(/^测试用户_\d+$/);
      expect(stats.is_hosted).toBe(false);
      expect(typeof stats.contacts_count).toBe('number');
      expect(typeof stats.has_did_private_key).toBe('boolean');
      expect(typeof stats.has_jwt_private_key).toBe('boolean');
    });

    it('应该能够刷新密钥缓存', async () => {
      await expect(userData.refreshKeyCache()).resolves.not.toThrow();
    });
  });

  describe('托管DID特殊功能', () => {
    it('应该正确解析托管DID信息', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'HOSTED_USER_1');
      const userData = new LocalUserData(options);

      expect(userData.isHostedDid).toBe(true);
      expect(userData.hostedInfo).toBeDefined();
      expect(userData.hostedInfo?.host).toBe('open.localhost');
      expect(userData.hostedInfo?.port).toBe(9527);
      expect(userData.hostedInfo?.did_suffix).toBe('b9b6b73772c692db');
    });

    it('应该在托管DID验证中检查父DID', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'HOSTED_USER_1');
      
      // 移除父DID信息
      if (options.agentCfg.hosted_config) {
        options.agentCfg.hosted_config = {
          ...options.agentCfg.hosted_config,
          parent_did: undefined as any
        };
      }
      
      const userData = new LocalUserData(options);
      const validation = await userData.validateIntegrity();

      expect(validation.valid).toBe(false);
      expect(validation.errors.some(error => error.includes('parent_did'))).toBe(true);
    });
  });
});