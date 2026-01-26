# 信息检索类场景设计指南

## 概述

信息检索类任务测试 Agent 在代码库中搜索特定信息并生成结构化报告的能力。

**核心特点**：
- 产物：结果文件（报告、清单）
- 可验证性：文件必须包含预期找到的具体项
- 安全相关：常用于安全审计、代码扫描

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `security_audit` | 安全漏洞/敏感信息扫描 | Grep + Write | file_content_contains |
| `todo_collection` | TODO/FIXME 收集 | Grep + Write | file_content_contains |
| `dependency_scan` | 依赖使用情况扫描 | Grep + Write | file_content_contains |
| `api_inventory` | API 端点清单生成 | Grep + Write | file_content_contains |

---

## 可验证性设计模式

### 核心原则：预埋 + 验证

```
设计思路：
1. 在环境中预埋要被发现的"目标"（硬编码密钥、TODO、废弃 API 等）
2. 每个目标有唯一标识（文件路径 + 行号，或唯一字符串）
3. 要求 Agent 搜索并生成报告
4. 验证报告包含所有预埋目标

关键点：目标必须是具体的、唯一的、从环境获取的
```

### 模式 1: 硬编码密钥扫描（Grep + Write）

```
场景：扫描代码中的硬编码敏感信息

设计思路：
1. 在多个文件中埋入硬编码密钥（带唯一标识）
2. 要求生成安全报告
3. 验证报告包含所有密钥位置

验证方式：
- file_content_contains: 检查每个密钥位置
```

**示例**：
```json
{
  "query": "扫描代码库中的硬编码密钥和敏感信息，生成 security-report.md",
  "environment": [
    {
      "path": "src/config/database.py",
      "content": "# Database configuration\nDB_HOST = 'localhost'\nDB_PASSWORD = 'hardcoded_secret_abc123'  # TODO: move to env"
    },
    {
      "path": "src/services/payment.py",
      "content": "class PaymentService:\n    API_KEY = 'sk_live_xyz789_secret_key'\n    \n    def process(self):\n        pass"
    },
    {
      "path": "src/utils/logger.py",
      "content": "import logging\n\nlogger = logging.getLogger(__name__)"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "security-report.md"}},
      {"check": "file_content_contains", "params": {"path": "security-report.md", "keyword": "database.py"}},
      {"check": "file_content_contains", "params": {"path": "security-report.md", "keyword": "hardcoded_secret_abc123"}},
      {"check": "file_content_contains", "params": {"path": "security-report.md", "keyword": "payment.py"}},
      {"check": "file_content_contains", "params": {"path": "security-report.md", "keyword": "sk_live_xyz789"}}
    ]
  }
}
```

### 模式 2: TODO 收集（Grep + Write）

```
场景：收集代码中的 TODO 注释

设计思路：
1. 在多个文件中埋入 TODO（带唯一描述）
2. 要求生成 TODO 清单
3. 验证清单包含所有 TODO

验证方式：
- file_content_contains: 检查每个 TODO 内容
```

**示例**：
```json
{
  "query": "收集代码库中所有 TODO 和 FIXME 注释，生成 todo-list.md",
  "environment": [
    {
      "path": "src/api/users.py",
      "content": "def get_user(id):\n    # TODO: add caching for user queries (JIRA-1234)\n    return db.query(id)"
    },
    {
      "path": "src/api/orders.py",
      "content": "def create_order(data):\n    # FIXME: validate order total before saving (JIRA-5678)\n    return db.save(data)"
    },
    {
      "path": "src/utils/helpers.py",
      "content": "def format_date(dt):\n    # TODO: support timezone conversion (JIRA-9012)\n    return dt.strftime('%Y-%m-%d')"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "todo-list.md"}},
      {"check": "file_content_contains", "params": {"path": "todo-list.md", "keyword": "JIRA-1234"}},
      {"check": "file_content_contains", "params": {"path": "todo-list.md", "keyword": "JIRA-5678"}},
      {"check": "file_content_contains", "params": {"path": "todo-list.md", "keyword": "JIRA-9012"}}
    ]
  }
}
```

### 模式 3: 废弃 API 使用扫描（Grep + Write）

```
场景：扫描使用了废弃 API 的代码

设计思路：
1. 定义一组废弃 API
2. 在代码中埋入这些 API 的使用
3. 要求生成废弃使用报告

验证方式：
- file_content_contains: 检查每个使用位置
```

**示例**：
```json
{
  "query": "扫描使用了废弃方法 'legacy_auth()' 的代码，生成 deprecated-usage.md",
  "environment": [
    {
      "path": "src/handlers/login.py",
      "content": "from auth import legacy_auth\n\ndef handle_login(request):\n    user = legacy_auth(request.token)  # line 5\n    return user"
    },
    {
      "path": "src/handlers/admin.py",
      "content": "from auth import legacy_auth, new_auth\n\ndef admin_login(request):\n    # Still using old auth\n    return legacy_auth(request.credentials)  # line 6"
    },
    {
      "path": "src/handlers/api.py",
      "content": "from auth import new_auth\n\ndef api_auth(request):\n    return new_auth(request.api_key)"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "deprecated-usage.md"}},
      {"check": "file_content_contains", "params": {"path": "deprecated-usage.md", "keyword": "login.py"}},
      {"check": "file_content_contains", "params": {"path": "deprecated-usage.md", "keyword": "admin.py"}},
      {"check": "file_content_not_contains", "params": {"path": "deprecated-usage.md", "keyword": "api.py"}}
    ]
  }
}
```

---

## Query 设计模板

### security_audit
```
扫描代码库中的 [安全问题类型]，生成 [报告文件名]，列出所有发现的问题。
```

### todo_collection
```
收集代码库中所有 [标记类型] 注释，生成 [报告文件名]。
```

### dependency_scan
```
扫描 [依赖/API] 的使用情况，生成 [报告文件名]。
```

### api_inventory
```
扫描代码库，列出所有 [API 类型]，生成 [报告文件名]。
```

---

## Grader 设计模板

### 安全扫描报告
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<report_file>"},
      "description": "验证报告已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<report_file>", "keyword": "<file_with_issue_1>"},
      "description": "验证发现问题文件 1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<report_file>", "keyword": "<unique_secret_1>"},
      "description": "验证发现具体问题 1"
    }
  ]
}
```

### TODO 收集
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "todo-list.md"},
      "description": "验证清单已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "todo-list.md", "keyword": "<unique_todo_id_1>"},
      "description": "验证包含 TODO 1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "todo-list.md", "keyword": "<unique_todo_id_2>"},
      "description": "验证包含 TODO 2"
    }
  ]
}
```

---

## 难度递进示例

### D2: 单一模式搜索
- 环境：3-4 个文件，2 个目标
- 任务：搜索一种模式
- 验证点：2-3 个
- Golden Action：2-3 步

### D3: 多文件搜索
- 环境：5-7 个文件，3-4 个目标
- 任务：跨多个文件搜索
- 验证点：3-4 个
- Golden Action：4-5 步

### D4: 复杂模式匹配
- 环境：8-10 个文件，4-6 个目标
- 任务：多种模式 + 有干扰项
- 验证点：4-6 个
- Golden Action：5-7 步

### D5+: 完整审计报告
- 环境：10+ 个文件
- 任务：多维度扫描 + 分类汇总
- 验证点：6+ 个
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Grep | 搜索模式 | 核心搜索工具 |
| Glob | 发现文件 | 了解搜索范围 |
| Read | 确认内容 | 验证搜索结果 |
| Write | 输出报告 | 最终产物 |

---

## 低 Hacking 设计要点

### 使用唯一标识符

```
错误设计：检查包含 "TODO"
正确设计：检查包含 "JIRA-1234"（环境中的具体标识）
```

### 使用具体文件路径

```
错误设计：检查包含 "hardcoded"
正确设计：检查包含 "database.py" + "hardcoded_secret_abc123"
```

### 验证"不包含"干净文件

```json
{
  "checks": [
    {"check": "file_content_contains", "params": {"keyword": "login.py"}},
    {"check": "file_content_contains", "params": {"keyword": "admin.py"}},
    {"check": "file_content_not_contains", "params": {"keyword": "api.py"}}
  ]
}
```

### 组合多种唯一信息

```json
{
  "checks": [
    {"check": "file_content_contains", "params": {"keyword": "src/config/database.py"}},
    {"check": "file_content_contains", "params": {"keyword": "hardcoded_secret_abc123"}},
    {"check": "file_content_contains", "params": {"keyword": "sk_live_xyz789"}}
  ]
}
```
