#!/usr/bin/env python3
"""Copy a Toy starter into an empty directory and set its public identity."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "templates"
DEFAULT_WORKFLOW = PROJECT_ROOT / "examples" / "workflows" / "toy.yml"
SLUG = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def scaffold(template: str, destination: Path, slug: str, title: str, workflow: Path | None = None) -> Path:
    if not SLUG.fullmatch(slug):
        raise ValueError("slug must be 1–64 ASCII letters, numbers, underscores, or hyphens")
    if not title.strip() or len(title) > 100:
        raise ValueError("title must be 1–100 characters")
    if template not in {"html", "vite"}:
        raise ValueError("template must be html or vite")

    destination = destination.expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"destination must be empty: {destination}")

    source = TEMPLATES / template
    if not source.is_dir():
        raise FileNotFoundError(f"template is unavailable: {source}")

    workflow = workflow or DEFAULT_WORKFLOW
    if not workflow.is_file():
        raise FileNotFoundError(f"workflow template is unavailable: {workflow}")

    shutil.copytree(source, destination, dirs_exist_ok=True)
    config_path = destination / "toy.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["slug"] = slug
    config["create"]["title"] = title.strip()
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index = destination / ("site/index.html" if template == "html" else "index.html")
    page = index.read_text(encoding="utf-8")
    page = page.replace("<title>My Toy · 我的 Toy</title>", f"<title>{html.escape(title.strip())}</title>")
    index.write_text(page, encoding="utf-8")

    workflow_dir = destination / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workflow, workflow_dir / "toy.yml")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", choices=("html", "vite"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--workflow-template", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        destination = scaffold(args.template, args.destination, args.slug, args.title, args.workflow_template)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(f"Created {destination}")
    print("Next: set the Toy session as a GitHub Secret, push to your repository, and inspect the preview.")


if __name__ == "__main__":
    main()
