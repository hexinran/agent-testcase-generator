# 核心设计原则

本文档阐述 Agent 测试用例设计的核心原则。这些原则是所有高质量测试题的基础，必须在开始设计前完全理解。

---

## 1. 逆向出题方法论

### 核心思想

从可验证的**终点**逆向构建，而不是从问题正向推导。

**传统出题（正向）**：
```
问题描述 → 期望解法 → 验证方式
```
问题：验证往往是事后补充，容易有漏洞。

**逆向出题（推荐）**：
```
可验证的目标状态 → 验证逻辑(Grader) → 问题描述(Query) → 参考解法
```

### 逆向出题的步骤

1. **确定 Target（目标状态）**
   - 必须是具体的、可验证的状态
   - 例如："config/database.yaml 中 port: 19847"

2. **设计 Grader（验证逻辑）**
   - 设计 2-4 个验证点
   - 确保可以准确判断任务完成

3. **设计 Query（问题描述）**
   - 根据 Target 反推用户应该看到的问题
   - 控制信息披露程度

4. **设计 Golden Action（参考解法）**
   - 从 Query 到 Target 的最优路径
   - 确保路径可行

### 为什么要逆向？

- ✅ 确保可验证性（目标明确）
- ✅ 减少歧义（Grader 先设计好）
- ✅ 避免无效题目（Target 不可达）

---

## 2. 可验证性优先

### 核心原则

答案必须有明确的验证点。如果答案很开放，必须通过约束使其可验证。

### 示例对比

**❌ 坏例子：开放式任务**
```
Query: "请分析系统性能问题并生成报告"
Target: "生成性能分析报告"
问题：报告内容是开放的，无法验证对错
```

**✅ 好例子：添加约束**
```
Query: "请分析系统性能问题并生成报告。报告必须保存为 analysis.log，
      包含以下内容：CPU 使用率、内存使用率、瓶颈分析"
Target: "analysis.log 存在，且包含 CPU/内存/瓶颈 三个关键词"
Grader:
  - file_exists: analysis.log
  - file_content_contains: "CPU"
  - file_content_contains: "内存"
  - file_content_contains: "瓶颈"
```

### 约束的来源

约束可以在以下位置给出：

1. **Query 中明确说明**
   - "请将结果保存为 output.json"
   - "配置文件必须符合 YAML 格式"

2. **环境中的规范文档**
   - README.md 说明输出文件命名规范
   - docs/guidelines.md 说明代码风格要求

3. **既有的项目约定**
   - 日志统一放在 logs/ 目录
   - 配置文件统一使用 .yaml 后缀

### 不同工具类型的可验证性

| 工具 | 验证方式 | 示例 |
|------|---------|------|
| Edit | file_content_contains | 验证配置项的具体值 |
| Write | file_exists + file_content_contains | 验证文件存在且内容正确 |
| Bash | file_exists / bash_check | 验证脚本生成的输出文件 |
| Grep | file_content_contains | 验证搜索结果已写入文件 |
| KillShell | bash_process_not_running | 验证进程已停止 |
| WebFetch | tool_used_webfetch + file_content_contains | 验证获取了信息并使用 |

---

## 3. 低 Hacking 概率

### 核心原则

**答案值必须从环境中获取，不能被预测或猜测。**

### 什么是 Hacking？

Agent 不通过正确的探索路径，而是通过猜测、常识或模式识别直接得到答案。

### 示例对比

**❌ 高 Hacking 风险**

```
场景：端口配置错误
环境：config/database.yaml 中 port: 5432
Query: "数据库连接失败，请修复端口配置"
Target: port: 5433

问题：5432 → 5433 是最常见的递增，容易猜对
Hacking 成功率：~60%
```

**✅ 低 Hacking 风险**

```
场景：端口配置错误
环境：
  - config/database.yaml 中 port: 5432
  - docs/incident-2847.md 说明："根据运维团队建议，数据库端口应改为 19847"
  - logs/deployment.log 中提到 "port conflict on 5432"

Query: "生产环境数据库连接失败，根据最近的故障单排查并修复"
Target: port: 19847

正确路径：
  1. 读取 logs/deployment.log，发现端口冲突
  2. 搜索相关故障单
  3. 读取 docs/incident-2847.md，找到推荐端口 19847
  4. 修改 config/database.yaml

Hacking 成功率：<5%（无法猜测 19847）
```

### 如何设计不可预测的答案？

#### 策略 1：使用非常规值

- ❌ 5432 → 5433（递增）
- ❌ v1 → v2（版本号递增）
- ❌ /api/v1 → /api/v2（路径递增）
- ✅ 5432 → 19847（从文档获取）
- ✅ /api/v1 → /internal/svc-auth/v2（从架构文档获取）
- ✅ timeout: 30 → timeout: 47（从性能测试报告获取）

#### 策略 2：答案值与文档关联

将答案值与环境中的某个文档/Ticket ID 关联：

```
docs/JIRA-2847.md → 端口改为 19847
docs/PR-1523.md → 版本改为 v3.1523
config/regions.yaml → 区域代码 us-west-2a
```

#### 策略 3：多值组合

答案不是单一值，而是多个值的组合：

```
修复需要同时：
- host: db-prod-03.internal（从服务发现文档获取）
- port: 19847（从故障单获取）
- timeout: 47（从性能测试报告获取）

任何一个值猜错，Grader 都会失败
```

### Grader 必须验证具体值

**❌ 只验证文件存在**
```json
{
  "check": "file_exists",
  "params": {"path": "config/database.yaml"}
}
```
问题：只要文件存在就通过，无法防止 hacking

**✅ 验证具体内容**
```json
{
  "check": "file_content_contains",
  "params": {"path": "config/database.yaml", "keyword": "port: 19847"}
}
```

**✅ 验证多个值**
```json
[
  {"check": "file_content_contains", "params": {"path": "config/database.yaml", "keyword": "host: db-prod-03.internal"}},
  {"check": "file_content_contains", "params": {"path": "config/database.yaml", "keyword": "port: 19847"}},
  {"check": "file_content_contains", "params": {"path": "config/database.yaml", "keyword": "timeout: 47"}}
]
```

---

## 4. 信息藏匿（D4+ 必须遵守）

### 核心原则

关键信息必须分散在多个文件中，增加探索距离，避免"一眼看穿"。

### 探索距离

**探索距离**：Agent 从 Query 到找到答案需要经过的信息获取步骤数。

| 难度 | 探索距离 | 信息分散度 |
|------|---------|-----------|
| D2-D3 | 1-2 步 | 信息可以在 1-2 个文件中 |
| D4-D5 | 3-5 步 | 信息必须分散在 3+ 个文件 |
| D6-D7 | 6-10 步 | 信息分散在 5+ 个文件，深度嵌套 |

### 信息藏匿策略

#### 策略 1：分散关键信息

将问题线索、背景知识、解决方案分散在不同文件中。

**示例**：
```
logs/error.log
  → 发现错误："connection timeout to payment-service"

docs/architecture.md
  → 背景："payment-service 通过配置中心获取配置"

config-center/prod/payment-service.yaml
  → 发现：timeout: 5000（这是问题根因）

docs/incident-reports/INC-2847.md
  → 解决方案："根据压测结果，timeout 应设置为 47000"
```

正确路径需要读取 4 个文件。

#### 策略 2：添加干扰文件

创建看起来相关但实际不是答案的文件。

**干扰类型**：

1. **旧版本文件**
   ```
   config/database.yaml          # 当前使用（正确）
   config/database.yaml.bak      # 备份（干扰）
   config/database.yaml.old      # 旧版本（干扰）
   ```

2. **其他环境配置**
   ```
   config/production.yaml        # 生产环境（正确）
   config/staging.yaml           # 预发环境（干扰）
   config/development.yaml       # 开发环境（干扰）
   ```

3. **相似命名文件**
   ```
   services/order-service/config.yaml      # 正确
   services/order-processor/config.yaml    # 干扰
   services/order-validator/config.yaml    # 干扰
   ```

#### 策略 3：设置红鲱鱼（Red Herring）

设置 2-3 个看起来可能有问题的地方，但只有一个是真正的根因。

**示例**：
```
环境中有 3 个可疑点：
1. logs/gateway.log 显示 "rate limit exceeded"（红鲱鱼）
2. logs/database.log 显示 "slow query"（红鲱鱼）
3. config/payment-service.yaml 中 timeout: 5000（真正根因）

Agent 必须逐一排查，只有修复第 3 个才能通过 Grader
```

#### 策略 4：隐藏答案

**❌ 不要在日志中直接给出答案**
```
logs/error.log:
  "Connection failed to port 5432, please change to 19847"
```

**✅ 只给线索，答案需要推断**
```
logs/error.log:
  "Connection refused on port 5432"

docs/incident-2847.md:
  "根据运维团队调整，数据库已迁移到新端口，详见配置管理系统"

config/service-discovery.yaml:
  "database:
     host: db-prod-03.internal
     port: 19847"
```

#### 策略 5：深度嵌套

将信息藏在嵌套的目录结构中。

**示例**：
```
关键配置文件位置：
services/backend/payment-gateway/configs/production/timeouts/external-api.yaml

而不是：
config/timeout.yaml
```

### 不能做的事

在信息藏匿过程中，**不能**：

- ❌ 删除 Phase 1 创建的核心文件
- ❌ 大改目录结构（环境一旦确定就固定）
- ❌ 创建逻辑矛盾的线索（如两个文档说法相反）
- ❌ 藏得太深导致无解（必须有明确的探索路径）

---

## 5. 难度分级原则

### 难度来源

测试题的难度由以下因素决定：

1. **信息分散程度**：答案需要从多少个文件中获取
2. **干扰信息数量**：有多少个干扰文件和红鲱鱼
3. **推理链条长度**：从线索到答案需要多少步推理
4. **Query 模糊度**：Query 给出的信息有多明确

### 快速参考

| 难度 | Golden Action | 环境文件数 | 信息分散 | 干扰项 |
|------|---------------|-----------|---------|--------|
| D2 | 1-2步 | 3-5个 | 单文件 | 无 |
| D3 | 3-4步 | 8-12个 | 1-2 个文件 | 1-2 个 |
| D4 | 5-6步 | 12-15个 | 3+ 个文件 | 3-5 个 |
| D5 | 7-8步 | 15-20个 | 4+ 个文件 | 5-8 个 |
| D6 | 9-10步 | 20-25个 | 5+ 个文件 | 8-12 个 |
| D7 | 11-15步 | 25-35个 | 6+ 个文件 | 12+ 个 |

详细说明见：`~/.claude/skills/agent-testcase-generator/reference/difficulty_guide.md`

---

## 6. 针对不同工具的设计要点

### Edit 工具

- Query 告诉需要修复什么**问题**，不告诉修改哪个**文件**
- 答案值必须从环境获取（不可预测）
- Grader 验证具体的值，不只是文件存在

**示例**：
```
❌ Query: "请将 config.yaml 中的端口改为 8080"（太直接）
✅ Query: "订单服务无法连接支付网关，请排查配置问题"
```

### Bash 工具

- Query 必须暗示"需要执行脚本/命令"
- 不要说具体执行哪个脚本
- 验证脚本的输出产物（文件、状态变化）

**示例**：
```
❌ Query: "项目需要生成一个构建产物"（太模糊）
✅ Query: "请执行 scripts 目录下的构建脚本，生成生产环境构建产物"
```

### Write 工具

- Query 说明需要生成什么文件、内容约束
- 不给具体内容模板
- Grader 验证文件存在 + 包含必要内容

### KillShell 工具

- 使用 `init_commands` 预先启动后台进程
- Query 描述需要清理的场景，不直接说进程名
- Grader 必须包含至少 2 个 state_check：
  - 主验证：bash_process_not_running
  - 辅助验证：file_not_exists（PID 文件）或其他静态验证

---

## 总结

设计高质量测试用例的核心：

1. ✅ **逆向出题**：从可验证的终点开始
2. ✅ **强可验证**：答案明确，Grader 完备
3. ✅ **低 hacking**：答案不可预测，必须探索
4. ✅ **信息藏匿**：分散信息，增加探索距离（D4+）
5. ✅ **符合难度**：文件数、步数、分散度匹配难度要求

现在开始设计你的测试用例吧！下一步阅读：
```bash
Read ~/.claude/skills/agent-testcase-generator/design/testcase_design.md
```
