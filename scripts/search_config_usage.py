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
        return any(part in skip_dirs for part in file_path.parts)

    def _analyze_file(self, file_path: Path, content: str):
        """分析单个文件中的配置使用"""
        relative_path = file_path.relative_to(self.root_path)

        # 搜索 get_global_config() 调用
        get_config_pattern = r'config\s*=\s*get_global_config\(\)'
        get_config_matches = re.finditer(get_config_pattern, content)

        # 搜索直接的配置访问模式
        config_access_patterns = [
            r'config\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'get_global_config\(\)\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]

        lines = content.split('\n')

        for match in get_config_matches:
            line_num = content[:match.start()].count('\n') + 1
            context = self._get_context(lines, line_num - 1)

            usage_info = {
                'file': str(relative_path),
                'line': line_num,
                'type': 'get_global_config',
                'code': lines[line_num - 1].strip(),
                'context': context,
                'function': self._find_function_name(lines, line_num - 1),
                'class': self._find_class_name(lines, line_num - 1)
            }

            self.config_usages.append(usage_info)
            self.files_with_config.add(str(relative_path))

        # 搜索配置属性访问
        for pattern in config_access_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                config_key = match.group(1)
                self.config_keys_used.add(config_key)

                usage_info = {
                    'file': str(relative_path),
                    'line': line_num,
                    'type': 'config_access',
                    'config_key': config_key,
                    'code': lines[line_num - 1].strip(),
                    'context': self._get_context(lines, line_num - 1),
                    'function': self._find_function_name(lines, line_num - 1),
                    'class': self._find_class_name(lines, line_num - 1)
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
                    'suggestion': f"为 {', '.join(classes_with_config)} 类添加 config 参数到构造函数"
                })

            if functions_with_config:
                analysis['injection_opportunities'].append({
                    'file': file_path,
                    'type': 'function_parameter_injection',
                    'functions': list(functions_with_config),
                    'usage_count': len(usages),
                    'suggestion': f"为 {', '.join(functions_with_config)} 函数添加 config 参数"
                })

        return analysis

    def analyze_config_usage_patterns(self) -> Dict:
        """分析配置使用模式，提出精简建议"""
        config_sections = defaultdict(set)

        for key in self.config_keys_used:
            if '.' in key:
                section = key.split('.')[0]
                config_sections[section].add(key)
            else:
                config_sections['root'].add(key)

        return {
            'used_sections': dict(config_sections),
            'unused_sections_suggestion': self._suggest_unused_sections(),
            'optimization_suggestions': self._generate_optimization_suggestions()
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
        return list(potentially_unused)

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

        return suggestions

    def generate_report(self, output_file: str = "config_usage_analysis.json"):
        """生成分析报告"""
        dependency_analysis = self.analyze_dependency_injection_opportunities()
        usage_patterns = self.analyze_config_usage_patterns()

        report = {
            'summary': {
                'total_config_usages': len(self.config_usages),
                'files_with_config': len(self.files_with_config),
                'unique_config_keys': len(self.config_keys_used),
                'analysis_timestamp': str(Path().absolute())
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
                recommendations.append({
                    'type': 'constructor_injection',
                    'target': class_name,
                    'priority': 'high',
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
                recommendations.append({
                    'type': 'function_parameter_injection',
                    'target': func_name,
                    'priority': 'medium',
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
    analyzer = ConfigUsageAnalyzer("anp-open-sdk-python")

    print("🔍 开始搜索配置使用...")
    analyzer.search_config_usage()

    print("📈 生成分析报告...")
    report = analyzer.generate_report()

    # 打印摘要
    print("\n📋 分析摘要:")
    print(f"  - 总配置使用次数: {report['summary']['total_config_usages']}")
    print(f"  - 涉及文件数量: {report['summary']['files_with_config']}")
    print(f"  - 使用的配置键: {report['summary']['unique_config_keys']}")

    print("\n🎯 主要发现:")
    for opportunity in report['dependency_injection_analysis']['injection_opportunities'][:5]:
        print(f"  - {opportunity['suggestion']}")

    print("\n💡 配置精简建议:")
    unused = report['config_usage_patterns']['unused_sections_suggestion']
    if unused:
        print(f"  - 可能未使用的配置节: {', '.join(unused)}")

    for suggestion in report['config_usage_patterns']['optimization_suggestions']:
        print(f"  - {suggestion}")

    print(f"\n✅ 详细报告已保存到: config_usage_analysis.json")

if __name__ == "__main__":
    main()