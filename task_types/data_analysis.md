# 数据分析类场景设计指南

## 概述

数据分析类任务测试 Agent 处理日志、数据文件和指标的能力，最终产出分析报告或处理后的数据文件。

**核心特点**：
- 产物明确：分析报告或处理后的数据文件
- 可验证性：文件内容包含从环境提取的具体信息
- 实用性强：模拟真实数据分析场景

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `log_analysis` | 日志文件分析与错误提取 | Grep/Bash + Write | file_content_contains |
| `data_processing` | 数据格式转换与清洗 | Bash + Write | file_content_contains |
| `quality_analysis` | 代码质量或数据质量分析 | Grep + Write | file_content_contains |
| `metrics_aggregation` | 指标聚合与统计 | Bash + Write | file_content_contains |

---

## 可验证性设计模式

### 模式 1: 日志分析（Grep + Write）

```
场景：从日志中提取错误信息生成报告

设计思路：
1. 创建包含多种日志的环境
2. 在日志中埋入特定错误（带唯一标识）
3. 要求 Agent 提取并汇总到报告

验证方式：
- file_exists: 报告文件存在
- file_content_contains: 报告包含特定错误标识
```

**示例**：
```json
{
  "query": "分析过去24小时的错误日志，生成 error-report.md 汇总所有 ERROR 级别的错误",
  "environment": [
    {
      "path": "logs/app-2026-01-25.log",
      "content": "2026-01-25 10:00:00 INFO Starting service\n2026-01-25 10:05:00 ERROR [ERR-7429] Database connection failed\n2026-01-25 10:10:00 WARN Low memory"
    },
    {
      "path": "logs/app-2026-01-26.log",
      "content": "2026-01-26 09:00:00 INFO Service running\n2026-01-26 09:30:00 ERROR [ERR-8156] Payment timeout\n2026-01-26 10:00:00 ERROR [ERR-7429] Database connection failed"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "error-report.md"}},
      {"check": "file_content_contains", "params": {"path": "error-report.md", "keyword": "ERR-7429"}},
      {"check": "file_content_contains", "params": {"path": "error-report.md", "keyword": "ERR-8156"}}
    ]
  }
}
```

### 模式 2: 数据转换（Bash + Write）

```
场景：将数据从一种格式转换为另一种

设计思路：
1. 提供源数据文件（CSV/JSON/XML）
2. 要求转换为目标格式
3. 验证转换结果包含关键数据

验证方式：
- file_exists: 目标文件存在
- file_content_contains: 包含关键字段值
```

**示例**：
```json
{
  "query": "将 users.csv 转换为 users.json 格式",
  "environment": [
    {
      "path": "data/users.csv",
      "content": "id,name,email\n1001,Alice,alice@example.com\n1002,Bob,bob@example.com"
    }
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "data/users.json"}},
      {"check": "file_content_contains", "params": {"path": "data/users.json", "keyword": "1001"}},
      {"check": "file_content_contains", "params": {"path": "data/users.json", "keyword": "alice@example.com"}}
    ]
  }
}
```

### 模式 3: 指标聚合（Bash + Write）

```
场景：从多个数据源聚合统计指标

设计思路：
1. 创建多个包含指标数据的文件
2. 要求 Agent 汇总计算
3. 验证汇总结果的关键数值

验证方式：
- file_content_contains: 包含正确的统计结果
```

**示例**：
```json
{
  "query": "汇总各服务的请求统计，生成 metrics-summary.md",
  "environment": [
    {"path": "metrics/order-service.json", "content": "{\"requests\": 15234, \"errors\": 127}"},
    {"path": "metrics/payment-service.json", "content": "{\"requests\": 8921, \"errors\": 45}"},
    {"path": "metrics/user-service.json", "content": "{\"requests\": 21056, \"errors\": 89}"}
  ],
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "metrics-summary.md"}},
      {"check": "file_content_contains", "params": {"path": "metrics-summary.md", "keyword": "45211"}},
      {"check": "file_content_contains", "params": {"path": "metrics-summary.md", "keyword": "261"}}
    ]
  }
}
```

---

## Query 设计模板

### log_analysis
```
分析 [时间范围] 的 [日志类型] 日志，提取所有 [目标信息]，生成 [报告文件名]。
```

### data_processing
```
将 [源文件] 从 [源格式] 转换为 [目标格式]，保存到 [目标文件]。
```

### quality_analysis
```
分析 [代码库/数据集] 的 [质量维度]，生成质量报告 [报告文件名]。
```

### metrics_aggregation
```
汇总 [数据源] 中的 [指标类型]，计算 [统计方式]，输出到 [报告文件]。
```

---

## Grader 设计模板

### 日志分析报告
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<report_file>"},
      "description": "验证报告文件已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<report_file>", "keyword": "<unique_error_id_1>"},
      "description": "验证包含第一个关键错误"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<report_file>", "keyword": "<unique_error_id_2>"},
      "description": "验证包含第二个关键错误"
    }
  ]
}
```

### 数据转换
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<output_file>"},
      "description": "验证输出文件已生成"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<output_file>", "keyword": "<key_data_point>"},
      "description": "验证关键数据正确转换"
    }
  ]
}
```

---

## 难度递进示例

### D2: 单文件分析
- 环境：1-2 个数据文件
- 任务：简单提取或转换
- Golden Action：2-3 步

### D3: 多文件聚合
- 环境：3-5 个数据文件
- 任务：跨文件汇总
- Golden Action：4-5 步

### D4: 复杂数据处理
- 环境：5-8 个文件，混合格式
- 任务：过滤 + 转换 + 聚合
- Golden Action：5-7 步

### D5+: 完整数据管道
- 环境：10+ 个文件
- 任务：多阶段处理 + 验证
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Grep | 搜索日志模式 | 用于快速定位 |
| Bash | 数据处理命令 | awk, sed, jq 等 |
| Write | 输出报告/结果 | 最终产物 |
| Read | 读取数据文件 | 理解数据结构 |
| Glob | 查找数据文件 | 发现数据源 |

---

## 低 Hacking 设计要点

### 使用唯一标识符

```
错误设计：检查报告包含 "error"
正确设计：检查报告包含 "ERR-7429"（环境中的具体错误码）
```

### 使用具体数值

```
错误设计：检查报告包含 "total requests"
正确设计：检查报告包含 "45211"（环境中的具体统计值）
```

### 多验证点组合

```json
{
  "checks": [
    {"check": "file_content_contains", "params": {"keyword": "ERR-7429"}},
    {"check": "file_content_contains", "params": {"keyword": "ERR-8156"}},
    {"check": "file_content_contains", "params": {"keyword": "Database connection"}}
  ]
}
```
