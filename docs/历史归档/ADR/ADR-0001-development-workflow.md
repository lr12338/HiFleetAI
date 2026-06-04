# ADR-0001: Master Agent, Sub Agents, And Harness-Driven Workflow

## Status

Accepted

## Context

HifleetAI is an enterprise customer service Agent platform. The MVP must keep scope limited to built-in admin console test sessions, Agent API, Harness, and standard customer service admin console foundations. The project must not expand into real WeChat Official Account, Chatwoot, WeChat Customer Service, production business writes, subscription notifications, or file-analysis sandbox work during Phase 0 to Phase 2.

The project requires repeatable quality evidence because apparent chat success is not a sufficient delivery standard. Model calls, RAG, Skill behavior, and handoff behavior can regress when prompts, providers, knowledge sources, or routing logic change.

## Decision

The project will use a master-agent plus sub-agent workflow:

1. The master agent owns task decomposition, dependency ordering, status tracking, review coordination, and final reporting.
2. Each sub agent executes one task only.
3. Every task must define scope, forbidden work, files, dependencies, Harness requirements, pytest or eval acceptance commands, and definition of done.
4. Development follows Harness-driven rules: case or validation first, implementation second, verification third, report fourth.
5. Sub agents must write task logs under `docs/dev-logs/` before a task can enter review.
6. Sub agents do not commit directly to `main`.

## Consequences

- Work can be parallelized across independent directories such as `harness/`, `deploy/`, and backend test scaffolding.
- Tasks that share files such as `.env.example`, `backend/tests/conftest.py`, and database migration configuration must be serialized or coordinated by the master agent.
- The repository gains additional process documentation, but this creates useful audit evidence for production-grade Agent development.
- Failed tests, missing credentials, unavailable services, and failed Harness cases remain visible instead of being hidden by manual summaries.

## Quality Rules

- Deterministic Harness judges are preferred before LLM judges.
- Mock Skill execution must go through Skill Hub and be marked as mock.
- Real provider credentials must remain outside Git.
- No channel adapter may bypass the Agent API.
- No task may be marked complete without acceptance command evidence or a documented environment blocker.
