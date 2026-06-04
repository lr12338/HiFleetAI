# Changelog

All notable changes to HiFleetAI will be documented in this file.

## Unreleased

### Added

- 初始化 Harness 驱动开发仓库结构。
- 补齐 `/api/v1/chat` 的 MVP 响应契约。
- 新增 `backend/tests/test_chat_api.py`，覆盖 regression、FAQ、Skill 三条最小链路。
- 新增交付文档：`docs/system-overview.md`、`docs/architecture-overview.md`、`docs/testing-deployment-maintenance.md`、`docs/development-status.md`、`docs/phase2-closeout.md`、`docs/agent-handoff.md`、`docs/next-agent-prompt.md`。

### Changed

- 完成 Phase 2 收口，将当前代码基线明确标记为“标准客服后台 MVP 已完成”。
- 更新 `README.md`，补齐中文项目说明、快速启动、测试方式和文档索引。
- 更新 `docs/task-board.md`，对齐 Phase 2 实际拆分结果与完成状态。
- 更新 `docs/implementation-plan.md`，标记 Phase 0-2 已完成、后续工作应从 Phase 3 规划开始。
- 更新 `docs/dev-logs/2026-06-03-master-log.md`，记录 Phase 2 最终验收与 `/api/v1/chat` 对齐结果。

### Validation

- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py`
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`
- `cd /home/ecs-user/HiFleetAI/frontend && npm test`
- `cd /home/ecs-user/HiFleetAI/frontend && npm run build`
- `HARNESS_AGENT_BASE_URL="http://127.0.0.1:<空闲端口>" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression`
