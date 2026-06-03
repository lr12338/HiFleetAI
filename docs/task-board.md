# HifleetAI Task Board

Status values: `planned`, `in_progress`, `blocked`, `review`, `done`.

| Task ID | Task Name | Phase | Owner | Status | Dependencies | Acceptance Commands | Log |
|---|---|---|---|---|---|---|---|
| P0-02 | Configuration system and environment variables | Phase 0 | sub-agent-config | review | P0-01 | `python3 -m pytest backend/tests/test_config.py` | `docs/dev-logs/P0-02-config.md` |
| P0-03 | Docker Compose basic dependencies | Phase 0 | sub-agent-deploy | planned | P0-02 variable contract | `docker compose -f deploy/docker-compose.yml config` | `docs/dev-logs/P0-03-docker-compose.md` |
| P0-04 | Database migration foundation | Phase 0 | sub-agent-db | planned | P0-02, P0-03 | `python3 -m pytest backend/tests/test_migrations.py`; `alembic upgrade head` | `docs/dev-logs/P0-04-migrations.md` |
| P0-05 | Pytest and test infrastructure | Phase 0 | sub-agent-test | review | P0-02 | `python3 -m pytest` | `docs/dev-logs/P0-05-pytest.md` |
| P0-06 | Harness skeleton | Phase 0 | sub-agent-harness | review | P0-05 | `python3 harness/runners/run_eval.py --list-cases`; `python3 harness/runners/run_eval.py --category faq` | `docs/dev-logs/P0-06-harness.md` |
| P1-01 | Agent API minimal health chain | Phase 1 | sub-agent-api | planned | P0-02, P0-05 | `python3 -m pytest backend/tests/test_health.py`; `python3 -m pytest` | `docs/dev-logs/P1-01-agent-api-health.md` |
| P1-02 | Conversation and Message base models | Phase 1 | sub-agent-conversation | planned | P0-04, P0-05, P1-01 | `python3 -m pytest backend/tests/test_conversations.py`; `python3 -m pytest` | `docs/dev-logs/P1-02-conversation-message.md` |
| P1-03 | Model Gateway abstraction | Phase 1 | sub-agent-model-gateway | planned | P0-02, P0-05, P1-01 | `python3 -m pytest backend/tests/test_model_gateway.py`; `python3 -m pytest` | `docs/dev-logs/P1-03-model-gateway.md` |
| P1-04 | Supervisor minimal routing skeleton | Phase 1 | sub-agent-supervisor | planned | P0-05, P1-01, P1-03 | `python3 -m pytest backend/tests/test_supervisor.py`; `python3 -m pytest`; `python3 harness/runners/run_eval.py --category regression` | `docs/dev-logs/P1-04-supervisor-routing.md` |

## Board Rules

- The master agent updates task status and assigns one task per sub agent.
- A sub agent writes exactly one task log before requesting review.
- No sub agent commits directly to `main`.
- A task cannot move to `done` until all acceptance commands are run or a documented environment blocker is recorded.
- Failed tests or failed Harness cases keep the task in `blocked` or `review`; they are not reported as success.
