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
  "init_commands": [...],  // 可选
  "reference_solution": [...],
  "graders": [...]
}
```

### Step 2: 执行验证脚本

使用绝对路径调用验证脚本：

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

**脚本会自动**：
1. 读取 case.json
2. 在工作目录的一个隔离子目录中创建环境
3. 执行 init_commands（如果有）
4. 逐步执行 reference_solution 中的每一步
5. 验证所有 graders
6. 输出详细结果

### Step 3: 查看结果

脚本会输出到终端，并保存到工作目录的 `phase4_result.json`。

**成功示例**：
```
=== Phase 4 验证开始 ===
创建验证环境: /tmp/workspace/phase4_verify_abc123/
执行环境初始化...
执行 Golden Action...
  Step 1/4: Read logs/error.log ✓
  Step 2/4: Grep timeout ✓
  Step 3/4: Read docs/incident-2847.md ✓
  Step 4/4: Edit config/database.yaml ✓
验证 Graders...
  state_check: 3/3 通过 ✓
  tool_calls: 1/1 通过 ✓
=== Phase 4 验证通过 ===
```

**失败示例**：
```
=== Phase 4 验证开始 ===
...
执行 Golden Action...
  Step 1/4: Read logs/error.log ✓
  Step 2/4: Grep timeout ✗
    错误: 文件不存在: config/database.yaml
=== Phase 4 验证失败 ===
```

### Step 4: 读取详细结果

```bash
Read phase4_result.json
```

**结果结构**：
```json
{
  "passed": true,
  "golden_action_result": {
    "all_steps_passed": true,
    "steps": [
      {"step": 1, "tool": "Read", "passed": true, "error": null},
      {"step": 2, "tool": "Grep", "passed": true, "error": null},
      ...
    ]
  },
  "grader_result": {
    "all_passed": true,
    "state_check": {"passed": 3, "total": 3},
    "tool_calls": {"passed": 1, "total": 1},
    "details": [...]
  }
}
```

---

## 解读结果

### 情况 1：验证通过

```
passed: true
golden_action_result.all_steps_passed: true
grader_result.all_passed: true
```

**结论**：设计正确，可以进入下一步（Haiku 验证）

**下一步**：
```bash
Read ~/.claude/skills/agent-testcase-generator/verification/haiku_verification.md
```

### 情况 2：Golden Action 失败

```
golden_action_result.all_steps_passed: false
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
golden_action_result.all_steps_passed: true
grader_result.all_passed: false
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
错误: 文件不存在: logs/error.log
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

修复后，重新执行 Step 2：

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

重复此过程，直到验证通过。

---

## 常见问题

### Q1: 脚本报错"找不到 case.json"

**原因**：case.json 不在当前工作目录

**解决**：确认 case.json 保存在工作目录根，或使用绝对路径：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py /tmp/workspace/case.json
```

### Q2: Golden Action 某一步失败

**解决步骤**：
1. 查看失败步骤的 error 信息
2. 检查该步骤的 input 参数
3. 确认环境中包含相关文件
4. 手动执行该步骤测试（使用对应工具）

### Q3: Grader check 一直失败

**解决步骤**：
1. 查看 grader_result.details 中的失败原因
2. 手动检查文件内容是否符合预期
3. 确认 keyword 或 pattern 是否正确
4. 考虑是否需要调整 Grader 验证条件

### Q4: Environment 创建失败

**原因**：environment 中有非法的文件路径或内容

**解决**：
- 检查路径中是否有特殊字符
- 确认 content 字段格式正确（使用 \n 表示换行）
- 确认 executable 字段是布尔值

---

## 脚本详细参数

phase4_verify.py 支持以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `case_json_path` | 测试用例 JSON 文件路径（必需） | `case.json` 或绝对路径 |
| `-v, --verbose` | 详细输出模式 | `--verbose` |
| `--keep-env` | 保留验证环境（不删除） | `--keep-env` |

**完整示例**：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --verbose --keep-env
```

**详细参数说明**：
```bash
Read ~/.claude/skills/agent-testcase-generator/reference/script_usage.md
```

---

## 下一步

验证通过后，进入 Haiku 验证：
```bash
Read ~/.claude/skills/agent-testcase-generator/verification/haiku_verification.md
```
