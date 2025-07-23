/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import 'reflect-metadata';
import { ANPUser } from '@foundation/user';
import { getLogger } from '@foundation/utils';

const logger = getLogger('AgentDecorators');

// 元数据键
const API_METADATA_KEY = Symbol('api');
const MESSAGE_HANDLER_METADATA_KEY = Symbol('messageHandler');
const GROUP_EVENT_HANDLER_METADATA_KEY = Symbol('groupEventHandler');

export interface ApiOptions {
  path?: string;
  method?: string;
  description?: string;
  public?: boolean;
}

export interface MessageHandlerOptions {
  eventType?: string;
  description?: string;
}

export interface GroupEventHandlerOptions {
  eventType?: string;
  description?: string;
}

export interface ApiMetadata {
  path: string;
  method: string;
  methodName: string;
  description?: string;
  public: boolean;
}

export interface MessageHandlerMetadata {
  eventType: string;
  methodName: string;
  description?: string;
}

export interface GroupEventHandlerMetadata {
  eventType: string;
  methodName: string;
  description?: string;
}

/**
 * API装饰器 - 将方法暴露为API端点
 */
export function api(path?: string, options?: ApiOptions) {
  return function(target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = options?.method || 'GET';
    const finalPath = path || `/${propertyName}`;
    const isPublic = options?.public ?? false;
    
    // 获取现有的API列表或创建新的
    const existingApis: ApiMetadata[] = Reflect.getMetadata(API_METADATA_KEY, target) || [];
    
    // 添加新的API元数据
    const apiMetadata: ApiMetadata = {
      path: finalPath,
      method: method.toUpperCase(),
      methodName: propertyName,
      description: options?.description,
      public: isPublic
    };
    
    existingApis.push(apiMetadata);
    
    // 设置元数据
    Reflect.defineMetadata(API_METADATA_KEY, existingApis, target);
    
    logger.debug(`注册API: ${method.toUpperCase()} ${finalPath} -> ${propertyName}`);
    
    return descriptor;
  };
}

/**
 * 消息处理器装饰器
 */
export function messageHandler(eventType?: string, options?: MessageHandlerOptions) {
  return function(target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const finalEventType = eventType || propertyName;
    
    // 获取现有的消息处理器列表或创建新的
    const existingHandlers: MessageHandlerMetadata[] = 
      Reflect.getMetadata(MESSAGE_HANDLER_METADATA_KEY, target) || [];
    
    // 添加新的消息处理器元数据
    const handlerMetadata: MessageHandlerMetadata = {
      eventType: finalEventType,
      methodName: propertyName,
      description: options?.description
    };
    
    existingHandlers.push(handlerMetadata);
    
    // 设置元数据
    Reflect.defineMetadata(MESSAGE_HANDLER_METADATA_KEY, existingHandlers, target);
    
    logger.debug(`注册消息处理器: ${finalEventType} -> ${propertyName}`);
    
    return descriptor;
  };
}

/**
 * 群组事件处理器装饰器
 */
export function groupEventHandler(eventType?: string, options?: GroupEventHandlerOptions) {
  return function(target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const finalEventType = eventType || propertyName;
    
    // 获取现有的群组事件处理器列表或创建新的
    const existingHandlers: GroupEventHandlerMetadata[] = 
      Reflect.getMetadata(GROUP_EVENT_HANDLER_METADATA_KEY, target) || [];
    
    // 添加新的群组事件处理器元数据
    const handlerMetadata: GroupEventHandlerMetadata = {
      eventType: finalEventType,
      methodName: propertyName,
      description: options?.description
    };
    
    existingHandlers.push(handlerMetadata);
    
    // 设置元数据
    Reflect.defineMetadata(GROUP_EVENT_HANDLER_METADATA_KEY, existingHandlers, target);
    
    logger.debug(`注册群组事件处理器: ${finalEventType} -> ${propertyName}`);
    
    return descriptor;
  };
}

/**
 * 工具类：从类中提取装饰器元数据
 */
export class DecoratorMetadataExtractor {
  /**
   * 获取类的所有API元数据
   */
  public static getApiMetadata(target: any): ApiMetadata[] {
    return Reflect.getMetadata(API_METADATA_KEY, target.prototype) || [];
  }

  /**
   * 获取类的所有消息处理器元数据
   */
  public static getMessageHandlerMetadata(target: any): MessageHandlerMetadata[] {
    return Reflect.getMetadata(MESSAGE_HANDLER_METADATA_KEY, target.prototype) || [];
  }

  /**
   * 获取类的所有群组事件处理器元数据
   */
  public static getGroupEventHandlerMetadata(target: any): GroupEventHandlerMetadata[] {
    return Reflect.getMetadata(GROUP_EVENT_HANDLER_METADATA_KEY, target.prototype) || [];
  }

  /**
   * 检查方法是否有特定装饰器
   */
  public static hasApi(target: any, methodName: string): boolean {
    const apis = this.getApiMetadata(target);
    return apis.some(api => api.methodName === methodName);
  }

  public static hasMessageHandler(target: any, methodName: string): boolean {
    const handlers = this.getMessageHandlerMetadata(target);
    return handlers.some(handler => handler.methodName === methodName);
  }

  public static hasGroupEventHandler(target: any, methodName: string): boolean {
    const handlers = this.getGroupEventHandlerMetadata(target);
    return handlers.some(handler => handler.methodName === methodName);
  }
}