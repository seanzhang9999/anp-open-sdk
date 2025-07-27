#!/usr/bin/env ts-node

/**
 * 测试DID路由是否正确工作
 */

import { AnpServer } from './src/server/express/anp-server';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('TestDIDRoute');

async function testDIDRoute() {
  try {
    logger.info('🧪 开始测试DID路由...');
    
    // 创建服务器实例，使用正确的端口9527
    const server = new AnpServer({
      host: 'localhost',
      port: 9527,  // 使用正确的端口
      enableAuth: false,  // 暂时禁用认证来测试路由
      enableCors: true,
      enableLogging: true
    });
    
    logger.info('✅ 服务器实例创建成功');
    
    // 启动服务器
    await server.start();
    logger.info('🚀 服务器启动成功: http://localhost:9527');
    
    // 测试DID文档端点
    const testUrl = 'http://localhost:9527/wba/user/e0959abab6fc3c3d/did.json';
    logger.info(`🔍 测试DID文档端点: ${testUrl}`);
    
    try {
      const response = await fetch(testUrl);
      logger.info(`📡 响应状态: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        logger.info('✅ DID文档获取成功:');
        logger.info(JSON.stringify(data, null, 2));
      } else {
        const errorText = await response.text();
        logger.warn(`❌ DID文档获取失败: ${response.status} - ${errorText}`);
      }
    } catch (fetchError) {
      logger.error('❌ 请求失败:', fetchError);
    }
    
    // 停止服务器
    await server.stop();
    logger.info('🛑 服务器已停止');
    
  } catch (error) {
    logger.error('❌ 测试失败:', error);
    process.exit(1);
  }
}

// 运行测试
testDIDRoute().then(() => {
  logger.info('🎉 测试完成');
  process.exit(0);
}).catch((error) => {
  logger.error('💥 测试异常:', error);
  process.exit(1);
});