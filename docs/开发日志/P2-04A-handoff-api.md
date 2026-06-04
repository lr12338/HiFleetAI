# P2-04A Handoff API

## 范围

- 仅实现 `P2-04A Handoff API` 的最小后端能力。
- 新增会话人工接管、暂停 AI、恢复 AI 三个 REST 接口。
- 增加最小状态校验与 `handoff_events` 审计记录。
- 补充后端测试与 handoff Harness 最小真实校验路径。
- 不包含前端 UI、真实外部客服平台联动、鉴权协议变更、其他 Phase 2 子任务。

## 修改文件

- `backend/app/api/conversations.py`
- `backend/app/services/conversation_service.py`
- `backend/tests/test_handoff_api.py`
- `backend/tests/test_harness_runner.py`
- `harness/runners/run_eval.py`
- `harness/judges/deterministic_judge.py`
- `harness/cases/handoff_cases.jsonl`
- `docs/task-board.md`
- `docs/dev-logs/P2-04A-handoff-api.md`

## 测试结果

- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_handoff_api.py`
  - 结果：通过，`4 passed`
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`
  - 结果：通过，`44 passed`
- `python3 harness/runners/run_eval.py --category handoff`
  - 结果：通过，`status=passed total=1 passed=1 failed=0`
- 备注：测试与 Harness 运行过程中均出现现有 `fastapi.testclient` 的 `StarletteDeprecationWarning`，未阻塞本任务验收。

## 风险

- 当前 handoff Harness 仅覆盖最小成功流转序列，未扩展到更多非法状态或权限边界场景。
- 项目仍未实现真实 `/api/v1/chat` 端到端链路，因此 handoff Harness 采用进程内真实 API 序列校验，而非依赖外部运行中的服务。
- `pause-ai` 与 `resume-ai` 的允许流转按 MVP 最小闭环实现，若后续产品要更严格区分 `human_pending`、`human_active`、`ai_paused` 的操作入口，需再细化状态机。

## 是否新增依赖

- 未新增依赖。
