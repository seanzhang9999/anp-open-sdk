#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全目录 Agent 用户绑定检查和修复脚本

功能：
1. 自动搜索所有 agents_config/*/agent_mappings.yaml 文件
2. 检查每个 agent 的 DID 绑定状态
3. 验证 DID 是否存在于对应的 anp_users 目录中
4. 自动创建缺失的用户 DID
5. 修复重复或无效的 DID 绑定
6. 生成详细的绑定关系报告

使用方法：
python agent_user_binding.py [根目录]  # 如果不指定根目录，将从当前目录搜索
"""

import os
import sys
import glob
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentUserBindingManager:
    """Agent 用户绑定管理器"""
    
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.agents_config_dirs = []
        self.user_data_dirs = []
        self.agent_mappings = {}
        self.user_dids = {}
        
    def discover_directories(self):
        """发现所有相关目录"""
        print("🔍 搜索 agents_config 和 anp_users 目录...")
        
        # 搜索所有 agents_config 目录
        for agents_config_dir in self.root_dir.glob("**/agents_config"):
            if agents_config_dir.is_dir():
                self.agents_config_dirs.append(agents_config_dir)
                
                # 查找对应的 anp_users 目录（兄弟目录）
                parent_dir = agents_config_dir.parent
                anp_users_dir = parent_dir / "anp_users"
                if anp_users_dir.exists() and anp_users_dir.is_dir():
                    self.user_data_dirs.append((agents_config_dir, anp_users_dir))
                else:
                    print(f"⚠️  找到 agents_config 但缺少对应的 anp_users: {agents_config_dir}")
        
        print(f"📂 找到 {len(self.agents_config_dirs)} 个 agents_config 目录")
        print(f"📂 找到 {len(self.user_data_dirs)} 个配对的目录组")
        
    def load_agent_mappings(self):
        """加载所有 agent_mappings.yaml 文件"""
        print("\n📋 加载 agent_mappings.yaml 文件...")
        
        for agents_config_dir, anp_users_dir in self.user_data_dirs:
            # 搜索该 agents_config 目录下的所有 agent_mappings.yaml
            mapping_files = list(agents_config_dir.glob("*/agent_mappings.yaml"))
            
            for mapping_file in mapping_files:
                try:
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    agent_name = config.get('name', 'Unknown')
                    agent_did = config.get('did', None)
                    
                    self.agent_mappings[str(mapping_file)] = {
                        'config': config,
                        'name': agent_name,
                        'did': agent_did,
                        'file_path': mapping_file,
                        'agents_config_dir': agents_config_dir,
                        'anp_users_dir': anp_users_dir
                    }
                    
                except Exception as e:
                    print(f"❌ 无法加载 {mapping_file}: {e}")
        
        print(f"✅ 成功加载 {len(self.agent_mappings)} 个 agent 配置")
    
    def load_user_dids(self):
        """加载所有用户 DID 信息"""
        print("\n👥 加载用户 DID 信息...")
        
        for agents_config_dir, anp_users_dir in self.user_data_dirs:
            # 搜索该 anp_users 目录下的所有用户目录
            user_dirs = [d for d in anp_users_dir.iterdir() if d.is_dir() and d.name.startswith('user_')]
            
            for user_dir in user_dirs:
                did_doc_path = user_dir / "did_document.json"
                if did_doc_path.exists():
                    try:
                        with open(did_doc_path, 'r', encoding='utf-8') as f:
                            did_doc = json.load(f)
                        
                        did = did_doc.get('id')
                        if did:
                            self.user_dids[did] = {
                                'user_dir': user_dir,
                                'user_name': user_dir.name,
                                'anp_users_dir': anp_users_dir,
                                'did_document': did_doc
                            }
                    except Exception as e:
                        print(f"⚠️  无法加载 {did_doc_path}: {e}")
        
        print(f"✅ 成功加载 {len(self.user_dids)} 个用户 DID")
    
    def check_duplicate_dids(self) -> Dict[str, List[str]]:
        """检查重复的 DID"""
        did_usage = {}
        
        for file_path, agent_info in self.agent_mappings.items():
            did = agent_info['did']
            if did:
                if did not in did_usage:
                    did_usage[did] = []
                did_usage[did].append(file_path)
        
        # 返回重复的 DID
        duplicates = {did: files for did, files in did_usage.items() if len(files) > 1}
        return duplicates
    
    def check_invalid_dids(self) -> List[str]:
        """检查无效或缺失的 DID"""
        invalid_agents = []
        
        for file_path, agent_info in self.agent_mappings.items():
            did = agent_info['did']
            if not did or did not in self.user_dids:
                invalid_agents.append(file_path)
        
        return invalid_agents
    
    def create_new_user_did(self, anp_users_dir: Path, agent_name: str) -> Optional[str]:
        """为 agent 创建新的用户 DID"""
        try:
            # 导入必要的模块（延迟导入避免配置依赖）
            from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import did_create_user
            import uuid
            
            # 生成用户ID
            user_id = str(uuid.uuid4()).replace('-', '')[:16]
            
            # 解析路径信息
            path_parts = str(anp_users_dir).split('/')
            host = 'localhost'
            port = 9527
            
            # 尝试从路径中提取主机和端口信息
            for part in path_parts:
                if 'localhost_' in part:
                    try:
                        port = int(part.split('_')[1])
                    except:
                        pass
                elif part.startswith('host_'):
                    host = part[5:]
            
            # 创建用户参数
            params = {
                'name': f"user_{user_id}",
                'host': host,
                'port': port,
                'dir': str(anp_users_dir),
                'type': 'user',
                'agent_name': agent_name
            }
            
            print(f"   🔧 为 agent '{agent_name}' 创建新用户...")
            print(f"      参数: {params}")
            
            # 创建用户
            did_doc = did_create_user(params)
            
            if did_doc and 'id' in did_doc:
                new_did = did_doc['id']
                print(f"   ✅ 成功创建用户 DID: {new_did}")
                
                # 更新用户 DID 缓存
                user_dir = anp_users_dir / f"user_{user_id}"
                self.user_dids[new_did] = {
                    'user_dir': user_dir,
                    'user_name': f"user_{user_id}",
                    'anp_users_dir': anp_users_dir,
                    'did_document': did_doc
                }
                
                return new_did
            else:
                print(f"   ❌ 创建用户失败")
                return None
                
        except Exception as e:
            print(f"   ❌ 创建用户时出错: {e}")
            return None
    
    def fix_invalid_agent(self, file_path: str, interactive: bool = True) -> bool:
        """修复无效的 agent DID 绑定"""
        agent_info = self.agent_mappings[file_path]
        agent_name = agent_info['name']
        current_did = agent_info['did']
        anp_users_dir = agent_info['anp_users_dir']
        
        print(f"\n🔧 修复 agent: {agent_name}")
        print(f"   文件: {file_path}")
        print(f"   当前 DID: {current_did or '无'}")
        
        # 找到该 anp_users_dir 对应的可用 DID
        available_dids = {did: info for did, info in self.user_dids.items() 
                         if info['anp_users_dir'] == anp_users_dir}
        
        # 排除已使用的 DID
        used_dids = {info['did'] for info in self.agent_mappings.values() if info['did']}
        unused_dids = {did: info for did, info in available_dids.items() if did not in used_dids}
        
        if interactive:
            print(f"   可用的未使用 DID:")
            for idx, (did, info) in enumerate(unused_dids.items(), 1):
                print(f"      [{idx}] {info['user_name']} ({did})")
            print(f"      [N] 创建新用户")
            
            choice = input("   请选择 DID 编号或输入 N 创建新用户: ").strip()
            
            if choice.upper() == 'N':
                new_did = self.create_new_user_did(anp_users_dir, agent_name)
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(unused_dids):
                        new_did = list(unused_dids.keys())[idx]
                        print(f"   ✅ 选择了 DID: {new_did}")
                    else:
                        print(f"   ❌ 无效选择")
                        return False
                except ValueError:
                    print(f"   ❌ 无效输入")
                    return False
        else:
            # 非交互模式：优先使用现有未使用的 DID，否则创建新的
            if unused_dids:
                new_did = list(unused_dids.keys())[0]
                print(f"   🔄 自动分配 DID: {new_did}")
            else:
                new_did = self.create_new_user_did(anp_users_dir, agent_name)
        
        if new_did:
            # 更新配置文件
            try:
                agent_info['config']['did'] = new_did
                with open(agent_info['file_path'], 'w', encoding='utf-8') as f:
                    yaml.dump(agent_info['config'], f, allow_unicode=True, sort_keys=False)
                
                # 更新内存中的信息
                self.agent_mappings[file_path]['did'] = new_did
                
                print(f"   ✅ 已更新配置文件")
                return True
            except Exception as e:
                print(f"   ❌ 更新配置文件失败: {e}")
                return False
        else:
            return False
    
    def generate_report(self):
        """生成绑定关系报告"""
        print(f"\n📊 Agent 用户绑定关系报告")
        print("=" * 100)
        print(f"{'Agent名称':<25} {'DID':<45} {'用户名':<20} {'配置文件':<30}")
        print("-" * 100)
        
        for idx, (file_path, agent_info) in enumerate(self.agent_mappings.items(), 1):
            agent_name = agent_info['name']
            agent_did = agent_info['did'] or '无DID'
            
            if agent_info['did'] and agent_info['did'] in self.user_dids:
                user_name = self.user_dids[agent_info['did']]['user_name']
            else:
                user_name = '未绑定'
            
            config_file = str(agent_info['file_path']).split('agents_config/')[-1] if 'agents_config/' in str(agent_info['file_path']) else str(agent_info['file_path'])
            
            print(f"{agent_name:<25} {agent_did:<45} {user_name:<20} {config_file:<30}")
        
        print("=" * 100)
        print(f"总计: {len(self.agent_mappings)} 个 Agent")
    
    def run_checks(self, interactive: bool = True, auto_fix: bool = False):
        """运行所有检查"""
        print("🚀 开始 Agent 用户绑定检查...")
        
        # 发现目录
        self.discover_directories()
        
        if not self.user_data_dirs:
            print("❌ 未找到任何 agents_config 和 anp_users 配对目录")
            return False
        
        # 加载数据
        self.load_agent_mappings()
        self.load_user_dids()
        
        if not self.agent_mappings:
            print("❌ 未找到任何 agent_mappings.yaml 文件")
            return False
        
        # 检查重复 DID
        duplicates = self.check_duplicate_dids()
        if duplicates:
            print(f"\n❌ 发现重复 DID:")
            for did, files in duplicates.items():
                print(f"   DID: {did}")
                for file_path in files:
                    agent_name = self.agent_mappings[file_path]['name']
                    print(f"     - {agent_name} ({file_path})")
        
        # 检查无效 DID
        invalid_agents = self.check_invalid_dids()
        if invalid_agents:
            print(f"\n⚠️  发现 {len(invalid_agents)} 个需要修复的 Agent:")
            
            fixed_count = 0
            for file_path in invalid_agents:
                if auto_fix or interactive:
                    if self.fix_invalid_agent(file_path, interactive):
                        fixed_count += 1
                else:
                    agent_name = self.agent_mappings[file_path]['name']
                    current_did = self.agent_mappings[file_path]['did']
                    print(f"   - {agent_name}: {current_did or '无DID'} ({file_path})")
            
            if auto_fix or interactive:
                print(f"\n🔧 修复完成: {fixed_count}/{len(invalid_agents)} 个 Agent")
        
        # 如果没有问题，显示报告
        if not duplicates and not invalid_agents:
            print("\n✅ 所有 Agent 的 DID 绑定都正常!")
        
        # 生成最终报告
        self.generate_report()
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 用户绑定检查和修复工具")
    parser.add_argument('root_dir', nargs='?', default=None, 
                       help='搜索根目录 (默认为当前目录)')
    parser.add_argument('--auto-fix', action='store_true', 
                       help='自动修复问题（非交互模式）')
    parser.add_argument('--no-interactive', action='store_true', 
                       help='非交互模式（仅报告问题）')
    
    args = parser.parse_args()
    
    # 获取根目录
    root_dir = args.root_dir or os.getcwd()
    print(f"📂 搜索根目录: {root_dir}")
    
    # 创建管理器并运行检查
    manager = AgentUserBindingManager(root_dir)
    
    interactive = not args.no_interactive
    auto_fix = args.auto_fix
    
    if auto_fix:
        interactive = False  # 自动修复模式不需要交互
    
    success = manager.run_checks(interactive=interactive, auto_fix=auto_fix)
    
    if success:
        print("\n🎉 Agent 用户绑定检查完成!")
    else:
        print("\n❌ 检查过程中出现错误")
        sys.exit(1)


if __name__ == "__main__":
    main()