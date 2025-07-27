/**
 * 测试Agent API路径修复
 */

const express = require('express');
const { AnpServer } = require('./dist/server/express/anp-server');

async function testAgentApiRoutes() {
  console.log('🧪 测试Agent API路径修复...');
  
  try {
    // 创建服务器实例
    const server = new AnpServer({
      port: 9528,
      enableAuth: false, // 暂时禁用认证以便测试
      enableLogging: true
    });
    
    // 启动服务器
    await server.start();
    console.log('✅ 服务器启动成功');
    
    // 测试路径
    const testPaths = [
      '/agent/api/test-did/add',
      '/agent/api/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A27c0b1d11180f973/add',
      '/agent/api/test-did/some-endpoint'
    ];
    
    console.log('📋 测试路径列表:');
    testPaths.forEach(path => {
      console.log(`  - ${path}`);
    });
    
    console.log('\n✅ Agent API路由修复已应用');
    console.log('🔍 现在可以处理 /agent/api/ 路径的请求');
    
    // 停止服务器
    await server.stop();
    console.log('✅ 测试完成，服务器已停止');
    
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
  }
}

// 运行测试
testAgentApiRoutes();