#!/usr/bin/env python3
"""Inject the standalone HTML Review Annotation engine into an HTML file.

The output remains a single self-contained HTML file (apart from dependencies that
already existed in the input document). Re-running the injector replaces the prior
HRA block instead of duplicating it and preserves embedded annotations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

START = "<!-- HTML-REVIEW-ANNOTATION:START -->"
END = "<!-- HTML-REVIEW-ANNOTATION:END -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Cannot decode {path} as UTF-8 or GB18030")


def json_script_payload(obj) -> str:
    # Prevent </script> termination and keep Chinese readable.
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def extract_json_script(html: str, element_id: str, default):
    pat = re.compile(
        r'<script\b[^>]*\bid=["\']' + re.escape(element_id) + r'["\'][^>]*>(.*?)</script\s*>',
        re.I | re.S,
    )
    m = pat.search(html)
    if not m:
        return default
    try:
        return json.loads(m.group(1).strip() or ("[]" if isinstance(default, list) else "{}"))
    except Exception:
        return default


def migrate_legacy(items):
    if not isinstance(items, list):
        return []
    out = []
    for i, x in enumerate(items, 1):
        if not isinstance(x, dict) or not x.get("text"):
            continue
        out.append(
            {
                "id": x.get("id") or f"legacy-{i}",
                "number": x.get("number") or i,
                "status": x.get("status") or "待确认",
                "priority": x.get("priority") or "normal",
                "module": x.get("module") or "当前页面",
                "author": x.get("author") or "",
                "text": x.get("text") or "",
                "anchorText": x.get("anchorText") or x.get("target") or "旧版批注",
                "selector": x.get("selector") or "",
                "relX": x.get("relX", 0.5),
                "relY": x.get("relY", 0.5),
                "contextType": "page",
                "contextSelector": "body",
                "pageKey": x.get("pageKey") or "",
                "fallbackX": x.get("x", 0),
                "fallbackY": x.get("y", 0),
                "createdAt": x.get("createdAt") or x.get("updatedAt") or "",
                "updatedAt": x.get("updatedAt") or x.get("createdAt") or "",
                "legacy": True,
            }
        )
    return out


def build_block(css: str, js: str, meta: dict, seed: list) -> str:
    return f"""{START}
<script id="hra-meta" type="application/json">{json_script_payload(meta)}</script>
<script id="hra-annotations-seed" type="application/json">{json_script_payload(seed)}</script>
<style id="hra-annotation-style">
{css.rstrip()}
</style>
<script id="hra-annotation-engine">
{js.rstrip()}
</script>
{END}"""


def inject(html: str, block: str) -> str:
    html = BLOCK_RE.sub("", html)
    body_close = re.search(r"</body\s*>", html, re.I)
    if body_close:
        idx = body_close.start()
        return html[:idx].rstrip() + "\n\n" + block + "\n" + html[idx:]
    html_close = re.search(r"</html\s*>", html, re.I)
    if html_close:
        idx = html_close.start()
        return html[:idx].rstrip() + "\n\n" + block + "\n" + html[idx:]
    return html.rstrip() + "\n\n" + block + "\n"


def validate_output(text: str) -> list[str]:
    errors = []
    if text.count(START) != 1 or text.count(END) != 1:
        errors.append("annotation sentinel block count is not exactly one")
    for token in ('id="hra-meta"', 'id="hra-annotations-seed"', 'id="hra-annotation-style"', 'id="hra-annotation-engine"'):
        if text.count(token) != 1:
            errors.append(f"{token} count is not exactly one")
    for capability in ("exportHtml", "copyForAI", "exportJson", "importJson"):
        if capability not in text:
            errors.append(f"required capability not found: {capability}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject reusable review annotations into a standalone HTML file")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")
    parser.add_argument("input", type=Path, help="input .html/.htm file")
    parser.add_argument("-o", "--output", type=Path, help="output HTML path; default: <stem>_可批注版.html")
    parser.add_argument("--zip", nargs="?", const="AUTO", help="also create a ZIP; optionally provide ZIP path")
    parser.add_argument("--default-author", default="", help="default annotation author; blank by default")
    parser.add_argument("--document-id", help="stable document id; normally auto/preserved")
    parser.add_argument(
        "--lang",
        choices=("auto", "zh-CN", "en"),
        default="auto",
        help="review UI language; auto follows the input document language",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2
    if args.input.suffix.lower() not in {".html", ".htm"}:
        print("ERROR: input must be .html or .htm", file=sys.stderr)
        return 2

    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent
    css = (root / "assets" / "annotation.css").read_text(encoding="utf-8")
    js = (root / "assets" / "annotation.js").read_text(encoding="utf-8")

    html, detected_encoding = read_text(args.input)
    existing_meta = extract_json_script(html, "hra-meta", {})
    seed = extract_json_script(html, "hra-annotations-seed", None)
    if seed is None:
        legacy_seed = extract_json_script(html, "pm-annotations-seed", [])
        seed = migrate_legacy(legacy_seed)
    if not isinstance(seed, list):
        seed = []

    doc_id = args.document_id or existing_meta.get("documentId")
    if not doc_id:
        digest = hashlib.sha256(
            args.input.name.encode("utf-8") + b"\0" + html.encode("utf-8", "ignore")
        ).hexdigest()[:16]
        doc_id = f"hra-{digest}"

    original_name = existing_meta.get("originalName") or args.input.name
    meta = {
        "engine": "html-review-annotation",
        "engineVersion": "2.0.0",
        "documentId": doc_id,
        "revisionId": existing_meta.get("revisionId") or "draft",
        "originalName": original_name,
        "defaultAuthor": args.default_author,
        "locale": args.lang,
    }
    if existing_meta.get("generatedAt"):
        meta["generatedAt"] = existing_meta["generatedAt"]
    if seed:
        meta["annotationCount"] = len(seed)

    block = build_block(css, js, meta, seed)
    output_text = inject(html, block)
    errors = validate_output(output_text)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 3

    default_suffix = "_reviewable.html" if args.lang == "en" else "_可批注版.html"
    out = args.output or args.input.with_name(args.input.stem + default_suffix)
    if out.resolve() == args.input.resolve():
        print("ERROR: output must differ from input; the original HTML is never overwritten", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output_text, encoding="utf-8", newline="\n")

    csp = re.search(r'<meta\b[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>', html, re.I)
    warnings = []
    if csp:
        warnings.append("input contains a Content-Security-Policy meta tag; strict CSP may block injected inline CSS/JS")
    if "pm-annotations-seed" in html:
        warnings.append("legacy pm-annotation UI detected; the new engine hides its UI and can migrate embedded legacy annotations")

    zip_path = None
    if args.zip is not None:
        zip_path = out.with_suffix(".zip") if args.zip == "AUTO" else Path(args.zip)
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(out, arcname=out.name)

    if not args.quiet:
        print(f"OK: {out}")
        print(f"Document ID: {doc_id}")
        print(f"Embedded annotations preserved/migrated: {len(seed)}")
        print(f"Input encoding detected: {detected_encoding}; output normalized to UTF-8")
        if zip_path:
            print(f"ZIP: {zip_path}")
        for w in warnings:
            print("WARNING:", w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
