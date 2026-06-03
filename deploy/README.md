# Deploy

Local Linux development deployment templates for HiFleetAI.

## Included Services

- `postgres`: `pgvector/pgvector:pg16` for PostgreSQL and pgvector-compatible development work
- `redis`: local cache and queue dependency
- `minio`: local object storage compatible with the current `MINIO_*` environment contract
- `backend`: dependency wiring template for the backend API service

## Configuration Validation Only

Run the acceptance command from the repository root to verify that the Compose file parses correctly:

```bash
docker compose -f deploy/docker-compose.yml config
```

This task only requires configuration validation. It does not require starting containers.

## Environment Variable Mapping

`deploy/docker-compose.yml` keeps the variable names aligned with `.env.example`, including:

- `POSTGRES_*`
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_*`
- `APP_*`
- `SECRET_KEY`
- `MODEL_PROVIDER`
- `ARK_*`
- `HARNESS_AGENT_BASE_URL`
- `HARNESS_REPORT_DIR`

The Compose file uses safe local placeholder defaults so `docker compose config` can run without production secrets.

## Backend Service Note

The `backend` service is scoped as a local wiring template. Its purpose in Phase 0 is to keep the service topology, ports, volumes, and environment mapping stable before the FastAPI runtime entrypoint is added in later tasks.

## Repository Hygiene

Do not commit runtime volumes, container caches, object storage data, or production configuration files.
