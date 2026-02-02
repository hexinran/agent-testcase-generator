# 高级 Check 类型

## any_of

多个 check 满足其一即可。

```json
{
  "check": "any_of",
  "params": {
    "checks": [
      {"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port: 19847"}},
      {"check": "file_content_contains", "params": {"path": "config.yaml", "keyword": "port: '19847'"}}
    ]
  },
  "description": "验证端口配置（允许带引号或不带引号）"
}
```

**参数**：
- `checks`：check 列表，满足任一即通过

---

## custom_script

执行自定义 Python 脚本验证。

```json
{
  "check": "custom_script",
  "params": {
    "script_content": "import json\nwith open('output/result.json') as f:\n    data = json.load(f)\n    assert data['count'] > 10",
    "timeout": 30
  },
  "description": "验证结果数量大于 10"
}
```

**参数**：
- `script_content`：Python 脚本内容
- `timeout`：超时时间（秒，可选）

**注意**：自定义脚本应谨慎使用，优先使用标准 check 类型。

---

## grep_output_contains

检查 grep 输出包含期望内容。

```json
{
  "check": "grep_output_contains",
  "params": {
    "pattern": "ERROR",
    "path": "logs/",
    "expected": "connection timeout"
  },
  "description": "验证日志包含超时错误"
}
```

**参数**：
- `pattern`：grep 模式
- `path`：搜索路径
- `expected`：期望在输出中的内容

---

## glob_result_count

检查 glob 结果数量。

```json
{
  "check": "glob_result_count",
  "params": {
    "pattern": "src/**/*.py",
    "min_count": 5,
    "max_count": 20
  },
  "description": "验证 Python 文件数量在合理范围"
}
```

**参数**：
- `pattern`：glob 模式
- `min_count`：最小数量（可选）
- `max_count`：最大数量（可选）
