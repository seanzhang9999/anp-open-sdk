import { Request, Response } from 'express';

export async function addHandler(requestData: any, request: Request): Promise<any> {
    const params = requestData.body?.params || requestData.params || requestData.body || {};
    const a = params.a || 0;
    const b = params.b || 0;
    const result = a + b;

    return {
        result,
        operation: "add",
        inputs: [a, b],
        agent: "Calculator Agent JS"
    };
}

export async function multiplyHandler(requestData: any, request: Request): Promise<any> {
    const params = requestData.body?.params || requestData.params || requestData.body || {};
    const a = params.a || 1;
    const b = params.b || 1;
    const result = a * b;

    return {
        result,
        operation: "multiply",
        inputs: [a, b],
        agent: "Calculator Agent JS"
    };
}

export async function handleTextMessage(msgData: any): Promise<any> {
    const content = msgData.content || '';
    return {
        reply: `Calculator Agent JS 收到消息: ${content}`
    };
}