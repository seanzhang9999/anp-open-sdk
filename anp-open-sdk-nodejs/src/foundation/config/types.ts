/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

export interface MultiAgentModeConfig {
  agentsCfgPath: string;
}

export interface AnpSdkAgentConfig {
  demoAgent1: string;
  demoAgent2: string;
  demoAgent3: string;
}

export interface AuthMiddlewareConfig {
  exemptPaths: string[];
}

export interface AnpSdkConfig {
  debugMode: boolean;
  host: string;
  port: number;
  userDidPath: string;
  userHostedPath: string;
  authVirtualDir: string;
  msgVirtualDir: string;
  tokenExpireTime: number;
  nonceExpireMinutes: number;
  jwtAlgorithm: string;
  userDidKeyId: string;
  helperLang: string;
  agent: AnpSdkAgentConfig;
  
  useTransformerServer: boolean;
  transformerServerUrl: string;
  fallbackToLocal: boolean;
}

export interface LlmConfig {
  apiUrl: string;
  defaultModel: string;
  maxTokens: number;
  systemPrompt: string;
}

export interface MailConfig {
  useLocalBackend: boolean;
  localBackendPath: string;
  smtpServer: string;
  smtpPort: number;
  imapServer: string;
  imapPort: number;
  hosterMailUser: string;
  senderMailUser: string;
  registerMailUser: string;
}

export interface ChatConfig {
  maxHistoryItems: number;
  maxProcessCount: number;
}

export interface WebApiServerConfig {
  generateNewDidEachTime: boolean;
  webuiHost: string;
  webuiPort: number;
}

export interface WebApiConfig {
  server: WebApiServerConfig;
}

export interface AccelerationConfig {
  enableLocal: boolean;
  performanceMonitoring: boolean;
  cacheSize: number;
}

export interface DidUserTypeConfig {
  user: string;
  hostuser: string;
  test: string;
}

export interface DidUrlEncodingConfig {
  usePercentEncoding: boolean;
  supportLegacyEncoding: boolean;
}

export interface DidPathTemplateConfig {
  userDidPath: string;
  userHostedPath: string;
  agentsCfgPath: string;
}

export interface DidParsingConfig {
  strictValidation: boolean;
  allowInsecure: boolean;
  defaultHost: string;
  defaultPort: number;
}

export interface DidConfig {
  method: string;
  formatTemplate: string;
  routerPrefix: string;
  userPathTemplate: string;
  hostuserPathTemplate: string;
  testuserPathTemplate: string;
  userTypes: DidUserTypeConfig;
  creatableUserTypes: string[];
  hosts: Record<string, number>;
  pathTemplates: DidPathTemplateConfig;
  urlEncoding: DidUrlEncodingConfig;
  insecurePatterns: string[];
  parsing: DidParsingConfig;
}

export interface LogDetailConfig {
  file?: string;
  maxSize?: number;
}

export interface LogConfig {
  logLevel?: string;
  detail: LogDetailConfig;
}

export interface EnvConfig {
  debugMode?: boolean;
  host?: string;
  port?: number;
  openaiApiKey?: string;
  anthropicApiKey?: string;
  mailPassword?: string;
  hosterMailPassword?: string;
  senderMailPassword?: string;
  databaseUrl?: string;
  redisUrl?: string;
  useLocalMail?: boolean;
  enableLocalAcceleration?: boolean;
}

export interface SecretsConfig {
  openaiApiKey?: string;
  anthropicApiKey?: string;
  mailPassword?: string;
  hosterMailPassword?: string;
  senderMailPassword?: string;
  databaseUrl?: string;
}

export interface BaseUnifiedConfig {
  multiAgentMode: MultiAgentModeConfig;
  logSettings: LogConfig;
  anpSdk: AnpSdkConfig;
  llm: LlmConfig;
  mail: MailConfig;
  chat: ChatConfig;
  webApi: WebApiConfig;
  acceleration: AccelerationConfig;
  authMiddleware: AuthMiddlewareConfig;
  didConfig: DidConfig;
  env: EnvConfig;
  secrets: SecretsConfig;
  appRoot: string;
}