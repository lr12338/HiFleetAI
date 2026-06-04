# HifleetAI Task Board

Status values: `planned`, `in_progress`, `blocked`, `review`, `done`.

| Task ID | Task Name | Phase | Owner | Status | Dependencies | Acceptance Commands | Log |
|---|---|---|---|---|---|---|---|
| P0-02 | Configuration system and environment variables | Phase 0 | sub-agent-config | review | P0-01 | `python3 -m pytest backend/tests/test_config.py` | `docs/dev-logs/P0-02-config.md` |
| P0-03 | Docker Compose basic dependencies | Phase 0 | sub-agent-deploy | review | P0-02 variable contract | `docker compose -f deploy/docker-compose.yml config` | `docs/dev-logs/P0-03-docker-compose.md` |
| P0-04 | Database migration foundation | Phase 0 | sub-agent-db | review | P0-02, P0-03 | `python3 -m pytest backend/tests/test_migrations.py`; `alembic upgrade head` | `docs/dev-logs/P0-04-migrations.md` |
| P0-05 | Pytest and test infrastructure | Phase 0 | sub-agent-test | review | P0-02 | `python3 -m pytest` | `docs/dev-logs/P0-05-pytest.md` |
| P0-06 | Harness skeleton | Phase 0 | sub-agent-harness | review | P0-05 | `python3 harness/runners/run_eval.py --list-cases`; `python3 harness/runners/run_eval.py --category faq` | `docs/dev-logs/P0-06-harness.md` |
| P1-01 | Agent API minimal health chain | Phase 1 | sub-agent-api | review | P0-02, P0-05 | `python3 -m pytest backend/tests/test_health.py`; `python3 -m pytest` | `docs/dev-logs/P1-01-agent-api-health.md` |
| P1-02 | Conversation and Message base models | Phase 1 | sub-agent-conversation | review | P0-04, P0-05, P1-01 | `python3 -m pytest backend/tests/test_conversations.py`; `python3 -m pytest` | `docs/dev-logs/P1-02-conversation-message.md` |
| P1-03 | Model Gateway abstraction | Phase 1 | sub-agent-model-gateway | review | P0-02, P0-05, P1-01 | `python3 -m pytest backend/tests/test_model_gateway.py`; `python3 -m pytest` | `docs/dev-logs/P1-03-model-gateway.md` |
| P1-04 | Supervisor minimal routing skeleton | Phase 1 | sub-agent-supervisor | review | P0-05, P1-01, P1-03 | `python3 -m pytest backend/tests/test_supervisor.py`; `python3 -m pytest`; `python3 harness/runners/run_eval.py --category regression` | `docs/dev-logs/P1-04-supervisor-routing.md` |
| P2-01 | Login and auth foundation | Phase 2 | sub-agent-phase2-auth | done | P1-01 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_auth.py`; `npm test`; `npm run build` | `docs/dev-logs/P2-01-login-auth.md` |
| P2-02 | Conversation list | Phase 2 | sub-agent-phase2-list | done | P1-02, P2-01 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_list.py`; `npm test`; `npm run build` | `docs/dev-logs/P2-02-conversation-list.md` |
| P2-03 | Conversation detail | Phase 2 | sub-agent-phase2-detail | done | P1-02, P1-03, P2-02 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_detail.py`; `npm test`; `npm run build` | `docs/dev-logs/P2-03-conversation-detail.md` |
| P2-04 | Human handoff and AI state | Phase 2 | sub-agent-phase2-handoff | done | P1-02, P1-04, P2-03 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_handoff_api.py`; `npm test`; `npm run build`; `python3 harness/runners/run_eval.py --category handoff` | `docs/dev-logs/P2-04A-handoff-api.md` / `docs/dev-logs/P2-04B-handoff-ui.md` |
| P2-05 | Internal notes | Phase 2 | sub-agent-phase2-notes | done | P2-03 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_notes_api.py`; `npm test`; `npm run build`; `python3 harness/runners/run_eval.py --category regression` | `docs/dev-logs/P2-05A-notes-api.md` / `docs/dev-logs/P2-05B-notes-ui.md` |
| P2-06 | Harness results page | Phase 2 | sub-agent-phase2-harness-ui | done | P0-06, P2-01 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_harness_api.py`; `npm test`; `npm run build` | `docs/dev-logs/P2-06A-harness-api.md` / `docs/dev-logs/P2-06B-harness-results-ui.md` |
| P2-01A | Frontend bootstrap | Phase 2 | sub-agent-phase2-frontend-bootstrap | done | none | `npm test`; `npm run build` | `docs/dev-logs/P2-01A-frontend-bootstrap.md` |
| P2-01B | Backend auth API foundation | Phase 2 | sub-agent-phase2-backend-auth | done | P1-01, P0-04 | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_auth.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest` | `docs/dev-logs/P2-01B-backend-auth.md` |
| P2-01C | Login UI and protected route | Phase 2 | sub-agent-phase2-login-ui | done | P2-01A, P2-01B | `npm test`; `npm run build` | `docs/dev-logs/P2-01C-login-ui.md` |
| P2-02A | Conversation list API | Phase 2 | sub-agent-phase2-list-api | done | P1-02, P2-01B | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_list.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest` | `docs/dev-logs/P2-02A-conversation-list-api.md` |
| P2-02B | Conversation list UI | Phase 2 | sub-agent-phase2-list-ui | done | P2-01A, P2-01C, P2-02A | `npm test`; `npm run build` | `docs/dev-logs/P2-02B-conversation-list-ui.md` |
| P2-03A | Conversation detail API | Phase 2 | sub-agent-phase2-detail-api | done | P1-02, P1-03, P2-01B | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_detail.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest` | `docs/dev-logs/P2-03A-conversation-detail-api.md` |
| P2-03B | Conversation detail UI | Phase 2 | sub-agent-phase2-detail-ui | done | P2-01A, P2-01C, P2-03A | `npm test`; `npm run build` | `docs/dev-logs/P2-03B-conversation-detail-ui.md` |
| P2-04A | Handoff API | Phase 2 | sub-agent-phase2-handoff-api | done | P1-02, P1-04, P2-03A | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_handoff_api.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`; `python3 harness/runners/run_eval.py --category handoff` | `docs/dev-logs/P2-04A-handoff-api.md` |
| P2-04B | Handoff UI | Phase 2 | sub-agent-phase2-handoff-ui | done | P2-03B, P2-04A | `npm test`; `npm run build` | `docs/dev-logs/P2-04B-handoff-ui.md` |
| P2-05A | Notes API | Phase 2 | sub-agent-phase2-notes-api | done | P2-03A, P2-01B | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_notes_api.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest` | `docs/dev-logs/P2-05A-notes-api.md` |
| P2-05B | Notes UI | Phase 2 | sub-agent-phase2-notes-ui | done | P2-03B, P2-05A | `npm test`; `npm run build` | `docs/dev-logs/P2-05B-notes-ui.md` |
| P2-06A | Harness results API | Phase 2 | sub-agent-phase2-harness-api | done | P0-06, P2-01B | `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_harness_api.py`; `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest` | `docs/dev-logs/P2-06A-harness-api.md` |
| P2-06B | Harness results UI | Phase 2 | sub-agent-phase2-harness-results-ui | done | P2-01A, P2-01C, P2-06A | `npm test`; `npm run build` | `docs/dev-logs/P2-06B-harness-results-ui.md` |

## Board Rules

- Phase 2 parent numbering follows `docs/phase2-subtasks.md` as the current execution baseline: AI pause/resume was merged into `P2-04`, `P2-05` is internal notes, and `P2-06` is the Harness results page.
- The master agent updates task status and assigns one task per sub agent.
- A sub agent writes exactly one task log before requesting review.
- No sub agent commits directly to `main`.
- A task cannot move to `done` until all acceptance commands are run or a documented environment blocker is recorded.
- Failed tests or failed Harness cases keep the task in `blocked` or `review`; they are not reported as success.
