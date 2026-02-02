# 输出格式详解

本文档详细说明最终测试用例 JSON 的输出格式和各字段含义。

---

## 保存位置

最终的测试用例 JSON 保存在工作目录（沙盒）中：

```
/tmp/workspace/case.json
```

外部流程会从这里获取最终的测试用例。

---

## 完整格式

```json
{
  "task": {
    "id": "<TOOL_NAME>_<DIFFICULTY>_<TIMESTAMP>",
    "desc": "问题描述（Query）",
    "tool_name": "<TOOL_NAME>",
    "difficulty": <DIFFICULTY_NUMBER>,
    "scenario_theme": "场景主题"
  },
  "environment": [
    {
      "path": "相对路径",
      "content": "文件内容",
      "executable": false
    }
  ],
  "init_commands": [
    {
      "command": "bash命令",
      "description": "命令描述",
      "wait_sec": 2
    }
  ],
  "reference_solution": [
    {
      "tool": "工具名",
      "input": {"参数": "值"},
      "reasoning": "推理说明"
    }
  ],
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "check类型",
          "params": {"参数": "值"},
          "description": "验证说明"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "工具名", "description": "必须使用该工具"}
      ]
    }
  ],
  "haiku_evaluation": {
    "passed": true,
    "haiku_steps": 5,
    "duration_sec": 45,
    "passed_checks": 4,
    "total_checks": 4
  },
  "haiku_trajectory": [
    {
      "step": 1,
      "tool": "Read",
      "input": {"file_path": "..."},
      "output": "完整的原始工具输出"
    }
  ],
  "quality_analysis": {
    "issue_type": "none",
    "reworked": false,
    "file_count": 12,
    "info_distribution": "关键信息分散在..."
  }
}
```

---

## 字段详解

### task（任务元信息）

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | ✅ | 测试用例唯一标识 | `"Edit_D4_20260120_153000"` |
| `desc` | string | ✅ | Query（问题描述） | `"订单服务数据库连接超时，请排查配置问题"` |
| `tool_name` | string | ✅ | 目标工具 | `"Edit"`, `"Bash"`, `"Write"` 等 |
| `difficulty` | number | ✅ | 难度等级 | `2`, `3`, `4`, `5`, `6`, `7` |
| `scenario_theme` | string | ✅ | 场景主题 | `"微服务配置错误"` |

**id 格式**：`<TOOL_NAME>_D<DIFFICULTY>_<TIMESTAMP>`

示例：
```json
{
  "id": "Edit_D4_20260120_153000",
  "desc": "订单服务数据库连接超时，请排查配置问题",
  "tool_name": "Edit",
  "difficulty": 4,
  "scenario_theme": "微服务配置错误"
}
```

---

### environment（环境文件）

环境文件列表，定义测试题的"世界"。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `path` | string | ✅ | 文件相对路径 |
| `content` | string | ✅ | 文件内容（使用 `\n` 表示换行） |
| `executable` | boolean | ✅ | 是否可执行 |

示例：
```json
{
  "environment": [
    {
      "path": "config/database.yaml",
      "content": "host: localhost\nport: 5432\ntimeout: 5000",
      "executable": false
    },
    {
      "path": "logs/error.log",
      "content": "2026-01-20 15:00:00 ERROR Connection refused on port 5432\n2026-01-20 15:00:01 ERROR Database timeout",
      "executable": false
    },
    {
      "path": "scripts/deploy.sh",
      "content": "#!/bin/bash\necho 'Deploying...'\n",
      "executable": true
    }
  ]
}
```

---

### init_commands（初始化命令，可选）

在环境创建后执行的命令，主要用于启动后台进程。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `command` | string | ✅ | 要执行的命令 |
| `description` | string | ✅ | 命令描述 |
| `wait_sec` | number | ✅ | 执行后等待秒数 |

示例：
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

**使用场景**：
- KillShell 场景：预先启动后台进程
- 需要复杂初始状态的场景
- 生成初始数据文件

---

### reference_solution（Golden Action）

从 Query 到 Target 的参考解答路径。

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `tool` | string | ✅ | 工具名称 |
| `input` | object | ✅ | 工具输入参数 |
| `reasoning` | string | ✅ | 推理说明 |

示例：
```json
{
  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "reasoning": "查看错误日志，定位问题"
    },
    {
      "tool": "Grep",
      "input": {
        "pattern": "timeout",
        "output_mode": "files_with_matches"
      },
      "reasoning": "搜索超时相关配置文件"
    },
    {
      "tool": "Read",
      "input": {"file_path": "docs/incident-2847.md"},
      "reasoning": "查看故障单，找到推荐配置"
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

**要求**：
- 步数符合难度要求
- 最后一步使用目标工具
- 每一步都可执行

---

### graders（验证逻辑）

定义如何验证任务完成情况。

#### state_check（状态检查）

```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_content_contains",
      "params": {
        "path": "config/database.yaml",
        "keyword": "timeout: 47000"
      },
      "description": "验证超时配置已修复为正确值"
    },
    {
      "check": "file_content_not_contains",
      "params": {
        "path": "config/database.yaml",
        "keyword": "timeout: 5000"
      },
      "description": "验证错误的超时值已移除"
    }
  ]
}
```

#### tool_calls（工具使用检查）

基础格式（只验证工具使用）：
```json
{
  "type": "tool_calls",
  "required": [
    {"tool": "Edit", "description": "必须使用 Edit 工具"}
  ]
}
```

带参数验证的格式：
```json
{
  "type": "tool_calls",
  "required": [
    {
      "tool": "Edit",
      "params": {
        "file_path": "config/database.yaml",
        "new_string": {"match": "contains", "value": "timeout: 47000"}
      },
      "description": "必须修改 database.yaml 并设置正确的 timeout"
    }
  ]
}
```

**参数匹配方式**：
- `exact`（默认）：完全相等，如 `"file_path": "config/db.yaml"`
- `contains`：包含匹配，如 `{"match": "contains", "value": "logs/"}`
- `regex`：正则匹配，如 `{"match": "regex", "value": "timeout|error"}`

**完整示例**：
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config/database.yaml", "keyword": "timeout: 47000"},
          "description": "验证超时配置正确"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {
          "tool": "Read",
          "params": {"file_path": {"match": "contains", "value": "logs/"}},
          "description": "必须读取 logs 目录下的文件"
        },
        {
          "tool": "Edit",
          "params": {
            "file_path": "config/database.yaml",
            "new_string": {"match": "contains", "value": "timeout: 47000"}
          },
          "description": "必须修改 database.yaml 并设置正确的 timeout"
        }
      ]
    }
  ]
}
```

**详细 check 类型**：见 `~/.claude/skills/agent-testcase-generator/reference/grader_spec.md`

---

### haiku_evaluation（Haiku 验证结果）

Haiku 验证的评估结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| `passed` | boolean | Haiku 是否通过所有验证 |
| `haiku_steps` | number | Haiku 执行的步数 |
| `duration_sec` | number | Haiku 执行耗时（秒） |
| `passed_checks` | number | 通过的 check 数量 |
| `total_checks` | number | 总 check 数量 |

示例：
```json
{
  "haiku_evaluation": {
    "passed": true,
    "haiku_steps": 5,
    "duration_sec": 45,
    "passed_checks": 4,
    "total_checks": 4
  }
}
```

**数据来源**：从 `haiku_space/phase6_result.json` 复制

---

### haiku_trajectory（Haiku 执行轨迹）

Haiku 真实的工具调用轨迹。

| 字段 | 类型 | 说明 |
|------|------|------|
| `step` | number | 步骤编号 |
| `tool` | string | 使用的工具 |
| `input` | object | 工具输入参数 |
| `output` | string | 工具原始输出（最多 500 字符） |

示例：
```json
{
  "haiku_trajectory": [
    {
      "step": 1,
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "output": "2026-01-20 15:00:00 ERROR Connection refused on port 5432\n2026-01-20 15:00:01 ERROR Database timeout\n..."
    },
    {
      "step": 2,
      "tool": "Grep",
      "input": {"pattern": "timeout", "output_mode": "files_with_matches"},
      "output": "config/database.yaml\ndocs/incident-2847.md\nmonitoring/metrics.yaml"
    },
    {
      "step": 3,
      "tool": "Read",
      "input": {"file_path": "docs/incident-2847.md"},
      "output": "# Incident 2847\n\n根据运维团队建议，数据库超时应设置为 47000ms..."
    },
    {
      "step": 4,
      "tool": "Edit",
      "input": {
        "file_path": "config/database.yaml",
        "old_string": "timeout: 5000",
        "new_string": "timeout: 47000"
      },
      "output": "File edited successfully"
    }
  ]
}
```

**🚨 强制要求**：
- ✅ 必须从 `haiku_space/phase6_result.json` 的 `haiku_execution.trajectory` 原封不动复制
- ✅ output 是完整的原始输出（可能被截断到 500 字符）
- ✅ 没有 `reasoning` 字段（真实轨迹没有）
- ❌ 严禁编造、总结或改写

---

### quality_analysis（质量分析，可选）

测试用例的质量分析和元信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `issue_type` | string | 问题类型（`"none"` 表示无问题） |
| `reworked` | boolean | 是否回炉修复过 |
| `file_count` | number | 环境文件数量 |
| `info_distribution` | string | 信息分散描述 |

示例：
```json
{
  "quality_analysis": {
    "issue_type": "none",
    "reworked": false,
    "file_count": 12,
    "info_distribution": "关键信息分散在 logs/error.log, docs/incident-2847.md, monitoring/metrics.yaml 中"
  }
}
```

**可选**：可以使用 `phase7_quality.py` 生成，也可以手动填写。

---

## 完整示例

```json
{
  "task": {
    "id": "Edit_D4_20260120_153000",
    "desc": "订单服务数据库连接超时，请根据监控和故障单排查配置问题",
    "tool_name": "Edit",
    "difficulty": 4,
    "scenario_theme": "微服务配置错误"
  },
  "environment": [
    {
      "path": "config/database.yaml",
      "content": "host: localhost\nport: 5432\ntimeout: 5000",
      "executable": false
    },
    {
      "path": "logs/error.log",
      "content": "2026-01-20 15:00:00 ERROR Connection refused\n2026-01-20 15:00:01 ERROR Database timeout",
      "executable": false
    },
    {
      "path": "docs/incident-2847.md",
      "content": "# Incident 2847\n\n根据运维团队建议，数据库超时应设置为 47000ms",
      "executable": false
    }
  ],
  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "reasoning": "查看错误日志"
    },
    {
      "tool": "Grep",
      "input": {"pattern": "timeout", "output_mode": "files_with_matches"},
      "reasoning": "搜索超时相关配置"
    },
    {
      "tool": "Read",
      "input": {"file_path": "docs/incident-2847.md"},
      "reasoning": "查看故障单"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "config/database.yaml",
        "old_string": "timeout: 5000",
        "new_string": "timeout: 47000"
      },
      "reasoning": "修复超时配置"
    }
  ],
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config/database.yaml", "keyword": "timeout: 47000"},
          "description": "验证超时配置已修复"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具"}
      ]
    }
  ],
  "haiku_evaluation": {
    "passed": true,
    "haiku_steps": 4,
    "duration_sec": 35,
    "passed_checks": 2,
    "total_checks": 2
  },
  "haiku_trajectory": [
    {
      "step": 1,
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "output": "2026-01-20 15:00:00 ERROR Connection refused..."
    },
    {
      "step": 2,
      "tool": "Grep",
      "input": {"pattern": "timeout", "output_mode": "files_with_matches"},
      "output": "config/database.yaml\ndocs/incident-2847.md"
    },
    {
      "step": 3,
      "tool": "Read",
      "input": {"file_path": "docs/incident-2847.md"},
      "output": "# Incident 2847\n\n根据运维团队建议..."
    },
    {
      "step": 4,
      "tool": "Edit",
      "input": {
        "file_path": "config/database.yaml",
        "old_string": "timeout: 5000",
        "new_string": "timeout: 47000"
      },
      "output": "File edited successfully"
    }
  ],
  "quality_analysis": {
    "issue_type": "none",
    "reworked": false,
    "file_count": 3,
    "info_distribution": "关键信息分散在 logs/error.log 和 docs/incident-2847.md 中"
  }
}
```

---

## 验证清单

保存 case.json 前确认：

- [ ] task 字段完整（id, desc, tool_name, difficulty, scenario_theme）
- [ ] environment 包含所有必需的文件
- [ ] init_commands 格式正确（如果有）
- [ ] reference_solution 步数符合难度要求
- [ ] graders 至少有 2-4 个验证点
- [ ] haiku_evaluation 和 haiku_trajectory 已从 phase6_result.json 复制
- [ ] haiku_trajectory 的 output 是完整原始输出（未改写）
- [ ] 文件保存为 `/tmp/workspace/case.json`（工作目录）

---

## 下一步

保存 case.json 后，测试用例生成完成！外部流程会从工作目录（沙盒）中获取这个文件。
