# Hifleet 客服 Agent Harness 驱动开发规范

## 文档信息

| 字段 | 内容 |
|---|---|
| 文档名称 | Hifleet 客服 Agent Harness 驱动开发规范 |
| 当前版本 | v1.0.0 |
| 创建日期 | 2026-06-03 |
| 适用范围 | Hifleet 企业级客服 Agent 平台 MVP 与后续阶段开发 |
| 主要对象 | 生产服务器 Codex / 开发 Agent / 人类开发者 |
| 关联文档 | `需求重构方案.md` |

## 一、目标

本规范用于指导生产服务器上的 Codex 或其他开发 Agent 以 Harness 驱动方式开发 Hifleet 企业级客服 Agent 平台。

核心目标：

1. 降低 Agent 开发过程中的幻觉风险。
2. 避免一次性开发过大范围导致上下文崩溃。
3. 让每个功能都有可运行、可复现、可回归的验收用例。
4. 防止 Prompt、模型、RAG、Skill 修改后造成能力退化。
5. 让人类负责人可以通过报告快速判断开发质量。

本项目不接受“看起来能聊”的交付标准。所有核心能力都必须能通过 Harness 或 pytest 验证。

## 二、基本原则

### 2.1 Harness-Driven Development

本项目采用 Harness 驱动开发：

```text
需求章节 -> 小任务 -> Harness 用例 -> pytest / eval runner -> 实现 -> 再运行验证 -> 汇报
```

每个任务都必须回答：

- 本任务对应 `需求重构方案.md` 的哪一节？
- 本任务新增或更新了哪些 Harness case？
- 本任务如何验证？
- 验证结果是否通过？
- 如果未通过，失败原因是什么？

### 2.2 小步开发

开发 Agent 每次只允许执行一个明确任务。

禁止：

- 一次性实现多个 Phase。
- 一次性接入多个渠道。
- 一次性修改大量无关文件。
- 在未确认的情况下扩展需求。
- 为了通过用例硬编码答案。

如果某个任务需要修改 5 个以上核心模块，必须先拆分任务。

### 2.3 证据优先

Agent 不得声称“已完成”但没有验证证据。

完成汇报必须包含：

1. 修改文件。
2. 新增或更新的 Harness case。
3. 运行命令。
4. pytest 结果。
5. Harness 结果。
6. 未通过项与原因。

如果因环境缺少 API key、数据库未启动、外部服务不可用导致无法验证，必须明确说明，不得伪造通过。

## 三、推荐 Harness 目录结构

建议在项目根目录建立：

```text
harness/
  README.md
  cases/
    faq_cases.jsonl
    rag_cases.jsonl
    skill_cases.jsonl
    web_search_cases.jsonl
    multimodal_cases.jsonl
    handoff_cases.jsonl
    regression_cases.jsonl
  fixtures/
    images/
      sample_ship_screenshot.png
    docs/
      sample_faq.md
      sample_wiki.md
  runners/
    run_eval.py
    run_case.py
  judges/
    deterministic_judge.py
    llm_judge.py
  reports/
    latest.json
    latest.md
```

第一期优先实现：

- `cases/`
- `runners/run_eval.py`
- `judges/deterministic_judge.py`
- `reports/latest.json`
- `reports/latest.md`

`llm_judge.py` 可以后续再做，不作为第一期必要项。

## 四、Harness Case 格式

Harness case 使用 JSONL，每行一个用例。

### 4.1 通用字段

```json
{
  "id": "faq_001",
  "category": "faq",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "Hifleet 如何查询船位？",
    "attachments": []
  },
  "expect": {
    "must_include_keywords": ["船位", "船名", "MMSI"],
    "must_not_include_keywords": ["我猜测", "可能是但不确定"],
    "must_use_knowledge": true,
    "must_use_web_search": false,
    "expected_skill": null,
    "min_sources": 1,
    "expected_handoff_status": "ai_active"
  },
  "metadata": {
    "priority": "p0",
    "description": "验证基础船位查询说明是否能基于知识库回答"
  }
}
```

### 4.2 字段说明

| 字段 | 说明 |
|---|---|
| `id` | 用例唯一 ID |
| `category` | 用例分类 |
| `phase` | 所属阶段 |
| `input.channel_type` | 渠道类型，MVP 默认为 `console` |
| `input.message_type` | `text` / `image` / `voice` / `file` |
| `input.content` | 用户输入文本 |
| `input.attachments` | 附件路径或对象存储引用 |
| `expect.must_include_keywords` | 回答必须包含的关键词 |
| `expect.must_not_include_keywords` | 回答禁止包含的词 |
| `expect.must_use_knowledge` | 是否必须调用知识库 |
| `expect.must_use_web_search` | 是否必须调用网页检索 |
| `expect.expected_skill` | 期望调用的 Skill |
| `expect.min_sources` | 最少来源数量 |
| `expect.expected_handoff_status` | 期望会话接管状态 |

## 五、用例分类

### 5.1 FAQ 用例

用于验证标准客服问题回答。

示例：

```json
{
  "id": "faq_001",
  "category": "faq",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "Hifleet 怎么查询船位？",
    "attachments": []
  },
  "expect": {
    "must_include_keywords": ["船位", "船名", "MMSI"],
    "must_not_include_keywords": ["我猜测", "随便"],
    "must_use_knowledge": true,
    "min_sources": 1,
    "expected_handoff_status": "ai_active"
  }
}
```

### 5.2 RAG 用例

用于验证知识库检索与来源引用。

示例：

```json
{
  "id": "rag_001",
  "category": "rag",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "Hifleet 的港口船舶统计功能怎么使用？",
    "attachments": []
  },
  "expect": {
    "must_use_knowledge": true,
    "min_sources": 1,
    "must_include_source_types": ["faq", "wiki"]
  }
}
```

### 5.3 Skill 用例

用于验证 Agent 是否正确识别业务 Skill 意图和参数。

第一期 Skills 只做架构，因此允许 mock，不要求真实调用船舶生产 API。

示例：

```json
{
  "id": "skill_001",
  "category": "skill",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "帮我查一下 EVER GIVEN 当前船位",
    "attachments": []
  },
  "expect": {
    "expected_skill": "ship.position.query",
    "expected_skill_args": {
      "keyword": "EVER GIVEN"
    },
    "must_create_tool_call": true,
    "allow_mock_result": true
  }
}
```

参数缺失示例：

```json
{
  "id": "skill_002",
  "category": "skill",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "帮我查一下当前船位",
    "attachments": []
  },
  "expect": {
    "expected_skill": "ship.position.query",
    "must_ask_clarifying_question": true,
    "must_not_execute_skill": true
  }
}
```

### 5.4 Web Search 用例

用于验证深度网页检索能力。

示例：

```json
{
  "id": "web_001",
  "category": "web_search",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "请检索并总结近期公开航运政策信息，给出来源。",
    "attachments": []
  },
  "expect": {
    "must_use_web_search": true,
    "min_sources": 2,
    "must_include_urls": true
  }
}
```

### 5.5 Multimodal 用例

用于验证图片理解。

示例：

```json
{
  "id": "image_001",
  "category": "multimodal",
  "phase": "phase1",
  "input": {
    "channel_type": "console",
    "message_type": "image",
    "content": "请分析这张图片里可能包含什么信息。",
    "attachments": [
      {
        "type": "image",
        "path": "harness/fixtures/images/sample_ship_screenshot.png"
      }
    ]
  },
  "expect": {
    "must_use_vision": true,
    "must_include_keywords": ["图片", "截图"]
  }
}
```

### 5.6 Handoff 用例

用于验证人工接管状态机。

示例：

```json
{
  "id": "handoff_001",
  "category": "handoff",
  "phase": "phase2",
  "input": {
    "channel_type": "console",
    "message_type": "text",
    "content": "我要投诉，找人工客服。",
    "attachments": []
  },
  "expect": {
    "expected_handoff_status": "human_pending",
    "must_not_continue_ai_after_handoff": true
  }
}
```

## 六、判断器设计

### 6.1 优先使用确定性判断

第一期优先使用 `deterministic_judge.py`，不要过早依赖 LLM Judge。

确定性判断包括：

- 是否返回 HTTP 200。
- 是否创建 `conversation`。
- 是否创建 `message`。
- 是否调用知识库。
- 是否记录 `retrieval_logs`。
- 是否记录 `tool_calls`。
- 是否调用期望 Skill。
- 是否包含必要关键词。
- 是否不包含禁止词。
- 是否返回来源。
- 是否进入正确人工接管状态。

### 6.2 LLM Judge 后置

LLM Judge 只用于开放式回答质量评分，不能替代结构化断言。

适用场景：

- 回答是否清晰。
- 总结是否完整。
- 复杂网页检索结果是否合理。
- 多轮会话是否自然。

不适用场景：

- Skill 是否调用。
- 数据库是否落库。
- 人工接管状态是否正确。
- 是否产生 ToolCall。

这些必须用结构化数据判断。

## 七、各阶段质量门禁

### 7.1 Phase 0：工程底座门禁

必须通过：

```text
pytest
GET /api/health 返回 200
数据库 migration 成功
Harness runner 能启动
```

通过标准：

- 单元测试全部通过。
- 数据库表能创建。
- 服务能启动。
- Harness 能读取 cases 并生成空报告或基础报告。

### 7.2 Phase 1：Agent 主链路门禁

必须通过：

```text
pytest
python harness/runners/run_eval.py --category faq
python harness/runners/run_eval.py --category rag
python harness/runners/run_eval.py --category skill
```

通过标准：

| 分类 | 通过标准 |
|---|---|
| FAQ | P0 用例通过率不低于 80% |
| RAG | 必须有来源引用 |
| Skill | mock Skill 意图识别通过率不低于 90% |
| ToolCall | Skill 用例必须写入 `tool_calls` |
| 失败处理 | 模型或工具失败时不得伪造成功 |

### 7.3 Phase 2：标准客服后台门禁

必须通过：

```text
pytest
python harness/runners/run_eval.py --category handoff
```

通过标准：

- 会话可查询。
- 消息时间线完整。
- 人工接管后 AI 不再自动回复。
- AI 暂停 / 恢复有状态记录。
- 客服备注不发送给用户。
- 工具调用详情可查看。

### 7.4 Phase 3：渠道接入门禁

接入公众号或 Chatwoot 前必须保证：

- 原有 Phase 1 / Phase 2 Harness 不退化。
- 渠道消息进入统一 `conversations` / `messages`。
- 渠道 Adapter 不绕过 Agent API。
- 渠道回复状态可追踪。
- 不在渠道代码里重新实现 Agent 业务逻辑。

### 7.5 Phase 4：微信客服平台门禁

必须验证：

- 微信客服消息可同步到后台。
- AI 回复与人工接管互斥。
- 人工接管后 AI 不自动发送消息。
- 消息发送状态、失败原因、重试结果可追踪。

### 7.6 Phase 5：数字员工能力门禁

必须验证：

- 文件分析在隔离环境运行。
- 沙箱失败不会影响主服务。
- 高风险写操作必须人工确认。
- 文件、报告、任务结果有审计记录。

## 八、开发 Agent 执行规则

### 8.1 每个任务开始前

开发 Agent 必须先输出：

```text
1. 本任务目标
2. 本任务对应需求文档章节
3. 本任务涉及文件
4. 本任务新增或更新的 Harness case
5. 本任务不做什么
```

未输出以上内容，不允许直接写代码。

### 8.2 每个任务执行中

必须遵守：

1. 先写或更新测试 / Harness case。
2. 再实现最小功能。
3. 每次只处理当前任务范围。
4. 不擅自接入真实外部平台。
5. 不擅自添加生产写操作。
6. 不把业务接口写死在 Prompt 中。
7. 不把渠道逻辑写进 Agent 核心。

### 8.3 每个任务完成后

必须输出：

```text
1. 修改文件列表
2. 新增/更新的 Harness case
3. 执行的命令
4. pytest 结果
5. Harness 结果
6. 未通过项
7. 风险与下一步建议
```

如果测试未通过，不得声称完成。

## 九、禁止事项

### 9.1 禁止硬编码

禁止为了通过 Harness 用例写死以下内容：

- 固定问题对应固定答案。
- 固定问题强制固定 Skill，绕过真实意图识别流程。
- 直接构造假的 `tool_calls`。
- 直接构造假的 `retrieval_logs`。
- 在测试模式之外返回 mock 模型回答。

允许的 mock：

- 第一阶段 Skill API 尚未接入真实服务时，可以使用 `execution_mode = mock`。
- mock 必须通过 Skill Hub 执行，并记录真实 `tool_calls`。
- mock 结果必须明确标记为 mock，不能伪装成真实生产数据。

### 9.2 禁止伪造成功

以下情况必须明确报告，不得说“已完成”：

- 模型 API key 缺失。
- 数据库未启动。
- MinIO 未启动。
- 外部搜索 API 不可用。
- 微信 / Chatwoot / 微信客服平台未配置。
- Harness 未运行。
- pytest 未运行。
- 用例失败。

### 9.3 禁止范围漂移

在 MVP 阶段，开发 Agent 不得主动实现：

- 微信公众号真实接入。
- Chatwoot 真实接入。
- 微信客服平台真实接入。
- 文件分析沙箱。
- 订阅通知。
- 生产写操作。
- 多租户商业化后台。

除非任务明确要求。

## 十、给 Codex 的任务模板

每次给生产服务器 Codex 下发任务时，建议使用以下模板：

```text
任务编号：
任务名称：

参考文档：
- 智能客服/客服开发/需求重构方案.md
- 智能客服/客服开发/Harness驱动开发规范.md
- 具体章节：

目标：
本任务只实现……

范围：
- 做……
- 做……
- 做……

必须新增或更新的 Harness case：
- case_id：
- category：
- 验证点：

禁止：
- 不做……
- 不接……
- 不改……

涉及文件建议：
- `path/to/file`
- `path/to/test`
- `harness/cases/...`

验收命令：
- `pytest`
- `python harness/runners/run_eval.py --category <category>`

完成后汇报：
1. 修改文件
2. 新增/更新 Harness case
3. pytest 结果
4. Harness 结果
5. 未通过项和原因
6. 下一步建议
```

## 十一、推荐第一批 Codex 任务

### Task H0-01：初始化 Harness 骨架

目标：

- 创建 `harness/` 目录结构。
- 创建基础 case 文件。
- 创建 `run_eval.py`。
- 创建确定性 judge。
- 生成 `reports/latest.json` 与 `reports/latest.md`。

验收：

```text
python harness/runners/run_eval.py --category faq
```

即使 Agent API 尚未实现，也应能输出“服务不可用 / case 未执行”的结构化报告，而不是崩溃。

### Task H0-02：定义第一批 MVP Case

目标：

- 新增 FAQ、RAG、Skill、Handoff 第一批用例。
- 每类至少 3 条。
- 不包含真实渠道用例。

验收：

```text
python harness/runners/run_eval.py --list-cases
```

能列出所有用例。

### Task H0-03：Agent API 与 Harness 联调

目标：

- Harness 能调用 `/api/v1/chat`。
- 能记录响应、耗时、状态码。
- 能根据返回结构做基础断言。

验收：

```text
pytest
python harness/runners/run_eval.py --category faq
```

### Task H0-04：Skill Harness 联调

目标：

- Skill 用例能验证 `expected_skill`。
- 能验证 `tool_calls` 是否生成。
- 允许 mock Skill，但必须走 Skill Hub。

验收：

```text
python harness/runners/run_eval.py --category skill
```

### Task H0-05：人工接管 Harness 联调

目标：

- Handoff 用例能验证 `handoff_status`。
- 人工接管后 AI 不自动回复。

验收：

```text
python harness/runners/run_eval.py --category handoff
```

## 十二、报告格式

### 12.1 `latest.json`

```json
{
  "run_id": "run_20260603_001",
  "started_at": "2026-06-03T16:00:00+08:00",
  "finished_at": "2026-06-03T16:02:00+08:00",
  "category": "skill",
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "pass_rate": 0.8
  },
  "results": [
    {
      "case_id": "skill_001",
      "passed": true,
      "score": 1,
      "failure_reason": null
    }
  ]
}
```

### 12.2 `latest.md`

```markdown
# Harness Report

- Run ID: run_20260603_001
- Category: skill
- Total: 10
- Passed: 8
- Failed: 2
- Pass Rate: 80%

## Failed Cases

### skill_002

Reason: expected clarifying question, but skill was executed.
```

## 十三、质量基线

MVP 发布前建议达到：

| 分类 | 最低要求 |
|---|---|
| FAQ | P0 用例通过率 >= 80% |
| RAG | 来源引用覆盖率 >= 90% |
| Skill | mock Skill 意图识别通过率 >= 90% |
| Handoff | 人工接管状态机 100% 通过 |
| Web Search | 必须返回 URL 来源 |
| Multimodal | 图片用例可成功调用视觉链路 |
| Regression | 历史关键用例无明显退化 |

## 十四、最终要求

生产服务器上的 Codex 必须按以下方式开发：

```text
小任务开发
+ Harness case 先行
+ pytest 验证
+ eval runner 验证
+ 结构化报告
+ 人类确认后进入下一任务
```

只要某个任务没有对应 Harness 或明确验证方式，就不应进入实现阶段。

本规范与 `需求重构方案.md` 共同作为 Hifleet 客服 Agent 项目的开发质量基线。
