# HifleetAI Phase 2 Context Snapshot

This document compresses the repository state before Phase 2 execution so later agents and maintainers can recover context without replaying the full chat history.

## Scope Boundary

The project remains restricted to MVP Phase 0 through Phase 2.

Still excluded:

- real WeChat Official Account integration
- real Chatwoot integration
- real WeChat Customer Service integration
- production business writes
- subscription notifications
- file-analysis sandbox
- other high-risk production execution paths

## Repository Status

- Repository root: `/home/ecs-user/HiFleetAI`
- Active branch: `feature/P0-05-pytest`
- Remote policy: SSH remote is preferred
- Local-only untracked data directory: `HiFleetData/`
- Local Python runtime: system `python3` plus project `.venv`
- Local frontend toolchain: Node.js and npm available

## Completed Work

### Phase 0

- `P0-02` configuration system and `.env.example` alignment
- `P0-03` Docker Compose templates for `postgres`, `redis`, `minio`, and `backend`
- `P0-04` SQLAlchemy and Alembic foundation with initial schema migration
- `P0-05` pytest foundation and local test fixtures
- `P0-06` Harness skeleton with deterministic judge, JSONL cases, and failure-report output

### Phase 1

- `P1-01` FastAPI application entry with `GET /api/health`
- `P1-02` `ConversationService` for `console` conversations and timeline reads
- `P1-03` provider-neutral `ModelGateway` with `fake` and `ark` failure-safe behavior
- `P1-04` deterministic `SupervisorRouter` with route-only decisions for MVP intents

## Current Validation Baseline

The latest verified backend validation state before Phase 2 is:

- full pytest suite passes
- migration test passes
- Harness list-cases passes
- Harness `faq` and `regression` runs produce structured failure when `/api/v1/chat` is unavailable

Known non-blocking warning:

- `StarletteDeprecationWarning` from `fastapi.testclient`

## Backend Foundation Available For Phase 2

- shared settings loader in `backend/app/core/config.py`
- database engine and session helpers in `backend/app/db/`
- ORM models in `backend/app/models/`
- FastAPI app entry in `backend/app/main.py`
- API router entry in `backend/app/api/__init__.py`
- health endpoint in `backend/app/api/health.py`
- model gateway in `backend/app/agent/model_gateway.py`
- supervisor router in `backend/app/agent/supervisor.py`
- conversation service in `backend/app/services/conversation_service.py`

## Frontend Status

- `frontend/` currently contains only a README
- no Vite app, routing, test runner, or build pipeline has been created yet
- Phase 2 must therefore start by bootstrapping the frontend while keeping the auth and admin-console scope minimal

## Agreed Minimal Auth Scheme

Phase 2 login and auth use:

- backend JWT bearer auth
- local admin / agent / viewer style roles
- frontend login page that stores a short-lived access token
- no SSO, OAuth, WeChat auth, MFA, or refresh-token complexity in the initial MVP

## Phase 2 Execution Rules

- one sub-agent executes exactly one task
- test or validation first, implementation second
- each task must update `docs/task-board.md`
- each task must write one task log in `docs/dev-logs/`
- master agent re-runs acceptance commands before commit
- no direct commits to `main`

## Phase 2 Risks To Track

- frontend bootstrap does not yet exist
- backend auth depends on extending the current schema safely
- `/api/v1/chat` is still unimplemented, so Harness end-to-end success remains unavailable
- `HiFleetData/` must stay outside commits unless explicitly approved later

## Recommended Next Order

1. bootstrap frontend app shell and local test/build pipeline
2. implement backend auth foundation and JWT issuance
3. connect login UI to auth API and protected routes
4. expose conversation list/detail APIs
5. add handoff, pause/resume, notes, and Harness results views
