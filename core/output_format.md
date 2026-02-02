# 输出格式详解

本文档说明最终测试用例 JSON 的输出格式。

**保存位置**：工作目录中的 `case.json`

---

## JSON 结构概览

```json
{
  "task": { ... },
  "environment": [ ... ],
  "init_commands": [ ... ],
  "reference_solution": [ ... ],
  "graders": [ ... ],
  "haiku_evaluation": { ... },
  "haiku_trajectory": [ ... ],
  "quality_analysis": { ... }
}
```

---

## 字段详解

### task（任务元信息）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | Yes | 唯一标识，格式：`<TOOL>_D<DIFFICULTY>_<TIMESTAMP>` |
| `desc` | string | Yes | Query（问题描述） |
| `tool_name` | string | Yes | 目标工具 |
| `difficulty` | number | Yes | 难度等级（2-7） |
| `scenario_theme` | string | Yes | 场景主题 |

### environment（环境文件）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `path` | string | Yes | 文件相对路径 |
| `content` | string | Yes | 文件内容（`\n` 表示换行） |
| `executable` | boolean | Yes | 是否可执行 |

### init_commands（初始化命令，可选）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `command` | string | Yes | 要执行的命令 |
| `description` | string | Yes | 命令描述 |
| `wait_sec` | number | Yes | 执行后等待秒数 |

### reference_solution（Golden Action）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `tool` | string | Yes | 工具名称 |
| `input` | object | Yes | 工具输入参数 |
| `reasoning` | string | Yes | 推理说明 |

### graders（验证逻辑）

#### state_check（状态检查）

```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_content_contains",
      "params": {"path": "config.yaml", "keyword": "timeout: 47000"},
      "description": "验证超时配置已修复"
    }
  ]
}
```

#### tool_calls（工具使用检查）

**基础格式**：
```json
{
  "type": "tool_calls",
  "required": [
    {"tool": "Edit", "description": "必须使用 Edit 工具"}
  ]
}
```

**带参数验证的格式**：
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

| match 类型 | 含义 | 示例 |
|-----------|------|------|
| `exact`（默认） | 完全相等 | `"file_path": "config/db.yaml"` |
| `contains` | 包含匹配 | `{"match": "contains", "value": "logs/"}` |
| `regex` | 正则匹配 | `{"match": "regex", "value": "timeout\|error"}` |
| `any` | 不检查 | `{"match": "any"}` |

### haiku_evaluation（Haiku 验证结果）

| 字段 | 类型 | 说明 |
|------|------|------|
| `passed` | boolean | Haiku 是否通过 |
| `haiku_steps` | number | Haiku 执行步数 |
| `duration_sec` | number | 执行耗时（秒） |
| `passed_checks` | number | 通过的 check 数量 |
| `total_checks` | number | 总 check 数量 |

**数据来源**：从 `phase6_result.json` 复制

### haiku_trajectory（Haiku 执行轨迹）

| 字段 | 类型 | 说明 |
|------|------|------|
| `step` | number | 步骤编号 |
| `tool` | string | 使用的工具 |
| `input` | object | 工具输入参数 |
| `output` | string | 工具原始输出（最多 500 字符） |

**强制要求**：
- 从 `phase6_result.json` 的 `haiku_execution.trajectory` 原封不动复制
- output 是完整原始输出
- 没有 `reasoning` 字段
- 严禁编造、总结或改写

### quality_analysis（质量分析，可选）

| 字段 | 类型 | 说明 |
|------|------|------|
| `issue_type` | string | 问题类型（`"none"` 表示无问题） |
| `reworked` | boolean | 是否回炉修复过 |
| `file_count` | number | 环境文件数量 |
| `info_distribution` | string | 信息分散描述 |

---

## 验证清单

保存 case.json 前确认：

- [ ] task 字段完整
- [ ] environment 包含所有必需的文件
- [ ] reference_solution 步数符合难度要求
- [ ] graders 至少有 2-4 个验证点
- [ ] haiku_evaluation 和 haiku_trajectory 已从 phase6_result.json 复制
- [ ] haiku_trajectory 的 output 是完整原始输出（未改写）
