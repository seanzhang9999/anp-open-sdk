"""
Pytest configuration and fixtures for refactoring tests.

This file makes fixtures available to all test files in the test_refactoring directory.
"""

# Import all fixtures from test_base.py
from test.test_refactoring.test_base import (
    temp_dir,
    sample_did_document,
    sample_private_key,
    sample_public_key,
    did_config_file,
    event_loop,
    TestDataFactory,
    MockDIDResolver,
    MockTokenStorage,
    MockHttpTransport,
    MockSessionStorage,
    assert_signature_valid,
    create_test_wba_header
)

# Re-export all fixtures and utilities
__all__ = [
    'temp_dir',
    'sample_did_document', 
    'sample_private_key',
    'sample_public_key',
    'did_config_file',
    'event_loop',
    'TestDataFactory',
    'MockDIDResolver',
    'MockTokenStorage',
    'MockHttpTransport',
    'MockSessionStorage',
    'assert_signature_valid',
    'create_test_wba_header'
]