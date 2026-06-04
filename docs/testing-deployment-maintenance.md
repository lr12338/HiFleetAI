# 测试、部署与维护说明

## 1. 适用范围

本文面向当前 Phase 2 收口后的 HiFleetAI 基线，说明如何在本地或服务器环境中运行、测试、验证和维护系统。

## 2. 当前运行前提

### 2.1 Python 环境

当前项目默认使用仓库根目录下的 `.venv`：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

当前仓库尚未提交独立的后端依赖锁定文件，因此日常维护应优先沿用现有 `.venv`，不要在未确认前随意重建环境。

### 2.2 前端环境

前端依赖由 `frontend/package.json` 管理，使用 `npm`：

```bash
cd frontend
npm test
npm run build
```

## 3. 本地运行方式

### 3.1 启动后端

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3.2 启动前端

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 3.3 验证 Docker Compose 模板

```bash
docker compose -f deploy/docker-compose.yml config
```

当前 Compose 主要提供 PostgreSQL、Redis、MinIO 和 backend 服务拓扑模板，不要求在每次开发时都启动。

## 4. 测试命令

### 4.1 后端单测

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

### 4.2 前端测试与构建

```bash
cd frontend
npm test
npm run build
```

### 4.3 Harness

#### handoff

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
```

#### regression

`regression` 会通过 HTTP 调用 `/api/v1/chat`，因此必须确保：

- 当前工作树对应的后端服务已经启动
- `HARNESS_AGENT_BASE_URL` 指向你刚启动的那个服务

示例：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 5. 端口冲突检查

### 5.1 检查端口是否被占用

```bash
ss -ltnp
```

如果只想看某个端口，可用 Python 或手动筛选输出。

### 5.2 推荐端口

- `8000`：后端默认端口
- `5173`：前端默认开发端口
- `5432`：PostgreSQL
- `6379`：Redis
- `9000`：MinIO

### 5.3 避免 Harness 命中旧服务

如果 `8000` 已经被别的旧进程占用，不要直接复用。建议：

1. 先挑一个空闲端口启动当前工作树服务
2. 用 `HARNESS_AGENT_BASE_URL` 显式指向这个端口

示例：

```bash
python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
```

然后：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port <空闲端口>
HARNESS_AGENT_BASE_URL="http://127.0.0.1:<空闲端口>" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 6. 日常维护要点

### 6.1 先看工作树

```bash
git status --short --branch
git diff --stat
```

### 6.2 先跑最小验证再改代码

推荐顺序：

1. `python3 -m pytest backend/tests/test_chat_api.py`
2. `python3 -m pytest`
3. `npm test`
4. `npm run build`
5. `python3 harness/runners/run_eval.py --category handoff`
6. `python3 harness/runners/run_eval.py --category regression`

### 6.3 注意 `latest.*` 报告会被覆盖

`harness/reports/latest.json` 与 `latest.md` 只保留最近一次结果。需要留证时，先手动复制或归档再继续跑下一轮。

### 6.4 不要误提交本地数据

不得提交：

- `HiFleetData/`
- `.env`
- 运行日志
- 缓存目录
- `dist/`
- `node_modules/`
- `.venv/`
- 临时 Harness 报告

## 7. 常见排障

### 7.1 `regression` 返回 `Connection refused`

原因：Agent API 没启动，或者 `HARNESS_AGENT_BASE_URL` 指向了错误地址。

处理：

1. 启动当前工作树后端
2. 显式设置 `HARNESS_AGENT_BASE_URL`
3. 重跑 `regression`

### 7.2 `regression` 返回 `HTTP 404`

原因通常有两种：

- 命中了旧服务进程
- 当前服务没有正确暴露 `/api/v1/chat`

处理：

1. 检查端口占用
2. 启动一个确定属于当前工作树的新端口服务
3. 用 `HARNESS_AGENT_BASE_URL` 指向它

### 7.3 前端测试通过但页面实际数据异常

优先检查：

- 是否登录成功并拿到了 token
- `/api/v1/conversations/*` 是否可用
- `/api/v1/harness/runs*` 是否可用
- 是否误用旧后端进程

## 8. 当前维护结论

当前项目已经具备稳定的测试入口、前后端运行入口和 Harness 回归路径。后续维护最关键的是保持：

- `/api/v1/chat` 契约稳定
- Harness 不退化
- 不把旧进程误当成当前工作树服务
