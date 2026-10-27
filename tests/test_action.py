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
    def __init__(self, records=None, states=None, release_sha=SHA):
        self.saved = []
        self.statuses = []
        self.records_data = records or []
        self.states = states or {}
        self.release_sha = release_sha

    def call(self, path):
        if path == "releases/77":
            return {"id": 77, "tag_name": "v1", "draft": False, "prerelease": False, "published_at": "2026-10-28T00:00:00Z"}
        if path == "commits/v1":
            return {"sha": self.release_sha}
        raise action.Failure("GitHub resource not found")

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
            "GITHUB_EVENT_PATH": str(self.base / "not-present-event.json"),
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

    def test_auditing_listing_without_url_keeps_verified_id_only(self):
        toy = object.__new__(action.Toy)
        toy.uid = 123

        def listing(item):
            return {"total": 1, "pn": 1, "ps": 50, "list": [item]}

        pending = {"id": 42, "status": "auditing", "user_info": {"mid": 123}}
        toy.call = lambda argv: listing(pending)
        row = toy.toys()[0]
        self.assertEqual(row["id"], 42)
        self.assertIsNone(row["slug"])
        self.assertNotIn("url", row)
        for bad in (
            {**pending, "user_info": {"mid": 999}},
            {**pending, "url": "https://foreign.example/toy/demo/index.html"},
            {**pending, "url": "http://www.bilibili.com/toy/demo/index.html"},
            {**pending, "url": "not a URL"},
        ):
            with self.subTest(item=bad):
                toy.call = lambda argv: listing(bad)
                with self.assertRaisesRegex(action.Failure, "ownership or slug"):
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

    def test_bound_toy_without_url_can_preview_and_update_but_conflicts_stop(self):
        path = self.bundle()
        gh = FakeGitHub([self.binding()])
        toy = FakeToy(items=[{"id": 42, "slug": None}], response={"preview_url": "https://www.bilibili.com/toy/preview/demo"})
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            action.write_operation(self.operation_args(path, mode="preview"))
        self.assertEqual(toy.calls[0][0][0:2], ["update", "42"])
        self.assertFalse(toy.calls[0][1])

        submit_toy = FakeToy(items=[{"id": 42, "slug": None}], response={"status": "auditing"})
        with patch.object(action, "GitHub", return_value=FakeGitHub([self.binding()])), \
             patch.object(action, "Toy", return_value=submit_toy):
            action.write_operation(self.operation_args(path))
        self.assertEqual(submit_toy.calls[0][0][0:2], ["update", "42"])
        self.assertTrue(submit_toy.calls[0][1])

        for items in (
            [{"id": 42, "slug": "different"}],
            [{"id": 42, "slug": None}, {"id": 43, "slug": "demo"}],
        ):
            with self.subTest(items=items):
                with self.assertRaisesRegex(action.Failure, "Toy ID, slug or account mismatch"):
                    action.resolve_target(FakeGitHub([self.binding()]), FakeToy(items=items), {"slug": "demo"}, "account-hash", SHA)

    def test_unbound_unknown_url_blocks_automatic_target_selection(self):
        pending = {"id": 43, "slug": None}
        known = {"id": 42, "slug": "demo"}
        for items in ([pending], [known, pending]):
            with self.subTest(items=items):
                gh = FakeGitHub()
                with self.assertRaisesRegex(action.Failure, "no verifiable slug"):
                    action.resolve_target(gh, FakeToy(items=items), {"slug": "demo"}, "account-hash", SHA)
                self.assertEqual(gh.saved, [])

        gh = FakeGitHub()
        chosen = action.resolve_target(gh, FakeToy(items=[known, pending]), {"slug": "demo", "toy_id": 42}, "account-hash", SHA)
        self.assertEqual(chosen["id"], 42)
        self.assertEqual(gh.saved[0]["payload"]["toy_id"], 42)
        with self.assertRaisesRegex(action.Failure, "Toy ID, slug or account mismatch"):
            action.resolve_target(FakeGitHub(), FakeToy(items=[known, pending]), {"slug": "demo", "toy_id": 43}, "account-hash", SHA)

    def test_new_toy_requires_both_images_before_preview_or_record(self):
        path = self.bundle()
        gh, toy = FakeGitHub(), FakeToy(items=[])
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            with self.assertRaisesRegex(action.Failure, "create.poster and create.icon"):
                action.write_operation(self.operation_args(path, mode="preview"))
        self.assertEqual(toy.calls, [])
        self.assertEqual(gh.saved, [])
        self.assertTrue(toy.closed)

    def test_query_failure_never_falls_back_to_new_toy_creation(self):
        path = self.bundle()
        gh, toy = FakeGitHub(), FakeToy(items=[])
        with patch.object(toy, "toys", side_effect=action.Failure("Toy query failed")):
            with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
                with self.assertRaisesRegex(action.Failure, "Toy query failed"):
                    action.write_operation(self.operation_args(path, mode="preview"))
        self.assertEqual(toy.calls, [])
        self.assertEqual(gh.saved, [])

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

    def test_preview_requires_record_permission_before_toy_upload(self):
        path = self.bundle()
        for denied_step in ("record", "status"):
            with self.subTest(denied_step=denied_step):
                gh = FakeGitHub([self.binding()])
                toy = FakeToy(response={"preview_url": "https://www.bilibili.com/toy/preview/demo"})
                with patch.object(gh, denied_step, side_effect=action.Failure("Deployment permission denied")):
                    with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
                        with self.assertRaisesRegex(action.Failure, "permission denied"):
                            action.write_operation(self.operation_args(path, mode="preview"))
                self.assertEqual(toy.calls, [])
                self.assertFalse(action.jsonfile(path / "manifest.json")["preview"])

    def test_failed_preview_records_uncertain_state_without_upload_retry(self):
        path = self.bundle()
        gh = FakeGitHub([self.binding()])
        toy = FakeToy(error=action.Failure("preview response unavailable"))
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            with self.assertRaisesRegex(action.Failure, "preview response unavailable"):
                action.write_operation(self.operation_args(path, mode="preview"))
        self.assertEqual(len(toy.calls), 1)
        self.assertEqual([state for _, state, _ in gh.statuses], ["in_progress", "error"])
        self.assertFalse(action.jsonfile(path / "manifest.json")["preview"])

    def test_live_update_status_only_receipt_uses_verified_existing_id(self):
        path = self.bundle()
        self.mark_preview(path)
        gh, toy = FakeGitHub([self.binding()]), FakeToy(response={"status": "auditing"})
        summaries = []
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy), \
             patch.object(action, "summary", side_effect=summaries.append):
            action.write_operation(self.operation_args(path))
        self.assertEqual(len(toy.calls), 1)
        self.assertEqual(gh.statuses[-1][1], "success")
        self.assertFalse(any(x["payload"]["kind"] == "binding" for x in gh.saved))
        context = next(text for text in summaries if text.startswith("Operation context"))
        for value in (SHA, "demo", '"toy_id":42', '"release_id":"77"', action.jsonfile(path / "manifest.json")["package_sha"]):
            self.assertIn(value, context)

    def test_metadata_image_bytes_change_record_fingerprint_without_raw_values_in_summary(self):
        image = self.base / "assets" / "icon.png"
        image.write_bytes(b"first icon")
        config = json.loads(self.config.read_text())
        config["metadata"] = {"title": "private display title", "icon": "assets/icon.png"}
        self.config.write_text(json.dumps(config))
        fingerprints = []
        image_digests = []
        for name, content in (("one", b"first icon"), ("two", b"second icon")):
            image.write_bytes(content)
            bundle = self.base / name
            action.package(SimpleNamespace(config=str(self.config), bundle=str(bundle), source_sha=SHA, metadata_only=True))
            gh = FakeGitHub([self.binding()])
            toy = FakeToy(response={"status": "auditing"})
            summaries = []
            args = self.operation_args(bundle, mode="sync-metadata")
            args.release_id = ""
            with patch.dict(os.environ, {"TOY_CLI_SESSION_TOKEN": "secret-canary-never-log"}), \
                 patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy), \
                 patch.object(action, "summary", side_effect=summaries.append):
                action.write_operation(args)
            record = gh.saved[0]["payload"]
            fingerprints.append(record["metadata_sha"])
            image_digests.append(record["metadata_images_sha256"]["icon"])
            self.assertEqual(record["metadata_fields"], ["icon", "title"])
            context = "\n".join(summaries)
            self.assertIn(record["metadata_sha"], context)
            self.assertIn(record["metadata_images_sha256"]["icon"], context)
            self.assertNotIn("private display title", context)
            self.assertNotIn("secret-canary-never-log", context)
        self.assertNotEqual(fingerprints[0], fingerprints[1])
        self.assertNotEqual(image_digests[0], image_digests[1])

    def test_live_update_rejects_a_different_returned_toy_id(self):
        path = self.bundle()
        self.mark_preview(path)
        gh, toy = FakeGitHub([self.binding()]), FakeToy(response={"id": 43, "status": "auditing"})
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
            with self.assertRaisesRegex(action.Unknown, "unexpected Toy ID"):
                action.write_operation(self.operation_args(path))
        self.assertEqual(len(toy.calls), 1)
        self.assertEqual([state for _, state, _ in gh.statuses], ["in_progress", "error"])
        self.assertFalse(any(x["payload"]["kind"] == "binding" for x in gh.saved))

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

    def test_unknown_recovery_requires_same_toy_target_and_sends_no_write(self):
        record = {"id": 9, "payload": {
            "tool": action.TOOL, "kind": "submission", "sha": SHA,
            "slug": "demo", "account": "account-hash", "toy_id": 42,
        }}

        class RecoveryGitHub(FakeGitHub):
            def call(self, path):
                if path == "deployments/9":
                    return record
                return super().call(path)

        args = SimpleNamespace(deployment_id=9, resolution="accepted")
        gh, wrong_toy = RecoveryGitHub(states={9: "error"}), FakeToy(items=[{"id": 43, "slug": "demo"}])
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=wrong_toy):
            with self.assertRaisesRegex(action.Failure, "differs from original request"):
                action.resolve_unknown(args)
        self.assertEqual(gh.saved, [])
        self.assertEqual(gh.statuses, [])
        self.assertEqual(wrong_toy.calls, [])

        gh, correct_toy = RecoveryGitHub(states={9: "error"}), FakeToy()
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=correct_toy):
            action.resolve_unknown(args)
        self.assertEqual(gh.saved[0]["payload"]["toy_id"], 42)
        self.assertEqual([state for _, state, _ in gh.statuses], ["success", "success"])
        self.assertEqual(correct_toy.calls, [])

    def test_unknown_recovery_with_missing_url_requires_original_toy_id(self):
        class RecoveryGitHub(FakeGitHub):
            def __init__(self, toy_id):
                super().__init__(states={9: "error"})
                self.toy_id = toy_id

            def call(self, path):
                if path == "deployments/9":
                    return {"id": 9, "payload": {
                        "tool": action.TOOL, "kind": "submission", "sha": SHA,
                        "slug": "demo", "account": "account-hash", "toy_id": self.toy_id,
                    }}
                return super().call(path)

        args = SimpleNamespace(deployment_id=9, resolution="accepted")
        known_gh, known_toy = RecoveryGitHub(42), FakeToy(items=[{"id": 42, "slug": None}])
        with patch.object(action, "GitHub", return_value=known_gh), patch.object(action, "Toy", return_value=known_toy):
            action.resolve_unknown(args)
        self.assertEqual(known_gh.saved[0]["payload"]["toy_id"], 42)
        self.assertEqual(known_gh.statuses[-1][1], "success")
        self.assertEqual(known_toy.calls, [])

        new_gh, new_toy = RecoveryGitHub(None), FakeToy(items=[{"id": 42, "slug": None}])
        with patch.object(action, "GitHub", return_value=new_gh), patch.object(action, "Toy", return_value=new_toy):
            with self.assertRaisesRegex(action.Failure, "listing URL is unavailable"):
                action.resolve_unknown(args)
        self.assertEqual(new_gh.saved, [])
        self.assertEqual(new_gh.statuses, [])
        self.assertEqual(new_toy.calls, [])

    def test_recovery_shows_original_request_before_changing_status(self):
        events = []

        class RecoveryGitHub(FakeGitHub):
            def __init__(self):
                super().__init__(states={9: "error"})

            def call(self, path):
                if path == "deployments/9":
                    return {"id": 9, "created_at": "2026-10-28T01:02:03Z", "payload": {
                        "tool": action.TOOL, "kind": "submission", "sha": SHA,
                        "slug": "demo", "account": "account-hash", "toy_id": 42,
                        "package_sha": "b" * 64, "run_id": "17", "release_id": "77",
                    }}
                return super().call(path)

            def status(self, record, state, description):
                events.append(("status", state))
                return super().status(record, state, description)

        with patch.object(action, "GitHub", return_value=RecoveryGitHub()), \
             patch.object(action, "Toy") as construct_toy, \
             patch.object(action, "summary", side_effect=lambda value: events.append(("summary", value))):
            action.resolve_unknown(SimpleNamespace(deployment_id=9, resolution="not-accepted"))
            construct_toy.assert_not_called()
        self.assertEqual(events[0][0], "summary")
        for value in (SHA, "demo", "b" * 64, '"toy_id":42', '"release_id":"77"', "2026-10-28T01:02:03Z"):
            self.assertIn(value, events[0][1])
        self.assertEqual(events[1], ("status", "failure"))

    def test_accepted_create_with_record_failure_cannot_be_created_again(self):
        (self.base / "assets" / "icon.png").write_bytes(b"icon")
        config = json.loads(self.config.read_text())
        config["create"]["icon"] = "assets/icon.png"
        self.config.write_text(json.dumps(config))

        class StorageGitHub(FakeGitHub):
            def __init__(self, fail_at):
                super().__init__()
                self.fail_at = fail_at

            def call(self, path):
                if path.startswith("deployments/"):
                    return next(r for r in self.records_data if str(r["id"]) == path.split("/")[-1])
                return super().call(path)

            def record(self, sha, slug, kind, **payload):
                if self.fail_at == "binding" and kind == "binding":
                    self.fail_at = None
                    raise action.Failure("binding record unavailable")
                result = super().record(sha, slug, kind, **payload)
                result["payload"].update(tool=action.TOOL, schema=action.SCHEMA)
                self.records_data.append(result)
                return result

            def status(self, record, state, description):
                if self.fail_at == "submission-status" and record["payload"]["kind"] == "submission" and state == "success":
                    self.fail_at = None
                    raise action.Failure("status unavailable")
                super().status(record, state, description)
                self.states[record["id"]] = state

        for failure_point in ("binding", "submission-status"):
            with self.subTest(failure_point=failure_point):
                path = self.bundle("bundle-" + failure_point)
                manifest = action.jsonfile(path / "manifest.json")
                manifest.update(preview=True, account="account-hash", toy_id=None, preview_run="17")
                action.save(path / "manifest.json", manifest)
                gh = StorageGitHub(failure_point)
                toy = FakeToy(items=[], response={"id": 99, "status": "auditing"})
                args = self.operation_args(path)
                with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy):
                    with self.assertRaisesRegex(action.Failure, "Preserve Toy ID 99 and reconcile Deployment 100"):
                        action.write_operation(args)
                    self.assertEqual(len(toy.calls), 1)
                    self.assertEqual(toy.calls[0][0][0], "create")
                    toy.items = [{"id": 99, "slug": "demo"}]
                    with self.assertRaisesRegex(action.Failure, "Previous write outcome is unknown"):
                        action.write_operation(args)
                    self.assertEqual(len(toy.calls), 1)
                    action.resolve_unknown(SimpleNamespace(deployment_id=100, resolution="accepted"))
                    action.write_operation(args)
                self.assertEqual(len(toy.calls), 1)
                self.assertEqual(gh.states[100], "success")

    def test_manual_override_cannot_run_from_release_event(self):
        path = self.bundle()
        gh, toy = FakeGitHub([self.binding()]), FakeToy()
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release"}):
            with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy) as construct_toy:
                with self.assertRaisesRegex(action.Failure, "manual dispatch"):
                    action.write_operation(self.operation_args(path, override=True))
                construct_toy.assert_not_called()

    def test_manual_override_summary_identifies_release_and_rebuilt_package(self):
        path = self.bundle()
        summaries = []
        gh, toy = FakeGitHub([self.binding()]), FakeToy(response={"status": "auditing"})
        with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy", return_value=toy), \
             patch.object(action, "summary", side_effect=summaries.append):
            action.write_operation(self.operation_args(path, override=True))
        context = next(item for item in summaries if item.startswith("Operation context"))
        self.assertIn('"override":true', context)
        self.assertIn('"release_id":"77"', context)
        self.assertIn('"release_tag":"v1"', context)
        self.assertIn(action.jsonfile(path / "manifest.json")["package_sha"], context)

    def test_submit_revalidates_published_release_tag_and_source_before_toy_access(self):
        path = self.bundle()
        self.mark_preview(path)
        for release_id, release_sha, source_sha, error in (
            ("", SHA, SHA, "published Release"),
            ("88", SHA, SHA, "resource not found"),
            ("77", "b" * 40, SHA, "does not point"),
            ("77", SHA, "b" * 40, "commit"),
        ):
            with self.subTest(release_id=release_id, release_sha=release_sha, source_sha=source_sha):
                args = self.operation_args(path)
                args.release_id = release_id
                args.source_sha = source_sha
                gh = FakeGitHub([self.binding()], release_sha=release_sha)
                with patch.object(action, "GitHub", return_value=gh), patch.object(action, "Toy") as construct_toy:
                    with self.assertRaisesRegex(action.Failure, error):
                        action.write_operation(args)
                    construct_toy.assert_not_called()

    def test_submit_matches_event_release_or_manual_selection(self):
        manifest = {"sha": SHA}
        args = SimpleNamespace(release_id="77", source_sha=SHA, override=False)
        event = self.base / "event.json"
        event.write_text(json.dumps({"release": {"id": 88}}))
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}):
            with self.assertRaisesRegex(action.Failure, "Triggered Release"):
                action.validate_submission_release(FakeGitHub(), args, manifest)
        event.write_text(json.dumps({"inputs": {"operation": "override", "release-tag": "other"}}))
        args.override = True
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_EVENT_PATH": str(event)}):
            with self.assertRaisesRegex(action.Failure, "same Release"):
                action.validate_submission_release(FakeGitHub(), args, manifest)
        event.write_text(json.dumps({"inputs": {"operation": "override", "release-tag": "v1"}}))
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_EVENT_PATH": str(event)}):
            self.assertEqual(action.validate_submission_release(FakeGitHub(), args, manifest)["id"], 77)

    def test_release_evidence_selects_only_same_repo_successful_preview(self):
        event = self.base / "release.json"
        event.write_text(json.dumps({"release": {
            "id": 77, "tag_name": "v1", "draft": False, "prerelease": False,
        }}))
        published = {}
        summaries = []
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}), \
             patch.object(action, "GitHub", return_value=FakePlanningGitHub(source_repository_id=2)), \
             patch.object(action, "output", side_effect=lambda key, value: published.__setitem__(key, value)), \
             patch.object(action, "summary", side_effect=summaries.append):
            action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))
        self.assertEqual(published["source-sha"], SHA)
        self.assertEqual(published["artifact-id"], 23)
        self.assertEqual(published["expected-package-sha"], "a" * 64)
        self.assertEqual(published["build"], "false")
        self.assertTrue(any('"artifact_id":23' in item and '"preview_run":"17"' in item and '"package_sha":"' + "a" * 64 + '"' in item for item in summaries))

        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}), \
             patch.object(action, "GitHub", return_value=FakePlanningGitHub(source_repository_id=999)), \
             patch.object(action, "output"):
            with self.assertRaisesRegex(action.Failure, "No usable successful preview artifact"):
                action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))

    def test_release_stops_on_missing_or_expired_preview_artifact(self):
        event = self.base / "release.json"
        event.write_text(json.dumps({"release": {
            "id": 77, "tag_name": "v1", "draft": False, "prerelease": False,
        }}))

        class ArtifactGitHub(FakePlanningGitHub):
            def __init__(self, artifacts):
                super().__init__()
                self.artifacts = artifacts

            def pages(self, path, key=None):
                if path == "actions/runs/17/artifacts":
                    return self.artifacts
                return super().pages(path, key)

        for artifacts in ([], [{"id": 23, "name": "toy-preview-" + SHA, "expired": True}]):
            with self.subTest(artifacts=artifacts):
                outputs = {}
                with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "release", "GITHUB_EVENT_PATH": str(event)}), \
                     patch.object(action, "GitHub", return_value=ArtifactGitHub(artifacts)), \
                     patch.object(action, "output", side_effect=lambda key, value: outputs.__setitem__(key, value)):
                    with self.assertRaisesRegex(action.Failure, "No usable successful preview artifact"):
                        action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))
                self.assertEqual(outputs["operation"], "submit")
                self.assertEqual(outputs["build"], "false")
                self.assertNotIn("artifact-id", outputs)

    def test_binding_lookup_scans_deployment_second_page(self):
        github = object.__new__(action.GitHub)
        paths = []
        binding = {"id": 101, "payload": {
            "tool": action.TOOL, "schema": action.SCHEMA, "kind": "binding",
            "slug": "demo", "account": "account-hash", "toy_id": 42,
        }}

        def page(path):
            paths.append(path)
            if path.endswith("page=1"):
                return [{"id": n, "payload": {"tool": "other"}} for n in range(1, 101)]
            if path.endswith("page=2"):
                return [binding]
            raise AssertionError("Unexpected pagination request")

        github.call = page
        self.assertEqual(github.records("demo", "binding"), [binding])
        self.assertEqual(len(paths), 2)

    def test_deployment_record_keeps_request_time_for_later_reconciliation(self):
        github = object.__new__(action.GitHub)
        github.call = lambda path, data: {"id": 9, "payload": data["payload"]}
        record = github.record(SHA, "demo", "submission", package_sha="b" * 64, toy_id=42)
        requested_at = record["payload"]["requested_at"]
        self.assertRegex(requested_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        shown = []
        with patch.object(action, "summary", side_effect=shown.append):
            action.operation_summary("resolve-unknown", SHA, "demo", requested_at=requested_at, package_sha="b" * 64, toy_id=42)
        self.assertIn(requested_at, shown[0])

    def test_fork_pull_request_plan_only_checks_package(self):
        event = self.base / "fork-pr.json"
        event.write_text(json.dumps({"pull_request": {"head": {"repo": {"fork": True}}}}))
        outputs = {}

        class ForkGitHub(FakePlanningGitHub):
            def call(self, path):
                if path != "":
                    raise AssertionError("Fork PR should not inspect Releases or deployments")
                return super().call(path)

            def pages(self, path, key=None):
                raise AssertionError("Fork PR should not read deployment artifacts")

        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(event)}), \
             patch.object(action, "GitHub", return_value=ForkGitHub()), \
             patch.object(action, "Toy") as toy_constructor, \
             patch.object(action, "output", side_effect=lambda key, value: outputs.__setitem__(key, value)):
            action.plan(SimpleNamespace(workflow_path=".github/workflows/toy.yml"))
            toy_constructor.assert_not_called()
        self.assertEqual(outputs["operation"], "check")
        self.assertEqual(outputs["build"], "true")
        self.assertEqual(outputs["release-id"], "")
        self.assertNotIn("artifact-id", outputs)


if __name__ == "__main__":
    unittest.main()
