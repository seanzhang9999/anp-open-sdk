"""
自定义记忆MCP工具测试
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from anp_runtime.local_service.memory.custom_memory_mcp_tools import (
    CustomMemoryMCPTools,
    get_custom_memory_mcp_tools,
    set_custom_memory_mcp_tools
)
from anp_runtime.local_service.memory.custom_memory_manager import CustomMemoryManager


class TestCustomMemoryMCPTools:
    """测试CustomMemoryMCPTools类"""
    
    @pytest.fixture
    async def mcp_tools(self):
        """创建测试用的MCP工具"""
        manager = CustomMemoryManager()
        return CustomMemoryMCPTools(manager)
    
    async def test_create_memory_template(self, mcp_tools):
        """测试创建记忆模板MCP工具"""
        schema_definition = {
            "fields": {
                "title": {"type": "str", "description": "标题"},
                "content": {"type": "str", "description": "内容"},
                "priority": {"type": "int", "description": "优先级", "min": 1, "max": 5}
            },
            "required_fields": ["title", "content"],
            "description": "测试模式"
        }
        
        result = await mcp_tools.create_memory_template(
            name="test_template",
            schema_definition=schema_definition,
            description="测试模板",
            default_tags=["test"],
            default_keywords=["测试"]
        )
        
        assert result["success"] is True
        assert result["template_id"] is not None
        assert "创建成功" in result["message"]
    
    async def test_create_memory_template_error(self, mcp_tools):
        """测试创建模板时出错"""
        # 模拟一个会导致错误的情况（传入None作为schema_definition）
        result = await mcp_tools.create_memory_template(
            name="invalid_template",
            schema_definition=None
        )
        
        assert result["success"] is False
        assert result["template_id"] is None
        assert "失败" in result["message"]
    
    async def test_create_custom_memory(self, mcp_tools):
        """测试创建自定义记忆MCP工具"""
        # 先创建模板
        schema_definition = {
            "fields": {
                "title": {"type": "str"},
                "content": {"type": "str"}
            },
            "required_fields": ["title", "content"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="memory_test_template",
            schema_definition=schema_definition
        )
        template_id = template_result["template_id"]
        
        # 创建记忆
        content = {
            "title": "测试记忆",
            "content": "这是一个测试记忆的内容"
        }
        
        result = await mcp_tools.create_custom_memory(
            template_id=template_id,
            content=content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent",
            title="MCP测试记忆",
            tags=["mcp_test"],
            keywords=["MCP", "测试"]
        )
        
        assert result["success"] is True
        assert result["memory_id"] is not None
        assert "创建成功" in result["message"]
    
    async def test_create_custom_memory_validation_error(self, mcp_tools):
        """测试创建记忆时验证失败"""
        # 先创建模板
        schema_definition = {
            "fields": {"title": {"type": "str"}},
            "required_fields": ["title"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="validation_test_template",
            schema_definition=schema_definition
        )
        template_id = template_result["template_id"]
        
        # 创建无效内容的记忆
        invalid_content = {"description": "缺少title字段"}
        
        result = await mcp_tools.create_custom_memory(
            template_id=template_id,
            content=invalid_content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert result["success"] is False
        assert result["memory_id"] is None
        assert "验证失败" in result["message"]
    
    async def test_get_custom_memory(self, mcp_tools):
        """测试获取自定义记忆MCP工具"""
        # 先创建模板和记忆
        schema_definition = {
            "fields": {"data": {"type": "str"}},
            "required_fields": ["data"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="get_test_template",
            schema_definition=schema_definition
        )
        
        memory_result = await mcp_tools.create_custom_memory(
            template_id=template_result["template_id"],
            content={"data": "测试数据"},
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        memory_id = memory_result["memory_id"]
        
        # 获取记忆
        result = await mcp_tools.get_custom_memory(memory_id)
        
        assert result["success"] is True
        assert result["memory"] is not None
        assert result["memory"]["id"] == memory_id
        assert "成功" in result["message"]
        
        # 获取不存在的记忆
        result = await mcp_tools.get_custom_memory("nonexistent_id")
        assert result["success"] is False
        assert result["memory"] is None
        assert "未找到" in result["message"]
    
    async def test_update_custom_memory(self, mcp_tools):
        """测试更新自定义记忆MCP工具"""
        # 先创建模板和记忆
        schema_definition = {
            "fields": {
                "title": {"type": "str"},
                "content": {"type": "str"}
            },
            "required_fields": ["title", "content"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="update_test_template",
            schema_definition=schema_definition
        )
        
        memory_result = await mcp_tools.create_custom_memory(
            template_id=template_result["template_id"],
            content={"title": "原始标题", "content": "原始内容"},
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        memory_id = memory_result["memory_id"]
        
        # 更新记忆
        result = await mcp_tools.update_custom_memory(
            memory_id=memory_id,
            content={"title": "更新标题", "content": "更新内容"},
            title="新标题",
            tags=["updated"],
            keywords=["更新"]
        )
        
        assert result["success"] is True
        assert "更新成功" in result["message"]
        
        # 验证更新
        get_result = await mcp_tools.get_custom_memory(memory_id)
        updated_memory = get_result["memory"]
        assert updated_memory["title"] == "新标题"
        assert updated_memory["content"]["custom_data"]["title"] == "更新标题"
    
    async def test_delete_custom_memory(self, mcp_tools):
        """测试删除自定义记忆MCP工具"""
        # 先创建模板和记忆
        schema_definition = {
            "fields": {"data": {"type": "str"}},
            "required_fields": ["data"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="delete_test_template",
            schema_definition=schema_definition
        )
        
        memory_result = await mcp_tools.create_custom_memory(
            template_id=template_result["template_id"],
            content={"data": "要删除的数据"},
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        memory_id = memory_result["memory_id"]
        
        # 删除记忆
        result = await mcp_tools.delete_custom_memory(memory_id)
        
        assert result["success"] is True
        assert "删除成功" in result["message"]
        
        # 验证删除
        get_result = await mcp_tools.get_custom_memory(memory_id)
        assert get_result["success"] is False
        assert get_result["memory"] is None
    
    async def test_search_custom_memories(self, mcp_tools):
        """测试搜索自定义记忆MCP工具"""
        # 先创建模板和多个记忆
        schema_definition = {
            "fields": {
                "title": {"type": "str"},
                "category": {"type": "str"}
            },
            "required_fields": ["title", "category"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="search_test_template",
            schema_definition=schema_definition
        )
        template_id = template_result["template_id"]
        
        # 创建多个记忆
        test_data = [
            {"title": "搜索测试1", "category": "测试"},
            {"title": "搜索测试2", "category": "测试"},
            {"title": "其他内容", "category": "其他"}
        ]
        
        for data in test_data:
            await mcp_tools.create_custom_memory(
                template_id=template_id,
                content=data,
                source_agent_did="did:anp:test_agent",
                source_agent_name="TestAgent"
            )
        
        # 搜索记忆
        result = await mcp_tools.search_custom_memories(
            template_name="search_test_template",
            content_query={"category": "测试"},
            limit=10
        )
        
        assert result["success"] is True
        assert result["count"] >= 2
        assert len(result["memories"]) >= 2
        assert "搜索完成" in result["message"]
        
        # 验证搜索结果
        for memory_data in result["memories"]:
            custom_data = memory_data["content"]["custom_data"]
            if custom_data["category"] == "测试":
                assert "搜索测试" in custom_data["title"]
    
    async def test_list_templates(self, mcp_tools):
        """测试列出所有模板MCP工具"""
        # 创建几个测试模板
        for i in range(2):
            schema_definition = {
                "fields": {"data": {"type": "str"}},
                "required_fields": ["data"]
            }
            await mcp_tools.create_memory_template(
                name=f"list_test_template_{i}",
                schema_definition=schema_definition
            )
        
        result = await mcp_tools.list_templates()
        
        assert result["success"] is True
        assert result["count"] > 0
        assert len(result["templates"]) > 0
        assert "获取模板列表成功" in result["message"]
        
        # 验证模板数据结构
        template_data = result["templates"][0]
        assert "id" in template_data
        assert "name" in template_data
        assert "schema_name" in template_data
        assert "default_tags" in template_data
        assert "default_keywords" in template_data
    
    async def test_get_template_by_name(self, mcp_tools):
        """测试根据名称获取模板MCP工具"""
        # 先创建模板
        schema_definition = {
            "fields": {"test_field": {"type": "str"}},
            "required_fields": ["test_field"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="named_template_test",
            schema_definition=schema_definition,
            description="按名称获取的模板"
        )
        
        # 根据名称获取模板
        result = await mcp_tools.get_template_by_name("named_template_test")
        
        assert result["success"] is True
        assert result["template"] is not None
        assert result["template"]["name"] == "named_template_test"
        assert result["template"]["description"] == "按名称获取的模板"
        assert "获取模板" in result["message"]
        
        # 获取不存在的模板
        result = await mcp_tools.get_template_by_name("nonexistent_template")
        assert result["success"] is False
        assert result["template"] is None
        assert "未找到" in result["message"]
    
    async def test_get_statistics(self, mcp_tools):
        """测试获取统计信息MCP工具"""
        result = await mcp_tools.get_statistics()
        
        assert result["success"] is True
        assert "statistics" in result
        assert "获取统计信息成功" in result["message"]
        
        # 验证统计信息结构
        stats = result["statistics"]
        assert "total_templates" in stats
        assert "total_schemas" in stats
        assert "total_custom_memories" in stats
        assert "template_usage" in stats
        assert "schema_usage" in stats
        
        # 验证数据类型
        assert isinstance(stats["total_templates"], int)
        assert isinstance(stats["total_schemas"], int)
        assert isinstance(stats["template_usage"], dict)
        assert isinstance(stats["schema_usage"], dict)
    
    async def test_convenience_methods(self, mcp_tools):
        """测试便捷方法MCP工具"""
        # 测试创建用户档案
        user_data = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "age": 25,
            "preferences": {"language": "zh-CN"}
        }
        
        result = await mcp_tools.create_user_profile(
            user_data=user_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert result["success"] is True
        assert result["memory_id"] is not None
        assert "张三" in result["message"]
        
        # 测试创建任务
        task_data = {
            "task_name": "MCP测试任务",
            "status": "进行中",
            "priority": 3,
            "assignee": "测试人员"
        }
        
        result = await mcp_tools.create_task(
            task_data=task_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert result["success"] is True
        assert result["memory_id"] is not None
        assert "MCP测试任务" in result["message"]
        
        # 测试创建知识
        knowledge_data = {
            "title": "MCP测试知识",
            "category": "技术",
            "content": "这是一个MCP测试知识条目"
        }
        
        result = await mcp_tools.create_knowledge(
            knowledge_data=knowledge_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert result["success"] is True
        assert result["memory_id"] is not None
        assert "MCP测试知识" in result["message"]
    
    async def test_batch_operations(self, mcp_tools):
        """测试批量操作MCP工具"""
        # 先创建模板
        schema_definition = {
            "fields": {
                "name": {"type": "str"},
                "value": {"type": "int"}
            },
            "required_fields": ["name", "value"]
        }
        
        template_result = await mcp_tools.create_memory_template(
            name="batch_test_template",
            schema_definition=schema_definition
        )
        template_id = template_result["template_id"]
        
        # 批量创建记忆
        contents = [
            {"name": "批量1", "value": 1},
            {"name": "批量2", "value": 2},
            {"name": "批量3", "value": 3}
        ]
        
        create_result = await mcp_tools.batch_create_memories(
            template_id=template_id,
            contents=contents,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent",
            title="批量测试"
        )
        
        assert create_result["success"] is True
        assert create_result["created_count"] == 3
        assert len(create_result["memory_ids"]) == 3
        assert "批量创建成功" in create_result["message"]
        
        # 批量删除记忆
        memory_ids = create_result["memory_ids"]
        delete_result = await mcp_tools.batch_delete_memories(memory_ids)
        
        assert delete_result["success"] is True
        assert delete_result["deleted_count"] == 3
        assert "批量删除成功" in delete_result["message"]


class TestGlobalMCPTools:
    """测试全局MCP工具"""
    
    def test_get_custom_memory_mcp_tools(self):
        """测试获取全局MCP工具"""
        tools1 = get_custom_memory_mcp_tools()
        tools2 = get_custom_memory_mcp_tools()
        
        # 应该返回同一个实例
        assert tools1 is tools2
        assert isinstance(tools1, CustomMemoryMCPTools)
    
    def test_set_custom_memory_mcp_tools(self):
        """测试设置全局MCP工具"""
        custom_tools = CustomMemoryMCPTools()
        set_custom_memory_mcp_tools(custom_tools)
        
        retrieved_tools = get_custom_memory_mcp_tools()
        assert retrieved_tools is custom_tools


if __name__ == "__main__":
    pytest.main([__file__])