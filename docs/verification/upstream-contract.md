# Toy CLI upstream contract, 2026-10-27

This note records public upstream evidence for the first implementation. It does not establish that a GitHub-hosted runner can authenticate or that the server retains every omitted field; those need live tests with an authorized test Toy.

## Pinned sources and binaries

| Item | Version / digest | Evidence |
| --- | --- | --- |
| Official skills and DSH repository | `ae156ecb3391dfb22bdd93d45d6b0067e1e5b723` | [GitHub commit](https://github.com/bilibili/toy/commit/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723) |
| Vendored `toy_doctor.py` | SHA-256 `cbbf1244fff1179cfa48272cddb2cbcbd870da73d5fff1c5f30720231d6eeb0c` | [Pinned source](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/skills/toy/scripts/toy_doctor.py), `vendor/UPSTREAM.json` |
| CLI Linux amd64 | `v0.6.4`, SHA-256 `d5d1377ffd7b037fb23c3f48ba77c2230cd446976dec74930bf99fadfb0dcf94` | [Archive](https://boss.hdslb.com/toy-cli/toy/releases/v0.6.4/toy_linux_amd64), [checksum](https://boss.hdslb.com/toy-cli/toy/releases/v0.6.4/toy_linux_amd64.sha256) |
| CLI macOS arm64 | `v0.6.4`, SHA-256 `f2e5fc6610d70528420475f89b210bb76579e40ffc2f2b80dee50b869661436b` | [Archive](https://boss.hdslb.com/toy-cli/toy/releases/v0.6.4/toy_darwin_arm64), [checksum](https://boss.hdslb.com/toy-cli/toy/releases/v0.6.4/toy_darwin_arm64.sha256) |

The official installer resolves `VERSION` to `releases/<version>/toy_<os>_<arch>` and downloads the adjacent `.sha256`. An explicit version does not fall back to latest. We fetched the macOS arm64 binary into a separate temporary path, checked its SHA-256, and verified that `toy version` reports `v0.6.4` with CLI build `68f6071` dated 2026-10-20. The local global `toy` remains v0.5.0. The Linux checksum came from its official adjacent `.sha256` endpoint; the Linux binary has not been executed on this macOS host.

## CLI command and JSON shape

The v0.6.4 `--help-json` schema reports `create <path>`, `update [id] [path]`, `mylist --page/--size`, `whoami`, and global `--json`. `create` and `update` take `--yes` to submit. `create` accepts a directory, one HTML file, or an existing ZIP; the ZIP must have a valid Toy entry, with `index.html` in the package root for the chosen implementation. `update` accepts the same package argument; metadata-only update omits `path` and submits directly. See the [official skill](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/skills/toy/SKILL.md).

For `--json`, the official [DSH fake CLI](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/dsh/packages/toy/test/fixtures/fake-toy.mjs) and [service adapter](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/dsh/packages/toy/src/host/service.js) show:

| Operation | Useful fields | Safe interpretation |
| --- | --- | --- |
| `whoami --json` | `uid`, `name` in fixture | Validate current account, but accept the actual v0.6.4 response after live inspection. Do not store the full response. |
| `mylist --json --page N --size M` | `total`, `pn`, `ps`, `list` | Require list array and coherent pagination. Query all pages before declaring a slug absent. |
| `mylist` item | `id`, `title`, `url`, `status`, `visibility`, optional metadata | The DSH adapter derives slug from `/toy/<slug>/` in `url`; it does not rely on a top-level `slug`. A missing or malformed URL makes automatic slug matching inconclusive. |
| `create/update <path> --json` | `preview_url` | Preview only. No Toy ID or accepted submission is implied. |
| `create/update <path> --json --yes` | `id`, `status`, possibly `preview_url` | Require positive ID and a successful CLI exit before recording submission. A returned status such as `reviewing` does not mean online. |
| `update <id> --title ... --json --yes` (without `path`) | `id`, `status` | Direct metadata submission; no package preview is produced. |

The official [DSH argv builder](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/dsh/packages/toy/src/argv.js) only adds update metadata flags when explicitly supplied. This verifies client behavior; the server's final retention of omitted fields still requires a live before/after check. The v0.6.4 help lists category choices `GAME`, `INTERACTIVE_PLAY`, `TOOL`, `TEST`, `GUIDE`, `COLLECTION`, `OTHER` and visibility choices `link-only`, `password`, `public`. The `update` command does not expose `--slug`.

The CLI strips the upstream `{code,message,data}` envelope on successful JSON calls; do not expect an outer `data` member. For failed calls, the official [error reference](https://github.com/bilibili/toy/blob/ae156ecb3391dfb22bdd93d45d6b0067e1e5b723/skills/toy/references/error-codes.md) distinguishes session expiry (`307001`, `307029`), business errors (`status=<n> code=<n> message=...`), usage errors, and ambiguous network failures. A write call that times out or returns invalid output after launch is an unknown result, not proof that nothing was submitted.

## Doctor invocation

The vendored checker takes a static directory, ZIP, or single HTML; `--json` prints `{ "ok": bool, "findings": [{"severity":"ERROR|WARN", "file":string, "message":string}] }`. It exits 1 on ERROR, 0 otherwise. It can validate the intended slug with `--slug` and entry layout with `--require-root-index`. A valid minimal `index.html` produced `{ "ok": true, "findings": [] }` locally.

The checker is advisory for rendering and only captures static issues. It does not establish that a deployed Toy page actually loads and works in a browser. Its own entry HTML size rule uses a 1 MiB limit and marks larger entries ERROR; its other large HTML checks produce WARN. Use the pinned checker unchanged for first release, attribute it with `vendor/LICENSE`, and review upstream changes deliberately.

## Implementation rules from this evidence

1. Download exact `v0.6.4` archive for the runner OS and architecture; verify a locally pinned checksum before execution. Do not execute `curl | bash` in every job or silently upgrade CLI.
2. Treat `--help-json` as a version check for required commands and flags, not as a substitute for integration tests of server behavior.
3. Query `mylist` through every page and require an identifiable slug before automatic adoption. If list fields or pagination differ from the fixture, parse the live response conservatively and save a sanitized fixture for tests.
4. Package the built static directory deterministically as a ZIP with root `index.html`, fingerprint the archive, and pass that exact ZIP to preview and submission.
5. Send metadata flags on `create` or the explicit metadata-sync operation only. Verify omitted fields survive ordinary `update` before claiming that behavior.
6. Never expose session material, access passwords, or unreviewed preview URLs in repository records or logs.
