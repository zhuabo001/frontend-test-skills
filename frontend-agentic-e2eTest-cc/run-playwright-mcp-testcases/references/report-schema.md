# 报告状态与 JSON 结构参考

本文件定义状态五分类与每次运行的 JSON 报告结构。生成报告时严格遵循，保证结果可统计、可复查、可转缺陷单。

## 目录

- [状态五分类](#状态五分类)
- [报告文件位置](#报告文件位置)
- [顶层 JSON 结构](#顶层-json-结构)
- [case 对象结构](#case-对象结构)
- [完整示例](#完整示例)

## 状态五分类

判定用例最终 `status` 时，必须在下列之一中选择，不可混淆：

| 状态 | 含义 | 典型场景 |
|------|------|----------|
| `passed` | 用例执行完成，断言符合预期 | 正向成功；负向被正确拒绝 |
| `failed` | **功能行为**不符合预期 | 正向未成功；负向被错误放行（如空姓名却创建成功） |
| `blocked` | 前置条件不满足，无法开始/继续测试 | 未登录、依赖数据缺失、目标页面打不开 |
| `inconclusive` | Agent 无法可靠判断结果 | 找不到控件、页面状态含糊、断言无法确认 |
| `error` | 执行器或环境异常 | playwright-mcp 崩溃、超时、网络中断导致无法执行 |

关键纪律：
- **"没找到按钮/元素" → `blocked` 或 `inconclusive`，不是 `failed`**。`failed` 只留给"产品行为确实错误"。
- 负向用例的 `passed`/`failed` 方向见 [execution-guide.md](execution-guide.md)。
- 无法确定时选 `inconclusive` 并写清原因，禁止臆测。

`summary` 计数字段固定为：`total` / `passed` / `failed` / `blocked` / `inconclusive`（`error` 计入并单列，见示例可加 `error` 计数）。

## 报告文件位置

```text
playwright-mcp-testresults/<run_id>/<run_id>.json
```

`run_id` 格式：`run-<YYYY-MM-DD-HHMMSS>`（本地时间），即本次测试唯一标识。

## 顶层 JSON 结构

```jsonc
{
  "run_id": "run-2026-07-09-143000",     // 本次运行唯一标识
  "source_dir": "playwright-mcp-testcases", // 或具体特性子目录
  "base_url": "http://localhost:5173",
  "started_at": "2026-07-09T14:30:00+08:00", // ISO8601 带时区
  "ended_at": "2026-07-09T14:35:12+08:00",
  "duration_ms": 312000,
  "environment": {
    "browser": "chromium",
    "frontend_command": "npm run dev",
    "branch": "feature/user-management",   // 取不到写 "unknown"
    "commit": "unknown"
  },
  "summary": {
    "total": 6,
    "passed": 4,
    "failed": 1,
    "blocked": 1,
    "inconclusive": 0,
    "error": 0
  },
  "cases": [ /* case 对象数组，见下 */ ]
}
```

## case 对象结构

```jsonc
{
  "id": "create-user-missing-name-validation",
  "title": "创建用户时姓名为空应出现必填校验",
  "case_type": "negative",              // positive | negative
  "status": "passed",                   // 五分类之一
  "duration_ms": 43000,
  "steps": [
    {
      "index": 1,
      "action": "navigate",
      "target": "/users",
      "status": "passed",               // 该步 passed/failed/blocked/error
      "actual": "用户管理页面可见"        // 实际观察，必填
    }
  ],
  "assertions": [
    {
      "type": "visible_text",
      "target": "姓名不能为空",
      "status": "passed",
      "reason": "toast 在 1.2s 内出现，文案匹配"  // 判定理由，建议填
    }
  ],
  "evidence": {
    "screenshots": ["screenshots/create-user-missing-name-validation-final.png"],
    "console_errors": [],
    "network_errors": []
  },
  "failure": null                       // 非 passed 时填对象，见下
}
```

`failure` 对象（当 `status` 为 `failed`/`blocked`/`inconclusive`/`error` 时填，`passed` 时为 `null`）：

```jsonc
"failure": {
  "category": "product | environment | agent_uncertain | precondition",
  "message": "一句话说明失败/阻塞/无法判断的原因",
  "at_step": 4,                         // 相关步骤 index，可为 null
  "details": "更详细的上下文，可选"
}
```

`category` 与 `status` 的对应建议：`failed`→`product`；`error`→`environment`；`inconclusive`→`agent_uncertain`；`blocked`→`precondition`。

## 完整示例

```json
{
  "run_id": "run-2026-07-09-143000",
  "source_dir": "playwright-mcp-testcases/user-management",
  "base_url": "http://localhost:5173",
  "started_at": "2026-07-09T14:30:00+08:00",
  "ended_at": "2026-07-09T14:35:12+08:00",
  "duration_ms": 312000,
  "environment": {
    "browser": "chromium",
    "frontend_command": "npm run dev",
    "branch": "feature/user-management",
    "commit": "unknown"
  },
  "summary": { "total": 2, "passed": 1, "failed": 1, "blocked": 0, "inconclusive": 0, "error": 0 },
  "cases": [
    {
      "id": "create-user-missing-name-validation",
      "title": "创建用户时姓名为空应出现必填校验",
      "case_type": "negative",
      "status": "passed",
      "duration_ms": 43000,
      "steps": [
        { "index": 1, "action": "navigate", "target": "/users", "status": "passed", "actual": "用户管理页面可见" },
        { "index": 2, "action": "click", "target": "新增用户按钮", "status": "passed", "actual": "弹窗打开" },
        { "index": 3, "action": "fill", "target": "邮箱输入框", "status": "passed", "actual": "已填入 demo@example.com" },
        { "index": 4, "action": "click", "target": "提交按钮", "status": "passed", "actual": "出现校验提示，弹窗未关闭" }
      ],
      "assertions": [
        { "type": "visible_text", "target": "姓名不能为空", "status": "passed", "reason": "1.1s 内出现" },
        { "type": "url_should_not_change", "value": "/users", "status": "passed", "reason": "URL 未变" },
        { "type": "no_success_toast", "target": "创建成功", "status": "passed", "reason": "未出现成功提示" }
      ],
      "evidence": {
        "screenshots": ["screenshots/create-user-missing-name-validation-final.png"],
        "console_errors": [],
        "network_errors": []
      },
      "failure": null
    },
    {
      "id": "create-user-success",
      "title": "管理员成功创建普通用户",
      "case_type": "positive",
      "status": "failed",
      "duration_ms": 51000,
      "steps": [
        { "index": 1, "action": "navigate", "target": "/users", "status": "passed", "actual": "用户管理页面可见" },
        { "index": 2, "action": "click", "target": "提交按钮", "status": "failed", "actual": "点击后无成功提示，列表未新增" }
      ],
      "assertions": [
        { "type": "visible_text", "target": "创建成功", "status": "failed", "reason": "5s 内未出现成功 toast" }
      ],
      "evidence": {
        "screenshots": ["screenshots/create-user-success-final.png"],
        "console_errors": ["POST /api/users 500"],
        "network_errors": ["POST /api/users -> 500"]
      },
      "failure": {
        "category": "product",
        "message": "提交后创建请求返回 500，用户未创建",
        "at_step": 2,
        "details": "network 显示 POST /api/users 返回 500"
      }
    }
  ]
}
```
