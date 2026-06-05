# Versioning Policy

This policy applies to HifleetAI Phase 0 to Phase 2 MVP development.

## Branch Naming

- `main`: stable branch, protected by review and validation.
- `feature/P0-02-config`: feature branch for a single planned task.
- `feature/P0-06-harness`: feature branch for Harness skeleton work.
- `fix/<task-id>-<short-name>`: branch for a scoped defect fix.
- `docs/<short-name>`: branch for documentation-only changes.

Rules:

1. One feature branch maps to one task whenever practical.
2. Branches must not mix unrelated Phase 0, Phase 1, and Phase 2 work.
3. Sub agents work on task branches and do not commit directly to `main`.
4. The master agent coordinates merge readiness.

## Tag Naming

- `v0.1.0-foundation`: Phase 0 foundation completed.
- `v0.2.0-agent-api`: minimal Agent API chain completed.
- `v0.3.0-agent-core`: core Agent routing, model gateway, conversation foundations completed.
- `v0.4.0-admin-console`: standard customer service admin console foundation completed.
- `v1.0.0-mvp`: MVP closed-loop acceptance completed.

Pre-release tags may use:

- `v0.1.0-rc.1`
- `v0.2.0-rc.1`

## Milestone Rules

- A milestone contains related tasks from one phase boundary.
- A milestone cannot close while required pytest or Harness commands are failing.
- A milestone must include a changelog entry with validation evidence.
- A milestone does not include real channel integrations before Phase 3.

## Commit Rules

Commit messages use:

```text
<type>(<scope>): <summary>
```

Allowed types:

- `feat`: user-visible or API capability.
- `test`: pytest, fixtures, or Harness case changes.
- `docs`: documentation.
- `chore`: repository, tooling, or non-runtime maintenance.
- `fix`: bug fix.
- `refactor`: internal restructuring without behavior change.

Examples:

- `feat(config): add backend settings loader`
- `test(harness): add initial faq case loader coverage`
- `docs(workflow): define sub-agent execution protocol`

Rules:

1. A commit should correspond to one task or one review fix.
2. Tests or Harness cases should be committed with the implementation they verify.
3. Do not mix dependency installation, formatting-only changes, and business logic in one commit.
4. Do not commit generated runtime artifacts.

## Merge To Main

Merging to `main` is allowed only when:

1. The task log exists under `docs/dev-logs/`.
2. All acceptance commands for the task have been run.
3. Failures are fixed or explicitly documented as environment blockers.
4. The change stays within the assigned MVP scope.
5. The diff contains no secrets, caches, logs, uploads, object storage files, or real customer data.
6. The master agent or human maintainer approves the merge.

## Tagging

A tag is allowed only when:

1. All tasks in the milestone are complete.
2. The repository is clean except intentionally untracked local data.
3. `CHANGELOG.md` contains the milestone entry.
4. Required pytest and Harness commands pass or documented infrastructure blockers are accepted by the maintainer.
5. The tag points to a commit already merged into `main`.

## Files That Must Not Be Committed

- `.env`
- `.env.*` except `.env.example`
- API keys, tokens, cookies, SSH private keys, TLS private keys
- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- `.venv/`
- `node_modules/`
- `dist/`
- `build/`
- `.vite/`
- `*.log`
- runtime logs outside curated `docs/dev-logs/`
- `uploads/`
- object storage files
- PostgreSQL data directories
- Redis dump files
- MinIO volumes
- generated embeddings
- generated Harness reports except `harness/reports/README.md`
- real customer data
- production configuration files

## Remote Policy

The preferred remote URL for this server is SSH:

```text
git@github.com:lr12338/HiFleetAI.git
```

HTTPS remotes can fail in non-interactive server sessions because Git cannot prompt for GitHub credentials.
