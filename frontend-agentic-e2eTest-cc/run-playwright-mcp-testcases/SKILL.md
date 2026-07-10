---
name: run-playwright-mcp-testcases
description: 读取 playwright-mcp-testcases 下的 YAML 测试用例，用 playwright-mcp 在真实浏览器中逐个执行，收集截图/console/network 等证据，并输出结构化 JSON 报告到 playwright-mcp-testresults 下以 run-id 命名的目录。执行前会确认或引导启动前端服务、确认 playwright-mcp 可用性（不可用时给出原因与安装/启动指引）。支持全量执行（testcases 全目录）或按特性执行（单个特性子目录）。当用户需要“执行/跑 playwright mcp 测试用例”“运行 e2e YAML 用例并出报告”“对某特性做冒烟/探索测试”时使用。本技能只解释与执行现有 YAML，不重新设计用例（用例生成由 generate-playwright-mcp-testcases 负责）。
---

# Run Playwright-MCP Testcases

## Overview

本技能读取 `generate-playwright-mcp-testcases` 产出的 YAML 用例，用 **playwright-mcp** 在真实浏览器里执行，收集证据，输出可复查的 JSON 报告。

> **定位（必须始终牢记）**：本方案是 MCP 探索执行，不是最终回归测试代码，也不适合直接当 CI 门禁；只有稳定、有长期价值的用例才需要后续转为 Playwright Test。

本技能**只解释与执行现有 YAML**：不重新设计用例、不改用例内容。

## 核心约定（不可违反）

1. **状态五分类，不可混淆**：`passed` / `failed` / `blocked` / `inconclusive` / `error`。定义见 [references/report-schema.md](references/report-schema.md)。**"找不到按钮"是 `blocked` 或 `inconclusive`，绝不是 `failed`**。`failed` 仅指功能行为确实不符合预期。
2. **负向用例的判定反过来**：负向用例（`case_type: negative`）达成"业务正确拒绝"（校验提示出现、URL 不变、无成功 toast）时应判 `passed`；只有系统错误地放行（如真的提交成功）才判 `failed`。
3. **报告必须记录过程，不只记 pass/fail**：每一步做了什么、实际观察到什么、每条断言为何通过/失败、截图路径、console/network 异常，全部写入 JSON。
4. **toast 等瞬时元素要主动等待**：关键操作后立即按断言的 `timeout_ms` 主动等待并截图/读取快照，避免错过短暂提示而误判。
5. **不臆造结果**：无法可靠判断时用 `inconclusive` 并说明原因，不要猜 pass/fail。

## 执行工作流

按顺序执行。任一前置步骤失败，先解决或如实上报，不要跳过。

### 步骤 1：确定执行范围

- **全量测试**：`playwright-mcp-testcases/` 下所有特性子目录的全部 YAML。
- **特性测试**：`playwright-mcp-testcases/<某特性子目录>/*.yaml`。

用户未指定时，列出可用特性子目录让其选择。存在 `manifest.yaml` 时优先据其确定用例清单与顺序。

### 步骤 2：预检——前端服务

确认前端服务是否已运行（默认基址如 `http://localhost:5173`，以项目实际为准）：
- 已运行：记录 `base_url` 与启动命令，继续。
- 未运行：查看项目 `package.json`/README 得到启动命令（如 `npm run dev`），启动服务并等待就绪；或按需请用户用 `! <command>` 自行启动。无法确定基址时询问用户。

### 步骤 3：预检——playwright-mcp 可用性

确认 playwright-mcp 是否可用（能否调用其浏览器工具）：
- **可用**：继续。
- **不可用**：**给出原因并引导用户完成启动（含安装）**，然后停下等待，不要伪造执行。排障与安装/启动指引见 [references/playwright-mcp-setup.md](references/playwright-mcp-setup.md)。

### 步骤 4：初始化本次运行

- 生成 `run_id`：`run-<YYYY-MM-DD-HHMMSS>`（本地时间），**run_id 即本次测试的唯一标识**。
- 创建目录：`playwright-mcp-testresults/<run_id>/`，其下建 `screenshots/` 与 `evidence/`。
- 记录 `started_at` 与 environment（browser、frontend_command、branch、commit，取不到写 `unknown`）。

### 步骤 5：逐个执行用例

对每个 YAML：

1. 读取并解析用例。校验 `preconditions`：不满足 → 判 `blocked` 并说明，跳过其余步骤。
2. 依 `steps` 顺序用 playwright-mcp 操作浏览器：`navigate`/`click`/`fill`/`select` 等（动作/断言词表见用例 schema，与 generate 技能一致）。
   - **target 是人类可读名称**，用可访问性快照按名称定位控件，不要臆造 selector。
   - 每步记录 `actual`（实际观察）与该步 `status`。
   - 关键操作后依 `timeout_ms` 主动等待瞬时元素（尤其 toast）。
3. 校验 `assertions`：逐条判定并记录理由；注意负向用例的判定方向（见核心约定 2）。
4. 收集证据：至少末态截图存入 `screenshots/`；记录 console 错误、network 错误/关键请求；失败用例多截关键节点。
5. 汇总该用例 `status`（五分类）、`duration_ms`、`steps`、`assertions`、`evidence`、`failure`（失败/异常时填，无则 `null`）。
6. 执行 `cleanup`（如有）。负向用例通常无需清理。

单个用例执行细节与判定边界见 [references/execution-guide.md](references/execution-guide.md)。

### 步骤 6：写 JSON 报告

汇总所有用例，写入 `playwright-mcp-testresults/<run_id>/<run_id>.json`。记录 `ended_at`、`duration_ms` 与 `summary`（各状态计数）。**结构严格遵循 [references/report-schema.md](references/report-schema.md)**。截图/证据用相对报告目录的路径引用。

### 步骤 7：向用户汇报

简要给出：run_id、范围、summary 计数、失败/blocked/inconclusive 用例清单及一句话原因、报告 JSON 路径。**不要**逐条复述全部通过用例。

## 参考文件

- 状态定义与 JSON 报告完整结构：[references/report-schema.md](references/report-schema.md)
- 单用例执行与判定细则（含 toast、负向判定、证据）：[references/execution-guide.md](references/execution-guide.md)
- playwright-mcp 排障与安装/启动指引：[references/playwright-mcp-setup.md](references/playwright-mcp-setup.md)

## 输出示例结构

```text
playwright-mcp-testresults/
  run-2026-07-09-143000/
    run-2026-07-09-143000.json
    screenshots/
    evidence/
```
