# Tests

Cross-module tests and shared test fixtures.

Backend-specific tests may live under `backend/tests/` once the backend application is created.

## Backend Pytest Entry

Run backend tests from the repository root:

```bash
python3 -m pytest
```

The P0-05 smoke suite lives under `backend/tests/` and uses local pytest fixtures only. It does not require model APIs, databases, object storage, network access, Docker services, or Harness runner execution.
