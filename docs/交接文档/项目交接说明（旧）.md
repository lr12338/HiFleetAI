# Agent 交接说明

## 1. 当前状态

当前仓库已经完成 Phase 2 收口，可以把它视为一个“已通过验证的标准客服后台 MVP 基线”。

当前已完成：

- 登录与鉴权
- 会话列表
- 会话详情
- 人工接管
- AI 暂停 / 恢复
- 内部备注
- Harness 结果页
- `/api/v1/chat` MVP 契约
- `pytest` 与 Harness 核心回归通过

## 2. 关键目录

- `backend/`：FastAPI 后端
- `frontend/`：React 管理后台
- `harness/`：回归测试工程
- `docs/`：当前交付文档、开发状态、交接材料
- `deploy/`：本地依赖模板

## 3. 关键文件

### 后端

- `backend/app/main.py`
- `backend/app/api/__init__.py`
- `backend/app/api/chat.py`
- `backend/app/api/conversations.py`
- `backend/app/api/harness.py`
- `backend/app/agent/supervisor.py`
- `backend/app/agent/model_gateway.py`
- `backend/app/services/conversation_service.py`

### 前端

- `frontend/src/App.tsx`
- `frontend/src/conversation-list-page.tsx`
- `frontend/src/conversation-detail-page.tsx`
- `frontend/src/harness-results-page.tsx`

### Harness

- `harness/runners/run_eval.py`
- `harness/judges/deterministic_judge.py`
- `harness/cases/*.jsonl`

## 4. 接手后必须先跑的验证

建议按以下顺序执行：

```bash
git status --short --branch
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
cd frontend && npm test && npm run build
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
```

如果需要验证 `regression`：

1. 先启动当前工作树后端服务
2. 用 `HARNESS_AGENT_BASE_URL` 显式指向该服务
3. 再跑 `regression`

## 5. 当前边界

以下范围当前不能碰，除非明确获批进入新阶段：

- 微信公众号真实接入
- Chatwoot 真实接入
- 微信客服平台真实接入
- 文件分析沙箱
- 订阅通知
- 高风险生产写操作
- 伪造 Harness 成功
- 跳过 `pytest` / Harness 直接宣称完成

## 6. 当前最需要保持稳定的部分

- `/api/v1/chat` 契约
- `SupervisorRouter` 路由规则
- `ModelGateway` 结构化失败行为
- handoff 状态迁移
- Harness runner 与 deterministic judge

## 7. 工作树注意事项

- `HiFleetData/` 是本地未跟踪目录，不能提交
- `harness/reports/latest.*` 是临时报告，会被覆盖，不能作为稳定产物提交
- 如果端口被旧服务占用，不要假设 `localhost:8000` 就是当前工作树服务

## 8. 下一步建议

后续 Agent 接手时，不要立刻大改代码。正确顺序应该是：

1. 读文档
2. 跑验证
3. 看工作树
4. 基于 Phase 3 规划拆任务
5. 再做单任务实现

## 9. 必读文档

- `HiFleetAI开发方案.md`
- `Harness驱动开发规范.md`
- `docs/system-overview.md`
- `docs/architecture-overview.md`
- `docs/testing-deployment-maintenance.md`
- `docs/development-status.md`
- `docs/phase2-closeout.md`

## 10. 交接结论

当前项目不是“待抢救的候选分支”，而是“Phase 2 已通过验证、可交付、可继续规划 Phase 3”的稳定基线。后续工作重点应转向渠道规划、契约设计和测试先行，而不是继续补已有 Phase 2 页面。
