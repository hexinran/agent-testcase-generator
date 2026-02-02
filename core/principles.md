# 核心设计原则

本文档阐述 Agent 测试用例设计的核心原则。**必须在开始设计前完全理解**。

---

## 1. 逆向出题方法论

### 核心思想

从可验证的**终点**逆向构建，而不是从问题正向推导。

```
传统出题（正向）：问题描述 → 期望解法 → 验证方式
问题：验证往往是事后补充，容易有漏洞。

逆向出题（推荐）：可验证的目标状态 → 验证逻辑(Grader) → 问题描述(Query) → 参考解法
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

---

## 2. 可验证性优先

### 核心原则

答案必须有明确的验证点。如果答案很开放，必须通过约束使其可验证。

### 示例对比

**不好**：开放式任务
```
Query: "请分析系统性能问题并生成报告"
Target: "生成性能分析报告"
问题：报告内容是开放的，无法验证对错
```

**好**：添加约束
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

1. **Query 中明确说明**："请将结果保存为 output.json"
2. **环境中的规范文档**：README.md 说明输出文件命名规范
3. **既有的项目约定**：日志统一放在 logs/ 目录

---

## 3. 低 Hacking 概率

### 核心原则

**答案值必须从环境中获取，不能被预测或猜测。**

### 什么是 Hacking？

Agent 不通过正确的探索路径，而是通过猜测、常识或模式识别直接得到答案。

### 示例对比

**高 Hacking 风险**：
```
场景：端口配置错误
环境：config/database.yaml 中 port: 5432
Query: "数据库连接失败，请修复端口配置"
Target: port: 5433

问题：5432 → 5433 是最常见的递增，容易猜对
Hacking 成功率：~60%
```

**低 Hacking 风险**：
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

**策略 1：使用非常规值**
- 不要 5432 → 5433（递增）
- 不要 v1 → v2（版本号递增）
- 要 5432 → 19847（从文档获取）
- 要 timeout: 30 → timeout: 47（从性能测试报告获取）

**策略 2：答案值与文档关联**
```
docs/JIRA-2847.md → 端口改为 19847
docs/PR-1523.md → 版本改为 v3.1523
config/regions.yaml → 区域代码 us-west-2a
```

**策略 3：多值组合**
```
修复需要同时：
- host: db-prod-03.internal（从服务发现文档获取）
- port: 19847（从故障单获取）
- timeout: 47（从性能测试报告获取）

任何一个值猜错，Grader 都会失败
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

**策略 1：分散关键信息**

将问题线索、背景知识、解决方案分散在不同文件中：
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

**策略 2：添加干扰文件**
- 旧版本文件：`config.yaml.bak`, `config.yaml.old`
- 其他环境配置：`staging.yaml`, `development.yaml`
- 相似命名文件：`order-service/`, `order-processor/`

**策略 3：设置红鲱鱼（Red Herring）**

设置 2-3 个看起来可能有问题的地方，但只有一个是真正的根因。

**策略 4：隐藏答案**

不要在日志中直接给出答案，只给线索，答案需要推断。

---

## 5. 总结

设计高质量测试用例的核心：

1. **逆向出题**：从可验证的终点开始
2. **强可验证**：答案明确，Grader 完备
3. **低 hacking**：答案不可预测，必须探索
4. **信息藏匿**：分散信息，增加探索距离（D4+）
5. **符合难度**：文件数、步数、分散度匹配难度要求
