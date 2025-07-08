import threading
import time
from anp_open_sdk.utils.log_base import  logging as logger
from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager


class DemoSDKManager:
    """SDK管理器"""
    
    def __init__(self):
        self.sdk = None
        self.server_thread = None

    def initialize_sdk(self) -> ANPSDK:
        """初始化SDK"""
        logger.debug("初始化ANPSDK...")
        self.sdk = ANPSDK()
        
        # 添加user_data_manager属性（与测试套件保持一致）
        user_data_manager = LocalUserDataManager()
        self.sdk.user_data_manager = user_data_manager
        logger.debug("✓ user_data_manager已注入到SDK")
        
        return self.sdk

    def start_server(self, sdk: ANPSDK):
        """启动服务器"""
        logger.debug("启动服务器...")
        
        def start_server_thread():
            try:
                sdk.start_server()
            except Exception as e:
                logger.error(f"服务器启动错误: {e}")

        self.server_thread = threading.Thread(target=start_server_thread)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # 等待服务器启动
        time.sleep(0.5)
        logger.debug("服务器启动完成")
        return self.server_thread

    def stop_server(self, sdk: ANPSDK):
        """停止服务器"""
        if sdk:
            logger.debug("停止服务器...")
            sdk.stop_server()