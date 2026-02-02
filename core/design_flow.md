# 设计流程

本文档指导测试用例的完整设计流程。

**前置要求**：已阅读 `core/principles.md` 并理解核心原则。

---

## 工作目录说明

你的工作目录已预设（通常是 `/tmp/workspace`），初始为空。直接在工作目录中创建环境文件。

---

## Phase 1: 环境构建

### 目标

创建符合真实项目的目录结构和文件，为测试题提供探索的"世界"。

### 获取参考项目（推荐，D5+ 必须）

根据场景主题搜索相关项目：
- 中文项目/技术：使用 `mcp__baidu-server__web_search`
- 英文项目/技术：使用 `mcp__google-server__web_search`

### 目录结构设计

| 项目类型 | 典型目录结构 |
|---------|-------------|
| 微服务 | `services/`, `config/`, `deploy/`, `docs/`, `logs/` |
| 前端项目 | `src/`, `config/`, `public/`, `docs/`, `scripts/` |
| 数据平台 | `pipelines/`, `config/`, `data/`, `logs/`, `docs/` |
| DevOps | `deploy/`, `scripts/`, `config/`, `monitoring/`, `docs/` |

### 文件数量要求

| 难度 | 文件数 |
|------|--------|
| D2 | 3-5 个 |
| D3 | 8-12 个 |
| D4 | 12-15 个 |
| D5 | 15-20 个 |
| D6 | 20-25 个 |
| D7 | 25-35 个 |

### environment 字段格式

```json
{
  "path": "config/database.yaml",
  "content": "host: localhost\nport: 5432\ntimeout: 5000",
  "executable": false
}
```

### init_commands（可选）

用于初始化命令，如启动后台进程（KillShell 场景必须）：

```json
{
  "init_commands": [
    {
      "command": "nohup python3 services/worker.py > logs/worker.log 2>&1 & echo $! > logs/worker.pid",
      "description": "启动后台 Worker 进程",
      "wait_sec": 2
    }
  ]
}
```

---

## Phase 2: Query 和 Target 设计

### Target（目标状态）

必须是具体、可验证的：
```
好的 Target:
- config/database.yaml 中包含 "port: 19847"
- output/report.json 文件存在且包含 "status: success"
- services/worker.py 进程已停止

坏的 Target:
- "系统正常运行"（太模糊）
- "配置正确"（不具体）
```

### Query（问题描述）

设计原则：
1. **探索距离原则**：重点是需要经过多少步找到答案
2. **给探索方向，不给答案**：告诉需要修复什么**问题**，不告诉修改哪个**文件**

### Query 模糊度与难度

| 难度 | Query 特点 |
|------|-----------|
| D2-D3 | 直接告诉目标，路径需探索 |
| D4-D5 | 描述现象，需分析推断 |
| D6-D7 | 模糊描述，需多处拼凑 |

---

## Phase 3: Grader 设计

### Grader 结构

```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config.yaml", "keyword": "port: 19847"},
          "description": "验证端口配置已修复为正确值"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改配置"}
      ]
    }
  ]
}
```

### 设计原则

1. **至少 2-4 个验证点**
2. **验证具体内容，不只是文件存在**
3. **防止答案被猜测**：验证具体的答案值

详细规范见：`graders/` 目录

---

## Phase 4: Golden Action 设计

### 结构

```json
{
  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "reasoning": "查看错误日志，定位问题"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "config/database.yaml",
        "old_string": "timeout: 5000",
        "new_string": "timeout: 47000"
      },
      "reasoning": "根据故障单建议修复超时配置"
    }
  ]
}
```

### 设计原则

1. **长度符合难度要求**

| 难度 | 步数 |
|------|------|
| D2 | 1-2 步 |
| D3 | 3-4 步 |
| D4 | 5-6 步 |
| D5 | 7-8 步 |
| D6 | 9-10 步 |
| D7 | 11-15 步 |

2. **最后一步必须使用目标工具**
3. **包含探索阶段 + 行动阶段**

---

## Phase 5: 信息复杂化

通过信息藏匿增加探索距离，直到满足难度要求。

### 策略

1. **分散关键信息**：问题线索、背景知识、解决方案分散在多个文件中
2. **添加干扰文件**：旧版本、其他环境、相似命名
3. **设置红鲱鱼**：多个可疑点，只有一个是真正根因
4. **隐藏答案**：只给线索，不给答案

### 不能做的事

- 删除 Phase 1 创建的核心文件
- 大改目录结构
- 创建逻辑矛盾的线索
- 藏得太深导致无解

---

## 完成设计

完成设计后，你应该有：

1. 完整的环境文件列表（environment）
2. 初始化命令（init_commands，如果需要）
3. Query 和 Target
4. Graders（2-4 个验证点）
5. Golden Action（符合难度要求）

将这些保存为 `case.json` 到工作目录。

**下一步**：进入验证阶段，阅读 `core/verify.md`
