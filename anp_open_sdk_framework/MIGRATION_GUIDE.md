# ANP Open SDK Framework 重构迁移指南

## 概述

本次重构将原有的分散调用体系统一为更清晰、更易用的架构：

1. **统一调用器** (UnifiedCaller) - 合并本地方法和远程API调用
2. **统一爬虫** (UnifiedCrawler) - 整合资源发现和智能调用
3. **主智能体** (MasterAgent) - 提供任务级别的统一调度
4. **基于API的服务架构** - 将service功能抽象为API调用

## 重构前后对比

### 调用方式对比

#### 重构前
