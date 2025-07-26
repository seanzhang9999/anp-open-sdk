/**
 * 自定义Jest报告器 - 提供更清晰的测试结果展示
 */

class CustomTestReporter {
  constructor(globalConfig, options) {
    this._globalConfig = globalConfig;
    this._options = options;
  }

  onRunComplete(contexts, results) {
    const { testResults, numFailedTests, numPassedTests, numTotalTests } = results;
    
    console.log('\n' + '═'.repeat(80));
    console.log('🧪 ANP Node.js SDK 测试结果详细报告');
    console.log('═'.repeat(80));
    
    // 总体统计
    console.log('\n📊 测试统计:');
    console.log(`   • 总测试数: ${numTotalTests}`);
    console.log(`   • 通过: ${numPassedTests} ✅`);
    console.log(`   • 失败: ${numFailedTests} ❌`);
    console.log(`   • 成功率: ${((numPassedTests / numTotalTests) * 100).toFixed(1)}%`);
    
    // 按测试套件分组显示结果
    console.log('\n📋 测试套件详情:');
    
    testResults.forEach((testResult) => {
      const suiteName = this.extractSuiteName(testResult.testFilePath);
      const { numFailingTests, numPassingTests, testResults: tests } = testResult;
      
      const suiteStatus = numFailingTests === 0 ? '✅' : '❌';
      console.log(`\n${suiteStatus} ${suiteName} (${numPassingTests}/${numPassingTests + numFailingTests})`);
      
      if (numFailingTests > 0) {
        console.log('   失败的测试:');
        tests.forEach((test) => {
          if (test.status === 'failed') {
            console.log(`   ❌ ${test.title}`);
            if (test.failureMessages && test.failureMessages.length > 0) {
              test.failureMessages.forEach((message) => {
                // 清理错误信息，只显示关键部分
                const cleanMessage = this.cleanErrorMessage(message);
                console.log(`      💥 ${cleanMessage}`);
              });
            }
          }
        });
      }
      
      // 显示通过的测试（可选）
      if (this._options && this._options.showPassed) {
        console.log('   通过的测试:');
        tests.forEach((test) => {
          if (test.status === 'passed') {
            console.log(`   ✅ ${test.title}`);
          }
        });
      }
    });
    
    // 失败测试的详细错误信息
    if (numFailedTests > 0) {
      console.log('\n🔍 失败测试详细信息:');
      console.log('─'.repeat(60));
      
      testResults.forEach((testResult) => {
        if (testResult.numFailingTests > 0) {
          testResult.testResults.forEach((test) => {
            if (test.status === 'failed') {
              console.log(`\n❌ ${test.ancestorTitles.join(' > ')} > ${test.title}`);
              console.log(`   文件: ${testResult.testFilePath.replace(process.cwd(), '.')}`);
              
              if (test.failureMessages) {
                test.failureMessages.forEach((message, index) => {
                  console.log(`   错误 ${index + 1}:`);
                  console.log(`   ${this.formatErrorMessage(message)}`);
                });
              }
            }
          });
        }
      });
    }
    
    // 性能统计
    console.log('\n⚡ 性能统计:');
    const totalTime = results.testResults.reduce((sum, result) => sum + (result.perfStats?.end - result.perfStats?.start || 0), 0);
    console.log(`   • 总执行时间: ${(totalTime / 1000).toFixed(2)}秒`);
    
    const slowTests = [];
    testResults.forEach((testResult) => {
      testResult.testResults.forEach((test) => {
        if (test.duration && test.duration > 1000) { // 超过1秒的测试
          slowTests.push({
            name: `${test.ancestorTitles.join(' > ')} > ${test.title}`,
            duration: test.duration
          });
        }
      });
    });
    
    if (slowTests.length > 0) {
      console.log('   • 慢速测试 (>1秒):');
      slowTests.sort((a, b) => b.duration - a.duration).forEach((test) => {
        console.log(`     - ${test.name}: ${test.duration}ms`);
      });
    }
    
    // 建议和总结
    console.log('\n🎯 测试总结:');
    if (numFailedTests === 0) {
      console.log('   🎉 所有测试通过！代码质量良好。');
    } else {
      console.log(`   ⚠️  发现 ${numFailedTests} 个失败测试，需要修复。`);
      console.log('   💡 建议:');
      console.log('      1. 检查上述失败测试的错误信息');
      console.log('      2. 确认测试环境和依赖是否正确');
      console.log('      3. 运行单个测试进行调试: npm test -- --testNamePattern="测试名称"');
    }
    
    console.log('\n' + '═'.repeat(80) + '\n');
  }
  
  extractSuiteName(filePath) {
    const fileName = filePath.split('/').pop();
    return fileName.replace('.test.ts', '').replace('.test.js', '');
  }
  
  cleanErrorMessage(message) {
    // 提取关键错误信息
    const lines = message.split('\n');
    for (const line of lines) {
      if (line.includes('Expected:') || line.includes('Received:') || line.includes('Error:')) {
        return line.trim();
      }
    }
    return lines[0] || message;
  }
  
  formatErrorMessage(message) {
    // 格式化错误信息，使其更易读
    return message
      .split('\n')
      .slice(0, 5) // 只显示前5行
      .map(line => `   ${line}`)
      .join('\n');
  }
}

module.exports = CustomTestReporter;