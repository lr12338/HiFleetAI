# P2-01C Login UI and protected route

## Task Metadata

- Task ID: P2-01C
- Executor: sub-agent-phase2-login-ui
- Phase: Phase 2
- Requirement Section: `docs/phase2-subtasks.md` P2-01C Login UI And Protected Route; `HiFleetAI开发方案.md` 7.2 页面清单
- Start Time: 2026-06-03T21:20:00+08:00
- End Time: 2026-06-03T21:25:11+08:00
- Status: review

## Scope

- Goal: Connect the frontend login page to the backend auth contract with token persistence, protected routing, and a minimal logout flow.
- In Scope: login page, auth client for `/api/v1/auth/login` and `/api/v1/auth/me`, local-storage access token persistence, protected route shell, logout action, frontend route test coverage, task-board status update, and task log.
- Out Of Scope: refresh tokens, SSO, OAuth, enterprise WeChat login, MFA, multi-tab session sync, conversation list/detail pages, handoff UI, notes UI, Harness results UI, real channel integration, and production write actions.
- Dependencies: P2-01A frontend bootstrap and P2-01B backend auth API foundation.

## Modified Files

- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/auth-client.ts`
- `frontend/src/auth.tsx`
- `frontend/src/styles.css`
- `frontend/src/test/App.test.tsx`
- `docs/task-board.md`
- `docs/dev-logs/P2-01C-login-ui.md`

## Harness Cases

No Harness case was added for P2-01C. Validation is frontend command based because this task only connects the login UI and protected-route shell.

## Acceptance Commands

- `npm test`
- `npm run build`

## Test Results

- `npm test`: passed with `2 passed` in Vitest.
- `npm run build`: passed with Vite production output emitted to `frontend/dist`.
- The first `jsdom` installation pulled version `27.0.1`, which exposed an upstream compatibility problem with local Node `v20.18.2` during Vitest worker startup. The task was corrected by installing compatible `jsdom@26.1.0`, after which the acceptance test command passed normally.

## Risks And Remaining Issues

- The frontend now guards the shell and persists the access token in local storage, but it still relies on the minimal backend JWT contract only. Refresh tokens, stronger session hardening, and cross-tab sync remain intentionally out of scope.
- The protected shell currently contains only a minimal authenticated placeholder. Later Phase 2 tasks must replace it with conversation list, detail, handoff, notes, and Harness pages without widening this task retroactively.
- The current branch is `feature/P0-05-pytest`, not a dedicated `P2-01C` task branch, so final branch hygiene remains a coordination item for the master agent.

## Next Stage Readiness

P2-01C may enter review. The login page exists, unauthenticated access is redirected to `/login`, successful auth stores the access token and restores the protected shell through `/api/v1/auth/me`, logout clears the token, the task-board entry is updated to `review`, and both acceptance commands pass.
