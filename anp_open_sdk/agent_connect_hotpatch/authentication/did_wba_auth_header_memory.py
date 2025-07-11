# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# AgentConnect: https://github.com/agent-network-protocol/AgentConnect
# Author: GaoWei Chang
# Email: chgaowei@gmail.com
# Website: https://agent-network-protocol.com/
#
# This project is open-sourced under the MIT License. For details, please see the LICENSE file.

import json
import logging
from typing import Dict, Optional
from urllib.parse import urlparse

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

logger = logging.getLogger(__name__)
# Import agent_connect for DID authentication
from .did_wba import (
    generate_auth_header_two_way
)

class DIDWbaAuthHeaderMemory:
    """
    Simplified DID authentication client providing HTTP authentication headers.
    """
    
    def __init__(self, did_document: str, private_key:ec.EllipticCurvePrivateKey):
        """
        Initialize the DID authentication client.
        
        Args:
            did_document_path: Path to the DID document (absolute or relative path)
            private_key_path: Path to the private key (absolute or relative path)
        """

        # State variables
        self.did_document = did_document
        self.private_key =private_key
        self.auth_headers = {}  # Store DID authentication headers by domain
        self.tokens = {}  # Store tokens by domain
        
        # logger.debug("DIDWbaAuthHeader initialized")
    
    def _get_domain(self, server_url: str) -> str:
        """从URL中提取域名，兼容FastAPI/Starlette的Request对象"""
        # 兼容FastAPI/Starlette的Request对象
        try:
            from starlette.requests import Request
        except ImportError:
            Request = None
        if Request and isinstance(server_url, Request):
            # 优先使用base_url（去除路径），否则用url
            url_str = str(getattr(server_url, "base_url", None) or getattr(server_url, "url", None))
        else:
            url_str = str(server_url)
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.split(':')[0]
        return domain

    
    def _sign_callback(self, content: bytes, method_fragment: str) -> bytes:
        """Sign callback function. Returns None on failure."""

        try:
            signature = self.private_key.sign(
                content,
                ec.ECDSA(hashes.SHA256())
            )
            
            logger.debug(f"Signed content with method fragment: {method_fragment}")
            return signature
        except Exception as e:
            logger.error(f"Error signing content: {e}")
            return None
    
    def _generate_auth_header_two_way(self, domain: str, resp_did:str) -> str:
        """Generate DID authentication header"""
        try:
            did_document = self.did_document
            auth_header = generate_auth_header_two_way(
                did_document,
                resp_did,
                domain,
                self._sign_callback
            )
            if not auth_header:
                logger.warning(f"Failed to generate auth header for domain {domain}, possibly due to signing failure.")
                return None


            # logger.debug(f"Generated authentication header for domain {domain}: {auth_header[:30]}...")
            return auth_header
        except Exception as e:
            logger.debug(f"Error generating authentication header: {e}")
            raise

    def get_auth_header(self, server_url: str, force_new: bool = False) -> Dict[str, str]:
        """
        Get authentication header.

        Args:
            server_url: Server URL
            force_new: Whether to force generate a new DID authentication header

        Returns:
            Dict[str, str]: HTTP header dictionary
        """
        domain = self._get_domain(server_url)

        # If there is a token and not forcing a new authentication header, return the token
        if domain in self.tokens and not force_new:
            token = self.tokens[domain]
            logging.debug(f"Using existing token for domain {domain}")
            return {"Authorization": f"Bearer {token}"}

        # Otherwise, generate or use existing DID authentication header
        if domain not in self.auth_headers or force_new:
            self.auth_headers[domain] = self._generate_auth_header(domain)

        logging.debug(f"Using DID authentication header for domain {domain}")
        return {"Authorization": self.auth_headers[domain]}

    def _generate_auth_header(self, domain: str) -> str:
        """Generate DID authentication header"""
        try:
            did_document = self.did_document
            from anp_open_sdk.agent_connect_hotpatch.authentication.did_wba import generate_auth_header
            auth_header = generate_auth_header(
                did_document,
                domain,
                self._sign_callback
            )

            logging.debug(f"Generated authentication header for domain {domain}: {auth_header[:30]}...")
            return auth_header
        except Exception as e:
            logging.error(f"Error generating authentication header: {e}")
            raise

    def get_auth_header_two_way(self, server_url: str, resp_did: str, force_new: bool = False) -> Dict[str, str]:
        """
        获取认证头。
        支持 server_url 为 FastAPI/Starlette Request 对象或字符串。
        """
        domain = self._get_domain(server_url)
        
        # If there is a token and not forcing a new authentication header, return the token
        if domain in self.tokens and not force_new:
            token = self.tokens[domain]
            # logger.debug(f"Using existing token for domain {domain}")
            return {"Authorization": f"Bearer {token}"}
        
        # Otherwise, generate or use existing DID authentication header
        if domain not in self.auth_headers or force_new:
            new_header = self._generate_auth_header_two_way(domain, resp_did)
            if new_header:
                self.auth_headers[domain] = new_header
            else:
                # 生成失败，确保不会使用过期的头
                self.auth_headers.pop(domain, None)
        
        auth_header_value = self.auth_headers.get(domain)
        if auth_header_value:
            return {"Authorization": auth_header_value}
        else:
            logger.warning(f"No valid authentication header or token available for domain {domain}.")
            return {}
    
    def update_token(self, server_url: str, headers: Dict[str, str]) -> Optional[str]:
        """
        Update token from response headers.
        
        Args:
            server_url: Server URL
            headers: Response header dictionary
            
        Returns:
            Optional[str]: Updated token, or None if no valid token is found
        """


        domain = self._get_domain(server_url)
        auth_data = headers.get("Authorization")
        if not auth_data:
            logger.debug(f"响应头中没有 Authorization 字段，跳过 token 更新。URL: {server_url}")
            return None

        if auth_data.startswith('Bearer '):
            token_value = auth_data[7:]  # 移除 "Bearer " 前缀
            logger.debug(f"解析到bearer token: {token_value}")
            return token_value

        try:
            auth_data = json.loads(auth_data)
            token_type = auth_data[0].get("token_type")
            access_token = auth_data[0].get("access_token")
            if token_type and token_type.lower() == "bearer":
                return access_token
            else:
                return None
        except json.JSONDecodeError:
            logger.debug(f"No valid token found in response headers for  {server_url}")
            return None
    
    def clear_token(self, server_url: str) -> None:
        """
        Clear token for the specified domain.
        
        Args:
            server_url: Server URL
        """
        domain = self._get_domain(server_url)
        if domain in self.tokens:
            del self.tokens[domain]
            # logger.debug(f"Cleared token for domain {domain}")
        else:
            logger.debug(f"No stored token for domain {domain}")
    
    def clear_all_tokens(self) -> None:
        """Clear all tokens for all domains"""
        self.tokens.clear()
        # logger.debug("Cleared all tokens for all domains")



# # Example usage
# async def example_usage():
#     # Get current script directory
#     current_dir = Path(__file__).parent
#     # Get project root directory (parent of current directory)
#     base_dir = current_dir.parent
    
#     # Create client with absolute paths
#     client = DIDWbaAuthHeader(
#         did_document_path=str(base_dir / "use_did_test_public/did.json"),
#         private_key_path=str(base_dir / "use_did_test_public/key-1_private.pem")
#     )
    
#     server_url = "http://localhost:9870"
    
#     # Get authentication header (first call, returns DID authentication header)
#     headers = client.get_auth_header(server_url)
    
#     # Send request
#     async with aiohttp.ClientSession() as session:
#         async with session.get(
#             f"{server_url}/agents/travel/hotel/ad/ph/12345/ad.json", 
#             headers=headers
#         ) as response:
#             # Check response
#             logger.debug(f"Status code: {response.status}")
            
#             # If authentication is successful, update token
#             if response.status == 200:
#                 token = client.update_token(server_url, dict(response.headers))
#                 if token:
#                     logger.debug(f"Received token: {token[:30]}...")
#                 else:
#                     logger.debug("No token received in response headers")
            
#             # If authentication fails and a token was used, clear the token and retry
#             elif response.status == 401:
#                 logger.debug("Invalid token, clearing and using DID authentication")
#                 client.clear_token(server_url)
#                 # Retry request here
    
#     # Get authentication header again (if a token was obtained in the previous step, this will return a token authentication header)
#     headers = client.get_auth_header(server_url)
#     logger.debug(f"Header for second request: {headers}")
    
#     # Force use of DID authentication header
#     headers = client.get_auth_header(server_url, force_new=True)
#     logger.debug(f"Forced use of DID authentication header: {headers}")
    
#     # Test different domain
#     another_server_url = "http://api.example.com"
#     headers = client.get_auth_header(another_server_url)
#     logger.debug(f"Header for another domain: {headers}")

# if __name__ == "__main__":
#     asyncio.run(example_usage())