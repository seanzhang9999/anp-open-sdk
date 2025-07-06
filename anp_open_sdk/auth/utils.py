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

"""
Authentication utility functions.
"""
import base64
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Dict
import logging

from anp_open_sdk.config import get_global_config

logger = logging.getLogger(__name__)

VALID_SERVER_NONCES: Dict[str, datetime] = {}


def generate_nonce(length: int = 16) -> str:
    """
    Generate a random nonce of specified length.
    Args:
        length: Length of the nonce to generate
    Returns:
        str: Generated nonce
    """
    characters = string.ascii_letters + string.digits
    nonce = ''.join(random.choice(characters) for _ in range(length))
    return nonce


def is_valid_server_nonce(nonce: str) -> bool:
    """
    Check if a nonce is valid and not expired.
    Each nonce can only be used once (proper nonce behavior).
    Args:
        nonce: The nonce to check
    Returns:
        bool: Whether the nonce is valid
    """
    try:
        config = get_global_config()
        nonce_expire_minutes = config.anp_sdk.nonce_expire_minutes
    except Exception:
        nonce_expire_minutes = 5

    current_time = datetime.now(timezone.utc)
    # Clean up expired nonces first
    expired_nonces = [
        n for n, t in VALID_SERVER_NONCES.items()
        if current_time - t > timedelta(minutes=nonce_expire_minutes)
    ]
    for n in expired_nonces:
        del VALID_SERVER_NONCES[n]
    # If nonce was already used, reject it
    if nonce in VALID_SERVER_NONCES:
        logger.warning(f"Nonce already used: {nonce}")
        return False
    # Mark nonce as used
    VALID_SERVER_NONCES[nonce] = current_time
    logger.debug(f"Nonce accepted and marked as used: {nonce}")
    return True


import base58

def multibase_to_bytes(mb_str: str) -> bytes:
    """
    Decodes a multibase string (currently only supports 'z' for base58-btc) into bytes.

    Args:
        mb_str: The multibase encoded string (e.g., "zQ3sh...").

    Returns:
        The decoded bytes.

    Raises:
        ValueError: If the multibase prefix is unsupported or the string is invalid.
    """
    if not isinstance(mb_str, str):
        raise TypeError("Input must be a string.")

    if mb_str.startswith('z'):
        # 'z' is the prefix for base58-btc
        return base58.b58decode(mb_str[1:])
    else:
        # You can add support for other bases here if needed
        raise ValueError(f"Unsupported multibase prefix: '{mb_str[0]}'")