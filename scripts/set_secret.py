#!/usr/bin/env python3
"""Copy a local Toy CLI session token into a GitHub Actions repository secret."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_SESSION = Path("~/.toy/session.json")
SECRET_NAME = "TOY_SESSION_TOKEN"
REPOSITORY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+")


def read_session_token(path: Path) -> str:
    path = path.expanduser()
    if path.stat().st_size > 64 * 1024:
        raise ValueError("Session file is unexpectedly large")
    data = json.loads(path.read_text(encoding="utf-8"))
    token = data.get("session_token") if isinstance(data, dict) else None
    if not isinstance(token, str) or not token or token != token.strip() or "\n" in token:
        raise ValueError("Session file does not contain a valid session_token")
    return token


def set_repository_secret(repo: str, token: str) -> None:
    if not REPOSITORY_RE.fullmatch(repo):
        raise ValueError("Repository must be in owner/name form")
    result = subprocess.run(
        ["gh", "secret", "set", SECRET_NAME, "--app", "actions", "--repo", repo],
        input=token,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        # The CLI may include request details in stderr. Never relay its output
        # from a command that handled a session token.
        raise RuntimeError("GitHub CLI could not save the secret. Check gh auth status and repository access.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository as owner/name")
    parser.add_argument("--session-file", type=Path, default=DEFAULT_SESSION)
    args = parser.parse_args()
    try:
        token = read_session_token(args.session_file)
        set_repository_secret(args.repo, token)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Secret setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {SECRET_NAME} to {args.repo}; token value was not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
