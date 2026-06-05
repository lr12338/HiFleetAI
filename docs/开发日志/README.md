# 开发日志说明

开发日志用于保存主控调度、任务执行、验证证据、风险与决策的过程记录。

## 1. 目录约定

- 主日志：`docs/开发日志/YYYY-MM-DD-master-log.md`
- 任务日志：`docs/开发日志/<task-id>-<short-name>.md`

示例：

- `docs/开发日志/2026-06-03-master-log.md`
- `docs/开发日志/P0-06-harness.md`
- `docs/开发日志/P1-03-model-gateway.md`

## 2. 主日志建议结构

```text
# YYYY-MM-DD Master Log

## Summary
## Repository State
## Task Dispatch
## Reviews
## Validation Evidence
## Risks And Decisions
## Next Actions
```

## 3. 任务日志建议结构

```text
# <Task ID> <Task Name>

## Task Metadata
## Scope
## Modified Files
## Harness Cases
## Acceptance Commands
## Test Results
## Risks And Remaining Issues
## Next Stage Readiness
```

## 4. 日志规则

1. 任务未形成日志，不算完整收口
2. 失败命令必须记录失败原因
3. 跳过命令必须说明原因
4. 环境阻塞不能伪装为成功
5. 不得写入 API key、token、cookie、生产凭据或客户敏感数据
6. 只提交人工整理后的开发日志，不提交运行时原始日志
