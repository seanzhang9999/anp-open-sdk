from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.service.interaction.anp_tool import ANPTool
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller


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
