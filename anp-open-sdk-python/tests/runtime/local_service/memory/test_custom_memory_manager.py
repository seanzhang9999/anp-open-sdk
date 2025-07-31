"""
自定义记忆管理器测试
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from anp_runtime.local_service.memory.custom_memory_manager import (
    CustomMemoryManager,
    get_custom_memory_manager,
    set_custom_memory_manager
)
from anp_runtime.local_service.memory.custom_memory_models import (
    CustomMemorySchema,
    CustomMemoryTemplate,
    TemplateFactory
)
from anp_runtime.local_service.memory.memory_models import MemoryType


class TestCustomMemoryManager:
    """测试CustomMemoryManager类"""
    
    @pytest.fixture
    async def manager(self):
        """创建测试用的自定义记忆管理器"""
        return CustomMemoryManager()
    
    @pytest.fixture
    def test_schema(self):
        """创建测试用的模式"""
        return CustomMemorySchema(
            name="test_schema",
            fields={
                "title": {"type": "str", "description": "标题"},
                "content": {"type": "str", "description": "内容"},
                "priority": {"type": "int", "description": "优先级", "min": 1, "max": 5}
            },
            required_fields=["title", "content"]
        )
    
    @pytest.fixture
    def test_template(self, test_schema):
        """创建测试用的模板"""
        return CustomMemoryTemplate(
            name="test_template",
            description="测试模板",
            schema=test_schema,
            default_tags=["test"],
            default_keywords=["测试"]
        )

    async def test_create_template(self, manager, test_schema):
        """测试创建模板"""
        template = await manager.create_template(
            name="new_template",
            schema=test_schema,
            description="新建模板",
            default_tags=["new"],
            default_keywords=["新建"]
        )
        
        assert template.name == "new_template"
        assert template.description == "新建模板"
        assert template.schema.name == test_schema.name
        assert template.default_tags == ["new"]
        assert template.default_keywords == ["新建"]
        
        # 验证模板是否被保存
        retrieved_template = await manager.get_template(template.id)
        assert retrieved_template is not None
        assert retrieved_template.name == "new_template"
    
    async def test_get_template_by_name(self, manager, test_template):
        """测试根据名称获取模板"""
        # 先创建模板
        await manager.create_template(
            name=test_template.name,
            schema=test_template.schema,
            description=test_template.description
        )
        
        retrieved_template = await manager.get_template_by_name(test_template.name)
        assert retrieved_template is not None
        assert retrieved_template.name == test_template.name
        
        # 测试不存在的模板
        nonexistent_template = await manager.get_template_by_name("nonexistent")
        assert nonexistent_template is None
    
    async def test_list_templates(self, manager):
        """测试列出所有模板"""
        # 获取初始模板数量（预定义模板）
        initial_templates = await manager.list_templates()
        initial_count = len(initial_templates)
        
        # 创建新模板
        schema = CustomMemorySchema(name="list_test_schema")
        await manager.create_template("template1", schema)
        await manager.create_template("template2", schema)
        
        templates = await manager.list_templates()
        assert len(templates) == initial_count + 2
        
        template_names = [t.name for t in templates]
        assert "template1" in template_names
        assert "template2" in template_names
    
    async def test_update_template(self, manager, test_template):
        """测试更新模板"""
        # 先创建模板
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 更新模板
        success = await manager.update_template(
            template_id=created_template.id,
            name="updated_template",
            description="更新的描述",
            default_tags=["updated"],
            default_keywords=["更新"]
        )
        
        assert success
        
        # 验证更新
        updated_template = await manager.get_template(created_template.id)
        assert updated_template.name == "updated_template"
        assert updated_template.description == "更新的描述"
        assert updated_template.default_tags == ["updated"]
        assert updated_template.default_keywords == ["更新"]
    
    async def test_delete_template(self, manager, test_template):
        """测试删除模板"""
        # 先创建模板
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 删除模板
        success = await manager.delete_template(created_template.id)
        assert success
        
        # 验证删除
        deleted_template = await manager.get_template(created_template.id)
        assert deleted_template is None
        
        # 删除不存在的模板
        success = await manager.delete_template("nonexistent_id")
        assert not success
    
    async def test_create_custom_memory(self, manager, test_template):
        """测试创建自定义记忆"""
        # 先创建模板
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema,
            default_tags=test_template.default_tags,
            default_keywords=test_template.default_keywords
        )
        
        content = {
            "title": "测试记忆",
            "content": "这是一个测试记忆的内容",
            "priority": 3
        }
        
        memory = await manager.create_custom_memory(
            template_id=created_template.id,
            content=content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent",
            title="自定义测试记忆",
            tags=["custom"],
            keywords=["自定义"]
        )
        
        assert memory.memory_type == MemoryType.PATTERN
        assert memory.title == "自定义测试记忆"
        assert memory.content["template_id"] == created_template.id
        assert memory.content["custom_data"] == content
        assert memory.metadata.source_agent_did == "did:anp:test_agent"
        
        # 验证标签和关键词合并
        assert "test" in memory.metadata.tags  # 从模板默认标签
        assert "custom" in memory.metadata.tags  # 自定义标签
        assert "测试" in memory.metadata.keywords  # 从模板默认关键词
        assert "自定义" in memory.metadata.keywords  # 自定义关键词
    
    async def test_create_custom_memory_validation_error(self, manager, test_template):
        """测试创建自定义记忆时验证失败"""
        # 先创建模板
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 无效内容（缺少必需字段）
        invalid_content = {"title": "测试"}  # 缺少content字段
        
        with pytest.raises(ValueError, match="数据验证失败"):
            await manager.create_custom_memory(
                template_id=created_template.id,
                content=invalid_content,
                source_agent_did="did:anp:test_agent",
                source_agent_name="TestAgent"
            )
    
    async def test_create_custom_memory_template_not_found(self, manager):
        """测试使用不存在的模板创建记忆"""
        with pytest.raises(ValueError, match="模板不存在"):
            await manager.create_custom_memory(
                template_id="nonexistent_template_id",
                content={"data": "test"},
                source_agent_did="did:anp:test_agent",
                source_agent_name="TestAgent"
            )
    
    async def test_get_custom_memory(self, manager, test_template):
        """测试获取自定义记忆"""
        # 先创建模板和记忆
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        content = {"title": "测试", "content": "内容"}
        created_memory = await manager.create_custom_memory(
            template_id=created_template.id,
            content=content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        # 获取记忆
        retrieved_memory = await manager.get_custom_memory(created_memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.id == created_memory.id
        assert retrieved_memory.content["custom_data"] == content
        
        # 获取不存在的记忆
        nonexistent_memory = await manager.get_custom_memory("nonexistent_id")
        assert nonexistent_memory is None
    
    async def test_update_custom_memory(self, manager, test_template):
        """测试更新自定义记忆"""
        # 先创建模板和记忆
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        original_content = {"title": "原始标题", "content": "原始内容"}
        created_memory = await manager.create_custom_memory(
            template_id=created_template.id,
            content=original_content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        # 更新记忆
        updated_content = {"title": "更新标题", "content": "更新内容"}
        success = await manager.update_custom_memory(
            memory_id=created_memory.id,
            content=updated_content,
            title="新标题",
            tags=["updated"],
            keywords=["更新"]
        )
        
        assert success
        
        # 验证更新
        updated_memory = await manager.get_custom_memory(created_memory.id)
        assert updated_memory.title == "新标题"
        assert updated_memory.content["custom_data"] == updated_content
        assert updated_memory.metadata.tags == ["updated"]
        assert updated_memory.metadata.keywords == ["更新"]
    
    async def test_delete_custom_memory(self, manager, test_template):
        """测试删除自定义记忆"""
        # 先创建模板和记忆
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        content = {"title": "测试", "content": "内容"}
        created_memory = await manager.create_custom_memory(
            template_id=created_template.id,
            content=content,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        # 删除记忆
        success = await manager.delete_custom_memory(created_memory.id)
        assert success
        
        # 验证删除
        deleted_memory = await manager.get_custom_memory(created_memory.id)
        assert deleted_memory is None
        
        # 删除不存在的记忆
        success = await manager.delete_custom_memory("nonexistent_id")
        assert not success
    
    async def test_search_custom_memories(self, manager, test_template):
        """测试搜索自定义记忆"""
        # 先创建模板和多个记忆
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 创建多个记忆
        memories = []
        for i in range(3):
            content = {"title": f"测试{i}", "content": f"内容{i}"}
            memory = await manager.create_custom_memory(
                template_id=created_template.id,
                content=content,
                source_agent_did="did:anp:test_agent",
                source_agent_name="TestAgent",
                tags=[f"tag{i}"]
            )
            memories.append(memory)
        
        # 基于模板名搜索
        results = await manager.search_custom_memories(template_name=test_template.name)
        assert len(results) >= 3
        
        # 基于模式名搜索
        results = await manager.search_custom_memories(schema_name=test_template.schema.name)
        assert len(results) >= 3
        
        # 基于内容查询搜索
        content_query = {"title": "测试1"}
        results = await manager.search_custom_memories(content_query=content_query)
        assert len(results) >= 1
        assert any("测试1" in r.content["custom_data"]["title"] for r in results)
    
    async def test_batch_create_memories(self, manager, test_template):
        """测试批量创建记忆"""
        # 先创建模板
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 批量创建数据
        contents = [
            {"title": "批量1", "content": "内容1"},
            {"title": "批量2", "content": "内容2"},
            {"title": "批量3", "content": "内容3"}
        ]
        
        memories = await manager.create_custom_memories_batch(
            template_id=created_template.id,
            contents=contents,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent",
            title="批量测试"
        )
        
        assert len(memories) == 3
        for i, memory in enumerate(memories):
            assert memory.content["custom_data"]["title"] == f"批量{i+1}"
            assert "批量测试" in memory.title
    
    async def test_batch_delete_memories(self, manager, test_template):
        """测试批量删除记忆"""
        # 先创建模板和记忆
        created_template = await manager.create_template(
            name=test_template.name,
            schema=test_template.schema
        )
        
        # 创建多个记忆
        memory_ids = []
        for i in range(3):
            content = {"title": f"删除测试{i}", "content": f"内容{i}"}
            memory = await manager.create_custom_memory(
                template_id=created_template.id,
                content=content,
                source_agent_did="did:anp:test_agent",
                source_agent_name="TestAgent"
            )
            memory_ids.append(memory.id)
        
        # 批量删除
        deleted_count = await manager.delete_custom_memories_batch(memory_ids)
        assert deleted_count == 3
        
        # 验证删除
        for memory_id in memory_ids:
            deleted_memory = await manager.get_custom_memory(memory_id)
            assert deleted_memory is None
    
    async def test_convenience_methods(self, manager):
        """测试便捷方法"""
        # 测试创建用户档案
        user_data = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "age": 25,
            "preferences": {"language": "zh-CN"}
        }
        
        user_memory = await manager.create_user_profile(
            user_data=user_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert user_memory.title == "用户档案-张三"
        assert user_memory.content["custom_data"] == user_data
        
        # 测试创建任务
        task_data = {
            "task_name": "测试任务",
            "status": "进行中",
            "priority": 3,
            "assignee": "测试人员"
        }
        
        task_memory = await manager.create_task(
            task_data=task_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert task_memory.title == "任务-测试任务"
        assert task_memory.content["custom_data"] == task_data
        
        # 测试创建知识
        knowledge_data = {
            "title": "测试知识",
            "category": "技术",
            "content": "这是一个测试知识条目"
        }
        
        knowledge_memory = await manager.create_knowledge(
            knowledge_data=knowledge_data,
            source_agent_did="did:anp:test_agent",
            source_agent_name="TestAgent"
        )
        
        assert knowledge_memory.title == "知识-测试知识"
        assert knowledge_memory.content["custom_data"] == knowledge_data
    
    async def test_get_statistics(self, manager):
        """测试获取统计信息"""
        stats = await manager.get_custom_memory_statistics()
        
        assert "total_templates" in stats
        assert "total_schemas" in stats
        assert "total_custom_memories" in stats
        assert "template_usage" in stats
        assert "schema_usage" in stats
        
        # 验证统计数据类型
        assert isinstance(stats["total_templates"], int)
        assert isinstance(stats["total_schemas"], int)
        assert isinstance(stats["total_custom_memories"], int)
        assert isinstance(stats["template_usage"], dict)
        assert isinstance(stats["schema_usage"], dict)


class TestGlobalCustomMemoryManager:
    """测试全局自定义记忆管理器"""
    
    def test_get_custom_memory_manager(self):
        """测试获取全局管理器"""
        manager1 = get_custom_memory_manager()
        manager2 = get_custom_memory_manager()
        
        # 应该返回同一个实例
        assert manager1 is manager2
        assert isinstance(manager1, CustomMemoryManager)
    
    def test_set_custom_memory_manager(self):
        """测试设置全局管理器"""
        custom_manager = CustomMemoryManager()
        set_custom_memory_manager(custom_manager)
        
        retrieved_manager = get_custom_memory_manager()
        assert retrieved_manager is custom_manager


if __name__ == "__main__":
    pytest.main([__file__])