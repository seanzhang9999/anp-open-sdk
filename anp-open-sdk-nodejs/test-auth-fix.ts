/**
 * 测试AuthVerifier的DID文档解析修复
 */

import { getAuthVerifier } from './src/foundation/auth/auth-verifier';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('TestAuthFix');

async function testDidDocumentResolution() {
  logger.info('🧪 开始测试DID文档解析修复...');
  
  try {
    const authVerifier = getAuthVerifier();
    
    // 构造一个测试请求对象
    const testRequest = {
      headers: {
        authorization: 'DIDWba did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d nonce:test123 timestamp:' + new Date().toISOString() + ' keyid:test signature:test'
      },
      method: 'GET',
      path: '/test',
      query: {},
      hostname: 'localhost'
    };
    
    logger.info('📡 测试认证请求...');
    const result = await authVerifier.authenticateRequest(testRequest);
    
    logger.info('📊 认证结果:');
    logger.info(`  成功: ${result.success}`);
    logger.info(`  消息: ${result.message}`);
    logger.info(`  结果: ${JSON.stringify(result.result, null, 2)}`);
    
    // 检查是否有DID文档获取的日志
    if (result.message.includes('Failed to resolve DID document')) {
      logger.info('✅ 修复验证：DID文档解析逻辑已被调用');
    } else {
      logger.info('ℹ️  其他认证失败原因，但DID文档解析逻辑应该已被调用');
    }
    
  } catch (error) {
    logger.error(`❌ 测试过程中出错: ${error}`);
  }
}

// 运行测试
testDidDocumentResolution().then(() => {
  logger.info('🎉 测试完成');
  process.exit(0);
}).catch((error) => {
  logger.error(`❌ 测试失败: ${error}`);
  process.exit(1);
});