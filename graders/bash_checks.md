# Bash 相关 Check 类型

## bash_check

执行 Bash 命令并检查输出。

```json
{
  "check": "bash_check",
  "params": {
    "command": "cat config.yaml | grep port",
    "expected": "19847"
  },
  "description": "验证端口配置"
}
```

**参数**：
- `command`：要执行的 Bash 命令
- `expected`：期望输出中包含的字符串

---

## bash_exit_code

检查命令退出码。

```json
{
  "check": "bash_exit_code",
  "params": {
    "command": "python3 test.py",
    "expected_code": 0
  },
  "description": "验证测试通过"
}
```

**参数**：
- `command`：要执行的命令
- `expected_code`：期望的退出码（可选，默认 0）

---

## bash_process_running

检查进程是否运行。

```json
{
  "check": "bash_process_running",
  "params": {
    "process_name": "worker.py"
  },
  "description": "验证 Worker 进程运行"
}
```

或使用 PID 文件：

```json
{
  "check": "bash_process_running",
  "params": {
    "pid_file": "logs/worker.pid"
  },
  "description": "验证 Worker 进程运行"
}
```

**参数**（二选一）：
- `process_name`：进程名称
- `pid_file`：PID 文件路径

---

## bash_process_not_running

检查进程是否已停止。

```json
{
  "check": "bash_process_not_running",
  "params": {
    "process_name": "legacy_sync"
  },
  "description": "验证 legacy_sync 进程已停止"
}
```

**参数**（二选一）：
- `process_name`：进程名称
- `pid_file`：PID 文件路径

**KillShell 场景必须**：
- 主验证：`bash_process_not_running`
- 辅助验证：`file_not_exists`（PID 文件）

---

## 示例：KillShell 场景完整 Grader

```json
{
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
      "required": [
        {"tool": "KillShell", "description": "必须使用 KillShell 工具"}
      ]
    }
  ]
}
```
