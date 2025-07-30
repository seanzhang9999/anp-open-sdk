import { agentApi } from '@runtime/decorators/simple-decorators';
import { GlobalMessageManager } from '@runtime/decorators/type-safe-decorators';
import * as handlers from './agent-handlers';

export function register(agent: any, config: any): void {
    console.log(`注册 ${agent.name} 的API处理器...`);

    // 注册API处理器
    if (config.api) {
        for (const apiConfig of config.api) {
            const handler = handlers[apiConfig.handler as keyof typeof handlers];
            if (handler) {
                agentApi(agent, apiConfig.path)(handler);
                console.log(`  -> 注册API: ${apiConfig.path}`);
            }
        }
    }

    // 注册消息处理器
    if (config.message_handlers) {
        for (const msgConfig of config.message_handlers) {
            const handler = handlers[msgConfig.handler as keyof typeof handlers];
            if (handler) {
                GlobalMessageManager.addHandler(msgConfig.type, handler);
                console.log(`  -> 注册消息处理器: ${msgConfig.type}`);
            }
        }
    }
}