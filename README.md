# HiFleetAI

HiFleetAI 是一个面向企业客服场景的 Agent 平台。当前仓库已经完成 Phase 2 收口，并补齐了“登录 -> Test Chat -> 会话详情”的本地最小体验闭环，可作为后续 Phase 3 规划与渠道接入准备的稳定基线。

## 当前边界

- 只做自建标准客服后台与内置测试会话
- 统一使用 `/api/v1/chat` 作为 Agent 聊天入口
- 所有核心交付必须有 `pytest`、前端测试或 Harness 证据
- 不接入真实微信公众号、Chatwoot、微信客服平台
- 不接入高风险生产写操作、订阅通知、文件分析沙箱

需求主文档与质量基线仍以以下文件为准：

- `HiFleetAI开发方案.md`
- `Harness驱动开发规范.md`

## 当前阶段

- 当前阶段：Phase 2 已完成收口
- 当前能力：登录鉴权、会话列表、会话详情、人工接管、AI 暂停/恢复、内部备注、Harness 结果页、`/api/v1/chat`、前端 `Test Chat`
- 当前建议：先补环境与知识库链路，再进入 Phase 3

## 仓库结构

```text
backend/    FastAPI 后端、认证、会话、Harness API、/api/v1/chat
frontend/   React + Vite 管理后台
harness/    用例、runner、judge、报告
docs/       主文档、验证报告、交接文档、开发日志、历史归档
deploy/     Docker Compose 本地依赖模板
scripts/    管理员初始化等辅助脚本
data/       本地运行数据目录
```

## 10 分钟上手

1. 阅读 `docs/README.md`
2. 阅读 `docs/项目总览与开发方案.md`
3. 阅读 `docs/系统架构说明.md`
4. 阅读 `docs/当前开发状态.md`
5. 按 `docs/测试与部署维护指南.md` 启动和验证本地环境

## 本地运行

### 后端

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

### 前端

```bash
cd /home/ecs-user/HiFleetAI/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

当前前端已配置 Vite dev proxy，浏览器中的 `/api/*` 请求会转发到 `127.0.0.1:8000`。

## 测试命令

### 后端

```bash
cd /home/ecs-user/HiFleetAI
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

### 前端

```bash
cd /home/ecs-user/HiFleetAI/frontend
npm test
npm run build
```

### Harness

```bash
cd /home/ecs-user/HiFleetAI
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 文档入口

- `docs/README.md`：文档索引
- `docs/项目总览与开发方案.md`：项目定位、范围、目录结构与开发方向
- `docs/系统架构说明.md`：当前系统结构与关键链路
- `docs/开发规范.md`：开发流程、提交规范、Agent 协作规则
- `docs/测试与部署维护指南.md`：运行、联调、测试与排障入口
- `docs/当前开发状态.md`：当前能力、阻塞与下一步建议
- `docs/验证报告/当前系统验证报告.md`：最近一轮系统级验证结论
- `docs/交接文档/项目交接说明.md`：后续开发接手说明

## 当前已知环境边界

最近一轮系统验证已明确：

- SQLite 基线可复现完整联调
- Ark 文本模型链路可用
- PostgreSQL 应用内验证仍受 `psycopg` 运行时问题阻塞
- Docker Compose 自举受当前账号 Docker 权限限制
- `HiFleetData/` 仍未真正接入知识库检索链路

## 提交约束

以下内容不得混入提交：

- `HiFleetData/`
- `.env` 与真实密钥
- 运行日志、缓存、上传文件
- `node_modules/`、`dist/`、`.venv/`
- Harness 临时报告文件
