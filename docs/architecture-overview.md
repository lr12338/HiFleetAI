# 架构概览

## 1. 架构目标

当前架构的目标不是一次性做成完整多渠道生产系统，而是先建立一个可验证、可扩展、可回归的客服 Agent 平台基线。核心原则是：

- 后台与后续渠道统一走 Agent API
- 能力扩展通过 Supervisor、Model Gateway、Skill / Knowledge / Harness 分层完成
- 所有关键路径都能被 `pytest` 和 Harness 验证

## 2. 当前总体结构

```mermaid
flowchart LR
    FE[前端管理后台 React/Vite] --> AUTH[/api/v1/auth/*/]
    FE --> CONV[/api/v1/conversations/*/]
    FE --> HARNESS[/api/v1/harness/runs*]
    FE --> CHAT[/api/v1/chat]

    HARNESS_RUNNER[Harness runner] --> CHAT
    HARNESS_RUNNER --> HANDOFF_API[handoff in-process API]

    CHAT --> SUPERVISOR[SupervisorRouter]
    CHAT --> GATEWAY[Model Gateway]

    SUPERVISOR --> FAQ[FAQ / 知识路由]
    SUPERVISOR --> SKILL[Skill 候选路由]
    SUPERVISOR --> WEB[网页检索路由占位]
    SUPERVISOR --> HANDOFF[人工接管路由]

    CONV --> CONV_SERVICE[ConversationService]
    CONV_SERVICE --> DB[(会话/消息/备注/接管状态)]

    HARNESS --> HARNESS_SERVICE[HarnessResultService]
    HARNESS_SERVICE --> REPORTS[harness/reports/latest.*]
    HARNESS_SERVICE --> DB
```

## 3. Backend 当前状态

### 3.1 API 层

后端入口在 `backend/app/main.py`，路由统一通过 `backend/app/api/__init__.py` 组织。

当前关键 API：

- `/api/health`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/chat`
- `/api/v1/conversations`
- `/api/v1/conversations/{id}`
- `/api/v1/conversations/{id}/handoff`
- `/api/v1/conversations/{id}/pause-ai`
- `/api/v1/conversations/{id}/resume-ai`
- `/api/v1/conversations/{id}/notes`
- `/api/v1/harness/runs`
- `/api/v1/harness/runs/{run_id}`

### 3.2 `/api/v1/chat`

`/api/v1/chat` 是当前统一聊天入口，也是 Harness 直接调用的主链路。当前实现重点是“满足 MVP 响应契约并保持结构可验证”，而不是完整生产对话引擎。

它当前完成的事情：

- 接收标准化聊天请求
- 调用 `SupervisorRouter` 进行规则优先路由
- 根据不同意图生成最小结构化响应
- 在 general chat 分支下调用 `ModelGateway`
- 保证返回 `conversation_id`、`message_id`、`reply`、`handoff_status`、`tool_calls`、`sources`

它当前没有做的事情：

- 不做真实知识检索执行
- 不做真实网页检索执行
- 不做真实多模态推理
- 不做真实 Skill 服务调用
- 不做完整会话落库闭环

## 4. Supervisor 路由

`backend/app/agent/supervisor.py` 负责最小规则优先路由。当前可识别：

- FAQ
- Skill 候选
- Web Research
- Image Understanding
- Handoff Required
- General Chat

Supervisor 的职责是“决定走哪条链路”，不是直接执行所有外部能力。

## 5. Model Gateway

`backend/app/agent/model_gateway.py` 封装模型提供方差异。当前支持：

- `fake` provider：用于本地结构化成功返回
- `ark` provider：在缺少配置或超出当前任务范围时返回结构化失败

Model Gateway 的价值在于：

- 不把模型提供方细节散落到 API 层
- 缺少密钥时明确失败，不伪造成功
- 后续切换真实模型提供方时只收敛到统一接口

## 6. Conversation / Message / Notes / Handoff

`backend/app/services/conversation_service.py` 是当前会话域的核心服务层。它负责：

- 创建和读取会话
- 追加消息并维护时间线
- 管理内部备注
- 执行 handoff / pause-ai / resume-ai 状态迁移
- 读取工具调用和错误上下文

当前数据库模型已覆盖：

- `conversations`
- `messages`
- `model_calls`
- `retrieval_logs`
- `tool_calls`
- `handoff_events`
- `conversation_notes`
- `harness_runs`
- `harness_results`

## 7. Frontend 当前状态

前端位于 `frontend/`，技术栈为 React + Vite + TypeScript。

当前已实现页面：

- 登录页
- 会话列表页
- 会话详情页
- Harness 结果页

当前前端主要消费以下后端能力：

- 认证
- 会话列表
- 会话详情
- handoff / pause-ai / resume-ai
- 内部备注
- Harness 结果列表与详情

## 8. Harness 当前状态

Harness 位于 `harness/`，当前由以下部分组成：

- `cases/`：分类测试用例
- `runners/run_eval.py`：执行器
- `judges/deterministic_judge.py`：确定性判断器
- `reports/latest.json` / `latest.md`：最新报告

当前运行特点：

- `handoff` 类别通过 in-process API 链路验证状态机
- `regression` 类别通过真实 HTTP 调用 `/api/v1/chat`
- `latest.*` 每次运行会覆盖，因此排障时要及时保存证据

## 9. Docs 当前状态

`docs/` 现在承担三类职责：

- 计划与状态：`implementation-plan.md`、`task-board.md`、`development-status.md`
- 架构与维护：`system-overview.md`、`architecture-overview.md`、`testing-deployment-maintenance.md`
- 交付与交接：`phase2-closeout.md`、`agent-handoff.md`、`next-agent-prompt.md`

## 10. 当前架构结论

当前系统已经形成一个清晰的 MVP 分层：

- 前端后台负责管理体验
- Backend API 负责统一契约与状态管理
- Supervisor 负责规则优先路由
- Model Gateway 负责模型提供方抽象
- ConversationService 负责会话域持久化能力
- Harness 负责回归验证

后续进入 Phase 3 时，应该继续保持这个分层，不要把渠道适配逻辑直接塞回前端页面或聊天入口函数里。
