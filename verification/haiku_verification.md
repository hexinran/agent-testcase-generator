# Haiku 验证流程

本文档指导你使用 Haiku 模型验证测试题的合理性。

---

## 目的

**Haiku 验证**：用较弱的模型测试题目是否合理。

**核心原则**：
- Haiku 只能看到 **Query** 和 **环境文件**
- Haiku **不能看到** 答案（reference_solution 和 graders）
- Haiku 自己探索和解题
- 通过 Haiku 的表现判断题目难度是否合理

---

## 脚本工作原理

`phase6_haiku.py` 脚本会自动完成以下步骤：

```
/tmp/workspace/              # 出题 CC 工作目录
├── case.json                # 包含答案，Haiku 看不到
├── phase6_result.json       # 验证结果（脚本生成）
│
└── haiku_space/             # 脚本创建的隔离目录
    ├── config/              # 根据 environment 创建
    ├── logs/
    ├── services/
    └── (Haiku 在这里工作)
```

**关键隔离机制**：
1. 脚本从 `case.json` 读取 environment 和 init_commands
2. 在 `haiku_space/` 中创建环境文件
3. **执行 init_commands**（KillShell 场景必需！）
4. **cd 到 `haiku_space/` 后调用 Haiku CLI**
5. Haiku 的工作目录是 `haiku_space/`，看不到外面的 `case.json`
6. 验证 graders 并保存结果

---

## 执行步骤

### Step 1: 确保 case.json 已保存

确保测试用例已保存为 `case.json`：

```json
{
  "task": {"id": "...", "desc": "..."},
  "environment": [...],
  "init_commands": [...],  // KillShell 场景必须
  "reference_solution": [...],
  "graders": [...]
}
```

### Step 2: 执行 Haiku 验证脚本

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json
```

**脚本会自动**：
1. 创建 `haiku_space/` 目录
2. 根据 `environment` 创建文件
3. 执行 `init_commands`（启动后台进程等）
4. cd 到 `haiku_space/`，调用 Haiku CLI
5. 捕获 Haiku 的工具调用轨迹
6. 验证 graders
7. 保存结果到 `phase6_result.json`

**执行时间**：通常需要 30-120 秒，取决于题目复杂度。

### Step 3: 查看输出

脚本会输出实时进度：

```
============================================================
Phase 6: Haiku 验证
============================================================
Case ID: KillShell_D4_20260126
Query: 系统中存在一个占用资源的后台同步进程，请找到并停止它...
Working directory: /tmp/workspace
Haiku directory: /tmp/workspace/haiku_space

--- Setting up Haiku environment ---
  Created 8 environment files
  Executing 1 init commands...
    - 启动 legacy_sync 后台进程

--- Running Haiku validation ---
This may take a few minutes...
Execution completed in 45.2s
Total steps: 6

--- Verifying Graders ---
  ✓ [bash_process_not_running] Process legacy_sync not running
  ✓ [file_not_exists] File logs/legacy_sync.pid does not exist

--- Tool Calls ---
  ✓ KillShell: 必须使用 KillShell 工具

============================================================
✓ Phase 6 PASSED - Haiku completed the task
  Checks: 2/2 passed
  Haiku steps: 6
  Duration: 45.2s
============================================================

Result saved to: /tmp/workspace/phase6_result.json
```

### Step 4: 读取验证结果

```bash
Read phase6_result.json
```

**结果结构**：
```json
{
  "phase": 6,
  "case_id": "KillShell_D4_20260126",
  "timestamp": "2026-01-26T15:30:00",
  "haiku_execution": {
    "success": true,
    "total_steps": 6,
    "duration_sec": 45.2,
    "trajectory": [
      {"step": 1, "tool": "Glob", "input": {...}, "output": "..."},
      {"step": 2, "tool": "Read", "input": {...}, "output": "..."},
      ...
    ]
  },
  "grader_result": {
    "passed": true,
    "total_checks": 2,
    "passed_checks": 2,
    "failed_checks": 0,
    "tool_calls_verified": true
  },
  "haiku_evaluation": {
    "passed": true,
    "haiku_steps": 6,
    "duration_sec": 45.2,
    "passed_checks": 2,
    "total_checks": 2
  }
}
```

### Step 5: 提取轨迹数据

**🚨 强制要求**：必须原封不动复制 `haiku_trajectory`

从 `phase6_result.json` 提取以下字段，复制到最终的 `case.json`：

1. **haiku_evaluation**
2. **haiku_trajectory**（从 `haiku_execution.trajectory` 复制）

**⚠️ 严禁**：
- ❌ 编造轨迹数据
- ❌ 总结或改写 output
- ❌ 添加 reasoning 字段
- ❌ 简化或省略任何步骤

---

## 脚本参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `case_file` | 测试用例 JSON 文件路径（必需） | `case.json` |
| `--haiku-dir` | Haiku 工作目录名（默认: haiku_space） | `--haiku-dir my_haiku` |
| `--timeout` | Haiku 执行超时秒数（默认: 600） | `--timeout 300` |
| `--output` | 输出结果文件路径 | `--output result.json` |
| `-v, --verbose` | 详细输出 | `-v` |

**完整示例**：
```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --timeout 300 -v
```

---

## KillShell 场景特别说明

KillShell 场景需要 `init_commands` 来启动后台进程：

```json
{
  "init_commands": [
    {
      "command": "nohup bash services/legacy_sync.sh > logs/legacy_sync.log 2>&1 & echo $! > logs/legacy_sync.pid",
      "description": "启动 legacy_sync 后台进程",
      "wait_sec": 2
    }
  ]
}
```

脚本会在 `haiku_space/` 中自动执行这些命令，确保：
1. 后台进程在 Haiku 开始工作前已启动
2. Haiku 可以找到并停止该进程
3. Grader 可以验证进程已停止

---

## 分析结果

### 情况 1：Haiku 通过，步数合理

```
passed: true
haiku_steps: 5（接近 Golden Action 的 5 步）
```

**结论**：题目合理，难度适中

### 情况 2：Haiku 通过，步数太少

```
passed: true
haiku_steps: 2（Golden Action 是 5 步）
```

**原因**：题目太简单，信息不够分散

**回炉策略**：
- 增加信息分散度
- 添加更多干扰文件
- 调整 Query 模糊度

### 情况 3：Haiku 失败，环境/Query 问题

**判断是否是出题问题**：
- Query 是否有歧义？
- 环境中是否缺少关键线索？
- Grader 是否过严？

**回炉策略**：
- 修复 Query 歧义
- 补充环境线索
- 调整 Grader 验证条件

### 情况 4：Haiku 失败，能力不足

**结论**：对于 D5+ 题目，这是可接受的

---

## 常见问题

### Q1: init_commands 没有执行？

检查 `case.json` 中 `init_commands` 格式是否正确：

```json
{
  "init_commands": [
    {
      "command": "...",
      "description": "...",
      "wait_sec": 2
    }
  ]
}
```

### Q2: Haiku 看到了 case.json？

不可能。脚本将 Haiku 的工作目录设置为 `haiku_space/`，该目录中不包含 `case.json`。

### Q3: 进程没有启动成功？

检查脚本输出中的 Warning 信息。常见原因：
- 脚本文件不存在
- 脚本没有执行权限（需要 `executable: true`）
- `wait_sec` 设置太短

### Q4: Haiku 超时？

增加超时时间：
```bash
python3 phase6_haiku.py case.json --timeout 900
```

---

## 下一步

完成 Haiku 验证后：

1. 将 `haiku_evaluation` 和 `haiku_trajectory` 添加到 case.json
2. 添加 `quality_analysis`（可使用 phase7_quality.py）
3. 保存最终的 case.json

**输出格式详解**：
```bash
Read ~/.claude/skills/agent-testcase-generator/reference/output_format.md
```
