# 后端说明

## 1. 模块定位

`backend/` 是 HiFleetAI 的 FastAPI 服务层，当前已完成 Phase 2 基线能力，能够支撑前端管理后台、Harness 评测和 `/api/v1/chat` 最小聊天链路。

当前覆盖的关键接口：

- `/api/health`
- `/api/v1/auth/*`
- `/api/v1/chat`
- `/api/v1/conversations/*`
- `/api/v1/harness/runs*`

## 2. 目录重点

- `app/api/`：HTTP 路由与依赖注入
- `app/agent/`：SupervisorRouter、ModelGateway 与 Provider
- `app/services/`：会话、Harness 等服务层
- `app/models/`：数据库模型
- `app/core/`：配置与安全相关逻辑
- `tests/`：后端 `pytest`

## 3. 当前已打通能力

- 登录与鉴权
- 会话列表与会话详情
- 内部备注
- handoff / pause-ai / resume-ai
- Harness 结果查询
- `/api/v1/chat` FAQ / Skill / regression / general_chat 最小链路

## 4. 当前限制

- 知识库真实导入 / 检索尚未接入
- 多模态尚未接入应用内 `/api/v1/chat`
- PostgreSQL 应用内验证仍受当前环境驱动阻塞

## 5. 常用命令

### 启动服务

```bash
cd /home/ecs-user/HiFleetAI
set -a
source .env
export DATABASE_BACKEND=sqlite
export SQLITE_DB_PATH=data/app-dev.db
export DATABASE_URL=
set +a
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 运行测试

```bash
cd /home/ecs-user/HiFleetAI
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

## 6. 相关文档

- `docs/系统架构说明.md`
- `docs/测试与部署维护指南.md`
- `docs/当前开发状态.md`
- `docs/验证报告/当前系统验证报告.md`
