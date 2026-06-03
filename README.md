# HiFleetAI

Hifleet enterprise customer service Agent platform.

This repository is initialized for Harness-driven development. The MVP scope is limited to:

- built-in admin console test sessions
- Agent API
- Harness evaluation
- standard customer service admin console

The first phase does not include WeChat Official Account, Chatwoot, WeChat Customer Service, production write operations, subscription notifications, or file-analysis sandbox capabilities.

## Development Rule

Every feature task must follow:

```text
requirement section -> small task -> Harness case -> pytest / eval runner -> implementation -> verification -> report
```

No task is complete without executable verification evidence.

## Current Foundation

- Backend: `backend/`
- Frontend: `frontend/`
- Harness: `harness/`
- Deployment templates: `deploy/`
- Documentation: `docs/`
- Scripts: `scripts/`
- Cross-module tests: `tests/`
- Local runtime data: `data/`

## Security

Do not commit `.env`, API keys, tokens, logs, caches, uploads, or database volumes.
