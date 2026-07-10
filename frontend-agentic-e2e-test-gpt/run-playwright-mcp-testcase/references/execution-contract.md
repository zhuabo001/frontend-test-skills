# Execution contract

## Contents

- [Input selection](#input-selection)
- [Input validation](#input-validation)
- [Environment preparation](#environment-preparation)
- [Playwright MCP readiness](#playwright-mcp-readiness)
- [Authentication](#authentication)
- [Case lifecycle](#case-lifecycle)
- [Actions and assertions](#actions-and-assertions)
- [Status decisions](#status-decisions)
- [Safety and evidence](#safety-and-evidence)

## Input selection

Accept these scopes:

1. `playwright-mcp-testcases/`: discover feature directories recursively.
2. `playwright-mcp-testcases/<feature>/`: execute that feature.
3. One or more explicit case YAML files.

For each feature directory:

- Load `manifest.yaml` when present.
- Execute only entries under `cases`, in listed order.
- Resolve each `file` relative to the manifest directory.
- Never execute `manifest.yaml` as a case.
- Without a manifest, execute non-manifest `*.yaml` files in lexical order and add a warning.

For an explicit file selection, preserve the user's order.

## Input validation

Accept case schema version `"1.0"`. Require:

- `id`, `title`, `feature`
- `case_type`: `positive` or `negative`
- `priority`
- `review_status`
- `preconditions`
- `test_data`
- `steps`
- `assertions`
- `cleanup`

Require `expected_behavior` for negative cases. Require an `action` on every step and a `type` on every assertion.

Handle invalid inputs without editing them:

- YAML parse failure or structurally invalid case: create a synthetic result from its filename with status `error`.
- Unsupported schema version: status `error`.
- `review_status: needs-review`: status `blocked` unless the user explicitly resolves the noted gap.
- Duplicate case ID: mark every conflicting case `error`.
- Manifest entry points to a missing file: create an `error` result for that entry.
- Case file exists but is not referenced by a manifest: do not run it in manifest-driven mode; add a warning.

Validate the complete selection before browser execution so input errors are visible even when MCP readiness later fails.

## Environment preparation

Resolve the frontend command from repository documentation and package scripts. Do not invent a command from framework convention when the repository contradicts it.

Before starting a service:

- confirm required dependencies already exist;
- request permission before installing missing dependencies or making persistent configuration changes;
- preserve the command and startup diagnostics in the report;
- do not use terminal output as proof that the canonical target is HTTP-ready.

Reuse an already healthy service when possible. Otherwise start the documented service command before the target-URL confirmation gate. Starting a service and seeing terminal URLs does not establish which browser origin the backend accepts.

After the service is running and before Playwright MCP readiness probes, authentication, or case execution, resolve one canonical base URL using this priority:

1. Explicit user-provided URL.
2. Repository E2E or application configuration, including `vite.config.*`, `vitest.config.*`, and shared configuration imported by those files.
3. User clarification when configuration does not yield one complete, unambiguous target.

When inspecting configuration:

- Prefer an intentional public/browser origin such as `server.origin` over a socket bind address.
- Combine an explicitly configured protocol, hostname, port, and base path without dropping any component.
- Treat `0.0.0.0`, `::`, and boolean host settings as listen behavior, not as a browser hostname.
- Treat environment-variable references as unresolved unless their effective values are available without exposing secrets.
- Treat multiple domain or port candidates as ambiguous unless repository rules clearly select one for the current environment.
- Do not infer the canonical target from Vite's `Local` or `Network` terminal output. Those URLs may reach the frontend while still being rejected by an enterprise backend or SSO policy.

If configuration does not provide one complete target, ask the user for the exact browser URL and port. Require enough information to construct an absolute `http` or `https` URL, including any base path; have the user explicitly confirm a default port such as 80 or 443 when no port appears in the URL. Keep the report in progress and do not operate the MCP browser while this clarification is pending. If the user cancels or cannot provide the target, leave `base_url` unset and mark otherwise runnable cases `blocked` with `precondition_unmet` rather than guessing.

Once confirmed, the canonical base URL is immutable for that run:

- Store the exact value in the report's `base_url`.
- Perform the HTTP-ready check against that exact URL. If it is unreachable, report the environment failure; do not fall back to a terminal-advertised URL.
- Resolve every relative application navigation against it, preserving its origin and base path.
- Before following an absolute application URL from a testcase or page, compare its origin with the confirmed target. Ask for new user confirmation instead of silently switching to a different origin.
- Allow a different origin only for an expected authentication-provider redirect. After authentication, verify that the browser returns to the confirmed application origin before continuing.

Stop only a service process started by this run. Record whether the service was reused, started, stopped, or left running.

Treat public domains, production hostnames, and non-local targets as production-like unless the user or repository proves otherwise. Block create, update, delete, upload, payment, notification, and other side-effecting cases until the user explicitly authorizes the target and scope.

## Playwright MCP readiness

Check actual callable Playwright MCP tools, not package presence. Perform a harmless probe such as creating or inspecting a blank page when supported.

Classify readiness failures:

- `not_configured`: no Playwright MCP server/tools are available.
- `connection_failed`: the configured MCP server cannot be reached.
- `executable_missing`: the configured server command or package is absent.
- `browser_missing`: the server runs but cannot launch its browser.
- `permission_denied`: sandbox, filesystem, display, or process permission blocks it.
- `launch_failed`: another startup error prevents a usable browser.
- `capability_missing`: a required capability such as network observation is unavailable.

When unavailable:

1. Preserve the exact tool or process error.
2. Inspect the detected MCP client's configuration and local command help.
3. Use current official Playwright MCP documentation when local information is insufficient.
4. Provide host-specific installation/configuration steps, including the verified installation command when installation is missing.
5. State whether the MCP host must be restarted or reloaded.
6. Finalize the run as `error` when user action is required.

When readiness fails before execution, create an `error` result with category `executor_failure` for every otherwise-runnable selected case. Do not report these as product failures.

Do not silently fall back to Playwright Test, Playwright CLI, Chrome control, an in-app browser, or generic computer control.

## Authentication

Determine authentication requirements from explicit user input, case preconditions, case intent, and navigation behavior. Do not change the testcase schema.

Treat a case as anonymous when its preconditions explicitly require a logged-out state or its purpose is to test login, logout, or unauthenticated access. Do not bootstrap authentication for that case. Treat a case as authentication-dependent when its preconditions require a logged-in role or its target redirects to login without authentication.

Resolve authentication in this order:

1. **Existing session**: probe the protected target in the current MCP session. Use `existing_session` only when the target remains accessible and page identity is reliable.
2. **Authentication state**: use `storage_state` only when the user explicitly provides a path and the active MCP server supports importing it without exposing its contents to the agent. Require the path to be outside the repository or covered by ignore rules. Never copy, inspect, print, or report the file or path.
3. **Manual login**: use this default for enterprise accounts. Confirm the MCP browser is headed, visible, interactive, and expected to preserve the same session across turns. Navigate to login, persist `run_status: waiting_for_auth` and `authentication.status: awaiting_user`, then ask the user to complete login in the browser. Do not request credentials in chat. Apply no automatic timeout. After the user confirms, re-probe the first protected target in the same session before setting `authenticated`.
4. **Credentials**: use only when the user explicitly opts in, the account is a dedicated non-production test account, and MCP provides a secret-safe input capability that keeps values out of prompts, tool arguments, traces, screenshots, and reports. Accept only secure environment or secret-provider references; never accept inline credentials, testcase data, or chat messages. Fall back to manual login if the capability is absent.

If credentials mode encounters SSO, MFA, CAPTCHA, QR code, a security key, or any other human challenge, stop automatic input, set `mfa_encountered: true`, and switch to manual login.

When resuming manual login:

1. Recheck that the original MCP session still exists.
2. Navigate to the first authentication-dependent target.
3. Confirm that the application no longer returns to login and that the expected protected page identity is observable.
4. Set `authentication.status: authenticated` and continue.

If the user cancels, the session is lost, the browser is headless, or authentication cannot be verified, set authentication to `blocked`. Mark authentication-dependent cases `blocked` with failure category `authentication_unavailable` or `precondition_unmet`; do not mark them `failed`. Continue explicitly anonymous cases only when their session isolation remains reliable.

For mixed suites, use an anonymous isolated context for login/logout cases when MCP supports it. If a trustworthy anonymous context cannot be established without destroying the authenticated session, mark those cases `blocked` rather than contaminating their result.

## Case lifecycle

For each valid, ready case:

1. Create a case result with start time.
2. Establish isolation as far as Playwright MCP supports. Use a new context when available; otherwise reset navigation and record any shared-session limitation.
3. Check each precondition. Apply the resolved authenticated or anonymous state. Never satisfy authentication by reading plaintext secrets from test data or repository files.
4. Start console/network observation when supported and clear unrelated prior entries.
5. Execute steps in order.
6. Evaluate all required assertions.
7. Attempt cleanup when safe, even after failure.
8. Capture final or failure evidence.
9. Set end time, duration, status, and failure details.
10. Atomically refresh the JSON report.

Continue after case-level `failed`, `blocked`, `inconclusive`, or recoverable `error`. Stop remaining cases only when shared environment or executor state is no longer trustworthy. Mark unstarted cases `blocked` for a missing shared precondition or service, and `error` for an executor failure; explain the fatal dependency.

## Actions and assertions

Interpret common actions:

- `navigate`, `click`, `fill`, `select`
- `check`, `uncheck`, `upload`
- `press`, `hover`, `wait_for`, `reload`

Resolve targets in this order:

1. accessible role and name;
2. label;
3. placeholder;
4. visible text;
5. stable test ID;
6. stable CSS selector;
7. XPath only as a last resort.

Fail an action only when its intended outcome is contradicted by reliable evidence. Ambiguous target matching or an unobservable transient state is normally `inconclusive`.

Interpret common assertions:

- visibility: `visible_text`, `hidden_text`, `element_visible`, `element_hidden`;
- control state: `field_value`, `enabled`, `disabled`, `checked`, `count`;
- navigation: `url`, `url_contains`, `url_should_not_change`;
- network: `request`, `no_request`, `response_status`.

Honor `timeout_ms`. For transient UI, begin observation before the triggering action and capture evidence immediately afterward.

Do not pass `no_request` or network assertions if network observation was unavailable. Mark the assertion and case `inconclusive` unless another required assertion already proves failure.

## Status decisions

Use:

- `passed` only when all required assertions pass.
- `failed` only for a demonstrated product mismatch.
- `blocked` for unmet preconditions or review gates.
- `inconclusive` for ambiguous target resolution or insufficient observation.
- `error` for malformed inputs or executor/environment faults.

Negative cases pass when the expected rejection occurs. A validation error, authorization denial, or rejected conflict is successful test behavior when declared by the case.

Use failure categories:

- `product_mismatch`
- `precondition_unmet`
- `authentication_unavailable`
- `testcase_invalid`
- `executor_failure`
- `environment_failure`
- `observation_ambiguous`

## Safety and evidence

- Never request credentials in chat or place them in testcase YAML.
- Never write credentials, tokens, cookies, authorization headers, authentication-state paths, or secret environment values into prompts, tool traces, screenshots, evidence, or reports.
- Do not read authentication-state file contents; pass an explicitly supplied path directly to MCP only when supported.
- Avoid screenshots containing secrets or unrelated personal data.
- Use synthetic test data and non-production targets by default.
- Do not interpret unrelated console warnings as product failures.
- Record console and network errors with timestamps and case scope.
- Store paths relative to the run directory.
- Include at least one final screenshot for a passed case when screenshots are supported.
- Include the failure point snapshot and available console/network context for every non-passed executed case.
- If an evidence capability is unavailable, record it under `environment.limitations`; do not fabricate an empty successful observation.
