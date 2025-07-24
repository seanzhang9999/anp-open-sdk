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

import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';
import * as yaml from 'yaml';
import { getUserDataManager } from './local-user-data-manager';
import { DIDDocument, AgentConfig } from '../types';

/**
 * 用户输入接口
 */
export interface CreateUserInput {
  name: string;
  host: string;
  port: number;
  dir: string;
  type: string;
}

/**
 * 创建DID用户选项
 */
export interface CreateDidUserOptions {
  didHex?: boolean;
  didCheckUnique?: boolean;
  userDidPath?: string;
}

/**
 * 创建DID用户
 * 对应Python版本的create_did_user函数
 */
export async function createDidUser(
  userInput: CreateUserInput,
  options: CreateDidUserOptions = {}
): Promise<DIDDocument | null> {
  const {
    didHex = true,
    didCheckUnique = true,
    userDidPath
  } = options;

  // 验证必需字段
  const requiredFields = ['name', 'host', 'port', 'dir', 'type'];
  for (const field of requiredFields) {
    if (!(field in userInput)) {
      console.error(`缺少必需的参数字段: ${field}`);
      return null;
    }
  }

  // 获取用户目录路径
  const resolvedUserDidPath = userDidPath || path.resolve(process.cwd(), '..', 'data_user');

  // 检查并处理用户名冲突
  const finalName = await handleUsernameConflict(userInput.name, resolvedUserDidPath);
  userInput.name = finalName;

  // 检查域名端口下用户名唯一性
  const userDataManager = getUserDataManager();
  if (userDataManager.isUsernameTaken(userInput.name, userInput.host, userInput.port)) {
    console.error(`用户名 '${userInput.name}' 在域名端口 ${userInput.host}:${userInput.port} 下已存在`);
    return null;
  }

  // 生成唯一ID
  const uniqueId = didHex ? crypto.randomBytes(8).toString('hex') : null;

  // 构建DID
  const didId = buildDidId(userInput, uniqueId);

  // 检查DID唯一性
  if (!didHex && didCheckUnique) {
    const isDuplicate = await checkDidUniqueness(didId, resolvedUserDidPath);
    if (isDuplicate) {
      console.error(`DID已存在: ${didId}`);
      return null;
    }
  }

  // 创建用户目录
  const userDirName = didHex ? `user_${uniqueId}` : `user_${userInput.name}`;
  const userDirPath = path.join(resolvedUserDidPath, userInput.host, 'anp_users', userDirName);

  try {
    // 创建目录结构
    await fs.mkdir(userDirPath, { recursive: true });

    // 构建路径段
    const pathSegments = [userInput.dir, userInput.type];
    if (didHex && uniqueId) {
      pathSegments.push(uniqueId);
    }

    // 构建Agent描述URL
    const agentDescriptionUrl = `http://${userInput.host}:${userInput.port}/${pathSegments.join('/')}/ad.json`;

    // 创建DID文档和密钥
    const { didDocument, keys } = await createDidWbaDocument({
      hostname: userInput.host,
      port: userInput.port,
      pathSegments,
      agentDescriptionUrl
    });

    // 设置DID ID
    didDocument.id = didId;
    if (keys && Object.keys(keys).length > 0) {
      didDocument.key_id = Object.keys(keys)[0];
    }

    // 保存DID文档
    const didDocPath = path.join(userDirPath, 'did_document.json');
    await fs.writeFile(didDocPath, JSON.stringify(didDocument, null, 2), 'utf-8');

    // 保存密钥文件
    if (keys) {
      for (const [keyId, keyPair] of Object.entries(keys)) {
        const privateKeyPath = path.join(userDirPath, `${keyId}_private.pem`);
        const publicKeyPath = path.join(userDirPath, `${keyId}_public.pem`);
        
        await fs.writeFile(privateKeyPath, keyPair.privateKey);
        await fs.writeFile(publicKeyPath, keyPair.publicKey);
      }
    }

    // 创建Agent配置
    const now = new Date();
    const agentCfg: AgentConfig = {
      name: userInput.name,
      unique_id: uniqueId || '',
      did: didDocument.id,
      type: userInput.type,
      owner: {
        name: "anpsdk 创造用户",
        '@id': "https://localhost"
      },
      description: "anpsdk的测试用户",
      version: "0.1.0",
      created_at: now.toISOString()
    };

    const agentCfgPath = path.join(userDirPath, 'agent_cfg.yaml');
    await fs.writeFile(agentCfgPath, yaml.stringify(agentCfg), 'utf-8');

    // 创建JWT密钥对
    await createJwtKeyPair(userDirPath);

    console.debug(`DID创建成功: ${didDocument.id}`);
    console.debug(`DID文档已保存到: ${userDirPath}`);
    console.debug(`密钥已保存到: ${userDirPath}`);
    console.debug(`用户文件已保存到: ${userDirPath}`);
    console.debug(`jwt密钥已保存到: ${userDirPath}`);

    // 创建成功后，立即加载到内存
    try {
      const newUserData = await userDataManager.loadSingleUser(userDirPath);
      if (newUserData) {
        console.log(`新用户已创建并加载到内存: ${newUserData.did}`);
      } else {
        console.warn(`用户创建成功但加载到内存失败: ${userDirPath}`);
      }
    } catch (error) {
      console.error(`创建用户后加载到用户管理器失败，报错: ${error}`);
      return null;
    }

    return didDocument;

  } catch (error) {
    console.error(`创建用户失败: ${error}`);
    return null;
  }
}

/**
 * 处理用户名冲突
 */
async function handleUsernameConflict(baseName: string, userDidPath: string): Promise<string> {
  const existingNames = await getExistingUsernames(userDidPath);
  
  if (!existingNames.includes(baseName)) {
    return baseName;
  }

  // 生成带日期后缀的新名称
  const dateSuffix = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  let newName = `${baseName}_${dateSuffix}`;
  
  if (!existingNames.includes(newName)) {
    console.debug(`用户名 ${baseName} 已存在，使用新名称：${newName}`);
    return newName;
  }

  // 如果带日期的名称也存在，添加数字后缀
  let counter = 1;
  while (existingNames.includes(`${newName}_${counter}`)) {
    counter++;
  }
  
  newName = `${newName}_${counter}`;
  console.debug(`用户名 ${baseName} 已存在，使用新名称：${newName}`);
  return newName;
}

/**
 * 获取现有用户名列表
 */
async function getExistingUsernames(userDidPath: string): Promise<string[]> {
  const usernames: string[] = [];
  
  try {
    const domains = await fs.readdir(userDidPath, { withFileTypes: true });
    
    for (const domain of domains) {
      if (domain.isDirectory()) {
        const usersPath = path.join(userDidPath, domain.name, 'anp_users');
        
        try {
          const users = await fs.readdir(usersPath, { withFileTypes: true });
          
          for (const user of users) {
            if (user.isDirectory()) {
              const cfgPath = path.join(usersPath, user.name, 'agent_cfg.yaml');
              
              try {
                const cfgContent = await fs.readFile(cfgPath, 'utf-8');
                const cfg = yaml.parse(cfgContent);
                if (cfg && cfg.name) {
                  usernames.push(cfg.name);
                }
              } catch {
                // 忽略读取错误
              }
            }
          }
        } catch {
          // anp_users目录不存在，跳过
        }
      }
    }
  } catch {
    // 用户目录不存在
  }
  
  return usernames;
}

/**
 * 构建DID ID
 */
function buildDidId(userInput: CreateUserInput, uniqueId: string | null): string {
  let hostPort = userInput.host;
  if (userInput.port !== 80 && userInput.port !== 443) {
    hostPort = `${userInput.host}%3A${userInput.port}`;
  }

  const didParts = ['did', 'wba', hostPort];
  
  if (userInput.dir) {
    didParts.push(encodeURIComponent(userInput.dir));
  }
  
  if (userInput.type) {
    didParts.push(encodeURIComponent(userInput.type));
  }
  
  if (uniqueId) {
    didParts.push(uniqueId);
  }
  
  return didParts.join(':');
}

/**
 * 检查DID唯一性
 */
async function checkDidUniqueness(didId: string, userDidPath: string): Promise<boolean> {
  try {
    const domains = await fs.readdir(userDidPath, { withFileTypes: true });
    
    for (const domain of domains) {
      if (domain.isDirectory()) {
        const usersPath = path.join(userDidPath, domain.name, 'anp_users');
        
        try {
          const users = await fs.readdir(usersPath, { withFileTypes: true });
          
          for (const user of users) {
            if (user.isDirectory()) {
              const didPath = path.join(usersPath, user.name, 'did_document.json');
              
              try {
                const didContent = await fs.readFile(didPath, 'utf-8');
                const didDoc = JSON.parse(didContent);
                if (didDoc.id === didId) {
                  return true; // 找到重复的DID
                }
              } catch {
                // 忽略读取错误
              }
            }
          }
        } catch {
          // anp_users目录不存在，跳过
        }
      }
    }
  } catch {
    // 用户目录不存在
  }
  
  return false; // 没有找到重复的DID
}

/**
 * 创建DID WBA文档
 * 简化版本，实际实现需要根据具体的DID WBA规范
 */
async function createDidWbaDocument(options: {
  hostname: string;
  port: number;
  pathSegments: string[];
  agentDescriptionUrl: string;
}): Promise<{
  didDocument: DIDDocument;
  keys: Record<string, { privateKey: string; publicKey: string }>;
}> {
  // 生成密钥对
  const keyPair = crypto.generateKeyPairSync('ec', {
    namedCurve: 'secp256k1',
    publicKeyEncoding: {
      type: 'spki',
      format: 'pem'
    },
    privateKeyEncoding: {
      type: 'pkcs8',
      format: 'pem'
    }
  });

  const keyId = 'key-1';
  
  // 创建DID文档
  const didDocument: DIDDocument = {
    '@context': [
      'https://www.w3.org/ns/did/v1',
      'https://w3id.org/security/suites/secp256k1-2019/v1'
    ],
    id: '', // 将在外部设置
    verificationMethod: [
      {
        id: `#${keyId}`,
        type: 'EcdsaSecp256k1VerificationKey2019',
        controller: '', // 将在外部设置
        publicKeyJwk: {
          kty: 'EC',
          crv: 'secp256k1',
          x: '', // 简化实现，实际需要从公钥提取
          y: '',
          kid: keyId
        }
      }
    ],
    authentication: [`#${keyId}`],
    service: [
      {
        id: '#agent-service',
        type: 'AgentService',
        serviceEndpoint: options.agentDescriptionUrl
      }
    ],
    key_id: keyId
  };

  const keys = {
    [keyId]: {
      privateKey: keyPair.privateKey,
      publicKey: keyPair.publicKey
    }
  };

  return { didDocument, keys };
}

/**
 * 创建JWT密钥对
 */
async function createJwtKeyPair(userDirPath: string): Promise<void> {
  const keyPair = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding: {
      type: 'spki',
      format: 'pem'
    },
    privateKeyEncoding: {
      type: 'pkcs8',
      format: 'pem'
    }
  });

  // 测试JWT功能
  const testContent = { user_id: 123 };
  const jwt = require('jsonwebtoken');
  
  try {
    const token = jwt.sign(testContent, keyPair.privateKey, { algorithm: 'RS256' });
    const decoded = jwt.verify(token, keyPair.publicKey, { algorithms: ['RS256'] });
    
    if (decoded.user_id === testContent.user_id) {
      const privateKeyPath = path.join(userDirPath, 'private_key.pem');
      const publicKeyPath = path.join(userDirPath, 'public_key.pem');
      
      await fs.writeFile(privateKeyPath, keyPair.privateKey);
      await fs.writeFile(publicKeyPath, keyPair.publicKey);
    } else {
      throw new Error('JWT测试失败');
    }
  } catch (error) {
    throw new Error(`JWT密钥对创建失败: ${error}`);
  }
}