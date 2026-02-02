# Agent Testcase Generator

Agent Benchmark 出题专家。为强化学习（RL）训练生成高质量、强可验证、低 hacking 概率的测试用例。

## 简介

这是一个 [Claude Code](https://claude.ai/claude-code) 的 Custom Skill，用于生成 Agent 评测的测试用例。

### 核心特点

- **逆向出题**：从可验证的目标逆向设计，确保题目有效
- **强可验证性**：每个题目都有明确的 Grader 验证逻辑
- **低 hacking 概率**：答案不能被猜测或蒙对，必须通过探索获得
- **多维度覆盖**：6 种任务类型 × 3 种视角 × 6 种难度 × 8 种工具
- **Plan 模式**：支持多文件协调操作的复杂重构场景

## 安装

```bash
# 克隆到本地
git clone https://github.com/hexinran/agent-testcase-generator.git

# 创建 symlink 到 Claude Code skills 目录
ln -sf $(pwd)/agent-testcase-generator ~/.claude/skills/agent-testcase-generator
```

## 使用方法

### 基本调用

```
/agent-testcase-generator

生成一个 Edit 工具的 D4 难度测试用例，场景是数据库连接超时问题
```

### 使用槽位参数

```
使用 agent-testcase-generator 生成测试用例：
- task_type: code_engineering
- perspective: reference
- difficulty: D4
- tool: Edit
- 场景主题: 微服务端口配置错误
```

## 槽位参数

外部程序通过 4 个槽位参数控制测试用例生成：

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `task_type` | 任务类型 | `code_engineering`, `system_ops`, `data_analysis`, `learning_understanding`, `content_creation`, `information_retrieval` |
| `perspective` | 人类视角 | `todo`, `reference`, `explore` |
| `difficulty` | 难度等级 | `D2`-`D7`, `Plan-D4` ~ `Plan-D7` |
| `tool` | 目标工具 | `Edit`, `Write`, `Bash`, `Grep`, `Glob`, `KillShell`, `WebFetch`, `web_search` |

### 任务类型说明

| 类型 | 描述 | 典型场景 |
|-----|------|---------|
| `code_engineering` | 代码工程 | Bug 修复、配置管理、测试执行、代码重构 |
| `system_ops` | 系统运维 | Git 操作、依赖管理、部署配置、进程管理 |
| `data_analysis` | 数据分析 | 日志分析、数据处理、指标聚合 |
| `learning_understanding` | 学习理解 | 架构总结、API 文档、依赖图谱 |
| `content_creation` | 内容创作 | 迁移指南、变更日志、README 更新 |
| `information_retrieval` | 信息检索 | 安全审计、TODO 收集、依赖扫描 |

### 难度等级

**普通模式**：D2-D7

| 等级 | 文件数 | 步数 | 特点 |
|-----|-------|-----|------|
| D2 | 3-5 | 1-2 | 简单直接 |
| D3 | 8-12 | 3-4 | 需要探索 |
| D4 | 12-15 | 5-6 | 有干扰项 |
| D5 | 15-20 | 7-8 | 复杂依赖 |
| D6 | 20-25 | 9-10 | 深度推理 |
| D7 | 25-35 | 11-15 | 极限挑战 |

**Plan 模式**：Plan-D4 ~ Plan-D7（多文件协调操作）

## 目录结构

```
agent-testcase-generator/
├── SKILL.md                      # Skill 入口文件
│
├── core/                         # 【必读】核心文档
│   ├── principles.md             # 核心设计原则
│   ├── design_flow.md            # 测试用例设计流程
│   ├── output_format.md          # 输出格式规范
│   ├── verify.md                 # 验证流程
│   └── grader_basics.md          # Grader 基础格式
│
├── task_types/                   # 【按槽位】任务类型
│   ├── code_engineering.md
│   ├── system_ops.md
│   ├── data_analysis.md
│   ├── learning_understanding.md
│   ├── content_creation.md
│   └── information_retrieval.md
│
├── difficulty/                   # 【按槽位】难度等级
│   ├── D2.md ~ D7.md
│
├── perspective/                  # 【按槽位】视角
│   ├── todo.md                   # todo 视角
│   ├── reference.md              # reference 视角
│   ├── explore.md                # explore 视角（Plan 模式）
│   └── explore_graders.md        # Plan 模式 Grader 模板
│
├── graders/                      # 【按需】Grader Check 类型
│   ├── file_checks.md            # 文件检查
│   ├── bash_checks.md            # Bash/进程检查
│   ├── web_checks.md             # Web 工具检查
│   ├── structured_data_checks.md # JSON/YAML 检查
│   └── advanced_checks.md        # 高级检查
│
├── tools/                        # 【待建设】工具特定指南
│
├── reference/                    # 参考文档
│   ├── examples.md               # 示例用例
│   ├── script_usage.md           # 脚本使用说明
│   └── plan_mode_examples.md     # Plan 模式完整示例
│
├── scripts/                      # 验证脚本
│   ├── custom_checks.py          # 自定义检查实现
│   ├── phase4_verify.py          # Phase 4 自测验证
│   └── phase6_haiku.py           # Phase 6 Haiku 验证
│
└── verification/                 # 验证文档
    ├── haiku_verification.md
    └── self_test.md
```

## 阅读路径

### 必读（所有出题）

```
SKILL.md → core/principles.md → core/design_flow.md → core/output_format.md → core/verify.md
```

### 按槽位追加

```
+ task_types/<task_type>.md
+ difficulty/<difficulty>.md
+ (如果 perspective=explore) perspective/explore.md
```

### 按需查阅

```
graders/<类型>.md    # 遇到不熟悉的 check 类型时
```

## License

MIT
