# 测试用例完整设计流程

本文档指导你完成测试用例的完整设计，包括环境构建、Query/Target/Grader/Golden Action 设计和信息复杂化。

**前置要求**：已阅读 `design/core_principles.md` 并理解核心原则。

---

## 工作目录说明

你的工作目录已预设（通常是 `/tmp/workspace`），初始为空。

**直接在工作目录中创建环境文件**，不需要创建额外的目录结构。

示例：
```bash
# 创建配置文件
Write(file_path="config/database.yaml", content="...")

# 创建日志文件
Write(file_path="logs/error.log", content="...")

# 创建文档
Write(file_path="docs/architecture.md", content="...")
```

---

## Part 1: 环境构建

### 目标

创建符合真实项目的目录结构和文件，为测试题提供探索的"世界"。

### 获取参考项目（推荐，D5+ 必须）

真实的项目结构让测试题更有说服力。

**搜索参考项目**：

根据场景主题搜索相关项目：
- 中文项目/技术：使用 `mcp__baidu-server__web_search`
- 英文项目/技术：使用 `mcp__google-server__web_search`

**获取项目结构**（可选）：
```bash
# Clone 到临时目录参考
git clone --depth 1 <repo_url> /tmp/ref_project

# 参考目录结构后删除
rm -rf /tmp/ref_project
```

### 目录结构设计

**必须有的目录**（根据项目类型选择）：

| 项目类型 | 典型目录结构 |
|---------|-------------|
| 微服务 | `services/`, `config/`, `deploy/`, `docs/`, `logs/` |
| 前端项目 | `src/`, `config/`, `public/`, `docs/`, `scripts/` |
| 数据平台 | `pipelines/`, `config/`, `data/`, `logs/`, `docs/` |
| DevOps | `deploy/`, `scripts/`, `config/`, `monitoring/`, `docs/` |

**关键原则**：
- ✅ 真实的项目结构（不要只有 config 和 logs）
- ✅ 合理的文件命名（不要 file1.txt, file2.txt）
- ✅ 符合行业惯例（Python 项目有 requirements.txt，Node 项目有 package.json）

### 文件数量要求

根据难度创建足够数量的文件，详见 `~/.claude/skills/agent-testcase-generator/reference/difficulty_guide.md`

**简要参考**：D2: 3-5个, D3: 8-12个, D4: 12-15个, D5: 15-20个, D6: 20-25个, D7: 25-35个

### environment 字段格式

```json
{
  "path": "config/database.yaml",
  "content": "host: localhost\nport: 5432\ntimeout: 5000",
  "executable": false
}
```

**字段说明**：
- `path`: 文件相对路径（相对于工作目录）
- `content`: 文件内容（使用 `\n` 表示换行）
- `executable`: 是否可执行（脚本文件设置为 `true`）

### init_commands（可选）

用于初始化命令，如启动后台进程（KillShell 场景必须）。

```json
{
  "init_commands": [
    {
      "command": "nohup python3 services/worker.py > logs/worker.log 2>&1 & echo $! > logs/worker.pid",
      "description": "启动后台 Worker 进程",
      "wait_sec": 2
    }
  ]
}
```

**字段说明**：
- `command`: 要执行的命令（在工作目录中执行）
- `description`: 命令描述（用于日志）
- `wait_sec`: 执行后等待秒数（让进程启动完成）

**使用场景**：
- 启动后台服务（配合 KillShell 验证清理能力）
- 生成初始数据文件
- 设置复杂的初始状态

### 环境构建检查清单

完成环境构建后确认：

- [ ] 文件数量符合难度要求
- [ ] 有真实的项目结构（不只是 config 和 logs）
- [ ] 文件命名合理（不是 file1.txt, file2.txt）
- [ ] 核心文件内容完整（不是占位符）
- [ ] 环境符合项目类型惯例

**重要**：环境一旦确定就固定，后续只能微调内容，不能大改结构。

---

## Part 2: Query 和 Target 设计

### Target（目标状态）

**定义**：用户完成任务后的预期状态，必须是具体、可验证的。

**示例**：
```
✅ 好的 Target:
- config/database.yaml 中包含 "port: 19847"
- output/report.json 文件存在且包含 "status: success"
- services/worker.py 进程已停止

❌ 坏的 Target:
- "系统正常运行"（太模糊）
- "配置正确"（不具体）
- "问题已解决"（无法验证）
```

### Query（问题描述）

**定义**：用户看到的任务描述，控制信息披露程度。

**设计原则**：

1. **探索距离原则**
   - 重点是**探索距离**（需要经过多少步找到答案）
   - 不是简单的"不能说什么"

2. **给探索方向，不给答案**
   - ✅ 告诉：需要修复什么**问题**
   - ❌ 告诉：修改哪个**文件**、改什么**值**

### 针对不同工具的 Query 设计

#### Edit 工具

| 应该告诉 | 不应该告诉 | 示例 |
|---------|-----------|------|
| 需要修复什么问题 | 具体修改哪个文件 | "订单服务连接数据库超时，请排查配置问题" |
| 问题的表现 | 改什么值 | "支付网关响应慢，用户反馈超时" |
| 影响范围 | 具体的配置项名称 | "生产环境所有微服务无法连接消息队列" |

**好的 Query 示例**：
```
"订单服务在生产环境无法连接数据库，错误日志显示连接超时。
请根据最近的架构调整文档排查并修复配置问题。"
```

#### Bash 工具

| 应该告诉 | 不应该告诉 | 示例 |
|---------|-----------|------|
| 需要执行什么类型的操作 | 具体脚本名称 | "请执行 scripts 目录下的构建脚本生成生产环境产物" |
| 操作的目标 | 具体命令 | "请执行测试并生成覆盖率报告" |

**好的 Query 示例**：
```
"请执行 scripts 目录下的构建脚本，生成生产环境构建产物。
产物应该包含编译后的代码和配置文件。"
```

**为什么 Bash 必须暗示"执行脚本"**：
- Edit/Write：用户天然知道要操作文件
- Bash：用户需要知道"要执行脚本/命令"，否则弱模型会陷入无限探索
- 对于 Bash 类题目，Query 必须暗示"需要执行某个脚本"

#### Write 工具

| 应该告诉 | 不应该告诉 | 示例 |
|---------|-----------|------|
| 需要生成什么文件 | 具体内容模板 | "请生成包含所有 TODO 项的审计报告" |
| 内容约束和格式 | 具体的字段和值 | "报告必须包含文件路径、行号、TODO 内容" |

#### Grep 工具

| 应该告诉 | 不应该告诉 | 示例 |
|---------|-----------|------|
| 需要搜索什么信息 | 具体搜索命令 | "找出项目中所有硬编码的 API 密钥" |
| 搜索的目的 | grep 的参数 | "扫描代码中的敏感信息并生成安全审计报告" |

### Query 模糊度与难度

| 难度 | Query 特点 | 示例 |
|------|-----------|------|
| D2-D3 | 直接告诉目标，路径需探索 | "config/database.yaml 中端口配置错误，请修复" |
| D4-D5 | 描述现象，需分析推断 | "订单服务数据库连接超时，请排查配置问题" |
| D6-D7 | 模糊描述，需多处拼凑 | "生产环境订单系统出现间歇性故障，请根据监控和日志排查" |

---

## Part 3: Grader 设计

### Grader 结构

Grader 由两部分组成：

1. **state_check**：检查任务执行后的系统状态
2. **tool_calls**：验证是否使用了特定工具

```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_contains",
          "params": {"path": "config.yaml", "keyword": "port: 19847"},
          "description": "验证端口配置已修复为正确值"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改配置"}
      ]
    }
  ]
}
```

### 常用 Check 类型

#### 文件检查

| Check 类型 | 用途 | 示例 |
|-----------|------|------|
| `file_exists` | 验证文件存在 | 验证生成了报告文件 |
| `file_not_exists` | 验证文件不存在 | 验证删除了临时文件 |
| `file_content_contains` | 验证文件包含关键词 | 验证配置项的值 |
| `file_content_not_contains` | 验证文件不包含关键词 | 验证删除了错误配置 |
| `file_content_match` | 验证文件内容匹配正则 | 验证格式正确性 |

#### 命令检查

| Check 类型 | 用途 | 示例 |
|-----------|------|------|
| `bash_check` | 执行命令检查输出 | 验证服务状态 |
| `bash_exit_code` | 检查命令退出码 | 验证脚本执行成功 |
| `bash_process_running` | 检查进程运行 | 验证服务已启动 |
| `bash_process_not_running` | 检查进程已停止 | 验证进程已清理 |

#### Web 工具检查

| Check 类型 | 用途 |
|-----------|------|
| `tool_used_webfetch` | 验证使用了 WebFetch |
| `tool_used_web_search` | 验证使用了 web_search |

### Grader 设计原则

#### 原则 1：至少 2-4 个验证点

**❌ 单一验证点**：
```json
{
  "checks": [
    {"check": "file_exists", "params": {"path": "config.yaml"}}
  ]
}
```
问题：只验证文件存在，无法确保内容正确

**✅ 多个验证点**：
```json
{
  "checks": [
    {"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "host: db-prod-03.internal"}},
    {"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port: 19847"}},
    {"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "timeout: 47000"}},
    {"check": "file_content_not_contains", "params": {"path": "config.yaml", "keyword": "timeout: 5000"}}
  ]
}
```

#### 原则 2：验证具体内容，不只是文件存在

**❌ 只验证存在**：
```json
{"check": "file_exists", "params": {"path": "report.json"}}
```

**✅ 验证具体内容**：
```json
[
  {"check": "file_exists", "params": {"path": "report.json"}},
  {"check": "file_content_contains", "params": {"path": "report.json", "keyword": "\"status\": \"completed\""}},
  {"check": "file_content_contains", "params": {"path": "report.json", "keyword": "\"total_issues\": 3"}}
]
```

#### 原则 3：防止答案被猜测

Grader 必须验证具体的答案值。

**❌ 可以被猜测**：
```json
{"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port:"}}
```
问题：任何端口都能通过

**✅ 验证具体值**：
```json
{"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port: 19847"}}
```

### KillShell 场景特殊要求

KillShell 场景必须：
1. 使用 `init_commands` 预先启动后台进程
2. Grader 必须包含至少 2 个 state_check 静态验证：
   - 主验证：`bash_process_not_running`（验证进程已停止）
   - 辅助验证：`file_not_exists`（验证 PID 文件清理）或其他

**示例**：
```json
{
  "init_commands": [
    {
      "command": "nohup bash services/legacy_sync.sh > logs/legacy_sync.log 2>&1 & echo $! > logs/legacy_sync.pid",
      "description": "启动 legacy_sync 后台进程",
      "wait_sec": 2
    }
  ],
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "bash_process_not_running",
          "params": {"process_name": "legacy_sync"},
          "description": "验证 legacy_sync 进程已停止"
        },
        {
          "check": "file_not_exists",
          "params": {"path": "logs/legacy_sync.pid"},
          "description": "验证 PID 文件已清理"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [{"tool": "KillShell", "description": "必须使用 KillShell 工具"}]
    }
  ]
}
```

### Grader 完整规范

详细的 check 类型、参数说明、实现模板见：
```bash
Read ~/.claude/skills/agent-testcase-generator/reference/grader_spec.md
```

---

## Part 4: Golden Action 设计

### 定义

**Golden Action**（参考解答）：从 Query 到 Target 的最优路径。

### 结构

```json
{
  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "logs/error.log"},
      "reasoning": "查看错误日志，定位问题"
    },
    {
      "tool": "Grep",
      "input": {"pattern": "timeout", "output_mode": "files_with_matches"},
      "reasoning": "搜索超时相关配置文件"
    },
    {
      "tool": "Read",
      "input": {"file_path": "docs/incident-2847.md"},
      "reasoning": "查看故障单，找到推荐配置"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "config/database.yaml",
        "old_string": "timeout: 5000",
        "new_string": "timeout: 47000"
      },
      "reasoning": "根据故障单建议修复超时配置"
    }
  ]
}
```

### 设计原则

#### 原则 1：长度符合难度要求

详见 `~/.claude/skills/agent-testcase-generator/reference/difficulty_guide.md`

**简要参考**：D2: 1-2步, D3: 3-4步, D4: 5-6步, D5: 7-8步, D6: 9-10步, D7: 11-15步

#### 原则 2：最后一步必须使用目标工具

如果目标工具是 Edit，最后一步必须是 Edit：
```json
[
  {"tool": "Read", ...},
  {"tool": "Grep", ...},
  {"tool": "Read", ...},
  {"tool": "Edit", ...}  // 最后一步
]
```

#### 原则 3：包含探索阶段 + 行动阶段

- **探索阶段**：Read、Grep、Glob、WebFetch 等（收集信息）
- **行动阶段**：Edit、Write、Bash、KillShell 等（执行操作）

**好的结构**：
```
Read → Grep → Read → Read → Edit
(探索)                    (行动)
```

#### 原则 4：每一步都可执行

Golden Action 必须在 Phase 4 验证时能够真实执行。

- ✅ input 参数完整且正确
- ✅ 文件路径存在
- ✅ 每一步的输出能支撑下一步

---

## Part 5: 信息复杂化

### 目标

通过信息藏匿增加探索距离，直到满足难度要求。

### 策略 1：分散关键信息

将问题线索、背景知识、解决方案分散在多个文件中。

**D4 示例**（5 步 Golden Action）：
```
1. Read logs/error.log → 发现 "connection timeout"
2. Grep "timeout" → 找到相关配置文件
3. Read docs/incident-2847.md → 找到推荐超时值
4. Read config/database.yaml → 看当前配置
5. Edit config/database.yaml → 修复
```

信息分散在：logs/ → config/ → docs/ 三个位置

### 策略 2：添加干扰文件

**旧版本文件**：
```
config/database.yaml          # 当前使用
config/database.yaml.bak      # 备份
config/database.yaml.old      # 旧版本
```

**其他环境**：
```
config/production.yaml        # 生产环境（正确）
config/staging.yaml           # 预发环境
config/development.yaml       # 开发环境
```

**相似命名**：
```
services/order-service/config.yaml      # 正确
services/order-processor/config.yaml    # 干扰
services/order-validator/config.yaml    # 干扰
```

### 策略 3：设置红鲱鱼

创建 2-3 个看起来可能有问题的地方，但只有一个是真正根因。

**示例**：
```
环境中有 3 个可疑点：
1. logs/gateway.log: "rate limit exceeded"（红鲱鱼）
2. logs/database.log: "slow query detected"（红鲱鱼）
3. config/payment-service.yaml: timeout: 5000（真正根因）

只有修复第 3 个才能通过 Grader
```

### 策略 4：隐藏答案

**❌ 日志直接给答案**：
```
logs/error.log:
  "Port 5432 failed, please change to 19847"
```

**✅ 只给线索**：
```
logs/error.log:
  "Connection refused on port 5432"

docs/incident-2847.md:
  "数据库已迁移，详见服务发现配置"

config/service-discovery.yaml:
  "database: db-prod-03.internal:19847"
```

### 同步调整 Query

在复杂化过程中，可以调整 Query 来匹配探索距离：
- 增加模糊性
- 减少直接提示
- 但必须保持可验证性

**示例**：

初版 Query：
```
"config/database.yaml 中端口配置错误，请修复"
```

复杂化后 Query：
```
"生产环境订单服务数据库连接失败，错误日志显示连接超时。
请根据最近的故障单和架构调整文档排查并修复。"
```

### 检查清单

完成信息复杂化后确认：

- [ ] Golden Action 长度符合难度要求
- [ ] 环境文件数符合难度要求
- [ ] 关键信息分散在 3+ 个文件中（D4+）
- [ ] 有足够的干扰文件（D4+）
- [ ] 答案值不可预测（从环境获取）
- [ ] Query 模糊度与难度匹配

### 不能做的事

- ❌ 删除 Phase 1 创建的核心文件
- ❌ 大改目录结构
- ❌ 创建逻辑矛盾的线索
- ❌ 藏得太深导致无解

---

## 完成设计

完成设计后，你应该有：

1. ✅ 完整的环境文件列表（environment）
2. ✅ 初始化命令（init_commands，如果需要）
3. ✅ Query 和 Target
4. ✅ Graders（2-4 个验证点）
5. ✅ Golden Action（符合难度要求）

将这些保存为 `case.json` 到工作目录。

**输出格式详解**：
```bash
Read ~/.claude/skills/agent-testcase-generator/reference/output_format.md
```

---

## 下一步

设计完成后，进入验证阶段：
```bash
Read ~/.claude/skills/agent-testcase-generator/verification/workflow.md
```
