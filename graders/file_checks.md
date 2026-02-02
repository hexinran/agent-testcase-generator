# 文件相关 Check 类型

## file_exists

验证文件存在。

```json
{
  "check": "file_exists",
  "params": {"path": "config/database.yaml"},
  "description": "验证配置文件存在"
}
```

**参数**：
- `path`：文件相对路径

---

## file_not_exists

验证文件不存在。

```json
{
  "check": "file_not_exists",
  "params": {"path": "old/config.yaml"},
  "description": "验证旧配置已删除"
}
```

**参数**：
- `path`：文件相对路径

---

## file_content_contains

验证文件包含指定关键词。

```json
{
  "check": "file_content_contains",
  "params": {
    "path": "config/database.yaml",
    "keyword": "port: 19847",
    "case_insensitive": false
  },
  "description": "验证端口配置正确"
}
```

**参数**：
- `path`：文件相对路径
- `keyword`：要匹配的关键词
- `case_insensitive`：是否忽略大小写（可选，默认 false）

---

## file_content_not_contains

验证文件不包含指定关键词。

```json
{
  "check": "file_content_not_contains",
  "params": {
    "path": "config/database.yaml",
    "keyword": "timeout: 5000"
  },
  "description": "验证错误配置已移除"
}
```

**参数**：
- `path`：文件相对路径
- `keyword`：不应包含的关键词

---

## file_content_match

验证文件内容匹配正则表达式。

```json
{
  "check": "file_content_match",
  "params": {
    "path": "config/database.yaml",
    "pattern": "port:\\s*\\d+"
  },
  "description": "验证端口配置格式正确"
}
```

**参数**：
- `path`：文件相对路径
- `pattern`：正则表达式

---

## directory_exists

验证目录存在。

```json
{
  "check": "directory_exists",
  "params": {"path": "src/validators"},
  "description": "验证验证器目录已创建"
}
```

**参数**：
- `path`：目录相对路径

---

## file_executable

验证文件可执行。

```json
{
  "check": "file_executable",
  "params": {"path": "scripts/build.sh"},
  "description": "验证构建脚本可执行"
}
```

**参数**：
- `path`：文件相对路径
