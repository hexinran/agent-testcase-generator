# Grader 格式规范

本文档定义 Grader（评分器）的标准格式。

---

## 核心原则：初始状态必须失败

**Grader 在初始环境状态下必须失败，只有 Agent 正确执行任务后才能通过。**

```
❌ 错误设计：
  环境：config.yaml 中 port: 8080
  Grader：检查 config.yaml 存在
  问题：初始状态就能通过！

✅ 正确设计：
  环境：config.yaml 中 port: 5432（错误值）
  Grader：检查 config.yaml 包含 "port: 8080"
  正确：初始状态失败，修复后通过
```

---

## Grader 类型

### 1. state_check（状态检查）

检查任务执行后的系统状态。

```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "<check_type>",
      "params": { ... },
      "description": "人类可读的描述"
    }
  ]
}
```

### 2. tool_calls（工具调用检查）

验证 Agent 是否使用了特定工具，支持参数匹配验证。

#### 基础格式（只验证工具使用）

```json
{
  "type": "tool_calls",
  "required": [
    {"tool": "Edit", "description": "必须使用 Edit 工具"}
  ]
}
```

#### 带参数验证的格式

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

#### 参数匹配方式

| match 类型 | 含义 | 示例 |
|-----------|------|------|
| `exact`（默认） | 完全相等 | `"file_path": "config/db.yaml"` |
| `contains` | 包含匹配 | `{"match": "contains", "value": "logs/"}` |
| `regex` | 正则匹配 | `{"match": "regex", "value": "timeout\|error"}` |
| `any` | 不检查 | `{"match": "any"}` |

**简化写法**：字符串值默认为 exact 匹配
```json
"file_path": "config/database.yaml"
// 等同于
"file_path": {"match": "exact", "value": "config/database.yaml"}
```

---

## 标准 Check 类型

### 文件检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `file_exists` | `path` | 检查文件存在 |
| `file_not_exists` | `path` | 检查文件不存在 |
| `file_content_contains` | `path`, `keyword`, `case_insensitive?` | 检查文件包含关键词 |
| `file_content_not_contains` | `path`, `keyword` | 检查文件不包含关键词 |
| `file_content_match` | `path`, `pattern` | 检查文件内容匹配正则 |
| `directory_exists` | `path` | 检查目录存在 |
| `file_executable` | `path` | 检查文件可执行 |

### 执行结果检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `bash_check` | `command`, `expected` | 执行命令检查输出 |
| `bash_exit_code` | `command`, `expected_code?` | 检查命令退出码 |

### 进程管理检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `bash_process_running` | `process_name?`, `pid_file?` | 检查进程运行 |
| `bash_process_not_running` | `process_name?`, `pid_file?` | 检查进程已停止 |

### Grep/Glob 结果检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `grep_output_contains` | `pattern`, `path`, `expected` | 检查 grep 输出 |
| `grep_finds_pattern` | `pattern`, `path`, `expected_files` | 检查 grep 找到的文件 |
| `glob_result_contains` | `pattern`, `expected_files` | 检查 glob 结果包含文件 |
| `glob_result_count` | `pattern`, `min_count?`, `max_count?` | 检查 glob 结果数量 |

### Web 工具检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `tool_used_webfetch` | `url_pattern?` | 验证使用了 WebFetch |
| `tool_used_web_search` | `keyword_pattern?` | 验证使用了 web_search |

### 结构化数据检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `json_path_equals` | `path`, `json_path`, `expected` | 检查 JSON 路径值 |
| `yaml_key_equals` | `path`, `key_path`, `expected` | 检查 YAML 键值 |

### 高级检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `custom_script` | `script_content`, `timeout?` | 执行自定义 Python 脚本 |
| `any_of` | `checks` | 多个 check 满足其一 |

---

## 路径格式规范

- **推荐使用相对路径**: `config/database.yaml`
- **支持占位符**: `{{SANDBOX}}/config/database.yaml`
- **执行器自动解析**: 相对路径会被解析为 `sandbox_dir / path`

---

## 实现细节

所有 check 类型的实现代码在 `scripts/custom_checks.py` 中。

函数签名：
```python
def check_<check_type>(
    sandbox_dir: Path,
    params: dict,
    trajectory: list = None
) -> Tuple[bool, str]:
    """返回 (是否通过, 描述信息)"""
```

参数匹配实现在 `scripts/phase4_verify.py` 的 `match_param_value()` 函数中。
