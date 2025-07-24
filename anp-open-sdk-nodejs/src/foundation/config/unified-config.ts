/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * 统一配置管理模块
 * 
 * 此模块提供统一的配置管理功能，支持：
 * - YAML配置文件管理
 * - 环境变量映射和类型转换
 * - 路径占位符自动解析
 * - 属性访问和代码提示
 * - 敏感信息保护
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { config } from 'dotenv';
import { 
  BaseUnifiedConfig, 
  BaseUnifiedConfigProtocol,
  EnvConfig,
  SecretsConfig,
  MultiAgentModeConfig,
  LogConfig,
  AnpSdkConfig,
  LlmConfig,
  MailConfig,
  ChatConfig,
  WebApiConfig,
  AccelerationConfig,
  AuthMiddlewareConfig,
  DidConfig
} from './types';

// 全局配置实例
let globalConfig: UnifiedConfig | null = null;

/**
 * 设置全局配置实例
 */
export function setGlobalConfig(configInstance: UnifiedConfig): void {
  if (globalConfig !== null) {
    console.warn("Warning: Global config is being overridden.");
  }
  globalConfig = configInstance;
}

/**
 * 获取全局配置实例
 */
export function getGlobalConfig(): BaseUnifiedConfigProtocol {
  if (globalConfig === null) {
    throw new Error(
      "Global config has not been set. " +
      "Please call setGlobalConfig(config) at your application's entry point."
    );
  }
  return globalConfig;
}

/**
 * 配置节点类
 * 提供动态属性访问和类型推断
 */
class ConfigNode {
  private data: Record<string, any>;
  private parentPath: string;

  constructor(data: Record<string, any>, parentPath: string = "") {
    this.data = data;
    this.parentPath = parentPath;
    
    // 动态创建属性
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        const childPath = parentPath ? `${parentPath}.${key}` : key;
        (this as any)[key] = new ConfigNode(value, childPath);
      } else {
        (this as any)[key] = value;
      }
    }
  }

  /**
   * 获取属性值
   */
  get(key: string): any {
    if (key in this.data) {
      return this.data[key];
    }
    throw new Error(`配置项 '${this.parentPath}.${key}' 不存在`);
  }

  /**
   * 设置属性值
   */
  set(key: string, value: any): void {
    this.data[key] = value;
    (this as any)[key] = value;
  }

  /**
   * 转换为普通对象
   */
  toObject(): Record<string, any> {
    return JSON.parse(JSON.stringify(this.data));
  }
}

/**
 * 环境变量配置类
 */
class EnvConfigNode implements EnvConfig {
  private envMapping: Record<string, string>;
  private values: Record<string, any> = {};

  constructor(envMapping: Record<string, string>) {
    this.envMapping = envMapping;
    this.loadEnv();
  }

  private loadEnv(): void {
    for (const [key, envVar] of Object.entries(this.envMapping)) {
      if (envVar) {
        const envValue = process.env[envVar];
        this.values[key] = this.convertEnvType(envValue, key);
        (this as any)[key] = this.values[key];
      }
    }
  }

  private convertEnvType(value: string | undefined, key: string): any {
    if (!value) return undefined;

    // 根据键名推断类型
    const keyLower = key.toLowerCase();
    
    if (keyLower.includes('port') || keyLower.includes('timeout') || keyLower.includes('max')) {
      const num = parseInt(value, 10);
      return isNaN(num) ? undefined : num;
    }
    
    if (keyLower.includes('debug') || keyLower.includes('enable') || keyLower.includes('use')) {
      return value.toLowerCase() === 'true' || value === '1';
    }
    
    if (keyLower.includes('path') && value.includes(path.delimiter)) {
      return value.split(path.delimiter).filter(p => p.trim());
    }
    
    return value;
  }

  reload(): void {
    this.loadEnv();
  }

  toDict(): Record<string, any> {
    return { ...this.values };
  }

  // 实现EnvConfig接口的所有属性
  debugMode?: boolean;
  host?: string;
  port?: number;
  systemPath?: string[];
  homeDir?: string;
  userName?: string;
  shell?: string;
  tempDir?: string;
  pythonPath?: string[];
  pythonHome?: string;
  virtualEnv?: string;
  javaHome?: string;
  nodePath?: string;
  goPath?: string;
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

/**
 * 敏感信息配置类
 */
class SecretsConfigNode implements SecretsConfig {
  private secretsList: string[];
  private envMapping: Record<string, string>;

  constructor(secretsList: string[], envMapping: Record<string, string>) {
    this.secretsList = secretsList;
    this.envMapping = envMapping;
    
    // 动态加载敏感信息
    for (const secretName of secretsList) {
      if (secretName in envMapping) {
        (this as any)[secretName] = process.env[envMapping[secretName]];
      }
    }
  }

  toDict(): Record<string, any> {
    const result: Record<string, any> = {};
    for (const name of this.secretsList) {
      result[name] = "***"; // 隐藏敏感信息
    }
    return result;
  }

  // 实现SecretsConfig接口的所有属性
  openaiApiKey?: string;
  anthropicApiKey?: string;
  mailPassword?: string;
  hosterMailPassword?: string;
  senderMailPassword?: string;
  databaseUrl?: string;
}

/**
 * 统一配置类
 * 对应Python版本的UnifiedConfig
 */
export class UnifiedConfig implements BaseUnifiedConfigProtocol {
  private static appRootCls: string | null = null;
  
  private appRootInstance: string;
  private configFile: string;
  private configData: Record<string, any> = {};
  private logger = console; // 简化的日志记录

  // 配置节点
  public multiAgentMode!: MultiAgentModeConfig;
  public logSettings!: LogConfig;
  public anpSdk!: AnpSdkConfig;
  public llm!: LlmConfig;
  public mail!: MailConfig;
  public chat!: ChatConfig;
  public webApi!: WebApiConfig;
  public acceleration!: AccelerationConfig;
  public authMiddleware!: AuthMiddlewareConfig;
  public didConfig!: DidConfig;
  public env!: EnvConfig;
  public secrets!: SecretsConfig;
  public appRoot!: string;

  constructor(configFile?: string, appRoot?: string) {
    // 设置应用根目录
    this.appRootInstance = appRoot ? path.resolve(appRoot) : process.cwd();
    
    // 如果类属性尚未设置，则使用实例的appRoot设置它
    if (UnifiedConfig.appRootCls === null) {
      UnifiedConfig.appRootCls = this.appRootInstance;
    } else if (UnifiedConfig.appRootCls !== this.appRootInstance) {
      this.logger.warn(
        `新的 UnifiedConfig 实例指定了不同的 app_root。` +
        `类方法将继续使用第一个初始化的路径: ${UnifiedConfig.appRootCls}`
      );
    }

    // 加载.env文件
    const envPath = path.join(this.appRootInstance, '.env');
    if (fs.existsSync(envPath)) {
      config({ path: envPath, override: true });
      this.logger.info(`已从 ${envPath} 加载环境变量`);
    }

    // 解析配置文件路径
    this.configFile = this.resolveConfigFile(configFile);
    
    // 加载配置
    this.load();
    this.createConfigTree();
    this.createEnvConfigs();
  }

  /**
   * 解析配置文件路径
   */
  private resolveConfigFile(configFile?: string): string {
    if (configFile) {
      return path.resolve(configFile);
    }
    return path.join(this.appRootInstance, 'unified_config.yaml');
  }

  /**
   * 创建配置树
   */
  private createConfigTree(): void {
    const processedData = this.processPathsInData(this.configData);
    const specialKeys = new Set(['env_mapping', 'secrets', 'env_types', 'path_config']);
    
    for (const [key, value] of Object.entries(processedData)) {
      if (!specialKeys.has(key) && typeof value === 'object' && value !== null) {
        (this as any)[key] = new ConfigNode(value, key);
      } else if (!specialKeys.has(key)) {
        (this as any)[key] = value;
      }
    }
    
    this.appRoot = this.appRootInstance;
  }

  /**
   * 创建环境变量和敏感信息配置
   */
  private createEnvConfigs(): void {
    const envMapping = this.configData.env_mapping || {};
    const secretsList = this.configData.secrets || [];
    
    this.env = new EnvConfigNode(envMapping);
    this.secrets = new SecretsConfigNode(secretsList, envMapping);
  }

  /**
   * 处理数据中的路径占位符
   */
  private processPathsInData(data: any): any {
    if (typeof data === 'object' && data !== null) {
      if (Array.isArray(data)) {
        return data.map(item => this.processPathsInData(item));
      } else {
        const result: Record<string, any> = {};
        for (const [key, value] of Object.entries(data)) {
          result[key] = this.processPathsInData(value);
        }
        return result;
      }
    } else if (typeof data === 'string' && data.includes('{APP_ROOT}')) {
      return UnifiedConfig.resolvePath(data);
    }
    return data;
  }

  /**
   * 加载配置文件
   */
  public load(): Record<string, any> {
    try {
      if (fs.existsSync(this.configFile)) {
        const content = fs.readFileSync(this.configFile, 'utf-8');
        this.configData = yaml.parse(content) || {};
        this.logger.info(`已从 ${this.configFile} 加载配置`);
      } else {
        this.configData = this.getDefaultConfig();
        this.save();
        this.logger.info(`已创建默认配置文件 ${this.configFile}`);
      }
    } catch (error) {
      this.logger.error(`加载配置出错: ${error}`);
      this.configData = this.getDefaultConfig();
    }
    return this.configData;
  }

  /**
   * 保存配置文件
   */
  public save(): boolean {
    try {
      const dir = path.dirname(this.configFile);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      
      const content = yaml.stringify(this.configData);
      fs.writeFileSync(this.configFile, content, 'utf-8');
      this.logger.info(`已保存配置到 ${this.configFile}`);
      return true;
    } catch (error) {
      this.logger.error(`保存配置出错: ${error}`);
      return false;
    }
  }

  /**
   * 重新加载配置
   */
  public reload(): void {
    this.load();
    this.createConfigTree();
    this.createEnvConfigs();
    this.logger.info("配置已重新加载");
  }

  /**
   * 解析路径，将{APP_ROOT}替换为实际的应用根目录
   */
  public static resolvePath(pathStr: string): string {
    if (UnifiedConfig.appRootCls === null) {
      throw new Error("UnifiedConfig 尚未初始化，无法解析路径。请先创建 UnifiedConfig 实例。");
    }

    const resolvedPath = pathStr.replace('{APP_ROOT}', UnifiedConfig.appRootCls);
    
    if (path.isAbsolute(resolvedPath)) {
      return path.resolve(resolvedPath);
    } else {
      return path.resolve(UnifiedConfig.appRootCls, resolvedPath);
    }
  }

  /**
   * 实例方法：解析路径
   */
  public resolvePath(pathStr: string): string {
    return UnifiedConfig.resolvePath(pathStr);
  }

  /**
   * 获取应用根目录
   */
  public static getAppRoot(): string {
    if (UnifiedConfig.appRootCls === null) {
      throw new Error("UnifiedConfig 尚未初始化，无法获取 app_root。请先创建 UnifiedConfig 实例。");
    }
    return UnifiedConfig.appRootCls;
  }

  /**
   * 实例方法：获取应用根目录
   */
  public getAppRoot(): string {
    return this.appRootInstance;
  }

  /**
   * 添加路径到PATH环境变量
   */
  public addToPath(newPath: string): void {
    const currentPath = process.env.PATH || '';
    const separator = process.platform === 'win32' ? ';' : ':';
    const newPathStr = `${newPath}${separator}${currentPath}`;
    process.env.PATH = newPathStr;
    
    if (this.env && 'reload' in this.env && typeof (this.env as any).reload === 'function') {
      (this.env as any).reload();
    }
  }

  /**
   * 在PATH中查找文件
   */
  public findInPath(filename: string): string[] {
    const matches: string[] = [];
    
    try {
      const pathEnv = process.env.PATH || '';
      if (!pathEnv) return matches;
      
      const separator = process.platform === 'win32' ? ';' : ':';
      const pathDirs = pathEnv.split(separator);
      
      for (const pathStr of pathDirs) {
        if (!pathStr.trim()) continue;
        
        try {
          const pathDir = path.resolve(pathStr.trim());
          if (!fs.existsSync(pathDir)) continue;
          
          const target = path.join(pathDir, filename);
          if (fs.existsSync(target) && fs.statSync(target).isFile()) {
            matches.push(target);
          }
          
          // Windows下检查.exe文件
          if (process.platform === 'win32' && !filename.endsWith('.exe')) {
            const targetExe = path.join(pathDir, `${filename}.exe`);
            if (fs.existsSync(targetExe) && fs.statSync(targetExe).isFile()) {
              matches.push(targetExe);
            }
          }
        } catch (error) {
          continue;
        }
      }
    } catch (error) {
      this.logger.error(`在 PATH 中查找文件 ${filename} 时出错: ${error}`);
    }
    
    return matches;
  }

  /**
   * 获取路径信息
   */
  public getPathInfo(): Record<string, any> {
    const info: Record<string, any> = {
      app_root: this.appRootInstance,
      config_file: this.configFile,
    };
    
    try {
      const pathEnv = process.env.PATH || '';
      if (pathEnv) {
        const separator = process.platform === 'win32' ? ';' : ':';
        const pathDirs = pathEnv.split(separator)
          .map(p => p.trim())
          .filter(p => p);
        
        const existingPaths: string[] = [];
        const missingPaths: string[] = [];
        
        for (const pathDir of pathDirs) {
          try {
            if (fs.existsSync(pathDir)) {
              existingPaths.push(pathDir);
            } else {
              missingPaths.push(pathDir);
            }
          } catch (error) {
            missingPaths.push(pathDir);
          }
        }
        
        info.path_count = pathDirs.length;
        info.existing_paths = existingPaths;
        info.missing_paths = missingPaths;
      }
      
      const homeEnv = process.env.HOME || process.env.USERPROFILE;
      if (homeEnv) {
        info.home_directory = homeEnv;
      }
      
      const userEnv = process.env.USER || process.env.USERNAME;
      if (userEnv) {
        info.current_user = userEnv;
      }
    } catch (error) {
      this.logger.error(`获取路径信息时出错: ${error}`);
    }
    
    return info;
  }

  /**
   * 转换为字典
   */
  public toDict(): Record<string, any> {
    return JSON.parse(JSON.stringify(this.configData));
  }

  /**
   * 获取默认配置
   */
  private getDefaultConfig(): Record<string, any> {
    const defaultConfigPath = path.join(this.appRootInstance, 'unified_config.default.yaml');
    
    if (fs.existsSync(defaultConfigPath)) {
      try {
        const content = fs.readFileSync(defaultConfigPath, 'utf-8');
        return yaml.parse(content) || {};
      } catch (error) {
        this.logger.warn(`读取默认配置文件失败: ${error}`);
      }
    } else {
      this.logger.warn(`默认配置文件 ${defaultConfigPath} 不存在。将使用空配置。`);
    }
    
    return {};
  }
}