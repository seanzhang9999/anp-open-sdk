import os
import yaml
from openai import AsyncOpenAI
from anp_open_sdk.anp_sdk_agent import LocalAgent

# --- Module-level variable，Represent thisAgentStatus of the instance ---
# These variables are created when the module is loaded.，And throughout the entire lifecycle of the application
my_agent_instance = None
my_llm_client = None


async def initialize_agent(agent, sdk_instance):
    """
    Initialization hook，The plugin is now responsible for its own creation and configuration.AgentExample。
    It no longer accepts parameters.，Return the created one instead.agentExample。
    """
    global my_agent_instance, my_llm_client

    print(f"  -> Self-initializing LLM Agent from its own module...")


    # 1. Use the incoming agent Example
    my_agent_instance = agent

    # __file__ It is the current file path.
    config_path = os.path.join(os.path.dirname(__file__), "agent_mappings.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    my_agent_instance.name = cfg["name"]
    print(f"  -> Self-created agent instance: {my_agent_instance.name}")

    # 3. Create and storeLLMClient as a module-level variable
    api_key = os.getenv("OPENAI_API_KEY", "your_default_key_if_not_set")
    base_url = os.getenv("OPENAI_BASE_URL")
    my_llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    print(f"  -> Self-created LLM client.")

    # 4. Register your own.API
    # Attention：Now, the method of the instance is directly called within the module.
    my_agent_instance.expose_api("/llm/chat", chat_completion, methods=["POST"])
    print(f"  -> Self-registered '/llm/chat' ability.")

    # 5. Create and configureagentInstance returned to the loader.
    return my_agent_instance


async def cleanup_agent():
    """
    Cleanup hook，Now, module-level variables are being used directly.。
    """
    global my_llm_client
    if my_llm_client:
        print(f"  -> Self-cleaning LLM Agent: Closing client...")
        await my_llm_client.close()
        print(f"  -> LLM client cleaned up.")


async def chat_completion(prompt: str ):
    """
    APIProcessing function，Now directly use the module's internal functions. my_llm_client。
    It no longer needs to be fromrequestObtain from ChinaagentExample。
    """
    global my_llm_client
    if not prompt:
        return {"error": "Prompt is required."}
    if not my_llm_client:
        return {"error": "LLM client is not initialized in this module."}
    try:
        print(f"  -> LLM Agent Module: Sending prompt to model...")
        response = await my_llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        message_content = response.choices[0].message.content
        return {"response": message_content}
    except Exception as e:
        print(f"  -> ❌ LLM Agent Module Error: {e}")
        return {"error": f"An error occurred: {str(e)}"}