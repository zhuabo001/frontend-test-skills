---
name: run-playwright-mcp-testcase
description: Execute existing structured YAML browser cases through Playwright MCP, resolve and lock the project-specific browser URL and port for local or enterprise development environments, handle authenticated applications with reusable sessions or human-in-the-loop enterprise login, collect screenshots and console/network evidence, and write a per-run JSON report under playwright-mcp-testresults. Use when Codex needs to run every case under playwright-mcp-testcases, run one feature directory or selected case files, confirm or start the frontend service, discover a custom development domain from Vite or Vitest configuration, ask the user to clarify an unresolved target URL, diagnose Playwright MCP availability, pause for SSO or MFA, distinguish product failures from blocked, inconclusive, and executor-error outcomes, or produce an evidence-backed exploratory test report. Do not use this skill to generate, redesign, or silently repair test cases, or to run Playwright Test source files.
---

# Run Playwright MCP Testcase

Interpret existing YAML test intent, execute it with Playwright MCP, and preserve enough evidence for another person to review each result.

This workflow is MCP-based exploratory execution, not a CI gate. Do not substitute `@playwright/test`, Playwright CLI, a generic browser plugin, or another browser tool without explicit user approval.

## Read the contracts

Read [references/execution-contract.md](references/execution-contract.md) before selecting cases or operating the browser. Read [references/report-format.md](references/report-format.md) before creating the run directory or report. Use [assets/report-template.json](assets/report-template.json) as the report skeleton.

## Select and validate cases

1. Resolve the requested scope:
   - no explicit path: run all feature directories under `playwright-mcp-testcases/`;
   - feature directory: run only cases listed by that directory's `manifest.yaml`;
   - explicit YAML files: run only those case files.
2. Exclude every `manifest.yaml` from execution.
3. Prefer manifest order. Without a manifest, use lexical filename order and add a report warning.
4. Parse and validate inputs before opening a browser. Do not edit invalid YAML.
5. Treat `review_status: needs-review`, unsupported schema versions, missing required fields, duplicate IDs, and missing manifest targets according to the execution contract.

## Prepare the run

1. Generate one unique local-time run ID in the form `run-YYYY-MM-DD-HHMMSS`. If it already exists, append `-02`, `-03`, and so on.
2. Create:

   ```text
   playwright-mcp-testresults/<run-id>/
     <run-id>.json
     screenshots/
     evidence/
   ```

3. Initialize the JSON report before execution and update it after every case so an interrupted run retains valid results.
4. Determine the frontend command from repository documentation, environment configuration, and existing package scripts. Do not treat URLs printed by the command as the confirmed browser target.
5. Reuse a healthy existing frontend service. Start only a documented project command when needed, record it, and stop only a process started by this run.
6. After the service is running and before any Playwright MCP navigation, resolve and lock one canonical base URL:
   - prefer an explicit user-provided URL;
   - otherwise inspect repository application/E2E configuration, including `vite.config.*`, `vitest.config.*`, and shared configuration imported by those files, for an intentional browser origin, hostname, port, and base path;
   - distinguish a bind address such as `0.0.0.0` from the hostname that a browser must use;
   - if there is no single complete and unambiguous target, ask the user for the exact URL and port and pause before browser execution;
   - probe the service through that exact target; do not silently fall back to a localhost, network, or other URL printed by the dev server.
7. Store the confirmed target in `base_url` and use it for every application navigation in the run. Resolve relative case paths against it. Do not navigate to a conflicting application origin without new user confirmation; authentication-provider redirects are allowed only as part of the authentication flow and must return to the confirmed application target.
8. Block mutating cases against a production-like target unless the user explicitly authorizes that exact target and scope.
9. Determine which selected cases require an authenticated or anonymous session from their preconditions, intent, redirects, and explicit user input. Do not pre-authenticate login, logout, or explicitly anonymous cases.

## Verify Playwright MCP

Inspect available tools and perform a harmless readiness probe before executing cases.

- Continue only with an operational Playwright MCP browser session.
- If unavailable, identify the failure category and preserve the exact diagnostic message.
- Give installation, configuration, browser-binary, permission, or restart guidance appropriate to the detected MCP host. Verify current commands from local help or official documentation rather than guessing.
- Do not claim that MCP is available because a Playwright package or browser exists in the repository.
- If readiness cannot be restored without user action, finalize the run as `error`; do not mark product cases `failed`.

## Authenticate when required

Resolve authentication before executing the first authentication-dependent case:

1. Reuse an already-authenticated MCP browser session when it reaches the protected target without returning to login.
2. If the user explicitly supplies an authentication-state path and MCP supports path-based import, pass the path to MCP without reading its contents. Require the file to be outside the repository or ignored.
3. Otherwise use manual authentication:
   - confirm that the MCP browser is visible and interactive;
   - navigate to login;
   - write `run_status: waiting_for_auth` and `authentication.status: awaiting_user`;
   - ask the user to complete login in that browser, never to paste credentials into chat;
   - wait without an automatic timeout;
   - after confirmation, verify the same session against the first protected target before resuming.
4. Use automatic credentials only after explicit user authorization, only for a non-production test account, and only when MCP exposes a secret-safe input capability that does not reveal values in prompts, tool arguments, traces, or reports.
5. Switch to manual authentication when automatic login encounters SSO, MFA, CAPTCHA, QR code, a security key, or another human challenge.

If the user cancels, the visible session is lost, or a headed browser is unavailable, mark only authentication-dependent cases `blocked` with `precondition_unmet` or `authentication_unavailable`. Continue cases that explicitly require an anonymous session when their isolation remains reliable. Never classify an authentication bootstrap failure as a product failure unless the selected case itself tests authentication.

## Execute each case

For every runnable case:

1. Establish the cleanest browser state supported by the MCP tools and satisfy the declared preconditions using the required authenticated or anonymous session.
2. Start case-scoped console and network observation when supported.
3. Perform steps in order using accessible page information. Resolve targets by role/name, label, placeholder, visible text, test ID, then stable selector.
4. After every action, wait only as required for the declared expected state. Capture transient messages immediately.
5. Record each step's action, actual observation, status, duration, and relevant evidence.
6. Evaluate every assertion from browser-observable evidence. Do not infer success from the absence of a tool error.
7. Run cleanup even after a failed assertion when safe.
8. Save a final screenshot for passed cases and failure-point evidence for all non-passed cases.
9. Finalize the case status and continue with independent cases unless a fatal environment or executor error makes further results unreliable.

For a negative case, pass it when the specified rejection behavior occurs. Never treat `case_type: negative` as an expected test failure.

## Classify results

- `passed`: execution completed and every required assertion matched.
- `failed`: reliable evidence shows product behavior violated an expected assertion.
- `blocked`: a declared precondition, required test datum, authentication state, service, or review gate prevented execution.
- `inconclusive`: execution occurred, but the agent or available evidence cannot reliably decide the result.
- `error`: invalid input or an MCP, browser, environment, or runner failure prevented reliable execution.

Do not classify “the agent could not locate the target” as `failed` unless the page identity is verified, the expected element should be present at that point, and the accessible snapshot reliably proves absence.

## Finalize the report

Recalculate totals, set end time and duration, finalize the authentication record, and run `python3 scripts/validate_report.py <report-path>`. Fix every reported error before presenting the run as complete. Keep evidence paths relative to the run directory and redact secrets, cookies, tokens, credentials, authentication-state paths, and unnecessary personal data.

Report the run ID, scope, base URL, effective authentication mode and status, totals by status, report path, failed/blocked/inconclusive/error case IDs, MCP or environment limitations, and whether a frontend process remains running.

Do not rewrite test-case YAML during or after the run. Report defects in the test material separately from product failures.
