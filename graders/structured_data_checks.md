# 结构化数据 Check 类型

## json_path_equals

检查 JSON 文件中指定路径的值。

```json
{
  "check": "json_path_equals",
  "params": {
    "path": "output/result.json",
    "json_path": "$.status",
    "expected": "success"
  },
  "description": "验证结果状态为 success"
}
```

**参数**：
- `path`：JSON 文件路径
- `json_path`：JSONPath 表达式
- `expected`：期望值

---

## yaml_key_equals

检查 YAML 文件中指定键的值。

```json
{
  "check": "yaml_key_equals",
  "params": {
    "path": "config/database.yaml",
    "key_path": "database.port",
    "expected": 19847
  },
  "description": "验证数据库端口配置"
}
```

**参数**：
- `path`：YAML 文件路径
- `key_path`：键路径（用 `.` 分隔）
- `expected`：期望值
