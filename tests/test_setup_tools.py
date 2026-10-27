from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install_cli, set_secret


class InstallCliTests(unittest.TestCase):
    def test_download_verifies_digest_before_replacing_existing_binary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "toy"
            destination.write_bytes(b"previous working binary")
            with patch.object(install_cli.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong binary")):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    install_cli.download_verified("v0.6.4", destination, "linux_amd64")
            self.assertEqual(destination.read_bytes(), b"previous working binary")
            self.assertEqual(list(Path(directory).glob(".toy-download-*")), [])

    def test_unknown_version_checks_official_checksum_and_rejects_invalid_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(install_cli.urllib.request, "urlopen", return_value=io.BytesIO(b"not-a-checksum")):
                with self.assertRaisesRegex(ValueError, "checksum"):
                    install_cli.download_verified("v0.6.5", Path(directory) / "toy", "linux_amd64")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_rejects_unrecorded_platform(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            install_cli.release_platform("Linux", "aarch64")


class SetSecretTests(unittest.TestCase):
    def test_uses_stdin_and_never_places_token_in_arguments_or_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.json"
            session.write_text(json.dumps({"session_token": "private-test-value"}))
            seen = {}

            def fake_run(argv, **kwargs):
                seen.update(argv=argv, **kwargs)
                return type("Completed", (), {"returncode": 0})()

            with patch.object(set_secret.subprocess, "run", side_effect=fake_run):
                set_secret.set_repository_secret("example/repo", set_secret.read_session_token(session))
            self.assertEqual(seen["input"], "private-test-value")
            self.assertNotIn("private-test-value", " ".join(seen["argv"]))
            self.assertEqual(seen["argv"][-2:], ["--repo", "example/repo"])
            self.assertTrue(seen["capture_output"])

    def test_bad_session_and_bad_repo_do_not_invoke_github(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.json"
            session.write_text(json.dumps({"session_token": ""}))
            with self.assertRaises(ValueError):
                set_secret.read_session_token(session)
        with patch.object(set_secret.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                set_secret.set_repository_secret("--unknown/repo", "example")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
