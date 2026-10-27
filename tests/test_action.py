"""Behavioral checks for package identity and Toy write boundaries."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import toy_action as action


SHA = "a" * 40
REPO = "example/toy-site"


class FakeGitHub:
    def __init__(self, records=None, states=None):
        self.saved = []
        self.statuses = []
        self.records_data = records or []
        self.states = states or {}

    def records(self, slug, kind=None):
        return [r for r in self.records_data if not kind or r["payload"]["kind"] == kind]

    def record(self, sha, slug, kind, **payload):
        result = {"id": 100 + len(self.saved), "payload": {"kind": kind, "slug": slug, "sha": sha, **payload}}
        self.saved.append(result)
        return result

    def status(self, record, state, description):
        self.statuses.append((record["id"], state, description))

    def state(self, record):
        return self.states[record["id"]]


class FakeToy:
    def __init__(self, *, items=None, response=None, error=None):
        self.items = items if items is not None else [{"id": 42, "slug": "demo"}]
        self.response = response
        self.error = error
        self.calls = []
        self.version = "v0.6.4"
        self.closed = False

    def account(self):
        return "account-hash"

    def toys(self):
        return self.items

    def metadata_flags(self, command, fields, bundle):
        return [entry for key, value in fields.items() for entry in ("--" + key, value)]

    def call(self, argv, write=False):
        self.calls.append((argv, write))
        if self.error:
            raise self.error
        return self.response or {"id": 42, "status": "reviewing"}

    def close(self):
        self.closed = True


class FakePlanningGitHub:
    def __init__(self, source_repository_id=2):
        self.source_repository_id = source_repository_id

    def call(self, path):
        if path == "":
            return {"default_branch": "main", "id": 2}
        if path == "commits/v1":
            return {"sha": SHA}
        if path == "compare/" + SHA + "...main":
            return {"status": "ahead"}
        if path == "actions/runs/17":
            return {
                "event": "push", "conclusion": "success", "head_branch": "main",
                "head_repository": {"id": self.source_repository_id},
                "path": ".github/workflows/toy.yml@refs/heads/main",
            }
        raise AssertionError("Unexpected GitHub path: " + path)

    def pages(self, path, key=None):
        if path.startswith("deployments?"):
            return [{"id": 5, "payload": {
                "tool": action.TOOL, "schema": action.SCHEMA,
                "sha": SHA, "run_id": "17", "package_sha": "a" * 64,
            }}]
        if path == "actions/runs/17/artifacts":
            return [{"id": 23, "name": "toy-preview-" + SHA, "expired": False}]
        raise AssertionError("Unexpected paginated path: " + path)

    def state(self, record):
        return "success"


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        (self.base / "site").mkdir()
        (self.base / "site" / "index.html").write_text(
            "<!doctype html><html><head><title>Demo</title></head><body>demo</body></html>"
        )
        (self.base / "assets").mkdir()
        (self.base / "assets" / "poster.png").write_bytes(b"PNG bytes for metadata test")
        self.config = self.base / "toy.config.json"
        self.config.write_text(json.dumps({
            "slug": "demo", "directory": "site",
            "create": {"title": "Demo", "category": "TOOL", "poster": "assets/poster.png"},
            "metadata": {"title": "New title"},
        }))
        self.env = patch.dict(os.environ, {
            "GITHUB_REPOSITORY": REPO, "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ID": "17",
            "GITHUB_ACTOR": "maintainer", "GITHUB_SHA": SHA,
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def bundle(self, name="bundle"):
        path = self.base / name
        args = SimpleNamespace(config=str(self.config), bundle=str(path), source_sha=SHA, metadata_only=False)
        action.package(args)
        return path

    def operation_args(self, path, mode="submit", *, override=False):
        return SimpleNamespace(
            bundle=str(path), source_sha=SHA, mode=mode, override=override,
            release_id="77", expose_preview=False,
        )

    def binding(self, toy_id=42, account="account-hash"):
        return {"id": 1, "payload": {"kind": "binding", "slug": "demo", "toy_id": toy_id, "account": account}}

    def mark_preview(self, path):
        manifest = action.jsonfile(path / "manifest.json")
        manifest.update(preview=True, account="account-hash", toy_id=42, preview_run="17")
        action.save(path / "manifest.json", manifest)

    def test_package_is_deterministic_and_metadata_images_are_sealed(self):
        first, second = self.bundle("first"), self.bundle("second")
        first_manifest = action.jsonfile(first / "manifest.json")
        second_manifest = action.jsonfile(second / "manifest.json")
        self.assertEqual(first_manifest["package_sha"], second_manifest["package_sha"])
        self.assertEqual((first / "package.zip").read_bytes(), (second / "package.zip").read_bytes())
        with zipfile.ZipFile(first / "package.zip") as archive:
            self.assertIn("index.html", archive.namelist())
            self.assertNotIn("assets/poster.png", archive.namelist())
        (first / "create-poster.png").write_bytes(b"changed")
        with self.assertRaisesRegex(action.Failure, "metadata digest mismatch"):
            action.load_bundle(self.operation_args(first))

    def test_bundle_requires_exact_commit_repository_and_preview(self):
        path = self.bundle()
        with self.assertRaisesRegex(action.Failure, "No successful preview"):
            action.load_bundle(self.operation_args(path), require_preview=True)
        self.mark_preview(path)
        wrong_sha = self.operation_args(path)
        wrong_sha.source_sha = "b" * 40
        with self.assertRaisesRegex(action.Failure, "commit"):
            action.load_bundle(wrong_sha, require_preview=True)
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "foreign/repo"}):
            with self.assertRaisesRegex(action.Failure, "another repository"):
                action.load_bundle(self.operation_args(path), require_preview=True)
        (path / "package.zip").write_bytes(b"substituted package")
        with self.assertRaisesRegex(action.Failure, "Package digest mismatch"):
            action.load_bundle(self.operation_args(path), require_preview=True)

    def test_toy_list_requires_all_pages_and_current_account_ownership(self):
        toy = object.__new__(action.Toy)
        toy.uid = 7
        pages = [
            {"total": 2, "pn": 1, "ps": 1, "list": [{"id": 11, "url": "https://www.bilibili.com/toy/one/", "user_info": {"mid": 7}}]},
            {"total": 2, "pn": 2, "ps": 1, "list": [{"id": 12, "url": "https://www.bilibili.com/toy/two/", "user_info": {"mid": 7}}]},
        ]
        toy.call = lambda argv: pages.pop(0)
        self.assertEqual([x["slug"] for x in toy.toys()], ["one", "two"])
        toy.call = lambda argv: {"total": 1, "pn": 1, "ps": 50, "list": [{"id": 11, "url": "https://www.bilibili.com/toy/one/", "user_info": {"mid": 8}}]}
        with self.assertRaisesRegex(action.Failure, "ownership"):
            toy.toys()
        toy.call = lambda argv: {"total": 1, "pn": 1, "ps": 50, "list": [{"id": 11, "url": "https://www.bilibili.com/toy/one/"}]}
        with self.assertRaisesRegex(action.Failure, "ownership"):
            toy.toys()

    def test_unique_slug_adoption_saves_binding_and_conflict_stops(self):
        gh = FakeGitHub()
        toy = FakeToy()
        chosen = action.resolve_target(gh, toy, {"slug": "demo"}, "account-hash", SHA)
        self.assertEqual(chosen["id"], 42)
        self.assertEqual(gh.saved[0]["payload"]["kind"], "binding")
        with self.assertRaisesRegex(action.Failure, "conflicts"):
            action.resolve_target(FakeGitHub([self.binding(toy_id=42)]), toy, {"slug": "demo", "toy_id": 23}, "account-hash", SHA)
        with self.assertRaisesRegex(action.Failure, "another Toy account"):
            action.resolve_target(FakeGitHub([self.binding(account="other")]), toy, {"slug": "demo"}, "account-hash", SHA)

    def test_preview_update_omits_all_metadata_flags(self):
        path = self.bundle()
        gh, toy = FakeGitHub([self.binding()]), FakeToy(response={"preview_url": "https://www.bilibili.com/toy/preview/demo"})
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            action.write_operation(self.operation_args(path, mode="preview"))
        argv, write = toy.calls[0]
        self.assertEqual(argv[:2], ["update", "42"])
        self.assertIn("package.zip", argv[2])
        self.assertEqual(len(argv), 3)
        self.assertFalse(write)
        self.assertTrue(toy.closed)
        self.assertTrue(action.jsonfile(path / "manifest.json")["preview"])

    def test_unknown_write_is_recorded_and_never_retried(self):
        path = self.bundle()
        self.mark_preview(path)
        gh, toy = FakeGitHub([self.binding()]), FakeToy(error=action.Unknown("timeout after send"))
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            with self.assertRaises(action.Unknown):
                action.write_operation(self.operation_args(path))
        self.assertEqual(len(toy.calls), 1)
        self.assertEqual([state for _, state, _ in gh.statuses], ["in_progress", "error"])
        self.assertEqual(gh.saved[0]["payload"]["kind"], "submission")
        self.assertTrue(toy.closed)

    def test_accepted_duplicate_submission_is_not_reissued(self):
        path = self.bundle()
        self.mark_preview(path)
        manifest = action.jsonfile(path / "manifest.json")
        key = action.hashlib.sha256(action.canonical(["77", "submission", SHA, manifest["package_sha"]]).encode()).hexdigest()
        previous = {"id": 9, "payload": {"kind": "submission", "slug": "demo", "key": key}}
        gh, toy = FakeGitHub([self.binding(), previous], {9: "success"}), FakeToy()
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            action.write_operation(self.operation_args(path))
        self.assertEqual(toy.calls, [])
        self.assertEqual(gh.saved, [])

    def test_unknown_previous_write_blocks_new_release(self):
        path = self.bundle()
        self.mark_preview(path)
        previous = {"id": 9, "payload": {"kind": "submission", "slug": "demo", "key": "other"}}
        gh, toy = FakeGitHub([self.binding(), previous], {9: "error"}), FakeToy()
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            with self.assertRaisesRegex(action.Failure, "Previous write outcome is unknown"):
                action.write_operation(self.operation_args(path))
        self.assertEqual(toy.calls, [])

    def test_manual_override_cannot_run_from_release_event(self):
        path = self.bundle()
        gh, toy = FakeGitHub([self.binding()]), FakeToy()
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release"}):
            with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy) as construct_toy:
                with self.assertRaisesRegex(action.Failure, "manual dispatch"):
                    action.write_operation(self.operation_args(path, override=True))
                construct_toy.assert_not_called()

    def test_release_evidence_selects_only_same_repo_successful_preview(self):
        event = self.base / "release.json"
        event.write_text(json.dumps({"release": {
            "id": 77, "tag_name": "v1", "draft": False, "prerelease": False,
        }}))
        published = {}
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}), \
             patch.object(action, "GitHub", return_value=FakePlanningGitHub(source_repository_id=2)), \
             patch.object(action, "output", side_effect=lambda key, value: published.__setitem__(key, value)):
            action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))
        self.assertEqual(published["source-sha"], SHA)
        self.assertEqual(published["artifact-id"], 23)
        self.assertEqual(published["expected-package-sha"], "a" * 64)
        self.assertEqual(published["build"], "false")

        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}), \
             patch.object(action, "GitHub", return_value=FakePlanningGitHub(source_repository_id=999)), \
             patch.object(action, "output"):
            with self.assertRaisesRegex(action.Failure, "No usable successful preview artifact"):
                action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))


if __name__ == "__main__":
    unittest.main()
