## python测试方法
### 1. 配置文件
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的 `OPENAI_API_KEY`、`OPENAI_API_MODEL_NAME` 和 `OPENAI_API_BASE_URL`。

### 2. 安装依赖

建议使用 Python 虚拟环境管理依赖：

```bash
python -m venv .venv
source .venv/bin/activate 
poetry install
```

### 3. 运行 SDK 测试和 Demo

运行工具和 Demo，验证核心 SDK 是否安装并能正常工作：

```bash
 PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python  python scripts/agent_user_binding.py

 PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python  python examples/flow_anp_agent/flow_anp_agent.py

```


## nodejs测试方法

### 运行所有测试
```bash
# 进入项目目录
cd anp-open-sdk-nodejs

# 安装依赖
npm install

# 运行所有测试
npm test

# 运行样例代码
npx ts-node examples/flow-anp-agent.ts
```
