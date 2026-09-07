from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INJECTOR = ROOT / "scripts" / "inject_annotation.py"
VALIDATOR = ROOT / "scripts" / "validate_annotation.py"
START = "<!-- HTML-REVIEW-ANNOTATION:START -->"
END = "<!-- HTML-REVIEW-ANNOTATION:END -->"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INJECTOR), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def script_json(html: str, element_id: str):
    match = re.search(
        rf'<script\b[^>]*\bid=["\']{re.escape(element_id)}["\'][^>]*>(.*?)</script\s*>',
        html,
        re.I | re.S,
    )
    if not match:
        raise AssertionError(f"missing #{element_id}")
    return json.loads(match.group(1))


class InjectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "report.html"
        self.source.write_text(
            '<!doctype html><html lang="en"><body><h1 id="title">Report</h1></body></html>',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_injects_v2_without_overwriting_source(self):
        before = self.source.read_bytes()
        result = run(str(self.source), "--lang", "en", "--zip")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.root / "report_reviewable.html"
        self.assertTrue(output.exists())
        self.assertTrue(output.with_suffix(".zip").exists())
        self.assertEqual(self.source.read_bytes(), before)
        html = output.read_text(encoding="utf-8")
        self.assertEqual(html.count(START), 1)
        self.assertEqual(html.count(END), 1)
        meta = script_json(html, "hra-meta")
        self.assertEqual(meta["engineVersion"], "2.0.0")
        self.assertEqual(meta["locale"], "en")
        self.assertEqual(meta["defaultAuthor"], "")

    def test_document_id_is_deterministic(self):
        first = self.root / "one.html"
        second = self.root / "two.html"
        self.assertEqual(run(str(self.source), "-o", str(first)).returncode, 0)
        self.assertEqual(run(str(self.source), "-o", str(second)).returncode, 0)
        self.assertEqual(
            script_json(first.read_text(encoding="utf-8"), "hra-meta")["documentId"],
            script_json(second.read_text(encoding="utf-8"), "hra-meta")["documentId"],
        )

    def test_reinjection_is_idempotent_and_preserves_seed(self):
        output = self.root / "review.html"
        self.assertEqual(run(str(self.source), "-o", str(output)).returncode, 0)
        html = output.read_text(encoding="utf-8")
        meta_before = script_json(html, "hra-meta")
        seed = [{"id": "a1", "text": "Increase contrast", "status": "pending"}]
        html = re.sub(
            r'(<script\b[^>]*\bid=["\']hra-annotations-seed["\'][^>]*>).*?(</script\s*>)',
            lambda m: m.group(1) + json.dumps(seed) + m.group(2),
            html,
            flags=re.I | re.S,
        )
        output.write_text(html, encoding="utf-8")
        upgraded = self.root / "upgraded.html"
        self.assertEqual(run(str(output), "-o", str(upgraded)).returncode, 0)
        final = upgraded.read_text(encoding="utf-8")
        self.assertEqual(final.count(START), 1)
        self.assertEqual(script_json(final, "hra-annotations-seed"), seed)
        self.assertEqual(script_json(final, "hra-meta")["documentId"], meta_before["documentId"])

    def test_refuses_to_overwrite_input(self):
        result = run(str(self.source), "-o", str(self.source))
        self.assertEqual(result.returncode, 2)
        self.assertIn("never overwritten", result.stderr)

    def test_validator_accepts_generated_file(self):
        output = self.root / "review.html"
        self.assertEqual(run(str(self.source), "-o", str(output)).returncode, 0)
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("one v2 annotation engine", result.stdout)

    def test_legacy_embedded_comments_are_migrated(self):
        legacy = [{"id": "old-1", "text": "Clarify this label", "target": "Old button"}]
        self.source.write_text(
            '<html><body><button>Old button</button><script id="pm-annotations-seed" '
            f'type="application/json">{json.dumps(legacy)}</script></body></html>',
            encoding="utf-8",
        )
        output = self.root / "migrated.html"
        self.assertEqual(run(str(self.source), "-o", str(output)).returncode, 0)
        seed = script_json(output.read_text(encoding="utf-8"), "hra-annotations-seed")
        self.assertEqual(seed[0]["id"], "old-1")
        self.assertEqual(seed[0]["anchorText"], "Old button")


if __name__ == "__main__":
    unittest.main()
