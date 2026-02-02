# 内容创作类场景设计指南

## 概述

内容创作类任务测试 Agent 根据代码库/项目状态生成技术文档的能力。通过**约束型文档产出**实现可验证性。

**核心特点**：
- 产物：技术文档（迁移指南、变更日志、README 等）
- 可验证性：文档必须包含从环境提取的具体内容
- 实用性：模拟真实文档编写场景

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `migration_guide` | API/版本迁移指南 | Grep + Write | file_content_contains |
| `changelog_generation` | 变更日志生成 | Bash(git) + Write | file_content_contains |
| `readme_update` | README 文档更新 | Read + Edit | file_content_contains |
| `technical_spec` | 技术规格文档 | Read + Write | file_content_contains |

---

## 可验证性设计模式

### 核心原则：约束型文档产出

```
关键洞察：
内容创作看似主观，但如果：
1. 要求文档包含特定内容（如废弃 API 列表、提交信息）
2. 这些内容只能从环境中获取
3. 验证文档包含这些具体内容

就可以实现可验证！
```

### 模式 1: 迁移指南（Grep + Write）

```
场景：根据代码中的废弃标记生成迁移指南

设计思路：
1. 代码中有 @deprecated 标记的 API
2. 注释中有替代方案
3. 要求生成迁移指南，包含每个废弃 API 及替代方案

验证方式：
- file_content_contains: 检查每个废弃 API 名称
- file_content_contains: 检查替代方案
```

**示例**：
```json
{
  "query": "根据代码中的废弃 API 标记，生成 migration-guide.md，列出所有废弃 API 及替代方案",
  "environment": [
    {
      "path": "src/api/users.py",
      "content": "# @deprecated: Use get_user_by_id instead\ndef get_user(id):\n    pass\n\ndef get_user_by_id(user_id):\n    '''New API for fetching user'''\n    pass"
    },
    {
      "path": "src/api/orders.py",
      "content": "# @deprecated: Use create_order_v2 instead\ndef create_order(data):\n    pass\n\ndef create_order_v2(order_data, options=None):\n    '''New order creation API'''\n    pass"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "migration-guide.md"}},
      {"check": "file_content_contains", "params": {"path": "migration-guide.md", "keyword": "get_user"}},
      {"check": "file_content_contains", "params": {"path": "migration-guide.md", "keyword": "get_user_by_id"}},
      {"check": "file_content_contains", "params": {"path": "migration-guide.md", "keyword": "create_order"}},
      {"check": "file_content_contains", "params": {"path": "migration-guide.md", "keyword": "create_order_v2"}}
    ]
  }
}
```

### 模式 2: 变更日志生成（Bash + Write）

```
场景：根据 git 提交历史生成 CHANGELOG

设计思路：
1. 预先创建带有规范提交消息的 git 历史
2. 要求根据提交生成 CHANGELOG
3. 验证 CHANGELOG 包含关键提交信息

验证方式：
- file_content_contains: 检查关键提交描述
```

**示例**：
```json
{
  "query": "根据 git 提交历史生成 CHANGELOG.md",
  "init_commands": [
    "cd {{SANDBOX}} && git init",
    "git config user.email 'test@example.com'",
    "git config user.name 'Test'",
    "echo 'v1' > version.txt && git add . && git commit -m 'feat: add user authentication module'",
    "echo 'v2' > version.txt && git add . && git commit -m 'fix: resolve payment timeout issue JIRA-5678'",
    "echo 'v3' > version.txt && git add . && git commit -m 'feat: implement order tracking feature'"
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "CHANGELOG.md"}},
      {"check": "file_content_contains", "params": {"path": "CHANGELOG.md", "keyword": "user authentication"}},
      {"check": "file_content_contains", "params": {"path": "CHANGELOG.md", "keyword": "payment timeout"}},
      {"check": "file_content_contains", "params": {"path": "CHANGELOG.md", "keyword": "order tracking"}}
    ]
  }
}
```

### 模式 3: README 更新（Read + Edit）

```
场景：根据新增功能更新 README

设计思路：
1. 现有 README 缺少新功能说明
2. 新功能代码已存在，有明确的功能名称
3. 要求更新 README，添加新功能说明

验证方式：
- file_content_contains: 检查新功能名称
```

**示例**：
```json
{
  "query": "根据新增的功能模块更新 README.md 的使用说明",
  "environment": [
    {
      "path": "README.md",
      "content": "# MyApp\n\n## Features\n- User management\n- Order processing\n\n## Usage\n..."
    },
    {
      "path": "src/features/real_time_notifications.py",
      "content": "'''Real-time Notifications Module\n\nProvides WebSocket-based real-time notifications for:\n- Order status updates\n- Payment confirmations\n- Inventory alerts\n'''\n\nclass NotificationService:\n    pass"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_content_contains", "params": {"path": "README.md", "keyword": "Real-time"}},
      {"check": "file_content_contains", "params": {"path": "README.md", "keyword": "notification"}}
    ]
  }
}
```

---

## Query 设计模板

### migration_guide
```
根据代码中的 [废弃标记类型]，生成 [输出文件名]，列出所有 [废弃内容] 及替代方案。
```

### changelog_generation
```
根据 git [历史范围] 生成 [输出文件名]，包含所有 [变更类型]。
```

### readme_update
```
根据新增的 [功能/模块] 更新 [README 文件]，添加 [目标内容]。
```

### technical_spec
```
根据 [代码/配置] 生成 [技术文档]，说明 [目标内容]。
```

---

## Grader 设计模板

### 迁移指南
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
      "params": {"path": "<output_doc>", "keyword": "<deprecated_api_1>"},
      "description": "验证包含废弃 API 1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_doc>", "keyword": "<replacement_api_1>"},
      "description": "验证包含替代方案 1"
    }
  ]
}
```

### 变更日志
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "CHANGELOG.md"},
      "description": "验证 CHANGELOG 已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "CHANGELOG.md", "keyword": "<commit_keyword_1>"},
      "description": "验证包含关键变更 1"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "CHANGELOG.md", "keyword": "<commit_keyword_2>"},
      "description": "验证包含关键变更 2"
    }
  ]
}
```

---

## 难度递进示例

### D2: 单一内容生成
- 环境：2-3 个文件
- 任务：生成简单文档
- 验证点：2-3 个
- Golden Action：2-3 步

### D3: 多源内容整合
- 环境：4-6 个文件
- 任务：整合多个来源
- 验证点：3-4 个
- Golden Action：4-5 步

### D4: 复杂文档生成
- 环境：6-10 个文件
- 任务：生成结构化文档
- 验证点：4-6 个
- Golden Action：5-7 步

### D5+: 完整文档套件
- 环境：10+ 个文件
- 任务：生成多个相关文档
- 验证点：6+ 个
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Grep | 搜索废弃标记/模式 | 定位目标内容 |
| Bash | git 命令获取历史 | 获取提交信息 |
| Read | 阅读现有文档/代码 | 理解上下文 |
| Write | 生成新文档 | 创建新文件 |
| Edit | 更新现有文档 | 修改现有文件 |

---

## 低 Hacking 设计要点

### 使用环境中的具体函数名/变量名

```
错误设计：检查包含 "deprecated"
正确设计：检查包含 "get_user"、"create_order_v2"（环境中的具体名称）
```

### 使用提交消息中的具体内容

```
错误设计：检查包含 "feature"
正确设计：检查包含 "user authentication"、"payment timeout"（具体提交内容）
```

### 验证多个独立内容点

```json
{
  "checks": [
    {"check": "file_content_contains", "params": {"keyword": "get_user"}},
    {"check": "file_content_contains", "params": {"keyword": "get_user_by_id"}},
    {"check": "file_content_contains", "params": {"keyword": "create_order"}},
    {"check": "file_content_contains", "params": {"keyword": "create_order_v2"}}
  ]
}
```
