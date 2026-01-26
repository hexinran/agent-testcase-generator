# 自测与修复流程

本文档指导你使用脚手架工具验证你的测试用例设计是否可行。

---

## 目的

**自测**：验证 Golden Action（参考解答）是否可以成功执行，以及所有 Grader 是否能通过。

**为什么要自测**：
- 确保 Golden Action 每一步都可执行
- 确保环境文件完整（没有缺失）
- 确保 Grader 验证逻辑正确
- 发现设计问题，及时修复

**与 Haiku 验证的区别**：
- 自测：按 reference_solution 执行，**不调用 AI 模型**，快速（几秒）
- Haiku 验证：Haiku 模型自己探索执行，慢（几分钟）

---

## 前置条件

1. 你已完成测试用例设计（environment, Query, Target, Grader, Golden Action）
2. 已将测试用例保存为 `case.json` 到工作目录

---

## 执行步骤

### Step 1: 保存测试用例

确保 `case.json` 已保存在工作目录中。

**case.json 必须包含的字段**：
```json
{
  "task": {...},
  "environment": [...],
  "init_commands": [...],  // 可选，KillShell 场景必须
  "reference_solution": [...],
  "graders": [...]
}
```

### Step 2: 执行验证脚本

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

**脚本会自动**：
1. 创建 `phase4_workspace/` 子目录
2. 根据 `environment` 创建文件
3. 执行 `init_commands`（如果有）
4. 按 `reference_solution` 逐步执行
5. 验证所有 `graders`
6. 输出详细结果
7. 清理工作目录（除非使用 `--keep-env`）

### Step 3: 查看结果

脚本会输出到终端，并保存到 `phase4_result.json`。

**成功示例**：
```
============================================================
Phase 4: 自测验证
============================================================
Case ID: Edit_D4_20260126
Tool: Edit, Difficulty: D4
Environment files: 12
Reference solution steps: 5
Work directory: /tmp/workspace/phase4_workspace

--- Setting up workspace ---
  Created 12 environment files
  Executing 1 init commands...
    - 启动后台服务

--- Executing Reference Solution ---
  ✓ Step 1: Read - Read 1523 chars from logs/error.log
  ✓ Step 2: Grep - Grep executed (exploration)
  ✓ Step 3: Read - Read 892 chars from docs/incident-2847.md
  ✓ Step 4: Read - Read 456 chars from config/database.yaml
  ✓ Step 5: Edit - Edited config/database.yaml

--- Verifying Graders ---
  ✓ [file_content_contains] keyword 'timeout: 47000' found in config/database.yaml
  ✓ [file_content_not_contains] keyword 'timeout: 5000' correctly not in config/database.yaml

--- Tool Calls ---
  ✓ Edit: 必须使用 Edit 工具修改配置

============================================================
✓ Phase 4 PASSED
  Checks: 2/2 passed
  Tool calls verified: True
============================================================

Result saved to: /tmp/workspace/phase4_result.json
Cleaned up: /tmp/workspace/phase4_workspace
```

**失败示例**：
```
--- Executing Reference Solution ---
  ✓ Step 1: Read - Read 1523 chars from logs/error.log
  ✗ Step 2: Edit - File not found: config/database.yaml

--- Verifying Graders ---
  ✗ [file_content_contains] file not found: config/database.yaml

============================================================
✗ Phase 4 FAILED
  Checks: 0/2 passed
  Tool calls verified: True
============================================================
```

### Step 4: 读取详细结果

```bash
Read phase4_result.json
```

**结果结构**：
```json
{
  "phase": 4,
  "case_id": "Edit_D4_20260126",
  "timestamp": "2026-01-26T14:30:00",
  "passed": true,
  "execution_trajectory": [
    {"step": 1, "tool": "Read", "success": true, "output": "..."},
    {"step": 2, "tool": "Grep", "success": true, "output": "..."},
    ...
  ],
  "grader_result": {
    "passed": true,
    "total_checks": 2,
    "passed_checks": 2,
    "failed_checks": 0,
    "tool_calls_verified": true,
    "details": [...]
  }
}
```

---

## 脚本参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `case_file` | 测试用例 JSON 文件路径（必需） | `case.json` |
| `--work-dir` | 工作目录名（默认: phase4_workspace） | `--work-dir my_test` |
| `--output` | 输出结果文件路径 | `--output result.json` |
| `--keep-env` | 保留工作环境（不删除） | `--keep-env` |
| `-v, --verbose` | 详细输出 | `-v` |

**完整示例**：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --keep-env -v
```

---

## 解读结果

### 情况 1：验证通过

```
passed: true
grader_result.all_passed: true
```

**结论**：设计正确，可以进入下一步（Haiku 验证）

**下一步**：
```bash
Read ~/.claude/skills/agent-testcase-generator/verification/haiku_verification.md
```

### 情况 2：Golden Action 失败

```
execution_trajectory 中某步 success: false
```

**常见原因**：
1. **文件路径错误**：引用了不存在的文件
2. **参数错误**：工具参数不完整或不正确
3. **逻辑错误**：步骤之间依赖关系不对

**修复策略**：
- 检查 Golden Action 中的文件路径
- 确保环境中包含所有引用的文件
- 逐步验证每一步的输入输出

### 情况 3：Grader 失败

```
execution_trajectory 全部 success: true
grader_result.passed: false
```

**常见原因**：
1. **Grader 验证条件过严**：期望值与实际值不匹配
2. **Grader 路径错误**：验证了错误的文件
3. **设计问题**：Golden Action 没有达到 Target

**修复策略**：
- 查看 grader_result.details 了解哪个 check 失败
- 检查 Grader 的 params 是否正确
- 确认 Golden Action 最后一步是否真正达到了 Target

### 情况 4：Environment 缺失

```
Step X: File not found: some/path.yaml
```

**原因**：environment 中缺少 Golden Action 引用的文件

**修复策略**：
- 将缺失的文件添加到 environment
- 或修改 Golden Action 不引用该文件

---

## 修复策略

### 可以修改的部分

在自测失败后，你**可以**修改：

1. **Query**
   - 修复歧义
   - 调整模糊度
   - 使目标更明确

2. **Grader**
   - 调整验证条件
   - 放宽过严的检查
   - 允许合理的替代方案

3. **Environment 内容**
   - 修复文件内容中的错误
   - 补充缺失的信息

### 不能修改的部分

**不能**修改：

1. **Environment 结构**
   - 不能删除核心文件
   - 不能大改目录结构
   - 环境已经固定

2. **Golden Action 核心逻辑**
   - 不能改变解题思路
   - 不能减少步骤数（影响难度）
   - 只能修复执行错误

### 修复后重新验证

修复后，重新执行验证：

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

重复此过程，直到验证通过。

---

## 下一步

验证通过后，进入 Haiku 验证：
```bash
Read ~/.claude/skills/agent-testcase-generator/verification/haiku_verification.md
```
