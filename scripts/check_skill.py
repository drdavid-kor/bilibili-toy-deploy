#!/usr/bin/env python3
"""Validate the distributed skill's frontmatter and local references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LOCAL_MARKDOWN_LINK = re.compile(r"\]\((references/[^)#]+\.md)(?:#[^)]+)?\)")


def check_skill(directory: Path) -> list[str]:
    problems: list[str] = []
    skill = directory / "SKILL.md"
    if not skill.is_file():
        return [f"Missing {skill}"]
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return ["SKILL.md must begin with YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end == -1:
        return ["SKILL.md frontmatter is not closed"]
    frontmatter = text[4:end]
    values: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            problems.append("Malformed frontmatter line")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    if values.get("name") != directory.name or not SKILL_NAME.fullmatch(values.get("name", "")):
        problems.append("Frontmatter name must match the skill directory")
    if not values.get("description") or len(values["description"]) < 24:
        problems.append("Frontmatter description is missing or too short")
    body = text[end + 5 :]
    if len(body.strip()) < 100:
        problems.append("SKILL.md has no substantive instructions")
    for target in LOCAL_MARKDOWN_LINK.findall(body):
        if not (directory / target).is_file():
            problems.append(f"Missing linked reference: {target}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    problems = check_skill(args.directory)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"Skill structure verified: {args.directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
