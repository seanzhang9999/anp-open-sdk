export * from './types';

// 从manager导出
export { ConfigManager, loadGlobalConfig } from './manager';

// 从unified-config导出，重命名以避免冲突
export {
  UnifiedConfig,
  setGlobalConfig,
  getGlobalConfig as getUnifiedGlobalConfig
} from './unified-config';

// 保持向后兼容，默认使用manager的getGlobalConfig
export { getGlobalConfig } from './manager';