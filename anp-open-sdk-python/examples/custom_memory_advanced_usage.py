"""
自定义Memory管理系统高级使用示例

演示如何在local_method装饰器中集成自定义Memory功能
以及MCP工具的使用
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from anp_runtime.local_service.local_methods_decorators import local_method
from anp_runtime.local_service.memory import (
    memory_enabled,
    CustomMemoryManager,
    CustomMemoryMCPTools,
    get_custom_memory_manager,
    get_custom_memory_mcp_tools
)


class UserService:
    """用户服务示例 - 演示在装饰器中使用自定义Memory"""
    
    def __init__(self):
        self.custom_manager = get_custom_memory_manager()
    
    @local_method(memory=memory_enabled(tags=["user_service", "profile"]))
    async def create_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建用户档案并保存为自定义记忆
        
        Args:
            user_data: 用户数据字典
        
        Returns:
            创建结果字典
        """
        try:
            # 验证用户数据
            required_fields = ["name", "email"]
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 使用自定义Memory管理器保存用户档案
            memory = await self.custom_manager.create_user_profile(
                user_data=user_data,
                source_agent_did="did:anp:user_service",
                source_agent_name="UserService",
                tags=["new_user", "profile_created"],
                keywords=["用户注册", "档案创建"]
            )
            
            return {
                "success": True,
                "user_id": user_data.get("name", "unknown"),
                "memory_id": memory.id,
                "message": f"用户档案 '{user_data['name']}' 创建成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "创建用户档案失败"
            }
    
    @local_method(memory=memory_enabled(tags=["user_service", "update"]))
    async def update_user_preferences(
        self, 
        user_name: str, 
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新用户偏好设置
        
        Args:
            user_name: 用户名
            preferences: 新的偏好设置
        
        Returns:
            更新结果字典
        """
        try:
            # 搜索用户档案记忆
            memories = await self.custom_manager.search_custom_memories(
                template_name="user_profile_template",
                content_query={"name": user_name}
            )
            
            if not memories:
                return {
                    "success": False,
                    "message": f"未找到用户 '{user_name}' 的档案"
                }
            
            user_memory = memories[0]
            current_data = user_memory.content["custom_data"]
            
            # 更新偏好设置
            if "preferences" not in current_data:
                current_data["preferences"] = {}
            current_data["preferences"].update(preferences)
            
            # 保存更新
            success = await self.custom_manager.update_custom_memory(
                memory_id=user_memory.id,
                content=current_data,
                tags=user_memory.metadata.tags + ["preferences_updated"],
                keywords=user_memory.metadata.keywords + ["偏好更新"]
            )
            
            return {
                "success": success,
                "user_name": user_name,
                "updated_preferences": preferences,
                "message": f"用户 '{user_name}' 偏好设置更新成功" if success else "更新失败"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "更新用户偏好失败"
            }
    
    @local_method(memory=memory_enabled(tags=["user_service", "query"]))
    async def get_user_profile(self, user_name: str) -> Dict[str, Any]:
        """
        获取用户档案信息
        
        Args:
            user_name: 用户名
        
        Returns:
            用户档案信息
        """
        try:
            # 搜索用户档案记忆
            memories = await self.custom_manager.search_custom_memories(
                template_name="user_profile_template",
                content_query={"name": user_name}
            )
            
            if not memories:
                return {
                    "success": False,
                    "message": f"未找到用户 '{user_name}' 的档案"
                }
            
            user_memory = memories[0]
            user_data = user_memory.content["custom_data"]
            
            return {
                "success": True,
                "user_data": user_data,
                "memory_info": {
                    "memory_id": user_memory.id,
                    "created_at": user_memory.created_at.isoformat(),
                    "updated_at": user_memory.updated_at.isoformat(),
                    "tags": user_memory.metadata.tags,
                    "keywords": user_memory.metadata.keywords
                },
                "message": f"成功获取用户 '{user_name}' 的档案信息"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取用户档案失败"
            }


class ProjectManager:
    """项目管理器示例 - 演示任务管理功能"""
    
    def __init__(self):
        self.custom_manager = get_custom_memory_manager()
    
    @local_method(memory=memory_enabled(tags=["project", "task_management"]))
    async def create_project_task(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目任务"""
        try:
            # 确保任务有完整信息
            task_data = {
                "task_name": task_info.get("task_name", "未命名任务"),
                "status": task_info.get("status", "待处理"),
                "priority": task_info.get("priority", 3),
                "assignee": task_info.get("assignee", "未分配"),
                "due_date": task_info.get("due_date", ""),
                "progress": task_info.get("progress", 0.0),
                "description": task_info.get("description", "")
            }
            
            # 创建任务记忆
            memory = await self.custom_manager.create_task(
                task_data=task_data,
                source_agent_did="did:anp:project_manager",
                source_agent_name="ProjectManager",
                session_id=task_info.get("project_id", "default_project"),
                tags=["project_task", task_data["status"]],
                keywords=["任务管理", "项目"]
            )
            
            return {
                "success": True,
                "task_id": memory.id,
                "task_name": task_data["task_name"],
                "message": f"任务 '{task_data['task_name']}' 创建成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "创建任务失败"
            }
    
    @local_method(memory=memory_enabled(tags=["project", "task_update"]))
    async def update_task_progress(
        self, 
        task_id: str, 
        progress: float, 
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新任务进度"""
        try:
            # 获取任务记忆
            task_memory = await self.custom_manager.get_custom_memory(task_id)
            if not task_memory:
                return {
                    "success": False,
                    "message": f"未找到任务ID: {task_id}"
                }
            
            # 更新任务数据
            task_data = task_memory.content["custom_data"]
            task_data["progress"] = max(0.0, min(1.0, progress))  # 确保进度在0-1范围内
            
            if status:
                task_data["status"] = status
            
            # 根据进度自动更新状态
            if progress >= 1.0 and not status:
                task_data["status"] = "已完成"
            elif progress > 0 and task_data["status"] == "待处理":
                task_data["status"] = "进行中"
            
            # 保存更新
            success = await self.custom_manager.update_custom_memory(
                memory_id=task_id,
                content=task_data,
                tags=task_memory.metadata.tags + ["progress_updated"],
                keywords=task_memory.metadata.keywords + ["进度更新"]
            )
            
            return {
                "success": success,
                "task_id": task_id,
                "task_name": task_data["task_name"],
                "progress": task_data["progress"],
                "status": task_data["status"],
                "message": f"任务进度更新成功: {progress*100:.1f}%"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "更新任务进度失败"
            }
    
    @local_method(memory=memory_enabled(tags=["project", "reporting"]))
    async def get_project_report(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """生成项目报告"""
        try:
            # 搜索项目任务
            if project_id:
                tasks = await self.custom_manager.search_custom_memories(
                    template_name="task_template",
                    session_id=project_id
                )
            else:
                tasks = await self.custom_manager.search_custom_memories(
                    template_name="task_template"
                )
            
            if not tasks:
                return {
                    "success": False,
                    "message": "未找到任何任务记录"
                }
            
            # 统计任务状态
            status_counts = {}
            progress_sum = 0
            total_tasks = len(tasks)
            
            for task_memory in tasks:
                task_data = task_memory.content["custom_data"]
                status = task_data.get("status", "未知")
                progress = task_data.get("progress", 0)
                
                status_counts[status] = status_counts.get(status, 0) + 1
                progress_sum += progress
            
            avg_progress = progress_sum / total_tasks if total_tasks > 0 else 0
            
            return {
                "success": True,
                "project_id": project_id or "all_projects",
                "total_tasks": total_tasks,
                "status_distribution": status_counts,
                "average_progress": avg_progress,
                "completion_rate": avg_progress * 100,
                "message": f"项目报告生成成功，共 {total_tasks} 个任务"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "生成项目报告失败"
            }


async def mcp_tools_example():
    """MCP工具使用示例"""
    print("=== MCP工具使用示例 ===\n")
    
    # 获取MCP工具
    mcp_tools = get_custom_memory_mcp_tools()
    
    # 1. 使用MCP工具创建模板
    print("1. 使用MCP工具创建自定义模板")
    schema_definition = {
        "fields": {
            "event_name": {"type": "str", "description": "事件名称"},
            "event_type": {"type": "str", "description": "事件类型"},
            "severity": {"type": "str", "description": "严重程度", 
                        "enum": ["low", "medium", "high", "critical"]},
            "timestamp": {"type": "str", "description": "事件时间"},
            "data": {"type": "dict", "description": "事件数据"},
            "resolved": {"type": "bool", "description": "是否已解决"}
        },
        "required_fields": ["event_name", "event_type", "severity", "timestamp"],
        "description": "系统事件记录模式"
    }
    
    template_result = await mcp_tools.create_memory_template(
        name="system_event_template",
        schema_definition=schema_definition,
        description="系统事件记录模板",
        default_tags=["system", "event", "monitoring"],
        default_keywords=["系统事件", "监控", "日志"]
    )
    
    print(f"✓ MCP创建模板结果: {template_result['success']}")
    if template_result["success"]:
        print(f"  模板ID: {template_result['template_id']}")
        print(f"  消息: {template_result['message']}\n")
    
    # 2. 使用MCP工具创建记忆
    if template_result["success"]:
        print("2. 使用MCP工具创建系统事件记忆")
        event_content = {
            "event_name": "数据库连接失败",
            "event_type": "database_error",
            "severity": "high",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "database": "user_db",
                "error_code": "CONNECTION_TIMEOUT",
                "retry_count": 3
            },
            "resolved": False
        }
        
        memory_result = await mcp_tools.create_custom_memory(
            template_id=template_result["template_id"],
            content=event_content,
            source_agent_did="did:anp:monitoring_system",
            source_agent_name="MonitoringSystem",
            title="系统事件-数据库连接失败",
            tags=["error", "database"],
            keywords=["连接失败", "高优先级"]
        )
        
        print(f"✓ MCP创建记忆结果: {memory_result['success']}")
        if memory_result["success"]:
            print(f"  记忆ID: {memory_result['memory_id']}")
            print(f"  消息: {memory_result['message']}\n")
    
    # 3. 使用MCP工具搜索记忆
    print("3. 使用MCP工具搜索系统事件")
    search_result = await mcp_tools.search_custom_memories(
        template_name="system_event_template",
        content_query={"severity": "high"},
        limit=10
    )
    
    print(f"✓ MCP搜索结果: {search_result['success']}")
    if search_result["success"]:
        print(f"  找到记忆数量: {search_result['count']}")
        for memory_data in search_result["memories"]:
            event_data = memory_data["content"]["custom_data"]
            print(f"  - {event_data['event_name']} ({event_data['severity']})")
        print()
    
    # 4. 使用MCP工具获取统计信息
    print("4. 使用MCP工具获取系统统计")
    stats_result = await mcp_tools.get_statistics()
    
    print(f"✓ MCP统计结果: {stats_result['success']}")
    if stats_result["success"]:
        stats = stats_result["statistics"]
        print(f"  总模板数: {stats['total_templates']}")
        print(f"  总自定义记忆数: {stats['total_custom_memories']}")
        print(f"  模板使用情况: {stats['template_usage']}")
        print()


async def integrated_workflow_example():
    """集成工作流示例"""
    print("=== 集成工作流示例 ===\n")
    
    # 初始化服务
    user_service = UserService()
    project_manager = ProjectManager()
    
    # 1. 创建用户档案
    print("1. 创建用户档案")
    user_data = {
        "name": "王五",
        "email": "wangwu@example.com",
        "age": 30,
        "preferences": {
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
            "theme": "dark"
        }
    }
    
    user_result = await user_service.create_user_profile(user_data)
    print(f"✓ {user_result['message']}")
    if user_result["success"]:
        print(f"  用户ID: {user_result['user_id']}")
        print(f"  记忆ID: {user_result['memory_id']}\n")
    
    # 2. 创建项目任务
    print("2. 创建项目任务")
    tasks = [
        {
            "task_name": "用户需求分析",
            "status": "已完成",
            "priority": 4,
            "assignee": "王五",
            "progress": 1.0,
            "project_id": "project_alpha"
        },
        {
            "task_name": "系统设计",
            "status": "进行中",
            "priority": 5,
            "assignee": "王五",
            "progress": 0.6,
            "project_id": "project_alpha"
        },
        {
            "task_name": "代码实现",
            "status": "待处理",
            "priority": 4,
            "assignee": "王五",
            "progress": 0.0,
            "project_id": "project_alpha"
        }
    ]
    
    task_ids = []
    for task_info in tasks:
        task_result = await project_manager.create_project_task(task_info)
        print(f"✓ {task_result['message']}")
        if task_result["success"]:
            task_ids.append(task_result["task_id"])
    print()
    
    # 3. 更新任务进度
    print("3. 更新任务进度")
    if len(task_ids) >= 2:
        # 更新第二个任务的进度
        progress_result = await project_manager.update_task_progress(
            task_id=task_ids[1],
            progress=0.8,
            status="进行中"
        )
        print(f"✓ {progress_result['message']}")
        
        # 更新第三个任务的进度
        progress_result = await project_manager.update_task_progress(
            task_id=task_ids[2],
            progress=0.3,
            status="进行中"
        )
        print(f"✓ {progress_result['message']}")
        print()
    
    # 4. 更新用户偏好
    print("4. 更新用户偏好")
    new_preferences = {
        "theme": "light",
        "notifications": True,
        "auto_save": True
    }
    
    pref_result = await user_service.update_user_preferences("王五", new_preferences)
    print(f"✓ {pref_result['message']}")
    if pref_result["success"]:
        print(f"  更新的偏好: {pref_result['updated_preferences']}\n")
    
    # 5. 获取用户档案
    print("5. 获取更新后的用户档案")
    profile_result = await user_service.get_user_profile("王五")
    if profile_result["success"]:
        user_data = profile_result["user_data"]
        print(f"✓ 用户: {user_data['name']} ({user_data['email']})")
        print(f"  偏好设置: {user_data['preferences']}")
        print(f"  记忆信息: {profile_result['memory_info']['tags']}\n")
    
    # 6. 生成项目报告
    print("6. 生成项目报告")
    report_result = await project_manager.get_project_report("project_alpha")
    if report_result["success"]:
        print(f"✓ {report_result['message']}")
        print(f"  总任务数: {report_result['total_tasks']}")
        print(f"  状态分布: {report_result['status_distribution']}")
        print(f"  平均进度: {report_result['average_progress']:.2f}")
        print(f"  完成率: {report_result['completion_rate']:.1f}%\n")


async def main():
    """主函数"""
    try:
        await mcp_tools_example()
        await integrated_workflow_example()
        
        print("=== 高级示例运行完成 ===")
        print("已演示自定义Memory在装饰器中的集成使用和MCP工具！")
        
    except Exception as e:
        print(f"❌ 运行高级示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())