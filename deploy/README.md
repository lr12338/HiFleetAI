# 部署说明

## 1. 模块定位

`deploy/` 存放本地 Linux 开发环境的 Compose 模板与基础依赖编排说明，目标是保持 PostgreSQL、Redis、MinIO 与后端服务的环境映射一致。

## 2. 当前包含服务

- `postgres`
- `redis`
- `minio`
- `backend`

## 3. 配置校验

从仓库根目录执行：

```bash
docker compose -f deploy/docker-compose.yml config
```

这一步用于验证 Compose 文件结构和环境变量映射是否正确。

## 4. 按需启动依赖

如果当前环境具备 Docker daemon 权限，可按需启动：

```bash
docker compose -f deploy/docker-compose.yml up -d postgres redis minio
docker compose -f deploy/docker-compose.yml ps
```

## 5. 当前环境限制

最近一轮系统验证中已确认：

- 当前账号访问 Docker daemon 时可能出现 `permission denied`
- MinIO 未在该轮验证中成功启动
- PostgreSQL 虽然端口可达，但应用内仍可能受 `psycopg` 运行时问题影响

因此，当前推荐的本地完整联调基线仍然是 SQLite。

## 6. 环境变量映射

`deploy/docker-compose.yml` 与 `.env.example` 保持同名变量映射，主要包括：

- `POSTGRES_*`
- `DATABASE_BACKEND`
- `SQLITE_DB_PATH`
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_*`
- `APP_*`
- `SECRET_KEY`
- `MODEL_PROVIDER`
- `ARK_*`
- `HARNESS_AGENT_BASE_URL`
- `HARNESS_REPORT_DIR`

## 7. 说明

- Compose 中的 `backend` 主要用于保持本地服务拓扑与环境映射稳定
- 容器化路径默认会切换到 PostgreSQL 模式
- 仓库中不得提交运行时卷、对象存储数据、缓存或生产配置

## 8. 相关文档

- `docs/测试与部署维护指南.md`
- `docs/验证报告/当前系统验证报告.md`
