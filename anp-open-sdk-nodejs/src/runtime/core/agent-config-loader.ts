import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { createAgent, createSharedAgent } from '../decorators/type-safe-decorators';
import { ANPUser } from '@foundation/index';
import { getUserDataManager } from '@foundation/user';
import { getLogger } from '@foundation/index';

const logger = getLogger('AgentConfigLoader');

interface AgentConfig {
    name: string;
    did?: string;
    share_did?: {
        enabled: boolean;
        shared_did: string;
        path_prefix: string;
        primary_agent: boolean;
    };
    api?: Array<{
        path: string;
        method: string;
        handler: string;
        description?: string;
    }>;
    message_handlers?: Array<{
        type: string;
        handler: string;
    }>;
}

export class AgentConfigLoader {
    private configBasePath: string;

    constructor(configBasePath: string = '../data_user/localhost_9527/agents_config_nj') {
        this.configBasePath = configBasePath;
    }

    async loadAllAgents(): Promise<any[]> {
        const agents: any[] = [];

        if (!fs.existsSync(this.configBasePath)) {
            logger.warn(`配置目录不存在: ${this.configBasePath}`);
            return agents;
        }

        const agentDirs = fs.readdirSync(this.configBasePath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name);

        for (const agentDir of agentDirs) {
            try {
                const agent = await this.loadAgent(agentDir);
                if (agent) {
                    agents.push(agent);
                }
            } catch (error) {
                logger.error(`加载 agent ${agentDir} 失败:`, error);
            }
        }

        return agents;
    }

    private async loadAgent(agentDirName: string): Promise<any | null> {
        const agentPath = path.join(this.configBasePath, agentDirName);
        const mappingsPath = path.join(agentPath, 'agent-mappings.yaml');
        const registerPath = path.join(agentPath, 'agent-register.ts');

        // 检查必要文件是否存在
        if (!fs.existsSync(mappingsPath)) {
            logger.warn(`配置文件不存在: ${mappingsPath}`);
            return null;
        }

        // 加载配置
        const configContent = fs.readFileSync(mappingsPath, 'utf8');
        const config: AgentConfig = yaml.load(configContent) as AgentConfig;

        logger.debug(`加载 agent 配置: ${config.name}`);

        // 创建 agent
        let agent: any;

        if (config.share_did?.enabled) {
            // 共享 DID 模式
            const userDataManager = getUserDataManager();
            const userData = userDataManager.getUserData(config.share_did.shared_did);

            if (!userData) {
                throw new Error(`找不到用户数据: ${config.share_did.shared_did}`);
            }

            const anpUser = new ANPUser(userData);

            agent = await createSharedAgent({
                name: config.name,
                did: config.share_did.shared_did,
                prefix: config.share_did.path_prefix,
                primaryAgent: config.share_did.primary_agent
            });
        } else if (config.did) {
            // 独立 DID 模式
            const userDataManager = getUserDataManager();
            const userData = userDataManager.getUserData(config.did);

            if (!userData) {
                throw new Error(`找不到用户数据: ${config.did}`);
            }

            const anpUser = new ANPUser(userData);

            agent = await createAgent({
                name: config.name,
                shared: false,
                // 添加 did 属性来指定用户
                did: anpUser.id, // 或者根据你的需求设置适当的 DID
                // 如果需要的话，还可以添加其他选项：
                // prefix: config.prefix,
                // primaryAgent: config.primaryAgent
            });
        } else {
            throw new Error(`Agent ${config.name} 缺少 DID 配置`);
        }

        // 加载并执行注册函数
        if (fs.existsSync(registerPath)) {
            try {
                // 动态导入注册模块
                const registerModule = await import(path.resolve(registerPath));
                if (registerModule.register) {
                    registerModule.register(agent, config);
                    logger.debug(`✅ ${config.name} 注册完成`);
                }
            } catch (error) {
                logger.error(`注册 ${config.name} 失败:`, error);
            }
        }

        return agent;
    }
}