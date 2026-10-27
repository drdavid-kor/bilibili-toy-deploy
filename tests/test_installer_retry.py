from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from scripts import install_cli


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid/toy", code, "test error", None, None)


class BrokenRead(io.BytesIO):
    def __init__(self) -> None:
        super().__init__(b"partial download")
        self.reads = 0

    def read(self, size: int = -1) -> bytes:
        self.reads += 1
        if self.reads == 2:
            raise TimeoutError("download stalled")
        return super().read(size)


class InstallerRetryTests(unittest.TestCase):
    def test_partial_timeout_and_503_use_fresh_temp_files_then_replace(self) -> None:
        binary = b"verified binary after retry"
        expected = hashlib.sha256(binary).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "toy"
            destination.write_bytes(b"previous binary")
            names = []
            real_mkstemp = install_cli.tempfile.mkstemp

            def traced_mkstemp(*args, **kwargs):
                fd, name = real_mkstemp(*args, **kwargs)
                names.append(name)
                return fd, name

            with (
                patch.dict(install_cli.PINNED_SHA256, {("v0.6.4", "linux_amd64"): expected}),
                patch.object(install_cli.urllib.request, "urlopen", side_effect=[BrokenRead(), http_error(503), io.BytesIO(binary)]) as open_url,
                patch.object(install_cli.tempfile, "mkstemp", side_effect=traced_mkstemp),
                patch.object(install_cli.time, "sleep") as sleep,
            ):
                result = install_cli.download_verified("v0.6.4", destination, "linux_amd64")

            self.assertEqual(result, destination.resolve())
            self.assertEqual(destination.read_bytes(), binary)
            self.assertEqual(open_url.call_count, 3)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])
            self.assertEqual(len(set(names)), 3)
            self.assertEqual(list(Path(directory).glob(".toy-download-*")), [])

    def test_checksum_fetch_retries_429_then_uses_that_digest(self) -> None:
        binary = b"future official binary"
        checksum = hashlib.sha256(binary).hexdigest().encode() + b"  toy_linux_amd64\n"
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "toy"
            with (
                patch.object(install_cli.urllib.request, "urlopen", side_effect=[http_error(429), io.BytesIO(checksum), io.BytesIO(binary)]) as open_url,
                patch.object(install_cli.time, "sleep") as sleep,
            ):
                install_cli.download_verified("v0.6.5", destination, "linux_amd64")
            self.assertEqual(destination.read_bytes(), binary)
            self.assertEqual(open_url.call_count, 3)
            self.assertTrue(open_url.call_args_list[0].args[0].endswith(".sha256"))
            self.assertTrue(open_url.call_args_list[1].args[0].endswith(".sha256"))
            sleep.assert_called_once_with(1)

    def test_404_and_digest_mismatch_do_not_retry_or_replace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "toy"
            destination.write_bytes(b"previous binary")
            with (
                patch.object(install_cli.urllib.request, "urlopen", side_effect=http_error(404)) as open_url,
                patch.object(install_cli.time, "sleep") as sleep,
            ):
                with self.assertRaises(urllib.error.HTTPError):
                    install_cli.download_verified("v0.6.4", destination, "linux_amd64")
                open_url.assert_called_once()
                sleep.assert_not_called()
            with (
                patch.object(install_cli.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong binary")) as open_url,
                patch.object(install_cli.time, "sleep") as sleep,
            ):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    install_cli.download_verified("v0.6.4", destination, "linux_amd64")
                open_url.assert_called_once()
                sleep.assert_not_called()
            self.assertEqual(destination.read_bytes(), b"previous binary")
            self.assertEqual(list(Path(directory).glob(".toy-download-*")), [])

    def test_transient_errors_stop_after_three_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "toy"
            destination.write_bytes(b"previous binary")
            with (
                patch.object(install_cli.urllib.request, "urlopen", side_effect=[http_error(503) for _ in range(3)]) as open_url,
                patch.object(install_cli.time, "sleep") as sleep,
            ):
                with self.assertRaises(urllib.error.HTTPError):
                    install_cli.download_verified("v0.6.4", destination, "linux_amd64")
                self.assertEqual(open_url.call_count, 3)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])
            self.assertEqual(destination.read_bytes(), b"previous binary")
            self.assertEqual(list(Path(directory).glob(".toy-download-*")), [])


if __name__ == "__main__":
    unittest.main()
