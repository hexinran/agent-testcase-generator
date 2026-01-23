# 测试用例示例集

本文档提供不同工具、不同难度的测试用例示例供参考。

---

## Edit D3 示例：配置文件端口错误

### 场景

订单服务连接数据库超时，需要修复配置中的端口设置。

### 环境文件（8个）

```
config/
  database.yaml         # 包含错误端口
  database.yaml.bak     # 干扰项
services/
  order-service/
    app.py
logs/
  error.log             # 显示连接失败
  access.log
docs/
  README.md
  troubleshooting.md    # 说明正确端口应该从服务发现配置读取
config-center/
  service-discovery.yaml  # 包含正确的端口 19847
```

### Query

```
"订单服务连接数据库失败，错误日志显示连接超时。请排查配置问题并修复。"
```

### Golden Action（4步）

```json
[
  {"tool": "Read", "input": {"file_path": "logs/error.log"}, "reasoning": "查看错误日志"},
  {"tool": "Grep", "input": {"pattern": "port", "output_mode": "files_with_matches"}, "reasoning": "搜索端口配置"},
  {"tool": "Read", "input": {"file_path": "config-center/service-discovery.yaml"}, "reasoning": "查看服务发现配置"},
  {"tool": "Edit", "input": {"file_path": "config/database.yaml", "old_string": "port: 5432", "new_string": "port: 19847"}, "reasoning": "修复端口配置"}
]
```

### Graders

```json
[
  {
    "type": "state_check",
    "checks": [
      {"check": "file_content_contains", "params": {"path": "config/database.yaml", "keyword": "port: 19847"}, "description": "验证端口已修复"},
      {"check": "file_content_not_contains", "params": {"path": "config/database.yaml", "keyword": "port: 5432"}, "description": "验证错误端口已移除"}
    ]
  },
  {
    "type": "tool_calls",
    "required": [{"tool": "Edit", "description": "必须使用 Edit 工具"}]
  }
]
```

### 设计要点

- ✅ 信息分散：logs/ → docs/ → config-center/
- ✅ 答案不可预测：端口 19847 来自服务发现配置
- ✅ 有干扰项：database.yaml.bak
- ✅ 符合 D3 要求：3-4 步，8 个文件

---

## Bash D4 示例：执行构建脚本

### 场景

项目需要生成生产环境构建产物，需要找到并执行正确的构建脚本。

### 环境文件（13个）

```
scripts/
  build-dev.sh          # 开发环境构建（干扰项）
  build-staging.sh      # 预发环境构建（干扰项）
  build-production.sh   # 生产环境构建（正确）
  deploy.sh             # 部署脚本（干扰项）
config/
  build.yaml            # 构建配置
  environments/
    dev.env
    staging.env
    production.env      # 包含构建参数
src/
  main.py
  utils.py
docs/
  BUILD_GUIDE.md        # 构建指南，说明生产环境使用 build-production.sh
  README.md
```

### Query

```
"请执行 scripts 目录下的构建脚本，生成生产环境构建产物。
产物应该包含编译后的代码和配置文件，输出到 dist/production/ 目录。"
```

### Golden Action（5步）

```json
[
  {"tool": "Read", "input": {"file_path": "docs/BUILD_GUIDE.md"}, "reasoning": "查看构建指南"},
  {"tool": "Glob", "input": {"pattern": "scripts/build-*.sh"}, "reasoning": "查找所有构建脚本"},
  {"tool": "Read", "input": {"file_path": "scripts/build-production.sh"}, "reasoning": "查看生产环境构建脚本"},
  {"tool": "Read", "input": {"file_path": "config/environments/production.env"}, "reasoning": "确认生产环境配置"},
  {"tool": "Bash", "input": {"command": "bash scripts/build-production.sh"}, "reasoning": "执行生产环境构建"}
]
```

### Graders

```json
[
  {
    "type": "state_check",
    "checks": [
      {"check": "directory_exists", "params": {"path": "dist/production"}, "description": "验证产物目录已创建"},
      {"check": "file_exists", "params": {"path": "dist/production/main.py"}, "description": "验证代码文件已生成"},
      {"check": "file_exists", "params": {"path": "dist/production/production.env"}, "description": "验证配置文件已包含"}
    ]
  },
  {
    "type": "tool_calls",
    "required": [{"tool": "Bash", "description": "必须使用 Bash 工具"}]
  }
]
```

### 设计要点

- ✅ Query 暗示"执行脚本"但不说具体哪个
- ✅ 多个干扰脚本（dev, staging, deploy）
- ✅ 需要从文档中确认正确的脚本
- ✅ 验证产物的具体内容
- ✅ 符合 D4 要求：5 步，13 个文件

---

## KillShell D3 示例：清理残留进程

### 场景

系统升级后发现有旧版本的后台同步服务仍在运行，需要清理。

### 环境文件（10个）

```
services/
  legacy_sync.sh        # 旧版同步服务脚本
  current_sync.sh       # 当前版本（干扰项）
logs/
  legacy_sync.log       # 旧版服务日志
  legacy_sync.pid       # PID 文件（将被清理）
  current_sync.log
docs/
  UPGRADE_GUIDE.md      # 升级指南，提到要清理旧服务
  README.md
config/
  services.yaml         # 服务配置
  processes.yaml        # 进程配置
scripts/
  check_processes.sh    # 进程检查脚本
```

### init_commands

```json
[
  {
    "command": "nohup bash services/legacy_sync.sh > logs/legacy_sync_output.log 2>&1 & echo $! > logs/legacy_sync.pid",
    "description": "启动 legacy_sync 后台进程模拟残留服务",
    "wait_sec": 2
  }
]
```

### Query

```
"系统升级后发现旧版本的数据同步服务仍在后台运行，占用资源。
请根据升级文档找到并清理残留的后台进程。"
```

### Golden Action（4步）

```json
[
  {"tool": "Read", "input": {"file_path": "docs/UPGRADE_GUIDE.md"}, "reasoning": "查看升级指南"},
  {"tool": "Bash", "input": {"command": "ps aux | grep legacy_sync"}, "reasoning": "查看运行的进程"},
  {"tool": "Read", "input": {"file_path": "logs/legacy_sync.pid"}, "reasoning": "读取PID文件"},
  {"tool": "KillShell", "input": {"shell_id": "<从Bash获取>"}, "reasoning": "停止残留进程"}
]
```

### Graders

```json
[
  {
    "type": "state_check",
    "checks": [
      {"check": "bash_process_not_running", "params": {"process_name": "legacy_sync"}, "description": "验证进程已停止"},
      {"check": "file_not_exists", "params": {"path": "logs/legacy_sync.pid"}, "description": "验证PID文件已清理"}
    ]
  },
  {
    "type": "tool_calls",
    "required": [{"tool": "KillShell", "description": "必须使用 KillShell 工具"}]
  }
]
```

### 设计要点

- ✅ 使用 init_commands 启动后台进程
- ✅ Grader 包含 2 个 state_check（进程状态 + 文件清理）
- ✅ Query 描述场景，不直接说进程名
- ✅ 需要从文档中了解要清理哪个服务
- ✅ 符合 D3 要求：4 步，10 个文件

---

## 更多示例

完整的测试用例示例可以在生成的测试题中查看。

每个测试用例都应该遵循：
1. **逆向出题**：从可验证的目标逆向设计
2. **低 hacking**：答案不可预测，必须从环境获取
3. **信息藏匿**：关键信息分散（D4+）
4. **真实场景**：模拟真实的软件工程任务

---

## 参考其他文档

- **难度详解**：`~/.claude/skills/agent-testcase-generator/reference/difficulty_guide.md`
- **Grader 规范**：`~/.claude/skills/agent-testcase-generator/reference/grader_spec.md`
- **设计流程**：`~/.claude/skills/agent-testcase-generator/design/testcase_design.md`
