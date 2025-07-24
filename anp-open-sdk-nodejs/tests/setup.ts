/**
 * Jest测试设置文件
 * 在所有测试运行前执行
 */

import * as path from 'path';
import { TestDataHelper } from '../src/foundation/test-utils';

// 设置测试超时
jest.setTimeout(30000);

// 全局测试配置
global.TEST_CONFIG = {
  DATA_USER_PATH: path.resolve(process.cwd(), 'data_user'),
  TIMEOUT: 30000,
  LOG_LEVEL: 'error', // 测试时减少日志输出
};

// 在所有测试开始前验证测试数据
beforeAll(async () => {
  console.log('🔍 验证测试数据完整性...');
  
  // 检查data_user目录是否存在
  const dataUserPath = TestDataHelper.getDataUserPath();
  try {
    const fs = require('fs/promises');
    await fs.access(dataUserPath);
    console.log('✅ data_user目录存在');
  } catch (error) {
    console.error('❌ data_user目录不存在，请确保项目根目录包含测试数据');
    throw new Error(`Test data directory not found: ${dataUserPath}`);
  }

  // 验证关键测试用户数据
  const criticalUsers = [
    { domain: 'LOCALHOST' as const, user: 'REGULAR_USER_1' as const },
    { domain: 'LOCALHOST' as const, user: 'HOSTED_USER_1' as const },
  ];

  for (const { domain, user } of criticalUsers) {
    try {
      const validation = await TestDataHelper.validateUserData(domain, user);
      if (!validation.valid) {
        console.warn(`⚠️ 用户数据不完整 ${domain}/${user}:`, validation.missing);
      } else {
        console.log(`✅ 用户数据验证通过: ${domain}/${user}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.warn(`⚠️ 无法验证用户数据 ${domain}/${user}:`, errorMessage);
    }
  }

  console.log('🚀 测试环境准备完成');
});

// 在每个测试文件后清理
afterEach(() => {
  // 清理可能的定时器
  jest.clearAllTimers();
  
  // 清理模块缓存（如果需要）
  // jest.resetModules();
});

// 全局错误处理
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// 扩展Jest匹配器
expect.extend({
  toBeValidDID(received: string) {
    const pass = typeof received === 'string' && received.startsWith('did:wba:');
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid DID`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid DID (should start with 'did:wba:')`,
        pass: false,
      };
    }
  },

  toHaveRequiredUserFiles(received: string[]) {
    const requiredFiles = ['did_document.json', 'agent_cfg.yaml'];
    const missing = requiredFiles.filter(file => !received.includes(file));
    
    if (missing.length === 0) {
      return {
        message: () => `expected user directory not to have all required files`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected user directory to have required files, missing: ${missing.join(', ')}`,
        pass: false,
      };
    }
  },
});

// 类型声明扩展
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidDID(): R;
      toHaveRequiredUserFiles(): R;
    }
  }
  
  var TEST_CONFIG: {
    DATA_USER_PATH: string;
    TIMEOUT: number;
    LOG_LEVEL: string;
  };
}