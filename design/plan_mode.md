# Plan 模式设计原则

## 概述

Plan 模式专为**多文件操作任务**设计，测试 Agent 在复杂重构、迁移、升级场景中的规划和执行能力。

**核心特点**：
- 涉及多个文件的协调修改
- 需要先规划再执行
- 强调闭环验证（新增 + 删除 + 引用更新）

---

## Plan 模式 vs 普通模式

| 维度 | 普通模式 | Plan 模式 |
|-----|---------|-----------|
| **文件操作** | 单文件或少量文件 | 多文件协调 |
| **任务复杂度** | 直接执行 | 需要规划 |
| **视角** | todo / reference | explore |
| **验证重点** | 内容正确 | 结构变化 + 引用一致 |
| **难度等级** | D2-D7 | Plan-D4 ~ Plan-D7 |

---

## 适用场景

### 1. 代码重构
- 模块拆分：将大模块拆分为多个小模块
- 函数提取：将重复代码提取为公共函数
- 代码移动：将代码从一个位置移动到另一个位置

### 2. 配置迁移
- 环境迁移：从开发环境配置生成生产环境配置
- 格式迁移：从旧配置格式迁移到新格式
- 集中化：将分散的配置集中到统一位置

### 3. API 升级
- 版本升级：从 v1 API 升级到 v2 API
- 废弃替换：替换废弃的 API 调用
- 接口重构：重构内部接口定义

---

## 设计原则

### 原则 1: 闭环验证

Plan 模式任务必须验证完整的"闭环"：

```
闭环 = 新增 + 删除 + 引用更新

示例（模块拆分）：
1. 新增：新模块文件存在
2. 删除：原文件中的代码已移除
3. 引用更新：所有 import 语句已更新
```

### 原则 2: 多验证点覆盖

```json
{
  "grader": {
    "checks": [
      {"check": "file_exists", "params": {"path": "new_location/module.py"}},
      {"check": "file_not_exists", "params": {"path": "old_location/module.py"}},
      {"check": "import_updated", "params": {
        "path": "main.py",
        "old_import": "from old_location import module",
        "new_import": "from new_location import module"
      }}
    ]
  }
}
```

### 原则 3: 结构验证优先

Plan 模式更关注"结构是否正确"而非"内容是否完美"：

```
优先验证：
- 文件是否在正确位置
- 引用是否已更新
- 旧文件是否已删除

次要验证：
- 具体实现细节
- 代码风格
```

---

## 难度定义

### Plan-D4: 简单重构
- **文件数**: 6-10 个
- **操作范围**: 2-3 个文件变更
- **复杂度**: 单一模块移动
- **验证点**: 3-4 个

**示例任务**：
```
将 utils/helpers.py 中的 format_date 函数移动到 utils/date_helpers.py，
并更新所有引用。
```

### Plan-D5: 中等重构
- **文件数**: 10-15 个
- **操作范围**: 4-6 个文件变更
- **复杂度**: 多模块协调
- **验证点**: 4-6 个

**示例任务**：
```
将订单服务的验证逻辑从 services/order.py 提取到 validators/order_validator.py，
同时更新相关的测试文件和导入语句。
```

### Plan-D6: 复杂重构
- **文件数**: 15-20 个
- **操作范围**: 6-10 个文件变更
- **复杂度**: 跨模块重构
- **验证点**: 6-8 个

**示例任务**：
```
将分散在各服务中的数据库访问逻辑统一到 repositories/ 目录下，
创建对应的 Repository 类，并更新所有服务的调用方式。
```

### Plan-D7: 大规模重构
- **文件数**: 20+ 个
- **操作范围**: 10+ 个文件变更
- **复杂度**: 架构级重构
- **验证点**: 8+ 个

**示例任务**：
```
将单体应用的用户模块拆分为独立的微服务，包括：
1. 创建新的服务目录结构
2. 迁移相关代码
3. 更新所有内部调用为 API 调用
4. 更新配置和依赖
```

---

## Query 设计指南

### 核心目标：触发 EnterPlanMode

Plan 模式的 Query 必须设计得让 Agent 意识到：**这个任务需要先规划再执行**，从而调用 `EnterPlanMode` 工具。

### 触发 Plan 模式的关键要素

| 要素 | 说明 | 示例表达 |
|-----|------|---------|
| **多文件操作** | 暗示需要修改多个文件 | "更新所有引用"、"涉及多个模块" |
| **结构变化** | 暗示目录/架构调整 | "重构"、"迁移"、"拆分" |
| **依赖关系** | 暗示修改有连锁影响 | "确保一致性"、"不破坏现有功能" |
| **复杂度信号** | 暗示需要思考 | "设计方案"、"规划步骤" |

### 触发词汇表

**强触发词**（高概率触发 EnterPlanMode）：
- "重构"、"迁移"、"拆分"、"合并"
- "设计一个方案"、"规划实施步骤"
- "涉及多个文件"、"更新所有相关引用"
- "确保架构一致性"、"不影响现有功能"

**弱触发词**（可能不触发）：
- "修改"、"更新"、"修复"（太简单）
- 直接指定文件和操作（太具体）

### Query 模板

**模板 A：强调规划（推荐 Plan-D6/D7）**
```
请设计方案并实施：[目标描述]，
需要考虑 [约束1]、[约束2]，
确保 [质量要求]。
```

**模板 B：强调多文件（推荐 Plan-D4/D5）**
```
将 [源位置] 的 [内容] [操作] 到 [目标位置]，
更新所有相关的 [引用类型]。
```

### 示例对比

**❌ 不好的 Query（太直接，可能不触发 Plan）**：
```
把 src/utils.py 里的 format_date 函数复制到 src/helpers/date.py
```

**✓ 好的 Query（触发 Plan 模式）**：
```
将 src/utils.py 中的日期处理相关函数提取到独立模块，
重构后需要更新所有引用这些函数的文件，确保测试仍然通过。
```

**❌ 不好的 Query（没有复杂度信号）**：
```
创建 config/production.yaml 文件
```

**✓ 好的 Query（有复杂度信号）**：
```
基于现有的开发环境配置，设计并生成生产环境配置，
需要识别所有环境相关的配置项并进行适当调整，
确保与现有部署脚本兼容。
```

### 难度与 Query 直接程度

| 难度 | Query 直接程度 | 说明 |
|-----|---------------|------|
| Plan-D4 | 较直接 | 明确说"将 A 移到 B，更新引用" |
| Plan-D5 | 中等 | 说目标和约束，不说具体步骤 |
| Plan-D6 | 较模糊 | 只说目标，需要 Agent 分析依赖 |
| Plan-D7 | 模糊 | 只说高层目标，需要 Agent 自己设计方案 |

---

## Grader 设计指南

### EnterPlanMode 验证

**必须验证** Agent 是否使用了 `EnterPlanMode` 工具：

```json
{
  "type": "tool_calls",
  "required": [
    {"tool": "EnterPlanMode", "description": "必须进入 Plan 模式进行规划"}
  ]
}
```

### 必须包含的验证

1. **新文件存在**
```json
{"check": "file_exists", "params": {"path": "new/location/file.py"}}
```

2. **旧文件状态**（根据场景选择）
```json
// 移动场景：旧文件不存在
{"check": "file_not_exists", "params": {"path": "old/location/file.py"}}

// 提取场景：旧文件中代码已移除
{"check": "file_content_not_contains", "params": {"path": "old/file.py", "keyword": "extracted_function"}}
```

3. **引用更新**
```json
{"check": "import_updated", "params": {
  "path": "main.py",
  "old_import": "from old import thing",
  "new_import": "from new import thing"
}}
```

### 专用 Check 类型

| Check 类型 | 用途 | 参数 |
|-----------|------|------|
| `file_moved` | 验证文件移动 | `source`, `destination` |
| `import_updated` | 验证导入更新 | `path`, `old_import`, `new_import` |
| `file_not_exists` | 验证文件已删除 | `path` |
| `directory_exists` | 验证目录创建 | `path` |

---

## 环境设计指南

### 文件结构要求

Plan 模式环境应该有清晰的项目结构：

```
project/
├── src/
│   ├── services/
│   │   ├── user_service.py      # 待重构
│   │   └── order_service.py
│   ├── utils/
│   │   └── helpers.py
│   └── main.py                   # 有导入引用
├── tests/
│   └── test_user_service.py     # 有导入引用
└── config/
    └── settings.yaml
```

### 预埋线索

在代码注释或文档中预埋重构提示：

```python
# TODO: This validation logic should be extracted to validators/
def create_user(data):
    # validation logic here (100+ lines)
    ...
```

### 干扰项设计

添加类似但不需要修改的文件：

```
src/
├── services/
│   ├── user_service.py      # 需要重构
│   ├── order_service.py     # 干扰：类似结构但不需要改
│   └── payment_service.py   # 干扰：类似结构但不需要改
```

---

## 完整示例

参见 `reference/plan_mode_examples.md`
