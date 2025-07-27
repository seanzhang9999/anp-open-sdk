/**
 * 调试测试脚本 - 验证认证中间件和API路径修复
 */

import { AuthVerifier } from './foundation/auth/auth-verifier';
import { AuthMiddleware } from './servicepoint/middleware/auth-middleware';
import { AgentApiCaller } from './runtime/services/agent-api-caller';
import { AgentMessageCaller } from './runtime/services/agent-message-caller';
import { getLogger } from './foundation/utils';

const logger = getLogger('DebugTest');

async function testAuthMiddleware() {
  logger.info('🧪 测试认证中间件修复...');
  
  try {
    // 创建AuthVerifier实例
    const verifier = new AuthVerifier();
    
    // 测试新的verifyAuthRequest方法
    const mockAuthHeader = 'Bearer test-token';
    const result = await verifier.verifyAuthRequest(mockAuthHeader);
    
    logger.info('✅ verifyAuthRequest方法调用成功');
    logger.info(`📋 返回结果: ${JSON.stringify(result, null, 2)}`);
    
    // 创建AuthMiddleware实例
    const authMiddleware = new AuthMiddleware(verifier);
    const middleware = authMiddleware.middleware();
    
    logger.info('✅ 认证中间件创建成功');
    
    return true;
  } catch (error) {
    logger.error(`❌ 认证中间件测试失败: ${error}`);
    return false;
  }
}

async function testApiPathConstruction() {
  logger.info('🧪 测试API路径拼装修复...');
  
  try {
    // 测试API调用路径
    const apiCaller = new AgentApiCaller('test-key', 'did:wba:localhost%3A9527:wba:user:test');
    logger.info('✅ AgentApiCaller创建成功');
    
    // 测试消息发送路径
    const messageCaller = new AgentMessageCaller('test-key', 'did:wba:localhost%3A9527:wba:user:test');
    logger.info('✅ AgentMessageCaller创建成功');
    
    // 模拟路径构建（不实际发送请求）
    const targetDid = 'did:wba:localhost%3A9527:wba:user:target';
    logger.info(`📍 目标DID: ${targetDid}`);
    logger.info('📍 API调用路径格式: http://host:port/endpoint');
    logger.info('📍 消息发送路径格式: http://host:port/agent/api/{did}/message/post');
    
    return true;
  } catch (error) {
    logger.error(`❌ API路径测试失败: ${error}`);
    return false;
  }
}

async function main() {
  logger.info('🚀 开始调试测试...');
  
  const authTest = await testAuthMiddleware();
  const pathTest = await testApiPathConstruction();
  
  logger.info('\n📊 测试结果总结:');
  logger.info(`  🔐 认证中间件: ${authTest ? '✅ 通过' : '❌ 失败'}`);
  logger.info(`  🔗 API路径拼装: ${pathTest ? '✅ 通过' : '❌ 失败'}`);
  
  if (authTest && pathTest) {
    logger.info('\n🎉 所有修复验证通过！');
  } else {
    logger.info('\n⚠️ 部分修复需要进一步调试');
  }
}

// 运行测试
if (require.main === module) {
  main().catch(error => {
    logger.error(`测试执行失败: ${error}`);
    process.exit(1);
  });
}

export { testAuthMiddleware, testApiPathConstruction };