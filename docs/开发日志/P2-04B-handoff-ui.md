# P2-04B Handoff UI

## 范围

- 仅实现 `P2-04B Handoff UI` 的最小前端能力。
- 在会话详情页增加人工接管控制区块，支持人工接管、暂停 AI、恢复 AI。
- 根据当前 `handoff_status` 展示状态标签、说明文案与按钮可用性。
- 调用现有后端接口并在成功后同步本地详情状态。
- 补充 loading、disabled、error 处理与前端测试。
- 不包含人工回复输入框、关闭会话、备注、外部平台联动、鉴权协议修改或其他 Phase 2 子任务。

## 修改文件

- `frontend/src/conversations-client.ts`
- `frontend/src/conversation-detail-page.tsx`
- `frontend/src/styles.css`
- `frontend/src/test/App.test.tsx`
- `docs/task-board.md`
- `docs/dev-logs/P2-04B-handoff-ui.md`

## 测试结果

- `npm test`
  - 结果：通过，`1 passed file, 8 passed tests`
- `npm run build`
  - 结果：通过，`tsc --noEmit && vite build`

## 风险

- 当前前端在动作成功后仅同步本地 `handoff_status` 与 `assigned_agent_id`，未额外重新拉取完整详情；若后续详情页需要实时反映 handoff 事件流或审计区块，可能需要补一次刷新。
- 当前 UI 按最小 MVP 只覆盖按钮状态与错误提示，不包含人工回复输入、关闭会话或更细粒度的角色提示。

## 是否新增依赖

- 未新增依赖。
