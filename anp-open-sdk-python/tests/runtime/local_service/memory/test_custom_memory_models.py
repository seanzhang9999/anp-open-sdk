"""
自定义记忆数据模型测试
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from anp_runtime.local_service.memory.custom_memory_models import (
    CustomMemoryType,
    CustomMemorySchema,
    CustomMemoryTemplate,
    CustomMemoryBuilder,
    TemplateFactory
)
from anp_runtime.local_service.memory.memory_models import MemoryType


class TestCustomMemorySchema:
    """测试CustomMemorySchema类"""
    
    def test_schema_creation(self):
        """测试模式创建"""
        schema = CustomMemorySchema(
            name="test_schema",
            version="1.0",
            description="测试模式",
            fields={
                "name": {"type": "str", "description": "名称"},
                "age": {"type": "int", "description": "年龄", "min": 0, "max": 120}
            },
            required_fields=["name"]
        )
        
        assert schema.name == "test_schema"
        assert schema.version == "1.0"
        assert "name" in schema.fields
        assert "age" in schema.fields
        assert schema.required_fields == ["name"]
    
    def test_schema_validation_success(self):
        """测试数据验证成功"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={
                "name": {"type": "str"},
                "age": {"type": "int", "min": 0, "max": 120},
                "status": {"type": "str", "enum": ["active", "inactive"]}
            },
            required_fields=["name", "age"]
        )
        
        data = {
            "name": "张三",
            "age": 25,
            "status": "active"
        }
        
        is_valid, errors = schema.validate_data(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_schema_validation_missing_required(self):
        """测试缺少必需字段的验证"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={"name": {"type": "str"}, "age": {"type": "int"}},
            required_fields=["name", "age"]
        )
        
        data = {"name": "张三"}  # 缺少age字段
        
        is_valid, errors = schema.validate_data(data)
        assert not is_valid
        assert "缺少必需字段: age" in errors
    
    def test_schema_validation_wrong_type(self):
        """测试错误类型的验证"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={"age": {"type": "int"}},
            required_fields=["age"]
        )
        
        data = {"age": "not_a_number"}  # 错误的类型
        
        is_valid, errors = schema.validate_data(data)
        assert not is_valid
        assert any("类型错误" in error for error in errors)
    
    def test_schema_validation_enum_values(self):
        """测试枚举值验证"""
        schema = CustomMemorySchema(
            name="status_schema",
            fields={
                "status": {"type": "str", "enum": ["active", "inactive", "pending"]}
            },
            required_fields=["status"]
        )
        
        # 有效枚举值
        valid_data = {"status": "active"}
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid
        
        # 无效枚举值
        invalid_data = {"status": "unknown"}
        is_valid, errors = schema.validate_data(invalid_data)
        assert not is_valid
        assert any("不在允许的枚举值中" in error for error in errors)
    
    def test_schema_validation_numeric_range(self):
        """测试数值范围验证"""
        schema = CustomMemorySchema(
            name="range_schema",
            fields={
                "score": {"type": "int", "min": 0, "max": 100}
            },
            required_fields=["score"]
        )
        
        # 有效范围
        valid_data = {"score": 85}
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid
        
        # 超出最大值
        invalid_max = {"score": 150}
        is_valid, errors = schema.validate_data(invalid_max)
        assert not is_valid
        assert any("大于最大值" in error for error in errors)
        
        # 低于最小值
        invalid_min = {"score": -10}
        is_valid, errors = schema.validate_data(invalid_min)
        assert not is_valid
        assert any("小于最小值" in error for error in errors)
    
    def test_schema_to_dict(self):
        """测试模式转换为字典"""
        schema = CustomMemorySchema(
            name="test_schema",
            version="2.0",
            description="测试模式",
            fields={"name": {"type": "str"}},
            required_fields=["name"]
        )
        
        schema_dict = schema.to_dict()
        
        assert schema_dict["name"] == "test_schema"
        assert schema_dict["version"] == "2.0"
        assert schema_dict["description"] == "测试模式"
        assert "name" in schema_dict["fields"]
        assert schema_dict["required_fields"] == ["name"]
    
    def test_schema_from_dict(self):
        """测试从字典创建模式"""
        schema_data = {
            "name": "test_schema",
            "version": "1.5",
            "description": "从字典创建的模式",
            "fields": {"title": {"type": "str"}},
            "required_fields": ["title"]
        }
        
        schema = CustomMemorySchema.from_dict(schema_data)
        
        assert schema.name == "test_schema"
        assert schema.version == "1.5"
        assert schema.description == "从字典创建的模式"
        assert "title" in schema.fields
        assert schema.required_fields == ["title"]


class TestCustomMemoryTemplate:
    """测试CustomMemoryTemplate类"""
    
    def test_template_creation(self):
        """测试模板创建"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={"name": {"type": "str"}},
            required_fields=["name"]
        )
        
        template = CustomMemoryTemplate(
            name="user_template",
            description="用户模板",
            schema=schema,
            default_tags=["user"],
            default_keywords=["用户", "档案"]
        )
        
        assert template.name == "user_template"
        assert template.description == "用户模板"
        assert template.schema.name == "user_schema"
        assert template.default_tags == ["user"]
        assert template.default_keywords == ["用户", "档案"]
        assert isinstance(template.created_at, datetime)
    
    def test_template_create_memory_success(self):
        """测试使用模板创建记忆成功"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={
                "name": {"type": "str"},
                "email": {"type": "str"}
            },
            required_fields=["name", "email"]
        )
        
        template = CustomMemoryTemplate(
            name="user_template",
            schema=schema,
            default_tags=["user"],
            default_keywords=["档案"]
        )
        
        content = {
            "name": "张三",
            "email": "zhangsan@example.com"
        }
        
        memory = template.create_memory(
            content=content,
            source_agent_did="did:anp:agent1",
            source_agent_name="TestAgent",
            title="测试用户"
        )
        
        assert memory.memory_type == MemoryType.PATTERN
        assert memory.title == "测试用户"
        assert memory.content["template_id"] == template.id
        assert memory.content["custom_data"] == content
        assert "user" in memory.metadata.tags
        assert "档案" in memory.metadata.keywords
    
    def test_template_create_memory_validation_error(self):
        """测试使用模板创建记忆时验证失败"""
        schema = CustomMemorySchema(
            name="user_schema",
            fields={"name": {"type": "str"}},
            required_fields=["name"]
        )
        
        template = CustomMemoryTemplate(
            name="user_template",
            schema=schema
        )
        
        # 缺少必需字段
        invalid_content = {"email": "test@example.com"}
        
        with pytest.raises(ValueError, match="数据验证失败"):
            template.create_memory(
                content=invalid_content,
                source_agent_did="did:anp:agent1",
                source_agent_name="TestAgent"
            )
    
    def test_template_merge_tags_keywords(self):
        """测试模板合并标签和关键词"""
        schema = CustomMemorySchema(
            name="test_schema",
            fields={"data": {"type": "str"}},
            required_fields=["data"]
        )
        
        template = CustomMemoryTemplate(
            name="test_template",
            schema=schema,
            default_tags=["default_tag"],
            default_keywords=["默认关键词"]
        )
        
        memory = template.create_memory(
            content={"data": "test"},
            source_agent_did="did:anp:agent1",
            source_agent_name="TestAgent",
            tags=["custom_tag"],
            keywords=["自定义关键词"]
        )
        
        # 检查标签和关键词是否正确合并
        assert "default_tag" in memory.metadata.tags
        assert "custom_tag" in memory.metadata.tags
        assert "默认关键词" in memory.metadata.keywords
        assert "自定义关键词" in memory.metadata.keywords
    
    def test_template_to_dict(self):
        """测试模板转换为字典"""
        schema = CustomMemorySchema(name="test_schema")
        template = CustomMemoryTemplate(
            name="test_template",
            description="测试模板",
            schema=schema,
            default_tags=["tag1"],
            default_keywords=["keyword1"]
        )
        
        template_dict = template.to_dict()
        
        assert template_dict["name"] == "test_template"
        assert template_dict["description"] == "测试模板"
        assert "schema" in template_dict
        assert template_dict["default_tags"] == ["tag1"]
        assert template_dict["default_keywords"] == ["keyword1"]
        assert "created_at" in template_dict
    
    def test_template_from_dict(self):
        """测试从字典创建模板"""
        template_data = {
            "name": "test_template",
            "description": "从字典创建",
            "schema": {
                "name": "test_schema",
                "fields": {"data": {"type": "str"}}
            },
            "default_tags": ["tag1"],
            "default_keywords": ["keyword1"],
            "created_at": datetime.now().isoformat()
        }
        
        template = CustomMemoryTemplate.from_dict(template_data)
        
        assert template.name == "test_template"
        assert template.description == "从字典创建"
        assert template.schema.name == "test_schema"
        assert template.default_tags == ["tag1"]
        assert template.default_keywords == ["keyword1"]


class TestCustomMemoryBuilder:
    """测试CustomMemoryBuilder类"""
    
    def test_create_user_profile_schema(self):
        """测试创建用户档案模式"""
        schema = CustomMemoryBuilder.create_user_profile_schema()
        
        assert schema.name == "user_profile"
        assert "name" in schema.fields
        assert "email" in schema.fields
        assert "age" in schema.fields
        assert "preferences" in schema.fields
        assert "name" in schema.required_fields
        assert "email" in schema.required_fields
        
        # 测试年龄范围验证
        valid_data = {"name": "张三", "email": "test@example.com", "age": 25}
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid
        
        invalid_data = {"name": "张三", "email": "test@example.com", "age": 150}
        is_valid, errors = schema.validate_data(invalid_data)
        assert not is_valid
    
    def test_create_task_management_schema(self):
        """测试创建任务管理模式"""
        schema = CustomMemoryBuilder.create_task_management_schema()
        
        assert schema.name == "task_management"
        assert "task_name" in schema.fields
        assert "status" in schema.fields
        assert "priority" in schema.fields
        assert "task_name" in schema.required_fields
        assert "status" in schema.required_fields
        assert "priority" in schema.required_fields
        
        # 测试状态枚举验证
        valid_data = {
            "task_name": "测试任务",
            "status": "进行中",
            "priority": 3
        }
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid
        
        # 测试无效状态
        invalid_data = {
            "task_name": "测试任务",
            "status": "invalid_status",
            "priority": 3
        }
        is_valid, errors = schema.validate_data(invalid_data)
        assert not is_valid
    
    def test_create_knowledge_base_schema(self):
        """测试创建知识库模式"""
        schema = CustomMemoryBuilder.create_knowledge_base_schema()
        
        assert schema.name == "knowledge_base"
        assert "title" in schema.fields
        assert "category" in schema.fields
        assert "content" in schema.fields
        assert "title" in schema.required_fields
        assert "category" in schema.required_fields
        assert "content" in schema.required_fields
    
    def test_create_conversation_schema(self):
        """测试创建对话历史模式"""
        schema = CustomMemoryBuilder.create_conversation_schema()
        
        assert schema.name == "conversation_history"
        assert "session_id" in schema.fields
        assert "participants" in schema.fields
        assert "messages" in schema.fields
        assert "sentiment" in schema.fields
        assert "session_id" in schema.required_fields
        
        # 测试情感枚举验证
        valid_data = {
            "session_id": "session123",
            "participants": ["user1", "user2"],
            "messages": ["Hello", "Hi"],
            "sentiment": "positive"
        }
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid
    
    def test_create_event_log_schema(self):
        """测试创建事件日志模式"""
        schema = CustomMemoryBuilder.create_event_log_schema()
        
        assert schema.name == "event_log"
        assert "event_name" in schema.fields
        assert "event_type" in schema.fields
        assert "level" in schema.fields
        assert "event_name" in schema.required_fields
        assert "level" in schema.required_fields
        
        # 测试日志级别枚举验证
        valid_data = {
            "event_name": "用户登录",
            "event_type": "authentication",
            "timestamp": "2024-01-01T10:00:00",
            "level": "INFO"
        }
        is_valid, errors = schema.validate_data(valid_data)
        assert is_valid


class TestTemplateFactory:
    """测试TemplateFactory类"""
    
    def test_create_user_profile_template(self):
        """测试创建用户档案模板"""
        template = TemplateFactory.create_user_profile_template()
        
        assert template.name == "user_profile_template"
        assert template.schema.name == "user_profile"
        assert "user" in template.default_tags
        assert "profile" in template.default_tags
        assert "用户信息" in template.default_keywords
    
    def test_create_task_template(self):
        """测试创建任务模板"""
        template = TemplateFactory.create_task_template()
        
        assert template.name == "task_template"
        assert template.schema.name == "task_management"
        assert "task" in template.default_tags
        assert "project" in template.default_tags
    
    def test_create_knowledge_template(self):
        """测试创建知识库模板"""
        template = TemplateFactory.create_knowledge_template()
        
        assert template.name == "knowledge_template"
        assert template.schema.name == "knowledge_base"
        assert "knowledge" in template.default_tags
        assert "reference" in template.default_tags
    
    def test_create_conversation_template(self):
        """测试创建对话历史模板"""
        template = TemplateFactory.create_conversation_template()
        
        assert template.name == "conversation_template"
        assert template.schema.name == "conversation_history"
        assert "conversation" in template.default_tags
        assert "history" in template.default_tags
    
    def test_create_event_log_template(self):
        """测试创建事件日志模板"""
        template = TemplateFactory.create_event_log_template()
        
        assert template.name == "event_log_template"
        assert template.schema.name == "event_log"
        assert "event" in template.default_tags
        assert "log" in template.default_tags
        assert "system" in template.default_tags


if __name__ == "__main__":
    pytest.main([__file__])