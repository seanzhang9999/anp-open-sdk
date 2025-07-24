/**
 * 测试数据完整性验证
 * 确保所有真实测试数据都可以正确读取和解析
 */

import { TestDataHelper, TestAssertions } from '../../src/foundation/test-utils';

describe('测试数据完整性验证', () => {
  describe('数据目录结构', () => {
    it('应该能够访问data_user根目录', () => {
      const dataUserPath = TestDataHelper.getDataUserPath();
      expect(dataUserPath).toBeTruthy();
      expect(dataUserPath).toContain('data_user');
    });

    it('应该能够访问所有测试域名目录', async () => {
      const domains = Object.keys(TestDataHelper.TEST_DOMAINS) as Array<keyof typeof TestDataHelper.TEST_DOMAINS>;
      
      for (const domain of domains) {
        const domainPath = TestDataHelper.getDomainPath(domain);
        expect(domainPath).toBeTruthy();
        
        // 检查目录是否存在
        const exists = await TestDataHelper.fileExists(domainPath);
        if (!exists) {
          console.warn(`⚠️ 域名目录不存在: ${domainPath}`);
        }
      }
    });
  });

  describe('用户数据读取测试', () => {
    it('应该能够读取普通用户的DID文档', async () => {
      const didDoc = await TestDataHelper.readDIDDocument('LOCALHOST', 'REGULAR_USER_1');
      
      expect(didDoc).toBeDefined();
      expect(didDoc.id).toMatch(/^did:wba:/);
      expect(didDoc.id).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(didDoc.verificationMethod).toHaveLength(1);
      expect(didDoc.authentication).toHaveLength(1);
      expect(didDoc.service).toHaveLength(1);
    });

    it('应该能够读取普通用户的Agent配置', async () => {
      const agentCfg = await TestDataHelper.readAgentConfig('LOCALHOST', 'REGULAR_USER_1');
      
      expect(agentCfg).toBeDefined();
      expect(agentCfg.name).toMatch(/^测试用户_\d+$/);
      expect(agentCfg.unique_id).toBe('27c0b1d11180f973');
      expect(agentCfg.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(agentCfg.type).toBe('user');
    });

    it('应该能够读取普通用户的Agent描述', async () => {
      const agentDesc = await TestDataHelper.readAgentDescription('LOCALHOST', 'REGULAR_USER_1');
      
      expect(agentDesc).toBeDefined();
      expect(agentDesc.name).toContain('DID Services for');
      expect(agentDesc['ad:interfaces']).toBeDefined();
      expect(Array.isArray(agentDesc['ad:interfaces'])).toBe(true);
    });

    it('应该能够读取托管用户的配置', async () => {
      const agentCfg = await TestDataHelper.readAgentConfig('LOCALHOST', 'HOSTED_USER_1');
      
      expect(agentCfg).toBeDefined();
      expect(agentCfg.hosted_config).toBeDefined();
      expect(agentCfg.hosted_config?.parent_did).toBe('did:wba:localhost%3A9527:wba:user:5fea49e183c6c211');
      expect(agentCfg.hosted_config?.host).toBe('open.localhost');
      expect(agentCfg.hosted_config?.port).toBe(9527);
      expect(agentCfg.name).toContain('hosted_');
    });
  });

  describe('Agent配置读取测试', () => {
    it('应该能够读取Calculator Agent的映射配置', async () => {
      const mappingCfg = await TestDataHelper.readAgentMappingConfig('LOCALHOST', 'CALCULATOR');
      
      expect(mappingCfg).toBeDefined();
      expect(mappingCfg.name).toBe('Calculator Agent');
      expect(mappingCfg.share_did).toBeDefined();
      expect(mappingCfg.share_did?.enabled).toBe(true);
      expect(mappingCfg.share_did?.shared_did).toBe('did:wba:localhost%3A9527:wba:user:28cddee0fade0258');
      expect(mappingCfg.share_did?.path_prefix).toBe('/calculator');
      expect(mappingCfg.api).toBeDefined();
      expect(Array.isArray(mappingCfg.api)).toBe(true);
      expect(mappingCfg.api.length).toBeGreaterThan(0);
    });
  });

  describe('数据完整性验证', () => {
    it('应该验证普通用户数据的完整性', async () => {
      const validation = await TestDataHelper.validateUserData('LOCALHOST', 'REGULAR_USER_1');
      
      expect(validation.valid).toBe(true);
      expect(validation.missing).toHaveLength(0);
      expect(validation.errors).toHaveLength(0);
    });

    it('应该验证托管用户数据的完整性', async () => {
      const validation = await TestDataHelper.validateUserData('LOCALHOST', 'HOSTED_USER_1');
      
      // 托管用户可能缺少某些文件，但基本结构应该正确
      if (!validation.valid) {
        console.log('托管用户验证结果:', validation);
      }
      
      // 至少应该有基本的配置文件
      expect(validation.missing.filter(f => f.includes('did_document.json')).length).toBe(0);
    });

    it('应该检测DID和配置的一致性', async () => {
      const didDoc = await TestDataHelper.readDIDDocument('LOCALHOST', 'REGULAR_USER_1');
      const agentCfg = await TestDataHelper.readAgentConfig('LOCALHOST', 'REGULAR_USER_1');
      
      expect(() => {
        TestAssertions.assertUserDataIntegrity(didDoc, agentCfg);
      }).not.toThrow();
    });
  });

  describe('密钥文件路径测试', () => {
    it('应该能够获取用户的密钥文件路径', () => {
      const keyPaths = TestDataHelper.getUserKeyPaths('LOCALHOST', 'REGULAR_USER_1');
      
      expect(keyPaths.didPrivateKey).toContain('key-1_private.pem');
      expect(keyPaths.didPublicKey).toContain('key-1_public.pem');
      expect(keyPaths.jwtPrivateKey).toContain('private_key.pem');
      expect(keyPaths.jwtPublicKey).toContain('public_key.pem');
    });

    it('应该能够检查密钥文件是否存在', async () => {
      const keyPaths = TestDataHelper.getUserKeyPaths('LOCALHOST', 'REGULAR_USER_1');
      
      const didPrivateExists = await TestDataHelper.fileExists(keyPaths.didPrivateKey);
      const didPublicExists = await TestDataHelper.fileExists(keyPaths.didPublicKey);
      const jwtPrivateExists = await TestDataHelper.fileExists(keyPaths.jwtPrivateKey);
      const jwtPublicExists = await TestDataHelper.fileExists(keyPaths.jwtPublicKey);
      
      expect(didPrivateExists).toBe(true);
      expect(didPublicExists).toBe(true);
      expect(jwtPrivateExists).toBe(true);
      expect(jwtPublicExists).toBe(true);
    });
  });

  describe('LocalUserDataOptions创建测试', () => {
    it('应该能够创建完整的LocalUserDataOptions', async () => {
      const options = await TestDataHelper.createLocalUserDataOptions('LOCALHOST', 'REGULAR_USER_1');
      
      expect(options).toBeDefined();
      expect(options.folderName).toBe('user_27c0b1d11180f973');
      expect(options.agentCfg).toBeDefined();
      expect(options.didDocument).toBeDefined();
      expect(options.didDocPath).toContain('did_document.json');
      expect(options.passwordPaths).toBeDefined();
      expect(options.userFolderPath).toContain('user_27c0b1d11180f973');
      
      // 验证数据一致性
      expect(options.agentCfg.did).toBe(options.didDocument.id);
      expect(options.agentCfg.unique_id).toBe('27c0b1d11180f973');
    });
  });

  describe('托管DID特殊测试', () => {
    it('应该能够识别托管DID格式', async () => {
      const didDoc = await TestDataHelper.readDIDDocument('LOCALHOST', 'HOSTED_USER_1');
      
      expect(() => {
        TestAssertions.assertHostedDID(didDoc.id, 'open.localhost');
      }).not.toThrow();
      
      expect(didDoc.id).toContain('hostuser');
      expect(didDoc.id).toContain('open.localhost');
    });
  });

  describe('动态用户发现测试', () => {
    it('应该能够发现localhost域名下的所有用户', async () => {
      const users = await TestDataHelper.getAvailableUsers('LOCALHOST');
      
      expect(Array.isArray(users)).toBe(true);
      expect(users.length).toBeGreaterThan(0);
      expect(users).toContain('user_27c0b1d11180f973');
      
      // 所有用户都应该以user_开头
      users.forEach(user => {
        expect(user).toMatch(/^user_/);
      });
    });

    it('应该能够发现localhost域名下的所有Agent配置', async () => {
      const agents = await TestDataHelper.getAvailableAgents('LOCALHOST');
      
      expect(Array.isArray(agents)).toBe(true);
      expect(agents.length).toBeGreaterThan(0);
      expect(agents).toContain('agent_caculator');
      
      console.log('发现的Agent配置:', agents);
    });
  });
});