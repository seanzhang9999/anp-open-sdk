#!/usr/bin/env ts-node

/**
 * 测试认证配置加载
 */

import { loadGlobalConfig, getGlobalConfig } from './src/foundation/config';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('TestAuthConfig');

async function testAuthConfig() {
  try {
    logger.info('🧪 测试认证配置加载...');
    
    // 加载配置
    await loadGlobalConfig();
    logger.info('✅ 配置加载成功');
    
    // 获取配置
    const config = getGlobalConfig();
    logger.info('✅ 配置获取成功');
    
    // 检查认证中间件配置
    if (config.authMiddleware) {
      logger.info('✅ authMiddleware配置存在');
      logger.info(`豁免路径: ${JSON.stringify(config.authMiddleware.exemptPaths, null, 2)}`);
      
      // 检查是否包含我们需要的路径
      const exemptPaths = config.authMiddleware.exemptPaths;
      const hasWbaUser = exemptPaths.some(path => path.includes('/wba/user'));
      const hasWbaUserDidJson = exemptPaths.some(path => path.includes('/wba/user/*/did.json'));
      
      logger.info(`包含 /wba/user 路径: ${hasWbaUser}`);
      logger.info(`包含 /wba/user/*/did.json 路径: ${hasWbaUserDidJson}`);
      
      if (hasWbaUser && hasWbaUserDidJson) {
        logger.info('🎉 认证豁免配置正确！');
      } else {
        logger.error('❌ 认证豁免配置不完整');
      }
    } else {
      logger.error('❌ authMiddleware配置不存在');
    }
    
  } catch (error) {
    logger.error('❌ 测试失败:', error);
  }
}

// 运行测试
testAuthConfig().then(() => {
  logger.info('🎉 测试完成');
  process.exit(0);
}).catch((error) => {
  logger.error('💥 测试异常:', error);
  process.exit(1);
});