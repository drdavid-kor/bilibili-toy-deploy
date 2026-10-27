"""Check that public starter files form usable, consistent projects."""

from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path

from scripts.toy_action import config_load


ROOT = Path(__file__).resolve().parents[1]


class PublicContractTests(unittest.TestCase):
    def test_starters_use_supported_config_and_reproducible_static_layout(self):
        for relative in ("templates/html", "templates/vite", "examples/react", "examples/vue"):
            with self.subTest(project=relative):
                project = ROOT / relative
                config = config_load(project / "toy.config.json")
                self.assertEqual(config["create"]["visibility"], "link-only")
                for field, dimensions in (("poster", (1200, 900)), ("icon", (256, 256))):
                    image = project / config["create"][field]
                    self.assertTrue(image.is_file())
                    raw = image.read_bytes()
                    self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(struct.unpack(">II", raw[16:24]), dimensions)
                    if field == "icon":
                        self.assertLessEqual(len(raw), 512 * 1024)
                if relative == "templates/html":
                    self.assertEqual(config["directory"], "site")
                    self.assertTrue((project / "site/index.html").is_file())
                else:
                    self.assertEqual(config["directory"], "dist")
                    self.assertTrue((project / "index.html").is_file())
                    self.assertTrue((project / "package-lock.json").is_file())
                    self.assertIn("base: './'", (project / "vite.config.js").read_text(encoding="utf-8"))

    def test_copied_workflow_uses_one_pinned_remote_action(self):
        workflow = (ROOT / "examples/workflows/toy.yml").read_text(encoding="utf-8")
        refs = re.findall(r"uses:\s*(drdavid-kor/bilibili-toy-deploy@[^\s]+)", workflow)
        self.assertGreaterEqual(len(refs), 3)
        self.assertEqual(len(set(refs)), 1)
        self.assertNotIn("uses: ./", workflow)
        self.assertIn("secrets.TOY_SESSION_TOKEN", workflow)
        self.assertTrue((ROOT / "action.yml").is_file())

    def test_sanitized_cli_fixture_is_safe_and_contains_realistic_entry_url(self):
        fixture = json.loads((ROOT / "tests/fixtures/toy_cli.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["whoami"]["uid"], fixture["mylist"]["list"][0]["user_info"]["mid"])
        self.assertIn("/toy/example-toy/index.html", fixture["mylist"]["list"][0]["url"])
        self.assertIn("preview_url", fixture["preview"])
        self.assertNotIn("session_token", json.dumps(fixture).lower())


if __name__ == "__main__":
    unittest.main()
