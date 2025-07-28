/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { formatDidFromUrl } from './src/foundation/did/did-url-formatter';
import { getLogger } from './src/foundation/utils';

const logger = getLogger('DIDFormatTest');

/**
 * 测试DID格式化函数
 */
function testDidFormatting() {
  console.log('开始测试DID格式化函数...');

  // 测试用例1：标准DID格式（已包含%3A）
  const did1 = 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211';
  const result1 = formatDidFromUrl(did1);
  console.log(`测试1 - 保持标准格式: ${did1} -> ${result1}`);
  console.assert(result1 === did1, '测试1失败：应该保持原始格式不变');

  // 测试用例2：非标准DID格式（使用:而非%3A）
  const did2 = 'did:wba:localhost:9527:wba:user:5fea49e183c6c211';
  const result2 = formatDidFromUrl(did2);
  console.log(`测试2 - 转换为标准格式: ${did2} -> ${result2}`);
  console.assert(result2 === 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211', '测试2失败：应该转换为标准格式');

  // 测试用例3：URL编码的DID
  const did3 = encodeURIComponent('did:wba:localhost%3A9527:wba:user:5fea49e183c6c211');
  const result3 = formatDidFromUrl(did3);
  console.log(`测试3 - 处理URL编码的DID: ${did3} -> ${result3}`);
  console.assert(result3 === 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211', '测试3失败：应该正确处理URL编码');

  // 测试用例4：使用unique_id格式
  const did4 = '5fea49e183c6c211';
  const result4 = formatDidFromUrl(did4, 'localhost', 9527);
  console.log(`测试4 - 从unique_id构建DID: ${did4} -> ${result4}`);
  console.assert(result4 === 'did:wba:localhost%3A9527:wba:user:5fea49e183c6c211', '测试4失败：应该从unique_id构建完整DID');

  // 测试用例5：使用标准端口
  const did5 = '5fea49e183c6c211';
  const result5 = formatDidFromUrl(did5, 'example.com', 80);
  console.log(`测试5 - 使用标准端口: ${did5} -> ${result5}`);
  console.assert(result5 === 'did:wba:example.com:wba:user:5fea49e183c6c211', '测试5失败：标准端口应该省略%3A');

  console.log('DID格式化函数测试完成！');
}

// 执行测试
testDidFormatting();