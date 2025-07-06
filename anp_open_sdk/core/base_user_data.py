from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


class BaseUserData(ABC):
    """
    用户数据的基础抽象类。
    定义了所有用户数据类型必须实现的通用接口。
    """

    @abstractmethod
    def get_did(self) -> str:
        """获取用户的DID。"""
        pass

    @abstractmethod
    def get_token_from_remote(self, remote_did: str) -> Optional[str]:
        """从存储中获取与特定远程DID通信的Token。"""
        pass

    @abstractmethod
    def save_token_for_remote(self, remote_did: str, token: str):
        """为特定的远程DID保存Token。"""
        pass

    # 为了向后兼容，提供 did 属性
    @property
    def did(self) -> str:
        """获取用户的DID（向后兼容属性）。"""
        return self.get_did()


class BaseUserDataManager(ABC):
    """
    用户数据管理器的基础抽象类。
    定义了所有用户数据管理器必须实现的通用接口。
    """

    @abstractmethod
    def get_user_data(self, did: str) -> Optional[BaseUserData]:
        """根据DID获取用户数据。"""
        pass

    @abstractmethod
    def get_all_users(self) -> List[BaseUserData]:
        """获取所有用户数据。"""
        pass

    @abstractmethod
    def get_user_data_by_name(self, name: str) -> Optional[BaseUserData]:
        """根据用户名获取用户数据。"""
        pass


@dataclass
class LocalUserData(BaseUserData):
    """
    代表从本地文件或内存加载的用户数据。

    重要:
    根据Python的规则，所有没有默认值的字段 (did_value, did_doc, private_keys)
    必须定义在有默认值的字段 (token_storage) 之前。
    """
    # --- 1. 没有默认值的字段 ---
    did_value: str  # 避免与父类方法名冲突
    did_doc: Dict[str, Any]
    private_keys: Dict[str, Any]

    # --- 2. 有默认值的字段 ---
    token_storage: Dict[str, str] = field(default_factory=dict)

    def get_did(self) -> str:
        """实现抽象方法，返回DID值。"""
        return self.did_value

    def get_token_from_remote(self, remote_did: str) -> Optional[str]:
        """从内存中的token_storage获取Token。"""
        return self.token_storage.get(remote_did)

    def save_token_for_remote(self, remote_did: str, token: str):
        """将Token保存到内存中的token_storage。"""
        self.token_storage[remote_did] = token
