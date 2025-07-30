# Node.js Local Methods System

一个完整的本地方法装饰器系统，对标Python版本的`local_methods_decorators.py`功能。

## 概述

Local Methods系统提供了一个强大的装饰器机制，允许Agent类的方法被全局注册和调用，实现了进程内的方法发现与调用机制。

## 核心特性

- **@localMethod 装饰器**: 标记Agent实例方法为可调用的本地方法
- **全局方法注册表**: 维护所有已注册方法的映射关系
- **方法发现与调用**: 通过方法键或搜索关键词调用方法
- **文档生成**: 自动生成JSON和Markdown格式的方法文档
- **搜索功能**: 按关键词、标签、Agent名称搜索方法
- **批量调用**: 支持串行和并发的批量方法调用
- **完整的TypeScript类型支持**: 类型安全的装饰器系统

## 核心组件

### 1. 装饰器系统 (`local-methods-decorators.ts`)

```typescript
import { localMethod, registerLocalMethodsToAgent } from '../src/runtime/local-service';

class CalculatorAgent {
  @localMethod('数学计算-加法', ['数学', '计算', '基础'])
  add(a: number, b: number): number {
    return a + b;
  }

  @localMethod('数学计算-乘法', ['数学', '计算'])
  async multiply(a: number, b: number): Promise<number> {
    return a * b;
  }
}
```

### 2. 方法注册

```typescript
// 创建Agent实例
const calculator = new CalculatorAgent();

// 注册方法到全局注册表
registerLocalMethodsToAgent(calculator, 'CalculatorAgent');
```

### 3. 方法调用 (`local-methods-caller.ts`)

```typescript
import { LocalMethodsCaller } from '../src/runtime/local-service';

const caller = new LocalMethodsCaller();

// 通过方法键调用
const result1 = await caller.callMethodByKey('CalculatorAgent::add', 5, 3);

// 通过搜索关键词调用
const result2 = await caller.callMethodBySearch('加法', 10, 20);

// 批量调用
const results = await caller.callMultipleMethods([
  { methodKey: 'CalculatorAgent::add', args: [1, 2] },
  { methodKey: 'CalculatorAgent::multiply', args: [3, 4] }
]);
```

### 4. 文档生成 (`local-methods-doc.ts`)

```typescript
import { LocalMethodsDocGenerator } from '../src/runtime/local-service';

const docGen = new LocalMethodsDocGenerator();

// 生成JSON文档
const jsonDoc = docGen.generateJsonDoc();

// 生成Markdown文档
const markdownDoc = docGen.generateMarkdownDoc();

// 搜索方法
const searchResults = docGen.searchMethods({
  keyword: '数学',
  tags: ['计算'],
  agentName: 'CalculatorAgent'
});
```

## API 参考

### @localMethod 装饰器

```typescript
@localMethod(description?: string, tags?: string[])
```

- `description`: 方法描述信息
- `tags`: 方法标签数组，用于搜索和分类

### LocalMethodsCaller 方法

- `callMethodByKey(methodKey: string, ...args: any[])`: 通过方法键调用
- `callMethodBySearch(keyword: string, ...args: any[])`: 通过搜索调用
- `callMultipleMethods(calls)`: 批量串行调用
- `callMethodsConcurrently(calls)`: 批量并发调用
- `listAllMethods()`: 列出所有方法
- `listMethodsByAgent(agentName)`: 按Agent列出方法
- `listMethodsByTag(tag)`: 按标签列出方法

### LocalMethodsDocGenerator 方法

- `generateJsonDoc()`: 生成JSON格式文档
- `generateMarkdownDoc()`: 生成Markdown格式文档
- `searchMethods(criteria)`: 搜索方法
- `getMethodInfo(methodKey)`: 获取方法详细信息
- `getStats()`: 获取统计信息

## 方法键格式

方法键采用 `AgentName::methodName` 格式，例如：
- `CalculatorAgent::add`
- `StringAgent::toUpperCase`
- `WeatherAgent::getCurrentWeather`

## 使用示例

### 完整的Agent示例

```typescript
import { localMethod, registerLocalMethodsToAgent, LocalMethodsCaller } from '../src/runtime/local-service';

class StringAgent {
  @localMethod('字符串转大写', ['字符串', '转换'])
  toUpperCase(text: string): string {
    return text.toUpperCase();
  }

  @localMethod('字符串长度计算', ['字符串', '统计'])
  getLength(text: string): number {
    return text.length;
  }
}

async function demo() {
  // 注册Agent
  const stringAgent = new StringAgent();
  registerLocalMethodsToAgent(stringAgent, 'StringAgent');

  // 创建调用器
  const caller = new LocalMethodsCaller();

  // 调用方法
  const upperText = await caller.callMethodByKey('StringAgent::toUpperCase', 'hello world');
  console.log(upperText); // "HELLO WORLD"

  const length = await caller.callMethodBySearch('长度', 'hello');
  console.log(length); // 5

  // 查看所有方法
  const methods = caller.listAllMethods();
  methods.forEach(method => {
    console.log(`${method.methodKey}: ${method.description}`);
  });
}
```

### 与现有Agent系统集成

```typescript
import { Agent } from '../src/runtime/core/agent';

class MyAgent extends Agent {
  constructor(options: AgentOptions) {
    super(options);
    // 注册local methods
    registerLocalMethodsToAgent(this, this.name);
  }

  @localMethod('业务逻辑处理', ['业务', '核心'])
  async processBusinessLogic(data: any): Promise<any> {
    // 业务逻辑处理
    return { processed: true, data };
  }
}
```

## 特性对比

| 特性 | Python版本 | Node.js版本 |
|------|-----------|-------------|
| 装饰器语法 | `@local_method` | `@localMethod` |
| 全局注册表 | ✅ | ✅ |
| 方法搜索 | ✅ | ✅ |
| 文档生成 | ✅ | ✅ |
| 异步支持 | ✅ | ✅ |
| 类型安全 | 部分 | 完整 |
| 批量调用 | ✅ | ✅ |
| 并发调用 | ✅ | ✅ |

## 编译配置

项目已包含专门的TypeScript配置文件 `tsconfig.local-service.json` 用于编译local-service模块。

```bash
# 编译检查
npx tsc --noEmit -p tsconfig.local-service.json
```

## 注意事项

1. **Agent实例必须先注册**: 使用 `registerLocalMethodsToAgent()` 注册Agent实例
2. **方法键唯一性**: 每个方法键在全局注册表中必须唯一
3. **类型安全**: 建议使用TypeScript以获得完整的类型检查
4. **异步方法支持**: 系统自动检测并处理async方法
5. **错误处理**: 调用失败时会抛出详细的错误信息

## 未来扩展

- [ ] 支持方法权限控制
- [ ] 添加方法调用统计
- [ ] 实现方法调用链追踪
- [ ] 支持远程方法调用（跨进程）
- [ ] 添加方法缓存机制

---

这个系统完全对标了Python版本的功能，并在TypeScript的类型安全基础上提供了更好的开发体验。