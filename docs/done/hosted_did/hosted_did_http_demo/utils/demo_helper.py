#!/usr/bin/env python3
"""
HTTP托管DID演示辅助工具

提供演示过程中需要的各种辅助功能，包括：
- 演示输出格式化
- 进度显示
- 错误处理
- 统计信息收集
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path


class HTTPDemoHelper:
    """HTTP托管DID演示辅助类"""
    
    def __init__(self, dev_mode: bool = False, verbose: bool = False):
        """
        初始化演示辅助工具
        
        Args:
            dev_mode: 开发模式，显示更多调试信息
            verbose: 详细模式，显示更多输出
        """
        self.dev_mode = dev_mode
        self.verbose = verbose
        self.start_time = time.time()
        self.stats = {
            'phases_completed': 0,
            'steps_completed': 0,
            'http_requests': 0,
            'successful_requests': 0,
            'errors': [],
            'warnings': []
        }
    
    def show_banner(self, title: str, subtitle: str = ""):
        """显示横幅"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print(f"{'='*60}")
    
    def show_phase(self, phase_text: str):
        """显示阶段信息"""
        self.stats['phases_completed'] += 1
        print(f"\n🔹 {phase_text}")
        print("-" * 50)
    
    def show_step(self, step_text: str):
        """显示步骤信息"""
        self.stats['steps_completed'] += 1
        print(f"  📋 {step_text}")
    
    def show_info(self, text: str):
        """显示信息"""
        print(f"     ℹ️  {text}")
    
    def show_success(self, text: str):
        """显示成功信息"""
        print(f"     ✅ {text}")
    
    def show_warning(self, text: str):
        """显示警告信息"""
        print(f"     ⚠️  {text}")
        self.stats['warnings'].append(text)
    
    def show_error(self, text: str):
        """显示错误信息"""
        print(f"     ❌ {text}")
        self.stats['errors'].append(text)
    
    def show_progress(self, current: int, total: int, description: str = ""):
        """显示进度"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        progress_text = f"[{bar}] {percentage:.1f}% ({current}/{total})"
        if description:
            progress_text += f" - {description}"
        
        print(f"     🔄 {progress_text}")
    
    def record_http_request(self, success: bool = True):
        """记录HTTP请求"""
        self.stats['http_requests'] += 1
        if success:
            self.stats['successful_requests'] += 1
    
    def show_http_request(self, method: str, url: str, status_code: int = None, response_data: Dict = None):
        """显示HTTP请求详情"""
        if self.verbose or self.dev_mode:
            print(f"     📡 {method} {url}")
            if status_code:
                status_icon = "✅" if 200 <= status_code < 300 else "❌"
                print(f"        {status_icon} HTTP {status_code}")
            if response_data and self.dev_mode:
                print(f"        📄 响应: {response_data}")
    
    def show_agent_info(self, agent_name: str, agent_id: str, additional_info: Dict = None):
        """显示Agent信息"""
        print(f"     👤 Agent: {agent_name}")
        print(f"        🆔 ID: {agent_id}")
        
        if additional_info:
            for key, value in additional_info.items():
                print(f"        📋 {key}: {value}")
    
    def show_hosted_did_info(self, hosted_did_id: str, source_host: str, source_port: int, 
                           created_time: str = None, endpoints: List[Dict] = None):
        """显示托管DID信息"""
        print(f"     🏠 托管DID: {hosted_did_id}")
        print(f"        🌐 来源: {source_host}:{source_port}")
        
        if created_time:
            print(f"        📅 创建时间: {created_time}")
        
        if endpoints:
            print(f"        🔗 服务端点:")
            for endpoint in endpoints:
                endpoint_type = endpoint.get('type', 'Unknown')
                endpoint_url = endpoint.get('serviceEndpoint', 'N/A')
                print(f"           - {endpoint_type}: {endpoint_url}")
    
    def show_directory_info(self, directory_path: Path, file_count: int = None, 
                          subdirs: List[str] = None):
        """显示目录信息"""
        print(f"     📁 目录: {directory_path}")
        
        if file_count is not None:
            print(f"        📄 文件数量: {file_count}")
        
        if subdirs:
            print(f"        📂 子目录:")
            for subdir in subdirs[:5]:  # 只显示前5个
                print(f"           - {subdir}")
            if len(subdirs) > 5:
                print(f"           ... 还有 {len(subdirs) - 5} 个")
    
    def show_api_endpoints(self, endpoints: List[Dict[str, str]]):
        """显示API端点信息"""
        print(f"     🔌 API端点:")
        for endpoint in endpoints:
            method = endpoint.get('method', 'GET')
            path = endpoint.get('path', '')
            description = endpoint.get('description', '')
            print(f"        {method} {path}")
            if description:
                print(f"           💬 {description}")
    
    def show_statistics(self):
        """显示统计信息"""
        duration = time.time() - self.start_time
        success_rate = (self.stats['successful_requests'] / self.stats['http_requests'] * 100) if self.stats['http_requests'] > 0 else 0
        
        print(f"\n📊 演示统计信息")
        print(f"   ⏱️  总耗时: {duration:.1f} 秒")
        print(f"   🎯 完成阶段: {self.stats['phases_completed']}")
        print(f"   📋 完成步骤: {self.stats['steps_completed']}")
        print(f"   📡 HTTP请求: {self.stats['http_requests']} 次")
        print(f"   ✅ 成功请求: {self.stats['successful_requests']} 次")
        print(f"   📈 成功率: {success_rate:.1f}%")
        
        if self.stats['warnings']:
            print(f"   ⚠️  警告数量: {len(self.stats['warnings'])}")
        
        if self.stats['errors']:
            print(f"   ❌ 错误数量: {len(self.stats['errors'])}")
            if self.dev_mode:
                print("   错误详情:")
                for error in self.stats['errors'][:3]:  # 只显示前3个
                    print(f"      - {error}")
    
    def show_recommendations(self):
        """显示建议"""
        print(f"\n💡 建议:")
        
        success_rate = (self.stats['successful_requests'] / self.stats['http_requests'] * 100) if self.stats['http_requests'] > 0 else 0
        
        if success_rate >= 90:
            print("   🌟 演示执行优秀！所有功能正常工作")
        elif success_rate >= 70:
            print("   👍 演示执行良好，大部分功能正常")
            print("   🔧 建议检查失败的请求并优化")
        else:
            print("   ⚠️  演示执行需要改进")
            print("   🔍 建议检查网络连接和服务器状态")
        
        if self.stats['errors']:
            print("   🛠️  建议解决以下问题:")
            for error in self.stats['errors'][:3]:
                print(f"      - {error}")
        
        if not self.dev_mode:
            print("   🔧 使用 --dev-mode 获取更详细的调试信息")
    
    async def wait_with_progress(self, duration: int, description: str = "等待中"):
        """带进度显示的等待"""
        print(f"     ⏳ {description} ({duration}秒)")
        
        for i in range(duration):
            remaining = duration - i
            print(f"        ⏱️  剩余 {remaining} 秒...", end='\r')
            await asyncio.sleep(1)
        
        print(f"        ✅ {description}完成" + " " * 20)  # 清除剩余字符
    
    def format_json(self, data: Dict[str, Any], max_depth: int = 2) -> str:
        """格式化JSON数据用于显示"""
        try:
            import json
            if max_depth <= 0:
                return str(data)
            
            # 简化深层嵌套的数据
            def simplify_dict(obj, depth=0):
                if depth >= max_depth:
                    return "..."
                
                if isinstance(obj, dict):
                    return {k: simplify_dict(v, depth + 1) for k, v in obj.items()}
                elif isinstance(obj, list):
                    if len(obj) > 3:
                        return [simplify_dict(item, depth + 1) for item in obj[:3]] + ["..."]
                    return [simplify_dict(item, depth + 1) for item in obj]
                else:
                    return obj
            
            simplified = simplify_dict(data)
            return json.dumps(simplified, indent=2, ensure_ascii=False)
        except Exception:
            return str(data)
    
    def create_summary_report(self) -> Dict[str, Any]:
        """创建总结报告"""
        duration = time.time() - self.start_time
        success_rate = (self.stats['successful_requests'] / self.stats['http_requests'] * 100) if self.stats['http_requests'] > 0 else 0
        
        return {
            'duration': duration,
            'phases_completed': self.stats['phases_completed'],
            'steps_completed': self.stats['steps_completed'],
            'http_requests': self.stats['http_requests'],
            'successful_requests': self.stats['successful_requests'],
            'success_rate': success_rate,
            'warnings_count': len(self.stats['warnings']),
            'errors_count': len(self.stats['errors']),
            'warnings': self.stats['warnings'],
            'errors': self.stats['errors']
        }


class DemoProgressTracker:
    """演示进度跟踪器"""
    
    def __init__(self, total_phases: int):
        self.total_phases = total_phases
        self.current_phase = 0
        self.phase_start_time = None
        self.phase_times = []
    
    def start_phase(self, phase_name: str):
        """开始新阶段"""
        if self.phase_start_time:
            # 记录上一个阶段的时间
            phase_duration = time.time() - self.phase_start_time
            self.phase_times.append(phase_duration)
        
        self.current_phase += 1
        self.phase_start_time = time.time()
        
        progress = (self.current_phase / self.total_phases) * 100
        print(f"\n🎯 阶段 {self.current_phase}/{self.total_phases}: {phase_name} ({progress:.1f}%)")
    
    def finish(self):
        """完成所有阶段"""
        if self.phase_start_time:
            phase_duration = time.time() - self.phase_start_time
            self.phase_times.append(phase_duration)
        
        total_time = sum(self.phase_times)
        print(f"\n⏱️  各阶段耗时:")
        for i, duration in enumerate(self.phase_times, 1):
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            print(f"   阶段 {i}: {duration:.1f}秒 ({percentage:.1f}%)")
        print(f"   总计: {total_time:.1f}秒")


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def format_duration(seconds: float) -> str:
    """格式化时间长度"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds:.0f}秒"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{remaining_minutes}分钟"


def truncate_text(text: str, max_length: int = 50) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


# 导出主要类和函数
__all__ = [
    'HTTPDemoHelper',
    'DemoProgressTracker',
    'format_file_size',
    'format_duration',
    'truncate_text'
]
