# JSON report format

Create one JSON report at:

```text
playwright-mcp-testresults/<run-id>/<run-id>.json
```

Start from [../assets/report-template.json](../assets/report-template.json). Keep the report valid JSON after every completed case.

Replace every angle-bracket placeholder before finalization. Replace the illustrative item under `cases` with actual selected-case records; do not retain it as a result.

New reports use schema version `"1.1"`. The validator continues to accept existing `"1.0"` reports, which do not contain an authentication record.

## Run identity

Use a local-time ID:

```text
run-YYYY-MM-DD-HHMMSS
```

The run ID identifies one execution instance. It is not a test-case or suite version. On collision, append `-02`, `-03`, and so on.

Use RFC 3339 timestamps with explicit timezone offsets for `started_at` and `ended_at`. Store durations as integer milliseconds.

## Run status

Use:

- `running`: execution is in progress.
- `waiting_for_auth`: the headed MCP browser is waiting for the user to complete manual authentication.
- `completed`: all selected cases have terminal statuses, even if some failed.
- `partial`: execution stopped after at least one case because the shared environment became unreliable.
- `error`: no reliable case execution could proceed because of selection, environment, or executor failure.
- `aborted`: the user stopped the run.

`running` and `waiting_for_auth` are intermediate states. A finalized report must use `completed`, `partial`, `error`, or `aborted`.

## Canonical base URL

Use `base_url` for the exact application target confirmed during environment preparation. It must be an absolute `http` or `https` URL and preserve the required hostname, effective port, and base path. Do not replace it with a localhost, network, or other URL merely because the frontend command printed that URL.

Resolve all relative application navigations against this value. A temporary authentication-provider redirect does not change `base_url`; verify that authentication returns to the confirmed application origin. Leave `base_url` as `null` only when target clarification or environment preparation prevented all browser execution, and explain that outcome in case failures or `run_errors`.

## Authentication record

Schema `"1.1"` reports require:

```json
{
  "authentication": {
    "required_for_selected_cases": true,
    "mode": "manual",
    "status": "authenticated",
    "session_reused": false,
    "mfa_encountered": true,
    "diagnostic": "User completed enterprise SSO in the shared browser."
  }
}
```

Allow these modes:

- `none`
- `existing_session`
- `storage_state`
- `manual`
- `credentials`

Allow `checking` and `awaiting_user` only while the report is in progress. A finalized authentication status must be:

- `not_required`
- `authenticated`
- `blocked`
- `error`

Use `mode: none`, `status: not_required`, and `required_for_selected_cases: false` when no selected case needs authentication. Do not record account names, credential references, passwords, tokens, cookies, authorization headers, secret values, or authentication-state paths. Keep `diagnostic` factual and redacted.

## Summary invariant

Maintain:

```text
total = passed + failed + blocked + inconclusive + error
```

`total` counts every selected case, including synthetic results created for malformed or missing files.

## Case records

Each case record must include:

- source identity: `id`, `title`, `feature`, `case_type`, `source_file`;
- timing and final `status`;
- precondition checks;
- step results with actual observations;
- assertion results with expected and actual behavior;
- cleanup results;
- evidence paths and scoped console/network errors;
- one failure object or `null`.

Use `null` for unavailable scalar values. Use empty arrays only when collection ran and found nothing. When collection was unsupported, describe it in `environment.limitations`.

## Evidence paths

Keep evidence under the run directory:

```text
screenshots/<case-id>-step-<index>.png
screenshots/<case-id>-final.png
evidence/<case-id>-console.json
evidence/<case-id>-network.json
```

Write relative paths such as `screenshots/create-user-success-final.png` into the report. Do not embed binary data.

## Failure object

Use `failure: null` for passed cases. Otherwise record:

```json
{
  "category": "product_mismatch",
  "message": "Expected validation text was not visible within 5000 ms.",
  "step_index": 4,
  "assertion_index": 1,
  "diagnostic": "Form remained open and the create request returned 201."
}
```

Use the categories defined in the execution contract. Keep messages factual and evidence-based.

## Report integrity

Before finalizing:

- verify all selected cases appear exactly once;
- recalculate summary counts from case records;
- verify `duration_ms` values are non-negative integers;
- verify every referenced evidence file exists;
- verify `base_url` is the confirmed canonical application target whenever browser execution occurred;
- remove or redact secrets and unnecessary personal data;
- verify schema `"1.1"` has a terminal authentication status and no secret-bearing fields;
- set `ended_at`, `duration_ms`, and final `run_status`;
- run `python3 scripts/validate_report.py <report-path>` from the skill directory and fix every reported error.
