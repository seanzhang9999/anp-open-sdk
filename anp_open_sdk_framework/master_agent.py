import logging
import re
from typing import Dict, Any, Optional, List
from .unified_crawler import UnifiedCrawler
logger = logging.getLogger(__name__)


class MasterAgent:
    """
    主智能体 - 提供任务级别的统一调度

    功能:
    1. 自然语言任务理解
    2. 智能资源匹配和调用
    3. 任务执行和结果管理
    """

    def __init__(self, sdk, name="MasterAgent", llm_config=None):
        self.sdk = sdk
        self.name = name
        self.llm_config = llm_config
        self.unified_crawler = None
        self.task_counter = 0

        logger.info(f"🤖 {self.name} 初始化完成")

    async def initialize(self):
        """初始化主智能体"""
        logger.info(f"🔧 初始化 {self.name}...")

        # 创建统一爬虫实例（传递LLM配置）
        self.unified_crawler = UnifiedCrawler(self.sdk, llm_config=self.llm_config)

        # 发现所有可用资源
        await self.unified_crawler.discover_all_resources()

        logger.info(f"✅ {self.name} 初始化完成")

    async def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task_description: 任务描述
            context: 任务上下文

        Returns:
            任务执行结果
        """
        self.task_counter += 1
        task_id = self.task_counter

        logger.info(f"📋 接收任务: {task_description}")
        try:
            # 分析任务类型
            task_type = self._analyze_task_type(task_description)

            if task_type == "search":
                # 搜索类任务
                result = await self._handle_search_task(task_description, context)
            elif task_type == "call":
                # 调用类任务
                result = await self._handle_call_task(task_description, context)
            else:
                # 通用智能调用
                result = await self._handle_intelligent_task(task_description, context)

            logger.info(f"✅ 任务完成: {task_description}")
            return {
                "task_id": task_id,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ 任务失败: {task_description}, 错误: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    def _analyze_task_type(self, task_description: str) -> str:
        """分析任务类型"""
        task_lower = task_description.lower()

        # 搜索类关键词
        search_keywords = ['查找', '搜索', '列表', '显示', '所有', '全部', 'search', 'find', 'list', 'show', 'all']
        if any(keyword in task_lower for keyword in search_keywords):
            return "search"

        # 调用类关键词
        call_keywords = ['调用', '执行', '运行', 'call', 'execute', 'run']
        if any(keyword in task_lower for keyword in call_keywords):
            return "call"

        # 默认为智能调用
        return "intelligent"
    
    async def _handle_search_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理搜索类任务"""
        logger.info(f"🔍 处理搜索任务: {task_description}")

        # 提取搜索关键词
        search_keyword = self._extract_search_keyword(task_description)

        # 执行搜索
        search_results = await self.unified_crawler.search_resources(search_keyword)

        return {
            "type": "search_results",
            "keyword": search_keyword,
            "results": search_results
        }
    
    def _extract_search_keyword(self, task_description: str) -> str:
        """从任务描述中提取搜索关键词"""
        # 移除常见的动作词
        action_words = ['查找', '搜索', '显示', '获取', '所有', '全部', 'search', 'find', 'show', 'all', 'list']

        clean_description = task_description
        for word in action_words:
            clean_description = clean_description.replace(word, '').strip()

        # 如果清理后为空，使用原描述
        if not clean_description:
            clean_description = task_description

        return clean_description

    async def _handle_call_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理调用类任务"""
        logger.info(f"📞 处理调用任务: {task_description}")

        # 提取任务信息
        task_info = self._extract_task_info(task_description, context)
        method_name = task_info['method_name']
        method_args = task_info['method_args']

        # 使用智能调用而不是按名称调用
        try:
            # 首先尝试智能调用
            result = await self.unified_crawler.intelligent_call(method_name, **method_args)
            return result
        except Exception as e:
            logger.warning(f"⚠️ 智能调用失败: {e}")

            # 如果智能调用失败，尝试按名称调用
            try:
                result = await self.unified_crawler.call_by_name(method_name, **method_args)
                return result
            except Exception as e2:
                logger.error(f"❌ 按名称调用也失败: {e2}")

                # 最后尝试使用原始任务描述进行智能调用
                result = await self.unified_crawler.intelligent_call(task_description, **method_args)
                return result

    async def _handle_intelligent_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理智能任务（通用）"""
        logger.info(f"🧠 处理智能任务: {task_description}")

        # 合并上下文参数
        kwargs = {}
        if context:
            kwargs.update(context)

        # 直接使用智能调用
        result = await self.unified_crawler.intelligent_call(task_description, **kwargs)
        return result

    def _extract_task_info(self, task_description, context=None):
        """
        从任务描述中提取关键信息
        改进版本，支持更好的自然语言理解
        """
        task_lower = task_description.lower()
        context = context or {}

        # 提取方法名的模式
        method_patterns = [
            # 直接方法名匹配
            r'调用\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*方法',
            r'执行\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*方法',
            r'运行\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*方法',
        ]

        extracted_method = None
        for pattern in method_patterns:
            match = re.search(pattern, task_lower)
            if match:
                extracted_method = match.group(1)
                break

        # 如果没有找到具体方法名，进行语义分析
        if not extracted_method:
            # 功能关键词映射 - 改进版本
            function_keywords = {
                # 计算相关 - 使用更通用的描述
                '计算': ['计算', '求和', '加法', '数学', 'calculate', 'sum', 'add', 'math'],
                '加法': ['加法', '求和', '计算', 'add', 'sum', 'calculate'],
                '求和': ['求和', '加法', '计算', 'sum', 'add', 'calculate'],
                'demo': ['演示', '示例', '测试', 'demo', 'test'],
                'info': ['信息', '详情', '查看', 'info', 'detail'],
                'list': ['列表', '所有', '全部', '查找', 'list', 'all', 'find'],
            }

            # 查找匹配的功能关键词
            for func_name, keywords in function_keywords.items():
                if any(keyword in task_lower for keyword in keywords):
                    extracted_method = func_name
                    break

            # 如果还是没找到，使用整个描述作为搜索关键词
            if not extracted_method:
                # 清理任务描述，但保留更多信息
                clean_description = task_description
                # 只移除明确的动作词
                action_words = ['调用', '执行', '运行']
                for word in action_words:
                    clean_description = clean_description.replace(word, '').strip()
                extracted_method = clean_description

        # 从上下文中提取参数
        method_args = {}
        if isinstance(context, dict):
            method_args.update(context)

        # 从任务描述中提取数字参数
        number_matches = re.findall(r'\d+(?:\.\d+)?', task_description)
        if len(number_matches) >= 2 and not method_args:
            try:
                numbers = [float(n) for n in number_matches[:2]]
                if any(word in task_lower for word in ['计算', 'sum', '加', '求和', 'calculate', '加法']):
                    method_args = {'a': numbers[0], 'b': numbers[1]}
            except ValueError:
                pass

        logger.info(f"📝 任务解析结果: 方法='{extracted_method}', 参数={method_args}")
        return {
            'method_name': extracted_method,
            'method_args': method_args,
            'original_task': task_description
        }

    async def get_available_resources(self) -> Dict[str, Any]:
        """获取所有可用资源"""
        if not self.unified_crawler:
            await self.initialize()

        return self.unified_crawler.discovered_resources

    def get_resource_summary(self) -> str:
        """获取资源摘要"""
        if not self.unified_crawler:
            return "主智能体尚未初始化"

        return self.unified_crawler.get_resource_summary()
