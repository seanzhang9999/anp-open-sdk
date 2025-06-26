# anp_open_sdk/agents_config/orchestrator_agent/agent_handlers.py

import httpx  # Installation required httpx: pip install httpx
import json

from anp_open_sdk.service.interaction.agent_api_call import agent_api_call_get
from anp_open_sdk.service.interaction.anp_tool import ANPToolCrawler
import logging
logger = logging.getLogger(__name__)
from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.anp_sdk_agent import LocalAgent
from anp_open_sdk.auth.auth_client import agent_auth_request
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator

# Create an invoker during initialization.
caller = None
# --- Module-level variable ---
my_agent_instance = None

async def initialize_agent(agent, sdk_instance):
    """
    Initialization hook，Create and configureAgentExample，And attach special abilities.。
    """
    global my_agent_instance,caller
    logger.debug(f" -> Self-initializing Orchestrator Agent from its own module...")

    my_agent_instance = agent
    caller = LocalMethodsCaller(sdk_instance)

    # Key steps：Dynamically attach functions as methods to the created object. Agent In practice
    agent.discover_and_describe_agents = discover_and_describe_agents
    agent.run_calculator_add_demo = run_calculator_add_demo
    agent.run_hello_demo = run_hello_demo
    agent.run_ai_crawler_demo = run_ai_crawler_demo
    agent.run_ai_root_crawler_demo = run_ai_root_crawler_demo
    agent.run_agent_002_demo = run_agent_002_demo
    agent.run_agent_002_demo_new = run_agent_002_demo_new
    logger.debug(f" -> Attached capability to loading side.")

    return my_agent_instance

async def discover_and_describe_agents(publisher_url):
    """
    Discover and obtain all published items.AgentDetailed description。
    This function will be attached to Agent Instance as a method。
    """
    logger.debug("\n🕵️  Starting agent discovery process (from agent method)...")



    async with httpx.AsyncClient() as client:
        try:
            # 1. Visit  Obtain publicly available agent List
            logger.debug("  - Step 1: Fetching public agent list...")
            response = await client.get(publisher_url)
            response.raise_for_status()
            data = response.json()
            agents = data.get("agents", [])
            logger.info(f"  - Found {len(agents)} public agents.")
            logger.info(f"\n  - {data}")
            for agent_info in agents:
                did = agent_info.get("did")
                if not did:
                    continue

                logger.debug(f"\n  🔎 Processing Agent DID: {did}")

                # 2. Obtain each agent Of DID Document
                user_id = did.split(":")[-1]
                host , port = ANPSDK.get_did_host_port_from_did(user_id)
                did_doc_url = f"http://{host}:{port}/wba/user/{user_id}/did.json"

                logger.debug(f"    - Step 2: Fetching DID Document from {did_doc_url}")
                status, did_doc_data, msg, success = await agent_auth_request(
                    caller_agent=my_agent_instance.id,  # Use self.id As the caller
                    target_agent=did,
                    request_url=did_doc_url
                )

                if not success:
                    logger.debug(f"    - ❌ Failed to get DID Document for {did}. Message: {msg}")
                    continue

                if isinstance(did_doc_data, str):
                    did_document = json.loads(did_doc_data)
                else:
                    did_document = did_doc_data

                # 3. From DID Document Extraction from the middle ad.json Address and retrieve content.
                ad_endpoint = None
                for service in did_document.get("service", []):
                    if service.get("type") == "AgentDescription":
                        ad_endpoint = service.get("serviceEndpoint")
                        logger.info(f"\n   - ✅ get endpoint from did-doc{did}:{ad_endpoint}")
                        break

                if not ad_endpoint:
                    logger.debug(f"    - ⚠️  No 'AgentDescription' service found in DID Document for {did}.")
                    continue

                logger.debug(f"    - Step 3: Fetching Agent Description from {ad_endpoint}")
                status, ad_data, msg, success = await agent_auth_request(
                    caller_agent=my_agent_instance.id,
                    target_agent=did,
                    request_url=ad_endpoint
                )

                if success:
                    if isinstance(ad_data, str):
                        agent_description = json.loads(ad_data)
                    else:
                        agent_description = ad_data
                    logger.info(f"Agent Description:{ad_data}")
                    logger.debug("    - ✅ Successfully fetched Agent Description:")
                    logger.debug(json.dumps(agent_description, indent=2, ensure_ascii=False))
                else:
                    logger.debug(
                        f"    - ❌ Failed to get Agent Description from {ad_endpoint}. Status: {status}")

        except httpx.RequestError as e:
            logger.debug(f"  - ❌ Discovery process failed due to a network error: {e}")
        except Exception as e:
            logger.debug(f"  - ❌ An unexpected error occurred during discovery: {e}")




async def run_calculator_add_demo():

    caculator_did = "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"
    calculator_agent = LocalAgent.from_did(caculator_did)
    # Construction JSON-RPC Request parameters
    params = {
        "a": 1.23,
        "b": 4.56
    }

    result = await agent_api_call_get(
    my_agent_instance.id, calculator_agent.id, "/calculator/add", params  )

    logger.info(f"CalculationapiInvocation result: {result}")
    return result


async def run_hello_demo():
    target_did = "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211"
    target_agent = LocalAgent.from_did(target_did)
    # Construction JSON-RPC Request parameters
    params = {
        "message": "hello"
    }

    result = await agent_api_call_get(
    my_agent_instance.id, target_agent.id, "/hello", params  )

    logger.info(f"hello apiInvocation result: {result}")
    return result


async def run_ai_crawler_demo():

    target_did= "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"


    crawler = ANPToolCrawler()

    # Collaborative agents request services from the assembled agents through web crawlers.
    task_description = "I need to calculate the sum of two floating-point numbers. 2.88888+999933.4445556"

    host,port = ANPSDK.get_did_host_port_from_did(target_did)
    try:
        result = await crawler.run_crawler_demo(
            req_did=my_agent_instance.id,  # The requester is a collaborative agent.
            resp_did=target_did,  # The goal is the assembled agent.
            task_input=task_description,
            initial_url=f"http://{host}:{port}/wba/user/{target_did}/ad.json",
            use_two_way_auth=True,  # Use two-factor authentication.
            task_type = "function_query"
        )
        logger.debug(f"Intelligent Invocation Results: {result}")
        return

    except Exception as e:
        logger.info(f"Error occurred during intelligent invocation.: {e}")
        return



async def run_ai_root_crawler_demo():

    target_did= "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"


    crawler = ANPToolCrawler()

    # Collaborative agents request services from the assembled agents through web crawlers.
    task_description = "I need to calculate the sum of two floating-point numbers. 2.88888+999933.4445556"

    host,port = ANPSDK.get_did_host_port_from_did(target_did)
    try:
        result = await crawler.run_crawler_demo(
            req_did=my_agent_instance.id,
            resp_did=target_did,
            task_input=task_description,
            initial_url="http://localhost:9527/publisher/agents",
            use_two_way_auth=True,  # Use two-factor authentication.
            task_type = "root_query"
        )
        logger.debug(f"Intelligent Exploration Results: {result}")
        return

    except Exception as e:
        logger.info(f"Error occurred during intelligent exploration.: {e}")
        return



async def run_agent_002_demo(sdk, **kwargs):
    """Invoke agent_002 Custom demonstration method above"""
    try:
        # Through sdk Acquire agent_002 Example
        target_agent = sdk.get_agent("did:wba:localhost%3A9527:wba:user:5fea49e183c6c211")
        if not target_agent:
            return "Error：Not found agent_002"

        # Invoke agent_002 Methods above
        if hasattr(target_agent, 'demo_method') and callable(target_agent.demo_method):
            result = target_agent.demo_method()
            return result
        else:
            return "Error：In agent_002 Not found above. demo_method"
            
    except Exception as e:
        logger.error(f"Invoke agent_002.demo_method Failure: {e}")
        return f"Invoke agent_002.demo_method Occasionally make mistakes.: {e}"


async def run_agent_002_demo_new():
    """Invoke through search agent_002 Demonstration method"""
    try:
        # Method1：Invoke through keyword search.
        result = await caller.call_method_by_search("demo_method")
        logger.info(f"Search call results: {result}")

        # Method2：Directly invoke through the method key.
        result2 = await caller.call_method_by_key(
            "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211::calculate_sum",
            10.5, 20.3
        )
        logger.info(f"Directly call the result.: {result2}")

        return result

    except Exception as e:
        logger.error(f"Call failed: {e}")
        return f"Error occurred during invocation.: {e}"


async def search_available_methods(keyword: str = ""):
    """Search for available local methods."""
    results = LocalMethodsDocGenerator.search_methods(keyword=keyword)
    for result in results:
        print(f"🔍 {result['agent_name']}.{result['method_name']}: {result['description']}")
    return results


async def cleanup_agent():
    """
    Cleanup hook。
    """
    global my_agent_instance
    if my_agent_instance:
        logger.debug(f" -> Self-cleaning Orchestrator Agent: {my_agent_instance.name}")
        my_agent_instance = None
    logger.debug(f" -> Orchestrator Agent cleaned up.")