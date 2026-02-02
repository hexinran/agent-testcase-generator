# Web 工具 Check 类型

## tool_used_webfetch

验证使用了 WebFetch 工具。

```json
{
  "check": "tool_used_webfetch",
  "params": {
    "url_pattern": "example.com"
  },
  "description": "验证获取了 example.com 的内容"
}
```

**参数**：
- `url_pattern`：URL 匹配模式（可选，不指定则只验证使用了 WebFetch）

---

## tool_used_web_search

验证使用了 web_search 工具。

```json
{
  "check": "tool_used_web_search",
  "params": {
    "keyword_pattern": "kubernetes"
  },
  "description": "验证搜索了 kubernetes 相关内容"
}
```

**参数**：
- `keyword_pattern`：搜索关键词匹配模式（可选）

---

## 示例：信息检索场景完整 Grader

```json
{
  "graders": [
    {
      "type": "state_check",
      "checks": [
        {
          "check": "file_exists",
          "params": {"path": "output/research_report.md"},
          "description": "验证报告文件存在"
        },
        {
          "check": "file_content_contains",
          "params": {"path": "output/research_report.md", "keyword": "kubernetes"},
          "description": "验证报告包含搜索主题"
        }
      ]
    },
    {
      "type": "tool_calls",
      "required": [
        {"tool": "WebFetch", "description": "必须使用 WebFetch 获取信息"},
        {"tool": "Write", "description": "必须使用 Write 生成报告"}
      ]
    }
  ]
}
```
