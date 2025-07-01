import logging
from typing import Dict, Any, List, Optional
from .unified_caller import UnifiedCaller

logger = logging.getLogger(__name__)


class UnifiedCrawler:
    """
    统一爬虫 - 整合资源发现和智能调用
    
    功能:
    1. 统一的资源发现 (本地方法、远程智能体、API端点)
    2. 智能方法匹配和调用 (支持LLM增强)
    3. 资源搜索和管理
    """
    
    def __init__(self, sdk, llm_config=None):
        self.sdk = sdk
        self.unified_caller = UnifiedCaller(sdk)
        self.discovered_resources = {}

        # 初始化LLM匹配器（可选）
        self.llm_matcher = self._init_llm_matcher(llm_config)
        
        # 初始化资源发现器
        self.discoverers = {
            'local_methods': self._discover_local_methods,
            'remote_agents': self._discover_remote_agents,
            'api_endpoints': self._discover_api_endpoints
        }

        logger.info("🔧 UnifiedCrawler 初始化完成")
    
    def _init_llm_matcher(self, llm_config):
        """初始化LLM匹配器"""
        if not llm_config:
            logger.info("🤖 未配置LLM，使用传统匹配方法")
            return None
        
        try:
            from .llm_matcher import LLMResourceMatcher, LLMClientFactory
            
            llm_type = llm_config.get('type', 'openai')
            
            if llm_type == 'openai':
                client = LLMClientFactory.create_openai_client(
                    api_key=llm_config.get('api_key'),
                    base_url=llm_config.get('base_url')
                )
            elif llm_type == 'anthropic':
                client = LLMClientFactory.create_anthropic_client(
                    api_key=llm_config.get('api_key')
                )
            elif llm_type == 'local':
                client = LLMClientFactory.create_local_client(
                    base_url=llm_config.get('base_url'),
                    model_name=llm_config.get('model_name')
                )
            else:
                logger.warning(f"⚠️ 不支持的LLM类型: {llm_type}")
                client = None
            
            logger.info(f"✅ LLM匹配器初始化成功: {llm_type}")
            return LLMResourceMatcher(client)
            
        except ImportError:
            logger.warning("⚠️ LLM匹配器模块未找到，使用传统匹配方法")
            return None
        except Exception as e:
            logger.error(f"❌ 初始化LLM匹配器失败: {e}")
            return None
    
    async def _discover_local_methods(self):
        """发现本地方法资源"""
        try:
            from .local_methods.local_methods_caller import LocalMethodsCaller
            
            caller = LocalMethodsCaller(self.sdk)
            methods = caller.list_all_methods()

            resources = {}
            for method_key, method_info in methods.items():
                resources[method_key] = {
                    'type': 'local_method',
                    'key': method_key,
                    'name': method_info.get('name', 'unknown'),
                    'agent_name': method_info.get('agent_name', 'unknown'),
                    'description': method_info.get('description', ''),
                    'tags': method_info.get('tags', []),
                    'signature': method_info.get('signature', ''),
                    'parameters': method_info.get('parameters', []),
                    'is_async': method_info.get('is_async', False)
                }
            
            logger.info(f"✅ 发现 {len(resources)} 个本地方法")
            return resources
    
        except Exception as e:
            logger.error(f"❌ 发现 local_methods 资源时出错: {e}")
            return {}

    async def _discover_remote_agents(self):
        """发现远程智能体资源"""
        try:
            # 这里可以实现远程智能体发现逻辑
            # 暂时返回空字典，后续可以扩展
            logger.info("🔍 远程智能体发现功能待实现")
            return {}
            
        except Exception as e:
            logger.error(f"❌ 发现 remote_agents 资源时出错: {e}")
            return {}

    async def _discover_api_endpoints(self):
        """发现API端点资源"""
        try:
            # 这里可以实现API端点发现逻辑
            # 暂时返回空字典，后续可以扩展
            logger.info("🔍 API端点发现功能待实现")
            return {}
            
        except Exception as e:
            logger.error(f"❌ 发现 api_endpoints 资源时出错: {e}")
            return {}

    async def discover_all_resources(self):
        """发现所有可用资源"""
        logger.info("🔍 开始发现所有可用资源...")
        
        all_resources = {}
        
        for resource_type, discoverer in self.discoverers.items():
            logger.info(f"  - 发现 {resource_type} 资源...")
            try:
                resources = await discoverer()
                all_resources[resource_type] = resources
                logger.info(f"    ✅ 发现 {len(resources)} 个 {resource_type} 资源")
            except Exception as e:
                logger.error(f"    ❌ 发现 {resource_type} 资源失败: {e}")
                all_resources[resource_type] = {}

        self.discovered_resources = all_resources
        total_count = self._count_total_resources()
        logger.info(f"🎯 资源发现完成，总计发现 {total_count} 个资源")
        return all_resources

    def _count_total_resources(self):
        """计算总资源数量"""
        total = 0
        for resource_type, resources in self.discovered_resources.items():
            total += len(resources)
        return total
        
    def get_resource_summary(self):
        """获取资源摘要"""
        if not self.discovered_resources:
            return "尚未发现任何资源，请先调用 discover_all_resources()"
        
        summary_lines = ["📊 资源摘要:"]
        total_resources = 0
        
        for resource_type, resources in self.discovered_resources.items():
            count = len(resources)
            total_resources += count
            summary_lines.append(f"  - {resource_type}: {count} 个")

            # 显示前几个资源的名称作为示例
            if count > 0:
                examples = list(resources.keys())[:3]
                if len(examples) < count:
                    examples.append("...")
                summary_lines.append(f"    例如: {', '.join(examples)}")

        summary_lines.append(f"📈 总计: {total_resources} 个资源")
        return "\n".join(summary_lines)

    async def search_resources(self, keyword, resource_types=None):
        """
        改进的资源搜索方法
        支持同义词和模糊匹配
        """
        if not self.discovered_resources:
            await self.discover_all_resources()

        keyword_lower = keyword.lower()
        results = {}

        search_types = resource_types or self.discovered_resources.keys()
        
        # 特殊处理 - 如果是"所有"或"全部"，返回所有资源
        if any(word in keyword_lower for word in ['所有', '全部', 'all', '列表', 'list']):
            logger.info(f"🔍 检测到'所有'关键词，返回所有资源")
            for resource_type in search_types:
                if resource_type in self.discovered_resources:
                    resources = self.discovered_resources[resource_type]
                    if resources:
                        results[resource_type] = resources
        else:
            # 正常搜索
            for resource_type in search_types:
                if resource_type not in self.discovered_resources:
                    continue
            
                type_results = {}
                resources = self.discovered_resources[resource_type]

                for resource_key, resource_info in resources.items():
                    # 搜索匹配逻辑
                    if self._matches_keyword(resource_info, keyword_lower):
                        type_results[resource_key] = resource_info

                if type_results:
                    results[resource_type] = type_results
        
        total_results = sum(len(r) for r in results.values())
        logger.info(f"🔍 搜索关键词 '{keyword}' 找到 {total_results} 个结果")
        
        # 如果没有找到结果，尝试模糊搜索
        if total_results == 0:
            logger.info("🔍 尝试模糊搜索...")
            results = await self._fuzzy_search(keyword_lower, search_types)
        
        return results

    def _matches_keyword(self, resource_info, keyword_lower):
        """
        改进的关键词匹配算法
        支持更智能的语义匹配
        """
        # 基础搜索字段
        searchable_fields = [
            resource_info.get('name', ''),
            resource_info.get('description', ''),
            resource_info.get('agent_name', ''),
        ]
        
        # 搜索标签
        tags = resource_info.get('tags', [])
        searchable_fields.extend(tags)
        
        # 同义词映射
        synonym_map = {
            # 计算相关
            '计算': ['calculate', 'compute', 'sum', 'add', 'math'],
            '加法': ['add', 'sum', 'calculate', 'plus'],
            '求和': ['sum', 'add', 'calculate', 'total'],
            '数学': ['math', 'calculate', 'compute'],
            '功能': ['method', 'function', 'feature'],
            '所有': ['all', 'list', 'show'],
            
            # 英文到中文
            'calculate': ['计算', '求和', '加法'],
            'sum': ['求和', '加法', '计算'],
            'add': ['加法', '求和', '计算'],
            'math': ['数学', '计算'],
            'demo': ['演示', '示例', '测试'],
        }
        
        # 分词处理 - 将关键词分解为更小的部分
        keywords_to_check = [keyword_lower]
        
        # 添加同义词
        for word in keyword_lower.split():
            if word in synonym_map:
                keywords_to_check.extend(synonym_map[word])
        
        # 检查是否有任何字段包含关键词或同义词
        for keyword in keywords_to_check:
            for field in searchable_fields:
                field_str = str(field).lower()
                if keyword in field_str:
                    return True
                
                # 反向检查 - 字段中的词是否在关键词中
                for field_word in field_str.split():
                    if field_word in synonym_map:
                        for synonym in synonym_map[field_word]:
                            if synonym in keyword_lower:
                                return True
        
        return False

    async def _fuzzy_search(self, keyword_lower, search_types):
        """模糊搜索 - 当精确搜索失败时使用"""
        results = {}
        
        # 提取关键词中的重要部分
        important_words = []
        for word in keyword_lower.split():
            if len(word) > 1 and word not in ['的', '和', '与', 'and', 'or', 'the']:
                important_words.append(word)
        
        if not important_words:
            return results
        
        for resource_type in search_types:
            if resource_type not in self.discovered_resources:
                continue
                
            type_results = {}
            resources = self.discovered_resources[resource_type]
            
            for resource_key, resource_info in resources.items():
                # 计算匹配分数
                score = self._calculate_match_score(resource_info, important_words)
                if score > 0:
                    resource_info_copy = resource_info.copy()
                    resource_info_copy['_match_score'] = score
                    type_results[resource_key] = resource_info_copy
            
            if type_results:
                # 按匹配分数排序
                sorted_results = dict(sorted(
                    type_results.items(), 
                    key=lambda x: x[1].get('_match_score', 0), 
                    reverse=True
                ))
                results[resource_type] = sorted_results
        
        total_results = sum(len(r) for r in results.values())
        if total_results > 0:
            logger.info(f"🎯 模糊搜索找到 {total_results} 个结果")
        
        return results
    
    def _calculate_match_score(self, resource_info, keywords):
        """计算匹配分数"""
        score = 0
        
        searchable_content = ' '.join([
            resource_info.get('name', ''),
            resource_info.get('description', ''),
            resource_info.get('agent_name', ''),
            ' '.join(resource_info.get('tags', []))
        ]).lower()
        
        for keyword in keywords:
            if keyword in searchable_content:
                score += 10
                
            # 部分匹配
            for word in searchable_content.split():
                if keyword in word or word in keyword:
                    score += 5
        
        return score

    async def intelligent_call(self, description, **kwargs):
        """
        智能调用 - 根据描述找到最佳匹配的资源并调用
        支持LLM增强匹配（如果配置了LLM）
        """
        logger.info(f"🤖 智能调用: {description}")

        # 确保已发现资源
        if not self.discovered_resources:
            await self.discover_all_resources()

        # 如果配置了LLM，优先使用LLM匹配
        if self.llm_matcher:
            try:
                logger.info("🧠 使用LLM进行智能匹配...")
                match_result = await self.llm_matcher.match_resources(description, self.discovered_resources)
                
                if match_result.get('success'):
                    # 获取匹配的资源
                    resource_type, resource_key, resource_info = match_result['matched_resource']
                    confidence = match_result['confidence']
                    reason = match_result['reason']
                    suggested_params = match_result.get('suggested_parameters', {})
                    
                    logger.info(f"🎯 LLM选择最佳匹配: {resource_type}.{resource_key} (置信度: {confidence:.2f})")
                    logger.info(f"📝 匹配原因: {reason}")
                    
                    # 合并用户参数和LLM建议的参数
                    final_kwargs = suggested_params.copy()
                    final_kwargs.update(kwargs)  # 用户参数优先级更高
                    
                    # 调用匹配的资源
                    if resource_type == 'local_methods':
                        result = await self._call_local_method(resource_key, resource_info, **final_kwargs)
                        # 添加LLM分析信息
                        result['llm_analysis'] = match_result.get('llm_analysis', {})
                        result['confidence'] = confidence
                        result['match_reason'] = reason
                        return result
                    elif resource_type == 'remote_agents':
                        return await self._call_remote_agent(resource_key, resource_info, **final_kwargs)
                    elif resource_type == 'api_endpoints':
                        return await self._call_api_endpoint(resource_key, resource_info, **final_kwargs)
                else:
                    logger.warning("🔄 LLM匹配失败，降级到传统搜索")
            except Exception as e:
                logger.error(f"❌ LLM智能调用失败: {e}")
                logger.info("🔄 降级到传统搜索方法")

        # 传统搜索方法
        search_results = await self.search_resources(description)

        if not search_results:
            raise ValueError(f"未找到与描述 '{description}' 匹配的资源")

        # 选择最佳匹配（优先选择本地方法）
        best_match = self._select_best_match(search_results, description)

        if not best_match:
            raise ValueError(f"无法确定最佳匹配的资源")

        resource_type, resource_key, resource_info = best_match
        logger.info(f"🎯 传统方法选择最佳匹配: {resource_type}.{resource_key}")

        # 根据资源类型调用相应的方法
        if resource_type == 'local_methods':
            return await self._call_local_method(resource_key, resource_info, **kwargs)
        elif resource_type == 'remote_agents':
            return await self._call_remote_agent(resource_key, resource_info, **kwargs)
        elif resource_type == 'api_endpoints':
            return await self._call_api_endpoint(resource_key, resource_info, **kwargs)
        else:
            raise ValueError(f"不支持的资源类型: {resource_type}")

    def _select_best_match(self, search_results, description):
        """选择最佳匹配的资源"""
        # 优先级: local_methods > remote_agents > api_endpoints
        priority_order = ['local_methods', 'remote_agents', 'api_endpoints']
        
        for resource_type in priority_order:
            if resource_type in search_results:
                resources = search_results[resource_type]
                if resources:
                    # 如果有匹配分数，选择分数最高的
                    if any('_match_score' in info for info in resources.values()):
                        best_key = max(resources.keys(), key=lambda k: resources[k].get('_match_score', 0))
                        return resource_type, best_key, resources[best_key]
                    else:
                        # 选择第一个匹配的资源
                        resource_key = next(iter(resources.keys()))
                        resource_info = resources[resource_key]
                        return resource_type, resource_key, resource_info
        
        return None

    async def _call_local_method(self, method_key, method_info, **kwargs):
        """调用本地方法"""
        try:
            from .local_methods.local_methods_caller import LocalMethodsCaller
            
            caller = LocalMethodsCaller(self.sdk)
            
            # 提取位置参数和关键字参数
            args = kwargs.pop('args', [])
            
            logger.info(f"📞 调用本地方法: {method_key}")
            logger.info(f"📋 参数: args={args}, kwargs={kwargs}")
            
            result = await caller.call_method_by_key(method_key, *args, **kwargs)
            
            return {
                'success': True,
                'result': result,
                'method_key': method_key,
                'method_info': method_info,
                'call_type': 'local_method'
            }
            
        except Exception as e:
            logger.error(f"❌ 调用本地方法失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'method_key': method_key,
                'call_type': 'local_method'
            }

    async def _call_remote_agent(self, agent_key, agent_info, **kwargs):
        """调用远程智能体"""
        # 待实现
        logger.warning("🚧 远程智能体调用功能待实现")
        return {
            'success': False,
            'error': '远程智能体调用功能待实现',
            'agent_key': agent_key,
            'call_type': 'remote_agent'
        }

    async def _call_api_endpoint(self, endpoint_key, endpoint_info, **kwargs):
        """调用API端点"""
        # 待实现
        logger.warning("🚧 API端点调用功能待实现")
        return {
            'success': False,
            'error': 'API端点调用功能待实现',
            'endpoint_key': endpoint_key,
            'call_type': 'api_endpoint'
        }

    async def call_by_name(self, name, **kwargs):
        """根据名称直接调用资源"""
        logger.info(f"🎯 根据名称调用: {name}")
        
        # 确保已发现资源
        if not self.discovered_resources:
            await self.discover_all_resources()
        
        # 在所有资源中查找匹配的名称
        for resource_type, resources in self.discovered_resources.items():
            for resource_key, resource_info in resources.items():
                if (resource_info.get('name') == name or
                    resource_key == name or
                    name in resource_info.get('name', '')):
                    
                    logger.info(f"🎯 找到匹配资源: {resource_type}.{resource_key}")
                    
                    if resource_type == 'local_methods':
                        return await self._call_local_method(resource_key, resource_info, **kwargs)
                    elif resource_type == 'remote_agents':
                        return await self._call_remote_agent(resource_key, resource_info, **kwargs)
                    elif resource_type == 'api_endpoints':
                        return await self._call_api_endpoint(resource_key, resource_info, **kwargs)
        
        raise ValueError(f"未找到名称为 '{name}' 的资源")


# 为了向后兼容，可以添加一些别名
LocalMethodsDiscoverer = UnifiedCrawler  # 别名，用于向后兼容