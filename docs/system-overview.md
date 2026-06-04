# 系统总览

## 1. 系统目标

HiFleetAI 的目标是建设一个可持续演进的企业客服 Agent 平台。当前阶段优先完成：

- 自建标准客服后台
- 统一 Agent API
- Harness 回归测试工程
- 会话、消息、人工接管、AI 状态与备注管理

系统设计强调“先打通后台测试会话，再扩展真实渠道”，避免在 MVP 阶段把复杂渠道接入、生产写操作和高风险能力混入核心链路。

## 2. 当前 MVP 范围

当前仓库的 MVP 范围是：

- 后台测试会话与管理后台登录
- `/api/v1/chat` 最小聊天响应契约
- 会话列表与会话详情
- 人工接管、AI 暂停、AI 恢复
- 内部备注
- Harness 结果页
- Harness 回归与 handoff 验证

当前仓库没有单独的 `需求重构方案.md`，需求主文档以根目录 `HiFleetAI开发方案.md` 为准。

## 3. 当前已实现能力

### 后端

- `GET /api/health` 健康检查
- `POST /api/v1/auth/login`、`GET /api/v1/auth/me`
- `POST /api/v1/chat` MVP 响应契约
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `POST /api/v1/conversations/{id}/handoff`
- `POST /api/v1/conversations/{id}/pause-ai`
- `POST /api/v1/conversations/{id}/resume-ai`
- `GET /api/v1/conversations/{id}/notes`
- `POST /api/v1/conversations/{id}/notes`
- `GET /api/v1/harness/runs`
- `GET /api/v1/harness/runs/{run_id}`

### 前端

- 登录页与受保护路由
- 会话列表页
- 会话详情页
- 人工接管 / 暂停 AI / 恢复 AI 控件
- 内部备注区块
- Harness 结果页

### Harness

- `faq`、`rag`、`skill`、`handoff`、`regression` 基础 case
- `run_eval.py` 统一执行入口
- 确定性 judge
- `latest.json` / `latest.md` 报告输出

## 4. 当前未实现范围

以下范围当前明确未实现，且不属于 Phase 2 收口交付：

- 微信公众号真实接入
- Chatwoot 真实接入
- 微信客服平台真实接入
- 真实网页检索执行
- 真实多模态图片理解执行
- 真实生产 Skill 服务接入
- 文件分析沙箱
- 订阅通知
- 高风险生产写操作
- 多租户商业化后台

## 5. 当前阶段在路线图中的位置

- Phase 0：工程底座，已完成
- Phase 1：Agent 核心链路，已完成
- Phase 2：标准客服后台，已完成收口
- Phase 3 及之后：真实渠道接入、渠道消息同步、真实客服试运行，尚未开始

## 6. 当前系统的交付结论

当前仓库已经具备“后台测试会话 + 结构化 Agent API + Harness 回归 + 标准客服后台”的 Phase 2 可交付基线。后续开发应从 Phase 3 规划与渠道接入拆解开始，而不是继续补 Phase 2 基础页面。
