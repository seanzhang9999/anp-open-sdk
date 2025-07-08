"""
Configuration Tests

Tests for configuration file loading and DID method registry configuration.
"""

import pytest
import yaml
import tempfile
from pathlib import Path

from anp_open_sdk.protocol.did_methods import (
    DIDProtocolRegistry, initialize_did_protocol_registry,
    reload_did_protocol_config, get_did_protocol, get_did_protocol_registry
)


class TestDIDMethodConfiguration:
    """Test DID method configuration loading"""
    
    def test_registry_without_config(self):
        """Test registry creation without config file"""
        registry = DIDProtocolRegistry()
        
        # Should have default methods
        supported_methods = registry.get_supported_methods()
        assert 'wba' in supported_methods
        assert 'key' in supported_methods
        assert 'web' in supported_methods
    
    def test_registry_with_valid_config(self, temp_dir):
        """Test registry creation with valid config file"""
        config = {
            "did_methods": {
                "wba": {
                    "enabled": True,
                    "description": "Test WBA method"
                },
                "key": {
                    "enabled": False,
                    "description": "Disabled Key method"
                },
                "web": {
                    "enabled": True,
                    "description": "Test Web method"
                }
            }
        }
        
        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should still have all default methods (enabled/disabled is just metadata)
        supported_methods = registry.get_supported_methods()
        assert 'wba' in supported_methods
        assert 'key' in supported_methods
        assert 'web' in supported_methods
    
    def test_registry_with_external_method_config(self, temp_dir):
        """Test loading external DID method from config"""
        config = {
            "did_methods": {
                "wba": {"enabled": True},
                "custom": {
                    "enabled": True,
                    "module": "nonexistent.module",
                    "class": "CustomDIDProtocol",
                    "parameters": {
                        "param1": "value1",
                        "param2": 42
                    }
                }
            }
        }
        
        config_file = temp_dir / "external_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Should handle missing module gracefully
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should still have default methods
        assert registry.get_protocol("wba") is not None
        
        # Custom method should not be loaded due to missing module
        assert registry.get_protocol("custom") is None
    
    def test_invalid_config_file(self, temp_dir):
        """Test handling of invalid config file"""
        # Create invalid YAML
        invalid_config = temp_dir / "invalid.yaml"
        with open(invalid_config, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        # Should handle gracefully and fall back to defaults
        registry = DIDProtocolRegistry(str(invalid_config))
        
        # Should still have default methods
        supported_methods = registry.get_supported_methods()
        assert 'wba' in supported_methods
    
    def test_nonexistent_config_file(self):
        """Test handling of non-existent config file"""
        # Should handle gracefully
        registry = DIDProtocolRegistry("/nonexistent/config.yaml")
        
        # Should still have default methods
        supported_methods = registry.get_supported_methods()
        assert 'wba' in supported_methods
    
    def test_config_reload(self, temp_dir):
        """Test configuration reloading"""
        # Create initial config
        initial_config = {
            "did_methods": {
                "wba": {"enabled": True},
                "key": {"enabled": False}
            }
        }
        
        config_file = temp_dir / "reload_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(initial_config, f)
        
        registry = DIDProtocolRegistry(str(config_file))
        
        # Add a custom protocol programmatically
        class CustomProtocol:
            def get_method_name(self):
                return "custom"
            
            def create_signed_payload(self, context_data, private_key_bytes):
                return {}
            
            def verify_signed_payload(self, payload_data, public_key_bytes):
                return True
            
            def extract_verification_data(self, payload_data):
                return {}
        
        registry.register_protocol(CustomProtocol())
        assert registry.get_protocol("custom") is not None
        
        # Create new config without custom method
        new_config = {
            "did_methods": {
                "wba": {"enabled": True},
                "key": {"enabled": True},
                "another_custom": {
                    "enabled": True,
                    "module": "missing.module",
                    "class": "MissingClass"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # Reload config
        registry.reload_config(str(config_file))
        
        # Custom protocol should be removed (not in default methods)
        assert registry.get_protocol("custom") is None
        
        # Default methods should still be there
        assert registry.get_protocol("wba") is not None
        assert registry.get_protocol("key") is not None


class TestGlobalRegistryFunctions:
    """Test global registry factory functions"""
    
    def test_initialize_global_registry(self, temp_dir):
        """Test initializing global registry"""
        config = {
            "did_methods": {
                "wba": {"enabled": True, "description": "Global test WBA"}
            }
        }
        
        config_file = temp_dir / "global_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Initialize global registry
        initialize_did_protocol_registry(str(config_file))
        
        # Should be able to get protocols from global registry
        wba_protocol = get_did_protocol("wba")
        assert wba_protocol is not None
        assert wba_protocol.get_method_name() == "wba"
    
    def test_initialize_without_config(self):
        """Test initializing global registry without config"""
        initialize_did_protocol_registry()
        
        # Should have default protocols
        wba_protocol = get_did_protocol("wba")
        assert wba_protocol is not None
    
    def test_get_global_registry(self):
        """Test getting global registry instance"""
        registry = get_did_protocol_registry()
        assert registry is not None
        
        # Should be same instance on subsequent calls
        registry2 = get_did_protocol_registry()
        assert registry is registry2
    
    def test_reload_global_config(self, temp_dir):
        """Test reloading global configuration"""
        # Create config
        config = {
            "did_methods": {
                "wba": {"enabled": True},
                "test_reload": {
                    "enabled": True,
                    "module": "test.module",
                    "class": "TestClass"
                }
            }
        }
        
        config_file = temp_dir / "reload_global_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Initialize
        initialize_did_protocol_registry()
        
        # Reload with new config
        reload_did_protocol_config(str(config_file))
        
        # Should still work
        registry = get_did_protocol_registry()
        assert registry.get_protocol("wba") is not None


class TestComplexConfiguration:
    """Test complex configuration scenarios"""
    
    def test_full_configuration_schema(self, temp_dir):
        """Test loading full configuration with all options"""
        config = {
            "did_methods": {
                "wba": {
                    "enabled": True,
                    "description": "Web-Based Authentication DID method"
                },
                "key": {
                    "enabled": False,
                    "description": "Key-based DID method"
                },
                "enterprise": {
                    "enabled": True,
                    "description": "Enterprise DID method",
                    "module": "enterprise.did_methods",
                    "class": "EnterpriseDIDProtocol",
                    "parameters": {
                        "enterprise_id": "corp_123",
                        "key_algorithm": "secp256k1",
                        "signature_format": "der",
                        "network_config": {
                            "timeout": 30,
                            "retries": 3
                        }
                    }
                }
            },
            "session": {
                "enabled": True,
                "default_expiry_hours": 24,
                "cleanup_interval_minutes": 60
            },
            "tokens": {
                "jwt": {
                    "enabled": True,
                    "algorithm": "RS256",
                    "expiry_hours": 1
                },
                "bearer": {
                    "enabled": True,
                    "expiry_hours": 12
                }
            }
        }
        
        config_file = temp_dir / "full_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Should load without errors
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should have default methods
        assert registry.get_protocol("wba") is not None
        assert registry.get_protocol("key") is not None
        
        # Enterprise method won't load due to missing module, but should not crash
        assert registry.get_protocol("enterprise") is None
    
    def test_partial_configuration(self, temp_dir):
        """Test configuration with only some methods specified"""
        config = {
            "did_methods": {
                "wba": {"enabled": True}
                # key and web not specified
            }
        }
        
        config_file = temp_dir / "partial_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should still have all default methods
        assert registry.get_protocol("wba") is not None
        assert registry.get_protocol("key") is not None
        assert registry.get_protocol("web") is not None
    
    def test_empty_configuration(self, temp_dir):
        """Test empty configuration file"""
        config = {}
        
        config_file = temp_dir / "empty_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should fall back to defaults
        assert registry.get_protocol("wba") is not None
        assert registry.get_protocol("key") is not None
        assert registry.get_protocol("web") is not None
    
    def test_malformed_method_config(self, temp_dir):
        """Test handling of malformed method configuration"""
        config = {
            "did_methods": {
                "wba": {"enabled": True},
                "malformed": {
                    "enabled": True,
                    "module": "test.module",
                    # Missing 'class' field
                    "parameters": {"key": "value"}
                },
                "another_malformed": {
                    "enabled": True,
                    # Missing both 'module' and 'class'
                }
            }
        }
        
        config_file = temp_dir / "malformed_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Should handle gracefully
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should have default methods
        assert registry.get_protocol("wba") is not None
        
        # Malformed methods should not be loaded
        assert registry.get_protocol("malformed") is None
        assert registry.get_protocol("another_malformed") is None


class TestConfigurationEnvironmentVariables:
    """Test configuration with environment variables (future feature)"""
    
    def test_config_with_env_vars_placeholder(self, temp_dir):
        """Test configuration that could support environment variables"""
        # This is a placeholder for future environment variable support
        config = {
            "did_methods": {
                "wba": {
                    "enabled": True,
                    "description": "WBA with env vars"
                },
                "cloud": {
                    "enabled": True,
                    "module": "cloud.did_methods",
                    "class": "CloudDIDProtocol",
                    "parameters": {
                        "api_key": "${CLOUD_API_KEY}",  # Future: env var support
                        "endpoint": "${CLOUD_ENDPOINT}",
                        "region": "us-east-1"
                    }
                }
            }
        }
        
        config_file = temp_dir / "env_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Currently this will just load as literal strings
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should not crash
        assert registry.get_protocol("wba") is not None


class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_validate_required_fields(self, temp_dir):
        """Test validation of required configuration fields"""
        # Config missing required fields for external method
        config = {
            "did_methods": {
                "incomplete": {
                    "enabled": True,
                    "description": "Method without required fields"
                    # Missing module and class
                }
            }
        }
        
        config_file = temp_dir / "incomplete_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        registry = DIDProtocolRegistry(str(config_file))
        
        # Should handle gracefully - incomplete method not loaded
        assert registry.get_protocol("incomplete") is None
    
    def test_validate_method_names(self, temp_dir):
        """Test validation of DID method names"""
        config = {
            "did_methods": {
                "": {  # Empty name
                    "enabled": True,
                    "module": "test.module",
                    "class": "TestClass"
                },
                "invalid-name": {  # Invalid characters
                    "enabled": True,
                    "module": "test.module", 
                    "class": "TestClass"
                }
            }
        }
        
        config_file = temp_dir / "invalid_names_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Should handle gracefully
        registry = DIDProtocolRegistry(str(config_file))
        
        # Invalid methods should not be loaded
        assert registry.get_protocol("") is None
        # Note: invalid-name might actually be loaded, depending on implementation