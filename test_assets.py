from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrowserAssetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "assets" / "annotation.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "assets" / "annotation.css").read_text(encoding="utf-8")

    def test_ai_and_interchange_actions_are_wired(self):
        for token in ("copyForAI", "exportJson", "importJson", "exportList", "exportHtml"):
            self.assertIn(token, self.js)

    def test_bilingual_ui_and_keyboard_shortcuts_are_present(self):
        self.assertIn("var I18N", self.js)
        self.assertIn("批注模式", self.js)
        self.assertIn("Annotate", self.js)
        self.assertIn("e.key.toLowerCase()==='a'", self.js)
        self.assertIn("e.key.toLowerCase()==='l'", self.js)

    def test_v1_local_drafts_have_upgrade_fallback(self):
        self.assertIn("html_review_annotations_v1_", self.js)
        self.assertIn("html_review_annotations_v2_", self.js)

    def test_review_ui_is_namespaced(self):
        self.assertIn("#hra-toolbar", self.css)
        self.assertIn("#hra-panel", self.css)
        self.assertIn("#hra-editor-overlay", self.css)


if __name__ == "__main__":
    unittest.main()
