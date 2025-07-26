module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.ts',
    '**/?(*.)+(spec|test).ts'
  ],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts',
    '!src/**/__tests__/**',
    '!src/**/test-utils/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 30000,
  verbose: true,
  // 增强测试报告
  reporters: [
    ['<rootDir>/tests/custom-reporter.js', { showPassed: false }],
    'default'
  ],
  // 显示更多错误信息
  errorOnDeprecated: true,
  bail: false,
  collectCoverage: false,
  maxWorkers: 1,
  // 支持路径映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@foundation/(.*)$': '<rootDir>/src/foundation/$1',
    '^@runtime/(.*)$': '<rootDir>/src/runtime/$1',
    '^@servicepoint/(.*)$': '<rootDir>/src/servicepoint/$1',
    '^@server/(.*)$': '<rootDir>/src/server/$1'
  },
  // 转换配置
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      tsconfig: 'tsconfig.json'
    }]
  },
  // 测试环境变量
  testEnvironmentOptions: {
    NODE_ENV: 'test'
  }
};