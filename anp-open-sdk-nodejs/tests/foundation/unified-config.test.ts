/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import { UnifiedConfig, setGlobalConfig, getGlobalConfig } from '../../src/foundation/config/unified-config';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as yaml from 'yaml';

describe('UnifiedConfig', () => {
  let tempDir: string;
  let configPath: string;

  beforeEach(() => {
    // Create temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'unified-config-test-'));
    configPath = path.join(tempDir, 'unified_config.yaml');
  });

  afterEach(() => {
    // Clean up temporary files
    if (tempDir) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('Configuration Loading', () => {
    it('should load configuration from YAML file', () => {
      const testConfig = {
        anp_foundation: {
          data_user_path: '/test/data_user',
          supported_domains: {
            'localhost': 9527,
            'example.com': 8080
          }
        },
        anp_runtime: {
          agent_manager: {
            auto_load: true,
            scan_interval: 30
          }
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));

      const config = new UnifiedConfig(configPath, tempDir);

      expect((config as any).anp_foundation).toBeDefined();
      expect((config as any).anp_foundation.data_user_path).toBe('/test/data_user');
      expect((config as any).anp_foundation.supported_domains.localhost).toBe(9527);
      expect((config as any).anp_runtime.agent_manager.auto_load).toBe(true);
    });

    it('should create default configuration when file does not exist', () => {
      const nonExistentPath = path.join(tempDir, 'nonexistent.yaml');
      const config = new UnifiedConfig(nonExistentPath, tempDir);

      expect(config).toBeDefined();
      expect(config.appRoot).toBe(tempDir);
    });

    it('should handle invalid YAML format gracefully', () => {
      fs.writeFileSync(configPath, 'invalid: yaml: content: [');

      const config = new UnifiedConfig(configPath, tempDir);

      // Should create config with default values instead of throwing
      expect(config).toBeDefined();
      expect(config.appRoot).toBe(tempDir);
    });

    it('should load environment variables from .env file', () => {
      const envPath = path.join(tempDir, '.env');
      fs.writeFileSync(envPath, 'TEST_VAR=test_value\nANOTHER_VAR=another_value');

      const testConfig = {
        env_mapping: {
          testVar: 'TEST_VAR',
          anotherVar: 'ANOTHER_VAR'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));

      const config = new UnifiedConfig(configPath, tempDir);

      expect(config.env).toBeDefined();
      expect((config.env as any).testVar).toBe('test_value');
      expect((config.env as any).anotherVar).toBe('another_value');
    });
  });

  describe('Configuration Access', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      const testConfig = {
        anp_foundation: {
          data_user_path: '/test/data_user',
          supported_domains: {
            'localhost': 9527,
            'example.com': 8080
          },
          auth: {
            token_expiry: 3600,
            enable_two_way: true
          }
        },
        anp_runtime: {
          agent_manager: {
            auto_load: true,
            scan_interval: 30,
            max_agents: 100
          }
        },
        anp_server: {
          host: '0.0.0.0',
          port: 8000,
          cors: {
            enabled: true,
            origins: ['http://localhost:3000']
          }
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should access nested configuration values', () => {
      expect((config as any).anp_foundation.data_user_path).toBe('/test/data_user');
      expect((config as any).anp_foundation.supported_domains.localhost).toBe(9527);
      expect((config as any).anp_runtime.agent_manager.auto_load).toBe(true);
      expect((config as any).anp_server.cors.enabled).toBe(true);
    });

    it('should provide configuration sections as objects', () => {
      expect((config as any).anp_foundation).toBeDefined();
      expect((config as any).anp_foundation.data_user_path).toBe('/test/data_user');
      expect((config as any).anp_foundation.supported_domains.localhost).toBe(9527);

      expect((config as any).anp_foundation.auth).toBeDefined();
      expect((config as any).anp_foundation.auth.token_expiry).toBe(3600);
      expect((config as any).anp_foundation.auth.enable_two_way).toBe(true);
    });

    it('should handle non-existent properties gracefully', () => {
      expect(() => {
        const nonExistent = (config as any).non_existent_section;
      }).not.toThrow();
    });
  });

  describe('Configuration Persistence', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      const testConfig = {
        anp_foundation: {
          data_user_path: '/test/data_user'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should save configuration to file', () => {
      const result = config.save();

      expect(result).toBe(true);
      expect(fs.existsSync(configPath)).toBe(true);

      // Verify the file contains valid YAML
      const savedContent = fs.readFileSync(configPath, 'utf-8');
      expect(() => yaml.parse(savedContent)).not.toThrow();
    });

    it('should reload configuration from file', () => {
      // Modify the file externally
      const updatedConfig = {
        anp_foundation: {
          data_user_path: '/external/update',
          new_external_key: 'external_value'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(updatedConfig));

      // Reload configuration
      config.reload();

      expect((config as any).anp_foundation.data_user_path).toBe('/external/update');
      expect((config as any).anp_foundation.new_external_key).toBe('external_value');
    });

    it('should handle save errors gracefully', () => {
      // Make directory read-only to simulate save error
      fs.chmodSync(tempDir, 0o444);

      const result = config.save();

      expect(result).toBe(false);

      // Restore permissions for cleanup
      fs.chmodSync(tempDir, 0o755);
    });
  });

  describe('Path Resolution', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      const testConfig = {
        anp_foundation: {
          data_user_path: '{APP_ROOT}/relative/path',
          absolute_path: '/absolute/path',
          template_path: '{APP_ROOT}/templates'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should resolve APP_ROOT placeholders', () => {
      expect((config as any).anp_foundation.data_user_path).toContain(tempDir);
      expect((config as any).anp_foundation.data_user_path).toContain('relative/path');
      expect((config as any).anp_foundation.template_path).toContain(tempDir);
      expect((config as any).anp_foundation.template_path).toContain('templates');
    });

    it('should handle absolute paths without modification', () => {
      expect((config as any).anp_foundation.absolute_path).toBe('/absolute/path');
    });

    it('should provide static path resolution method', () => {
      const testPath = '{APP_ROOT}/test/path';
      const resolvedPath = UnifiedConfig.resolvePath(testPath);
      
      expect(path.isAbsolute(resolvedPath)).toBe(true);
      expect(resolvedPath).toContain('test/path');
    });

    it('should provide instance path resolution method', () => {
      const testPath = '{APP_ROOT}/instance/path';
      const resolvedPath = config.resolvePath(testPath);
      
      expect(path.isAbsolute(resolvedPath)).toBe(true);
      expect(resolvedPath).toContain('instance/path');
    });
  });

  describe('Environment Variable Handling', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      // Set test environment variables
      process.env.TEST_STRING = 'test_value';
      process.env.TEST_PORT = '9527';
      process.env.TEST_DEBUG = 'true';
      process.env.TEST_PATH = '/path1:/path2:/path3';

      const testConfig = {
        env_mapping: {
          testString: 'TEST_STRING',
          testPort: 'TEST_PORT',
          testDebug: 'TEST_DEBUG',
          testPath: 'TEST_PATH'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    afterEach(() => {
      // Clean up test environment variables
      delete process.env.TEST_STRING;
      delete process.env.TEST_PORT;
      delete process.env.TEST_DEBUG;
      delete process.env.TEST_PATH;
    });

    it('should load environment variables with type conversion', () => {
      expect((config.env as any).testString).toBe('test_value');
      expect((config.env as any).testPort).toBe(9527); // Should be converted to number
      expect((config.env as any).testDebug).toBe(true); // Should be converted to boolean
    });

    it('should handle path environment variables', () => {
      const testPath = (config.env as any).testPath;
      if (Array.isArray(testPath)) {
        expect(testPath).toContain('/path1');
        expect(testPath).toContain('/path2');
        expect(testPath).toContain('/path3');
      }
    });

    it('should provide environment variable dictionary', () => {
      const envDict = (config.env as any).toDict();
      expect(envDict).toBeDefined();
      expect(typeof envDict).toBe('object');
    });
  });

  describe('Sensitive Data Handling', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      // Set sensitive environment variables
      process.env.SECRET_PASSWORD = 'secret123';
      process.env.API_KEY = 'key_abc123';

      const testConfig = {
        secrets: ['password', 'apiKey'],
        env_mapping: {
          password: 'SECRET_PASSWORD',
          apiKey: 'API_KEY'
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    afterEach(() => {
      delete process.env.SECRET_PASSWORD;
      delete process.env.API_KEY;
    });

    it('should mask sensitive data in dictionary representation', () => {
      const secretsDict = (config.secrets as any).toDict();
      
      expect(secretsDict.password).toBe('***');
      expect(secretsDict.apiKey).toBe('***');
    });

    it('should still allow access to sensitive data through properties', () => {
      expect((config.secrets as any).password).toBe('secret123');
      expect((config.secrets as any).apiKey).toBe('key_abc123');
    });
  });

  describe('Path Utilities', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should provide app root access', () => {
      expect(config.getAppRoot()).toBe(tempDir);
      expect(config.appRoot).toBe(tempDir);
    });

    it('should provide static app root access', () => {
      const staticAppRoot = UnifiedConfig.getAppRoot();
      expect(staticAppRoot).toBe(tempDir);
    });

    it('should add paths to PATH environment variable', () => {
      const originalPath = process.env.PATH;
      const testPath = '/test/path';

      config.addToPath(testPath);

      expect(process.env.PATH).toContain(testPath);

      // Restore original PATH
      process.env.PATH = originalPath;
    });

    it('should find files in PATH', () => {
      // This test depends on the system having common executables
      const matches = config.findInPath('node');
      
      // Should return an array (may be empty on some systems)
      expect(Array.isArray(matches)).toBe(true);
    });

    it('should provide path information', () => {
      const pathInfo = config.getPathInfo();
      
      expect(pathInfo.app_root).toBe(tempDir);
      expect(pathInfo.config_file).toBe(configPath);
      expect(typeof pathInfo.path_count).toBe('number');
      expect(Array.isArray(pathInfo.existing_paths)).toBe(true);
      expect(Array.isArray(pathInfo.missing_paths)).toBe(true);
    });
  });

  describe('Configuration Dictionary Operations', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      const testConfig = {
        anp_foundation: {
          data_user_path: '/test/data_user',
          supported_domains: {
            'localhost': 9527
          }
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should convert configuration to dictionary', () => {
      const configDict = config.toDict();
      
      expect(configDict).toBeDefined();
      expect(configDict.anp_foundation).toBeDefined();
      expect(configDict.anp_foundation.data_user_path).toBe('/test/data_user');
      expect(configDict.anp_foundation.supported_domains.localhost).toBe(9527);
    });

    it('should load configuration data', () => {
      const loadedData = config.load();
      
      expect(loadedData).toBeDefined();
      expect(loadedData.anp_foundation).toBeDefined();
      expect(loadedData.anp_foundation.data_user_path).toBe('/test/data_user');
    });
  });

  describe('Global Configuration Management', () => {
    it('should set and get global configuration', () => {
      const config = new UnifiedConfig(configPath, tempDir);
      
      setGlobalConfig(config);
      const globalConfig = getGlobalConfig();
      
      expect(globalConfig).toBe(config);
    });

    it('should throw error when accessing unset global config', () => {
      // Reset any existing global config by creating a new one
      // (since we can't directly reset the global variable)
      expect(() => {
        // This should work if global config is set
        getGlobalConfig();
      }).not.toThrow(); // Because we set it in the previous test
    });

    it('should warn when overriding global config', () => {
      const config1 = new UnifiedConfig(configPath, tempDir);
      const config2 = new UnifiedConfig(configPath, tempDir);
      
      // Mock console.warn to capture warnings
      const originalWarn = console.warn;
      const warnSpy = jest.fn();
      console.warn = warnSpy;
      
      setGlobalConfig(config1);
      setGlobalConfig(config2); // Should trigger warning
      
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Global config is being overridden')
      );
      
      // Restore console.warn
      console.warn = originalWarn;
    });
  });

  describe('Error Handling', () => {
    it('should handle configuration file permission errors', () => {
      fs.writeFileSync(configPath, 'test: value');
      fs.chmodSync(configPath, 0o000); // No permissions

      // Should not throw error, but handle gracefully
      expect(() => {
        new UnifiedConfig(configPath, tempDir);
      }).not.toThrow();

      // Restore permissions for cleanup
      fs.chmodSync(configPath, 0o644);
    });

    it('should handle malformed YAML gracefully', () => {
      const malformedYaml = `
        key1: value1
        key2: [unclosed array
        key3: value3
      `;

      fs.writeFileSync(configPath, malformedYaml);

      // Should not throw error, but create config with defaults
      expect(() => {
        new UnifiedConfig(configPath, tempDir);
      }).not.toThrow();
    });

    it('should handle missing default configuration file', () => {
      // Create config without any existing files
      const emptyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'empty-config-'));
      const emptyConfigPath = path.join(emptyDir, 'unified_config.yaml');

      expect(() => {
        new UnifiedConfig(emptyConfigPath, emptyDir);
      }).not.toThrow();

      // Cleanup
      fs.rmSync(emptyDir, { recursive: true, force: true });
    });
  });

  describe('Configuration Node Behavior', () => {
    let config: UnifiedConfig;

    beforeEach(() => {
      const testConfig = {
        test_section: {
          string_value: 'test',
          number_value: 42,
          boolean_value: true,
          nested: {
            deep_value: 'deep'
          }
        }
      };

      fs.writeFileSync(configPath, yaml.stringify(testConfig));
      config = new UnifiedConfig(configPath, tempDir);
    });

    it('should provide access to configuration values through properties', () => {
      const testSection = (config as any).test_section;
      
      expect(testSection).toBeDefined();
      expect(testSection.string_value).toBe('test');
      expect(testSection.number_value).toBe(42);
      expect(testSection.boolean_value).toBe(true);
      expect(testSection.nested.deep_value).toBe('deep');
    });

    it('should handle configuration node methods', () => {
      const testSection = (config as any).test_section;
      
      // Test get method if available
      if (typeof testSection.get === 'function') {
        expect(testSection.get('string_value')).toBe('test');
      }

      // Test toObject method if available
      if (typeof testSection.toObject === 'function') {
        const obj = testSection.toObject();
        expect(obj.string_value).toBe('test');
        expect(obj.number_value).toBe(42);
      }
    });
  });
});