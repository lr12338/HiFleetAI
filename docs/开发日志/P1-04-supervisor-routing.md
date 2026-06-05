# P1-04 Supervisor Minimal Routing Skeleton

## Task Metadata

- Task ID: P1-04
- Executor: sub-agent-supervisor
- Phase: Phase 1
- Requirement Section: `docs/implementation-plan.md` P1-04 Supervisor Minimal Routing Skeleton; `HiFleetAI开发方案.md` 6.2 Supervisor Agent
- Start Time: 2026-06-03T20:21:00+08:00
- End Time: 2026-06-03T20:24:59+08:00
- Status: review

## Scope

- Goal: Create a minimal Supervisor router that returns structured decisions for FAQ, web research, image understanding, skill candidates, human handoff, and general chat without executing real tools or models.
- In Scope: Supervisor route schema, deterministic rule-first router, pytest coverage for representative intent inputs, task board update, and task log.
- Out Of Scope: real RAG calls, real web search, real multimodal execution, real Skill execution, chat API orchestration, database writes, channel adapters, and frontend changes.
- Dependencies: P0-05, P1-01, and P1-03.

## Modified Files

- `backend/app/agent/supervisor.py`
- `backend/app/schemas/supervisor.py`
- `backend/tests/test_supervisor.py`
- `docs/task-board.md`
- `docs/dev-logs/P1-04-supervisor-routing.md`

## Harness Cases

No Harness case was added or changed for P1-04. The existing regression case was executed unchanged, and its structured failure was recorded exactly as observed because `/api/v1/chat` is not available in the local environment.

## Acceptance Commands

- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_supervisor.py`
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`
- `python3 harness/runners/run_eval.py --category regression`

## Test Results

- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_supervisor.py`: passed with 7 tests covering `faq`, `web_research`, `image_understanding`, `skill_candidate`, `handoff_required`, `general_chat`, and missing skill argument handling.
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`: passed with 24 tests.
- `python3 harness/runners/run_eval.py --category regression`: completed and wrote a structured failed report. The single regression case failed with `Agent API unavailable: <urlopen error [Errno 111] Connection refused>`.
- Full pytest emitted one existing warning from `fastapi.testclient` about future `httpx2` usage; it did not fail the suite.

## Risks And Remaining Issues

- The Supervisor router currently exposes only a deterministic route plan. It is not yet wired into `/api/v1/chat`, so Harness cannot validate end-to-end routing behavior through the Agent API.
- Skill detection is intentionally minimal and rule-based. It recognizes representative MVP patterns and returns structured candidate data, but it does not execute or validate against a live Skill registry.
- FAQ and web research classification currently depends on keyword heuristics. Future tasks may need richer routing rules once Knowledge Hub and Deep Search Hub are implemented.

## Next Stage Readiness

P1-04 may enter review. The Supervisor module is importable, returns structured `route_only` decisions for the required MVP intents, targeted pytest and full pytest pass, and the regression Harness run produced an honest structured failure instead of fake success.
