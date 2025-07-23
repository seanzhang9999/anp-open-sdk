/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { BaseUnifiedConfig } from './types';

export class ConfigManager {
  private static instance: ConfigManager;
  private config: BaseUnifiedConfig | null = null;
  private configPath: string;

  private constructor() {
    this.configPath = process.env.ANP_CONFIG_PATH || 'unified_config.yaml';
  }

  public static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }

  public async loadConfig(): Promise<BaseUnifiedConfig> {
    if (this.config) {
      return this.config;
    }

    try {
      const configContent = fs.readFileSync(this.configPath, 'utf8');
      const parsedConfig = yaml.parse(configContent) as BaseUnifiedConfig;
      
      // 合并环境变量
      this.mergeEnvironmentVariables(parsedConfig);
      
      this.config = parsedConfig;
      return this.config;
    } catch (error) {
      throw new Error(`Failed to load config from ${this.configPath}: ${error}`);
    }
  }

  public getConfig(): BaseUnifiedConfig {
    if (!this.config) {
      throw new Error('Config not loaded. Call loadConfig() first.');
    }
    return this.config;
  }

  public resolvePath(relativePath: string): string {
    if (path.isAbsolute(relativePath)) {
      return relativePath;
    }
    return path.resolve(this.getAppRoot(), relativePath);
  }

  public getAppRoot(): string {
    return this.config?.appRoot || process.cwd();
  }

  public reload(): void {
    this.config = null;
  }

  private mergeEnvironmentVariables(config: BaseUnifiedConfig): void {
    // 合并环境变量到配置中
    if (process.env.OPENAI_API_KEY) {
      config.env.openaiApiKey = process.env.OPENAI_API_KEY;
      config.secrets.openaiApiKey = process.env.OPENAI_API_KEY;
    }
    
    if (process.env.PORT) {
      config.anpSdk.port = parseInt(process.env.PORT, 10);
    }
    
    if (process.env.HOST) {
      config.anpSdk.host = process.env.HOST;
    }
    
    if (process.env.DEBUG_MODE) {
      config.anpSdk.debugMode = process.env.DEBUG_MODE === 'true';
    }
  }
}

// 全局配置访问函数
export function getGlobalConfig(): BaseUnifiedConfig {
  return ConfigManager.getInstance().getConfig();
}

export function loadGlobalConfig(): Promise<BaseUnifiedConfig> {
  return ConfigManager.getInstance().loadConfig();
}