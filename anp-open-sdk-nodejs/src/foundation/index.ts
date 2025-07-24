export * from './user';
export * from './did';
export * from './config';
export * from './utils';
export * from './domain';
export * from './contact';
export * from './test-utils';

// 显式导出认证模块以避免类型冲突
export {
  LegacyAuthInitiator,
  LegacyAuthVerifier,
  AuthManager,
  AuthInitiator,
  AuthVerifier,
  getAuthInitiator,
  resetAuthInitiator,
  getAuthVerifier,
  resetAuthVerifier
} from './auth';