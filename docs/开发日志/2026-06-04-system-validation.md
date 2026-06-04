# 2026-06-04 系统测试与交付验证日志

## 背景

- 项目：HiFleetAI
- 目录：`/home/ecs-user/HiFleetAI`
- 目标：基于当前系统测试指南，对当前代码基线做一次阶段性系统测试、联调验证与文档补齐

## 测试前观察

- 当前分支：`feature/P0-05-pytest`
- 工作树非干净，存在既有未提交改动
- `HiFleetData/` 为未跟踪本地目录，保持不纳入版本控制
- `docs/system-testing-guide.md` 与 `docs/testing-deployment-maintenance.md` 对前端 proxy 的描述曾出现不一致

## 实际动作记录

### 1. 环境检查

执行：

- `git status --short --branch`
- `python3 --version`
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest --version`
- `node --version`
- `npm --version`
- `docker --version`
- `docker compose version`

结果：

- Python、Node、npm、Docker、Docker Compose 均可执行
- 当前工作树已有未提交改动

### 2. 基础设施检查

执行：

- `docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'`
- socket 端口探测 `5432/6379/9000/9001/8000/5173`

结果：

- Docker daemon 返回 `permission denied`
- `5432`、`6379` 可达
- `9000`、`9001` 不可达

结论：

- PostgreSQL、Redis 似乎已有外部实例在运行
- MinIO 本轮不可用
- 无法确认或启动 Docker Compose 服务

### 3. PostgreSQL 运行时问题确认

执行：

- `import psycopg`
- SQLAlchemy 连接 `postgresql+psycopg://...`

结果：

- 统一失败：`no pq wrapper available`

结论：

- 当前 `.venv` 缺少可用 PostgreSQL 驱动运行时

### 4. 本地 `.env` 准备

动作：

- 创建本地 `.env`
- 写入 Ark key 与本地测试配置

注意：

- `.env` 已被 `.gitignore` 忽略
- 真实 key 未写入 git 跟踪文件

### 5. SQLite 回退并完成本轮主测试

原因：

- Docker 权限不足
- PostgreSQL 驱动运行时不可用

执行：

- `DATABASE_BACKEND=sqlite SQLITE_DB_PATH=data/app-dev.db DATABASE_URL= PATH=".../.venv/bin:$PATH" alembic upgrade head`
- `DATABASE_BACKEND=sqlite SQLITE_DB_PATH=data/app-dev.db DATABASE_URL= PATH=".../.venv/bin:$PATH" python3 scripts/bootstrap_local_admin.py --username admin --display-name admin --password admin`

结果：

- 迁移成功
- `admin/admin` 本地管理员创建成功

### 6. 后端进程处理

观察：

- 旧的 `8000`、`44571`、`44995` 端口上有残留 uvicorn 进程
- 旧 `8000` 实例 `health` 正常，但 `auth/login` 500，`chat` 仅走到 `best_effort_unavailable`

处理：

- 杀掉旧进程
- 重新启动当前工作树的 `8000` 后端，显式指定 SQLite 与本地 `.env`

结果：

- 新 `8000` 实例启动成功
- 成为本轮统一联调基线

### 7. 自动化验证

执行：

- `python3 -m pytest backend/tests/test_chat_api.py`
- `python3 -m pytest`
- `cd frontend && npm test`
- `cd frontend && npm run build`
- `python3 harness/runners/run_eval.py --category handoff`
- `HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" python3 harness/runners/run_eval.py --category regression`

结果：

- 后端专项测试通过
- 后端全量测试通过：`62 passed`
- 前端测试通过：`17 passed`
- 前端构建通过
- `handoff` 与 `regression` Harness 通过

### 8. 手工 API 验证

已验证：

- `/api/health`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/chat` regression / skill / FAQ / general_chat
- `/api/v1/conversations`
- `/api/v1/conversations/{id}`
- `/api/v1/conversations/{id}/notes`
- `/api/v1/conversations/{id}/handoff`
- `/api/v1/conversations/{id}/pause-ai`
- `/api/v1/conversations/{id}/resume-ai`
- `/api/v1/harness/runs`
- `/api/v1/harness/runs/{id}`

结果：

- 全部请求成功
- `general_chat` 经过 Ark 文本模型返回成功
- `notes / handoff / pause / resume` 均成功

### 9. Ark 验证

执行：

- 直接 curl 调用豆包多模态
- 直接 curl 调用 DeepSeek
- 发送 `general_chat` 到系统内 `/api/v1/chat`
- 读取 `data/app-dev.db` 中 `model_calls`

结果：

- 直连调用成功
- 系统内出现 `provider=ark`、`status=success` 的模型调用记录

### 10. 前端浏览器联调

执行：

- 启动 `npm run dev -- --host 127.0.0.1 --port 5173`
- 浏览器验证登录页
- 使用 `admin/admin` 登录
- 进入 `Test Chat`
- 发送消息 `帮我查一下 EVER GIVEN 当前船位`
- 点击 `Open persisted conversation`

结果：

- 页面加载成功
- 登录成功
- `Test Chat` 可发送请求
- 会话详情页成功打开

### 11. 知识库检查

执行：

- 检查 `HiFleetData/raw/`、`wiki/`、`outputs/`
- 搜索代码中的导入、索引、向量检索、知识库接入路径

结果：

- `HiFleetData/` 当前是知识源素材与结构化输出包
- 未发现完整导入/索引/检索链路
- FAQ 目前仍是契约型固定来源返回

## 本轮修订文档

- `docs/testing-deployment-maintenance.md`
- `docs/system-validation-report.md`
- `docs/dev-logs/2026-06-04-system-validation.md`
- `README.md`
- `docs/README.md`
- `docs/development-status.md`
- `docs/system-testing-guide.md`

## 最终结论

本轮系统测试完成了“自动化 + 手工 API + 浏览器联调 + Ark 直连/内链”的阶段性验证，证明当前 Phase 2 基线在 SQLite 路径下可用。

但以下缺口仍然存在：

1. Docker 权限不足，无法由本轮测试直接自举 Compose 依赖
2. MinIO 未启动
3. PostgreSQL 模式因 `psycopg` 运行时缺少 pq wrapper 未完成应用内验证
4. 知识库真实导入/索引/检索链路未完成

因此，本轮不应宣称“所有基础设施与知识库能力完全通过”，只能宣称“当前系统核心业务链路已完成阶段性验证，存在明确环境与能力边界”。
