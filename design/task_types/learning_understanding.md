# 学习理解类场景设计指南

## 概述

学习理解类任务测试 Agent 阅读、理解代码库并生成结构化文档的能力。通过**约束型文档产出**实现可验证性。

**核心特点**：
- 产物：结构化文档（架构总结、API 文档等）
- 可验证性：文档必须包含从环境提取的具体信息
- 低 hacking：验证点是环境中的具体名称/值

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `architecture_summary` | 架构分析与总结 | Read/Grep + Write | file_content_contains |
| `api_documentation` | API 端点文档生成 | Grep + Write | file_content_contains |
| `code_walkthrough` | 代码流程解析 | Read + Write | file_content_contains |
| `dependency_mapping` | 依赖关系图谱 | Grep + Write | file_content_contains |

---

## 可验证性设计模式

### 核心原则：约束型文档产出

```
关键洞察：
只要任务最终产出是静态产物（文件），
且产物内容有明确约束（必须包含从环境获取的特定信息），
就可以验证！

设计模式：
1. 环境中包含具体的、唯一的信息（服务名、端点、依赖等）
2. 要求 Agent 生成文档，文档必须包含这些具体信息
3. 验证文档包含这些具体信息
```

### 模式 1: 架构总结（Read + Write）

```
场景：分析微服务架构，生成架构总结文档

设计思路：
1. 创建多个服务的配置/代码文件
2. 文件中包含服务间的通信关系
3. 要求生成架构总结，必须包含具体的服务名和通信方式

验证方式：
- file_content_contains: 检查每个服务名
- file_content_contains: 检查通信方式关键词
```

**示例**：
```json
{
  "query": "分析项目的微服务架构，生成 architecture-summary.md，总结所有服务及其通信方式",
  "environment": [
    {
      "path": "services/order-service/config.yaml",
      "content": "name: order-service\ndependencies:\n  - payment-service via gRPC\n  - inventory-service via Kafka"
    },
    {
      "path": "services/payment-service/config.yaml",
      "content": "name: payment-service\ndependencies:\n  - notification-service via REST"
    },
    {
      "path": "services/inventory-service/config.yaml",
      "content": "name: inventory-service\ndependencies:\n  - warehouse-service via gRPC"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "architecture-summary.md"}},
      {"check": "file_content_contains", "params": {"path": "architecture-summary.md", "keyword": "order-service"}},
      {"check": "file_content_contains", "params": {"path": "architecture-summary.md", "keyword": "payment-service"}},
      {"check": "file_content_contains", "params": {"path": "architecture-summary.md", "keyword": "Kafka"}},
      {"check": "file_content_contains", "params": {"path": "architecture-summary.md", "keyword": "gRPC"}}
    ]
  }
}
```

### 模式 2: API 文档生成（Grep + Write）

```
场景：从代码中提取 API 端点，生成文档

设计思路：
1. 创建包含 API 定义的代码文件
2. 文件中有具体的端点路径
3. 要求生成 API 文档，必须包含所有端点

验证方式：
- file_content_contains: 检查每个端点路径
```

**示例**：
```json
{
  "query": "分析代码库，生成 api-endpoints.md，列出所有 REST API 端点",
  "environment": [
    {
      "path": "src/routes/users.py",
      "content": "@app.route('/api/v1/users', methods=['GET'])\ndef list_users():\n    pass\n\n@app.route('/api/v1/users/<id>', methods=['GET'])\ndef get_user(id):\n    pass"
    },
    {
      "path": "src/routes/orders.py",
      "content": "@app.route('/api/v1/orders', methods=['POST'])\ndef create_order():\n    pass\n\n@app.route('/api/v1/orders/<id>/cancel', methods=['POST'])\ndef cancel_order(id):\n    pass"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "api-endpoints.md"}},
      {"check": "file_content_contains", "params": {"path": "api-endpoints.md", "keyword": "/api/v1/users"}},
      {"check": "file_content_contains", "params": {"path": "api-endpoints.md", "keyword": "/api/v1/orders"}},
      {"check": "file_content_contains", "params": {"path": "api-endpoints.md", "keyword": "cancel"}}
    ]
  }
}
```

### 模式 3: 依赖关系图谱（Grep + Write）

```
场景：分析模块依赖关系，生成依赖文档

设计思路：
1. 创建多个相互依赖的模块
2. 文件中有明确的 import 语句
3. 要求生成依赖文档，必须包含所有依赖关系

验证方式：
- file_content_contains: 检查关键依赖描述
```

---

## Query 设计模板

### architecture_summary
```
阅读项目架构文档和配置文件，生成 [输出文件名]，总结所有 [目标内容]。
```

### api_documentation
```
分析代码库中的 [API 类型] 定义，生成 [输出文件名]，列出所有 [端点信息]。
```

### code_walkthrough
```
阅读 [模块/功能] 的实现代码，生成 [输出文件名]，解释 [流程/逻辑]。
```

### dependency_mapping
```
分析项目的 [依赖类型]，生成 [输出文件名]，说明各模块的依赖关系。
```

---

## Grader 设计模板

### 架构总结
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<output_doc>"},
      "description": "验证文档已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<service_name_1>"},
      "description": "验证包含服务1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<service_name_2>"},
      "description": "验证包含服务2"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<communication_method>"},
      "description": "验证包含通信方式"
    }
  ]
}
```

### API 文档
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<output_doc>"},
      "description": "验证文档已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<endpoint_1>"},
      "description": "验证包含端点1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<endpoint_2>"},
      "description": "验证包含端点2"
    }
  ]
}
```

---

## 难度递进示例

### D2: 单一信息提取
- 环境：2-3 个文件
- 任务：提取一类信息
- 验证点：2-3 个
- Golden Action：2-3 步

### D3: 多源信息整合
- 环境：4-6 个文件
- 任务：整合多个文件的信息
- 验证点：3-4 个
- Golden Action：4-5 步

### D4: 复杂结构分析
- 环境：6-10 个文件
- 任务：分析复杂依赖/架构
- 验证点：4-6 个
- Golden Action：5-7 步

### D5+: 完整文档生成
- 环境：10+ 个文件
- 任务：生成完整的技术文档
- 验证点：6+ 个
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Read | 阅读文档/配置 | 主要探索工具 |
| Grep | 搜索模式 | 快速定位信息 |
| Glob | 发现文件 | 了解项目结构 |
| Write | 输出文档 | 最终产物 |

---

## 低 Hacking 设计要点

### 使用环境中的具体名称

```
错误设计：检查文档包含 "microservice"
正确设计：检查文档包含 "order-service"（环境中的具体服务名）
```

### 多验证点覆盖

```
不要只验证一个信息点，要验证多个：
- 多个服务名
- 多个端点
- 多个依赖关系
```

### 避免通用词汇

```
错误：检查包含 "database"、"API"、"service"
正确：检查包含 "payment-service"、"/api/v1/orders"、"Kafka"
```
