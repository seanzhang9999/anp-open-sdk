/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

/**
 * Servicepoint模块 - ANP服务端点处理
 * 
 * 提供完整的服务端点处理功能，包括：
 * - DID服务处理 (DID文档、Agent描述)
 * - 发布者服务 (智能体列表、统计)
 * - 认证服务 (token验证、权限检查)
 * - 主机服务 (托管DID管理)
 * - 认证豁免处理 (无需认证的路径)
 * 
 * 对应Python版本的anp_servicepoint模块
 */

// 导出所有处理器
export * from './handlers';

// 注意：ServicePointManager和ServicePointRouter需要在实际项目中使用时导入
// 目前由于模块解析问题，暂时注释掉这些导出
// export { ServicePointManager } from './service-point-manager';
// export { ServicePointRouter } from './service-point-router';