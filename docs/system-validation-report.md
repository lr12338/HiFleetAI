# 文档迁移说明

`docs/system-validation-report.md` 已迁移到：

- `docs/验证报告/当前系统验证报告.md`

当前系统级测试结论以新路径为准。
# 当前系统验证报告

## 1. 概述

- 验证日期：2026-06-04
- 验证目录：`/home/ecs-user/HiFleetAI`
- 验证目标：对当前 Phase 2 基线做一次可复现的系统测试与联调验证
- 验证原则：自动化优先，手工 API 与浏览器联调补充

本轮结论：

- 当前代码基线的后端、前端、Harness、认证和 `/api/v1/chat` 主链路可以跑通
- 本地浏览器联调已成功完成：`admin/admin -> Test Chat -> 会话详情`
- Ark 直连与系统内文本模型链路均已验证成功
- 知识库真实导入/索引/检索链路仍未实现，当前 FAQ 只体现为固定契约与来源结构
- Docker 基础设施和 PostgreSQL 运行时验证未完全打通，原因已在下文明确记录

## 2. 环境检查

### 2.1 基础环境

命令：

```bash
git status --short --branch
python3 --version
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest --version
node --version
npm --version
docker --version
docker compose version
```

结果：

- Python：`3.12.3`
- 项目 `.venv` 内 `pytest`：`9.0.3`
- Node：`v20.18.2`
- npm：`10.9.8`
- Docker：`28.3.3`
- Docker Compose：`v2.39.1`
- 当前分支：`feature/P0-05-pytest`
- 当前工作树：非干净，存在既有未提交改动和未跟踪目录 `HiFleetData/`

结论：

- 代码与测试环境可用
- 本轮测试是在非干净工作树上完成，报告中所有结论都应理解为“当前工作树快照下的验证结果”

风险：

- 提交前必须重新审查工作树，避免把 `.env`、`HiFleetData/`、缓存和临时产物混入版本控制

## 3. 数据库与基础设施

### 3.1 Docker 与基础设施检查

命令：

```bash
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
python3 - <<'PY'
import socket
for port in (5432, 6379, 9000, 9001, 8000, 5173):
    s = socket.socket()
    try:
        s.settimeout(0.3)
        s.connect(("127.0.0.1", port))
        print(f"{port}: OPEN")
    except Exception:
        print(f"{port}: CLOSED")
    finally:
        s.close()
PY
```

结果：

- Docker daemon：当前用户无权限访问，`docker ps` 返回 `permission denied`
- 端口状态：
  - `5432`：OPEN
  - `6379`：OPEN
  - `9000`：CLOSED
  - `9001`：CLOSED
  - `8000`：OPEN（由当前测试重新启动的后端）
  - `5173`：OPEN（前端 dev server）

结论：

- 当前机器上已有 PostgreSQL 和 Redis 可达
- MinIO 本轮未启动成功，且因 Docker 权限问题无法由本轮测试补起

风险：

- 当前不能声称“Postgres/Redis/MinIO 三件套由项目当前账号完整自举成功”

### 3.2 PostgreSQL 运行时验证

命令：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 - <<'PY'
try:
    import psycopg
    print('psycopg: OK')
except Exception as exc:
    print(f'psycopg: FAIL: {exc}')
PY
```

结果：

- `psycopg` 运行时失败，报错 `no pq wrapper available`

结论：

- 当前 `.venv` 缺少可用的 PostgreSQL 驱动实现
- 即使 `5432` 端口可达，应用内 PostgreSQL 模式也无法完成启动验证

风险：

- 若后续开发者要跑 PostgreSQL 模式，需要先补齐 `psycopg-binary` 或系统 `libpq`

### 3.3 本轮实际数据库基线

本轮最终采用：

- 数据库后端：`SQLite`
- 数据文件：`data/app-dev.db`

初始化命令：

```bash
DATABASE_BACKEND=sqlite SQLITE_DB_PATH=data/app-dev.db DATABASE_URL= \
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" alembic upgrade head
```

结果：

- Alembic 迁移执行成功

结论：

- 当前系统在 SQLite 路径下可以完成登录、会话、备注、接管、Harness API 和前端联调

## 4. 管理员账号验证

创建命令：

```bash
DATABASE_BACKEND=sqlite SQLITE_DB_PATH=data/app-dev.db DATABASE_URL= \
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" \
python3 scripts/bootstrap_local_admin.py --username admin --display-name admin --password admin
```

结果：

- 成功创建本地管理员账号
- 用户名：`admin`
- 密码：`admin`
- 角色：`admin`

说明：

- 该账号仅用于本地测试环境，不得用于生产环境

### 4.1 登录接口

命令：

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

结果：

- HTTP `200`
- 返回 `access_token`、`token_type`、`expires_in`、`user`
- `user.role == "admin"`

### 4.2 me 接口

命令：

```bash
curl -sS http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

结果：

- HTTP `200`
- 返回用户：`admin / admin / admin / active`

结论：

- 本地 `admin/admin` 登录链路可用
- 当前账号具备管理员权限

## 5. 后端与 API 验证

### 5.1 后端启动

实际启动命令：

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

说明：

- 本轮显式覆盖为 SQLite，避免终端残留的 PostgreSQL 环境变量导致服务启动失败
- `8000` 端口上的旧进程已先清理，再启动当前工作树新实例

### 5.2 健康检查

命令：

```bash
curl -i http://127.0.0.1:8000/api/health
```

结果：

- HTTP `200`
- 返回 `{"service":"HiFleetAI","status":"ok","api_version":"v1"}`

### 5.3 `/api/v1/chat`

#### regression 风格

结果：

- HTTP `200`
- `reply.content` 包含“失败原因”“不可用”
- `handoff_status == "ai_active"`
- `metadata.persistence_status == "persisted"`

#### skill 风格

结果：

- HTTP `200`
- `tool_calls[0].tool_name == "ship.position.query"`
- `tool_calls[0].status == "mocked"`
- 会话成功落库

#### FAQ 风格

结果：

- HTTP `200`
- 返回 FAQ 风格 `sources`
- 回复中包含船位查询说明

#### general_chat / Ark 风格

结果：

- HTTP `200`
- 回复内容正常返回
- 会话成功落库
- 后续直接检查 `model_calls` 表，已存在 `provider=ark`、`status=success`

结论：

- `/api/v1/chat` 的 regression、FAQ、Skill 和 general_chat 四类最小链路都已验证成功

### 5.4 Conversations / Notes / Handoff / Pause / Resume

测试结果：

- `/api/v1/conversations`：HTTP `200`
- `/api/v1/conversations/{id}`：HTTP `200`
- `/api/v1/conversations/{id}/notes` `POST`：HTTP `201`
- `/api/v1/conversations/{id}/notes` `GET`：HTTP `200`
- `/api/v1/conversations/{id}/handoff`：HTTP `200`
- `/api/v1/conversations/{id}/pause-ai`：HTTP `200`
- `/api/v1/conversations/{id}/resume-ai`：HTTP `200`

结论：

- 当前 SQLite 基线下，后台人工协同和备注 API 均可用

### 5.5 Harness Runs API

测试结果：

- `/api/v1/harness/runs`：HTTP `200`
- `/api/v1/harness/runs/{id}`：HTTP `200`
- 当前 API 返回的是最近一次 `latest.*` 对应的 report-file 结果

结论：

- Harness Results API 可用
- 但它当前主要面向“最近一次报告”，不是完整历史数据库浏览器

### 5.6 自动化验证

已执行并通过：

```bash
git status --short --branch
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
cd frontend && npm test
cd frontend && npm run build
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

结果：

- 后端专项 `pytest`：通过
- 后端全量 `pytest`：`62 passed`
- 前端 `npm test`：`17 passed`
- 前端 `npm run build`：通过
- `handoff` Harness：通过
- `regression` Harness：通过

## 6. 前端联调验证

### 6.1 前端启动

命令：

```bash
cd /home/ecs-user/HiFleetAI/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

结果：

- `http://127.0.0.1:5173/` 正常启动

### 6.2 浏览器级联调

实际验证步骤：

1. 打开登录页
2. 使用 `admin/admin` 登录
3. 进入受保护后台
4. 打开 `Test Chat`
5. 发送消息：`帮我查一下 EVER GIVEN 当前船位`
6. 收到响应
7. 点击 `Open persisted conversation`
8. 进入会话详情页并看到消息和工具调用

结果：

- 登录成功
- 后台主页显示 `Signed in as admin (admin)`
- `Test Chat` 页面可访问
- `/api/v1/chat` 请求成功
- 会话持久化成功
- 会话详情页正常展示

关键页面证据：

- 登录页标题：`Login to HiFleetAI Console`
- 后台导航：`Conversations / Test Chat / Harness Results`
- 助手响应：`已按 MVP 模式记录技能调用请求，目标关键词为 EVER GIVEN。`

结论：

- 前端代理、登录、测试会话页和会话详情跳转都已验证成功

## 7. 火山 Ark 模型验证

### 7.1 本地配置方式

本轮通过本地 `.env` 配置：

- `ARK_API_KEY`
- `ARK_BASE_URL`
- `ARK_TEXT_MODEL`
- `ARK_VISION_MODEL`

说明：

- 真实 key 只写入本地 `.env`
- 未写入 `.env.example`、README、报告正文或 git 跟踪文件

### 7.2 豆包多模态直连

命令：

```bash
curl https://ark.cn-beijing.volces.com/api/v3/responses \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...doubao multimodal payload...}'
```

结果：

- 请求成功
- 返回 `status=completed`
- 返回正文明确说明支持图片输入的是 `Doubao-Seed-1.8`

### 7.3 DeepSeek 直连

命令：

```bash
curl https://ark.cn-beijing.volces.com/api/v3/responses \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...deepseek payload...}'
```

结果：

- 请求成功
- 返回 `status=completed`
- 返回文本响应

### 7.4 系统内模型链路

验证方式：

- 启动当前工作树后端
- 发送 `general_chat` 类型问题到 `/api/v1/chat`
- 检查 `model_calls` 表

结果：

- `/api/v1/chat` 返回成功回复
- `model_calls` 表中存在 `provider=ark`、`model_name=deepseek-v4-flash-260425`、`status=success`

结论：

- Ark 文本链路已在系统内打通
- 多模态链路尚未接入到应用内 `/api/v1/chat`，当前只完成了 Ark 直连验证

风险：

- 当前环境下 PostgreSQL 驱动仍未打通，若未来切回 PostgreSQL 模式，需要重新验证系统内 Ark 链路

## 8. Hifleet 知识库验证

### 8.1 HiFleetData 当前角色

当前目录：

- `HiFleetData/raw/`：原始资料
- `HiFleetData/wiki/`：整理后的知识主题
- `HiFleetData/outputs/`：结构化问答、FAQ 检索词、JSONL 样本

结论：

- `HiFleetData/` 当前更像“知识源素材包 + 结构化候选输出”
- 不是已经接入应用检索链路的在线知识库

### 8.2 导入/索引/检索链路

检查结果：

- 仓库中未发现完整的知识库导入、索引构建、向量化检索或在线召回实现
- `backend/app/api/chat.py` 中的 FAQ 返回仍是固定契约逻辑，并未真正读取 `HiFleetData/`

结论：

- 当前不能声称“知识库已真实接通”
- 当前只能确认 FAQ 风格来源结构与 Harness 契约可工作

### 8.3 FAQ / 检索验证

已验证：

- `/api/v1/chat` FAQ 风格请求返回成功
- `sources` 中包含 FAQ 来源结构
- Harness `faq/rag/regression` 的知识使用预期仍停留在契约层

当前缺口：

1. 缺少正式导入命令
2. 缺少索引构建流程
3. 缺少向量检索或关键词检索服务
4. 缺少把 `HiFleetData/` 真正接入 `/api/v1/chat` 的代码路径

## 9. 总体结论

### 已通过

- 后端健康检查
- `admin/admin` 本地管理员账号
- 登录与 `me`
- `/api/v1/chat` 四类最小链路
- Conversations / Notes / Handoff / Pause / Resume
- Harness handoff / regression
- Harness Results API
- 前端登录联调与 Test Chat
- Ark 直连与系统内文本模型调用

### 未完全通过或存在缺口

- Docker 权限不足，无法由本轮测试直接使用 `docker compose` 自举依赖
- MinIO 本轮未启动
- PostgreSQL 模式因 `psycopg` 运行时缺少 pq wrapper 未完成应用内验证
- 知识库真实导入/索引/检索链路未实现

### 是否建议提交

- 不建议在本轮直接提交“测试已全部完成”结论
- 原因：基础设施与知识库链路仍有明确缺口，应按事实记录为“阶段性系统验证完成，存在环境与能力边界”
