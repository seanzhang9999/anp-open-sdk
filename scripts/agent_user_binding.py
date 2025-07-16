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
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from anp_sdk.utils.log_base import setup_logging
from anp_sdk.config import UnifiedConfig,set_global_config

app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
set_global_config(app_config)

setup_logging() # 假设 setup_logging 内部也改用 get_global_config()
logger = logging.getLogger(__name__)


class AgentUserBindingManager:
    """Agent 用户绑定管理器"""
    
    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.agents_config_dirs = []
        self.user_data_dirs = []
        self.agent_mappings = {}
        self.user_dids = {}
        self.shared_did_configs = {}  # 新增：共享DID配置
        
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
                    
                    # 🆕 处理共享DID配置
                    share_did_config = config.get('share_did', {})
                    shared_did = None
                    if share_did_config.get('enabled'):
                        shared_did = share_did_config.get('shared_did')
                    
                    self.agent_mappings[str(mapping_file)] = {
                        'config': config,
                        'name': agent_name,
                        'did': agent_did,
                        'shared_did': shared_did,
                        'share_did_config': share_did_config,
                        'file_path': mapping_file,
                        'agents_config_dir': agents_config_dir,
                        'anp_users_dir': anp_users_dir
                    }
                    
                    # 🆕 收集共享DID配置
                    if shared_did:
                        if shared_did not in self.shared_did_configs:
                            self.shared_did_configs[shared_did] = []
                        self.shared_did_configs[shared_did].append({
                            'agent_name': agent_name,
                            'path_prefix': share_did_config.get('path_prefix', ''),
                            'file_path': mapping_file,
                            'api_paths': [api.get('path', '') for api in config.get('api', [])]
                        })
                    
                except Exception as e:
                    print(f"❌ 无法加载 {mapping_file}: {e}")
        
        print(f"✅ 成功加载 {len(self.agent_mappings)} 个 agent 配置")
        if self.shared_did_configs:
            print(f"🔗 发现 {len(self.shared_did_configs)} 个共享DID配置")
    
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
    

    def check_username_conflicts(self):
        """检查用户名冲突"""
        print("\n🔍 检查用户名冲突...")

        # 按域名端口分组用户
        users_by_host_port = {}
        for did, user_info in self.user_dids.items():
            # 从DID中提取域名和端口
            from anp_sdk.did.did_tool import parse_wba_did_host_port
            host, port = parse_wba_did_host_port(did)

            if host and port:
                host_port_key = (host, port)
                if host_port_key not in users_by_host_port:
                    users_by_host_port[host_port_key] = {}

                # 从agent_cfg.yaml中获取用户名
                cfg_path = user_info['user_dir'] / 'agent_cfg.yaml'
                if cfg_path.exists():
                    try:
                        with open(cfg_path, 'r', encoding='utf-8') as f:
                            cfg = yaml.safe_load(f)
                            name = cfg.get('name')
                            if name:
                                if name in users_by_host_port[host_port_key]:
                                    # 发现冲突
                                    existing_did = users_by_host_port[host_port_key][name]
                                    print(f"⚠️  发现用户名冲突: '{name}' 在 {host}:{port}")
                                    print(f"   - DID 1: {existing_did}")
                                    print(f"   - DID 2: {did}")

                                    # 记录冲突
                                    if not hasattr(self, 'name_conflicts'):
                                        self.name_conflicts = []
                                    self.name_conflicts.append({
                                        'name': name,
                                        'host': host,
                                        'port': port,
                                        'dids': [existing_did, did]
                                    })
                                else:
                                    users_by_host_port[host_port_key][name] = did
                    except Exception as e:
                        print(f"⚠️  读取配置文件失败 {cfg_path}: {e}")

        # 返回冲突列表
        conflicts = getattr(self, 'name_conflicts', [])
        if conflicts:
            print(f"⚠️  发现 {len(conflicts)} 个用户名冲突")
        else:
            print("✅ 未发现用户名冲突")

        return conflicts

    def fix_username_conflict(self, conflict, interactive=True):
        """修复用户名冲突"""
        name = conflict['name']
        host = conflict['host']
        port = conflict['port']
        dids = conflict['dids']

        print(f"\n🔧 修复用户名冲突: '{name}' 在 {host}:{port}")

        # 导入必要的模块
        from anp_sdk.anp_user_local_data import get_user_data_manager

        # 获取用户数据管理器
        manager = get_user_data_manager()

        # 为每个冲突的DID显示信息
        for idx, did in enumerate(dids, 1):
            user_info = self.user_dids[did]
            user_dir = user_info['user_dir']
            print(f"   [{idx}] DID: {did}")
            print(f"       目录: {user_dir}")

        if interactive:
            # 交互式修复
            print("\n   选项:")
            print("   [1-N] 选择要重命名的DID")
            print("   [S] 跳过此冲突")

            choice = input("   请选择操作: ").strip().upper()

            if choice == 'S':
                print("   ⏭️  跳过此冲突")
                return False

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(dids):
                    did_to_rename = dids[idx]

                    # 请求新名称
                    new_name = input(f"   请输入 {did_to_rename} 的新名称: ").strip()
                    if not new_name:
                        print("   ❌ 名称不能为空")
                        return False

                    # 检查新名称是否可用
                    if manager.is_username_taken(new_name, host, int(port)):
                        print(f"   ❌ 新名称 '{new_name}' 已被使用")
                        return False

                    # 使用resolve_username_conflict解决冲突
                    success = manager.resolve_username_conflict(did_to_rename, new_name)

                    if success:
                        print(f"   ✅ 成功将 {did_to_rename} 重命名为 '{new_name}'")
                        return True
                    else:
                        print(f"   ❌ 重命名失败")
                        return False
                else:
                    print(f"   ❌ 无效选择")
                    return False
            except ValueError:
                print(f"   ❌ 无效输入")
                return False
        else:
            # 自动修复模式：为第二个DID添加时间戳后缀
            from datetime import datetime

            did_to_rename = dids[1]  # 选择第二个DID进行重命名
            date_suffix = datetime.now().strftime('%Y%m%d')
            new_name = f"{name}_{date_suffix}"

            # 检查新名称是否可用
            if manager.is_username_taken(new_name, host, int(port)):
                # 如果还是被使用，添加随机后缀
                import secrets
                random_suffix = secrets.token_hex(4)
                new_name = f"{name}_{date_suffix}_{random_suffix}"

            # 使用resolve_username_conflict解决冲突
            success = manager.resolve_username_conflict(did_to_rename, new_name)

            if success:
                print(f"   ✅ 自动将 {did_to_rename} 重命名为 '{new_name}'")
                return True
            else:
                print(f"   ❌ 自动重命名失败")
                return False
        

    def create_new_user_did(self, anp_users_dir: Path, agent_name: str) -> Optional[str]:
        """为 agent 创建新的用户 DID"""
        try:
            # 导入必要的模块（延迟导入避免配置依赖）
            from anp_sdk.anp_user_local_data import create_did_user
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
                'dir': 'wba',
                'type': 'user',
                'agent_name': agent_name
            }
            
            print(f"   🔧 为 agent '{agent_name}' 创建新用户...")
            print(f"      参数: {params}")
            
            # 创建用户
            did_doc = create_did_user(params)
            
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
    
    def validate_config_consistency(self):
        """验证配置一致性"""
        print("\n🔍 检查配置一致性...")
        errors = []
        
        for file_path, agent_info in self.agent_mappings.items():
            config = agent_info['config']
            agent_name = agent_info['name']
            
            # 检查1: share_did和did不能同时存在
            has_did = 'did' in config and config['did']
            has_share_did = 'share_did' in config and config['share_did'].get('enabled')
            
            if has_did and has_share_did:
                errors.append(f"{agent_name}: 不能同时配置 'did' 和 'share_did'")
            
            if not has_did and not has_share_did:
                errors.append(f"{agent_name}: 必须配置 'did' 或 'share_did' 之一")
            
            # 注意：%3A 是正确的URL编码格式，不需要修复
            # 检查2: DID基本格式验证
            if has_did:
                did = config['did']
                if not did.startswith('did:'):
                    errors.append(f"{agent_name}: DID格式错误，应以 'did:' 开头")
            
            # 检查3: 共享DID基本格式验证
            if has_share_did:
                shared_did = config['share_did']['shared_did']
                if not shared_did.startswith('did:'):
                    errors.append(f"{agent_name}: 共享DID格式错误，应以 'did:' 开头")
        
        if errors:
            print("❌ 发现配置一致性错误:")
            for error in errors:
                print(f"   {error}")
        else:
            print("✅ 配置一致性检查通过!")
        
        return errors
    
    def check_shared_did_path_conflicts(self):
        """检查共享DID路径冲突"""
        print("\n🔍 检查共享DID路径冲突...")
        conflicts = {}
        
        for shared_did, agents in self.shared_did_configs.items():
            path_conflicts = []
            path_owners = {}
            
            for agent in agents:
                path_prefix = agent['path_prefix']
                for api_path in agent['api_paths']:
                    # 组合完整路径：path_prefix + api_path
                    full_path = f"{path_prefix.rstrip('/')}{api_path}"
                    
                    if full_path in path_owners:
                        conflict_msg = f"路径 '{full_path}' 冲突: {path_owners[full_path]} vs {agent['agent_name']}"
                        path_conflicts.append(conflict_msg)
                    else:
                        path_owners[full_path] = agent['agent_name']
            
            if path_conflicts:
                conflicts[shared_did] = path_conflicts
        
        if conflicts:
            print("❌ 发现共享DID路径冲突:")
            for shared_did, conflict_list in conflicts.items():
                print(f"   共享DID: {shared_did}")
                for conflict in conflict_list:
                    print(f"     {conflict}")
        else:
            print("✅ 共享DID路径检查通过!")
        
        return conflicts
    
    def validate_did_format(self, file_path: str) -> List[str]:
        """验证DID格式（不修复，只检查）"""
        agent_info = self.agent_mappings[file_path]
        config = agent_info['config']
        agent_name = agent_info['name']
        warnings = []
        
        # 检查独立DID格式
        if 'did' in config and config['did']:
            did = config['did']
            if not did.startswith('did:'):
                warnings.append(f"{agent_name}: DID格式可能有问题，应以 'did:' 开头")
        
        # 检查共享DID格式
        if 'share_did' in config and config['share_did'].get('enabled'):
            share_config = config['share_did']
            if 'shared_did' in share_config:
                shared_did = share_config['shared_did']
                if not shared_did.startswith('did:'):
                    warnings.append(f"{agent_name}: 共享DID格式可能有问题，应以 'did:' 开头")
        
        return warnings
    
    def generate_report(self):
        """生成绑定关系报告"""
        print(f"\n📊 Agent 用户绑定关系报告")
        print("=" * 120)
        print(f"{'Agent名称':<25} {'类型':<10} {'DID/共享DID':<50} {'用户名':<20} {'配置文件':<30}")
        print("-" * 120)
        
        for idx, (file_path, agent_info) in enumerate(self.agent_mappings.items(), 1):
            agent_name = agent_info['name']
            
            # 判断类型和DID
            if agent_info['shared_did']:
                agent_type = "共享DID"
                did_info = agent_info['shared_did']
                path_prefix = agent_info['share_did_config'].get('path_prefix', '')
                if path_prefix:
                    did_info += f" ({path_prefix})"
                user_name = "共享"
            else:
                agent_type = "独立DID"
                did_info = agent_info['did'] or '无DID'
                if agent_info['did'] and agent_info['did'] in self.user_dids:
                    user_name = self.user_dids[agent_info['did']]['user_name']
                else:
                    user_name = '未绑定'
            
            config_file = str(agent_info['file_path']).split('agents_config/')[-1] if 'agents_config/' in str(agent_info['file_path']) else str(agent_info['file_path'])
            
            print(f"{agent_name:<25} {agent_type:<10} {did_info:<50} {user_name:<20} {config_file:<30}")
        
        print("=" * 120)
        print(f"总计: {len(self.agent_mappings)} 个 Agent")
        
        # 共享DID统计
        if self.shared_did_configs:
            print(f"\n🔗 共享DID统计:")
            for shared_did, agents in self.shared_did_configs.items():
                print(f"   {shared_did}:")
                for agent in agents:
                    print(f"     - {agent['agent_name']} (前缀: {agent['path_prefix'] or '无'})")
    
    def run_checks(self, interactive: bool = True, auto_fix: bool = False):
        """运行所有检查"""
        print("🚀 开始增强的 Agent 用户绑定检查...")
        
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
        
        # 🆕 1. 配置一致性检查
        consistency_errors = self.validate_config_consistency()
        
        # 🆕 2. DID格式验证
        print("\n🔍 验证DID格式...")
        format_warnings = []
        for file_path in self.agent_mappings:
            warnings = self.validate_did_format(file_path)
            format_warnings.extend(warnings)
        
        if format_warnings:
            print("⚠️  发现DID格式警告:")
            for warning in format_warnings:
                print(f"   {warning}")
        else:
            print("✅ DID格式验证通过!")
        
        # 🆕 3. 共享DID路径冲突检查
        path_conflicts = self.check_shared_did_path_conflicts()
        
        # 4. 检查重复 DID
        duplicates = self.check_duplicate_dids()
        if duplicates:
            print(f"\n❌ 发现重复 DID:")
            for did, files in duplicates.items():
                print(f"   DID: {did}")
                for file_path in files:
                    agent_name = self.agent_mappings[file_path]['name']
                    print(f"     - {agent_name} ({file_path})")
        
        # 5. 检查无效 DID（只检查独立DID的agent）
        invalid_agents = []
        for file_path, agent_info in self.agent_mappings.items():
            # 只检查独立DID的agent
            if not agent_info['shared_did']:
                did = agent_info['did']
                if not did or did not in self.user_dids:
                    invalid_agents.append(file_path)
        
        if invalid_agents:
            print(f"\n⚠️  发现 {len(invalid_agents)} 个需要修复的独立DID Agent:")
            
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
        

        # 检查用户名冲突
        name_conflicts = self.check_username_conflicts()
        if name_conflicts and (auto_fix or interactive):
            print("\n🔧 开始修复用户名冲突...")
            fixed_count = 0
            for conflict in name_conflicts:
                if self.fix_username_conflict(conflict, interactive):
                    fixed_count += 1
            print(f"\n🔧 修复完成: {fixed_count}/{len(name_conflicts)} 个用户名冲突")
            
        # 6. 总结检查结果
        total_issues = len(consistency_errors) + len(path_conflicts) + len(duplicates) + len(invalid_agents)
        if total_issues == 0:
            print("\n✅ 所有检查都通过了！配置完全正常。")
        else:
            print(f"\n📋 检查总结:")
            print(f"   - 配置一致性错误: {len(consistency_errors)}")
            print(f"   - 共享DID路径冲突: {len(path_conflicts)}")
            print(f"   - 重复DID: {len(duplicates)}")
            print(f"   - 无效DID绑定: {len(invalid_agents)}")
            print(f"   - 用户名冲突: {len(name_conflicts)}")
        
        # 7. 生成最终报告
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
