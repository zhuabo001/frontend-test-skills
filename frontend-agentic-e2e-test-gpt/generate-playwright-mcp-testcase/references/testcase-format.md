# Playwright MCP testcase format

Use YAML 1.2-compatible values. Keep keys in the order shown by the templates so reviews and diffs remain predictable.

## Feature manifest

Place `manifest.yaml` beside the case files:

```yaml
schema_version: "1.0"
feature: "user-management"
source_documents:
  - "docs/plan.md"
generated_at: "2026-07-09T15:30:00+08:00"
coverage:
  - requirement: "AC-1"
    description: "管理员可以创建用户"
    positive_cases:
      - "create-user-success"
    negative_cases:
      - "create-user-missing-name-validation"
cases:
  - id: "create-user-success"
    file: "create-user-success.yaml"
    title: "管理员使用有效信息创建用户"
    case_type: "positive"
    priority: "high"
  - id: "create-user-missing-name-validation"
    file: "create-user-missing-name-validation.yaml"
    title: "创建用户时姓名为空应出现必填校验"
    case_type: "negative"
    priority: "high"
assumptions: []
open_questions: []
```

Requirements:

- Keep `schema_version` as a quoted string.
- Use the feature or plan name selected by the workflow in `feature`.
- Write source paths relative to the repository root when possible.
- Use RFC 3339 with an explicit timezone for `generated_at`.
- Add one `coverage` entry per functional point or acceptance criterion.
- Reference case IDs in `positive_cases` and `negative_cases`.
- Keep `cases` synchronized with files that the runner should execute.
- Record only material assumptions and unresolved questions.

## Test case

Write exactly one case per YAML file:

```yaml
schema_version: "1.0"
id: "create-user-missing-name-validation"
title: "创建用户时姓名为空应出现必填校验"
feature: "user-management"
case_type: "negative"
expected_behavior: "validation_error"
priority: "high"
review_status: "ready"
source:
  documents:
    - "docs/plan.md"
  requirements:
    - "AC-1"
preconditions:
  - "已登录管理员账号"
  - "当前位于用户管理页面"
test_data:
  name: ""
  email: "demo@example.com"
  role: "普通用户"
steps:
  - action: "navigate"
    target: "/users"
    expected: "用户管理页面可见"
  - action: "click"
    target: "新增用户按钮"
    expected: "新增用户弹窗打开"
  - action: "fill"
    target: "邮箱输入框"
    value: "demo@example.com"
  - action: "click"
    target: "提交按钮"
assertions:
  - type: "visible_text"
    target: "姓名不能为空"
    required: true
    timeout_ms: 5000
  - type: "url_should_not_change"
    value: "/users"
  - type: "hidden_text"
    target: "创建成功"
cleanup:
  - "无需清理，因为用例不应创建数据"
notes: []
```

### Required fields

Require these top-level keys:

- `schema_version`
- `id`
- `title`
- `feature`
- `case_type`: `positive` or `negative`
- `priority`: `high`, `medium`, or `low`
- `review_status`: `ready` or `needs-review`
- `source`
- `preconditions`
- `test_data`
- `steps`
- `assertions`
- `cleanup`
- `notes`

Require `expected_behavior` for negative cases. Prefer one of:

- `validation_error`
- `authorization_denied`
- `conflict_rejected`
- `boundary_rejected`
- `recovery_prompted`

Use a concise custom snake-case value when none applies.

### Steps

Each step requires `action` and usually `target`. Use a runner-interpretable verb such as:

- `navigate`
- `click`
- `fill`
- `select`
- `check`
- `uncheck`
- `upload`
- `press`
- `hover`
- `wait_for`
- `reload`

Use `value` for entered or selected data. Use `expected` only for an immediate observation that helps the runner confirm it can continue. Put final behavior checks in `assertions`.

### Assertions

Each assertion requires `type` plus the fields needed to observe it. Common types include:

- `visible_text`
- `hidden_text`
- `element_visible`
- `element_hidden`
- `field_value`
- `enabled`
- `disabled`
- `checked`
- `count`
- `url`
- `url_contains`
- `url_should_not_change`
- `request`
- `no_request`
- `response_status`

Use `timeout_ms` for toast, notification, loading, and other transient behavior. An assertion must describe evidence the browser runner can actually observe; do not assert internal implementation details unless network observation is explicitly required.

## Quality rules

- Prefer accessible, human-readable targets over selectors.
- Quote strings that could be parsed as booleans, dates, or numbers.
- Do not place passwords, tokens, cookies, or production personal data in test data.
- Do not use `expected_failure`; negative behavior is a business expectation, not a failing test.
- Do not generate Playwright Test code in these files.
- Mark a case `needs-review` rather than fabricating an expected result.
