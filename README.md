# Agent Testcase Generator

Agent Benchmark 出题专家。为强化学习（RL）训练生成高质量、强可验证、低 hacking 概率的测试用例。

## 简介

这是一个 [Claude Code](https://claude.ai/claude-code) 的 Custom Skill，用于生成 Agent 评测的测试用例。

### 核心特点

- **逆向出题**：从可验证的目标逆向设计，确保题目有效
- **强可验证性**：每个题目都有明确的 Grader 验证逻辑
- **低 hacking 概率**：答案不能被猜测或蒙对，必须通过探索获得
- **难度分级**：支持 D2-D7 难度，覆盖不同复杂度场景

## 安装

```bash
# 克隆到本地
git clone https://github.com/hexinran/agent-testcase-generator.git

# 创建 symlink 到 Claude Code skills 目录
ln -sf $(pwd)/agent-testcase-generator ~/.claude/skills/agent-testcase-generator
```

## 使用方法

在 Claude Code 中调用：

```
/agent-testcase-generator

生成一个 Edit 工具的 D4 难度测试用例，场景是数据库连接超时问题
```

## 目录结构

```
agent-testcase-generator/
├── SKILL.md                 # Skill 入口文件
├── design/                  # 设计原则文档
│   ├── core_principles.md   # 核心设计原则
│   └── testcase_design.md   # 测试用例设计流程
├── reference/               # 参考文档
│   ├── difficulty_guide.md  # 难度分级指南
│   ├── examples.md          # 示例用例
│   ├── grader_spec.md       # Grader 格式规范
│   ├── output_format.md     # 输出格式规范
│   └── script_usage.md      # 脚本使用说明
├── scripts/                 # 验证脚本
│   ├── custom_checks.py     # 自定义检查实现
│   ├── phase4_verify.py     # Phase 4 自测验证
│   ├── phase6_haiku.py      # Phase 6 Haiku 验证
│   └── phase7_quality.py    # Phase 7 质量检查
└── verification/            # 验证流程文档
    ├── haiku_verification.md
    └── self_test.md
```

## 支持的工具类型

| 工具 | 描述 | 难度范围 |
|------|------|----------|
| Edit | 修改配置文件 | D2-D7 |
| Bash | 执行脚本命令 | D3-D7 |
| Write | 创建新文件 | D3-D6 |
| Grep | 搜索代码/日志 | D2-D5 |
| Glob | 文件模式匹配 | D2-D4 |
| KillShell | 进程管理 | D4-D6 |
| WebFetch | 获取网页信息 | D4-D6 |

## License

MIT
