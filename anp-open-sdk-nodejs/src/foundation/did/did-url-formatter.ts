/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { getLogger } from '../utils';

const logger = getLogger('DIDUrlFormatter');

/**
 * 格式化URL中的DID，支持W3C DID标准
 * 参考Python版本: anp_servicepoint/core_service_handler/did_service_handler.py
 */
export function formatDidFromUrl(userIdOrDid: string, host?: string, port?: number): string {
  // 只进行一次URL解码
  const decodedOnce = decodeURIComponent(userIdOrDid);
  
  logger.debug(`DID格式化输入: ${userIdOrDid} -> 解码一次: ${decodedOnce}`);
  
  if (decodedOnce.startsWith("did:wba")) {
    // 处理已经是DID格式的情况
    if (decodedOnce.includes("%3A")) {
      // 已包含标准DID编码，直接使用（保持W3C DID标准）
      logger.debug(`保持W3C DID标准格式: ${decodedOnce}`);
      return decodedOnce;
    } else {
      // 需要转换为标准格式
      const parts = decodedOnce.split(":");
      if (parts.length > 4 && /^\d+$/.test(parts[3])) {
        // 格式: did:wba:localhost:9527:wba:user:xxx -> did:wba:localhost%3A9527:wba:user:xxx
        const standardFormat = parts.slice(0, 3).join(":") + "%3A" + parts.slice(3).join(":");
        logger.debug(`转换为标准DID格式: ${decodedOnce} -> ${standardFormat}`);
        return standardFormat;
      } else {
        // 其他格式保持不变
        return decodedOnce;
      }
    }
  } else if (decodedOnce.length === 16 && /^[a-f0-9]{16}$/.test(decodedOnce)) {
    // unique_id格式，需要构建完整DID
    const targetHost = host || 'localhost';
    const targetPort = port || 9527;
    
    if (targetPort === 80 || targetPort === 443) {
      const result = `did:wba:${targetHost}:wba:user:${decodedOnce}`;
      logger.debug(`构建DID (标准端口): ${result}`);
      return result;
    } else {
      const result = `did:wba:${targetHost}%3A${targetPort}:wba:user:${decodedOnce}`;
      logger.debug(`构建DID (自定义端口): ${result}`);
      return result;
    }
  } else {
    // 其他格式保持不变
    logger.debug(`保持原格式: ${decodedOnce}`);
    return decodedOnce;
  }
}

/**
 * 简化版DID格式化，用于Agent查找
 */
export function normalizeDIDForAgentLookup(did: string): string {
  return formatDidFromUrl(did);
}

/**
 * 检查DID格式是否有效
 */
export function isValidDIDFormat(did: string): boolean {
  const normalized = formatDidFromUrl(did);
  return normalized.startsWith("did:wba:") && normalized.includes("%3A");
}