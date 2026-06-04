# 开发状态

## 1. 当前代码基线

- 仓库路径：`/home/ecs-user/HiFleetAI`
- 当前主交付分支：`feature/P0-05-pytest`
- 当前基线状态：Phase 2 已完成收口，进入交付整理与后续 Phase 3 规划准备阶段

## 2. 各阶段进展

### Phase 0：工程底座

状态：已完成

已具备：

- 配置系统与 `.env.example`
- Docker Compose 模板
- 数据库模型与迁移基础
- pytest 基础设施
- Harness 骨架

### Phase 1：Agent 核心链路

状态：已完成

已具备：

- FastAPI 应用与健康检查
- Conversation / Message 基础模型
- Model Gateway 抽象
- Supervisor 规则优先路由
- Harness 基础回归链路

### Phase 2：标准客服后台

状态：已完成

已具备：

- 登录与鉴权
- 会话列表
- 会话详情
- 人工接管
- AI 暂停 / 恢复
- 内部备注
- Harness 结果页
- `/api/v1/chat` MVP 契约补齐
- `handoff` 与 `regression` Harness 验收通过

### Phase 3：渠道接入

状态：未开始

当前未实现：

- 微信公众号真实接入
- Chatwoot 真实接入
- 渠道消息同步与统一来源展示
- 渠道绑定与消息发送状态追踪

### Phase 4 及以后

状态：未开始

未开始的能力包括：

- 微信客服平台
- 更完整的真实客服试运行链路
- 文件分析沙箱
- 更复杂的自动化与高风险写操作控制

## 3. 当前已交付能力清单

### 后端

- `auth`
- `chat`
- `conversations`
- `harness`
- `health`

### 前端

- 登录页
- 受保护路由
- 会话列表与详情
- handoff / pause / resume 控件
- 内部备注
- Harness 结果页

### 测试与质量

- `pytest` 全量通过
- 前端 `npm test` 与 `npm run build` 通过
- Harness `handoff` / `regression` 通过

## 4. 当前仍需注意的事实

- `/api/v1/chat` 当前是 MVP 级实现，重点是稳定契约与可验证性，不是完整生产对话引擎
- 真实知识检索、真实网页检索、真实多模态与真实 Skill 执行尚未接入
- `HiFleetData/` 是本地未跟踪目录，不应混入版本库
- Harness 的 `latest.*` 会被新一次执行覆盖

## 5. 下一阶段建议从哪里开始

建议不要直接编码 Phase 3，而是先完成一轮规划与拆任务。优先顺序建议如下：

1. 明确渠道接入的统一契约，禁止绕过 `/api/v1/chat`
2. 设计 Phase 3 的 `channel_bindings`、`channel_message_id`、来源追踪与状态同步方案
3. 为渠道接入补 Harness / pytest 用例，而不是先写适配器
4. 评估 `/api/v1/chat` 是否需要在 Phase 3 中从 MVP 响应器演进到更完整的执行编排
5. 梳理依赖清单与环境管理策略，避免后续渠道开发对当前 `.venv` 形成隐式依赖

## 6. 当前结论

当前代码基线已经不再是“Phase 2 候选”，而是“Phase 2 已完成、可交付、可继续规划 Phase 3”的状态。后续工作应从渠道规划、契约设计和测试先行开始。
