---
name: generate-playwright-mcp-testcases
description: 从需求文档（plan.md / feature.md / prd.md / 用户故事 / 验收标准）生成可被 playwright-mcp 执行的 YAML 测试用例物料。为每个功能点生成结构化的正向用例与负向校验用例，写入 playwright-mcp-testcases 下与特性同名的子目录并附带 manifest.yaml。当用户需要“根据 plan/feature/需求生成测试用例”“把需求转成 playwright mcp 测试物料”“生成 e2e 测试 YAML”时使用。本技能只生成用例物料，不启动项目、不操作浏览器、不执行测试（执行由 run-playwright-mcp-testcases 负责）。
---

# Generate Playwright-MCP Testcases

## Overview

本技能把需求文档转换成**结构化、可被 Agent 执行的 YAML 测试意图物料**。产物供 `run-playwright-mcp-testcases` 技能用 playwright-mcp 解释并在真实浏览器中执行。

> **定位（必须始终牢记）**：本方案生成的是 MCP 探索测试物料，不是最终回归测试代码；只有稳定、有长期价值的用例才需要后续转为 Playwright Test。

本技能**只做生成**：读文档 → 识别功能点 → 产出 YAML + manifest。它**不**启动前端、**不**操作浏览器、**不**执行测试。

## 核心约定（不可违反）

1. **负向用例 ≠ 预期测试失败**。负向用例是“业务应当拒绝错误输入”，其正确表现（如出现校验提示、请求被阻止、页面不跳转）达成时结果应为 `passed`。因此**禁止**使用 `expected_failure: true`；改用 `case_type: negative` + `expected_behavior`。
2. **target 用人类可读的可访问名称**（如“新增用户按钮”“邮箱输入框”），**不要写 CSS selector / xpath**。playwright-mcp 依赖可访问性快照定位。
3. **每个用例必须有 `case_type`**（`positive` 或 `negative`）。
4. **每个负向用例必须明确写出“正确的失败表现”**（体现在 assertions 中，例如出现某段校验文案、URL 不变、无成功 toast）。
5. **assertions 必须具体**，不能只写“结果正确”。toast 类断言要带 `timeout_ms`（toast 短暂出现，容易被错过）。
6. **steps 必须原子化**，一步一个动作，禁止“测试一下创建是否正常”这种模糊描述。

完整字段定义、动作词表、断言词表、正/负向完整示例见 [references/yaml-schema.md](references/yaml-schema.md)——**开始生成前先读它**。

## 工作流

### 步骤 1：读取并理解需求文档

读取用户指定的文档（plan.md / feature.md / prd.md / 用户故事 / 验收标准）。若用户未指定，询问文档路径或让其粘贴内容。

提取：
- **特性名称**（feature/plan 名称）——用于目录命名。
- **功能点清单**——每个可独立验证的行为（如“创建用户”“删除用户”“搜索用户”）。
- 每个功能点的**输入/字段、前置条件、验收标准、边界与校验规则**。

### 步骤 2：为每个功能点设计用例

每个功能点**至少**生成：
- **1 个正向用例**（`case_type: positive`）——主成功路径。
- **1 个有意义的负向用例**（`case_type: negative`）——针对真实校验规则（必填、格式、重复、越权等），而非编造。

有多条校验规则时，为每条有价值的规则各写一个负向用例。优先覆盖验收标准里明确提到的规则。

用例内容需包含：`preconditions`、`test_data`、原子化 `steps`（含每步 `expected`）、具体 `assertions`、`cleanup`。字段用法严格遵循 [references/yaml-schema.md](references/yaml-schema.md)。

### 步骤 3：确定输出目录

1. 若 `playwright-mcp-testcases/` 目录不存在则创建（默认建在项目根目录；若用户另有指定则用指定路径）。
2. 在其下创建**与特性名/plan 名一致**的子目录（kebab-case，例如 `user-management`）。若已存在同名子目录，先读现有内容避免 id/文件名冲突，再增量补充。
3. 所有 YAML 与 manifest 写入该子目录。

### 步骤 4：写用例文件

- 每个 YAML 一个用例。
- **文件名 = 用例 id + `.yaml`**，用可读 kebab-case 描述意图与结果，例如：
  - `create-user-success.yaml`
  - `create-user-missing-name-validation.yaml`
  - `create-user-duplicate-email-validation.yaml`
- 文件内 `id` 字段必须与文件名（去掉扩展名）一致。

### 步骤 5：生成 manifest.yaml

在特性子目录下生成 `manifest.yaml`，索引本次生成的所有用例。结构见 [references/yaml-schema.md](references/yaml-schema.md) 的 “Manifest 结构” 一节。可从 [assets/manifest-template.yaml](assets/manifest-template.yaml) 复制起步。

### 步骤 6：向用户汇报

简要说明：特性名、输出目录、生成了几个用例（正向/负向各几个）、各自覆盖的功能点/校验规则。提示下一步可用 `run-playwright-mcp-testcases` 执行。

## 模板

- 单用例起步模板：[assets/case-template.yaml](assets/case-template.yaml)
- manifest 起步模板：[assets/manifest-template.yaml](assets/manifest-template.yaml)

复制模板后按实际需求填充；不要保留模板中的占位注释。

## 输出示例结构

```text
playwright-mcp-testcases/
  user-management/
    manifest.yaml
    create-user-success.yaml
    create-user-missing-name-validation.yaml
    create-user-duplicate-email-validation.yaml
```
