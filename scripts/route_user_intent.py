#!/usr/bin/env python3
"""Deterministic message router for AGENTS trigger tokens."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ROUTER_POLICY_PATH = Path(__file__).resolve().parents[1] / ".mcp" / "router_policy.yaml"

DEFAULT_ROUTER_POLICY: dict[str, Any] = {
    "version": 1,
    "blocked_tools": ["web.image_query"],
    "rules": [
        {
            "id": "stop_run",
            "kind": "regex",
            "action": "stop_run",
            "reason": "STOPRUN command detected.",
            "pattern": r"\bSTOPRUN\s+(?P<run_id>[A-Za-z0-9_.:-]+)\b",
            "flags": ["IGNORECASE"],
        },
        {
            "id": "stop_job",
            "kind": "regex",
            "action": "stop_job",
            "reason": "STOP command detected.",
            "pattern": r"\bSTOP\s+(?P<job_id>[A-Za-z0-9_.:-]+)\b",
            "flags": ["IGNORECASE"],
        },
        {
            "id": "mcp_sandbox_trigger",
            "kind": "token_any",
            "action": "mcp_sandbox_factory",
            "reason": "MCP_SANDBOX trigger detected.",
            "case_sensitive": True,
            "tokens": [
                "MCP_SANDBOX_SYNC",
                "MCP_SANDBOX_STOP_SMOKE",
                "MCP_SANDBOX_DEV",
                "MCP_SANDBOX_EXP",
                "MCP_SANDBOX_ANALYZE",
                "MCP_SANDBOX_LOOP",
            ],
        },
        {
            "id": "external_ram",
            "kind": "token_any",
            "action": "workflow_external_ram",
            "reason": "External RAM trigger detected.",
            "case_sensitive": False,
            "tokens": ["@RAM", "@todoist"],
        },
        {
            "id": "ollama_report",
            "kind": "token_any",
            "action": "ollama_generate_report",
            "reason": "Ollama @REPORT trigger detected.",
            "case_sensitive": False,
            "tokens": ["@REPORT"],
        },
        {
            "id": "ollama_summary",
            "kind": "token_any",
            "action": "ollama_summarize_directory",
            "reason": "Ollama @SUMMARY trigger detected.",
            "case_sensitive": False,
            "tokens": ["@SUMMARY"],
        },
        {
            "id": "ollama_index",
            "kind": "token_any",
            "action": "ollama_rebuild_index",
            "reason": "Ollama @INDEX trigger detected.",
            "case_sensitive": False,
            "tokens": ["@INDEX"],
        },
        {
            "id": "ollama_search",
            "kind": "token_any",
            "action": "ollama_semantic_search",
            "reason": "Ollama @SEARCH trigger detected.",
            "case_sensitive": False,
            "tokens": ["@SEARCH"],
        },
    ],
}

TOKEN_BOUNDARY = r"A-Za-z0-9_"
FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


def default_router_policy_path() -> Path:
    return DEFAULT_ROUTER_POLICY_PATH


def _load_yaml_map(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return loaded


def load_router_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy: dict[str, Any] = dict(DEFAULT_ROUTER_POLICY)
    selected_path = Path(path).expanduser() if path else default_router_policy_path()
    if selected_path.exists():
        loaded = _load_yaml_map(selected_path)
        for key in ("version", "blocked_tools", "rules"):
            value = loaded.get(key)
            if isinstance(value, (dict, list, str, int)):
                policy[key] = value
    return policy


def _normalize_blocked_tools(raw_tools: Any) -> list[str]:
    if not isinstance(raw_tools, list):
        return []
    blocked: list[str] = []
    for item in raw_tools:
        if isinstance(item, str):
            value = item.strip()
            if value:
                blocked.append(value)
    return sorted(set(blocked))


def _normalize_flags(raw_flags: Any) -> int:
    if not isinstance(raw_flags, list):
        return 0
    flags = 0
    for raw in raw_flags:
        name = str(raw).strip().upper()
        if not name:
            continue
        if name not in FLAG_MAP:
            raise ValueError(f"Unsupported regex flag: {name}")
        flags |= FLAG_MAP[name]
    return flags


def _token_regex(token: str) -> str:
    escaped = re.escape(token)
    return rf"(?<![{TOKEN_BOUNDARY}]){escaped}(?![{TOKEN_BOUNDARY}])"


def _find_first_token_hit(message: str, tokens: list[str], *, case_sensitive: bool) -> dict[str, Any] | None:
    if not tokens:
        return None
    flags = 0 if case_sensitive else re.IGNORECASE
    best: dict[str, Any] | None = None
    for token in tokens:
        pattern = re.compile(_token_regex(token), flags)
        match = pattern.search(message)
        if match is None:
            continue
        candidate = {
            "token": token,
            "span": [match.start(), match.end()],
        }
        if best is None or candidate["span"][0] < best["span"][0]:
            best = candidate
    return best


def _normalize_rule(raw_rule: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw_rule, dict):
        raise ValueError(f"Rule at index {index} must be a mapping.")
    rule_id = str(raw_rule.get("id", f"rule_{index}")).strip()
    kind = str(raw_rule.get("kind", "")).strip()
    action = str(raw_rule.get("action", "")).strip()
    reason = str(raw_rule.get("reason", "")).strip()
    if not rule_id:
        raise ValueError(f"Rule at index {index} has empty id.")
    if kind not in {"regex", "token_any"}:
        raise ValueError(f"Rule '{rule_id}' has unsupported kind '{kind}'.")
    if not action:
        raise ValueError(f"Rule '{rule_id}' must define action.")
    normalized: dict[str, Any] = {
        "id": rule_id,
        "kind": kind,
        "action": action,
        "reason": reason or f"Matched rule '{rule_id}'.",
    }
    if kind == "regex":
        pattern = str(raw_rule.get("pattern", "")).strip()
        if not pattern:
            raise ValueError(f"Regex rule '{rule_id}' must define pattern.")
        normalized["pattern"] = pattern
        normalized["flags"] = _normalize_flags(raw_rule.get("flags", []))
    else:
        raw_tokens = raw_rule.get("tokens", [])
        if not isinstance(raw_tokens, list):
            raise ValueError(f"Token rule '{rule_id}' must define tokens as list.")
        tokens = [str(item).strip() for item in raw_tokens if str(item).strip()]
        if not tokens:
            raise ValueError(f"Token rule '{rule_id}' must provide at least one token.")
        normalized["tokens"] = tokens
        normalized["case_sensitive"] = bool(raw_rule.get("case_sensitive", True))
    return normalized


def _normalize_rules(raw_rules: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_rules, list):
        return []
    return [_normalize_rule(raw_rule, index) for index, raw_rule in enumerate(raw_rules)]


def _match_rule(message: str, rule: dict[str, Any]) -> dict[str, Any] | None:
    if rule["kind"] == "regex":
        pattern = re.compile(str(rule["pattern"]), int(rule["flags"]))
        match = pattern.search(message)
        if match is None:
            return None
        arguments = {key: value for key, value in match.groupdict().items() if value is not None}
        return {
            "arguments": arguments,
            "matched_text": match.group(0),
            "span": [match.start(), match.end()],
        }

    token_hit = _find_first_token_hit(
        message,
        list(rule["tokens"]),
        case_sensitive=bool(rule["case_sensitive"]),
    )
    if token_hit is None:
        return None
    return {
        "arguments": {"token": token_hit["token"]},
        "matched_text": token_hit["token"],
        "span": token_hit["span"],
    }


def route_user_intent(message: str, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_router_policy()
    blocked_tools = _normalize_blocked_tools(policy.get("blocked_tools", []))
    rules = _normalize_rules(policy.get("rules", []))

    for rule in rules:
        matched = _match_rule(message, rule)
        if matched is None:
            continue
        return {
            "ok": True,
            "action": rule["action"],
            "matched_rule": rule["id"],
            "reason": rule["reason"],
            "arguments": matched["arguments"],
            "matched_text": matched["matched_text"],
            "span": matched["span"],
            "blocked_tools": blocked_tools,
        }

    return {
        "ok": True,
        "action": "normal_flow",
        "matched_rule": None,
        "reason": "No trigger token matched.",
        "arguments": {},
        "matched_text": None,
        "span": None,
        "blocked_tools": blocked_tools,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route user message by AGENTS trigger rules."
    )
    parser.add_argument(
        "message",
        nargs="+",
        help='Message text to route, e.g. "STOPRUN run-123".',
    )
    parser.add_argument(
        "--policy",
        default=str(default_router_policy_path()),
        help="Path to router policy YAML. Defaults to .mcp/router_policy.yaml.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    message = " ".join(args.message)
    policy = load_router_policy(args.policy)
    result = route_user_intent(message, policy=policy)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
