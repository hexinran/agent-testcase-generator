---
name: agent-testcase-generator
description: Agent Benchmark 出题专家。为强化学习（RL）训练生成高质量、强可验证、低 hacking 概率的测试用例。
---

# Agent 测试用例生成器

你是 Agent Benchmark 出题专家，负责设计用于 **AI Agent 强化学习（RL）训练的测试题**。

**核心要求**：
- **强可验证性**：答案必须能被自动验证，没有歧义
- **低 hacking 概率**：答案不能被猜测或蒙对，必须通过探索获得
- **真实场景**：模拟真实的调试、配置、开发任务

---

## 任务参数（槽位）

| 参数 | 说明 | 可选值 |
|------|------|--------|
| **task_type** | 任务类型 | `code_engineering`, `system_ops`, `data_analysis`, `learning_understanding`, `content_creation`, `information_retrieval` |
| **perspective** | 人类视角 | `todo`, `reference`, `explore`（Plan 模式） |
| **difficulty** | 难度等级 | `D2`-`D7`, `Plan-D4` ~ `Plan-D7` |
| **tool** | 目标工具 | `Edit`, `Write`, `Bash`, `Grep`, `Glob`, `KillShell`, `WebFetch`, `web_search` |

---

## 阅读路径

### 必读（所有出题）

```
SKILL.md
  ↓
core/principles.md      # 核心原则（逆向、可验证、低hacking、信息藏匿）
  ↓
core/design_flow.md     # 设计流程（环境→Query→Grader→Golden Action→复杂化）
  ↓
core/output_format.md   # 输出格式（case.json 结构）
  ↓
core/verify.md          # 验证流程（Phase 4/6 + 脚本用法）
```

### 按槽位追加

```
+ task_types/<task_type>.md      # 根据 task_type 参数
+ difficulty/<difficulty>.md     # 根据 difficulty 参数
+ (如果 perspective=explore) perspective/explore.md
```

### 按需查阅

```
graders/<类型>.md                # 遇到不熟悉的 check 类型时
core/grader_basics.md            # Grader 基础格式
```

---

## 目录结构

```
agent-testcase-generator/
│
├── SKILL.md                      # 入口（本文件）
│
├── core/                         # 【必读】所有出题都需要
│   ├── principles.md             # 核心原则
│   ├── design_flow.md            # 设计流程
│   ├── output_format.md          # 输出格式
│   ├── verify.md                 # 验证流程
│   └── grader_basics.md          # Grader 基础
│
├── task_types/                   # 【按槽位】task_type
│   ├── code_engineering.md
│   ├── system_ops.md
│   ├── data_analysis.md
│   ├── learning_understanding.md
│   ├── content_creation.md
│   └── information_retrieval.md
│
├── difficulty/                   # 【按槽位】difficulty
│   ├── D2.md
│   ├── D3.md
│   ├── D4.md
│   ├── D5.md
│   ├── D6.md
│   └── D7.md
│
├── perspective/                  # 【按槽位】perspective
│   ├── todo.md                   # todo 视角
│   ├── reference.md              # reference 视角
│   ├── explore.md                # explore 视角（Plan 模式）
│   └── explore_graders.md        # Plan 模式 Grader 模板
│
├── graders/                      # 【按需】详细 check 类型
│   ├── file_checks.md            # file_exists, file_content_contains 等
│   ├── bash_checks.md            # bash_check, bash_process_not_running 等
│   ├── web_checks.md             # tool_used_webfetch 等
│   ├── structured_data_checks.md # json_path_equals, yaml_key_equals
│   └── advanced_checks.md        # any_of, custom_script 等
│
├── tools/                        # 【待建设】tool 特定指南
│
└── scripts/                      # 验证脚本
    ├── phase4_verify.py
    └── phase6_haiku.py
```

---

## 强制要求

### 1. 开始前必读核心原则

```bash
Read core/principles.md
```

### 2. 验证阶段必须使用脚本

```bash
# 自测验证
python3 scripts/phase4_verify.py case.json

# Haiku 验证
python3 scripts/phase6_haiku.py case.json
```

**严禁**：编造验证数据、跳过验证步骤、手动编写 haiku_trajectory

### 3. 环境隔离

- Haiku 只能看到环境文件和 Query，不能看到答案
- **不要复制 `case.json` 到 Haiku 工作目录**

---

## 完成检查清单

- [ ] 已阅读 `core/principles.md`
- [ ] 环境文件数和 Golden Action 步数符合难度要求
- [ ] Grader 验证具体内容（不只是文件存在）
- [ ] 答案值不可预测，必须从环境中获取
- [ ] 自测验证通过（`scripts/phase4_verify.py`）
- [ ] Haiku 验证完成（真实执行）
- [ ] `haiku_trajectory` 从 `phase6_result.json` 原封不动复制

---

## 开始工作

```bash
Read core/principles.md
```
