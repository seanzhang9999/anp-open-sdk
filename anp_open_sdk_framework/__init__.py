"""
ANP Open SDK Framework - 统一的多智能体调用框架

提供统一的调用接口、智能爬虫和主智能体功能
"""

# 版本信息
__version__ = "1.0.0"

# 核心组件导入
from .unified_caller import UnifiedCaller
from .unified_crawler import UnifiedCrawler
from .master_agent import MasterAgent

# 智能体管理 - 延迟导入以避免循环依赖
# from .agent_manager import LocalAgentManager

# 本地方法相关
from .local_methods.local_methods_caller import LocalMethodsCaller
from .local_methods.local_methods_doc import LocalMethodsDocGenerator
from .local_methods.local_methods_decorators import local_method, register_local_methods_to_agent

# 服务层组件（从 anp_open_sdk 迁移） - 延迟导入以避免循环依赖
# from .service.router.router_agent import AgentRouter, wrap_business_handler
# from .service.interaction.anp_tool import ANPTool, ANPToolCrawler
# from .service.publisher.anp_sdk_publisher import ANPSDKPublisher

# 导出的主要类和函数
__all__ = [
    # 核心组件
    'UnifiedCaller',
    'UnifiedCrawler', 
    'MasterAgent',
    
    # 智能体管理 - 注释掉以避免循环导入
    # 'LocalAgentManager',
    
    # 本地方法
    'LocalMethodsCaller',
    'LocalMethodsDocGenerator',
    'local_method',
    'register_local_methods_to_agent',
    
    # 服务层组件 - 注释掉以避免循环导入
    # 'AgentRouter',
    # 'wrap_business_handler',
    # 'ANPTool',
    # 'ANPToolCrawler',
    # 'ANPSDKPublisher',
]

# 框架信息
FRAMEWORK_INFO = {
    'name': 'ANP Open SDK Framework',
    'version': __version__,
    'description': '统一的多智能体调用框架',
    'components': {
        'UnifiedCaller': '统一调用器 - 合并本地方法和远程API调用',
        'UnifiedCrawler': '统一爬虫 - 整合资源发现和智能调用',
        'MasterAgent': '主智能体 - 提供任务级别的统一调度',
        # 'LocalAgentManager': '本地智能体管理器',
        'AgentRouter': '智能体路由器 - 管理多智能体请求路由',
        'ANPTool': 'ANP工具 - 代理网络协议交互工具',
        'ANPSDKPublisher': 'ANP发布器 - DID发布和注册服务',
    }
}

def get_local_agent_manager():
    """延迟导入 LocalAgentManager 以避免循环依赖"""
    from .agent_manager import LocalAgentManager
    return LocalAgentManager

def get_agent_router():
    """延迟导入 AgentRouter 以避免循环依赖"""
    from .service.router.router_agent import AgentRouter, wrap_business_handler
    return AgentRouter, wrap_business_handler

def get_anp_tool():
    """延迟导入 ANPTool 以避免循环依赖"""
    from .service.interaction.anp_tool import ANPTool, ANPToolCrawler
    return ANPTool, ANPToolCrawler

def get_anp_sdk_publisher():
    """延迟导入 ANPSDKPublisher 以避免循环依赖"""
    from .service.publisher.anp_sdk_publisher import ANPSDKPublisher
    return ANPSDKPublisher

def get_framework_info():
    """获取框架信息"""
    return FRAMEWORK_INFO

def show_framework_info():
    """显示框架信息"""
    info = get_framework_info()
    print(f"\n🤖 {info['name']} v{info['version']}")
    print(f"📝 {info['description']}\n")
    
    print("🔧 核心组件:")
    for component, description in info['components'].items():
        print(f"  • {component}: {description}")
    
    print(f"\n📚 使用示例:")
    print("  from anp_open_sdk_framework import UnifiedCaller, UnifiedCrawler, MasterAgent")
    print("  # 详见 MIGRATION_GUIDE.md")

# 便捷的创建函数
def create_unified_caller(sdk):
    """创建统一调用器实例"""
    return UnifiedCaller(sdk)

def create_unified_crawler(sdk):
    """创建统一爬虫实例"""
    return UnifiedCrawler(sdk)

def create_master_agent(sdk, name="MasterAgent"):
    """创建主智能体实例"""
    return MasterAgent(sdk, name=name)

# 添加到导出列表
__all__.extend([
    'get_framework_info',
    'show_framework_info', 
    'create_unified_caller',
    'create_unified_crawler',
    'create_master_agent',
])