import threading
import time
from anp_open_sdk.utils.log_base import  logging as logger
from anp_open_sdk_framework.server.anp_server import ANP_Server


class DemoSDKManager:
    """SDK管理器"""
    
    def __init__(self):
        self.sdk = None
        self.server_thread = None

    def initialize_sdk(self) -> ANP_Server:
        """初始化SDK"""
        logger.debug("初始化ANPSDK...")
        self.sdk = ANP_Server()
        return self.sdk

    def start_server(self, sdk: ANP_Server):
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

    def stop_server(self, sdk: ANP_Server):
        """停止服务器"""
        if sdk:
            logger.debug("停止服务器...")
            sdk.stop_server()