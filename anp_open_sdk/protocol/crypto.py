"""
Protocol Layer - Pure Cryptographic Operations

This module contains only pure cryptographic operations without any DID-specific logic.
It provides the foundation for all signature operations used by the SDK layer.
"""

import base64
import logging
from typing import Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CryptoSigner(ABC):
    """Abstract base class for cryptographic signers"""
    
    @abstractmethod
    def sign(self, payload: Union[str, bytes], private_key_bytes: bytes) -> bytes:
        """Sign payload and return signature bytes"""
        pass
    
    @abstractmethod
    def verify(self, payload: Union[str, bytes], signature_bytes: bytes, public_key_bytes: bytes) -> bool:
        """Verify signature"""
        pass


class Secp256k1Signer(CryptoSigner):
    """Pure secp256k1 cryptographic signer"""
    
    def sign(self, payload: Union[str, bytes], private_key_bytes: bytes) -> bytes:
        """Sign payload using secp256k1 and return DER signature"""
        try:
            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload
            
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes
            
            private_key_obj = ec.derive_private_key(
                int.from_bytes(private_key_bytes, byteorder="big"), 
                ec.SECP256K1()
            )
            
            # Generate DER format signature
            signature_der = private_key_obj.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
            return signature_der
            
        except Exception as e:
            logger.error(f"Secp256k1 signing failed: {e}")
            raise
    
    def verify(self, payload: Union[str, bytes], signature_bytes: bytes, public_key_bytes: bytes) -> bool:
        """Verify secp256k1 signature"""
        try:
            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload

            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes

            # Create public key object based on format
            if len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
                # Uncompressed format
                x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
                y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
                public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
                public_key_obj = public_numbers.public_key()
            elif len(public_key_bytes) == 33:
                # Compressed format
                public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
            else:
                logger.error(f"Unsupported secp256k1 public key length: {len(public_key_bytes)}")
                return False

            # Verify signature (expects DER format)
            public_key_obj.verify(signature_bytes, payload_bytes, ec.ECDSA(hashes.SHA256()))
            return True

        except Exception as e:
            logger.error(f"Secp256k1 verification failed: {e}")
            return False


class Ed25519Signer(CryptoSigner):
    """Pure Ed25519 cryptographic signer"""
    
    def sign(self, payload: Union[str, bytes], private_key_bytes: bytes) -> bytes:
        """Sign payload using Ed25519"""
        try:
            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload
            
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            signature = private_key_obj.sign(payload_bytes)
            return signature
            
        except Exception as e:
            logger.error(f"Ed25519 signing failed: {e}")
            raise
    
    def verify(self, payload: Union[str, bytes], signature_bytes: bytes, public_key_bytes: bytes) -> bool:
        """Verify Ed25519 signature"""
        try:
            # Handle payload types
            if isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            else:
                payload_bytes = payload

            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            if len(public_key_bytes) != 32:
                logger.error(f"Invalid Ed25519 public key length: {len(public_key_bytes)}")
                return False
            
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key_obj.verify(signature_bytes, payload_bytes)
            return True

        except Exception as e:
            logger.error(f"Ed25519 verification failed: {e}")
            return False


class SignatureEncoder:
    """Utility class for signature encoding/decoding operations"""
    
    @staticmethod
    def der_to_rs_format(der_signature: bytes, curve_size: int = 32) -> bytes:
        """Convert DER signature to R|S format"""
        try:
            from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
            
            r, s = decode_dss_signature(der_signature)
            r_bytes = r.to_bytes(curve_size, byteorder='big')
            s_bytes = s.to_bytes(curve_size, byteorder='big')
            return r_bytes + s_bytes
            
        except Exception as e:
            logger.error(f"Failed to convert DER to R|S format: {e}")
            raise
    
    @staticmethod
    def rs_to_der_format(rs_signature: bytes) -> bytes:
        """Convert R|S format to DER signature"""
        try:
            from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
            
            if len(rs_signature) != 64:
                raise ValueError(f"Invalid R|S signature length: {len(rs_signature)}, expected 64")
            
            r_bytes = rs_signature[:32]
            s_bytes = rs_signature[32:]
            
            r = int.from_bytes(r_bytes, 'big')
            s = int.from_bytes(s_bytes, 'big')
            
            if r == 0 or s == 0:
                raise ValueError("Invalid signature: R or S is zero")
            
            return encode_dss_signature(r, s)
            
        except Exception as e:
            logger.error(f"Failed to convert R|S to DER format: {e}")
            raise
    
    @staticmethod
    def encode_base64url(data: bytes) -> str:
        """Encode bytes to base64url string"""
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')
    
    @staticmethod
    def decode_base64url(data: str) -> bytes:
        """Decode base64url string to bytes"""
        return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


# Factory functions
def create_secp256k1_signer() -> CryptoSigner:
    """Create secp256k1 signer"""
    return Secp256k1Signer()


def create_ed25519_signer() -> CryptoSigner:
    """Create Ed25519 signer"""
    return Ed25519Signer()


def get_signer_for_key_type(key_type: str) -> CryptoSigner:
    """Get appropriate signer for key type"""
    if key_type.lower() in ['secp256k1', 'ecdsa']:
        return create_secp256k1_signer()
    elif key_type.lower() in ['ed25519']:
        return create_ed25519_signer()
    else:
        raise ValueError(f"Unsupported key type: {key_type}")