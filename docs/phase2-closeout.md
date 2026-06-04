# Phase 2 收口文档

## 1. 结论

Phase 2 已完成。

判断依据：

- 后台标准能力已经全部到位
- `/api/v1/chat` MVP 契约已补齐
- `backend/tests/test_chat_api.py` 通过
- 全量 `pytest` 通过
- 前端 `npm test` 与 `npm run build` 通过
- Harness `handoff` 与 `regression` 已通过

## 2. 本阶段目标

Phase 2 的目标是把系统从“仅有 Agent 核心链路”推进到“可试用的 AI + 人工客服工作台”。

本阶段交付重点：

- 登录与权限
- 会话列表
- 会话详情
- 人工接管
- AI 暂停 / 恢复
- 内部备注
- Harness 结果页
- Agent API 与 Harness 回归闭环

## 3. 已完成任务

### 后端

- 鉴权 API
- 会话列表 API
- 会话详情 API
- handoff / pause-ai / resume-ai API
- 内部备注 API
- Harness 结果 API
- `/api/v1/chat` MVP 响应契约

### 前端

- 登录页与受保护路由
- 会话列表页
- 会话详情页
- handoff / pause / resume 控件
- 内部备注区块
- Harness 结果页

### 测试与验证

- `backend/tests/test_auth.py`
- `backend/tests/test_conversation_list.py`
- `backend/tests/test_conversation_detail.py`
- `backend/tests/test_handoff_api.py`
- `backend/tests/test_notes_api.py`
- `backend/tests/test_harness_api.py`
- `backend/tests/test_chat_api.py`
- 前端单测与构建
- Harness handoff / regression

## 4. 关键文件

### 后端关键文件

- `backend/app/main.py`
- `backend/app/api/__init__.py`
- `backend/app/api/auth.py`
- `backend/app/api/chat.py`
- `backend/app/api/conversations.py`
- `backend/app/api/harness.py`
- `backend/app/agent/supervisor.py`
- `backend/app/agent/model_gateway.py`
- `backend/app/services/conversation_service.py`
- `backend/app/services/harness_service.py`

### 前端关键文件

- `frontend/src/App.tsx`
- `frontend/src/conversation-list-page.tsx`
- `frontend/src/conversation-detail-page.tsx`
- `frontend/src/harness-results-page.tsx`
- `frontend/src/conversations-client.ts`
- `frontend/src/harness-client.ts`

### 测试与 Harness 关键文件

- `backend/tests/test_chat_api.py`
- `backend/tests/test_handoff_api.py`
- `backend/tests/test_notes_api.py`
- `backend/tests/test_harness_api.py`
- `frontend/src/test/App.test.tsx`
- `harness/runners/run_eval.py`
- `harness/judges/deterministic_judge.py`
- `harness/cases/*.jsonl`

## 5. 验证命令

### 后端

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
```

### 前端

```bash
cd frontend
npm test
npm run build
```

### Harness

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category handoff
HARNESS_AGENT_BASE_URL="http://127.0.0.1:8000" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 6. 本阶段关键改动摘要

- 补齐了后台登录、会话、接管、备注、Harness 结果查看能力
- 将 AI 暂停 / 恢复纳入 handoff 状态链路
- 在前端后台中打通了受保护路由与管理视图
- 对齐了 Harness 依赖的 `/api/v1/chat` 契约
- 将 regression Harness 从 `404` 阻塞状态推进到真实通过

## 7. 遗留风险

以下风险不会阻止 Phase 2 完成结论，但后续开发必须注意：

- `/api/v1/chat` 当前是 MVP 级实现，不是完整生产编排引擎
- 真实知识检索、真实网页检索、真实多模态、真实 Skill 执行尚未接入
- 后端依赖当前主要沉淀在本地 `.venv`，维护时要避免环境漂移
- `HiFleetData/` 为本地未跟踪目录，不能混入提交
- Harness `latest.*` 会被覆盖，调试时要主动保存证据

## 8. 本阶段对应日志

- `docs/dev-logs/2026-06-03-master-log.md`
- `docs/dev-logs/P2-01-*.md`
- `docs/dev-logs/P2-02*.md`
- `docs/dev-logs/P2-03*.md`
- `docs/dev-logs/P2-04*.md`
- `docs/dev-logs/P2-05A-notes-api.md`
- `docs/dev-logs/P2-05B-notes-ui.md`
- `docs/dev-logs/P2-06A-harness-api.md`
- `docs/dev-logs/P2-06B-harness-results-ui.md`

## 9. Phase 2 是否完成

结论：已完成。

完成定义满足情况：

- 标准客服后台已具备可试用工作台能力
- Harness 验证链路可运行
- 回归基线已通过
- 前后端主要功能均有自动化验证
- 交付文档与交接材料已补齐
