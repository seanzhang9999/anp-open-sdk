from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.service.interaction.anp_tool import ANPTool, ANPToolCrawler
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator
import logging
import json
import re

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
    智能本地方法调用爬虫，通过智能分析本地方法列表来找到并调用指定方法
    
    Args:
        sdk: ANPSDK 实例
        target_method_name: 要查找和调用的方法名
        req_did: 请求方的 DID，如果不提供则使用默认值
    """
    logger.info(f"🚀 启动智能本地方法调用爬虫，目标方法: {target_method_name}")
    
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
        
        # 3. 构造方法信息列表
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
        
        logger.info("🤖 开始智能分析方法列表...")
        
        # 4. 使用智能匹配算法找到最佳方法
        best_match = await intelligent_method_matching(methods_info, target_method_name)
        
        if best_match:
            method_key = best_match["method_key"]
            reason = best_match["reason"]
            
            logger.info(f"✅ 智能匹配找到方法: {method_key}")
            logger.info(f"📝 选择原因: {reason}")
            
            # 5. 调用找到的方法
            logger.info(f"🎯 调用方法: {method_key}")
            
            # 根据方法名决定参数
            method_name = best_match.get("method_name", "")
            if any(keyword in method_name.lower() for keyword in ["calculate", "sum", "add"]):
                # 如果是计算方法，传入数字参数
                call_result = await local_caller.call_method_by_key(method_key, 15.5, 25.3)
            else:
                # 其他方法不传参数
                call_result = await local_caller.call_method_by_key(method_key)
            
            return {
                "success": True,
                "method_key": method_key,
                "reason": reason,
                "result": call_result,
                "method_info": best_match
            }
        else:
            logger.warning(f"❌ 智能匹配未找到合适的方法")
            # 降级到简单搜索
            return await fallback_method_search(local_caller, target_method_name)
            
    except Exception as e:
        logger.error(f"❌ 智能方法调用过程中出错: {e}")
        # 降级到简单搜索
        return await fallback_method_search(local_caller, target_method_name)


async def intelligent_method_matching(methods_info, target_method_name):
    """
    智能方法匹配算法
    
    Args:
        methods_info: 方法信息列表
        target_method_name: 目标方法名
    
    Returns:
        最佳匹配的方法信息，如果没有找到则返回 None
    """
    logger.info(f"🔍 智能匹配目标方法: {target_method_name}")
    
    # 候选方法列表，每个元素包含方法信息和匹配分数
    candidates = []
    
    for method_info in methods_info:
        method_name = method_info.get("method_name", "").lower()
        description = method_info.get("description", "").lower()
        tags = [tag.lower() for tag in method_info.get("tags", [])]
        
        target_lower = target_method_name.lower()
        
        # 计算匹配分数
        score = 0
        reasons = []
        
        # 1. 精确匹配方法名 (最高分)
        if method_name == target_lower:
            score += 100
            reasons.append("方法名完全匹配")
        
        # 2. 方法名包含目标关键词
        elif target_lower in method_name:
            score += 80
            reasons.append("方法名包含目标关键词")
        
        # 3. 目标关键词包含方法名
        elif method_name in target_lower:
            score += 70
            reasons.append("目标关键词包含方法名")
        
        # 4. 描述中包含目标关键词
        if target_lower in description:
            score += 30
            reasons.append("描述中包含目标关键词")
        
        # 5. 标签匹配
        for tag in tags:
            if target_lower in tag or tag in target_lower:
                score += 20
                reasons.append(f"标签匹配: {tag}")
        
        # 6. 模糊匹配 - 检查相似的关键词
        similarity_keywords = {
            "calculate": ["calc", "compute", "sum", "add", "math"],
            "sum": ["add", "plus", "total", "calculate"],
            "demo": ["test", "example", "sample"],
            "info": ["information", "detail", "data"],
            "hello": ["hi", "greeting", "welcome"]
        }
        
        for key, synonyms in similarity_keywords.items():
            if key in target_lower:
                for synonym in synonyms:
                    if synonym in method_name or synonym in description:
                        score += 15
                        reasons.append(f"同义词匹配: {synonym}")
        
        # 7. 特殊处理 - 如果目标是 calculate_sum，优先匹配包含 calculate 或 sum 的方法
        if "calculate" in target_lower and "sum" in target_lower:
            if "calculate" in method_name and "sum" in method_name:
                score += 50
                reasons.append("复合关键词完全匹配")
            elif "calculate" in method_name or "sum" in method_name:
                score += 25
                reasons.append("复合关键词部分匹配")
        
        if score > 0:
            candidates.append({
                "method_info": method_info,
                "score": score,
                "reasons": reasons
            })
            logger.info(f"  📊 {method_info['method_name']}: 分数={score}, 原因={reasons}")
    
    if not candidates:
        logger.warning("❌ 没有找到任何匹配的候选方法")
        return None
    
    # 按分数排序，选择最高分的方法
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best_candidate = candidates[0]
    
    # 如果最高分太低，认为没有合适的匹配
    if best_candidate["score"] < 15:
        logger.warning(f"❌ 最佳匹配分数太低: {best_candidate['score']}")
        return None
    
    # 构造返回结果
    best_method = best_candidate["method_info"]
    result = {
        "method_key": best_method["method_key"],
        "method_name": best_method["method_name"],
        "agent_name": best_method["agent_name"],
        "description": best_method["description"],
        "score": best_candidate["score"],
        "reason": f"智能匹配 (分数: {best_candidate['score']}) - " + "; ".join(best_candidate["reasons"])
    }
    
    logger.info(f"🎯 选择最佳匹配: {result['method_name']} (分数: {result['score']})")
    return result


async def fallback_method_search(local_caller: LocalMethodsCaller, target_method_name: str):
    """
    降级方法：当智能匹配失败时，使用简单的关键词搜索
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
        
        # 根据方法名决定参数
        method_name = selected_method.get("method_name", "")
        if any(keyword in method_name.lower() for keyword in ["calculate", "sum", "add"]):
            # 如果是计算方法，传入数字参数
            call_result = await local_caller.call_method_by_key(method_key, 12.5, 18.7)
        else:
            # 其他方法不传参数
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
