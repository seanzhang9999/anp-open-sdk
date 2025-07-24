/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

// 导出原有的认证类（重命名以避免冲突）
export {
  AuthInitiator as LegacyAuthInitiator,
  AuthVerifier as LegacyAuthVerifier,
  AuthManager
} from './auth';

// 导出新的增强认证类
export { AuthInitiator } from './auth-initiator';
export { AuthVerifier } from './auth-verifier';

// 导出便捷函数
export { getAuthInitiator, resetAuthInitiator } from './auth-initiator';
export { getAuthVerifier, resetAuthVerifier } from './auth-verifier';

// 导出类型
export type {
  AuthenticationContext,
  AuthResult,
  AuthHeaderParts,
  NonceInfo,
  AuthResponse,
  BearerTokenPayload,
  HttpRequestOptions,
  HttpResponse,
  AuthenticatedRequestResult
} from '../types';