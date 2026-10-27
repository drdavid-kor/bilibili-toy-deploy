"""Regression checks for decisions that protect the user's Toy."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import toy_action as action


class ToyBoundaryTests(unittest.TestCase):
    def test_only_release_or_manual_dispatch_can_submit_and_metadata_is_manual(self):
        cases = (
            ("push", "submit", "77", "published Release"),
            ("release", "submit", "", "published Release"),
            ("push", "sync-metadata", "", "manual dispatch"),
            ("release", "preview", "", "cannot silently generate"),
        )
        for event, mode, release_id, message in cases:
            with self.subTest(event=event, mode=mode):
                with patch.dict(os.environ, {"GITHUB_EVENT_NAME": event}):
                    with self.assertRaisesRegex(action.Failure, message):
                        action.write_operation(SimpleNamespace(mode=mode, release_id=release_id, override=False))

    def test_list_accepts_actual_index_entry_and_rejects_foreign_host(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/toy_cli.json").read_text(encoding="utf-8"))
        toy = object.__new__(action.Toy)
        toy.uid = fixture["whoami"]["uid"]
        toy.call = lambda _: fixture["mylist"]
        self.assertEqual(toy.toys()[0]["slug"], "example-toy")

        foreign = json.loads(json.dumps(fixture["mylist"]))
        foreign["list"][0]["url"] = "https://unrelated.example/toy/example-toy/index.html"
        toy.call = lambda _: foreign
        with self.assertRaisesRegex(action.Failure, "ownership"):
            toy.toys()

    def test_watermark_is_a_boolean_and_cli_receives_bool_flag_value(self):
        toy = object.__new__(action.Toy)
        toy.help = {("update",): {"flags": [{"name": "watermark", "type": "bool"}]}}
        self.assertEqual(toy.metadata_flags("update", {"watermark": False}, Path(".")), ["--watermark=false"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "toy.config.json"
            path.write_text(json.dumps({"slug": "demo", "directory": "site", "metadata": {"watermark": True}}))
            self.assertIs(action.config_load(path)["metadata"]["watermark"], True)
            path.write_text(json.dumps({"slug": "demo", "directory": "site", "metadata": {"watermark": "true"}}))
            with self.assertRaisesRegex(action.Failure, "JSON boolean"):
                action.config_load(path)


if __name__ == "__main__":
    unittest.main()
