# YAML 用例 Schema 参考

本文件定义单用例 YAML 与 manifest 的字段。生成时严格遵循，保证 `run-playwright-mcp-testcases` 能可靠解释。

## 目录

- [设计原则](#设计原则)
- [单用例字段](#单用例字段)
- [action 动作词表](#action-动作词表)
- [assertion 断言词表](#assertion-断言词表)
- [正向用例完整示例](#正向用例完整示例)
- [负向用例完整示例](#负向用例完整示例)
- [Manifest 结构](#manifest-结构)
- [反面示例（禁止这样写）](#反面示例禁止这样写)

## 设计原则

- **一个 YAML = 一个用例**。
- **target 用人类可读的可访问名称**，不写 CSS/xpath。runner 依赖可访问性快照按名称定位控件。
- **steps 原子化**：一步一个动作。
- **负向用例**描述“业务应当拒绝”的正确表现，达成即 `passed`。

## 单用例字段

顶层字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 用例唯一标识，kebab-case，须与文件名（去扩展名）一致。 |
| `title` | 是 | 人类可读标题，说明意图与预期。 |
| `feature` | 是 | 所属特性名（与目录名一致）。 |
| `case_type` | 是 | `positive` 或 `negative`。 |
| `expected_behavior` | 负向必填 | 负向用例的预期业务行为，如 `validation_error`、`request_blocked`、`permission_denied`。正向可省略或写 `success`。 |
| `source` | 是 | 来源文档文件名，如 `plan.md`。 |
| `priority` | 建议 | `high` / `medium` / `low`。 |
| `preconditions` | 建议 | 字符串数组，执行前应满足的状态（如“已登录管理员账号”）。 |
| `test_data` | 视情况 | 键值对，本用例使用的输入数据。 |
| `steps` | 是 | 有序操作步骤数组，见下。 |
| `assertions` | 是 | 断言数组，见下。 |
| `cleanup` | 建议 | 字符串数组，测试后清理说明；负向用例通常写“无需清理，用例不应创建数据”。 |

### step 字段

每个 step 是一个对象：

| 字段 | 必填 | 说明 |
|------|------|------|
| `action` | 是 | 动作词，见动作词表。 |
| `target` | 视动作 | 人类可读控件/元素名称。`navigate` 用路径或 URL。 |
| `value` | 视动作 | `fill`/`select` 等需要输入值时提供。 |
| `expected` | 建议 | 该步执行后的可观察预期（便于 runner 记录 actual 并对比）。 |

### assertion 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | 是 | 断言类型，见断言词表。 |
| `target` | 视类型 | 断言针对的文案/元素/URL 等。 |
| `value` | 视类型 | 期望值（如 URL、文本内容）。 |
| `required` | 否 | `true` 表示该断言是判定 pass/fail 的关键断言。 |
| `timeout_ms` | toast/瞬时元素建议 | 等待出现的最大毫秒数，默认由 runner 决定，建议 toast 给 5000。 |

## action 动作词表

优先使用以下标准动作词（runner 对这些有确定处理）：

- `navigate`：跳转到 `target`（路径或 URL）。
- `click`：点击 `target` 指向的按钮/链接/元素。
- `fill`：向 `target` 输入框填入 `value`。
- `clear`：清空 `target` 输入框。
- `select`：在 `target` 下拉/选择器中选择 `value`。
- `check` / `uncheck`：勾选/取消勾选 `target` 复选框。
- `hover`：悬停在 `target` 上。
- `press`：按下键盘按键 `value`（如 `Enter`）。
- `upload`：向 `target` 上传文件 `value`（文件路径）。
- `wait_for`：等待 `target`（文本或元素）出现，可带 `timeout_ms`。

如需其他动作，用清晰的动词并保证语义无歧义。

## assertion 断言词表

- `visible_text`：页面上应出现 `target` 文案（用于 toast/校验提示时加 `timeout_ms`）。
- `not_visible_text`：页面不应出现 `target` 文案。
- `element_visible` / `element_hidden`：`target` 元素应可见/隐藏。
- `url_should_be`：当前 URL 等于 `value`。
- `url_should_not_change`：URL 应仍为 `value`（负向常用）。
- `no_success_toast`：不应出现成功提示（`target` 为成功文案，负向常用）。
- `input_value`：`target` 输入框的值等于 `value`。
- `row_count` / `list_contains`：列表包含/数量断言（`target` 描述列表，`value` 为期望）。
- `no_network_request_to`：不应发出到 `target`（接口路径）的请求（负向“请求被阻止”）。

## 正向用例完整示例

```yaml
id: create-user-success
title: 管理员成功创建普通用户
feature: user-management
case_type: positive
expected_behavior: success
source: plan.md
priority: high

preconditions:
  - 已登录管理员账号
  - 当前位于用户管理页面

test_data:
  name: "Alice"
  email: "alice@example.com"
  role: "普通用户"

steps:
  - action: navigate
    target: "/users"
    expected: "用户管理页面可见"

  - action: click
    target: "新增用户按钮"
    expected: "新增用户弹窗打开"

  - action: fill
    target: "姓名输入框"
    value: "Alice"

  - action: fill
    target: "邮箱输入框"
    value: "alice@example.com"

  - action: select
    target: "角色下拉框"
    value: "普通用户"

  - action: click
    target: "提交按钮"

assertions:
  - type: visible_text
    target: "创建成功"
    required: true
    timeout_ms: 5000

  - type: list_contains
    target: "用户列表"
    value: "alice@example.com"
    required: true

cleanup:
  - 删除测试创建的用户 alice@example.com
```

## 负向用例完整示例

```yaml
id: create-user-missing-name-validation
title: 创建用户时姓名为空应出现必填校验
feature: user-management
case_type: negative
expected_behavior: validation_error
source: plan.md
priority: high

preconditions:
  - 已登录管理员账号
  - 当前位于用户管理页面

test_data:
  name: ""
  email: "demo@example.com"
  role: "普通用户"

steps:
  - action: navigate
    target: "/users"
    expected: "用户管理页面可见"

  - action: click
    target: "新增用户按钮"
    expected: "新增用户弹窗打开"

  - action: fill
    target: "邮箱输入框"
    value: "demo@example.com"

  - action: click
    target: "提交按钮"

assertions:
  - type: visible_text
    target: "姓名不能为空"
    required: true
    timeout_ms: 5000

  - type: url_should_not_change
    value: "/users"

  - type: no_success_toast
    target: "创建成功"

cleanup:
  - 无需清理，因为用例不应创建数据
```

## Manifest 结构

在特性子目录下生成 `manifest.yaml`，索引本次生成的全部用例：

```yaml
feature: user-management
source: plan.md
generated_at: "2026-07-09T14:30:00+08:00"
summary:
  total: 3
  positive: 1
  negative: 2
cases:
  - id: create-user-success
    file: create-user-success.yaml
    case_type: positive
    priority: high
    covers: "创建用户（主成功路径）"
  - id: create-user-missing-name-validation
    file: create-user-missing-name-validation.yaml
    case_type: negative
    priority: high
    covers: "创建用户-姓名必填校验"
  - id: create-user-duplicate-email-validation
    file: create-user-duplicate-email-validation.yaml
    case_type: negative
    priority: medium
    covers: "创建用户-邮箱重复校验"
```

## 反面示例（禁止这样写）

模糊步骤（禁止）：

```yaml
steps:
  - 测试一下创建用户是否正常   # ❌ 不是原子动作，runner 无法执行
```

误导性字段（禁止）：

```yaml
expected_failure: true   # ❌ 会让人误以为“测试应失败”，改用 case_type + expected_behavior
```

用 selector 定位（禁止）：

```yaml
- action: click
  target: "#submit-btn > span.btn-primary"   # ❌ 用“提交按钮”这类可读名称
```

含糊断言（禁止）：

```yaml
assertions:
  - type: correct
    target: "结果正确"   # ❌ 无法判定，必须写具体可观察的断言
```
