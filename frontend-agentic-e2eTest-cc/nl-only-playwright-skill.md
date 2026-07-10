可行，而且**做成两个 skill 分体执行是合理的**。但我会稍微调整你的定义：第一个 skill 不只是“生成 YAML”，而是生成**可执行测试意图物料**；第二个 skill 不只是“跑 MCP”，而是负责**解释 YAML、操作浏览器、收集证据、输出结构化报告**。

最小闭环可以是：

```text
plan.md / feature.md
        ↓
Skill 1：测试用例生成
        ↓
playwright-mcp-testcases/feature(plan)-name/*.yaml
        ↓
Skill 2：MCP 执行与报告
        ↓
playwright-mcp-testresults/[runid]/*.json
```

## 一、两个 skill 分体的可行性

我建议拆成两个 skill：

```text
Skill A：mcp-testcase-generator
Skill B：mcp-testcase-runner
```

这样比一个大 skill 更清晰。

### Skill A：测试物料生成

输入：

```text
plan.md / feature.md / prd.md / 用户故事 / 验收标准
```

输出：

```text
playwright-mcp-testcases/
  [待测试的特性名称]/
    create-user-success.yaml
    create-user-missing-name-validation.yaml
    create-user-duplicate-email-validation.yaml
```

职责：

```text
读取新特性文档
识别功能点
生成正向用例
生成负向用例
补充前置条件、测试数据、操作步骤、断言
给每个用例起可读文件名
```

它不碰浏览器，不启动项目，不执行测试。

---

### Skill B：MCP 测试执行与报告

输入：

```text
playwright-mcp-testcases/下所有的yaml文件(全量测试)，或者是playwright-mcp-testcases/[某个特性子目录]/*.yaml作为特性测试
```
**注意**：runid就是本次测试的
执行：

```text
启动或确认前端服务
确认playwright-mcp状态是否可用，不可用请给出原因并引导用户完成plawright-mcp的启动(包括安装)
使用 playwright-mcp 打开页面
按 YAML 步骤操作
观察页面状态
验证断言
收集截图、console、network、错误信息
```

输出：

```text
playwright-mcp-testresults/
  run-2026-07-09-143000/
    run-2026-07-09-143000.json
    screenshots/
    traces-or-evidence/
```

它不重新设计用例，只解释和执行现有 YAML。

---

## 二、最关键的约定：负向用例不是“预期测试失败”

这里一定要定义清楚。

你说“预期成功以及预期失败的用例”，我建议改成：

```text
positive case：正向成功场景
negative case：负向校验场景
```

负向用例不是测试失败，而是业务应该拒绝错误输入。

例如：

```text
不填写必填字段点击提交
```

正确结果应该是：

```text
出现 “名称不能为空” toast
不发送创建请求，或请求被阻止
页面仍停留在当前表单
```

如果这些都符合，测试结果应该是：

```text
passed
```

如果系统真的提交成功了，才是：

```text
failed
```

所以 YAML 里不要写 `expected_failure: true`，容易误导。建议写：

```yaml
case_type: negative
expected_behavior: validation_error
```

---

## 三、建议的 YAML 用例格式

一个 YAML 一个用例是可以的。建议控制成这种结构：

```yaml
id: create-user-missing-name-validation
title: 创建用户时姓名为空应出现必填校验
feature: user-management
case_type: negative
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

  - type: url_should_not_change
    value: "/users"

  - type: no_success_toast
    target: "创建成功"

cleanup:
  - 无需清理，因为用例不应创建数据
```

注意几点：

```text
1. target 尽量写成人能理解的可访问名称，而不是 CSS selector。
2. assertions 要明确，不要只写“结果正确”。
3. 每个用例必须有 case_type。
4. 每个负向用例必须说明“正确的失败表现”。
```

---

## 四、报告 JSON 应该包含哪些指标

我建议每次执行生成一个总报告 JSON：

```text
playwright-mcp-testresults/run-<timestamp>.json
```

结构可以这样：

```json
{
  "run_id": "run-2026-07-09-143000",
  "source_dir": "playwright-mcp-testcases",
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
  "summary": {
    "total": 6,
    "passed": 4,
    "failed": 1,
    "blocked": 1,
    "inconclusive": 0
  },
  "cases": [
    {
      "id": "create-user-missing-name-validation",
      "title": "创建用户时姓名为空应出现必填校验",
      "case_type": "negative",
      "status": "passed",
      "duration_ms": 43000,
      "steps": [
        {
          "index": 1,
          "action": "navigate",
          "target": "/users",
          "status": "passed",
          "actual": "用户管理页面可见"
        }
      ],
      "assertions": [
        {
          "type": "visible_text",
          "target": "姓名不能为空",
          "status": "passed"
        }
      ],
      "evidence": {
        "screenshots": [
          "screenshots/create-user-missing-name-validation-final.png"
        ],
        "console_errors": [],
        "network_errors": []
      },
      "failure": null
    }
  ]
}
```

状态建议定义为：

```text
passed：用例执行完成，断言符合预期
failed：功能行为不符合预期
blocked：前置条件不满足，无法测试
inconclusive：Agent 无法可靠判断结果
error：执行器或环境异常
```

这里一定要有 `blocked` 和 `inconclusive`，否则 Agent 很容易把“我没找到按钮”误判成“产品失败”。

---

## 五、这个 demo 的优势

这套 demo 有几个明显优点：

```text
1. 不要求马上写 Playwright Test 代码，落地快。
2. 可以直接利用公司已有 playwright-mcp 能力。
3. YAML 用例可 review，比纯 prompt 稳定。
4. 正向/负向用例可以从 plan.md 自动生成。
5. JSON 报告方便后续做统计、看板或转成缺陷单。
6. 后续可以把稳定用例再沉淀成 Playwright Test。
```

对 demo 来说，这个方向是合适的。

---

## 六、主要风险

### 1. YAML 过于自然语言，执行会不稳定

如果 steps 写成：

```yaml
- 测试一下创建用户是否正常
```

就太模糊了。

应该拆成：

```yaml
- action: click
  target: 新增用户按钮
- action: fill
  target: 用户名输入框
  value: Alice
```

### 2. MCP 识别 toast 仍可能不稳定

这正好和你前面担心的一致。toast 通常短暂出现，MCP/Agent 可能错过。解决方式是在 YAML 里明确：

```yaml
assertions:
  - type: visible_text
    target: "姓名不能为空"
    timeout_ms: 5000
```

并要求 runner 在关键操作后主动等待、截图、读取页面状态。

### 3. 报告不能只记录最终 pass/fail

必须记录：

```text
每一步做了什么
实际观察到了什么
断言为什么通过或失败
截图在哪里
console/network 有没有异常
```

否则失败报告没有可复查价值。

### 4. 不要把这个 demo 当成 CI 门禁

这套方案当前更适合：

```text
新特性冒烟测试
Agent 探索性测试
需求到测试物料生成
模糊 bug 复现
```

不适合一开始就作为严格 CI gate。

长期稳定用例仍然应该转成 Playwright Test。

---

## 七、我建议的两个 skill 边界

### Skill 1：`generate-playwright-mcp-testcases`

职责：

```text
读取指定 plan.md
创建 playwright-mcp-testcases 目录(如果没这个目录则需要创建)，有的话请在这个目录下创建一个新的目录，目录名称必须和feature名称或者plan名称保持一致
生成多个 YAML 用例
每个功能点至少包含：
  - 1 个正向用例
  - 1 个有意义的负向用例
生成 testcase-manifest.json 或 manifest.yaml
```

输出：

```text
playwright-mcp-testcases/
  manifest.yaml
  create-user-success.yaml
  create-user-missing-name-validation.yaml
```

### Skill 2：`run-playwright-mcp-testcases`

职责：

```text
读取 playwright-mcp-testcases
确认或启动前端服务
确认playwright-mcp状态，若已开启就继续下面流程，若提示mcp不可用，需要给出原因和解决方法
逐个执行 YAML
使用 playwright-mcp 操作浏览器
收集证据
输出 JSON 报告
```

输出：

```text
playwright-mcp-testresults/
  run-2026-07-09-14300/
    run-2026-07-09-143000.json
    screenshots/
    evidence/
```

---

## 八、最终评价

这个方案做成两个 skill **可行，而且适合快速 demo**。

但我会给它一个准确定位：

```text
它不是最终的自动化测试体系，
而是“需求文档 → Agent 可执行测试物料 → MCP 探索执行 → JSON 证据报告”的最小闭环。
```

最重要的设计点是：

```text
1. YAML schema 必须足够结构化。
2. 负向用例必须定义为“业务校验成功”，不是“测试失败”。
3. JSON 报告必须记录步骤、断言和证据。
4. MCP 执行失败要区分产品失败、环境阻塞和 Agent 无法判断。
5. 稳定高价值用例后续应沉淀成 Playwright Test。
```

用这个 demo 跑通，但建议在 skill 里明确写死这句话：

> **本方案生成的是 MCP 探索测试物料，不是最终回归测试代码；只有稳定、有长期价值的用例才需要后续转为 Playwright Test。**

