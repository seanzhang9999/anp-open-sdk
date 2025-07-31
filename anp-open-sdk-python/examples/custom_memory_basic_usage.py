"""
自定义Memory管理系统基础使用示例

演示如何使用自定义Memory管理系统进行基本的CRUD操作
"""

import asyncio
from datetime import datetime

from anp_runtime.local_service.memory import (
    CustomMemoryManager,
    CustomMemorySchema,
    CustomMemoryTemplate,
    TemplateFactory,
    get_custom_memory_manager
)


async def basic_usage_example():
    """基础使用示例"""
    print("=== 自定义Memory管理系统基础使用示例 ===\n")
    
    # 1. 获取自定义记忆管理器
    print("1. 获取自定义记忆管理器")
    custom_manager = get_custom_memory_manager()
    print("✓ 自定义记忆管理器已初始化\n")
    
    # 2. 创建自定义模式
    print("2. 创建自定义模式")
    user_schema = CustomMemorySchema(
        name="user_profile",
        version="1.0",
        description="用户档案信息",
        fields={
            "name": {"type": "str", "description": "用户姓名"},
            "email": {"type": "str", "description": "用户邮箱"},
            "age": {"type": "int", "description": "用户年龄", "min": 0, "max": 120},
            "preferences": {"type": "dict", "description": "用户偏好"},
            "last_login": {"type": "str", "description": "最后登录时间"}
        },
        required_fields=["name", "email"]
    )
    print(f"✓ 创建用户档案模式: {user_schema.name}\n")
    
    # 3. 创建自定义模板
    print("3. 创建自定义模板")
    user_template = await custom_manager.create_template(
        name="user_profile_template",
        schema=user_schema,
        description="用户档案记忆模板",
        default_tags=["user", "profile"],
        default_keywords=["用户信息", "档案"]
    )
    print(f"✓ 创建用户档案模板: {user_template.name} (ID: {user_template.id})\n")
    
    # 4. 创建自定义记忆
    print("4. 创建自定义记忆")
    user_data = {
        "name": "张三",
        "email": "zhangsan@example.com",
        "age": 28,
        "preferences": {
            "language": "zh-CN",
            "theme": "dark",
            "notifications": True
        },
        "last_login": "2024-01-15T10:30:00Z"
    }
    
    user_memory = await custom_manager.create_custom_memory(
        template_id=user_template.id,
        content=user_data,
        source_agent_did="did:anp:user_service",
        source_agent_name="UserService",
        title="用户档案-张三",
        tags=["active_user"],
        keywords=["VIP用户"]
    )
    print(f"✓ 创建用户记忆: {user_memory.title} (ID: {user_memory.id})")
    print(f"  - 记忆类型: {user_memory.memory_type.value}")
    print(f"  - 标签: {user_memory.metadata.tags}")
    print(f"  - 关键词: {user_memory.metadata.keywords}\n")
    
    # 5. 获取自定义记忆
    print("5. 获取自定义记忆")
    retrieved_memory = await custom_manager.get_custom_memory(user_memory.id)
    if retrieved_memory:
        print(f"✓ 成功获取记忆: {retrieved_memory.title}")
        print(f"  - 用户名: {retrieved_memory.content['custom_data']['name']}")
        print(f"  - 邮箱: {retrieved_memory.content['custom_data']['email']}")
        print(f"  - 年龄: {retrieved_memory.content['custom_data']['age']}\n")
    
    # 6. 更新自定义记忆
    print("6. 更新自定义记忆")
    updated_data = user_data.copy()
    updated_data["age"] = 29
    updated_data["last_login"] = "2024-01-16T09:15:00Z"
    updated_data["preferences"]["theme"] = "light"
    
    success = await custom_manager.update_custom_memory(
        memory_id=user_memory.id,
        content=updated_data,
        tags=["active_user", "premium"],
        keywords=["VIP用户", "已更新"]
    )
    print(f"✓ 更新记忆成功: {success}")
    
    # 验证更新
    updated_memory = await custom_manager.get_custom_memory(user_memory.id)
    if updated_memory:
        print(f"  - 新年龄: {updated_memory.content['custom_data']['age']}")
        print(f"  - 新主题偏好: {updated_memory.content['custom_data']['preferences']['theme']}")
        print(f"  - 新标签: {updated_memory.metadata.tags}\n")
    
    # 7. 搜索自定义记忆
    print("7. 搜索自定义记忆")
    
    # 基于模板名搜索
    template_results = await custom_manager.search_custom_memories(
        template_name="user_profile_template"
    )
    print(f"✓ 基于模板名搜索到 {len(template_results)} 条记忆")
    
    # 基于内容查询搜索
    content_query = {"name": "张三"}
    content_results = await custom_manager.search_custom_memories(
        content_query=content_query
    )
    print(f"✓ 基于内容查询搜索到 {len(content_results)} 条记忆")
    
    # 基于标签搜索
    tag_results = await custom_manager.search_custom_memories(
        tags=["premium"]
    )
    print(f"✓ 基于标签搜索到 {len(tag_results)} 条记忆\n")
    
    # 8. 获取统计信息
    print("8. 获取统计信息")
    stats = await custom_manager.get_custom_memory_statistics()
    print("✓ 系统统计信息:")
    print(f"  - 总模板数: {stats['total_templates']}")
    print(f"  - 总模式数: {stats['total_schemas']}")
    print(f"  - 总自定义记忆数: {stats['total_custom_memories']}")
    print(f"  - 模板使用情况: {stats['template_usage']}")
    print(f"  - 模式使用情况: {stats['schema_usage']}\n")
    
    # 9. 删除自定义记忆
    print("9. 删除自定义记忆")
    delete_success = await custom_manager.delete_custom_memory(user_memory.id)
    print(f"✓ 删除记忆成功: {delete_success}")
    
    # 验证删除
    deleted_memory = await custom_manager.get_custom_memory(user_memory.id)
    print(f"✓ 验证删除: 记忆已不存在 ({deleted_memory is None})\n")


async def predefined_templates_example():
    """预定义模板使用示例"""
    print("=== 预定义模板使用示例 ===\n")
    
    custom_manager = get_custom_memory_manager()
    
    # 1. 使用预定义的用户档案模板
    print("1. 使用预定义用户档案模板")
    user_data = {
        "name": "李四",
        "email": "lisi@example.com",
        "age": 32,
        "preferences": {"language": "en-US", "timezone": "UTC+8"}
    }
    
    user_memory = await custom_manager.create_user_profile(
        user_data=user_data,
        source_agent_did="did:anp:app",
        source_agent_name="Application"
    )
    print(f"✓ 创建用户档案: {user_memory.title}\n")
    
    # 2. 使用预定义的任务模板
    print("2. 使用预定义任务模板")
    task_data = {
        "task_name": "实现自定义Memory功能",
        "status": "进行中",
        "priority": 4,
        "assignee": "开发团队",
        "due_date": "2024-02-01",
        "progress": 0.8,
        "description": "为ANP SDK添加自定义记忆管理功能"
    }
    
    task_memory = await custom_manager.create_task(
        task_data=task_data,
        source_agent_did="did:anp:project_manager",
        source_agent_name="ProjectManager",
        session_id="project_session_001"
    )
    print(f"✓ 创建任务记忆: {task_memory.title}\n")
    
    # 3. 使用预定义的知识库模板
    print("3. 使用预定义知识库模板")
    knowledge_data = {
        "title": "自定义Memory系统架构",
        "category": "技术文档",
        "content": "自定义Memory系统采用模板化设计，支持灵活的数据模式定义...",
        "source": "内部文档",
        "confidence": 0.95,
        "references": ["设计文档v1.0", "API规范"],
        "tags": ["架构", "设计模式"]
    }
    
    knowledge_memory = await custom_manager.create_knowledge(
        knowledge_data=knowledge_data,
        source_agent_did="did:anp:knowledge_base",
        source_agent_name="KnowledgeBase"
    )
    print(f"✓ 创建知识记忆: {knowledge_memory.title}\n")
    
    # 4. 列出所有模板
    print("4. 查看所有可用模板")
    templates = await custom_manager.list_templates()
    for template in templates:
        print(f"  - {template.name}: {template.description}")
        print(f"    模式: {template.schema.name} v{template.schema.version}")
        print(f"    默认标签: {template.default_tags}")
        print()


async def batch_operations_example():
    """批量操作示例"""
    print("=== 批量操作示例 ===\n")
    
    custom_manager = get_custom_memory_manager()
    
    # 获取任务模板
    task_template = await custom_manager.get_template_by_name("task_template")
    if not task_template:
        print("❌ 任务模板不存在")
        return
    
    # 1. 批量创建记忆
    print("1. 批量创建任务记忆")
    task_contents = [
        {
            "task_name": "设计数据模型",
            "status": "已完成",
            "priority": 3,
            "assignee": "架构师",
            "progress": 1.0
        },
        {
            "task_name": "实现CRUD接口",
            "status": "已完成",
            "priority": 4,
            "assignee": "后端开发",
            "progress": 1.0
        },
        {
            "task_name": "编写单元测试",
            "status": "进行中",
            "priority": 3,
            "assignee": "QA工程师",
            "progress": 0.7
        },
        {
            "task_name": "撰写文档",
            "status": "待处理",
            "priority": 2,
            "assignee": "技术文档",
            "progress": 0.0
        }
    ]
    
    batch_memories = await custom_manager.create_custom_memories_batch(
        template_id=task_template.id,
        contents=task_contents,
        source_agent_did="did:anp:project_manager",
        source_agent_name="ProjectManager",
        title="项目任务",
        session_id="batch_project_001"
    )
    
    print(f"✓ 批量创建了 {len(batch_memories)} 个任务记忆")
    for i, memory in enumerate(batch_memories):
        task_data = memory.content["custom_data"]
        print(f"  {i+1}. {task_data['task_name']} - {task_data['status']} ({task_data['progress']*100:.0f}%)")
    print()
    
    # 2. 搜索批量创建的记忆
    print("2. 搜索已完成的任务")
    completed_tasks = await custom_manager.search_custom_memories(
        template_name="task_template",
        content_query={"status": "已完成"}
    )
    print(f"✓ 找到 {len(completed_tasks)} 个已完成的任务:")
    for memory in completed_tasks:
        task_data = memory.content["custom_data"]
        print(f"  - {task_data['task_name']} (负责人: {task_data['assignee']})")
    print()
    
    # 3. 批量删除记忆
    print("3. 清理测试数据 - 批量删除记忆")
    memory_ids = [memory.id for memory in batch_memories]
    deleted_count = await custom_manager.delete_custom_memories_batch(memory_ids)
    print(f"✓ 批量删除了 {deleted_count} 个记忆\n")


async def main():
    """主函数"""
    try:
        await basic_usage_example()
        await predefined_templates_example()
        await batch_operations_example()
        
        print("=== 示例运行完成 ===")
        print("所有自定义Memory操作都已成功演示！")
        
    except Exception as e:
        print(f"❌ 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())