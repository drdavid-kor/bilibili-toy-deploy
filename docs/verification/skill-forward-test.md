# Skill existing project forward test

Date: 2026-10-28. Evaluator: a separate implementation agent that did not author `skills/toy-github/SKILL.md`. This was a local release-candidate test in an isolated temporary directory. It did not install a published Skill, use a GitHub account, call the Toy platform, or involve an independent human tester.

## Realistic request and starting project

> 用 toy-github 将当前 Vite React 网页适配 Toy 并接入发布，保留现有部署。

The starting project was a temporary copy of `examples/react/`, with `toy.config.json` removed and `vite.config.js` reset to `base: '/'`, a common root-hosted frontend setting. It contained working `#en` and `#zh` hash navigation and an existing `.github/workflows/test.yml`. Generated `node_modules/` and `dist/` were excluded from the copy. This is a controlled sample, not evidence that an arbitrary React app works unchanged.

## Actions following the Skill

The evaluator read `skills/toy-github/SKILL.md` and `references/existing-project.md`, inspected the project, changed Vite's base to `'./'`, wrote `toy.config.json` with slug `existing-react-toy` and output `dist`, and copied the release-candidate `examples/workflows/toy.yml` into `.github/workflows/toy.yml`. The existing workflow and React application source were left byte-for-byte unchanged.

## Observed results

| Check | Result |
| --- | --- |
| `npm ci` in the adapted project | Exit 0 |
| `npm run build` | Exit 0; produced `dist/index.html` |
| Vendored Toy doctor with `--slug existing-react-toy --require-root-index --json` | Exit 0, 0 findings |
| Local HTTP server serving the output at `/toy/existing-react-toy/` | `index.html`, JavaScript and CSS each returned HTTP 200 |
| Built HTML resource paths | Two `./assets/` references, both resolved under the Toy subpath |
| Existing workflow | Content hash unchanged |
| Hash route source | Content hash unchanged; actual browser navigation was not exercised |
| New workflow | References `drdavid-kor/bilibili-toy-deploy@v0.1.0-beta.1` consistently |
| Generated dependencies in initial copy | None |

The work tested local adaptation and packaging only. It does not prove the remote Action tag exists, that GitHub-hosted authentication works, that a Toy preview loads in a browser, or that Bilibili accepts review submission. Those require the public installation and hosted-runner checks. The project plan's separate non-author **human** usability test is also still outstanding.

## Scaffold follow-up

Local template builds left `node_modules/` and `dist/` in the template source. `scripts/scaffold.py` now ignores these generated directories when copying a new starter; `tests/test_scaffold.py` verifies neither directory appears in the generated project. Generated folders should still be removed from the release checkout before tagging.
