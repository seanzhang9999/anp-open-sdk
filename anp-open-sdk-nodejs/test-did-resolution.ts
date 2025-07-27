/**
 * 直接测试DID文档解析功能
 */

import { getAuthVerifier } from './src/foundation/auth/auth-verifier';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('TestDidResolution');

async function testDidDocumentResolutionDirectly() {
  logger.info('🧪 直接测试DID文档解析功能...');
  
  try {
    const authVerifier = getAuthVerifier();
    
    // 使用反射访问私有方法进行测试
    const resolveMethod = (authVerifier as any).resolveDidDocumentInsecurely;
    
    if (!resolveMethod) {
      logger.error('❌ 无法访问resolveDidDocumentInsecurely方法');
      return;
    }
    
    // 测试DID解析
    const testDid = 'did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d';
    logger.info(`📡 测试DID解析: ${testDid}`);
    
    const result = await resolveMethod.call(authVerifier, testDid);
    
    logger.info('📊 DID解析结果:');
    if (result) {
      logger.info(`✅ 成功获取DID文档: ${JSON.stringify(result, null, 2)}`);
    } else {
      logger.info('❌ DID文档解析返回null');
    }
    
    // 测试URL构造
    logger.info('\n🔍 验证URL构造逻辑:');
    const parts = testDid.split(':');
    let hostname = parts[2];
    if (hostname.includes('%3A')) {
      hostname = decodeURIComponent(hostname);
    }
    const pathSegments = parts.slice(3);
    const userId = pathSegments[pathSegments.length - 1];
    const userDir = pathSegments[pathSegments.length - 2];
    const expectedUrl = `http://${hostname}/wba/${userDir}/${userId}/did.json`;
    
    logger.info(`🌐 预期URL: ${expectedUrl}`);
    
    // 手动测试HTTP请求
    logger.info('\n🌐 手动测试HTTP请求:');
    try {
      const response = await fetch(expectedUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        signal: AbortSignal.timeout(5000)
      });
      
      logger.info(`📡 HTTP响应状态: ${response.status} ${response.statusText}`);
      
      if (response.status === 200) {
        const data = await response.json();
        logger.info(`✅ 成功获取DID文档: ${JSON.stringify(data, null, 2)}`);
      } else {
        const text = await response.text();
        logger.info(`❌ HTTP请求失败，响应内容: ${text}`);
      }
    } catch (fetchError: any) {
      logger.info(`❌ HTTP请求异常: ${fetchError.message}`);
      if (fetchError.name === 'TimeoutError') {
        logger.info('⏰ 请求超时');
      } else if (fetchError.code === 'ECONNREFUSED') {
        logger.info('🔌 连接被拒绝 - 服务器可能未运行');
      } else if (fetchError.code === 'ENOTFOUND') {
        logger.info('🌐 域名解析失败');
      }
    }
    
  } catch (error) {
    logger.error(`❌ 测试过程中出错: ${error}`);
  }
}

// 运行测试
testDidDocumentResolutionDirectly().then(() => {
  logger.info('🎉 测试完成');
  process.exit(0);
}).catch((error) => {
  logger.error(`❌ 测试失败: ${error}`);
  process.exit(1);
});