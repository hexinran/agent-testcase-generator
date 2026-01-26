# 代码工程类场景设计指南

## 概述

代码工程类任务是 Agent 最核心的能力测试领域，涵盖代码修复、搜索、配置管理、测试执行等场景。

**核心特点**：
- 产物明确：代码/配置文件变更
- 可验证性强：文件内容检查
- 低 hacking 概率：答案值来自环境

---

## 子场景分类

| 子场景 | 描述 | 主要工具 | 验证方式 |
|-------|------|---------|---------|
| `bug_fix` | 修复代码中的 Bug | Edit | file_content_contains |
| `code_search` | 在代码库中搜索特定模式 | Grep/Glob | grep_output_contains |
| `config_management` | 配置文件修改与管理 | Edit | file_content_contains |
| `test_execution` | 运行测试并处理结果 | Bash | bash_exit_code |
| `code_refactor` | 代码重构（Plan 模式） | Edit | file_content_contains + file_moved |

---

## 可验证性设计模式

### 模式 1: 配置修复（Edit）

```
场景：配置文件中的值错误导致服务异常

设计思路：
1. 在日志/错误信息中隐藏正确值
2. 配置文件中设置错误值
3. Agent 需要从环境中提取正确值

验证方式：
- file_content_contains: 检查正确值存在
- file_content_not_contains: 检查错误值已移除
```

**示例**：
```json
{
  "query": "订单服务连接数据库超时，请排查并修复",
  "environment": [
    {"path": "logs/error.log", "content": "Connection timeout. Expected timeout: 47000ms"},
    {"path": "config/db.yaml", "content": "timeout: 5000"}
  ],
  "grader": {
    "checks": [
      {"check": "file_content_contains", "params": {"path": "config/db.yaml", "keyword": "timeout: 47000"}}
    ]
  }
}
```

### 模式 2: Bug 修复（Edit）

```
场景：代码逻辑错误导致功能异常

设计思路：
1. 在测试用例/错误日志中隐藏预期行为
2. 代码中设置错误逻辑
3. Agent 需要理解预期并修复

验证方式：
- file_content_contains: 检查正确逻辑存在
- bash_exit_code: 测试通过
```

### 模式 3: 测试执行（Bash）

```
场景：运行测试套件并处理失败

设计思路：
1. 创建测试文件和被测代码
2. 被测代码有 bug 导致测试失败
3. Agent 需要修复后重新运行测试

验证方式：
- bash_exit_code: 测试退出码为 0
- file_exists: 测试报告生成
```

**示例**：
```json
{
  "query": "运行测试套件，修复失败的测试",
  "environment": [
    {"path": "tests/test_calculator.py", "content": "def test_add(): assert add(1, 2) == 3"},
    {"path": "src/calculator.py", "content": "def add(a, b): return a - b"}
  ],
  "grader": {
    "checks": [
      {"check": "bash_exit_code", "params": {"command": "python -m pytest tests/", "expected_code": 0}}
    ]
  }
}
```

---

## Query 设计模板

### bug_fix
```
[服务名] 出现 [异常现象]，请排查原因并修复。
```

### code_search
```
找出所有使用了 [目标模式] 的文件，并生成报告。
```

### config_management
```
[服务名] 的 [配置项] 配置错误，请根据 [参考来源] 进行修复。
```

### test_execution
```
运行 [测试类型] 测试，确保所有测试通过。如有失败，请修复。
```

### code_refactor (Plan 模式)
```
将 [模块/功能] 从 [旧位置] 重构到 [新位置]，确保所有引用正确更新。
```

---

## Grader 设计模板

### 配置修复
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_content_contains",
      "params": {"path": "<config_file>", "keyword": "<correct_value>"},
      "description": "验证配置已修复为正确值"
    },
    {
      "check": "file_content_not_contains",
      "params": {"path": "<config_file>", "keyword": "<wrong_value>"},
      "description": "验证错误值已移除"
    }
  ]
}
```

### 测试执行
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "bash_exit_code",
      "params": {"command": "python -m pytest tests/", "expected_code": 0},
      "description": "验证所有测试通过"
    }
  ]
}
```

### 代码重构 (Plan 模式)
```json
{
  "type": "state_check",
  "checks": [
    {
      "check": "file_exists",
      "params": {"path": "<new_location>"},
      "description": "验证文件已移动到新位置"
    },
    {
      "check": "file_content_contains",
      "params": {"path": "<importing_file>", "keyword": "from <new_module> import"},
      "description": "验证引用已更新"
    }
  ]
}
```

---

## 难度递进示例

### D2: 单文件修复
- 环境：2-3 个文件
- 线索：直接在错误日志中
- Golden Action：2-3 步

### D3: 跨文件追踪
- 环境：4-6 个文件
- 线索：需要读取多个文件
- Golden Action：3-5 步

### D4: 多线索整合
- 环境：6-10 个文件
- 线索：分散在多个文件，有干扰项
- Golden Action：5-7 步

### D5+: 复杂依赖链
- 环境：10+ 个文件
- 线索：需要理解服务间依赖
- Golden Action：7-10 步

---

## 工具使用要求

| 工具 | 典型用途 | 注意事项 |
|-----|---------|---------|
| Edit | 修改代码/配置 | 必须是最终操作工具 |
| Grep | 搜索错误模式 | 用于定位问题 |
| Glob | 查找文件 | 用于发现项目结构 |
| Read | 读取文件内容 | 用于理解上下文 |
| Bash | 运行测试/构建 | 用于验证修复效果 |
