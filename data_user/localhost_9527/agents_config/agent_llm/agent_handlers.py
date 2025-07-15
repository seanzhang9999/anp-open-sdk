import os
import yaml
from openai import AsyncOpenAI
from anp_sdk.anp_user import ANPUser
from anp_sdk.config import get_global_config

# --- 模块级变量，代表这个Agent实例的状态 ---
# 这些变量在模块被加载时创建，并贯穿整个应用的生命周期
my_agent_instance = None
my_llm_client = None


async def initialize_agent(agent):
    """
    初始化钩子，现在由插件自己负责创建和配置Agent实例。
    它不再接收参数，而是返回创建好的agent实例。
    """
    global my_agent_instance, my_llm_client

    print(f"  -> Self-initializing LLM Agent from its own module...")


    # 1. 使用传入的 agent 实例
    my_agent_instance = agent

    # __file__ 是当前文件的路径
    config_path = os.path.join(os.path.dirname(__file__), "agent_mappings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    my_agent_instance.name = cfg["name"]
    print(f"  -> Self-created agent instance: {my_agent_instance.name}")

    # 3. 创建并存储LLM客户端作为模块级变量
    config = get_global_config()
    api_key = config.secrets.openai_api_key
    base_url = config.llm.api_url

    my_llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    print(f"  -> Self-created LLM client.")

    # 4. 将创建和配置好的agent实例返回给加载器
    # 注意：API注册现在由独立的agent_register.py处理
    return my_agent_instance


async def cleanup_agent():
    """
    清理钩子，现在也直接使用模块级变量。
    """
    global my_llm_client
    if my_llm_client:
        print(f"  -> Self-cleaning LLM Agent: Closing client...")
        await my_llm_client.close()
        print(f"  -> LLM client cleaned up.")


async def chat_completion(request_data, request):
    """
    API处理函数，现在直接使用模块内的 my_llm_client。
    它不再需要从request中获取agent实例。
    """
    global my_llm_client
    
    print(f"  -> LLM Agent API调用，接收到的request_data: {request_data}")
    
    # 从request_data中提取消息内容 - 支持多种格式
    message = None
    
    # 尝试多种可能的参数格式
    if isinstance(request_data, dict):
        # 格式1: {"params": {"message": "..."}}
        if 'params' in request_data and isinstance(request_data['params'], dict):
            message = request_data['params'].get('message')
        # 格式2: {"message": "..."}
        elif 'message' in request_data:
            message = request_data['message']
        # 格式3: {"content": "..."}
        elif 'content' in request_data:
            message = request_data['content']
        # 格式4: 直接从请求体中获取
        else:
            # 尝试从FastAPI请求中获取JSON数据
            try:
                if hasattr(request, 'json'):
                    body_data = await request.json()
                    message = body_data.get('message') or body_data.get('content')
                    print(f"  -> 从请求体获取消息: {message}")
            except Exception as e:
                print(f"  -> 无法解析请求体: {e}")
    
    if not message:
        error_msg = f"Message is required. Received request_data: {request_data}"
        print(f"  -> ❌ {error_msg}")
        return {"error": error_msg}
    
    if not my_llm_client:
        return {"error": "LLM client is not initialized in this module."}
    
    try:
        print(f"  -> LLM Agent Module: Sending message to model: {message}")
        response = await my_llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            temperature=0.0
        )
        message_content = response.choices[0].message.content
        print(f"  -> LLM Agent Module: Got response: {message_content}")
        return {"response": message_content}
    except Exception as e:
        print(f"  -> ❌ LLM Agent Module Error: {e}")
        return {"error": f"An error occurred: {str(e)}"}


# 新增：消息处理器
async def handle_message(msg):
    """
    通用消息处理器，处理所有类型的消息
    """
    global my_llm_client
    
    print(f"  -> LLM Agent收到消息: {msg}")
    
    # 提取消息内容
    content = msg.get('content', '')
    message_type = msg.get('message_type', 'text')
    
    if not content:
        return {"reply": "LLM Agent: 消息内容为空"}
    
    if not my_llm_client:
        return {"reply": "LLM Agent: LLM客户端未初始化"}
    
    try:
        print(f"  -> LLM Agent: 处理{message_type}类型消息: {content}")
        response = await my_llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": content}],
            temperature=0.0
        )
        message_content = response.choices[0].message.content
        print(f"  -> LLM Agent: 生成回复: {message_content}")
        return {"reply": f"LLM Agent回复: {message_content}"}
    except Exception as e:
        print(f"  -> ❌ LLM Agent消息处理错误: {e}")
        return {"reply": f"LLM Agent: 处理消息时出错: {str(e)}"}


async def handle_text_message(msg):
    """
    专门处理text类型消息的处理器
    """
    global my_llm_client
    
    print(f"  -> LLM Agent收到text消息: {msg}")
    
    # 提取消息内容
    content = msg.get('content', '')
    
    if not content:
        return {"reply": "LLM Agent: text消息内容为空"}
    
    if not my_llm_client:
        return {"reply": "LLM Agent: LLM客户端未初始化"}
    
    try:
        print(f"  -> LLM Agent: 处理text消息: {content}")
        response = await my_llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"请简洁回复: {content}"}],
            temperature=0.0
        )
        message_content = response.choices[0].message.content
        print(f"  -> LLM Agent: 生成text回复: {message_content}")
        return {"reply": f"LLM Agent(text): {message_content}"}
    except Exception as e:
        print(f"  -> ❌ LLM Agent text消息处理错误: {e}")
        return {"reply": f"LLM Agent: 处理text消息时出错: {str(e)}"}
