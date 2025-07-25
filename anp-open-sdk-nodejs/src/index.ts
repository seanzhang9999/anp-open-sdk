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

export * from './foundation';
export * from './servicepoint';

// 导出Runtime模块 - 避免AgentInfo类型冲突
export {
  Agent,
  AgentManager,
  GlobalMessageManager,
  GlobalGroupManager,
  GroupRunner
} from './runtime';
export type {
  AgentOptions,
  ApiRoute,
  MessageHandler,
  GroupEventHandler,
  AgentInfo as RuntimeAgentInfo,
  AgentSearchRecord,
  AgentContactInfo,
  SessionRecord,
  ApiCallRecord
} from './runtime';
export * from './runtime/decorators';

export * from './server';