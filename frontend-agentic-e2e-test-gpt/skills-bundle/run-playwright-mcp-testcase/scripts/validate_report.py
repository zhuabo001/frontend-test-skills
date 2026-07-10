#!/usr/bin/env python3
"""Validate a finalized Playwright MCP JSON run report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}
RUN_STATUSES = {"completed", "partial", "error", "aborted"}
CASE_STATUSES = {"passed", "failed", "blocked", "inconclusive", "error"}
SUMMARY_KEYS = ("passed", "failed", "blocked", "inconclusive", "error")
AUTH_MODES = {"none", "existing_session", "storage_state", "manual", "credentials"}
FINAL_AUTH_STATUSES = {"not_required", "authenticated", "blocked", "error"}
REQUIRED_AUTH_KEYS = {
    "required_for_selected_cases",
    "mode",
    "status",
    "session_reused",
    "mfa_encountered",
    "diagnostic",
}
SENSITIVE_KEYS = {
    "access_token",
    "account",
    "account_id",
    "account_name",
    "api_key",
    "auth_header",
    "auth_state_path",
    "authentication_state_path",
    "authorization",
    "authorization_header",
    "client_secret",
    "cookie",
    "cookies",
    "credential",
    "credential_ref",
    "credentials",
    "id_token",
    "password",
    "password_ref",
    "passwd",
    "refresh_token",
    "secret",
    "secret_ref",
    "set_cookie",
    "storage_state_path",
    "token",
    "username",
    "username_ref",
}
REQUIRED_REPORT_KEYS = {
    "schema_version",
    "run_id",
    "run_status",
    "base_url",
    "selection",
    "started_at",
    "ended_at",
    "duration_ms",
    "environment",
    "executor",
    "summary",
    "cases",
    "run_errors",
    "warnings",
}
REQUIRED_CASE_KEYS = {
    "id",
    "title",
    "feature",
    "case_type",
    "source_file",
    "status",
    "started_at",
    "ended_at",
    "duration_ms",
    "preconditions",
    "steps",
    "assertions",
    "cleanup",
    "evidence",
    "failure",
}


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _find_placeholders(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(_find_placeholders(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_placeholders(child, f"{location}[{index}]"))
    elif isinstance(value, str) and value.startswith("<") and value.endswith(">"):
        errors.append(f"{location}: unresolved template placeholder {value!r}")
    return errors


def _find_sensitive_keys(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            child_location = f"{location}.{key}"
            if normalized_key in SENSITIVE_KEYS:
                errors.append(f"{child_location}: sensitive field is forbidden")
            errors.extend(_find_sensitive_keys(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_sensitive_keys(child, f"{location}[{index}]"))
    return errors


def _validate_base_url(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, str) or not value:
        return ["$.base_url: must be null or a non-empty string"]

    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError as error:
        return [f"$.base_url: invalid URL: {error}"]

    errors: list[str] = []
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        errors.append("$.base_url: must be an absolute http or https URL")
    if parsed.username is not None or parsed.password is not None:
        errors.append("$.base_url: must not contain user information")
    if parsed.query or parsed.fragment:
        errors.append("$.base_url: must not contain a query string or fragment")
    return errors


def _validate_evidence_path(
    value: Any, location: str, run_dir: Path, errors: list[str]
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value:
        errors.append(f"{location}: evidence path must be a non-empty string")
        return
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{location}: evidence path must stay inside the run directory")
        return
    if not (run_dir / path).is_file():
        errors.append(f"{location}: evidence file does not exist: {value}")


def validate_report(report: Any, report_path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["$: report must be a JSON object"]

    schema_version = report.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            "$.schema_version: must be one of "
            + ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
        )

    required_report_keys = set(REQUIRED_REPORT_KEYS)
    if schema_version == "1.1":
        required_report_keys.add("authentication")

    missing = sorted(required_report_keys - report.keys())
    if missing:
        errors.append(f"$: missing required keys: {', '.join(missing)}")

    if schema_version == "1.0" and "authentication" in report:
        errors.append(
            "$.authentication: requires schema_version \"1.1\""
        )

    run_id = report.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        errors.append("$.run_id: must be a non-empty string")
    else:
        if report_path.stem != run_id:
            errors.append("$.run_id: must match the report filename")
        if report_path.parent.name != run_id:
            errors.append("$.run_id: must match the run directory name")

    if report.get("run_status") not in RUN_STATUSES:
        errors.append(
            "$.run_status: must be one of " + ", ".join(sorted(RUN_STATUSES))
        )
    if report.get("ended_at") is None:
        errors.append("$.ended_at: must be set on a finalized report")
    if not _nonnegative_integer(report.get("duration_ms")):
        errors.append("$.duration_ms: must be a non-negative integer")
    errors.extend(_validate_base_url(report.get("base_url")))

    if schema_version == "1.1":
        authentication = report.get("authentication")
        if not isinstance(authentication, dict):
            errors.append("$.authentication: must be an object")
        else:
            missing_auth_keys = sorted(REQUIRED_AUTH_KEYS - authentication.keys())
            if missing_auth_keys:
                errors.append(
                    "$.authentication: missing required keys: "
                    + ", ".join(missing_auth_keys)
                )

            auth_required = authentication.get("required_for_selected_cases")
            auth_mode = authentication.get("mode")
            auth_status = authentication.get("status")
            session_reused = authentication.get("session_reused")
            mfa_encountered = authentication.get("mfa_encountered")
            diagnostic = authentication.get("diagnostic")

            if not isinstance(auth_required, bool):
                errors.append(
                    "$.authentication.required_for_selected_cases: "
                    "must be a boolean"
                )
            if auth_mode not in AUTH_MODES:
                errors.append(
                    "$.authentication.mode: must be one of "
                    + ", ".join(sorted(AUTH_MODES))
                )
            if auth_status not in FINAL_AUTH_STATUSES:
                errors.append(
                    "$.authentication.status: finalized reports must use one of "
                    + ", ".join(sorted(FINAL_AUTH_STATUSES))
                )
            if not isinstance(session_reused, bool):
                errors.append("$.authentication.session_reused: must be a boolean")
            if not isinstance(mfa_encountered, bool):
                errors.append("$.authentication.mfa_encountered: must be a boolean")
            if diagnostic is not None and not isinstance(diagnostic, str):
                errors.append("$.authentication.diagnostic: must be a string or null")

            if auth_required is False:
                if auth_mode != "none":
                    errors.append(
                        "$.authentication.mode: must be \"none\" when "
                        "authentication is not required"
                    )
                if auth_status != "not_required":
                    errors.append(
                        "$.authentication.status: must be \"not_required\" when "
                        "authentication is not required"
                    )
                if session_reused is True:
                    errors.append(
                        "$.authentication.session_reused: must be false when "
                        "authentication is not required"
                    )
            elif auth_required is True:
                if auth_mode == "none":
                    errors.append(
                        "$.authentication.mode: cannot be \"none\" when "
                        "authentication is required"
                    )
                if auth_status == "not_required":
                    errors.append(
                        "$.authentication.status: cannot be \"not_required\" when "
                        "authentication is required"
                    )

            if session_reused is True and auth_mode not in {
                "existing_session",
                "storage_state",
            }:
                errors.append(
                    "$.authentication.session_reused: true requires "
                    "\"existing_session\" or \"storage_state\" mode"
                )
            if (
                auth_status == "authenticated"
                and auth_mode in {"existing_session", "storage_state"}
                and session_reused is not True
            ):
                errors.append(
                    "$.authentication.session_reused: authenticated "
                    "\"existing_session\" or \"storage_state\" mode requires true"
                )
            if mfa_encountered is True and auth_mode not in {
                "manual",
                "credentials",
            }:
                errors.append(
                    "$.authentication.mfa_encountered: true requires "
                    "\"manual\" or \"credentials\" mode"
                )

    cases = report.get("cases")
    if not isinstance(cases, list):
        errors.append("$.cases: must be an array")
        cases = []

    counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    run_dir = report_path.parent

    for index, case in enumerate(cases):
        location = f"$.cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{location}: must be an object")
            continue

        missing_case_keys = sorted(REQUIRED_CASE_KEYS - case.keys())
        if missing_case_keys:
            errors.append(
                f"{location}: missing required keys: {', '.join(missing_case_keys)}"
            )

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{location}.id: must be a non-empty string")
        elif case_id in seen_ids:
            errors.append(f"{location}.id: duplicate case id {case_id!r}")
        else:
            seen_ids.add(case_id)

        status = case.get("status")
        if status not in CASE_STATUSES:
            errors.append(
                f"{location}.status: must be one of "
                + ", ".join(sorted(CASE_STATUSES))
            )
        else:
            counts[status] += 1

        if not _nonnegative_integer(case.get("duration_ms")):
            errors.append(f"{location}.duration_ms: must be a non-negative integer")
        if status == "passed" and case.get("failure") is not None:
            errors.append(f"{location}.failure: passed cases must use null")
        if status in CASE_STATUSES - {"passed"} and not isinstance(
            case.get("failure"), dict
        ):
            errors.append(f"{location}.failure: non-passed cases need an object")

        evidence = case.get("evidence")
        if isinstance(evidence, dict):
            for key in ("screenshots", "artifacts"):
                values = evidence.get(key, [])
                if not isinstance(values, list):
                    errors.append(f"{location}.evidence.{key}: must be an array")
                    continue
                for evidence_index, value in enumerate(values):
                    _validate_evidence_path(
                        value,
                        f"{location}.evidence.{key}[{evidence_index}]",
                        run_dir,
                        errors,
                    )

        for step_index, step in enumerate(case.get("steps", [])):
            if isinstance(step, dict) and step.get("screenshot") is not None:
                _validate_evidence_path(
                    step["screenshot"],
                    f"{location}.steps[{step_index}].screenshot",
                    run_dir,
                    errors,
                )

        for assertion_index, assertion in enumerate(case.get("assertions", [])):
            if not isinstance(assertion, dict):
                continue
            values = assertion.get("evidence", [])
            if not isinstance(values, list):
                errors.append(
                    f"{location}.assertions[{assertion_index}].evidence: "
                    "must be an array"
                )
                continue
            for evidence_index, value in enumerate(values):
                _validate_evidence_path(
                    value,
                    (
                        f"{location}.assertions[{assertion_index}]"
                        f".evidence[{evidence_index}]"
                    ),
                    run_dir,
                    errors,
                )

    summary = report.get("summary")
    if not isinstance(summary, dict):
        errors.append("$.summary: must be an object")
    else:
        expected_total = len(cases)
        if summary.get("total") != expected_total:
            errors.append(
                f"$.summary.total: expected {expected_total}, "
                f"got {summary.get('total')!r}"
            )
        for key in SUMMARY_KEYS:
            if summary.get(key) != counts[key]:
                errors.append(
                    f"$.summary.{key}: expected {counts[key]}, "
                    f"got {summary.get(key)!r}"
                )

    errors.extend(_find_placeholders(report))
    errors.extend(_find_sensitive_keys(report))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    try:
        with args.report.open(encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Report validation failed: {error}", file=sys.stderr)
        return 1

    errors = validate_report(report, args.report)
    if errors:
        print("Report validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Report is valid: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
