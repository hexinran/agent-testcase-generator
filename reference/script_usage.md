# 脚手架脚本用法

本文档说明验证脚本的使用方法。

**脚本位置**：`~/.claude/skills/agent-testcase-generator/scripts/`

---

## 脚本概览

| 脚本 | 用途 | 阶段 |
|------|------|------|
| `phase4_verify.py` | 自测验证（执行 Golden Action） | Phase 4 |
| `phase6_haiku.py` | Haiku 验证（AI 模型测试） | Phase 6 |
| `phase7_quality.py` | 质量评估 | Phase 7 |

---

## phase4_verify.py - 自测验证

### 功能

执行 Golden Action（参考解答）并验证所有 Grader。

### 用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py <case_json_path> [选项]
```

### 参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 |
| `-v, --verbose` | ❌ | 详细输出模式 |
| `--keep-env` | ❌ | 保留验证环境（不删除） |
| `--verify-dir` | ❌ | 指定验证目录 |

### 示例

```bash
# 基本用法
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json

# 保留环境用于调试
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json --keep-env -v
```

### 输出

- 终端显示每步执行状态（✓/✗）和 Grader 验证结果
- 结果保存到 `phase4_result.json`

---

## phase6_haiku.py - Haiku 验证

### 功能

在隔离环境中执行 Haiku 模型验证，捕获真实的工具调用轨迹。

### 用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py <case_json_path> [选项]
```

### 参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 |
| `--haiku-dir` | ❌ | Haiku 工作目录（默认: haiku_space） |
| `--timeout` | ❌ | 执行超时秒数（默认: 600） |
| `-v, --verbose` | ❌ | 详细输出模式 |

### 示例

```bash
# 基本用法
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json

# 增加超时时间
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json --timeout 300
```

### 输出

- 终端显示 Haiku 执行进度和验证结果
- 结果保存到 `phase6_result.json`
- **重要**：从结果中复制 `haiku_evaluation` 和 `haiku_trajectory` 到最终 case.json

---

## phase7_quality.py - 质量评估

### 功能

评估测试用例的质量，包括 hacking 风险、难度合理性、信息分散度等。

### 用法

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase7_quality.py <case_json_path> [选项]
```

### 参数

| 参数 | 必需 | 说明 |
|------|------|------|
| `case_json_path` | ✅ | 测试用例 JSON 文件路径 |
| `--json` | ❌ | 输出 JSON 格式 |
| `-v, --verbose` | ❌ | 详细输出模式 |

---

## 故障排查

### 常见问题

**Q: 找不到 case.json**
- 使用绝对路径：`python3 ... /tmp/workspace/case.json`

**Q: Golden Action 某步失败**
- 查看 `phase4_result.json` 中的 `error` 字段
- 检查文件路径是否正确、环境中是否包含所需文件

**Q: Grader 验证失败**
- 查看 `grader_result.details` 了解哪个 check 失败
- 确认 Golden Action 是否真正达到了 Target

**Q: Haiku 执行超时**
- 增加 timeout：`--timeout 900`

**Q: Python 权限问题**
- 确保脚本可执行：`chmod +x scripts/*.py`

---

## 总结

使用时机：

1. **phase4_verify.py**：设计完成后立即使用，验证 Golden Action 可行性
2. **phase6_haiku.py**：Phase 4 通过后使用，测试题目合理性
3. **phase7_quality.py**：最后使用，评估题目质量（可选）

**严禁**：跳过验证或编造数据，必须使用脚手架真实执行。
