#!/usr/bin/env python3
"""Install a verified official Toy CLI binary without executing an installer."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import os
import platform
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://boss.hdslb.com/toy-cli/toy/releases"
DEFAULT_VERSION = "v0.6.4"
PINNED_SHA256 = {
    ("v0.6.4", "linux_amd64"): "d5d1377ffd7b037fb23c3f48ba77c2230cd446976dec74930bf99fadfb0dcf94",
    ("v0.6.4", "darwin_arm64"): "f2e5fc6610d70528420475f89b210bb76579e40ffc2f2b80dee50b869661436b",
}
MAX_BINARY_BYTES = 100 * 1024 * 1024
MAX_DOWNLOAD_ATTEMPTS = 3


def release_platform(system: str | None = None, machine: str | None = None) -> str:
    """Return an architecture with a recorded checksum, or reject it."""
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    mapped = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(machine)
    name = f"{system}_{mapped}"
    if name not in {"linux_amd64", "darwin_arm64"}:
        raise ValueError(f"Unsupported CLI platform: {system}/{machine}")
    return name


def archive_url(version: str, target: str) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?", version):
        raise ValueError("Toy CLI version must look like v0.6.4")
    if target not in {"linux_amd64", "darwin_arm64"}:
        raise ValueError(f"Unsupported CLI platform: {target}")
    return f"{BASE_URL}/{version}/toy_{target}"


def _read_checksum(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as response:
        raw = response.read(256).decode("ascii", errors="strict")
    digest = raw.split(maxsplit=1)[0].lower()
    if not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Official checksum endpoint did not return a SHA-256 digest")
    return digest


def _retry_transient(operation):
    for attempt in range(MAX_DOWNLOAD_ATTEMPTS):
        try:
            return operation()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 and not 500 <= exc.code < 600:
                raise
            if attempt == MAX_DOWNLOAD_ATTEMPTS - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead):
            if attempt == MAX_DOWNLOAD_ATTEMPTS - 1:
                raise
        time.sleep(2**attempt)


def download_verified(version: str, destination: Path, target: str | None = None) -> Path:
    """Download, verify, and atomically replace destination; leave old file on failure."""
    target = target or release_platform()
    url = archive_url(version, target)
    expected = PINNED_SHA256.get((version, target)) or _retry_transient(lambda: _read_checksum(url + ".sha256"))
    destination = Path(destination).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    def download_once() -> Path:
        fd, temporary_name = tempfile.mkstemp(prefix=".toy-download-", dir=destination.parent)
        temporary = Path(temporary_name)
        try:
            digest = hashlib.sha256()
            size = 0
            with os.fdopen(fd, "wb") as output, urllib.request.urlopen(url, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_BINARY_BYTES:
                        raise ValueError("Toy CLI archive exceeds the size limit")
                    digest.update(chunk)
                    output.write(chunk)
            if size == 0 or digest.hexdigest() != expected:
                raise ValueError("Toy CLI SHA-256 mismatch; existing binary was preserved")
            temporary.chmod(0o755)
            temporary.replace(destination)
            return destination
        finally:
            temporary.unlink(missing_ok=True)

    return _retry_transient(download_once)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Exact Toy CLI version")
    parser.add_argument("--destination", type=Path, required=True, help="Path to the installed toy binary")
    args = parser.parse_args()
    try:
        installed = download_verified(args.version, args.destination)
    except (OSError, ValueError, urllib.error.URLError, http.client.IncompleteRead) as exc:
        print(f"Toy CLI installation failed: {exc}", file=sys.stderr)
        return 1
    print(installed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
