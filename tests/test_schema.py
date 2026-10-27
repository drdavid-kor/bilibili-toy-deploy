"""Ensure the public configuration schema reflects the runtime contract."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.toy_action import CATEGORIES, META, config_load


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema/toy.config.schema.json").read_text(encoding="utf-8"))


class ConfigurationSchemaTests(unittest.TestCase):
    def test_schema_covers_runtime_fields_and_real_starters(self):
        self.assertEqual(SCHEMA["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIs(SCHEMA["additionalProperties"], False)
        self.assertEqual(set(SCHEMA["properties"]), {"slug", "directory", "toy_id", "create", "metadata"})
        meta = SCHEMA["$defs"]["metadata"]
        self.assertIs(meta["additionalProperties"], False)
        self.assertEqual(set(meta["properties"]), META)
        self.assertEqual(set(meta["properties"]["category"]["enum"]), CATEGORIES)
        self.assertEqual(meta["properties"]["watermark"]["type"], "boolean")
        for project in ("templates/html", "templates/vite", "examples/react", "examples/vue"):
            with self.subTest(project=project):
                path = ROOT / project / "toy.config.json"
                cfg = config_load(path)
                self.assertTrue(re.search(SCHEMA["properties"]["slug"]["pattern"], cfg["slug"]))
                self.assertTrue(re.search(SCHEMA["$defs"]["relativePath"]["pattern"], cfg["directory"]))

    def test_relative_path_pattern_blocks_parent_and_absolute_paths(self):
        pattern = re.compile(SCHEMA["$defs"]["relativePath"]["pattern"])
        for value in ("site", "assets/poster.png", "项目/assets/海报.png"):
            self.assertIsNotNone(pattern.fullmatch(value), value)
        for value in ("", "/tmp/file", "C:/absolute", "../secret", "foo/../../secret", r"foo\secret", "a\x00b"):
            self.assertIsNone(pattern.fullmatch(value), value)


if __name__ == "__main__":
    unittest.main()
