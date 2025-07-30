/**
 * 简单测试 Local Methods 系统
 */

import { localMethod, registerLocalMethodsToAgent, LocalMethodsCaller } from '../src/runtime/local-service';

// 创建一个测试Agent类
class TestAgent {
  public name: string;
  
  constructor(name: string) {
    this.name = name;
  }

  @localMethod('加法运算', ['数学', '计算'])
  add(a: number, b: number): number {
    return a + b;
  }

  @localMethod('字符串处理')
  greet(name: string): string {
    return `Hello, ${name}!`;
  }
}

async function testLocalMethods() {
  // 创建Agent实例
  const agent = new TestAgent('TestAgent');
  
  // 注册方法到全局注册表
  registerLocalMethodsToAgent(agent, 'TestAgent');
  
  // 创建调用器
  const caller = new LocalMethodsCaller();
  
  // 测试方法调用
  try {
    console.log('=== 测试 Local Methods 系统 ===');
    
    // 测试加法
    const result1 = await caller.callMethodByKey('TestAgent::add', 5, 3);
    console.log('add(5, 3) =', result1);
    
    // 测试字符串方法
    const result2 = await caller.callMethodByKey('TestAgent::greet', 'World');
    console.log('greet("World") =', result2);
    
    // 列出所有注册的方法
    const methods = caller.listAllMethods();
    console.log('注册的方法:', methods.map((m: any) => m.methodKey));
    
    console.log('✅ Local Methods 系统测试通过！');
    
  } catch (error) {
    console.error('❌ 测试失败:', error);
  }
}

// 运行测试
if (require.main === module) {
  testLocalMethods();
}

export { testLocalMethods };