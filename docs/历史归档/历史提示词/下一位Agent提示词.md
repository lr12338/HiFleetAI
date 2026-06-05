# 下一位 Agent 接力提示词

你现在接手的是 HifleetAI 项目，项目根目录为 `/home/ecs-user/HiFleetAI`。

请注意：当前系统不是从零开始，也不是“Phase 2 候选状态”，而是已经完成了 Phase 2 收口并通过关键验证的基线。你的任务不是直接大改代码，而是先理解当前系统状态，再基于现有计划继续推进 Phase 3 及之后的工作。

## 一、项目当前状态

- 当前已完成 Phase 0、Phase 1、Phase 2
- 当前已经具备标准客服后台 MVP
- 当前 `/api/v1/chat` 已补齐 MVP 响应契约
- 当前后端 `pytest` 已通过
- 当前前端 `npm test` 与 `npm run build` 已通过
- 当前 Harness `handoff` 与 `regression` 已通过

## 二、接手后必读文档

请先阅读以下文档，不要跳过：

1. `HiFleetAI开发方案.md`
2. `Harness驱动开发规范.md`
3. `docs/system-overview.md`
4. `docs/architecture-overview.md`
5. `docs/testing-deployment-maintenance.md`
6. `docs/development-status.md`
7. `docs/phase2-closeout.md`
8. `docs/agent-handoff.md`
9. `docs/task-board.md`
10. `docs/versioning-policy.md`

## 三、当前系统边界

当前仍然禁止：

- 擅自扩大 MVP 范围
- 接入真实微信公众号
- 接入真实 Chatwoot
- 接入真实微信客服平台
- 接入高风险生产写操作
- 接入文件分析沙箱
- 跳过 Harness
- 伪造成功结果

## 四、当前已完成能力

- 登录与鉴权
- 会话列表
- 会话详情
- 人工接管
- AI 暂停 / 恢复
- 内部备注
- Harness 结果页
- `/api/v1/chat` MVP 契约
- Supervisor 最小规则路由
- Model Gateway 抽象
- Harness runner 与 deterministic judge

## 五、当前未完成能力

- 真实微信公众号接入
- 真实 Chatwoot 接入
- 真实微信客服平台接入
- 真实网页检索执行
- 真实多模态图片理解执行
- 真实 Skill 服务接入
- 渠道绑定与渠道消息同步
- 更完整的生产级聊天编排

## 六、接手时先做环境检查

先执行：

```bash
git status --short --branch
git diff --stat
```

确认：

- 当前分支
- 是否有未提交改动
- 是否混有 `HiFleetData/`、`.env`、运行产物、缓存

## 七、接手时先跑测试和 Harness

建议按这个顺序：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_chat_api.py
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest
cd /home/ecs-user/HiFleetAI/frontend && npm test
cd /home/ecs-user/HiFleetAI/frontend && npm run build
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 /home/ecs-user/HiFleetAI/harness/runners/run_eval.py --category handoff
```

如果你要跑 `regression`，必须先确认你启动的是“当前工作树服务”，而不是系统里残留的旧进程：

```bash
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port <空闲端口>
HARNESS_AGENT_BASE_URL="http://127.0.0.1:<空闲端口>" PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 harness/runners/run_eval.py --category regression
```

## 八、如何确认当前工作树状态

你必须明确检查：

- 当前有没有未提交的代码
- 当前是否存在未跟踪本地数据
- 当前 Harness 报告是否只是最近一次临时输出

重点禁止提交：

- `HiFleetData/`
- `.env`
- `.venv/`
- `node_modules/`
- `dist/`
- `harness/reports/latest.json`
- `harness/reports/latest.md`

## 九、如何继续拆任务

后续工作应该基于现有计划进行，不要直接跳进实现。建议顺序：

1. 先分析 `HiFleetAI开发方案.md` 中的 Phase 3 范围
2. 结合 `docs/development-status.md` 和 `docs/task-board.md` 拆成单任务
3. 每次只推进一个明确范围
4. 先补测试 / Harness，再实现最小功能
5. 做完后更新日志、任务板、收口说明

## 十、严禁事项

严禁：

1. 擅自扩范围
2. 伪造测试通过
3. 不跑 Harness 就声称完成
4. 命中旧服务端口后误判当前工作树正常
5. 直接把渠道逻辑写死在 `/api/v1/chat`
6. 在没有规划的情况下大改数据模型或前端结构
7. 将本地数据目录和临时报告混入提交

## 十一、推荐起手动作

请按以下顺序开始：

1. 阅读文档
2. 检查工作树
3. 跑当前验证
4. 输出分析与计划
5. 等计划清晰后再进入实现

不要一上来大改代码。先做分析和计划，再执行。
