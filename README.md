# HiFleetAI

HiFleetAI 是一个面向企业客服场景的 Agent 平台。当前仓库已经完成 Phase 2 收口，可作为“后台测试会话 + Agent API + Harness 回归 + 标准客服工作台”的 MVP 基线继续开发。

项目当前坚持以下边界：

- 只做自建标准客服后台与内置测试会话
- 统一使用 `/api/v1/chat` 作为 Agent 聊天入口
- 所有核心交付必须有 `pytest` 或 Harness 证据
- 不接入真实微信公众号、Chatwoot、微信客服平台
- 不接入高风险生产写操作、订阅通知、文件分析沙箱

仓库当前没有单独的 `需求重构方案.md`，实际以根目录的 `HiFleetAI开发方案.md` 作为需求主文档，`Harness驱动开发规范.md` 作为开发质量基线。

## 当前阶段

- 当前阶段：Phase 2 已完成收口
- 当前能力：登录与鉴权、会话列表、会话详情、人工接管、AI 暂停/恢复、内部备注、Harness 结果页、`/api/v1/chat` MVP 响应契约、Harness 回归链路
- 下一阶段：进入 Phase 3 规划与渠道接入准备，而不是继续扩展 Phase 2

## 目录结构

```text
backend/    FastAPI 后端、认证、会话、Harness API、/api/v1/chat
frontend/   React + Vite 管理后台
harness/    用例、runner、judge、报告
docs/       交付文档、计划、状态、交接材料
deploy/     Docker Compose 本地依赖模板
data/       本地运行数据目录
tests/      跨模块说明与辅助测试目录
```

## 5 分钟快速了解

1. 先读 `HiFleetAI开发方案.md` 了解目标、MVP 边界与阶段路线图。
2. 再读 `Harness驱动开发规范.md`，确认“不跑测试不算完成”的开发规则。
3. 打开 `docs/system-overview.md`、`docs/architecture-overview.md`、`docs/development-status.md`，快速建立当前系统全貌。
4. 运行 `python3 -m pytest` 与 Harness 回归命令，确认本地工作树状态和运行基线。

## 本地运行

### 后端 API

当前仓库默认沿用项目根目录的 `.venv` 环境运行后端：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 前端后台

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 本地依赖模板

需要验证 PostgreSQL / Redis / MinIO 配置时：

```bash
docker compose -f deploy/docker-compose.yml config
```

当前 Phase 2 的大多数测试不依赖真实本地数据库服务；`pytest` 已通过测试夹具隔离了运行环境。

## 测试与 Harness

### 后端测试

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

### 前端测试与构建

```bash
cd frontend
npm test
npm run build
```

### Harness 回归

`handoff` 类别可直接运行；`regression` 类别建议指向一个明确由当前工作树启动的本地 API：

```bash
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
```

如果 `localhost:8000` 已被其他旧进程占用，请先换一个空闲端口启动当前工作树服务，再显式设置 `HARNESS_AGENT_BASE_URL`。

## 文档索引

- `HiFleetAI开发方案.md`：需求主文档与阶段路线图
- `Harness驱动开发规范.md`：Harness 驱动开发规则
- `docs/system-overview.md`：系统目标、MVP 范围、当前已实现能力
- `docs/architecture-overview.md`：系统架构、模块关系、关键链路
- `docs/testing-deployment-maintenance.md`：运行、测试、部署、排障说明
- `docs/development-status.md`：阶段进展与下一阶段建议
- `docs/phase2-closeout.md`：Phase 2 收口总结
- `docs/agent-handoff.md`：给后续开发 Agent 的交接材料
- `docs/next-agent-prompt.md`：可直接复制给下一位 Agent 的提示词

## 开发规则

每个功能任务都必须遵循以下顺序：

```text
需求章节 -> 小任务 -> 测试 / Harness case -> 最小实现 -> 验证 -> 记录 -> 复审
```

以下情况不得声称完成：

- 没有运行 `pytest`
- 没有运行对应 Harness
- 外部依赖不可用却伪装成功
- 超出当前 MVP 范围

## 安全与提交约束

以下内容不得混入提交：

- `HiFleetData/`
- `.env` 与真实密钥
- 运行日志、缓存、上传文件
- `node_modules/`、`dist/`、`.venv/`
- Harness 临时报告文件
