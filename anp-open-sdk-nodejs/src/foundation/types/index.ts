/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

/**
 * Foundation层核心类型定义
 * 基于真实data_user数据结构设计
 */

// ============================================================================
// DID相关类型
// ============================================================================

export interface DIDDocument {
  '@context': string[];
  id: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  service: Service[];
  key_id?: string;
}

export interface VerificationMethod {
  id: string;
  type: string;
  controller: string;
  publicKeyJwk: PublicKeyJwk;
}

export interface PublicKeyJwk {
  kty: string;
  crv: string;
  x: string;
  y: string;
  kid: string;
}

export interface Service {
  id: string;
  type: string;
  serviceEndpoint: string;
}

// ============================================================================
// Agent配置类型
// ============================================================================

export interface AgentConfig {
  name: string;
  unique_id: string;
  did: string;
  type: string;
  owner?: {
    name: string;
    '@id': string;
  };
  description?: string;
  version?: string;
  created_at?: string;
  hosted_config?: HostedConfig;
}

export interface HostedConfig {
  parent_did: string;
  host: string;
  port: number;
  created_at: string;
  purpose: string;
}

// ============================================================================
// Agent描述类型
// ============================================================================

export interface AgentDescription {
  '@context': Record<string, string>;
  '@type': string;
  name: string;
  owner: {
    name: string;
    '@id': string;
  };
  description: string;
  version: string;
  created_at: string;
  security_definitions: {
    didwba_sc: {
      scheme: string;
      in: string;
      name: string;
    };
  };
  'ad:interfaces': AgentInterface[];
}

export interface AgentInterface {
  '@type': string;
  protocol: string;
  url?: string;
  name?: string;
  description: string;
}

// ============================================================================
// 密钥和路径类型
// ============================================================================

export interface PasswordPaths {
  did_private_key_file_path: string;
  did_public_key_file_path: string;
  jwt_private_key_file_path: string;
  jwt_public_key_file_path: string;
}

export interface KeyPair {
  privateKey: string;
  publicKey: string;
}

// ============================================================================
// 用户数据类型
// ============================================================================

export interface LocalUserDataOptions {
  folderName: string;
  agentCfg: AgentConfig;
  didDocument: DIDDocument;
  didDocPath: string;
  passwordPaths: PasswordPaths;
  userFolderPath: string;
}

export interface HostedInfo {
  host: string;
  port: number;
  did_suffix?: string;
}

export interface ConflictInfo {
  name: string;
  host: string;
  port: number;
  users: string[];
}

// ============================================================================
// 联系人类型
// ============================================================================

export interface Contact {
  did: string;
  name?: string;
  host?: string;
  port?: number;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface TokenInfo {
  token: string;
  created_at: string;
  expires_at?: string;
  is_revoked?: boolean;
  req_did: string;
}

// ============================================================================
// 认证相关类型
// ============================================================================

export interface AuthenticationContext {
  caller_did: string;
  target_did: string;
  request_url: string;
  method?: string;
  custom_headers?: Record<string, string>;
  json_data?: any;
  use_two_way_auth?: boolean;
  domain?: string;
}

export interface AuthResult {
  success: boolean;
  caller_did?: string;
  error?: string;
  payload?: any;
  token?: string;
  token_type?: string;
  resp_did_auth_header?: any;
}

export interface AuthHeaderParts {
  did: string;
  nonce: string;
  timestamp: string;
  resp_did?: string;
  keyid: string;
  signature: string;
}

export interface NonceInfo {
  nonce: string;
  created_at: Date;
  used: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  req_did: string;
  resp_did: string;
  resp_did_auth_header?: any;
}

export interface BearerTokenPayload {
  req_did: string;
  resp_did: string;
  exp: number;
  iat?: number;
  comments?: string;
}

export interface HttpRequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: any;
  json?: any;
}

export interface HttpResponse {
  status: number;
  headers: Record<string, string>;
  data: any;
}

export interface AuthenticatedRequestResult {
  status: number;
  response: string;
  info: string;
  is_auth_pass: boolean;
}

// ============================================================================
// 域名管理类型
// ============================================================================

export interface DomainConfig {
  domain: string;
  supported: boolean;
  port: number;
  data_path: string;
}

export interface DomainPaths {
  base_path: string;
  user_did_path: string;
  user_hosted_path: string;
  agents_cfg_path: string;
  hosted_did_queue?: string;
  hosted_did_results?: string;
}

export interface SupportedDomains {
  [domain: string]: number;
}

export interface DomainStats {
  supported_domains: number;
  domains: string[];
  cache_size: number;
  domain_status: Record<string, DomainStatus>;
}

export interface DomainStatus {
  base_exists: boolean;
  users_exists: boolean;
  agents_exists: boolean;
}

export interface HostPortPair {
  host: string;
  port: number;
}

export interface DomainValidationResult {
  valid: boolean;
  error?: string;
}

// ============================================================================
// Agent映射配置类型
// ============================================================================

export interface AgentMappingConfig {
  name: string;
  share_did?: {
    enabled: boolean;
    shared_did: string;
    path_prefix: string;
    primary_agent: boolean;
  };
  api: ApiEndpoint[];
  openapi_version?: string;
  title?: string;
  version?: string;
}

export interface ApiEndpoint {
  path: string;
  method: string;
  handler: string;
  summary?: string;
  params?: Record<string, ApiParam>;
  result?: Record<string, ApiParam>;
}

export interface ApiParam {
  type: string;
  value: any;
}

// ============================================================================
// 错误类型
// ============================================================================

export class ANPError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ANPError';
  }
}

export class UserNotFoundError extends ANPError {
  constructor(did: string) {
    super(`User not found: ${did}`, 'USER_NOT_FOUND', { did });
  }
}

export class DomainNotSupportedError extends ANPError {
  constructor(domain: string, port: number) {
    super(`Domain not supported: ${domain}:${port}`, 'DOMAIN_NOT_SUPPORTED', { domain, port });
  }
}

export class FileNotFoundError extends ANPError {
  constructor(filePath: string) {
    super(`File not found: ${filePath}`, 'FILE_NOT_FOUND', { filePath });
  }
}

// ============================================================================
// 工具类型
// ============================================================================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// ============================================================================
// 常量
// ============================================================================

export const DEFAULT_CONFIG = {
  USER_DID_KEY_ID: 'key-1',
  DEFAULT_HOST: 'localhost',
  DEFAULT_PORT: 9527,
  DATA_USER_DIR: 'data_user',
  SUPPORTED_DID_METHODS: ['did:wba'],
  SUPPORTED_KEY_TYPES: ['EcdsaSecp256k1VerificationKey2019'],
} as const;

export const FILE_NAMES = {
  DID_DOCUMENT: 'did_document.json',
  AGENT_CONFIG: 'agent_cfg.yaml',
  AGENT_DESCRIPTION: 'ad.json',
  API_INTERFACE_YAML: 'api_interface.yaml',
  API_INTERFACE_JSON: 'api_interface.json',
  PRIVATE_KEY: 'private_key.pem',
  PUBLIC_KEY: 'public_key.pem',
} as const;

export const FOLDER_PREFIXES = {
  USER: 'user_',
  HOSTED_USER: 'user_hosted_',
  AGENT_CONFIG: 'agent_',
} as const;