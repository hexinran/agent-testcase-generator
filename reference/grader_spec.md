# Grader 格式规范 v2

本文档定义了 Agent 测试用例中 Grader（评分器）的标准格式。

## 概述

Grader 用于验证 Agent 是否正确完成了任务。相比旧版 `golden_check`，新版格式具有：

1. **结构化分类**: 将检查分为 `state_check` 和 `tool_calls` 两类
2. **可执行代码**: 包含 `grader_implementations` 字段，存储实际验证代码
3. **标准化命名**: 统一 check 类型命名和参数结构
4. **更好的可读性**: 每个 check 包含 `description` 描述

---

## Grader 设计核心原则

### 初始状态必须失败

**这是最重要的原则：Grader 在初始环境状态下必须失败，只有 Agent 正确执行任务后才能通过。**

如果 Grader 在 Agent 执行前就能通过，说明：
- 测试用例无效（无法区分"做了"和"没做"）
- 环境设置有问题（目标状态已经存在）
- Grader 设计过于宽松

**示例**：

```
任务：修复配置文件中的端口错误

❌ 错误设计：
  环境：config.yaml 中 port: 8080
  Grader：检查 config.yaml 存在
  问题：初始状态就能通过！

✅ 正确设计：
  环境：config.yaml 中 port: 5432（错误值）
  Grader：检查 config.yaml 包含 "port: 8080"
  正确：初始状态失败，修复后通过
```

**验证方法**：

设计完 Grader 后，心理模拟：
1. 只部署环境，不执行任何操作
2. 运行 Grader
3. 如果通过 → 设计有问题，需要修改

---

## 格式对比

### 旧格式 (golden_check)

```json
{
  "golden_check": [
    {"type": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port: 8080"}},
    {"type": "file_exists", "params": {"path": "output.log"}}
  ]
}
```

### 新格式 (graders)

```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config.yaml", "keyword": "port: 8080"},
          "description": "验证配置文件包含正确的端口"
        },
        {
          "check": "file_exists",
          "params": {"path": "output.log"},
          "description": "验证输出文件已生成"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改配置"}
      ]
    }
  ],
  "grader_implementations": {
    "file_content_contains": "def check_file_content_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]: ...",
    "file_exists": "def check_file_exists(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]: ...",
    "_helper__resolve_path": "def _resolve_path(path: str, sandbox_dir: Path) -> Path: ..."
  }
}
```

---

## Grader 类型定义

### 1. state_check（状态检查）

检查任务执行后的系统状态（文件、输出等）。

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

验证 Agent 是否使用了特定工具。

```json
{
  "type": "tool_calls",
  "required": [
    {"tool": "Edit", "description": "必须使用 Edit 工具"}
  ]
}
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

### Grep/Glob 结果检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `grep_output_contains` | `pattern`, `path`, `expected`/`expected_file` | 检查 grep 输出 |
| `grep_finds_pattern` | `pattern`, `path`, `expected_files` | 检查 grep 找到的文件 |
| `glob_result_contains` | `pattern`, `expected_files` | 检查 glob 结果包含文件 |
| `glob_result_count` | `pattern`, `min_count?`, `max_count?` | 检查 glob 结果数量 |

### 高级检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `custom_script` | `script_content`, `timeout?` | 执行自定义 Python 脚本 |
| `any_of` | `checks` | 多个 check 满足其一 |

### 进程管理检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `bash_process_running` | `process_name?`, `pid_file?` | 检查进程是否运行 |
| `bash_process_not_running` | `process_name?`, `pid_file?` | 检查进程已停止 |

### Web 工具检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `tool_used_webfetch` | `url_pattern?` | 验证使用了 WebFetch |
| `tool_used_web_search` | `keyword_pattern?` | 验证使用了 web_search |

### Git 相关检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `git_commit_message` | `pattern` | 检查最新提交消息匹配模式 |
| `git_branch_exists` | `branch_name` | 检查分支是否存在 |
| `git_file_staged` | `file_path` | 检查文件是否已暂存 |
| `git_file_committed` | `file_path` | 检查文件是否在最新提交中 |

### 结构化数据检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `json_path_equals` | `path`, `json_path`, `expected` | 检查 JSON 路径值 |
| `yaml_key_equals` | `path`, `key_path`, `expected` | 检查 YAML 键值 |

### Plan 模式检查类

| Check 类型 | 参数 | 描述 |
|-----------|------|------|
| `file_moved` | `source`, `destination` | 验证文件从源移动到目标 |
| `import_updated` | `path`, `old_import`, `new_import` | 验证导入语句已更新 |
| `file_not_exists` | `path` | 检查文件不存在 |
| `directory_exists` | `path` | 检查目录存在 |

---

## Grader Implementation 函数签名

所有 grader implementation 必须遵循统一的函数签名：

```python
def check_<check_type>(
    sandbox_dir: Path,
    params: dict,
    trajectory: list = None
) -> Tuple[bool, str]:
    """
    执行检查

    Args:
        sandbox_dir: sandbox 根目录
        params: check 的参数
        trajectory: Agent 执行轨迹（可选，用于 tool_calls 检查）

    Returns:
        (passed, message): 是否通过 + 描述信息
    """
    pass
```

### Helper 函数命名约定

Helper 函数以 `_helper__` 前缀命名：

```python
"_helper__resolve_path": "def _resolve_path(path: str, sandbox_dir: Path) -> Path: ..."
```

---

## 标准 Implementation 模板

### 文件类检查

```python
def check_file_content_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """检查文件内容是否包含关键词"""
    path = params.get('path', '')
    keyword = params.get('keyword', '')
    case_insensitive = params.get('case_insensitive', False)

    full_path = _resolve_path(path, sandbox_dir)

    if not full_path.exists():
        return False, f"file not found: {path}"

    try:
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if case_insensitive:
            found = keyword.lower() in content.lower()
        else:
            found = keyword in content

        if found:
            return True, f"keyword '{keyword}' found in {path}"
        return False, f"keyword '{keyword}' not found in {path}"
    except Exception as e:
        return False, f"error reading file: {e}"
```

### Bash 检查

```python
def check_bash_check(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:
    """执行 bash 命令并检查输出"""
    command = params.get('command', '')
    expected = params.get('expected', '')

    if not command:
        return False, "no command provided"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(sandbox_dir),
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout.strip()
        if expected in output:
            return True, f"command output contains '{expected}'"
        return False, f"expected '{expected}' not in output: {output[:100]}"
    except Exception as e:
        return False, f"bash error: {e}"
```

### Helper 函数

```python
def _resolve_path(path: str, sandbox_dir: Path) -> Path:
    """解析路径，支持相对路径和绝对路径"""
    if not path:
        return sandbox_dir
    p = Path(path)
    if p.is_absolute():
        return p
    return sandbox_dir / path
```

---

## 路径格式规范

1. **推荐使用相对路径**: `config/database.yaml`
2. **支持占位符**: `{{SANDBOX}}/config/database.yaml`
3. **执行器自动解析**: 相对路径会被解析为 `sandbox_dir / path`

```json
// 推荐
{"path": "config/database.yaml"}

// 也支持
{"path": "{{SANDBOX}}/config/database.yaml"}
```

---

## 完整示例

```json
{
  "task": {
    "id": "Edit_D4_20260119",
    "desc": "订单服务数据库连接超时，请排查并修复配置问题",
    "tool_name": "Edit",
    "difficulty": 4
  },
  "environment": [
    {"path": "config/database.yaml", "content": "..."},
    {"path": "logs/error.log", "content": "..."}
  ],
  "reference_solution": [
    {"tool": "Read", "input": {"file_path": "logs/error.log"}, "reasoning": "查看错误日志"},
    {"tool": "Grep", "input": {"pattern": "timeout"}, "reasoning": "搜索超时相关配置"},
    {"tool": "Edit", "input": {"file_path": "config/database.yaml", "..."}, "reasoning": "修复配置"}
  ],
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config/database.yaml", "keyword": "timeout: 30000"},
          "description": "验证超时配置已修复为正确值"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "config/database.yaml", "keyword": "timeout: 5000"},
          "description": "验证错误的超时值已移除"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改配置"}
      ]
    }
  ],
  "grader_implementations": {
    "file_content_contains": "def check_file_content_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:\n    path = params.get('path', '')\n    keyword = params.get('keyword', '')\n    case_insensitive = params.get('case_insensitive', False)\n\n    full_path = _resolve_path(path, sandbox_dir)\n\n    if not full_path.exists():\n        return False, f\"file not found: {path}\"\n\n    try:\n        content = full_path.read_text(encoding='utf-8', errors='replace')\n        if case_insensitive:\n            found = keyword.lower() in content.lower()\n        else:\n            found = keyword in content\n\n        if found:\n            return True, f\"keyword '{keyword}' found in {path}\"\n        return False, f\"keyword '{keyword}' not found in {path}\"\n    except Exception as e:\n        return False, f\"error reading file: {e}\"",
    "file_content_not_contains": "def check_file_content_not_contains(sandbox_dir: Path, params: dict, trajectory=None) -> Tuple[bool, str]:\n    path = params.get('path', '')\n    keyword = params.get('keyword', '')\n    case_insensitive = params.get('case_insensitive', False)\n\n    full_path = _resolve_path(path, sandbox_dir)\n\n    if not full_path.exists():\n        return True, f\"file not found (OK for not_contains): {path}\"\n\n    try:\n        content = full_path.read_text(encoding='utf-8', errors='replace')\n        if case_insensitive:\n            found = keyword.lower() in content.lower()\n        else:\n            found = keyword in content\n\n        if not found:\n            return True, f\"keyword '{keyword}' correctly not in {path}\"\n        return False, f\"keyword '{keyword}' unexpectedly found in {path}\"\n    except Exception as e:\n        return False, f\"error reading file: {e}\"",
    "_helper__resolve_path": "def _resolve_path(path: str, sandbox_dir: Path) -> Path:\n    if not path:\n        return sandbox_dir\n    p = Path(path)\n    if p.is_absolute():\n        return p\n    return sandbox_dir / path"
  }
}
```

---

## 迁移指南

### 从旧格式迁移

1. 将 `golden_check` 改为 `graders`
2. 将 check 按类型分组到 `state_check` 和 `tool_calls`
3. 将 `type` 改为 `check`
4. 为每个 check 添加 `description`
5. 添加 `grader_implementations` 字段

### 自动迁移脚本

```python
def migrate_golden_check(old_case: dict) -> dict:
    """将旧格式转换为新格式"""
    golden_check = old_case.get('golden_check', old_case.get('test_case', {}).get('golden_check', []))

    state_checks = []
    tool_calls = []

    for check in golden_check:
        check_type = check.get('type', '')
        params = check.get('params', {})

        if check_type == 'tool_used':
            tool_calls.append({
                'tool': params.get('tool', params.get('name', '')),
                'description': f"必须使用 {params.get('tool', '')} 工具"
            })
        else:
            state_checks.append({
                'check': check_type,
                'params': params,
                'description': f"验证 {check_type}"
            })

    graders = []
    if state_checks:
        graders.append({'type': 'state_check', 'checks': state_checks})
    if tool_calls:
        graders.append({'type': 'tool_calls', 'required': tool_calls})

    return graders
```
