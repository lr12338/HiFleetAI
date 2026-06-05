# P2-06A Harness Results API

## 范围

- 仅实现 `P2-06A Harness Results API` 的最小后端查询能力。
- 新增受保护的 Harness run 列表/摘要接口与单个 run 详情接口。
- 数据源优先读取 `HarnessRun/HarnessResult`，当数据库中没有可读 run 时回退到 `harness/reports/latest.json`。
- 增加后端测试，覆盖摘要读取、详情读取、未认证访问、无数据/不存在 run 的返回。
- 更新 `docs/task-board.md` 将 `P2-06A` 置为 `review`。
- 不包含前端 Harness 页面、judge 语义调整、无关重构、提交行为。

## 修改文件

- `backend/app/api/__init__.py`
- `backend/app/api/harness.py`
- `backend/app/services/harness_service.py`
- `backend/tests/test_harness_api.py`
- `docs/task-board.md`
- `docs/dev-logs/P2-06A-harness-api.md`

## 测试结果

- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest backend/tests/test_harness_api.py`
  - 结果：通过，`5 passed, 1 warning`
- `PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" python3 -m pytest`
  - 结果：失败，`54 passed, 1 failed, 1 warning`
  - 阻塞项：现有 `backend/tests/test_notes_api.py` 在 `test_notes_endpoints_require_login` 处失败，报错为 `TestClient.get() got an unexpected keyword argument 'json'`
- 备注：本任务新增的 Harness API 专项测试通过；出现的 warning 仍是现有 `fastapi.testclient` / `starlette` 弃用告警，未单独处理。

## 风险

- 数据库侧 `HarnessResult.case_id` 当前模型仍为 UUID 类型，而 Harness 文件报告里的 `case_id` 为字符串标识；本次 API 仅读取已有数据，不扩展写入链路，后续若要把文件报告完整落库，需要统一该字段语义。
- 文件回退路径当前只读取 `harness/reports/latest.json`，因此在没有数据库 run 历史时只能暴露最新一次报告，而不是完整历史列表。
- 详情接口对数据库来源和文件来源返回统一最小结构；文件来源包含 `assertions` / `agent_result`，数据库来源目前只暴露结构化结果字段，不补造不存在的 judge 明细。

## 是否新增依赖

- 未新增依赖。
