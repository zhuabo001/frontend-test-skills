# playwright-mcp 排障与安装/启动指引

SKILL.md 步骤 3 判定 playwright-mcp 不可用时，用本文件给用户可执行的原因与解决方法，然后停下等待，**不要伪造执行**。

## 目录

- [如何确认是否可用](#如何确认是否可用)
- [不可用的常见原因](#不可用的常见原因)
- [安装与启动](#安装与启动)
- [引导话术模板](#引导话术模板)

## 如何确认是否可用

playwright-mcp 以 MCP server 形式提供浏览器操作工具（如打开页面、快照、点击、截图等）。可用性判断：
- 当前会话是否暴露了 playwright / playwright-mcp 相关工具且可成功调用（如成功打开一个页面或取快照）。
- 若相关工具不存在，或调用报连接/启动错误 → 视为不可用。

不要因为"没试过"就假设可用；用一次最小调用（如打开 base_url 并取快照）来确认。

## 不可用的常见原因

1. **MCP server 未在客户端注册**：Claude Code / IDE 的 MCP 配置里没有 playwright-mcp 条目。
2. **server 未启动或已崩溃**：注册了但进程未运行。
3. **未安装**：`@playwright/mcp` 包或 Playwright 浏览器二进制未安装。
4. **浏览器二进制缺失**：装了包但没跑 `playwright install`。
5. **环境限制**：无头环境缺少依赖、端口占用、权限不足。

## 安装与启动

以下命令供**引导用户执行**（在其终端用 `! <command>` 或自行运行）。具体以团队/公司既有的 playwright-mcp 配置为准——若公司已有标准接入方式，优先按公司方式。

安装 Playwright 浏览器二进制：

```bash
npx playwright install
```

以 MCP server 方式运行 playwright-mcp（Node 环境）：

```bash
npx @playwright/mcp@latest
```

在 Claude Code 中注册该 MCP server（示例，名称与参数以实际为准）：

```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

注册后通常需**重启会话/客户端**让工具生效，再重新确认可用性。

## 引导话术模板

对用户说明时包含三要素：**结论 + 原因 + 下一步**。示例：

> playwright-mcp 当前不可用：会话里没有检测到可调用的 playwright 浏览器工具，判断是 MCP server 未注册/未启动。
> 请任选其一完成后告诉我，我再继续执行：
> 1. 若尚未安装浏览器：`! npx playwright install`
> 2. 注册并启动 server：`! claude mcp add playwright -- npx @playwright/mcp@latest`，然后重启本会话。
> 若你们公司已有 playwright-mcp 的标准接入方式，直接按公司方式启用即可。
> 启用后回来告诉我，我会重新确认可用性并开始跑用例。

停在此处等待，不要在 mcp 不可用时编造步骤结果或报告。
