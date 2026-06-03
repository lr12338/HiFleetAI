# Phase 2 Subtask Breakdown

This breakdown refines Phase 2 into single-agent tasks that fit the current execution protocol.

## P2-01 Login And Auth Foundation

### P2-01A Frontend Bootstrap

- Goal: Create the initial React + Vite admin-console app shell.
- Scope: Vite scaffold, package manifest, TypeScript config, basic app shell, route shell, test command, build command.
- Out of scope: real business pages, real auth flow, conversation UI.
- Acceptance:
  - `npm test`
  - `npm run build`

### P2-01B Backend Auth API Foundation

- Goal: Implement backend login contract and protected-user lookup.
- Scope: password hashing, JWT issuance, `/api/v1/auth/login`, `/api/v1/auth/me`, role checks, auth tests.
- Out of scope: SSO, OAuth, refresh tokens, password reset, multi-factor auth.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_auth.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`

### P2-01C Login UI And Protected Route

- Goal: Connect the frontend login page to the backend auth contract.
- Scope: login form, token persistence, auth client, protected layout route, logout action.
- Out of scope: multi-tab session sync, refresh tokens, advanced security hardening.
- Acceptance:
  - `npm test`
  - `npm run build`

## P2-02 Conversation List

### P2-02A Conversation List API

- Goal: Provide conversation list and filter API endpoints.
- Scope: list endpoint, basic status/channel search filters, response schema, tests.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_list.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`

### P2-02B Conversation List UI

- Goal: Render the admin conversation list against the API.
- Scope: table/list page, status filter, loading/error state, auth-guarded route.
- Acceptance:
  - `npm test`
  - `npm run build`

## P2-03 Conversation Detail

### P2-03A Conversation Detail API

- Goal: Return one conversation with messages, tool-call summary, and error context.
- Scope: detail endpoint, response schema, tests.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_conversation_detail.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`

### P2-03B Conversation Detail UI

- Goal: Render the detail timeline and supporting metadata.
- Scope: timeline, status panel, tool-call summary, error block, source block.
- Acceptance:
  - `npm test`
  - `npm run build`

## P2-04 Handoff And AI State

### P2-04A Handoff API

- Goal: Add backend state transitions for handoff, pause AI, and resume AI.
- Scope: API endpoints, state validation, tests, handoff Harness validation.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_handoff_api.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`
  - `python3 harness/runners/run_eval.py --category handoff`

### P2-04B Handoff UI

- Goal: Expose handoff, pause, and resume controls in the admin console.
- Scope: buttons, disabled states, status labels, mutation handling.
- Acceptance:
  - `npm test`
  - `npm run build`

## P2-05 Internal Notes

### P2-05A Notes API

- Goal: Add internal note create/list endpoints.
- Scope: backend notes schema, endpoints, tests.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_notes_api.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`

### P2-05B Notes UI

- Goal: Render internal notes in the conversation detail view.
- Scope: note list, note composer, non-user-visible UI boundary.
- Acceptance:
  - `npm test`
  - `npm run build`

## P2-06 Harness Results Page

### P2-06A Harness Results API

- Goal: Expose latest Harness run summaries and details.
- Scope: backend endpoint for report list/detail, tests.
- Acceptance:
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_harness_api.py`
  - `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`

### P2-06B Harness Results UI

- Goal: Render the Harness results page in the admin console.
- Scope: summary list, failed-case details, route protection.
- Acceptance:
  - `npm test`
  - `npm run build`

## Suggested Execution Order

1. `P2-01A` and `P2-01B` in parallel
2. `P2-01C`
3. `P2-02A` and `P2-02B`
4. `P2-03A` and `P2-03B`
5. `P2-04A` and `P2-04B`
6. `P2-05A` and `P2-05B`
7. `P2-06A` and `P2-06B`
