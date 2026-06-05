# Agent Execution Protocol

This protocol applies to the master agent and every sub agent working on HifleetAI.

## Scope Control

1. A sub agent executes exactly one assigned task.
2. The task must map to a documented requirement section and a task ID in `docs/task-board.md`.
3. The sub agent must not expand beyond the assigned scope.
4. Phase 0 to Phase 2 MVP work excludes real WeChat Official Account integration, Chatwoot integration, WeChat Customer Service integration, production business writes, subscription notifications, and file-analysis sandbox work.

## Required Start Statement

Before editing files, a sub agent must state:

1. Task ID and task name.
2. Requirement document section.
3. Goal.
4. In-scope files.
5. Out-of-scope items.
6. Required tests or Harness cases.
7. Acceptance commands.

## Test-First Rule

1. A sub agent must write a test, a Harness case, or a documented validation method before implementation.
2. If a task is infrastructure-only, the validation method must be an executable command.
3. Harness work must use deterministic checks first.
4. Unit tests must not depend on live model API calls.

## Completion Rule

Before a task is marked complete, the sub agent must:

1. Run every acceptance command listed for the task.
2. Record the command output summary in a task log under `docs/dev-logs/`.
3. List all modified files.
4. Report failed tests, skipped commands, and environment blockers exactly as observed.
5. State whether the task can enter review or remains blocked.

## Git Rule

1. Sub agents must not commit directly to `main`.
2. Feature branches use the naming rules in `docs/versioning-policy.md`.
3. The master agent coordinates review, merge readiness, and push decisions.
4. Secrets, caches, logs, uploads, object storage files, and real customer data must never be committed.

## Integrity Rule

1. Do not fake model, knowledge, Skill, database, or Harness success.
2. Do not hard-code fixed answers to pass Harness cases.
3. Do not create fake `tool_calls` or `retrieval_logs`.
4. Missing API keys, unavailable databases, unavailable object storage, failed tests, and failed Harness cases must be reported as blockers or failures.
5. Mock Skill execution is allowed only when routed through Skill Hub and clearly marked as mock.
