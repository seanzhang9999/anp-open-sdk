"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.register = register;
var simple_decorators_1 = require("@runtime/decorators/simple-decorators");
var type_safe_decorators_1 = require("@runtime/decorators/type-safe-decorators");
var handlers = require("./agent-handlers");
function register(agent, config) {
    console.log("\u6CE8\u518C ".concat(agent.name, " \u7684API\u5904\u7406\u5668..."));
    // 注册API处理器
    if (config.api) {
        for (var _i = 0, _a = config.api; _i < _a.length; _i++) {
            var apiConfig = _a[_i];
            var handler = handlers[apiConfig.handler];
            if (handler) {
                (0, simple_decorators_1.agentApi)(agent, apiConfig.path)(handler);
                console.log("  -> \u6CE8\u518CAPI: ".concat(apiConfig.path));
            }
        }
    }
    // 注册消息处理器
    if (config.message_handlers) {
        for (var _b = 0, _c = config.message_handlers; _b < _c.length; _b++) {
            var msgConfig = _c[_b];
            var handler = handlers[msgConfig.handler];
            if (handler) {
                type_safe_decorators_1.GlobalMessageManager.addHandler(msgConfig.type, handler);
                console.log("  -> \u6CE8\u518C\u6D88\u606F\u5904\u7406\u5668: ".concat(msgConfig.type));
            }
        }
    }
}
