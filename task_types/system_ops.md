# 系统运维类场景设计指南

## 概述

系统运维类任务测试 Agent 对版本控制、依赖管理、部署流程和进程管理的能力。

**核心特点**：
- 产物多样：git 状态、进程状态、系统文件
- 可验证性：通过命令输出或状态检查
- 实用性强：模拟真实运维场景

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `version_control` | Git 操作（提交、分支、合并） | Bash | git_commit_message, git_branch_exists |
| `dependency_management` | 依赖版本管理与升级 | Edit/Bash | file_content_contains |
| `deployment` | 部署脚本与配置 | Write/Bash | file_exists, bash_exit_code |
| `process_management` | 进程启动/停止/监控 | Bash/KillShell | bash_process_running |

---

## 可验证性设计模式

### 模式 1: Git 提交（Bash）

```
场景：根据变更生成规范的 commit

设计思路：
1. 预先设置文件变更（unstaged）
2. 要求 Agent 生成符合规范的提交
3. 验证提交消息格式

验证方式：
- git_commit_message: 检查提交消息包含特定内容
- git_file_committed: 检查文件已提交
```

**示例**：
```json
{
  "query": "将当前的数据库配置修改提交到 git，提交消息需要包含 ticket 编号 JIRA-1234",
  "init_commands": [
    "cd {{SANDBOX}} && git init",
    "echo 'port: 5432' > config/db.yaml",
    "git add . && git commit -m 'initial'",
    "echo 'port: 3306' > config/db.yaml"
  ],
  "grader": {
    "checks": [
      {"check": "git_commit_message", "params": {"pattern": "JIRA-1234"}}
    ]
  }
}
```

### 模式 2: 分支管理（Bash）

```
场景：创建功能分支并切换

设计思路：
1. 在主分支上有待修复的问题
2. 要求 Agent 创建特定名称的分支
3. 验证分支存在且包含修复

验证方式：
- git_branch_exists: 检查分支存在
- bash_check: 检查当前分支
```

**示例**：
```json
{
  "query": "为修复支付超时问题创建分支 fix/payment-timeout-JIRA-5678",
  "grader": {
    "checks": [
      {"check": "git_branch_exists", "params": {"branch_name": "fix/payment-timeout-JIRA-5678"}}
    ]
  }
}
```

### 模式 3: 进程管理（Bash + KillShell）

```
场景：清理僵尸进程或启动服务

设计思路：
1. 预先启动后台进程或模拟僵尸进程
2. 要求 Agent 识别并处理
3. 验证进程状态变化

验证方式：
- bash_process_running: 检查进程运行
- bash_process_not_running: 检查进程已停止
```

**示例**：
```json
{
  "query": "有一个占用大量 CPU 的后台进程需要清理，请终止它",
  "init_commands": [
    "nohup bash -c 'while true; do :; done' &",
    "echo $! > /tmp/zombie.pid"
  ],
  "grader": {
    "checks": [
      {"check": "bash_process_not_running", "params": {"pid_file": "/tmp/zombie.pid"}}
    ]
  }
}
```

### 模式 4: 依赖管理（Edit）

```
场景：升级依赖版本解决兼容性问题

设计思路：
1. 错误日志显示版本冲突
2. 依赖文件中有过时版本
3. Agent 需要更新到正确版本

验证方式：
- file_content_contains: 检查版本号
- bash_exit_code: 安装成功
```

---

## Query 设计模板

### version_control
```
请将 [变更描述] 提交到 git，提交消息需要符合 [规范要求]。
```

```
为 [功能/修复] 创建分支 [分支名规范]，并提交初始修改。
```

### dependency_management
```
[服务名] 因为 [依赖名] 版本过低导致 [问题]，请升级到兼容版本。
```

### deployment
```
根据 [部署需求]，生成 [目标环境] 的部署脚本/配置。
```

### process_management
```
系统中存在 [问题进程]，请识别并 [处理方式]。
```

---

## Grader 设计模板

### Git 提交
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "git_commit_message",
      "params": {"pattern": "<required_pattern>"},
      "description": "验证提交消息包含必要内容"
    },
    {
      "check": "git_file_committed",
      "params": {"file_path": "<modified_file>"},
      "description": "验证文件已提交"
    }
  ]
}
```

### 分支管理
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "git_branch_exists",
      "params": {"branch_name": "<expected_branch>"},
      "description": "验证分支已创建"
    }
  ]
}
```

### 进程管理
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "bash_process_not_running",
      "params": {"process_name": "<target_process>"},
      "description": "验证进程已终止"
    }
  ]
}
```

---

## 难度递进示例

### D2: 简单 Git 操作
- 任务：提交已暂存的文件
- 环境：2-3 个文件
- Golden Action：2-3 步

### D3: 多步 Git 操作
- 任务：创建分支 + 修改 + 提交
- 环境：4-6 个文件
- Golden Action：4-5 步

### D4: 复杂分支场景
- 任务：解决合并冲突
- 环境：6-10 个文件，多分支
- Golden Action：5-7 步

### D5+: 完整发布流程
- 任务：版本升级 + 变更日志 + tag
- 环境：10+ 个文件
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Bash | Git 命令、进程管理 | 核心工具 |
| KillShell | 终止后台进程 | 配合 Bash 使用 |
| Edit | 修改配置/依赖文件 | 辅助工具 |
| Read | 查看日志/配置 | 用于排查问题 |
| Grep | 搜索错误信息 | 用于定位问题 |

---

## 特殊注意事项

### Git 环境初始化

```json
{
  "init_commands": [
    "cd {{SANDBOX}} && git init",
    "git config user.email 'test@example.com'",
    "git config user.name 'Test User'",
    "git add . && git commit -m 'initial commit'"
  ]
}
```

### 进程管理安全

- 使用 PID 文件跟踪进程
- 设置合理的超时时间
- 避免使用 `kill -9` 除非必要
