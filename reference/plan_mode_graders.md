# Plan 模式 Grader 模板

本文档提供 Plan 模式任务的 Grader 设计模板。

---

## 1. 代码移动 Grader

### 场景
将代码从一个位置移动到另一个位置。

### 模板
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "<新位置路径>"},
          "description": "验证文件已移动到新位置"
        },
        {
          "check": "file_not_exists",
          "params": {"path": "<旧位置路径>"},
          "description": "验证旧文件已删除"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<新位置路径>", "keyword": "<关键代码标识>"},
          "description": "验证代码内容正确迁移"
        },
        {
          "check": "import_updated",
          "params": {
            "path": "<引用文件路径>",
            "old_import": "from <旧模块> import <名称>",
            "new_import": "from <新模块> import <名称>"
          },
          "description": "验证导入语句已更新"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改文件"}
      ]
    }
  ]
}
```

### 示例
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "src/formatters/date.py"},
          "description": "验证 DateFormatter 已移动到新位置"
        },
        {
          "check": "file_not_exists",
          "params": {"path": "src/utils/date_utils.py"},
          "description": "验证旧文件已删除"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/formatters/date.py", "keyword": "class DateFormatter"},
          "description": "验证类定义存在"
        },
        {
          "check": "import_updated",
          "params": {
            "path": "src/main.py",
            "old_import": "from src.utils.date_utils import DateFormatter",
            "new_import": "from src.formatters.date import DateFormatter"
          },
          "description": "验证 main.py 导入已更新"
        }
      ]
    }
  ]
}
```

---

## 2. 配置迁移 Grader

### 场景
将配置从一种格式/位置迁移到另一种。

### 模板
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "<新配置文件路径>"},
          "description": "验证新配置文件已创建"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<新配置文件路径>", "keyword": "<必须包含的配置键>"},
          "description": "验证关键配置已迁移"
        },
        {
          "check": "yaml_key_equals",
          "params": {
            "path": "<新配置文件路径>",
            "key_path": "<配置键路径>",
            "expected": "<预期值>"
          },
          "description": "验证配置值正确"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "<新配置文件路径>", "keyword": "<不应包含的开发环境值>"},
          "description": "验证开发环境配置已替换"
        }
      ]
    }
  ]
}
```

### 示例
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "config/production.yaml"},
          "description": "验证生产配置文件已创建"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "database:"},
          "description": "验证包含数据库配置"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "host: prod-db.example.com"},
          "description": "验证使用生产数据库地址"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "config/production.yaml", "keyword": "localhost"},
          "description": "验证不包含开发环境地址"
        }
      ]
    }
  ]
}
```

---

## 3. 模块拆分 Grader

### 场景
将大模块拆分为多个小模块。

### 模板
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "<新模块1路径>"},
          "description": "验证新模块1已创建"
        },
        {
          "check": "file_exists",
          "params": {"path": "<新模块2路径>"},
          "description": "验证新模块2已创建"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<新模块1路径>", "keyword": "<模块1关键内容>"},
          "description": "验证模块1内容正确"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "<原模块路径>", "keyword": "<已提取的内容>"},
          "description": "验证原模块中已移除提取的内容"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<原模块路径>", "keyword": "from <新模块> import"},
          "description": "验证原模块导入了新模块"
        }
      ]
    }
  ]
}
```

### 示例
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "src/validators/user_validator.py"},
          "description": "验证验证器模块已创建"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/validators/user_validator.py", "keyword": "def validate_email"},
          "description": "验证 validate_email 函数已迁移"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "src/services/user_service.py", "keyword": "def validate_email"},
          "description": "验证原服务中已移除验证函数"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/services/user_service.py", "keyword": "from src.validators.user_validator import"},
          "description": "验证服务导入了验证器"
        }
      ]
    }
  ]
}
```

---

## 4. API 升级 Grader

### 场景
将 API 调用从旧版本升级到新版本。

### 模板
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_not_contains",
          "params": {"path": "<文件1路径>", "keyword": "<旧API调用>"},
          "description": "验证文件1中旧API已替换"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<文件1路径>", "keyword": "<新API调用>"},
          "description": "验证文件1使用新API"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "<文件2路径>", "keyword": "<旧API调用>"},
          "description": "验证文件2中旧API已替换"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "<文件2路径>", "keyword": "<新API调用>"},
          "description": "验证文件2使用新API"
        }
      ]
    }
  ]
}
```

### 示例
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_content_not_contains",
          "params": {"path": "src/handlers/login.py", "keyword": "legacy_auth("},
          "description": "验证 login.py 不再使用旧认证"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/handlers/login.py", "keyword": "authenticate_v2("},
          "description": "验证 login.py 使用新认证"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "src/handlers/admin.py", "keyword": "legacy_auth("},
          "description": "验证 admin.py 不再使用旧认证"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/handlers/admin.py", "keyword": "authenticate_v2("},
          "description": "验证 admin.py 使用新认证"
        }
      ]
    }
  ]
}
```

---

## 5. 目录重组 Grader

### 场景
重新组织项目目录结构。

### 模板
```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "directory_exists",
          "params": {"path": "<新目录路径>"},
          "description": "验证新目录已创建"
        },
        {
          "check": "file_moved",
          "params": {
            "source": "<旧文件路径>",
            "destination": "<新文件路径>"
          },
          "description": "验证文件已移动"
        },
        {
          "check": "file_exists",
          "params": {"path": "<新目录>/__init__.py"},
          "description": "验证包初始化文件存在"
        }
      ]
    }
  ]
}
```

---

## Check 类型速查

| Check 类型 | 参数 | 用途 |
|-----------|------|------|
| `file_exists` | `path` | 验证文件存在 |
| `file_not_exists` | `path` | 验证文件已删除 |
| `file_moved` | `source`, `destination` | 验证文件移动 |
| `file_content_contains` | `path`, `keyword` | 验证包含内容 |
| `file_content_not_contains` | `path`, `keyword` | 验证不包含内容 |
| `import_updated` | `path`, `old_import`, `new_import` | 验证导入更新 |
| `directory_exists` | `path` | 验证目录存在 |
| `yaml_key_equals` | `path`, `key_path`, `expected` | 验证 YAML 值 |
| `json_path_equals` | `path`, `json_path`, `expected` | 验证 JSON 值 |
