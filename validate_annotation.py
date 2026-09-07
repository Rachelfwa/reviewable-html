#!/usr/bin/env python3
"""Validate a generated Reviewable HTML file without third-party packages."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

START = "<!-- HTML-REVIEW-ANNOTATION:START -->"
END = "<!-- HTML-REVIEW-ANNOTATION:END -->"
SCRIPT_RE = r'<script\b[^>]*\bid=["\']{id}["\'][^>]*>(.*?)</script\s*>'


def script_json(text: str, element_id: str):
    match = re.search(SCRIPT_RE.format(id=re.escape(element_id)), text, re.I | re.S)
    if not match:
        raise ValueError(f"missing #{element_id}")
    return json.loads(match.group(1).strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Reviewable HTML file")
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    issues: list[str] = []

    try:
        text = args.html.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"FAIL: cannot read UTF-8 HTML: {exc}")
        return 1

    if text.count(START) != 1 or text.count(END) != 1:
        issues.append("sentinel block must appear exactly once")
    if text.find(START) > text.find(END):
        issues.append("sentinel block order is invalid")

    for token in ("hra-meta", "hra-annotations-seed", "hra-annotation-style", "hra-annotation-engine"):
        if len(re.findall(rf'id=["\']{re.escape(token)}["\']', text, re.I)) != 1:
            issues.append(f"#{token} must appear exactly once")

    try:
        meta = script_json(text, "hra-meta")
        if meta.get("engine") != "html-review-annotation":
            issues.append("unexpected engine metadata")
        if not str(meta.get("engineVersion", "")).startswith("2."):
            issues.append("engineVersion must be 2.x")
        if "defaultAuthor" not in meta or not isinstance(meta.get("defaultAuthor"), str):
            issues.append("defaultAuthor metadata must be a string")
        if meta.get("locale") not in {"auto", "zh-CN", "en"}:
            issues.append("locale must be auto, zh-CN, or en")
    except (ValueError, json.JSONDecodeError) as exc:
        issues.append(f"invalid metadata JSON: {exc}")

    try:
        seed = script_json(text, "hra-annotations-seed")
        if not isinstance(seed, list):
            issues.append("annotation seed must be a JSON array")
    except (ValueError, json.JSONDecodeError) as exc:
        issues.append(f"invalid annotation seed JSON: {exc}")

    for capability in ("exportHtml", "copyForAI", "exportJson", "importJson", "localStorage"):
        if capability not in text:
            issues.append(f"required capability not found: {capability}")

    csp = re.search(
        r'<meta\b[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>', text, re.I
    )

    if issues:
        for issue in issues:
            print("FAIL:", issue)
        return 1

    print(f"PASS: one v2 annotation engine, valid metadata, {len(seed)} embedded annotations")
    if csp:
        print("WARNING: a strict Content-Security-Policy may block injected inline CSS or JavaScript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
