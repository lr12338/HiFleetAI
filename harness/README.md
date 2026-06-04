# Harness 说明

## 1. 模块定位

`harness/` 是 HiFleetAI 的评测与回归目录，用于用例驱动验证聊天契约、状态流转和阶段性回归结果。

## 2. 目录结构

- `cases/`：分类 JSONL 用例
- `fixtures/`：本地辅助资料
- `runners/`：执行入口
- `judges/`：判断逻辑
- `reports/`：最近一次报告输出目录

## 3. 当前主要类别

- `handoff`
  - 验证人工接管相关状态流转
- `regression`
  - 验证 `/api/v1/chat` 契约不退化

## 4. 常用命令

```bash
cd /home/ecs-user/HiFleetAI
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --list-cases
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 5. 结果说明

最近一次执行结果写入：

- `harness/reports/latest.json`
- `harness/reports/latest.md`

如果 Agent API 不可用，runner 会写入结构化失败结果，而不是把失败伪装成通过。

## 6. 当前局限

- `latest.*` 会被下一次执行覆盖
- 结果 API 当前更偏向读取最近一次报告，不是完整历史查询系统
- 知识库、真实多模态、真实渠道接入尚未形成完整 Harness 场景

## 7. 相关文档

- `docs/开发规范.md`
- `docs/测试与部署维护指南.md`
- `docs/验证报告/当前系统验证报告.md`
