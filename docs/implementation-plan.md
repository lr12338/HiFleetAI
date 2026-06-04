# HifleetAI Phase 0-1 Implementation Plan

## 当前状态说明

本文档原始作用是定义 Phase 0 到 Phase 1 的实施顺序。当前仓库已经完成 Phase 2 收口，因此本文件不再代表“当前待做清单”，而是作为历史计划基线保留。

当前阶段状态：

- Phase 0：已完成
- Phase 1：已完成
- Phase 2：已完成收口
- Phase 2 的实际拆分与交付结果以 `docs/phase2-subtasks.md`、`docs/task-board.md`、`docs/phase2-closeout.md` 为准
- 后续待开发范围应从 Phase 3 规划开始，而不是回到本文件继续拆 Phase 0-1

后续开发建议：

1. 先阅读 `HiFleetAI开发方案.md` 中的 Phase 3 路线图。
2. 结合 `docs/development-status.md` 制定新的分任务计划。
3. 新计划继续遵循 Harness 驱动、小任务开发和证据优先原则。

This plan covers only P0-02 to P0-06 and P1-01 to P1-04. It follows the MVP boundary: built-in admin console test sessions, Agent API, Harness, and standard customer service admin console foundations. It excludes real WeChat Official Account, Chatwoot, WeChat Customer Service, production write operations, subscription notifications, file-analysis sandbox, and real production business writes.

## Development Order

1. P0-02 creates backend configuration and environment variable loading.
2. P0-03 creates Docker Compose templates for local dependencies.
3. P0-04 creates database migration foundations and core schema placeholders.
4. P0-05 creates pytest and test infrastructure.
5. P0-06 creates Harness skeleton, case loader, deterministic judge entry points, and report shape.
6. P1-01 creates the minimal Agent API health chain.
7. P1-02 creates Conversation and Message base models.
8. P1-03 creates Model Gateway abstraction without embedding provider secrets.
9. P1-04 creates Supervisor minimal routing skeleton.

## Task Details

### P0-02 Configuration System And Environment Variables

- Goal: Create a backend configuration layer that reads local environment variables and supports safe defaults for development.
- Scope: `backend/app/core/config.py`, backend package initialization, `.env.example` alignment, configuration tests.
- Forbidden: Do not write real API keys, do not start services, do not connect to production systems, do not hard-code provider credentials.
- Files: `backend/app/core/config.py`, `backend/app/__init__.py`, `backend/tests/test_config.py`, `.env.example`.
- Dependencies: P0-01.
- Harness case requirement: No Agent Harness case is required. Validation is pytest-based because this task prepares runtime configuration.
- Acceptance commands: `python3 -m pytest backend/tests/test_config.py`.
- Definition of done: Configuration loads required settings, rejects missing required runtime values where appropriate, and test coverage proves secrets are not stored in source files.

### P0-03 Docker Compose Basic Dependencies

- Goal: Provide local development dependency templates for PostgreSQL with pgvector, Redis, and MinIO.
- Scope: Compose file, deployment README, environment variable mapping.
- Forbidden: Do not start Docker services, do not write production passwords, do not commit volumes, do not add real object storage data.
- Files: `deploy/docker-compose.yml`, `deploy/README.md`, `.env.example`.
- Dependencies: P0-02 for consistent environment variable names.
- Harness case requirement: No Agent Harness case is required. Compose validation is the acceptance method.
- Acceptance commands: `docker compose -f deploy/docker-compose.yml config`.
- Definition of done: Compose config renders successfully and all local dependency credentials are provided through placeholder environment variables.

### P0-04 Database Migration Foundation

- Goal: Establish migration tooling and foundational schema structure for MVP tables.
- Scope: Database connection module, migration environment, initial migration for users, conversations, messages, model calls, retrieval logs, skills, tool calls, handoff events, conversation notes, and Harness run/result tables.
- Forbidden: Do not connect to production databases, do not insert production data, do not add real customer data, do not optimize pgvector beyond schema compatibility.
- Files: `backend/app/db/`, `backend/app/models/`, `backend/alembic/`, `backend/tests/test_migrations.py`.
- Dependencies: P0-02 and P0-03.
- Harness case requirement: Harness database tables must support future run/result records, but no eval case is required for this task.
- Acceptance commands: `python3 -m pytest backend/tests/test_migrations.py`; `alembic upgrade head`.
- Definition of done: Migration can create the foundational schema in a local development database and tests validate expected table names.

### P0-05 Pytest And Test Infrastructure

- Goal: Make the backend test suite repeatable for all later tasks.
- Scope: pytest configuration, test client fixtures, temporary database strategy, environment isolation, coverage of health/config scaffolding.
- Forbidden: Do not rely on external model APIs, do not require real object storage, do not require real network access.
- Files: `backend/pyproject.toml` or `backend/pytest.ini`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `tests/README.md`.
- Dependencies: P0-02.
- Harness case requirement: No Agent Harness case is required. This task supports later Harness and API validation.
- Acceptance commands: `python3 -m pytest`.
- Definition of done: A clean test run succeeds from the repository root with deterministic local fixtures.

### P0-06 Harness Skeleton

- Goal: Create the first executable Harness framework without pretending the Agent API exists.
- Scope: JSONL case directory, case loader, category filtering, deterministic judge shell, structured `latest.json` and `latest.md` failure report generation when API is unavailable.
- Forbidden: Do not fake Agent API success, do not introduce LLM Judge as a required dependency, do not hard-code answers to pass cases.
- Files: `harness/cases/*.jsonl`, `harness/runners/run_eval.py`, `harness/judges/deterministic_judge.py`, `harness/reports/README.md`, `harness/README.md`.
- Dependencies: P0-05.
- Harness case requirement: Create initial schema-valid cases for `faq`, `rag`, `skill`, `handoff`, and `regression`, with at least one case per category.
- Acceptance commands: `python3 harness/runners/run_eval.py --list-cases`; `python3 harness/runners/run_eval.py --category faq`.
- Definition of done: Harness lists cases and writes structured failure reports when the Agent API endpoint is unavailable.

### P1-01 Agent API Minimal Health Chain

- Goal: Create the minimal backend API structure needed for future `/api/v1/chat` work.
- Scope: FastAPI application entry, `GET /api/health`, versioned API router, request id middleware, basic error response shape.
- Forbidden: Do not implement full chat behavior, do not call a model provider, do not write channel adapters.
- Files: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/api/__init__.py`, `backend/tests/test_health.py`.
- Dependencies: P0-02 and P0-05.
- Harness case requirement: Harness may check service availability later, but pytest is the required validation for this task.
- Acceptance commands: `python3 -m pytest backend/tests/test_health.py`; `python3 -m pytest`.
- Definition of done: Health endpoint returns a stable response and the backend app can be loaded by the test client.

### P1-02 Conversation And Message Base Models

- Goal: Define the minimum persistence model for conversation and message tracking.
- Scope: ORM models, schemas, repository/service layer for create/read operations, tests for message timeline ordering.
- Forbidden: Do not add external channel identities beyond `console`, do not implement production send operations, do not add customer data fixtures.
- Files: `backend/app/models/conversation.py`, `backend/app/models/message.py`, `backend/app/services/conversation_service.py`, `backend/tests/test_conversations.py`.
- Dependencies: P0-04, P0-05, and P1-01.
- Harness case requirement: Future FAQ cases must be able to assert conversation and message creation; this task may add a structural regression case only if P0-06 is complete.
- Acceptance commands: `python3 -m pytest backend/tests/test_conversations.py`; `python3 -m pytest`.
- Definition of done: A service can create a console conversation, append user and assistant messages, and return a correctly ordered timeline.

### P1-03 Model Gateway Abstraction

- Goal: Create a provider-neutral model gateway that can later call Volcengine Ark Doubao and DeepSeek through configuration.
- Scope: Gateway interface, request/response types, provider selection by config, timeout/error shape, model call logging contract.
- Forbidden: Do not store API keys in code, do not perform live model calls in unit tests, do not claim success when provider credentials are missing.
- Files: `backend/app/agent/model_gateway.py`, `backend/app/schemas/model.py`, `backend/tests/test_model_gateway.py`.
- Dependencies: P0-02, P0-05, and P1-01.
- Harness case requirement: Future regression cases must verify missing credentials produce explicit failure rather than fake success.
- Acceptance commands: `python3 -m pytest backend/tests/test_model_gateway.py`; `python3 -m pytest`.
- Definition of done: Tests prove the gateway returns structured success for fake local providers and structured failure for missing real provider credentials.

### P1-04 Supervisor Minimal Routing Skeleton

- Goal: Create a minimal Supervisor routing skeleton for FAQ, RAG, web search, image understanding, Skill candidate, handoff required, and general chat decisions.
- Scope: Intent enum, deterministic rule-first router, route result schema, tests for representative inputs.
- Forbidden: Do not implement full RAG, web search, multimodal, Skill execution, or channel adapters in this task.
- Files: `backend/app/agent/supervisor.py`, `backend/app/schemas/supervisor.py`, `backend/tests/test_supervisor.py`.
- Dependencies: P0-05, P1-01, P1-03.
- Harness case requirement: Add or update Harness cases only after P0-06 exists; cases must assert route metadata rather than hard-coded final answers.
- Acceptance commands: `python3 -m pytest backend/tests/test_supervisor.py`; `python3 -m pytest`; `python3 harness/runners/run_eval.py --category regression` when P0-06 is complete.
- Definition of done: The router emits a structured route decision for each MVP intent and refuses to execute unavailable tools directly.

## Parallelization Strategy

### Parallel Group A

- Tasks: P0-02, P0-03, P0-05.
- Suggested sub agents: 3.
- Reason: These tasks touch different primary areas: backend config, deploy templates, and test infrastructure. Coordination is required for environment variable names.

### Parallel Group B

- Tasks: P0-06 and P1-01 after P0-02 and P0-05.
- Suggested sub agents: 2.
- Reason: Harness and API health chain live in separate directories and only share the service base URL contract.

### Tasks That Must Wait

- P0-04 waits for P0-02 and P0-03 because migration config depends on environment names and database service naming.
- P1-02 waits for P0-04 and P1-01 because it needs database foundations and application entry points.
- P1-03 waits for P0-02 and P1-01 because it depends on configuration and application conventions.
- P1-04 waits for P1-03 because routing must reference Model Gateway contracts without implementing provider logic.

### Parallel Risks

- `.env.example` may be modified by P0-02 and P0-03, so those sub agents must coordinate variable names before editing.
- `backend/tests/conftest.py` may be modified by P0-05, P0-04, and P1 tasks, so database fixture work must be serialized.
- Harness cases and Supervisor routing may define overlapping intent names; P0-06 should define category names before P1-04 adds route-aligned assertions.
