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

### 模板

```
将 [源位置] 的 [目标内容] [操作类型] 到 [目标位置]，
确保 [约束条件]。
```

### 示例

**代码移动**：
```
将 src/utils.py 中的 DateFormatter 类移动到 src/formatters/date.py，
并更新所有引用该类的文件。
```

**模块拆分**：
```
将 src/services/user_service.py 中的验证逻辑提取到 src/validators/user.py，
保持原有功能不变。
```

**配置迁移**：
```
根据 config/development.yaml 生成 config/production.yaml，
将所有开发环境特定的值替换为生产环境值。
```

---

## Grader 设计指南

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
