import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scaffold", ROOT / "scripts" / "scaffold.py")
SCAFFOLD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAFFOLD)


class ScaffoldTests(unittest.TestCase):
    def test_html_starter_is_ready_in_separate_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "my-toy"
            workflow = Path(temp) / "toy.yml"
            workflow.write_text("name: Toy\n", encoding="utf-8")
            SCAFFOLD.scaffold("html", destination, "my-toy", "A & B", workflow)

            config = json.loads((destination / "toy.config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["slug"], "my-toy")
            self.assertEqual(config["directory"], "site")
            self.assertEqual(config["create"]["title"], "A & B")
            self.assertTrue((destination / "site/assets/main.js").is_file())
            self.assertTrue((destination / ".github/workflows/toy.yml").is_file())
            self.assertIn("A &amp; B", (destination / "site/index.html").read_text(encoding="utf-8"))

    def test_rejects_existing_project_without_touching_it(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)
            sentinel = destination / "existing.txt"
            sentinel.write_text("keep", encoding="utf-8")
            workflow = destination / "workflow.yml"
            workflow.write_text("name: Toy\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty"):
                SCAFFOLD.scaffold("vite", destination, "my-toy", "My Toy", workflow)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertFalse((destination / "toy.config.json").exists())

    def test_rejects_invalid_slug_before_copying(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "new"
            with self.assertRaisesRegex(ValueError, "slug"):
                SCAFFOLD.scaffold("html", destination, "../bad", "My Toy", Path(temp) / "missing")
            self.assertFalse(destination.exists())

    def test_vite_starter_keeps_reproducible_build_and_relative_base(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "vite-toy"
            workflow = Path(temp) / "toy.yml"
            workflow.write_text("name: Toy\n", encoding="utf-8")
            SCAFFOLD.scaffold("vite", destination, "vite-toy", "Vite Toy", workflow)

            config = json.loads((destination / "toy.config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["directory"], "dist")
            self.assertEqual(config["slug"], "vite-toy")
            self.assertTrue((destination / "package-lock.json").is_file())
            self.assertIn("base: './'", (destination / "vite.config.js").read_text(encoding="utf-8"))
            self.assertTrue((destination / ".github/workflows/toy.yml").is_file())


if __name__ == "__main__":
    unittest.main()
