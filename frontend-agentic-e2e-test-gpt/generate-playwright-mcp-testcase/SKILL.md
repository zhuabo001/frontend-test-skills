---
name: generate-playwright-mcp-testcase
description: Generate structured, reviewable YAML test-case materials from feature plans, PRDs, user stories, or acceptance criteria for later execution through Playwright MCP. Use when Codex needs to analyze a new feature document, create or update a feature-specific directory under playwright-mcp-testcases, produce positive and meaningful negative browser scenarios, and maintain a manifest that traces requirements to cases. Do not use this skill to start an application, operate a browser, execute cases, or produce Playwright Test source code.
---

# Generate Playwright MCP Testcase

Convert feature requirements into MCP-executable exploratory test materials. Treat the output as an intermediate contract between requirements and a separate browser runner, not as final regression-test code.

## Read the format contract

Read [references/testcase-format.md](references/testcase-format.md) before generating files. Copy and adapt [assets/testcase-template.yaml](assets/testcase-template.yaml) and [assets/manifest-template.yaml](assets/manifest-template.yaml) instead of inventing a different structure.

## Generate the test materials

1. Read every source document named by the user. Do not infer product behavior from filenames alone.
2. Extract the feature name, functional points, acceptance criteria, roles, preconditions, validation rules, state changes, and externally observable outcomes.
3. Choose the output directory as `playwright-mcp-testcases/<feature-name>/`.
   - Use an explicit feature or plan name exactly when the source provides one.
   - Otherwise use the source document filename without its extension.
   - Replace only filesystem-invalid characters with `-`; do not silently rename the feature for style.
4. Create the root and feature directories when absent.
5. Build a coverage matrix before writing cases. For every functional point, include at least:
   - one positive case proving the intended path;
   - one meaningful negative case proving a validation, authorization, boundary, conflict, or recovery behavior.
6. Write one YAML file per case and one `manifest.yaml` in the feature directory.
7. Use stable, readable kebab-case case IDs and matching filenames: `<case-id>.yaml`.
8. Update the manifest so every generated case maps back to its source requirement.

## Write executable cases

- Keep each step atomic: one navigation, interaction, or observation per step.
- Prefer role, accessible name, label, placeholder, and visible text in `target`. Use CSS or XPath only when the requirement or repository explicitly provides a stable selector.
- State exact observable assertions. Never write vague outcomes such as `结果正确`, `页面正常`, or `操作成功`.
- Keep test data explicit and internally consistent. Use obviously synthetic data unless the source requires seeded data.
- Make cases independent where practical. Add cleanup only when the case can mutate persistent state.
- Record source references and assumptions. Do not invent unspecified UI copy, permissions, routes, or backend behavior.
- Put unresolved requirement gaps in `manifest.yaml` under `open_questions`. If a gap prevents a reliable assertion, mark the affected case `review_status: needs-review` and state the gap in `notes`.
- Preserve unrelated existing files. When regenerating, update files with matching case IDs and the manifest; do not delete unreferenced cases unless the user requests cleanup.

## Model negative behavior correctly

Use `case_type: negative` for invalid or disallowed user behavior. A negative case passes when the product rejects the action as specified.

For every negative case:

- set `expected_behavior` to the intended rejection category;
- assert the visible validation or error state;
- assert that forbidden success behavior did not occur when observable;
- assert retained page or form state when relevant;
- never add `expected_failure: true`.

For example, submitting a required field empty should pass when the validation appears and no record is created. It should fail only when the product violates that expected rejection.

## Validate before finishing

Check all generated files against the reference contract, then verify:

- all YAML is syntactically valid;
- every case file contains exactly one case;
- IDs and filenames match and are unique;
- the manifest references every active case and no missing file;
- every functional point has positive and negative coverage;
- every case has preconditions, explicit steps, observable assertions, and cleanup;
- transient UI assertions define a timeout;
- no case contains secrets, production credentials, or destructive production actions;
- no browser was opened and no application or test command was started.

Finish by reporting the output directory, generated and updated files, coverage totals, assumptions, and open questions.

Do not execute the generated cases. Leave execution, evidence collection, and JSON reporting to `run-playwright-mcp-testcases`.
