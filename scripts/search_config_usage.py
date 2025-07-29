#!/usr/bin/env python3
"""
搜索 anp-open-sdk-python 中所有使用配置的文件和函数
分析依赖注入改进方案
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ConfigUsageAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.config_usages = []
        self.config_keys_used = set()
        self.files_with_config = set()

    def search_config_usage(self):
        """搜索所有Python文件中的配置使用"""
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                self._analyze_file(py_file, content)
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否跳过文件"""
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}

        # 排除目录
        if any(part in skip_dirs for part in file_path.parts):
            return True

        # 排除当前脚本文件本身
        if file_path.name == 'search_config_usage.py':
            return True

        # 排除其他分析脚本
        if file_path.name.startswith('search_') and file_path.name.endswith('.py'):
            return True

        return False

    def _analyze_file(self, file_path: Path, content: str):
        """分析单个文件中的配置使用"""
        relative_path = file_path.relative_to(self.root_path)
        lines = content.split('\n')

        # 1. 搜索 get_global_config() 调用
        self._find_get_global_config(content, lines, relative_path)

        # 2. 搜索直接的配置属性访问
        self._find_config_attribute_access(content, lines, relative_path)

        # 3. 搜索 getattr(config, ...) 调用
        self._find_getattr_config_access(content, lines, relative_path)

        # 4. 搜索 hasattr(config, ...) 调用
        self._find_hasattr_config_access(content, lines, relative_path)

        # 5. 搜索 setattr(config, ...) 调用
        self._find_setattr_config_access(content, lines, relative_path)

    def _find_get_global_config(self, content: str, lines: List[str], relative_path: Path):
        """查找 get_global_config() 调用"""
        get_config_patterns = [
            r'config\s*=\s*get_global_config\(\)',
            r'get_global_config\(\)',
            r'from\s+.*\s+import\s+.*get_global_config',
            r'import\s+.*get_global_config'
        ]

        for pattern in get_config_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context = self._get_context(lines, line_num - 1)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'get_global_config',
                    'code': lines[line_num - 1].strip(),
                    'context': context,
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1),
                    'pattern_matched': pattern
                }

                self.config_usages.append(usage_info)
                self.files_with_config.add(str(relative_path))

    def _find_config_attribute_access(self, content: str, lines: List[str], relative_path: Path):
        """查找直接的配置属性访问"""
        config_access_patterns = [
            r'config\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'get_global_config\(\)\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]

        for pattern in config_access_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                config_key = match.group(1)
                self.config_keys_used.add(config_key)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'config_attribute_access',
                    'config_key': config_key,
                    'code': lines[line_num - 1].strip(),
                    'context': self._get_context(lines, line_num - 1),
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1),
                    'full_match': match.group(0)
                }

                self.config_usages.append(usage_info)
                self.files_with_config.add(str(relative_path))

    def _find_getattr_config_access(self, content: str, lines: List[str], relative_path: Path):
        """查找 getattr(config, ...) 调用"""
        # 匹配各种 getattr 模式
        getattr_patterns = [
            r'getattr\s*\(\s*config\s*,\s*[\'"]([^\'\"]+)[\'"]',  # getattr(config, "attr_name")
            r'getattr\s*\(\s*config\s*,\s*([a-zA-Z_][a-zA-Z0-9_]*)',  # getattr(config, attr_var)
            r'getattr\s*\(\s*get_global_config\(\)\s*,\s*[\'"]([^\'\"]+)[\'"]',  # getattr(get_global_config(), "attr")
        ]

        for pattern in getattr_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1

                # 尝试提取属性名
                attr_name = match.group(1) if match.group(1) else "dynamic_attribute"
                if attr_name and not attr_name.startswith('_'):  # 忽略私有属性
                    self.config_keys_used.add(attr_name)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'getattr_config_access',
                    'config_key': attr_name,
                    'code': lines[line_num - 1].strip(),
                    'context': self._get_context(lines, line_num - 1),
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1),
                    'full_match': match.group(0)
                }

                self.config_usages.append(usage_info)
                self.files_with_config.add(str(relative_path))

    def _find_hasattr_config_access(self, content: str, lines: List[str], relative_path: Path):
        """查找 hasattr(config, ...) 调用"""
        hasattr_patterns = [
            r'hasattr\s*\(\s*config\s*,\s*[\'"]([^\'\"]+)[\'"]',  # hasattr(config, "attr_name")
            r'hasattr\s*\(\s*get_global_config\(\)\s*,\s*[\'"]([^\'\"]+)[\'"]',  # hasattr(get_global_config(), "attr")
        ]

        for pattern in hasattr_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                attr_name = match.group(1)

                if attr_name and not attr_name.startswith('_'):
                    self.config_keys_used.add(attr_name)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'hasattr_config_access',
                    'config_key': attr_name,
                    'code': lines[line_num - 1].strip(),
                    'context': self._get_context(lines, line_num - 1),
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1),
                    'full_match': match.group(0)
                }

                self.config_usages.append(usage_info)
                self.files_with_config.add(str(relative_path))

    def _find_setattr_config_access(self, content: str, lines: List[str], relative_path: Path):
        """查找 setattr(config, ...) 调用"""
        setattr_patterns = [
            r'setattr\s*\(\s*config\s*,\s*[\'"]([^\'\"]+)[\'"]',  # setattr(config, "attr_name", value)
            r'setattr\s*\(\s*get_global_config\(\)\s*,\s*[\'"]([^\'\"]+)[\'"]',
            # setattr(get_global_config(), "attr", value)
        ]

        for pattern in setattr_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                attr_name = match.group(1)

                if attr_name and not attr_name.startswith('_'):
                    self.config_keys_used.add(attr_name)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'setattr_config_access',
                    'config_key': attr_name,
                    'code': lines[line_num - 1].strip(),
                    'context': self._get_context(lines, line_num - 1),
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1),
                    'full_match': match.group(0)
                }

                self.config_usages.append(usage_info)
                self.files_with_config.add(str(relative_path))

    def _get_context(self, lines: List[str], line_idx: int, context_size: int = 3) -> List[str]:
        """获取代码上下文"""
        start = max(0, line_idx - context_size)
        end = min(len(lines), line_idx + context_size + 1)
        return lines[start:end]

    def _find_function_name(self, lines: List[str], line_idx: int) -> str:
        """查找当前行所在的函数名"""
        for i in range(line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith('def ') or line.startswith('async def '):
                match = re.match(r'(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if match:
                    return match.group(1)
        return "unknown"

    def _find_class_name(self, lines: List[str], line_idx: int) -> str:
        """查找当前行所在的类名"""
        for i in range(line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                match = re.match(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                if match:
                    return match.group(1)
        return "unknown"

    def analyze_dependency_injection_opportunities(self) -> Dict:
        """分析依赖注入改进机会"""
        analysis = {
            'total_usages': len(self.config_usages),
            'files_count': len(self.files_with_config),
            'config_keys_used': sorted(list(self.config_keys_used)),
            'usage_types_summary': self._get_usage_types_summary(),
            'injection_opportunities': [],
            'refactor_suggestions': []
        }

        # 按文件分组分析
        file_groups = defaultdict(list)
        for usage in self.config_usages:
            file_groups[usage['file']].append(usage)

        for file_path, usages in file_groups.items():
            classes_with_config = set()
            functions_with_config = set()

            for usage in usages:
                if usage['class'] != 'unknown':
                    classes_with_config.add(usage['class'])
                if usage['function'] != 'unknown':
                    functions_with_config.add(usage['function'])

            if classes_with_config:
                analysis['injection_opportunities'].append({
                    'file': file_path,
                    'type': 'class_constructor_injection',
                    'classes': list(classes_with_config),
                    'usage_count': len(usages),
                    'usage_types': self._get_file_usage_types(usages),
                    'suggestion': f"为 {', '.join(classes_with_config)} 类添加 config 参数到构造函数"
                })

            if functions_with_config:
                analysis['injection_opportunities'].append({
                    'file': file_path,
                    'type': 'function_parameter_injection',
                    'functions': list(functions_with_config),
                    'usage_count': len(usages),
                    'usage_types': self._get_file_usage_types(usages),
                    'suggestion': f"为 {', '.join(functions_with_config)} 函数添加 config 参数"
                })

        return analysis

    def _get_usage_types_summary(self) -> Dict[str, int]:
        """获取使用类型统计"""
        usage_types = defaultdict(int)
        for usage in self.config_usages:
            usage_types[usage['type']] += 1
        return dict(usage_types)

    def _get_file_usage_types(self, usages: List[Dict]) -> Dict[str, int]:
        """获取文件中的使用类型统计"""
        usage_types = defaultdict(int)
        for usage in usages:
            usage_types[usage['type']] += 1
        return dict(usage_types)

    def analyze_config_usage_patterns(self) -> Dict:
        """分析配置使用模式，提出精简建议"""
        config_sections = defaultdict(set)

        for key in self.config_keys_used:
            if '.' in key:
                section = key.split('.')[0]
                config_sections[section].add(key)
            else:
                config_sections['root'].add(key)

        # 转换 set 为 list 以便 JSON 序列化
        config_sections_serializable = {}
        for section, keys in config_sections.items():
            config_sections_serializable[section] = sorted(list(keys))

        return {
            'used_sections': config_sections_serializable,
            'unused_sections_suggestion': self._suggest_unused_sections(),
            'optimization_suggestions': self._generate_optimization_suggestions(),
            'dynamic_access_analysis': self._analyze_dynamic_access()
        }

    def _analyze_dynamic_access(self) -> Dict:
        """分析动态访问模式"""
        dynamic_usages = [u for u in self.config_usages if
                          u['type'] in ['getattr_config_access', 'hasattr_config_access', 'setattr_config_access']]

        return {
            'total_dynamic_accesses': len(dynamic_usages),
            'dynamic_access_files': list(set(u['file'] for u in dynamic_usages)),
            'dynamic_attributes': list(set(u.get('config_key', '') for u in dynamic_usages if u.get('config_key'))),
            'suggestions': [
                "动态属性访问使得配置依赖不够明确，建议转换为直接属性访问",
                "考虑为动态访问的属性创建明确的配置接口"
            ] if dynamic_usages else []
        }

    def _suggest_unused_sections(self) -> List[str]:
        """基于已知的配置文件结构，建议可能未使用的部分"""
        # 从 unified_config_framework_demo.yaml 中已知的配置节
        known_sections = {
            'multi_agent_mode', 'did_config', 'log_settings', 'auth_middleware',
            'anp_sdk', 'llm', 'mail', 'anp_user_service', 'env_mapping',
            'secrets', 'env_types', 'path_config'
        }

        used_sections = set()
        for key in self.config_keys_used:
            if '.' in key:
                used_sections.add(key.split('.')[0])
            else:
                used_sections.add(key)

        potentially_unused = known_sections - used_sections
        return sorted(list(potentially_unused))

    def _generate_optimization_suggestions(self) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 基于使用频率的建议
        file_usage_count = defaultdict(int)
        for usage in self.config_usages:
            file_usage_count[usage['file']] += 1

        high_usage_files = [f for f, count in file_usage_count.items() if count > 5]

        if high_usage_files:
            suggestions.append(
                f"高频使用配置的文件 ({len(high_usage_files)} 个) 建议优先进行依赖注入改造: " +
                ", ".join(high_usage_files[:3]) + ("..." if len(high_usage_files) > 3 else "")
            )

        # 基于配置键使用的建议
        if len(self.config_keys_used) < 20:
            suggestions.append("配置使用相对集中，可以考虑创建专门的配置子集类")

        # 基于动态访问的建议
        dynamic_count = len([u for u in self.config_usages if
                             'getattr' in u['type'] or 'hasattr' in u['type'] or 'setattr' in u['type']])
        if dynamic_count > 0:
            suggestions.append(f"发现 {dynamic_count} 处动态配置访问，建议转换为静态属性访问以提高代码可读性")

        return suggestions

    def generate_report(self, output_file: str = None):
        if output_file is None:
            # 获取脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_file = os.path.join(script_dir, "search_config_usage_analysis.json")

        """生成分析报告"""
        dependency_analysis = self.analyze_dependency_injection_opportunities()
        usage_patterns = self.analyze_config_usage_patterns()

        report = {
            'summary': {
                'total_config_usages': len(self.config_usages),
                'files_with_config': len(self.files_with_config),
                'unique_config_keys': len(self.config_keys_used),
                'analysis_timestamp': str(Path().absolute()),
                'excluded_files': ['search_config_usage.py', 'search_*.py']  # 记录排除的文件
            },
            'detailed_usages': self.config_usages,
            'dependency_injection_analysis': dependency_analysis,
            'config_usage_patterns': usage_patterns,
            'refactor_recommendations': self._generate_refactor_recommendations()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📊 配置使用分析报告已生成: {output_file}")
        return report

    def _generate_refactor_recommendations(self) -> List[Dict]:
        """生成重构建议"""
        recommendations = []

        # 1. 构造函数注入建议
        class_usages = defaultdict(list)
        for usage in self.config_usages:
            if usage['class'] != 'unknown':
                class_usages[usage['class']].append(usage)

        for class_name, usages in class_usages.items():
            if len(usages) > 2:  # 类中多次使用配置
                usage_types = self._get_file_usage_types(usages)
                recommendations.append({
                    'type': 'constructor_injection',
                    'target': class_name,
                    'priority': 'high',
                    'usage_count': len(usages),
                    'usage_types': usage_types,
                    'description': f"类 {class_name} 中使用了 {len(usages)} 次配置，建议在构造函数中注入",
                    'example_code': f"""
class {class_name}:
    def __init__(self, config: Optional[UnifiedConfig] = None):
        self.config = config or get_global_config()
        # ... rest of init ...
"""
                })

        # 2. 函数参数注入建议
        function_usages = defaultdict(list)
        for usage in self.config_usages:
            if usage['function'] != 'unknown' and usage['class'] == 'unknown':
                function_usages[usage['function']].append(usage)

        for func_name, usages in function_usages.items():
            if len(usages) > 1:
                usage_types = self._get_file_usage_types(usages)
                recommendations.append({
                    'type': 'function_parameter_injection',
                    'target': func_name,
                    'priority': 'medium',
                    'usage_count': len(usages),
                    'usage_types': usage_types,
                    'description': f"函数 {func_name} 中使用了 {len(usages)} 次配置，建议添加配置参数",
                    'example_code': f"""
def {func_name}(..., config: Optional[UnifiedConfig] = None):
    config = config or get_global_config()
    # ... rest of function ...
"""
                })

        return recommendations


def main():
    # 使用示例
    analyzer = ConfigUsageAnalyzer(".")  # 当前目录

    print("🔍 开始搜索配置使用...")
    print("📝 排除文件: search_config_usage.py 和其他分析脚本")
    analyzer.search_config_usage()

    print("📈 生成分析报告...")
    report = analyzer.generate_report()

    # 打印摘要
    print("\n📋 分析摘要:")
    print(f"  - 总配置使用次数: {report['summary']['total_config_usages']}")
    print(f"  - 涉及文件数量: {report['summary']['files_with_config']}")
    print(f"  - 使用的配置键: {report['summary']['unique_config_keys']}")

    # 打印使用类型统计
    usage_types = report['dependency_injection_analysis']['usage_types_summary']
    print(f"\n📊 使用类型统计:")
    for usage_type, count in usage_types.items():
        print(f"  - {usage_type}: {count}")

    print("\n🎯 主要发现:")
    # 按文件路径分组
    from collections import defaultdict
    grouped_opportunities = defaultdict(list)

    for opportunity in report['dependency_injection_analysis']['injection_opportunities']:
        file_path = opportunity.get('file', '未知文件')
        grouped_opportunities[file_path].append(opportunity)

    # 按文件路径排序并显示
    for file_idx, file_path in enumerate(sorted(grouped_opportunities.keys()), 1):
        print(f"\n📁 {file_idx}. [{file_path}]")
        opportunities = grouped_opportunities[file_path]
        for i, opportunity in enumerate(opportunities, 1):
            print(f"  {i}. {opportunity['suggestion']}")

    print("\n💡 配置精简建议:")
    unused = report['config_usage_patterns']['unused_sections_suggestion']
    if unused:
        print(f"  - 可能未使用的配置节: {', '.join(unused)}")

    # 打印动态访问分析
    dynamic_analysis = report['config_usage_patterns']['dynamic_access_analysis']
    if dynamic_analysis['total_dynamic_accesses'] > 0:
        print(f"\n🔧 动态访问分析:")
        print(f"  - 动态访问次数: {dynamic_analysis['total_dynamic_accesses']}")
        print(f"  - 涉及文件: {len(dynamic_analysis['dynamic_access_files'])}")
        print(f"  - 动态属性: {', '.join(dynamic_analysis['dynamic_attributes'][:5])}")

    for suggestion in report['config_usage_patterns']['optimization_suggestions']:
        print(f"  - {suggestion}")

    print(f"\n✅ 详细报告已保存到: config_usage_analysis.json")


if __name__ == "__main__":
    main()