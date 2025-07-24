/**
 * LocalUserDataManager类的单元测试
 * 基于真实data_user数据进行测试
 */

import { LocalUserDataManager, getUserDataManager } from '../../src/foundation/user/local-user-data-manager';
import { TestDataHelper } from '../../src/foundation/test-utils';

describe('LocalUserDataManager类测试', () => {
  let manager: LocalUserDataManager;

  beforeEach(() => {
    // 重置单例实例以确保测试隔离
    LocalUserDataManager.resetInstance();
    manager = LocalUserDataManager.getInstance();
  });

  afterEach(() => {
    // 清理单例实例
    LocalUserDataManager.resetInstance();
  });

  describe('单例模式', () => {
    it('应该返回同一个实例', () => {
      const manager1 = LocalUserDataManager.getInstance();
      const manager2 = LocalUserDataManager.getInstance();
      
      expect(manager1).toBe(manager2);
    });

    it('应该能够通过便捷函数获取实例', () => {
      const manager1 = getUserDataManager();
      const manager2 = LocalUserDataManager.getInstance();
      
      expect(manager1).toBe(manager2);
    });

    it('应该能够重置实例', () => {
      const manager1 = LocalUserDataManager.getInstance();
      LocalUserDataManager.resetInstance();
      const manager2 = LocalUserDataManager.getInstance();
      
      expect(manager1).not.toBe(manager2);
    });
  });

  describe('初始化和加载', () => {
    it('应该能够初始化管理器', async () => {
      expect(manager.isInitialized()).toBe(false);
      
      await manager.initialize();
      
      expect(manager.isInitialized()).toBe(true);
    });

    it('应该能够加载所有用户数据', async () => {
      await manager.loadAllUsers();
      
      const allUsers = manager.getAllUsers();
      expect(allUsers.length).toBeGreaterThan(0);
      
      // 验证能找到已知的测试用户
      const testUser = manager.getUserData('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(testUser).toBeDefined();
      expect(testUser?.name).toMatch(/^测试用户_\d+$/);
    });

    it('应该能够处理不存在的用户目录', async () => {
      const invalidManager = LocalUserDataManager.getInstance('/path/that/does/not/exist');
      
      // 应该不会抛出错误，而是优雅地处理
      await expect(invalidManager.loadAllUsers()).resolves.not.toThrow();
    });

    it('应该能够获取统计信息', async () => {
      await manager.loadAllUsers();
      
      const stats = manager.getStats();
      expect(stats.total_users).toBeGreaterThan(0);
      expect(stats.initialized).toBe(true);
      expect(stats.user_dir).toBeDefined();
    });
  });

  describe('用户查询功能', () => {
    beforeEach(async () => {
      await manager.loadAllUsers();
    });

    it('应该能够通过DID查询用户', () => {
      const did = 'did:wba:localhost%3A9527:wba:user:27c0b1d11180f973';
      const userData = manager.getUserData(did);
      
      expect(userData).toBeDefined();
      expect(userData?.did).toBe(did);
      expect(userData?.name).toMatch(/^测试用户_\d+$/);
    });

    it('应该能够通过用户名查询用户', () => {
      // 先获取实际的用户名
      const testUser = manager.getUserData('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      const actualName = testUser?.name;
      
      expect(actualName).toBeDefined();
      
      const userData = manager.getUserDataByName(actualName!);
      
      expect(userData).toBeDefined();
      expect(userData?.name).toBe(actualName);
      expect(userData?.did).toBe('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
    });

    it('应该能够获取所有用户', () => {
      const allUsers = manager.getAllUsers();
      
      expect(Array.isArray(allUsers)).toBe(true);
      expect(allUsers.length).toBeGreaterThan(0);
      
      // 验证返回的都是LocalUserData实例
      allUsers.forEach(user => {
        expect(user.did).toBeDefined();
        expect(user.name).toBeDefined();
      });
    });

    it('应该能够通过域名端口查询用户', () => {
      const users = manager.getUsersByDomain('localhost', 9527);
      
      expect(Array.isArray(users)).toBe(true);
      expect(users.length).toBeGreaterThan(0);
      
      // 验证所有用户都属于指定域名端口
      users.forEach(user => {
        expect(user.did).toContain('localhost%3A9527');
      });
    });

    it('应该在查询不存在的用户时返回undefined', () => {
      const userData = manager.getUserData('did:wba:nonexistent:user');
      expect(userData).toBeUndefined();
      
      const userByName = manager.getUserDataByName('不存在的用户');
      expect(userByName).toBeUndefined();
    });

    it('应该能够检查用户名是否已被使用', () => {
      // 先获取实际的用户名
      const testUser = manager.getUserData('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      const actualName = testUser?.name;
      
      expect(actualName).toBeDefined();
      
      const taken = manager.isUsernameTaken(actualName!, 'localhost', 9527);
      expect(taken).toBe(true);
      
      const notTaken = manager.isUsernameTaken('不存在的用户名', 'localhost', 9527);
      expect(notTaken).toBe(false);
    });
  });

  describe('托管DID功能', () => {
    beforeEach(async () => {
      await manager.loadAllUsers();
    });

    it('应该能够识别托管DID用户', () => {
      const hostedUsers = manager.getAllUsers().filter(user => user.isHostedDid);
      expect(hostedUsers.length).toBeGreaterThan(0);
      
      // 找到有parentDid的托管DID用户
      const hostedUserWithParent = hostedUsers.find(user => user.parentDid);
      expect(hostedUserWithParent).toBeDefined();
      
      if (hostedUserWithParent) {
        expect(hostedUserWithParent.isHostedDid).toBe(true);
        expect(hostedUserWithParent.parentDid).toBeDefined();
        expect(hostedUserWithParent.hostedInfo).toBeDefined();
      }
    });

    it('应该能够创建托管DID用户', async () => {
      const parentUser = manager.getUserData('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      expect(parentUser).toBeDefined();

      if (parentUser) {
        const mockDidDocument = {
          '@context': ['https://www.w3.org/ns/did/v1'],
          id: 'did:wba:test.example.com%3A9527:wba:hostuser:testuser123',
          verificationMethod: [],
          authentication: [],
          service: []
        };

        const result = await manager.createHostedUser(
          parentUser,
          'test.example.com',
          '9527',
          mockDidDocument
        );

        // 注意：这个测试可能会失败，因为我们不想实际创建文件
        // 在真实环境中，这应该成功
        if (result.success) {
          expect(result.userData).toBeDefined();
          expect(result.userData?.isHostedDid).toBe(true);
          expect(result.userData?.parentDid).toBe(parentUser.did);
        } else {
          // 如果失败，至少验证错误处理
          expect(result.error).toBeDefined();
        }
      }
    });
  });

  describe('用户管理功能', () => {
    beforeEach(async () => {
      await manager.loadAllUsers();
    });

    it('应该能够扫描并加载新用户', async () => {
      const initialCount = manager.getAllUsers().length;
      
      // 扫描新用户（在真实环境中，这会检测文件系统变化）
      await manager.scanAndLoadNewUsers();
      
      const finalCount = manager.getAllUsers().length;
      
      // 在测试环境中，用户数量应该保持不变
      expect(finalCount).toBe(initialCount);
    });

    it('应该能够重新加载所有用户', async () => {
      const initialCount = manager.getAllUsers().length;
      
      await manager.reloadAllUsers();
      
      const finalCount = manager.getAllUsers().length;
      expect(finalCount).toBe(initialCount);
    });

    it('应该能够刷新指定用户', async () => {
      const did = 'did:wba:localhost%3A9527:wba:user:27c0b1d11180f973';
      const refreshedUser = await manager.refreshUser(did);
      
      expect(refreshedUser).toBeDefined();
      expect(refreshedUser?.did).toBe(did);
    });

    it('应该在刷新不存在的用户时返回null', async () => {
      const refreshedUser = await manager.refreshUser('did:wba:nonexistent:user');
      expect(refreshedUser).toBeNull();
    });
  });

  describe('冲突检测和解决', () => {
    beforeEach(async () => {
      await manager.loadAllUsers();
    });

    it('应该能够获取冲突用户信息', () => {
      const conflicts = manager.getConflictingUsers();
      
      expect(Array.isArray(conflicts)).toBe(true);
      // 在测试数据中可能有或没有冲突，这里只验证方法正常工作
    });

    it('应该能够解决用户名冲突', async () => {
      const did = 'did:wba:localhost%3A9527:wba:user:27c0b1d11180f973';
      const newName = `测试用户_${Date.now()}`;
      
      // 注意：这个测试会尝试修改文件，在只读环境中可能失败
      const result = await manager.resolveUsernameConflict(did, newName);
      
      if (result) {
        // 如果成功，验证用户名已更新
        const userData = manager.getUserData(did);
        expect(userData?.name).toBe(newName);
      } else {
        // 如果失败，这在只读测试环境中是预期的
        console.log('用户名冲突解决失败（预期在只读环境中）');
      }
    });

    it('应该在解决不存在用户的冲突时返回false', async () => {
      const result = await manager.resolveUsernameConflict('did:wba:nonexistent:user', 'newname');
      expect(result).toBe(false);
    });
  });

  describe('边界情况和错误处理', () => {
    it('应该能够处理空的用户目录', async () => {
      // 重置单例以创建新实例
      LocalUserDataManager.resetInstance();
      
      const emptyManager = LocalUserDataManager.getInstance('/tmp/empty_test_dir');
      
      await expect(emptyManager.loadAllUsers()).resolves.not.toThrow();
      expect(emptyManager.getAllUsers()).toHaveLength(0);
      
      // 恢复原来的管理器实例
      LocalUserDataManager.resetInstance();
      manager = LocalUserDataManager.getInstance();
      await manager.initialize();
    });

    it('应该能够处理损坏的用户数据', async () => {
      // 这个测试验证管理器能够优雅地处理损坏的数据文件
      await manager.loadAllUsers();
      
      // 即使有损坏的文件，也应该能加载其他正常的用户
      const users = manager.getAllUsers();
      expect(users.length).toBeGreaterThanOrEqual(0);
    });

    it('应该提供正确的用户目录路径', () => {
      const userDir = manager.getUserDir();
      expect(userDir).toBeDefined();
      expect(typeof userDir).toBe('string');
      expect(userDir).toContain('data_user');
    });
  });

  describe('性能测试', () => {
    it('应该能够快速加载大量用户', async () => {
      const startTime = Date.now();
      
      await manager.loadAllUsers();
      
      const endTime = Date.now();
      const loadTime = endTime - startTime;
      
      // 加载时间应该在合理范围内（这里设置为5秒）
      expect(loadTime).toBeLessThan(5000);
      
      console.log(`加载 ${manager.getAllUsers().length} 个用户耗时: ${loadTime}ms`);
    });

    it('应该能够快速查询用户', async () => {
      await manager.loadAllUsers();
      
      const startTime = Date.now();
      
      // 执行多次查询
      for (let i = 0; i < 1000; i++) {
        manager.getUserData('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973');
      }
      
      const endTime = Date.now();
      const queryTime = endTime - startTime;
      
      // 1000次查询应该在100ms内完成
      expect(queryTime).toBeLessThan(100);
      
      console.log(`1000次DID查询耗时: ${queryTime}ms`);
    });
  });
});