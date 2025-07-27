#!/usr/bin/env ts-node

/**
 * 测试完整的认证流程
 */

import { AnpServer } from './src/server/express/anp-server';
import { loadGlobalConfig } from './src/foundation/config';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('TestAuthFlow');

async function testAuthFlow() {
  try {
    logger.info('🧪 开始测试完整认证流程...');
    
    // 1. 加载配置
    await loadGlobalConfig();
    logger.info('✅ 配置加载成功');
    
    // 2. 创建服务器实例
    const server = new AnpServer({
      host: 'localhost',
      port: 9527,
      enableAuth: true,  // 启用认证
      enableCors: true,
      enableLogging: true
    });
    
    logger.info('✅ 服务器实例创建成功');
    
    // 3. 启动服务器
    await server.start();
    logger.info('🚀 服务器启动成功: http://localhost:9527');
    
    // 4. 测试DID文档端点（应该豁免认证）
    const testUrl = 'http://localhost:9527/wba/user/e0959abab6fc3c3d/did.json';
    logger.info(`🔍 测试DID文档端点: ${testUrl}`);
    
    try {
      const response = await fetch(testUrl);
      logger.info(`📡 响应状态: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json() as any;
        logger.info('✅ DID文档获取成功（认证豁免工作正常）');
        logger.info(`DID: ${data.id}`);
      } else {
        const errorText = await response.text();
        logger.error(`❌ DID文档获取失败: ${response.status} - ${errorText}`);
      }
    } catch (fetchError) {
      logger.error('❌ 请求失败:', fetchError);
    }
    
    // 5. 测试需要认证的端点（应该返回401）
    const protectedUrl = 'http://localhost:9527/agents';
    logger.info(`🔍 测试受保护端点: ${protectedUrl}`);
    
    try {
      const response = await fetch(protectedUrl);
      logger.info(`📡 响应状态: ${response.status}`);
      
      if (response.status === 401) {
        logger.info('✅ 受保护端点正确返回401（认证中间件工作正常）');
      } else {
        logger.warn(`⚠️ 受保护端点返回状态: ${response.status}，期望401`);
      }
    } catch (fetchError) {
      logger.error('❌ 请求失败:', fetchError);
    }
    
    // 6. 停止服务器
    await server.stop();
    logger.info('🛑 服务器已停止');
    
    logger.info('🎉 认证流程测试完成！');
    
  } catch (error) {
    logger.error('❌ 测试失败:', error);
    process.exit(1);
  }
}

// 运行测试
testAuthFlow().then(() => {
  logger.info('🎉 测试完成');
  process.exit(0);
}).catch((error) => {
  logger.error('💥 测试异常:', error);
  process.exit(1);
});