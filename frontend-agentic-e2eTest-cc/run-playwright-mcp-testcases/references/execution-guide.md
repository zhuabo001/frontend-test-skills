# 单用例执行与判定细则

本文件补充 SKILL.md 步骤 5 的执行细节。目标：稳定执行、正确判定、留下可复查证据。

## 目录

- [用可访问性快照定位](#用可访问性快照定位)
- [动作词处理](#动作词处理)
- [断言词处理](#断言词处理)
- [负向用例判定方向](#负向用例判定方向)
- [toast 等瞬时元素](#toast-等瞬时元素)
- [状态判定决策树](#状态判定决策树)
- [证据收集](#证据收集)

## 用可访问性快照定位

用例的 `target` 是**人类可读名称**（如"新增用户按钮"）。定位控件时优先读取页面的可访问性快照（accessibility snapshot），按角色/名称匹配，**不要臆造 CSS selector**。

- 找到唯一匹配 → 操作。
- 多个匹配 → 结合上下文（就近文案、所在弹窗/区域）择一，并在 `actual` 记录如何消歧。
- 找不到匹配 → **不是 failed**。先做合理等待与重新快照；仍找不到则该步 `blocked`/`inconclusive`（见决策树）。

## 动作词处理

与用例 schema 对齐（generate 技能）：

- `navigate`：跳转到 target（相对路径拼 base_url，或完整 URL）。
- `click`：点击 target。
- `fill`：向 target 输入框填 value（先聚焦，必要时先 clear）。
- `clear`：清空 target。
- `select`：在 target 下拉中选 value。
- `check` / `uncheck`：勾选/取消。
- `hover`：悬停。
- `press`：按键 value（如 Enter）。
- `upload`：向 target 上传文件 value。
- `wait_for`：等待 target（文本/元素）出现，遵循 timeout_ms。

每步执行后在快照/页面上确认结果，写入该步 `actual` 与 `status`。遇到未知动作词，按其字面语义谨慎执行，无法执行则该步 `inconclusive` 并说明。

## 断言词处理

- `visible_text` / `not_visible_text`：页面应/不应出现某文案（瞬时文案配合 timeout_ms 主动等待）。
- `element_visible` / `element_hidden`：元素可见/隐藏。
- `url_should_be` / `url_should_not_change`：当前 URL 等于 value / 仍为 value。
- `no_success_toast`：不应出现成功提示（target 为成功文案）。
- `input_value`：输入框当前值等于 value。
- `row_count` / `list_contains`：列表数量/包含判定。
- `no_network_request_to`：不应发出到某接口路径的请求（结合 network 记录判断）。

每条断言逐一判定并写 `reason`。`required: true` 的断言是判定用例 pass/fail 的关键项：任一关键断言不符 → 用例倾向 `failed`（正向）或按负向方向判定。

## 负向用例判定方向

`case_type: negative` 的用例，其 `expected_behavior`（如 `validation_error`/`request_blocked`/`permission_denied`）达成即为**业务正确拒绝**：

- 校验提示按预期出现、URL 未跳转、无成功 toast、创建请求未发出/被拒 → **`passed`**。
- 系统**错误地放行**（如空必填却提交成功、越权却操作成功）→ **`failed`**（`failure.category = product`）。

切勿把"出现了校验错误提示"本身当成 failed——那正是负向用例期望的结果。

## toast 等瞬时元素

toast 短暂出现，容易错过。处理：

1. 在会触发 toast 的关键操作（如点提交）**之后立即**开始等待，不要先做别的。
2. 依断言 `timeout_ms`（无则默认约 5000ms）轮询/等待文案出现。
3. 一旦捕获，立即截图存证；即使消失也已记录。
4. 到时仍未出现：正向的成功 toast 未现 → 结合其他证据判 `failed` 或 `inconclusive`；负向的校验 toast 未现且也无其他拒绝表现 → 可能 `failed`（被错误放行）或 `inconclusive`（无法确认），据实判定。

## 状态判定决策树

对每个用例，按序判断最终 `status`：

1. 执行器/环境异常（mcp 崩溃、超时、断网）导致无法执行 → `error`。
2. 前置条件不满足（未登录、页面打不开、依赖数据缺失）→ `blocked`。
3. 关键控件反复找不到、页面状态含糊、断言无法可靠确认 → `inconclusive`。
4. 功能行为确实错误（正向未成功；负向被错误放行）→ `failed`。
5. 断言全部符合预期（正向成功；负向被正确拒绝）→ `passed`。

牢记：**"没找到按钮" 属于 3（inconclusive）或 2（blocked），绝不是 4（failed）**。

## 证据收集

每个用例至少：
- **末态截图**存入 `screenshots/`，命名含用例 id（如 `<id>-final.png`）。
- 记录 `console_errors`（页面 console 报错）。
- 记录 `network_errors`（失败请求）及负向用例关心的关键请求是否发出。

失败/异常用例额外在关键节点（触发点、报错弹窗）多截图，必要证据放 `evidence/`。所有路径以报告目录为基准写相对路径。
