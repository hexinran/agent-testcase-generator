# 验证流程

本文档指导测试用例的验证流程，包括自测和 Haiku 验证两个阶段。

---

## 阶段 1：自测验证（Phase 4）

### 目的

验证 Golden Action（参考解答）是否可以成功执行，以及所有 Grader 是否能通过。

**与 Haiku 验证的区别**：
- 自测：按 reference_solution 执行，**不调用 AI 模型**，快速（几秒）
- Haiku：Haiku 模型自己探索执行，慢（几分钟）

### 执行

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase4_verify.py case.json
```

### 解读结果

| 情况 | 原因 | 修复策略 |
|------|------|---------|
| Golden Action 某步失败 | 文件路径错误、参数不完整 | 检查路径、确保环境包含所需文件 |
| Grader 失败 | 验证条件过严、期望值不匹配 | 查看 `phase4_result.json` 详情，调整 Grader |
| 环境缺失 | environment 中缺少文件 | 添加缺失文件或修改 Golden Action |

### 可修改的部分

- Query（修复歧义、调整模糊度）
- Grader（调整验证条件）
- Environment 内容（修复错误、补充信息）
- **不能**大改 Environment 结构
- **不能**减少 Golden Action 核心逻辑

**验证通过后进入 Phase 6**。

---

## 阶段 2：Haiku 验证（Phase 6）

### 目的

用较弱的模型测试题目是否合理。

**核心原则**：
- Haiku 只能看到 **Query** 和 **环境文件**
- Haiku **不能看到**答案（reference_solution 和 graders）

### 执行

```bash
python3 ~/.claude/skills/agent-testcase-generator/scripts/phase6_haiku.py case.json
```

脚本会自动：
1. 创建 `haiku_space/` 隔离目录
2. 部署环境文件
3. 执行 `init_commands`（启动后台进程等）
4. 调用 Haiku CLI
5. 验证 graders
6. 保存结果到 `phase6_result.json`

### 分析结果

| 情况 | 含义 | 处理 |
|------|------|------|
| 通过，步数合理 | 题目设计合理 | 继续 |
| 通过，步数太少 | 题目太简单 | 增加信息分散度、添加干扰文件 |
| 失败，能力不足 | D5+ 题目可接受 | 记录轨迹即可 |
| 失败，Query/环境问题 | 出题问题 | 修复 Query 歧义、补充环境线索 |

### 提取轨迹数据

**强制要求**：从 `phase6_result.json` 复制到最终 `case.json`：

1. `haiku_evaluation`（整个对象）
2. `haiku_trajectory`（从 `haiku_execution.trajectory` 复制）

**严禁**：
- 编造轨迹数据
- 总结或改写 output
- 添加 reasoning 字段

---

## KillShell 场景特别说明

KillShell 场景需要 `init_commands` 启动后台进程：

```json
{
  "init_commands": [
    {
      "command": "nohup bash services/legacy_sync.sh > logs/legacy_sync.log 2>&1 & echo $! > logs/legacy_sync.pid",
      "description": "启动 legacy_sync 后台进程",
      "wait_sec": 2
    }
  ]
}
```

---

## 常见问题

**Q: init_commands 没有执行？**
- 检查格式是否正确（command, description, wait_sec）

**Q: Haiku 看到了 case.json？**
- 不可能。脚本将 Haiku 的工作目录设置为 `haiku_space/`，该目录中不包含 case.json

**Q: Haiku 超时？**
- 增加超时：`--timeout 900`

---

## 下一步

验证完成后，输出最终结果：阅读 `core/output_format.md`
