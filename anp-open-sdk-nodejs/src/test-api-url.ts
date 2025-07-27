/**
 * 测试AgentApiCaller的URL构建是否正确
 */

import { AgentApiCaller } from './runtime/services/agent-api-caller';
import { getLogger } from './foundation/utils';

const logger = getLogger('TestApiUrl');

async function testUrlConstruction() {
  logger.info('🧪 测试AgentApiCaller URL构建...');
  
  try {
    const callerDid = 'did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d';
    const targetDid = 'did:wba:localhost%3A9527:wba:user:27c0b1d11180f973';
    
    const apiCaller = new AgentApiCaller('test-key', callerDid);
    
    // 模拟调用，但不实际发送请求（通过捕获错误来查看URL构建）
    try {
      await apiCaller.callAgentApi(targetDid, '/add', { a: 5, b: 3 });
    } catch (error) {
      // 预期会有错误，因为没有实际的服务器，但我们可以从日志中看到URL构建
      logger.info('预期的网络错误（用于查看URL构建）:', error.message);
    }
    
    logger.info('✅ URL构建测试完成，请查看上面的调试日志');
    
  } catch (error) {
    logger.error('❌ URL构建测试失败:', error);
  }
}

// 运行测试
if (require.main === module) {
  testUrlConstruction().catch(console.error);
}

export { testUrlConstruction };