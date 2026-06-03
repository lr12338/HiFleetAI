# Development Log Rules

Development logs provide audit evidence for master-agent coordination, sub-agent execution, test results, and Harness outcomes.

## File Layout

- Master log: `docs/dev-logs/YYYY-MM-DD-master-log.md`
- Task log: `docs/dev-logs/<task-id>-<short-name>.md`

Examples:

- `docs/dev-logs/2026-06-03-master-log.md`
- `docs/dev-logs/P0-06-harness.md`
- `docs/dev-logs/P1-03-model-gateway.md`

## Master Log Format

Each master log must include:

```text
# YYYY-MM-DD Master Log

## Summary

## Repository State

## Task Dispatch

## Reviews

## Validation Evidence

## Risks And Decisions

## Next Actions
```

## Task Log Format

Each task log must include:

```text
# <Task ID> <Task Name>

## Task Metadata

- Task ID:
- Executor:
- Phase:
- Requirement Section:
- Start Time:
- End Time:
- Status:

## Scope

- Goal:
- In Scope:
- Out Of Scope:
- Dependencies:

## Modified Files

## Harness Cases

## Acceptance Commands

## Test Results

## Risks And Remaining Issues

## Next Stage Readiness
```

## Required Fields

Every task log must record:

1. Task ID.
2. Executor.
3. Start time.
4. End time.
5. Modified files.
6. Acceptance commands.
7. Test results.
8. Risks and remaining issues.
9. Whether the task may enter the next stage.

## Logging Rules

1. A task is not complete until its task log exists.
2. Failed commands must be recorded with the failing command and summarized error.
3. Skipped commands must include the reason.
4. Environment blockers must not be reported as success.
5. Logs must not include API keys, tokens, cookies, private customer data, or production credentials.
6. Generated runtime logs are not committed; only curated development logs under this directory are committed.
