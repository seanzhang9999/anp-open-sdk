"""
ANP Open SDK Protocol Wrapper - Verification Methods

This module provides verification method implementations to replace agent_connect library dependency.
"""

import base64
import base58
import hashlib
import logging
from typing import Dict, Union, Optional
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

logger = logging.getLogger(__name__)

# Curve mapping for different verification methods
CURVE_MAPPING = {
    'secp256k1': ec.SECP256K1(),
    'P-256': ec.SECP256R1(),
    'Ed25519': 'Ed25519'
}


def _decode_base64url(data: str) -> bytes:
    """Decode base64url format data"""
    # Add padding if needed
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def _encode_base64url(data: bytes) -> str:
    """Encode bytes data to base64url format"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


class BaseVerificationMethod:
    """Base class for verification methods"""
    
    def __init__(self, verification_method: Dict):
        self.verification_method = verification_method
        self.public_key = self._extract_public_key()
    
    def _extract_public_key(self) -> Union[ec.EllipticCurvePublicKey, ed25519.Ed25519PublicKey]:
        """Extract public key from verification method"""
        raise NotImplementedError
    
    def encode_signature(self, signature_bytes: bytes) -> str:
        """Encode signature bytes to string format"""
        raise NotImplementedError
    
    def verify_signature(self, content_hash: bytes, signature: str) -> bool:
        """Verify signature against content hash"""
        raise NotImplementedError


class EcdsaSecp256k1VerificationKey2019(BaseVerificationMethod):
    """ECDSA secp256k1 verification method implementation"""
    
    def _extract_public_key(self) -> ec.EllipticCurvePublicKey:
        """Extract secp256k1 public key from verification method"""
        if 'publicKeyJwk' in self.verification_method:
            return self._extract_from_jwk(self.verification_method['publicKeyJwk'])
        elif 'publicKeyMultibase' in self.verification_method:
            return self._extract_from_multibase(self.verification_method['publicKeyMultibase'])
        else:
            raise ValueError("Unsupported public key format for EcdsaSecp256k1VerificationKey2019")
    
    def _extract_from_jwk(self, jwk: Dict) -> ec.EllipticCurvePublicKey:
        """Extract public key from JWK format"""
        if jwk.get('kty') != 'EC':
            raise ValueError("Invalid JWK: kty must be EC")
        
        if jwk.get('crv') != 'secp256k1':
            raise ValueError("Invalid curve for secp256k1 verification method")
        
        try:
            x = int.from_bytes(_decode_base64url(jwk['x']), 'big')
            y = int.from_bytes(_decode_base64url(jwk['y']), 'big')
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            return public_numbers.public_key()
        except Exception as e:
            raise ValueError(f"Invalid JWK parameters: {str(e)}")
    
    def _extract_from_multibase(self, multibase: str) -> ec.EllipticCurvePublicKey:
        """Extract public key from multibase format"""
        if not multibase.startswith('z'):
            raise ValueError("Unsupported multibase encoding format, must start with 'z' (base58btc)")
        
        try:
            key_bytes = base58.b58decode(multibase[1:])
            if len(key_bytes) != 33:
                raise ValueError("Invalid secp256k1 public key length")
            
            return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid multibase key: {str(e)}")
    
    def encode_signature(self, signature_bytes: bytes) -> str:
        """
        Encode signature bytes to base64url format.
        Converts DER format to R|S format if needed.
        """
        try:
            # If signature is in DER format, decode it
            if len(signature_bytes) > 64:
                # Parse DER format
                r, s = self._decode_der_signature(signature_bytes)
                # Convert to R|S format (32 bytes each)
                r_bytes = r.to_bytes(32, 'big')
                s_bytes = s.to_bytes(32, 'big')
                signature_bytes = r_bytes + s_bytes
            
            return _encode_base64url(signature_bytes)
        except Exception as e:
            raise ValueError(f"Failed to encode signature: {str(e)}")
    
    def _decode_der_signature(self, der_signature: bytes) -> tuple:
        """Decode DER format signature to (r, s) integers"""
        try:
            # Simple DER decoder for ECDSA signature
            if der_signature[0] != 0x30:
                raise ValueError("Invalid DER signature")
            
            # Skip sequence tag and length
            offset = 2
            
            # Read r
            if der_signature[offset] != 0x02:
                raise ValueError("Invalid DER signature - missing r integer")
            offset += 1
            r_len = der_signature[offset]
            offset += 1
            r_bytes = der_signature[offset:offset + r_len]
            r = int.from_bytes(r_bytes, 'big')
            offset += r_len
            
            # Read s
            if der_signature[offset] != 0x02:
                raise ValueError("Invalid DER signature - missing s integer")
            offset += 1
            s_len = der_signature[offset]
            offset += 1
            s_bytes = der_signature[offset:offset + s_len]
            s = int.from_bytes(s_bytes, 'big')
            
            return r, s
        except Exception as e:
            raise ValueError(f"Failed to decode DER signature: {str(e)}")
    
    def verify_signature(self, content_hash: bytes, signature: str) -> bool:
        """Verify ECDSA signature"""
        try:
            signature_bytes = _decode_base64url(signature)
            
            # Convert R|S format to DER if needed
            if len(signature_bytes) == 64:
                signature_bytes = self._encode_der_signature(signature_bytes)
            
            self.public_key.verify(signature_bytes, content_hash, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception as e:
            logger.debug(f"Signature verification failed: {str(e)}")
            return False
    
    def _encode_der_signature(self, rs_signature: bytes) -> bytes:
        """Encode R|S format signature to DER format"""
        if len(rs_signature) != 64:
            raise ValueError("R|S signature must be 64 bytes")
        
        r_bytes = rs_signature[:32]
        s_bytes = rs_signature[32:]
        
        # Remove leading zeros but keep at least one byte
        r_bytes = r_bytes.lstrip(b'\x00') or b'\x00'
        s_bytes = s_bytes.lstrip(b'\x00') or b'\x00'
        
        # Add padding if first bit is 1 (to avoid negative interpretation)
        if r_bytes[0] & 0x80:
            r_bytes = b'\x00' + r_bytes
        if s_bytes[0] & 0x80:
            s_bytes = b'\x00' + s_bytes
        
        # Build DER structure
        r_der = b'\x02' + bytes([len(r_bytes)]) + r_bytes
        s_der = b'\x02' + bytes([len(s_bytes)]) + s_bytes
        
        sequence_content = r_der + s_der
        return b'\x30' + bytes([len(sequence_content)]) + sequence_content


class Ed25519VerificationKey2020(BaseVerificationMethod):
    """Ed25519 verification method implementation"""
    
    def _extract_public_key(self) -> ed25519.Ed25519PublicKey:
        """Extract Ed25519 public key from verification method"""
        if 'publicKeyJwk' in self.verification_method:
            return self._extract_from_jwk(self.verification_method['publicKeyJwk'])
        elif 'publicKeyBase58' in self.verification_method:
            return self._extract_from_base58(self.verification_method['publicKeyBase58'])
        elif 'publicKeyMultibase' in self.verification_method:
            return self._extract_from_multibase(self.verification_method['publicKeyMultibase'])
        else:
            raise ValueError("Unsupported public key format for Ed25519VerificationKey2020")
    
    def _extract_from_jwk(self, jwk: Dict) -> ed25519.Ed25519PublicKey:
        """Extract public key from JWK format"""
        if jwk.get('kty') != 'OKP' or jwk.get('crv') != 'Ed25519':
            raise ValueError("Invalid JWK parameters for Ed25519")
        
        try:
            key_bytes = base64.b64decode(jwk['x'] + '==')
            return ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid Ed25519 JWK: {str(e)}")
    
    def _extract_from_base58(self, base58_key: str) -> ed25519.Ed25519PublicKey:
        """Extract public key from base58 format"""
        try:
            key_bytes = base58.b58decode(base58_key)
            return ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid base58 key: {str(e)}")
    
    def _extract_from_multibase(self, multibase: str) -> ed25519.Ed25519PublicKey:
        """Extract public key from multibase format"""
        if not multibase.startswith('z'):
            raise ValueError("Unsupported multibase encoding")
        
        try:
            key_bytes = base58.b58decode(multibase[1:])
            return ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid multibase key: {str(e)}")
    
    def encode_signature(self, signature_bytes: bytes) -> str:
        """Encode Ed25519 signature to base64url format"""
        return _encode_base64url(signature_bytes)
    
    def verify_signature(self, content_hash: bytes, signature: str) -> bool:
        """Verify Ed25519 signature"""
        try:
            signature_bytes = _decode_base64url(signature)
            self.public_key.verify(signature_bytes, content_hash)
            return True
        except Exception as e:
            logger.debug(f"Ed25519 signature verification failed: {str(e)}")
            return False


class JsonWebKey2020(EcdsaSecp256k1VerificationKey2019):
    """JsonWebKey2020 verification method - inherits from ECDSA implementation"""
    pass


# Factory function to create verification method instances
def create_verification_method(verification_method: Dict) -> BaseVerificationMethod:
    """
    Create appropriate verification method instance based on type.
    
    Args:
        verification_method: Verification method dictionary from DID document
        
    Returns:
        BaseVerificationMethod: Verification method instance
        
    Raises:
        ValueError: If verification method type is unsupported
    """
    method_type = verification_method.get('type')
    if not method_type:
        raise ValueError("Verification method missing 'type' field")
    
    if method_type == 'EcdsaSecp256k1VerificationKey2019':
        return EcdsaSecp256k1VerificationKey2019(verification_method)
    elif method_type in ['Ed25519VerificationKey2020', 'Ed25519VerificationKey2018']:
        return Ed25519VerificationKey2020(verification_method)
    elif method_type == 'JsonWebKey2020':
        return JsonWebKey2020(verification_method)
    else:
        raise ValueError(f"Unsupported verification method type: {method_type}")