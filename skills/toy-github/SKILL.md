---
name: toy-github
description: Initialize a static web project for Bilibili Toy or adapt an existing HTML/Vite project, then connect it to the bilibili-toy-deploy GitHub Action. Use for Toy GitHub onboarding, not ordinary local Toy publishing.
license: MIT
---

# Connect a web project to Bilibili Toy

This skill has two modes. For a new project, read [new-project.md](references/new-project.md). For an existing frontend, read [existing-project.md](references/existing-project.md). If the user has not identified a mode, inspect the target directory: an empty target means new; an existing application means adaptation. If ambiguous, ask which project should change.

The installed skill may contain only `skills/toy-github/`. Do not assume repository templates, workflows, scripts or docs exist next to this file. Obtain them from the **same published tag** selected for the Action, using the repository release or a temporary checkout. Pin that tag in the user's workflow. If no published tag can be verified, report that the Action cannot yet be installed; do not invent a release ref or silently use `main`.

Supported scope is plain HTML/CSS/JavaScript and Vite, including React and Vue. The user supplies or chooses the build command; the Action receives a built static directory. For another framework, inspect compatibility and explain what remains unverified rather than claim full support. Backend migration, replacing login, and redesigning storage need a separate user decision before those dependent changes.

Read project instructions and current files first. Preserve existing features and unrelated edits. Use the repository's current schema, templates and example workflow as the single source for fields and event names; do not maintain a second protocol in this skill. Keep Bilibili session material and access passwords out of source files, chat, logs and artifacts. Use official `toy` CLI through the Action, never unpublished HTTP endpoints.

Complete local code, config, and workflow changes within the user's authorized scope. Where GitHub access and credentials permit, run the relevant checks and a preview, then report the actual preview result. A green static precheck does not prove the Toy page works: verify the page itself when possible. State whether work stopped at local preparation, GitHub workflow run, Toy preview, or accepted review submission. A Release submits for review; it does not prove the new version is live.

The skill does not grant a creator account or permission to publish an arbitrary user's project. Follow the current user's authorization for remote repository creation, pushing workflows, storing Secrets and triggering review submission. When a change would alter login, storage or backend behavior, show the concrete impact and wait for the user's decision on that change.
