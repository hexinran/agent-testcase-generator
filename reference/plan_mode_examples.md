# Plan 模式完整示例

本文档提供 Plan 模式测试用例的完整示例。

---

## 示例 1: 代码移动 (Plan-D4)

### 任务描述
将日期格式化工具类移动到专门的 formatters 目录。

### 完整测试用例

```json
{
  "task": {
    "id": "Plan_D4_code_move_20260126",
    "desc": "将 src/utils/date_utils.py 中的 DateFormatter 类移动到 src/formatters/date.py，并更新所有引用",
    "tool_name": "Edit",
    "difficulty": "Plan-D4",
    "scenario_theme": "代码移动重构",
    "task_type": "code_engineering",
    "perspective": "explore"
  },

  "environment": [
    {
      "path": "src/utils/date_utils.py",
      "content": "\"\"\"Date utility functions\"\"\"\n\nclass DateFormatter:\n    \"\"\"Format dates in various styles\"\"\"\n    \n    @staticmethod\n    def to_iso(dt):\n        return dt.strftime('%Y-%m-%d')\n    \n    @staticmethod\n    def to_human(dt):\n        return dt.strftime('%B %d, %Y')\n    \n    @staticmethod\n    def to_timestamp(dt):\n        return int(dt.timestamp())\n"
    },
    {
      "path": "src/utils/__init__.py",
      "content": "from .date_utils import DateFormatter\n"
    },
    {
      "path": "src/main.py",
      "content": "\"\"\"Main application entry point\"\"\"\nfrom datetime import datetime\nfrom src.utils.date_utils import DateFormatter\n\ndef main():\n    now = datetime.now()\n    print(f\"ISO: {DateFormatter.to_iso(now)}\")\n    print(f\"Human: {DateFormatter.to_human(now)}\")\n\nif __name__ == '__main__':\n    main()\n"
    },
    {
      "path": "src/services/report_service.py",
      "content": "\"\"\"Report generation service\"\"\"\nfrom src.utils.date_utils import DateFormatter\nfrom datetime import datetime\n\nclass ReportService:\n    def generate_header(self):\n        return f\"Report generated on {DateFormatter.to_human(datetime.now())}\"\n"
    },
    {
      "path": "src/formatters/__init__.py",
      "content": "# Formatters package\n"
    },
    {
      "path": "tests/test_date_formatter.py",
      "content": "\"\"\"Tests for DateFormatter\"\"\"\nimport unittest\nfrom datetime import datetime\nfrom src.utils.date_utils import DateFormatter\n\nclass TestDateFormatter(unittest.TestCase):\n    def test_to_iso(self):\n        dt = datetime(2026, 1, 15)\n        self.assertEqual(DateFormatter.to_iso(dt), '2026-01-15')\n"
    }
  ],

  "init_commands": [],

  "reference_solution": [
    {
      "tool": "Glob",
      "input": {"pattern": "**/*.py"},
      "reasoning": "查找所有 Python 文件了解项目结构"
    },
    {
      "tool": "Grep",
      "input": {"pattern": "from.*date_utils.*import", "path": "src/"},
      "reasoning": "找出所有导入 DateFormatter 的文件"
    },
    {
      "tool": "Read",
      "input": {"file_path": "src/utils/date_utils.py"},
      "reasoning": "读取要移动的源文件"
    },
    {
      "tool": "Write",
      "input": {
        "file_path": "src/formatters/date.py",
        "content": "\"\"\"Date formatting utilities\"\"\"\n\nclass DateFormatter:\n    \"\"\"Format dates in various styles\"\"\"\n    \n    @staticmethod\n    def to_iso(dt):\n        return dt.strftime('%Y-%m-%d')\n    \n    @staticmethod\n    def to_human(dt):\n        return dt.strftime('%B %d, %Y')\n    \n    @staticmethod\n    def to_timestamp(dt):\n        return int(dt.timestamp())\n"
      },
      "reasoning": "在新位置创建文件"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "src/main.py",
        "old_string": "from src.utils.date_utils import DateFormatter",
        "new_string": "from src.formatters.date import DateFormatter"
      },
      "reasoning": "更新 main.py 的导入"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "src/services/report_service.py",
        "old_string": "from src.utils.date_utils import DateFormatter",
        "new_string": "from src.formatters.date import DateFormatter"
      },
      "reasoning": "更新 report_service.py 的导入"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "tests/test_date_formatter.py",
        "old_string": "from src.utils.date_utils import DateFormatter",
        "new_string": "from src.formatters.date import DateFormatter"
      },
      "reasoning": "更新测试文件的导入"
    },
    {
      "tool": "Bash",
      "input": {"command": "rm src/utils/date_utils.py"},
      "reasoning": "删除原文件"
    }
  ],

  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "src/formatters/date.py"},
          "description": "验证新文件已创建"
        },
        {
          "check": "file_not_exists",
          "params": {"path": "src/utils/date_utils.py"},
          "description": "验证旧文件已删除"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/formatters/date.py", "keyword": "class DateFormatter"},
          "description": "验证类定义已迁移"
        },
        {
          "check": "import_updated",
          "params": {
            "path": "src/main.py",
            "old_import": "from src.utils.date_utils import DateFormatter",
            "new_import": "from src.formatters.date import DateFormatter"
          },
          "description": "验证 main.py 导入已更新"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/services/report_service.py", "keyword": "from src.formatters.date import DateFormatter"},
          "description": "验证 report_service.py 导入已更新"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "tests/test_date_formatter.py", "keyword": "from src.formatters.date import DateFormatter"},
          "description": "验证测试文件导入已更新"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具更新导入"}
      ]
    }
  ]
}
```

---

## 示例 2: 模块拆分 (Plan-D5)

### 任务描述
将用户服务中的验证逻辑提取到独立的验证器模块。

### 完整测试用例

```json
{
  "task": {
    "id": "Plan_D5_module_split_20260126",
    "desc": "将 src/services/user_service.py 中的验证函数提取到 src/validators/user_validator.py，保持功能不变",
    "tool_name": "Edit",
    "difficulty": "Plan-D5",
    "scenario_theme": "模块拆分重构",
    "task_type": "code_engineering",
    "perspective": "explore"
  },

  "environment": [
    {
      "path": "src/services/user_service.py",
      "content": "\"\"\"User service with validation logic\"\"\"\nimport re\nfrom typing import Dict, Any\n\nclass UserService:\n    def __init__(self, db):\n        self.db = db\n    \n    # TODO: Extract validation logic to separate module\n    def validate_email(self, email: str) -> bool:\n        \"\"\"Validate email format\"\"\"\n        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n        return bool(re.match(pattern, email))\n    \n    def validate_password(self, password: str) -> tuple:\n        \"\"\"Validate password strength\"\"\"\n        errors = []\n        if len(password) < 8:\n            errors.append('Password must be at least 8 characters')\n        if not re.search(r'[A-Z]', password):\n            errors.append('Password must contain uppercase letter')\n        if not re.search(r'[0-9]', password):\n            errors.append('Password must contain number')\n        return len(errors) == 0, errors\n    \n    def validate_username(self, username: str) -> bool:\n        \"\"\"Validate username format\"\"\"\n        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))\n    \n    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Create a new user\"\"\"\n        if not self.validate_email(data.get('email', '')):\n            raise ValueError('Invalid email')\n        \n        valid, errors = self.validate_password(data.get('password', ''))\n        if not valid:\n            raise ValueError(f'Invalid password: {errors}')\n        \n        if not self.validate_username(data.get('username', '')):\n            raise ValueError('Invalid username')\n        \n        return self.db.insert('users', data)\n    \n    def get_user(self, user_id: int) -> Dict[str, Any]:\n        \"\"\"Get user by ID\"\"\"\n        return self.db.find_one('users', {'id': user_id})\n"
    },
    {
      "path": "src/services/__init__.py",
      "content": "from .user_service import UserService\n"
    },
    {
      "path": "src/validators/__init__.py",
      "content": "# Validators package\n"
    },
    {
      "path": "src/api/user_api.py",
      "content": "\"\"\"User API endpoints\"\"\"\nfrom src.services.user_service import UserService\n\ndef create_user_endpoint(request, db):\n    service = UserService(db)\n    return service.create_user(request.json)\n"
    },
    {
      "path": "tests/test_user_service.py",
      "content": "\"\"\"Tests for UserService\"\"\"\nimport unittest\nfrom unittest.mock import Mock\nfrom src.services.user_service import UserService\n\nclass TestUserService(unittest.TestCase):\n    def setUp(self):\n        self.db = Mock()\n        self.service = UserService(self.db)\n    \n    def test_validate_email_valid(self):\n        self.assertTrue(self.service.validate_email('test@example.com'))\n    \n    def test_validate_email_invalid(self):\n        self.assertFalse(self.service.validate_email('invalid-email'))\n    \n    def test_validate_password_weak(self):\n        valid, errors = self.service.validate_password('weak')\n        self.assertFalse(valid)\n"
    }
  ],

  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "src/services/user_service.py"},
      "reasoning": "阅读源文件了解验证逻辑"
    },
    {
      "tool": "Grep",
      "input": {"pattern": "validate_", "path": "src/"},
      "reasoning": "查找所有验证函数的使用"
    },
    {
      "tool": "Write",
      "input": {
        "file_path": "src/validators/user_validator.py",
        "content": "\"\"\"User validation functions\"\"\"\nimport re\nfrom typing import Tuple, List\n\ndef validate_email(email: str) -> bool:\n    \"\"\"Validate email format\"\"\"\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))\n\ndef validate_password(password: str) -> Tuple[bool, List[str]]:\n    \"\"\"Validate password strength\"\"\"\n    errors = []\n    if len(password) < 8:\n        errors.append('Password must be at least 8 characters')\n    if not re.search(r'[A-Z]', password):\n        errors.append('Password must contain uppercase letter')\n    if not re.search(r'[0-9]', password):\n        errors.append('Password must contain number')\n    return len(errors) == 0, errors\n\ndef validate_username(username: str) -> bool:\n    \"\"\"Validate username format\"\"\"\n    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))\n"
      },
      "reasoning": "创建独立的验证器模块"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "src/services/user_service.py",
        "old_string": "\"\"\"User service with validation logic\"\"\"\nimport re\nfrom typing import Dict, Any",
        "new_string": "\"\"\"User service\"\"\"\nfrom typing import Dict, Any\nfrom src.validators.user_validator import validate_email, validate_password, validate_username"
      },
      "reasoning": "更新导入语句"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "src/services/user_service.py",
        "old_string": "    # TODO: Extract validation logic to separate module\n    def validate_email(self, email: str) -> bool:\n        \"\"\"Validate email format\"\"\"\n        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n        return bool(re.match(pattern, email))\n    \n    def validate_password(self, password: str) -> tuple:\n        \"\"\"Validate password strength\"\"\"\n        errors = []\n        if len(password) < 8:\n            errors.append('Password must be at least 8 characters')\n        if not re.search(r'[A-Z]', password):\n            errors.append('Password must contain uppercase letter')\n        if not re.search(r'[0-9]', password):\n            errors.append('Password must contain number')\n        return len(errors) == 0, errors\n    \n    def validate_username(self, username: str) -> bool:\n        \"\"\"Validate username format\"\"\"\n        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))\n    ",
        "new_string": "    "
      },
      "reasoning": "移除已提取的验证函数"
    },
    {
      "tool": "Edit",
      "input": {
        "file_path": "src/services/user_service.py",
        "old_string": "if not self.validate_email",
        "new_string": "if not validate_email"
      },
      "reasoning": "更新函数调用（移除 self.）"
    }
  ],

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
          "description": "验证 validate_email 已迁移"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/validators/user_validator.py", "keyword": "def validate_password"},
          "description": "验证 validate_password 已迁移"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "src/services/user_service.py", "keyword": "def validate_email(self"},
          "description": "验证原服务中验证函数已移除"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "src/services/user_service.py", "keyword": "from src.validators.user_validator import"},
          "description": "验证服务导入了验证器"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Edit", "description": "必须使用 Edit 工具修改文件"},
        {"tool": "Write", "description": "必须使用 Write 工具创建新文件"}
      ]
    }
  ]
}
```

---

## 示例 3: 配置迁移 (Plan-D4)

### 任务描述
根据开发环境配置生成生产环境配置。

### 完整测试用例

```json
{
  "task": {
    "id": "Plan_D4_config_migration_20260126",
    "desc": "根据 config/development.yaml 生成 config/production.yaml，替换所有开发环境特定的值",
    "tool_name": "Write",
    "difficulty": "Plan-D4",
    "scenario_theme": "配置迁移",
    "task_type": "system_ops",
    "perspective": "explore"
  },

  "environment": [
    {
      "path": "config/development.yaml",
      "content": "# Development configuration\napp:\n  name: myapp\n  env: development\n  debug: true\n\ndatabase:\n  host: localhost\n  port: 5432\n  name: myapp_dev\n  user: dev_user\n  password: dev_password_123\n\nredis:\n  host: localhost\n  port: 6379\n\nlogging:\n  level: DEBUG\n  format: verbose\n"
    },
    {
      "path": "config/production.template.yaml",
      "content": "# Production configuration template\n# Replace the following values:\n# - database.host -> prod-db.internal.example.com\n# - database.name -> myapp_prod\n# - database.user -> prod_user\n# - database.password -> (use environment variable)\n# - redis.host -> prod-redis.internal.example.com\n# - logging.level -> INFO\n# - app.debug -> false\n"
    },
    {
      "path": "docs/deployment.md",
      "content": "# Deployment Guide\n\n## Production Database\n- Host: prod-db.internal.example.com\n- Port: 5432\n- Database: myapp_prod\n\n## Production Redis\n- Host: prod-redis.internal.example.com\n- Port: 6379\n\n## Environment Variables\n- DB_USER: prod_user\n- DB_PASSWORD: ${DB_PASSWORD}\n"
    }
  ],

  "reference_solution": [
    {
      "tool": "Read",
      "input": {"file_path": "config/development.yaml"},
      "reasoning": "读取开发配置了解结构"
    },
    {
      "tool": "Read",
      "input": {"file_path": "config/production.template.yaml"},
      "reasoning": "读取生产配置模板了解替换规则"
    },
    {
      "tool": "Read",
      "input": {"file_path": "docs/deployment.md"},
      "reasoning": "读取部署文档获取生产环境值"
    },
    {
      "tool": "Write",
      "input": {
        "file_path": "config/production.yaml",
        "content": "# Production configuration\napp:\n  name: myapp\n  env: production\n  debug: false\n\ndatabase:\n  host: prod-db.internal.example.com\n  port: 5432\n  name: myapp_prod\n  user: prod_user\n  password: ${DB_PASSWORD}\n\nredis:\n  host: prod-redis.internal.example.com\n  port: 6379\n\nlogging:\n  level: INFO\n  format: json\n"
      },
      "reasoning": "创建生产配置文件"
    }
  ],

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
          "params": {"path": "config/production.yaml", "keyword": "prod-db.internal.example.com"},
          "description": "验证使用生产数据库地址"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "myapp_prod"},
          "description": "验证使用生产数据库名"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "prod-redis.internal.example.com"},
          "description": "验证使用生产 Redis 地址"
        },
        {
          "check": "file_content_not_contains",
          "params": {"path": "config/production.yaml", "keyword": "localhost"},
          "description": "验证不包含 localhost"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "debug: false"},
          "description": "验证 debug 已关闭"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "config/production.yaml", "keyword": "level: INFO"},
          "description": "验证日志级别为 INFO"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "Write", "description": "必须使用 Write 工具创建配置文件"}
      ]
    }
  ]
}
```

---

## 使用指南

### 1. 选择合适的难度

- **Plan-D4**: 2-3 个文件变更，单一方向重构
- **Plan-D5**: 4-6 个文件变更，需要协调多个模块
- **Plan-D6**: 6-10 个文件变更，复杂的依赖关系
- **Plan-D7**: 10+ 个文件变更，架构级重构

### 2. 设计验证闭环

确保验证覆盖：
1. 新文件/目录创建
2. 旧文件/代码删除或修改
3. 所有引用更新

### 3. 避免的问题

- 不要只验证新文件存在，还要验证旧文件处理
- 不要遗漏任何导入更新的验证
- 确保验证点使用环境中的具体值（低 hacking）
