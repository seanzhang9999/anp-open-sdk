#!/usr/bin/env python3
"""
测试500错误修复的脚本
"""

import asyncio
import aiohttp
import json

async def test_calculator_api():
    """测试Calculator Agent的API调用"""
    url = "http://localhost:9527/agent/api/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A28cddee0fade0258/calculator/add"
    
    payload = {
        "a": 2.88888,
        "b": 999933.4445556
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试直接调用（不带认证）
            async with session.post(url, json=payload) as response:
                status = response.status
                try:
                    body = await response.json()
                except:
                    body = await response.text()
                
                print(f"🧪 直接调用测试:")
                print(f"   状态码: {status}")
                print(f"   响应: {body}")
                
                return status == 200
                
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

async def test_publisher_agents():
    """测试获取agent列表"""
    url = "http://localhost:9527/publisher/agents"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                status = response.status
                body = await response.json()
                
                print(f"🧪 获取agent列表测试:")
                print(f"   状态码: {status}")
                print(f"   智能体数量: {len(body) if isinstance(body, list) else 'unknown'}")
                
                return status == 200
                
    except Exception as e:
        print(f"❌ 获取agent列表失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 测试500错误修复")
    print("=" * 50)
    
    async def run_tests():
        # 先检查服务器是否运行
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                async with session.get("http://localhost:9527/publisher/agents") as response:
                    if response.status != 200:
                        print("❌ 服务器未运行或无法访问")
                        return
        except:
            print("❌ 服务器未运行，请先启动:")
            print("   cd demo_anp_open_sdk_framework && python framework_demo.py")
            return
        
        print("✅ 服务器已运行")
        
        # 运行测试
        test1 = await test_publisher_agents()
        test2 = await test_calculator_api()
        
        print("\n" + "=" * 50)
        if test1 and test2:
            print("🎉 所有测试通过!")
        else:
            print("❌ 部分测试失败")
    
    asyncio.run(run_tests())