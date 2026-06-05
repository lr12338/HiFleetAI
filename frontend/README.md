# 前端说明

## 1. 模块定位

`frontend/` 是 HiFleetAI 的 React + Vite 管理后台，当前已经不是空壳，而是一个可登录、可查看会话、可调用 `/api/v1/chat` 的 Phase 2 工作台。

## 2. 当前页面

- 登录页
- 受保护路由
- 会话列表页
- 会话详情页
- 人工接管 / 暂停 AI / 恢复 AI 控件
- 内部备注区块
- Harness 结果页
- `Test Chat` 页面

## 3. 当前联调方式

当前前端已经配置 Vite `dev proxy`：

- 浏览器访问 `http://127.0.0.1:5173`
- `/api/*` 请求自动转发到 `http://127.0.0.1:8000`

因此，当前支持完整本地联调：

1. 登录后台
2. 进入 `Test Chat`
3. 发送消息
4. 跳转到持久化会话详情

## 4. 常用命令

```bash
cd /home/ecs-user/HiFleetAI/frontend
npm test
npm run build
npm run dev -- --host 127.0.0.1 --port 5173
```

## 5. 当前限制

- 前端展示仍基于当前 MVP 范围
- 真实渠道来源展示尚未接入
- 知识库真实检索结果尚未接入页面
- 当前完整联调更推荐基于 SQLite，而不是 PostgreSQL

## 6. 相关文档

- `docs/系统架构说明.md`
- `docs/测试与部署维护指南.md`
- `docs/当前开发状态.md`
