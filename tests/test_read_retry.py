"""Only identity and listing queries may repeat after an uncertain CLI failure."""

from __future__ import annotations

import subprocess
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import toy_action as action


def result(returncode, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class ToyReadRetryTests(unittest.TestCase):
    def setUp(self):
        self.toy = object.__new__(action.Toy)
        self.toy.binary = "/temporary/toy"
        self.toy.env = {"TOY_CLI_SESSION_TOKEN": "private-test-token"}

    def test_bounded_retries_only_for_transient_identity_and_list_reads(self):
        good = result(0, '{"uid":123}')
        cases = (
            ("timeout", [subprocess.TimeoutExpired("toy", 100), good], ["whoami"]),
            ("transport", [result(1, stderr="temporary network failure"), good], ["mylist"]),
            ("invalid-json", [result(0, stdout="gateway HTML"), good], ["whoami"]),
        )
        for name, sequence, argv in cases:
            with self.subTest(name=name):
                with patch.object(action.subprocess, "run", side_effect=sequence) as run, \
                     patch.object(action.time, "sleep") as sleep:
                    self.assertEqual(self.toy.call(argv)["uid"], 123)
                self.assertEqual(run.call_count, 2)
                sleep.assert_called_once()

        with patch.object(action.subprocess, "run", side_effect=[subprocess.TimeoutExpired("toy", 100)] * 3) as run, \
             patch.object(action.time, "sleep") as sleep:
            with self.assertRaisesRegex(action.Failure, "timed out"):
                self.toy.call(["whoami"])
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_auth_business_usage_missing_binary_and_uploads_never_retry(self):
        cases = (
            (["whoami"], False, result(1, stderr="status=200 code=307029 message=expired"), action.Failure),
            (["whoami"], False, result(1, stderr="status=200 code=307009 message=rejected"), action.Failure),
            (["mylist"], False, result(1, stderr="unknown flag: --page"), action.Failure),
            (["whoami"], False, FileNotFoundError("toy"), action.Failure),
            (["create", "package.zip"], False, subprocess.TimeoutExpired("toy", 100), action.Failure),
            (["update", "42", "package.zip"], False, result(1, stderr="network failure"), action.Failure),
            (["update", "42", "package.zip", "--yes"], True, subprocess.TimeoutExpired("toy", 100), action.Unknown),
        )
        for argv, write, failure, error in cases:
            with self.subTest(argv=argv, failure=str(type(failure))):
                with patch.object(action.subprocess, "run", side_effect=[failure]) as run, \
                     patch.object(action.time, "sleep") as sleep:
                    with self.assertRaises(error):
                        self.toy.call(argv, write=write)
                run.assert_called_once()
                sleep.assert_not_called()


class GitHubReadRetryTests(unittest.TestCase):
    def test_only_get_retries_rate_limit_and_never_retries_auth_or_write(self):
        github = object.__new__(action.GitHub)
        github.repo = "example/repo"
        github.token = "private-test-token"
        limited = lambda code: HTTPError("https://api.github.com", code, "error", {}, None)
        with patch.object(action.urllib.request, "urlopen", side_effect=[limited(429), BytesIO(b'{"ok":true}')]) as open_url, \
             patch.object(action.time, "sleep") as sleep:
            self.assertEqual(github.call("")["ok"], True)
        self.assertEqual(open_url.call_count, 2)
        sleep.assert_called_once()

        for code, data in ((401, None), (429, {"operation": "write"})):
            with self.subTest(code=code, data=data):
                with patch.object(action.urllib.request, "urlopen", side_effect=limited(code)) as open_url, \
                     patch.object(action.time, "sleep") as sleep:
                    with self.assertRaises(action.Failure):
                        github.call("deployments", data)
                open_url.assert_called_once()
                sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
