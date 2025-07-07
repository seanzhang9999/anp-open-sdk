#!/usr/bin/env python3
"""
Debug script to trace signature creation and verification
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anp_open_sdk.auth_methods.wba.implementation import PureWBASigner
from anp_open_sdk.auth.schemas import DIDCredentials
import hashlib
import jcs

# Test data
test_data = {
    "nonce": "test_nonce_123",
    "timestamp": "2025-07-07T22:30:00Z",
    "service": "localhost",
    "did": "did:wba:localhost%3A9527:wba:user:28cddee0fade0258",
    "resp_did": "did:wba:localhost%3A9527:wba:user:42cd01f324d61962"
}

print("=== Signature Debug Test ===")

# Create canonical JSON and hash
canonical_json = jcs.canonicalize(test_data)
content_hash = hashlib.sha256(canonical_json).digest()

print(f"Canonical JSON: {canonical_json}")
print(f"Content hash (hex): {content_hash.hex()}")

# Sample keys (from the logs)
sample_private_key = bytes.fromhex("placeholder_private_key_32_bytes")  # Replace with actual key
sample_public_key = bytes.fromhex("04efe954993093673be33f64bb274b86077fbd1a987239e05ecceaca00bdacedfb137290fbeea4801af4b3b8f0f4a509994b3c62bb32a671718f3c281ac7dddc95")

print(f"Public key length: {len(sample_public_key)}")
print(f"Public key (hex): {sample_public_key.hex()}")

# Create signer
signer = PureWBASigner()

# Test 1: Create signature using signer
print("\n=== Test 1: PureWBASigner.create_signature ===")
try:
    signature_b64 = signer.create_signature(content_hash, sample_private_key)
    print(f"Signature (base64url): {signature_b64}")
    
    # Test verification
    print("\n=== Test 2: PureWBASigner.verify_signature ===")
    is_valid = signer.verify_signature(content_hash, signature_b64, sample_public_key)
    print(f"Verification result: {is_valid}")
    
except Exception as e:
    print(f"Error in signer test: {e}")

print("\n=== Test 3: DIDCredentials.sign (if available) ===")
# This would need actual DID credentials to test
print("Skipping DIDCredentials test - would need actual credentials")

print("\n=== Debug complete ===")