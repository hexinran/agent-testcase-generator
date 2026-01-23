# 脚手架脚本详细用法

本文档详细说明所有脚手架脚本的参数、选项和使用方法。

---

## 脚本概览

| 脚本 | 用途 | 阶段 |
|------|------|------|
| `phase4_verify.py` | 自测验证 | Phase 4 |
| `phase6_haiku.py` | Haiku 验证 | Phase 6 |
| `phase7_quality.py` | 质量评估 | Phase 7 |
| `custom_checks.py` | Check 验证模块 | 被其他脚本调用 |

**脚本位置**：`~/.claude/skills/agent-testcase-generator/scripts/`

---

## phase4_verify.py - 自测验证

### 功能

执行 Golden Action（参考解答）并验证所有 Grader。

### 基本用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py <case_json_path>
```

### 参数

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 | `case.json` 或 `/tmp/workspace/case.json` |
| `-v, --verbose` | ❌ | 详细输出模式 | `--verbose` |
| `--keep-env` | ❌ | 保留验证环境（不删除） | `--keep-env` |
| `--verify-dir` | ❌ | 指定验证目录（默认自动创建） | `--verify-dir ./phase4_test` |

### 完整示例

```bash
# 基本用法
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json

# 详细输出
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --verbose

# 保留环境用于调试
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --keep-env --verbose

# 指定验证目录
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --verify-dir ./my_test
```

### 输出

**终端输出示例**（成功）：
```
=== Phase 4 验证开始 ===
测试用例: case.json
创建验证环境: /tmp/workspace/phase4_verify_abc123/

执行环境初始化...
  创建 12 个文件...
  执行 init_commands (如果有)...

执行 Golden Action (4 步)...
  Step 1/4: Read logs/error.log ✓
  Step 2/4: Grep timeout ✓
  Step 3/4: Read docs/incident-2847.md ✓
  Step 4/4: Edit config/database.yaml ✓

验证 Graders...
  state_check: 3/3 通过 ✓
    ✓ file_content_contains: config/database.yaml 包含 "port: 19847"
    ✓ file_content_contains: config/database.yaml 包含 "timeout: 47000"
    ✓ file_content_not_contains: config/database.yaml 不包含 "timeout: 5000"
  tool_calls: 1/1 通过 ✓
    ✓ 使用了 Edit 工具

=== Phase 4 验证通过 ✓ ===
结果已保存: phase4_result.json
```

**终端输出示例**（失败）：
```
=== Phase 4 验证开始 ===
...
执行 Golden Action (4 步)...
  Step 1/4: Read logs/error.log ✓
  Step 2/4: Grep timeout ✗
    错误: 文件不存在: config/database.yaml

=== Phase 4 验证失败 ✗ ===
详细信息见: phase4_result.json
```

**结果文件**：`phase4_result.json`

```json
{
  "passed": true,
  "golden_action_result": {
    "all_steps_passed": true,
    "total_steps": 4,
    "passed_steps": 4,
    "steps": [
      {
        "step": 1,
        "tool": "Read",
        "input": {"file_path": "logs/error.log"},
        "passed": true,
        "output": "Connection refused...",
        "error": null
      },
      ...
    ]
  },
  "grader_result": {
    "all_passed": true,
    "state_check": {"passed": 3, "total": 3, "details": [...]},
    "tool_calls": {"passed": 1, "total": 1, "details": [...]}
  },
  "environment_path": "/tmp/workspace/phase4_verify_abc123/",
  "timestamp": "2026-01-20T15:30:00Z"
}
```

### 常见问题

**Q1: 找不到 case.json**

确认文件路径正确，或使用绝对路径：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py /tmp/workspace/case.json
```

**Q2: Golden Action 某步失败**

查看 `phase4_result.json` 中的 `error` 字段，检查：
- 文件路径是否正确
- 工具参数是否完整
- 环境中是否包含所需文件

**Q3: Grader 验证失败**

查看 `grader_result.details`，确认：
- 文件内容是否符合预期
- Grader 参数（keyword, pattern）是否正确
- 是否需要调整 Grader 验证条件

---

## phase6_haiku.py - Haiku 验证

### 功能

在隔离环境中执行 Haiku 模型验证，捕获真实的工具调用轨迹。

### 基本用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py <case_json_path> --haiku-dir <haiku_space_path>
```

### 参数

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 | `case.json` |
| `--haiku-dir` | ✅ | Haiku 工作目录（已准备好环境） | `haiku_space/` |
| `-v, --verbose` | ❌ | 详细输出模式 | `--verbose` |
| `--timeout` | ❌ | Haiku 执行超时（秒，默认 180） | `--timeout 300` |
| `--keep-log` | ❌ | 保留 Haiku 执行日志 | `--keep-log` |

### 前置准备

在调用脚本前，必须先准备 Haiku 环境：

```bash
# 1. 创建 haiku_space 目录
mkdir -p haiku_space

# 2. 复制环境文件（不要复制 case.json）
cp -r config/ logs/ docs/ services/ haiku_space/
```

### 完整示例

```bash
# 基本用法
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --haiku-dir haiku_space/

# 详细输出
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --haiku-dir haiku_space/ --verbose

# 增加超时时间
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --haiku-dir haiku_space/ --timeout 300

# 保留日志用于调试
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --haiku-dir haiku_space/ --keep-log --verbose
```

### 输出

**终端输出示例**（成功）：
```
=== Phase 6 Haiku 验证开始 ===
测试用例: case.json
Haiku 工作目录: /tmp/workspace/haiku_space/

读取测试用例...
Query: "订单服务数据库连接超时，请排查配置问题"

调用 Haiku CLI...
Haiku 执行中（最长 180 秒）...

Haiku 执行轨迹:
  Step 1: Read logs/error.log
  Step 2: Grep timeout
  Step 3: Read docs/incident-2847.md
  Step 4: Read config/database.yaml
  Step 5: Edit config/database.yaml

Haiku 执行完成: 5 步，耗时 45 秒

验证 Graders...
  state_check: 3/3 通过 ✓
  tool_calls: 1/1 通过 ✓

=== Phase 6 验证通过 ✓ ===
结果已保存: /tmp/workspace/haiku_space/phase6_result.json
```

**结果文件**：`haiku_space/phase6_result.json`

```json
{
  "passed": true,
  "haiku_steps": 5,
  "duration_sec": 45,
  "haiku_evaluation": {
    "passed": true,
    "haiku_steps": 5,
    "duration_sec": 45,
    "passed_checks": 4,
    "total_checks": 4
  },
  "haiku_execution": {
    "query": "订单服务数据库连接超时，请排查配置问题",
    "trajectory": [
      {
        "step": 1,
        "tool": "Read",
        "input": {"file_path": "logs/error.log"},
        "output": "Connection refused on port 5432..."
      },
      {
        "step": 2,
        "tool": "Grep",
        "input": {"pattern": "timeout", "output_mode": "files_with_matches"},
        "output": "config/database.yaml\ndocs/incident-2847.md"
      },
      ...
    ]
  },
  "grader_result": {...},
  "timestamp": "2026-01-20T15:35:00Z"
}
```

### 使用结果

从 `phase6_result.json` 中提取以下数据，复制到最终的 `case.json`：

1. **haiku_evaluation**（整个对象）
2. **haiku_trajectory**（从 `haiku_execution.trajectory` 复制）

```json
{
  "haiku_evaluation": {...},
  "haiku_trajectory": [...]
}
```

### 常见问题

**Q1: 找不到 haiku-dir**

确认目录存在且已准备好环境：
```bash
ls -la haiku_space/
# 应该看到 config/, logs/, docs/ 等目录
```

**Q2: Haiku 执行超时**

增加 timeout 参数：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --haiku-dir haiku_space/ --timeout 300
```

**Q3: Haiku 看到了 case.json**

检查 haiku_space/ 中是否错误地复制了 case.json：
```bash
ls haiku_space/case.json
# 不应该存在
```

**Q4: 轨迹数据格式不对**

确保：
- 直接从 `phase6_result.json` 复制
- 没有手动修改 output 字段
- 没有添加 reasoning 字段

---

## phase7_quality.py - 质量评估

### 功能

评估测试用例的质量，包括 hacking 风险、难度合理性、信息分散度等。

### 基本用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase7_quality.py <case_json_path>
```

### 参数

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 | `case.json` |
| `--json` | ❌ | 输出 JSON 格式 | `--json` |
| `-v, --verbose` | ❌ | 详细输出模式 | `--verbose` |

### 完整示例

```bash
# 基本用法（人类可读格式）
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase7_quality.py case.json

# JSON 格式输出
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase7_quality.py case.json --json

# 详细输出
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase7_quality.py case.json --verbose
```

### 输出

**终端输出示例**：
```
=== 测试用例质量评估 ===

基本信息:
  工具: Edit
  难度: D4
  场景: 微服务配置错误

难度合理性:
  环境文件数: 12 (要求: 12-15) ✓
  Golden Action 步数: 5 (要求: 5-6) ✓
  信息分散度: 关键信息分散在 3 个文件中 ✓

Hacking 风险:
  答案可预测性: 低 ✓
    - 端口 19847 来自 docs/incident-2847.md
    - 超时 47000 来自 monitoring/metrics.yaml
  Grader 验证: 验证具体值 ✓

Query 质量:
  明确性: 模糊度适中 ✓
  无具体命令: ✓
  无文件路径: ✓

Grader 质量:
  验证点数量: 4 ✓
  验证具体内容: ✓
  防止 hacking: ✓

总体评分: A (优秀)
```

**JSON 输出示例**：
```json
{
  "overall_score": "A",
  "issues": [],
  "warnings": [],
  "metrics": {
    "file_count": 12,
    "golden_action_steps": 5,
    "info_distribution": "分散在 3 个文件",
    "hacking_risk": "低",
    "grader_quality": "优秀"
  },
  "recommendations": []
}
```

### 评估维度

| 维度 | 检查内容 |
|------|---------|
| **难度合理性** | 文件数、步数是否符合难度要求 |
| **Hacking 风险** | 答案是否可预测、Grader 是否验证具体值 |
| **信息分散度** | 关键信息是否分散在多个文件（D4+） |
| **Query 质量** | 是否包含具体命令、文件路径 |
| **Grader 质量** | 验证点数量、是否验证具体内容 |

### 常见问题

**Q1: 评分低怎么办**

查看 `issues` 和 `warnings` 了解具体问题，根据建议修复。

**Q2: 如何提高评分**

- 增加信息分散度
- 使用不可预测的答案值
- 添加更多验证点
- 确保 Grader 验证具体内容

---

## custom_checks.py - Check 验证模块

### 功能

统一的 Check 验证模块，被 phase4_verify.py 和 phase6_haiku.py 调用。

### 说明

这是一个内部模块，不需要直接调用。

提供所有 check 类型的实现：
- `file_exists`
- `file_content_contains`
- `file_content_not_contains`
- `file_content_match`
- `bash_check`
- `bash_exit_code`
- `bash_process_running`
- `bash_process_not_running`
- 等等...

完整 check 类型见：`~/.claude/skills/agent-testcase-generator/reference/grader_spec.md`

---

## 故障排查

### 脚本执行权限问题

```bash
# 确保脚本可执行
chmod +x ~/.claude/skills/agent-testcase-generator/scripts/*.py
```

### Python 依赖问题

脚本需要 Python 3.7+，如果遇到依赖问题：

```bash
# 检查 Python 版本
python3 --version

# 确保在正确的环境中
which python3
```

### 路径问题

始终使用绝对路径调用脚本：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

而不是：
```bash
python3 scripts/phase4_verify.py case.json  # ❌ 可能找不到
```

---

## 总结

三个核心脚本的使用时机：

1. **phase4_verify.py**：设计完成后立即使用，验证 Golden Action 可行性
2. **phase6_haiku.py**：Phase 4 通过后使用，测试题目合理性
3. **phase7_quality.py**：最后使用，评估题目质量（可选）

记住：**严禁跳过验证或编造数据**，必须使用脚手架真实执行。
