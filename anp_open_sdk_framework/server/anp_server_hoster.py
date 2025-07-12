import json
import os
import secrets
import socket
from pathlib import Path
from typing import Optional

from anp_open_sdk.anp_user import ANPUser, logger
from anp_open_sdk.config import get_global_config
from anp_open_sdk.utils.log_base import logging as logger
from anp_open_sdk_framework.server.publisher.anp_sdk_publisher_mail_backend import EnhancedMailManager
from anp_open_sdk_framework.server.anp_server import logger


class DIDHostManager:
    """DID管理器，用于处理DID文档的存储和管理"""
    
    def __init__(self, hosted_dir: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None):
        """
        初始化DID管理器
        
        Args:
            hosted_dir: DID托管目录路径，如果为None则使用默认路径
            host: 指定主机名（用于多域名环境）
            port: 指定端口（用于多域名环境）
        """
        if host is not None and port is not None:
            # 多域名模式：使用指定的主机和端口
            from anp_open_sdk.domain import get_domain_manager
            domain_manager = get_domain_manager()
            paths = domain_manager.get_all_data_paths(host, port)
            self.hosted_dir = paths['user_hosted_path']
            self.hostdomain = host
            self.hostport = str(port)
        else:
            # 兼容模式：使用现有逻辑
            config = get_global_config()
            self.hosted_dir = Path(hosted_dir or config.anp_sdk.user_hosted_path)
            self.hostdomain = os.environ.get('HOST_DID_DOMAIN', 'localhost')
            self.hostport = os.environ.get('HOST_DID_PORT', '9527')
            
        self.hosted_dir.mkdir(parents=True, exist_ok=True)
        
        # 保持现有的其他初始化逻辑
        self.hostname = socket.gethostname()
        self.hostip = socket.gethostbyname(self.hostname)
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'DIDHostManager':
        """为指定域名创建DID托管管理器"""
        return cls(hosted_dir=None, host=host, port=port)
    
    def is_duplicate_did(self, did_document: dict) -> bool:
        """
        检查DID是否已存在
        
        Args:
            did_document: DID文档
            
        Returns:
            bool: 是否存在重复的DID
        """
        def _get_did_id(did_document):
            if isinstance(did_document, str):  # 可能是 JSON 字符串
                try:
                    did_document = json.loads(did_document)  # 解析 JSON
                except json.JSONDecodeError:
                    return None  # 解析失败，返回 None
            if isinstance(did_document, dict):  # 确保是字典
                return did_document.get('id')  # 取值
            return None


        did_id = _get_did_id(did_document)
        if not did_id:
            return False
            
        for user_req in self.hosted_dir.glob('user_*/did_document_request.json'):
            try:
                with open(user_req, 'r', encoding='utf-8') as f:
                    req_doc = json.load(f)
                if req_doc.get('id') == did_id:
                    return True
            except Exception as e:
                logger.error(f"读取DID文档失败: {e}")
        return False
    
    def store_did_document(self, did_document: dict) -> tuple[bool, dict, str]:
        """
        存储DID文档
        
        Args:
            did_document: DID文档
            
        Returns:
            tuple: (是否成功, 新的DID文档, 错误信息)
        """
        try:
            # 生成新的sid
            sid = secrets.token_hex(8)
            user_dir = self.hosted_dir / f"user_{sid}"
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存原始请求
            req_path = user_dir / 'did_document_request.json'
            with open(req_path, 'w', encoding='utf-8') as f:
                json.dump(did_document, f, ensure_ascii=False, indent=2)
            
            # 修改DID文档
            modified_doc = self._modify_did_document(did_document.copy(), sid)
            
            # 保存修改后的文档
            did_path = user_dir / 'did_document.json'
            with open(did_path, 'w', encoding='utf-8') as f:
                json.dump(modified_doc, f, ensure_ascii=False, indent=2)
                
            return True, modified_doc, ""
            
        except Exception as e:
            error_msg = f"存储DID文档失败: {e}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def _modify_did_document(self, did_document: dict, sid: str) -> dict:
        """
        修改DID文档，更新主机信息和ID
        
        Args:
            did_document: 原始DID文档
            sid: 新的会话ID
            
        Returns:
            dict: 修改后的DID文档
        """
        old_id = did_document['id']
        parts = old_id.split(':')
        
        if len(parts) > 3:
            # 更新主机和端口部分
            parts[2] = f"{self.hostdomain}%3A{self.hostport}"
            # 将user替换为hostuser
            for i in range(len(parts)):
                if parts[i] == "user":
                    parts[i] = "hostuser"
            parts[-1] = sid
            new_id = ':'.join(parts)
            did_document['id'] = new_id
            
            # 更新相关字段
            def replace_all_old_id(did_document, old_id, new_id):
                #递归遍历整个 DID 文档，替换所有出现的 old_id
                if isinstance(did_document, dict):  # 处理字典
                    return {
                        key: replace_all_old_id(value, old_id, new_id)
                        for key, value in did_document.items()
                    }
                elif isinstance(did_document, list):  # 处理列表
                    return [replace_all_old_id(item, old_id, new_id) for item in did_document]
                elif isinstance(did_document, str):  # 处理字符串
                    return did_document.replace(old_id, new_id)
                else:
                    return did_document  # 其他类型不变
            # 全局替换所有 `old_id`
            did_document = replace_all_old_id(did_document, old_id, new_id)
    
                        
        return did_document


async def register_hosted_did(agent:ANPUser):
    try:
        from anp_open_sdk_framework.server.publisher.anp_sdk_publisher_mail_backend import EnhancedMailManager



        did_document = agent.user_data.did_document
        if did_document is None:
            raise ValueError("当前 LocalAgent 未包含 did_document")
        from anp_open_sdk.config import get_global_config
        config = get_global_config()
        use_local = config.mail.use_local_backend
        logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")
        mail_manager = EnhancedMailManager(use_local_backend=use_local)
        register_email = os.environ.get('REGISTER_MAIL_USER')
        if not register_email:
            raise ValueError("REGISTER_MAIL_USER 环境变量未设置")
        success = mail_manager.send_hosted_did_request(did_document, register_email)
        if success:
            logger.info(f"{agent.id}的托管DID申请邮件已发送")
            return True
        else:
            logger.error("发送托管DID申请邮件失败")
            return False
    except Exception as e:
        logger.error(f"注册托管DID失败: {e}")
        return False


async def check_hosted_did(agent: ANPUser):
    try:
        import re
        import json
        from anp_open_sdk.config import get_global_config
        config = get_global_config()
        use_local = config.mail.use_local_backend
        logger.debug(f"注册邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")
        mail_manager = EnhancedMailManager(use_local_backend=use_local)
        responses = mail_manager.get_unread_hosted_responses()
        if not responses:
            return "没有找到匹配的托管 DID 激活邮件"
        count = 0
        for response in responses:
            try:
                body = response.get('content', '')
                message_id = response.get('message_id')
                if not message_id:
                    logger.warning("邮件缺少message_id，跳过处理")
                    continue
                try:
                    if isinstance(body, str):
                        did_document = json.loads(body)
                    else:
                        did_document = body
                except Exception as e:
                    logger.debug(f"无法解析 did_document: {e}")
                    continue
                did_id = did_document.get('id', '')
                m = re.search(r'did:wba:([^:]+)%3A(\d+):', did_id)
                if not m:
                    logger.debug(f"无法从id中提取host:port: {did_id}")
                    continue
                host = m.group(1)
                port = m.group(2)
                success, hosted_dir_name = agent.create_hosted_did(host, port, did_document)
                if success:
                    mail_manager.mark_message_as_read(message_id)
                    logger.info(f"已创建{agent.id}申请的托管DID{did_id}的文件夹: {hosted_dir_name}")
                    count += 1
                else:
                    logger.error(f"创建托管DID文件夹失败: {host}:{port}")
            except Exception as e:
                logger.error(f"处理邮件时出错: {e}")
        if count > 0:
            return f"成功处理{count}封托管DID邮件"
        else:
            return "未能成功处理任何托管DID邮件"
    except Exception as e:
        logger.error(f"检查托管DID时发生错误: {e}")
        return f"检查托管DID时发生错误: {e}"


async def check_did_host_request():
    from anp_open_sdk_framework.server.publisher.anp_sdk_publisher_mail_backend import \
        EnhancedMailManager
    try:
        config = get_global_config()
        use_local = config.mail.use_local_backend
        logger.debug(f"管理邮箱检查前初始化，使用本地文件邮件后端参数设置:{use_local}")
        mail_manager = EnhancedMailManager(use_local_backend=use_local)
        did_manager = DIDHostManager()

        did_requests = mail_manager.get_unread_did_requests()
        if not did_requests:
            return "没有新的DID托管请求"

        result = "开始处理DID托管请求\n"
        for request in did_requests:
            did_document = request['content']
            from_address = request['from_address']
            message_id = request['message_id']

            parsed_json = json.loads(did_document)
            did_document_dict = dict(parsed_json)

            if did_manager.is_duplicate_did(did_document):
                mail_manager.send_reply_email(
                    from_address,
                    "DID已申请",
                    "重复的DID申请，请联系管理员"
                )
                mail_manager.mark_message_as_read(message_id)
                result += f"{from_address}的DID {did_document_dict.get('id')} 已申请，退回\n"
                continue

            success, new_did_doc, error = did_manager.store_did_document(did_document_dict)
            if success:
                mail_manager.send_reply_email(
                    from_address,
                    "ANP HOSTED DID RESPONSED",
                    json.dumps(new_did_doc, ensure_ascii=False, indent=2))

                result += f"{from_address}的DID {new_did_doc['id']} 已保存\n"
            else:
                mail_manager.send_reply_email(
                    from_address,
                    "DID托管申请失败",
                    f"处理DID文档时发生错误: {error}"
                )
                result += f"{from_address}的DID处理失败: {error}\n"
            mail_manager.mark_message_as_read(message_id)
        logger.info(f"DID托管受理检查结果{result}")
        return result
    except Exception as e:
        error_msg = f"处理DID托管请求时发生错误: {e}"
        logger.error(error_msg)
        return error_msg
