from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.service.interaction.anp_tool import ANPTool, ANPToolCrawler
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator
import logging
import json

logger = logging.getLogger(__name__)


async def run_local_method_crawler(sdk: ANPSDK):
    """
    一个爬虫，用于演示通过 anp_tool 调用本地方法。
    """
    # 获取 agent_002 的 DID
    # 在实际场景中，这个 DID 会从配置或服务发现中获取
    # 这里我们为了演示，直接使用一个已知的 DID
    agent_002_did = "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211"

    # 创建 LocalMethodsCaller 实例
    local_caller = LocalMethodsCaller(sdk)

    # 创建 ANPTool 并注入 local_caller
    anp_tool = ANPTool(local_caller=local_caller)

    # 构造本地调用 URI
    local_uri = f"local://{agent_002_did}/demo_method"

    print(f"--- Crawler: 准备通过 anp_tool 调用本地方法 ---")
    print(f"Target URI: {local_uri}")

    # 使用 anp_tool 执行本地调用
    result = await anp_tool.execute(url=local_uri)

    print(f"--- Crawler: 调用完成 ---")
    print(f"Status Code: {result.get('status_code')}")
    print(f"Source: {result.get('source')}")
    print(f"Data: {result.get('data')}")

    return result


async def run_intelligent_local_method_crawler(sdk: ANPSDK, target_method_name: str = "demo_method", req_did: str = None):
    """
    智能本地方法调用爬虫，通过 LLM 分析本地方法列表来找到并调用指定方法
    
    Args:
        sdk: ANPSDK 实例
        target_method_name: 要查找和调用的方法名
        req_did: 请求方的 DID，如果不提供则使用默认值
    """
    logger.info(f"🚀 启动智能本地方法调用爬虫，目标方法: {target_method_name}")
    
    # 设置默认的请求方 DID（可以是 orchestrator_agent 的 DID）
    if not req_did:
        req_did = "did:wba:localhost%3A9527:wba:user:orchestrator"  # 根据实际情况调整
    
    try:
        # 1. 创建 LocalMethodsCaller 实例
        local_caller = LocalMethodsCaller(sdk)
        
        # 2. 获取所有可用的本地方法
        logger.info("📋 获取所有可用的本地方法...")
        all_methods = local_caller.list_all_methods()
        
        if not all_methods:
            logger.warning("⚠️ 未找到任何本地方法")
            return {"error": "未找到任何本地方法"}
        
        logger.info(f"📊 找到 {len(all_methods)} 个本地方法")
        
        # 3. 创建 ANPToolCrawler 进行智能分析
        crawler = ANPToolCrawler()
        
        # 4. 构造任务描述，包含方法列表和目标方法名
        methods_info = []
        for method_key, method_data in all_methods.items():
            methods_info.append({
                "method_key": method_key,
                "agent_name": method_data.get("agent_name", "unknown"),
                "method_name": method_data.get("name", "unknown"),
                "description": method_data.get("description", ""),
                "tags": method_data.get("tags", []),
                "is_async": method_data.get("is_async", False)
            })
        
        task_description = f"""
我需要找到并调用名为 '{target_method_name}' 的本地方法。

可用的本地方法列表：
{json.dumps(methods_info, indent=2, ensure_ascii=False)}

请分析这些方法，找到最匹配 '{target_method_name}' 的方法，并返回该方法的 method_key。
如果找到多个匹配的方法，请选择最相关的一个。
如果没有找到匹配的方法，请说明原因。

请以 JSON 格式返回结果：
{{
    "found": true/false,
    "method_key": "找到的方法键",
    "reason": "选择原因或未找到的原因"
}}
"""
        
        logger.info("🤖 通过 LLM 分析方法列表...")
        
        # 5. 使用智能爬虫进行分析（这里使用一个虚拟的目标 DID，主要是为了触发 LLM 分析）
        analysis_result = await crawler.run_crawler_demo(
            req_did=req_did,
            resp_did="did:wba:localhost%3A9527:wba:user:analysis_target",  # 虚拟目标
            task_input=task_description,
            initial_url="http://localhost:9527/publisher/agents",  # 起始 URL
            use_two_way_auth=True,
            task_type="method_analysis"
        )
        
        logger.info(f"🧠 LLM 分析结果: {analysis_result}")
        
        # 6. 解析 LLM 的分析结果
        try:
            if isinstance(analysis_result, str):
                analysis_data = json.loads(analysis_result)
            else:
                analysis_data = analysis_result
            
            if analysis_data.get("found", False):
                method_key = analysis_data.get("method_key")
                reason = analysis_data.get("reason", "")
                
                logger.info(f"✅ LLM 找到匹配方法: {method_key}")
                logger.info(f"📝 选择原因: {reason}")
                
                # 7. 调用找到的方法
                logger.info(f"🎯 调用方法: {method_key}")
                call_result = await local_caller.call_method_by_key(method_key)
                
                return {
                    "success": True,
                    "method_key": method_key,
                    "reason": reason,
                    "result": call_result
                }
            else:
                reason = analysis_data.get("reason", "未知原因")
                logger.warning(f"❌ LLM 未找到匹配方法: {reason}")
                return {
                    "success": False,
                    "reason": reason
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ 解析 LLM 结果失败: {e}")
            # 如果 LLM 返回的不是标准 JSON，尝试直接搜索方法
            return await fallback_method_search(local_caller, target_method_name)
            
    except Exception as e:
        logger.error(f"❌ 智能方法调用过程中出错: {e}")
        # 降级到简单搜索
        return await fallback_method_search(local_caller, target_method_name)


async def fallback_method_search(local_caller: LocalMethodsCaller, target_method_name: str):
    """
    降级方法：当 LLM 分析失败时，使用简单的关键词搜索
    """
    logger.info(f"🔄 降级到简单搜索模式，搜索关键词: {target_method_name}")
    
    try:
        # 使用 LocalMethodsDocGenerator 进行搜索
        doc_generator = LocalMethodsDocGenerator()
        search_results = doc_generator.search_methods(keyword=target_method_name)
        
        if not search_results:
            return {
                "success": False,
                "reason": f"未找到包含关键词 '{target_method_name}' 的方法"
            }
        
        if len(search_results) > 1:
            method_list = [f"{r['agent_name']}.{r['method_name']}" for r in search_results]
            logger.warning(f"⚠️ 找到多个匹配方法: {method_list}，选择第一个")
        
        # 选择第一个匹配的方法
        selected_method = search_results[0]
        method_key = selected_method["method_key"]
        
        logger.info(f"🎯 调用方法: {method_key}")
        call_result = await local_caller.call_method_by_key(method_key)
        
        return {
            "success": True,
            "method_key": method_key,
            "reason": f"通过关键词搜索找到方法",
            "result": call_result,
            "search_results": search_results
        }
        
    except Exception as e:
        logger.error(f"❌ 降级搜索也失败了: {e}")
        return {
            "success": False,
            "reason": f"搜索失败: {str(e)}"
        }


async def demo_intelligent_crawler():
    """
    演示智能爬虫的使用
    """
    # 这里需要一个 SDK 实例，在实际使用中会从外部传入
    # sdk = ANPSDK(...)  # 根据实际情况初始化
    
    print("🎭 智能本地方法调用爬虫演示")
    print("=" * 50)
    
    # 演示调用不同的方法
    test_methods = ["demo_method", "calculate_sum", "info_method"]
    
    for method_name in test_methods:
        print(f"\n🔍 测试调用方法: {method_name}")
        print("-" * 30)
        
        # result = await run_intelligent_local_method_crawler(sdk, method_name)
        # print(f"结果: {result}")
        
        # 这里只是演示结构，实际运行需要 SDK 实例
        print(f"[演示] 将会智能搜索并调用 {method_name}")
