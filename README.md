# bilibili-toy-deploy

把 GitHub 上的静态网页项目接入哔哩哔哩 Toy。这个仓库提供 GitHub Action、纯 HTML 与 Vite 起点、已有项目接入示例，以及帮助编程助手完成适配的 `toy-github` Skill。它调用 B 站官方 `toy` CLI；B 站接受提审后仍需等待平台审核。

**测试版范围：**纯 HTML/CSS/JS 和 Vite（含 React、Vue），一个仓库对应一个 Toy。当前示例工作流固定引用 [`v0.1.0-beta.2`](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.2)。外部仓库已用 beta.1 完成新建 Vite 路径；beta.2 和本人试用的状态见[验收记录](docs/verification/acceptance.md)。

## 复制给编程助手

```text
请把我正在处理的网页项目接入哔哩哔哩 Toy；如果当前目录是空的，就从最小可运行项目开始。
先阅读当前工作区和 AGENTS.md、现有构建与部署方式，
再查看 https://github.com/drdavid-kor/bilibili-toy-deploy 的最新已发布测试版文档和 toy-github Skill。
可用时优先使用 Skill，否则按同版本指南执行。
已有纯 HTML 或 Vite（含 React/Vue）项目请做最小适配，保留原有功能、未提交改动和部署流程；
空目录则建立模板，业务方向不明确时只问完成项目所必需的问题。
填写真实构建命令与输出目录，修好 Toy 子路径下的资源和路由，
准备封面、图标、toy.config.json 与同版本 GitHub 工作流。
先完成本地构建、静态预检和必要的页面检查；在你有权限时，连接我自己的 GitHub 仓库、
推送主分支，打开并核验真实 Toy 预览。
登录只在本机用官方 toy login，并用发行版的 set_secret.py 写入 GitHub Secret；
缺少账号或权限时告诉我具体操作，不索要或输出令牌。
只有在我明确要求提交审核时，才为已预览的同一提交发布普通 GitHub Release 并复用那份预览包；
缺包时先补预览，手动 override 只能经我明确指定，不能暗中提审。
若必须重做后端、登录或存储，先说明影响并等我决定。
最后交付改了什么、验证结果和运行链接、以后如何更新、实际阻碍；
“已提交审核”不能写成“已上线”。
```

## 选择上手路径

| 你的起点 | 从这里开始 | 得到什么 |
| --- | --- | --- |
| 想新建一个 Toy 网页 | [从零创建指南](docs/quickstart-new.md) | 一个纯 HTML 或 Vite 最小项目、配置文件和发布工作流 |
| 已有网页前端项目 | [已有项目接入指南](docs/quickstart-existing.md) | 保留现有项目，适配 Toy 子路径并接入发布工作流 |

已经有 Toy 的开发者可填入其 ID；若没有 ID，Action 会在当前 B 站账号下完整查询 slug，唯一匹配时自动接管。查询失败或结果不唯一时停止，不直接创建第二个 Toy。[配置规则](docs/configuration.md)

## 从零创建：最短路径

先从 [v0.1.0-beta.2 发布页](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.2)下载源码并解压。在解压目录运行下面的命令，把目录、slug 和标题换成自己的；脚手架会复制与该版本匹配的工作流：

```bash
python3 scripts/scaffold.py --template html --destination ./my-toy --slug my-toy --title "My Toy"
```

Vite 项目把 `html` 改为 `vite`。两个起点都自带 `toy-assets/poster.png` 和 `toy-assets/icon.png`，首次创建无需先制作图片；提审前应按作品内容换成自己的封面与图标。之后在 GitHub 建空仓库，在本机完成 `toy login` 和 `gh auth login`，再从下载的本项目目录运行 `python3 scripts/set_secret.py --repo OWNER/REPOSITORY`。它把本机 Toy 会话设置为该仓库的 Actions Secret `TOY_SESSION_TOKEN`，不会打印会话值。[认证配置与更新](docs/authentication.md)

推送新项目的主分支后，到 Actions 页打开预览。检查真实页面，再为**同一提交**发布 GitHub Release；工作流会复用该预览包并提交审核。只推送 tag 不会提审。完整的建仓、推送和页面检查步骤在[从零创建指南](docs/quickstart-new.md)。

## 已有项目：接入方式

从同一已发布版本复制 `examples/workflows/toy.yml` 到项目的 `.github/workflows/`，按项目现有命令修改构建步骤，并填写仓库根目录的 `toy.config.json`。若这个仓库将**首次创建** Toy，也要提供 `create.poster` 与 `create.icon` 指向的图片：可以先复制 `templates/html/toy-assets/` 中的占位图，再替换为自己的封面与图标。已有 Toy 接管后，普通内容更新会保留平台现有图片。纯 HTML 产物必须有根目录 `index.html`；Vite 项目可参考 [`examples/react`](examples/react/README.md) 和 [`examples/vue`](examples/vue/README.md)。Toy 页面位于 `/toy/<slug>/`，请检查资源路径和路由。Action 接收已构建目录，不替项目猜构建命令。[已有项目接入指南](docs/quickstart-existing.md)

## 发布行为

| 事件 | 行为 |
| --- | --- |
| PR | 构建与静态预检，不读取 Toy Secret，不上传 Toy |
| 默认分支 push | 构建、预检、生成 Toy 预览，保存对应构建包 |
| 发布 GitHub Release | 取该提交已预览的同一构建包，创建或更新 Toy 并提审 |
| 手动 `preview` | 对默认分支历史中的指定提交生成预览 |
| 手动 `submit` | 对指定的已发布 Release 复用预览包提审 |
| 手动 `override` | 对指定 Release 重新构建、预检并直接提审，明确记录覆盖 |
| 手动 `sync-metadata` | 只同步配置中显式填写的元信息并提审 |
| 手动 `resolve-unknown` | 在 B 站核实后记录不确定写入的结果，不再次发送请求 |

工作流以“已提交审核”为成功边界；它不声明该版本已经上线。若缺少对应预览包，常规 Release 提审会停止。网络中断后结果不明时不会自动重提。查看[配置规则](docs/configuration.md)和[故障排查](docs/troubleshooting.md)了解恢复入口。

**预览可见性：**Action 的 `expose-preview` 默认是 `false`，不会输出预览 URL。示例工作流明确设置为 `true`，以便从运行 Summary 打开页面。公开仓库的读者可能看到该链接及工作流 Artifact 中的网页包；预览链接可让持有者访问未提审内容。只将愿意分享的内容放进此示例流程，不要把凭据或敏感文件打进网页包。

## 用 Skill 接入

以下命令已在 Codex 上完成公开安装验证：

```bash
npx --yes skills@latest add drdavid-kor/bilibili-toy-deploy --skill toy-github --agent codex --yes --copy --json
```

可对编程助手说：“用 `toy-github` 在空目录创建一个 Vite Toy 项目并接入 GitHub 发布”，或“用 `toy-github` 检查并适配当前项目，保留原有部署流程”。安装版 Skill 已由独立实现代理完成一次新 Vite 项目的本地构建、预检及子路径访问测试；这不等于真人试用或平台提审。Skill 会处理常规代码与工作流修改；涉及后端迁移、登录替换或存储重做时会先说明影响，待你决定。它不能代替你的 Toy 发布资格和真实页面验收。[Skill 入口](skills/toy-github/SKILL.md) · [本人试用指南](docs/verification/user-trial.md)

## 开发与来源

本项目使用 Python 标准库实现 Action 逻辑，发布时下载并校验固定版本的官方 CLI。运行本地测试：

```bash
python3 -m unittest discover -s tests -v
```

[开发方案](docs/development-plan.md)记录了需求与验收标准；[验收记录](docs/verification/acceptance.md)区分已完成与待验证项目；[上游 CLI 契约记录](docs/verification/upstream-contract.md)列出已核对的版本；[原始调研](docs/references/bili-toys-publish.original.md)仅作背景。仓库代码使用 [MIT 许可](LICENSE)，随附的官方预检脚本归属及来源见 `vendor/`。

## English

Connect a static GitHub web project to Bilibili Toy with an Action, HTML and Vite starters, React/Vue examples, and a `toy-github` onboarding skill. The Action wraps the official `toy` CLI. “Submitted for review” means Bilibili accepted the request; it does not mean the version is live.

The beta supports plain HTML/CSS/JavaScript and Vite, including React and Vue, with one Toy per repository. The current example workflow pins [`v0.1.0-beta.2`](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.2). A separate repository completed the new Vite path with beta.1; see the [acceptance record](docs/verification/acceptance.md) for beta.2 and the pending human trial.

### Copy into your coding agent

```text
Connect the web project I am working on to Bilibili Toy; if this directory is empty,
start from a minimal working project. First inspect the workspace, AGENTS.md,
and existing build and deployment setup. Then read the latest published beta
documentation and toy-github skill at https://github.com/drdavid-kor/bilibili-toy-deploy.
Use the skill when available; otherwise follow the matching release guide.
For an existing plain HTML or Vite project (including React/Vue), make the smallest
practical changes and preserve its features, uncommitted work, and other deployments.
For an empty directory, scaffold the starter and ask only for essential missing product details.
Set the real build command and output directory, fix assets and routing under the Toy subpath,
and prepare poster/icon artwork, toy.config.json, and the workflow from the same release.
Build, run the static precheck, and inspect the relevant pages locally. If you have permission,
connect my own GitHub repository, push the default branch, and open and verify a real Toy preview.
Authenticate only through the official toy login on my computer and use the release's
set_secret.py to set the GitHub Secret. If account access or permissions are missing,
give me the exact steps without asking for or printing tokens.
Submit for review only when I explicitly ask: publish a normal GitHub Release for the same
previewed commit and reuse that preview package. If the package is missing, preview that commit first.
Use manual override only when I explicitly request it; never submit silently.
If backend, login, or storage must be redesigned, explain the impact and wait for my decision.
Finish with the changes made, verification and run links, how I update later, and any real blocker.
Never describe “submitted for review” as “live.”
```

### Choose a path

| Starting point | Guide | Result |
| --- | --- | --- |
| New Toy site | [Start a new project](docs/quickstart-new.md) | Minimal HTML or Vite site, config, and workflow |
| Existing frontend | [Adapt an existing project](docs/quickstart-existing.md) | Toy-compatible paths and a publishing workflow without replacing the application |

For a new site, download the `v0.1.0-beta.2` source archive and run this from its extracted directory:

```bash
python3 scripts/scaffold.py --template html --destination ./my-toy --slug my-toy --title "My Toy"
```

Choose `--template vite` for a Vite starter. Both starters include placeholder `toy-assets/poster.png` and `toy-assets/icon.png`, so you can complete first-time setup without making images first; replace them with artwork for your Toy before review submission. Create an empty GitHub repository, run the official `toy login` and `gh auth login` locally, then run `python3 scripts/set_secret.py --repo OWNER/REPOSITORY` from this release checkout. It stores the Toy session in the repository's `TOY_SESSION_TOKEN` Actions Secret without printing the value. See [authentication](docs/authentication.md) for expiry and replacement.

Push the new project's default branch and inspect the Actions preview. Publish a GitHub Release pointing to **that same commit** to submit the previewed package for review. A tag push alone does not submit. For an existing site, copy the matching `examples/workflows/toy.yml`, set an explicit build command and output directory in `toy.config.json`, and follow the [adaptation guide](docs/quickstart-existing.md). If that site will create a new Toy, also provide `create.poster` and `create.icon`, for example by copying the starter artwork and then replacing it. The Action does not auto-detect a build system.

| Event | Action |
| --- | --- |
| Pull request | Build and static checks; no Toy upload or session secret |
| Default-branch push | Build, precheck, and Toy preview |
| Published, non-prerelease GitHub Release | Reuse that commit's preview package and submit it for review |
| Manual `preview` / `submit` | Preview a selected commit / submit a selected published Release |
| Manual `override` | Rebuild and precheck the selected Release commit, then submit directly |
| Manual `sync-metadata` / `resolve-unknown` | Submit explicit metadata fields / record a verified uncertain result without another Toy write |

Unknown write outcomes require inspection on Bilibili before manual reconciliation; they are never retried automatically. See [configuration](docs/configuration.md) and [troubleshooting](docs/troubleshooting.md).

The Action's `expose-preview` input defaults to `false` and withholds the preview URL. The example workflow explicitly sets it to `true` for a clickable job-summary link. In a public repository, readers may obtain that link and the site package from workflow artifacts. Do not include secrets or unshared material in the package.

The following Codex installation command has been tested against the public repository:

```bash
npx --yes skills@latest add drdavid-kor/bilibili-toy-deploy --skill toy-github --agent codex --yes --copy --json
```

Ask your coding assistant to “use `toy-github` to create a Vite Toy project and connect the GitHub Action” or “adapt this existing frontend for Toy while keeping its other deployment.” An independent implementation agent built and checked a new Vite starter using the installed skill; the separate human trial is pending. The skill can make ordinary code and workflow changes. It pauses for your decision when backend, login, or storage behavior must change. [Skill entrypoint](skills/toy-github/SKILL.md) · [Human trial guide](docs/verification/user-trial.md)

Run local tests with `python3 -m unittest discover -s tests -v`. The [plan](docs/development-plan.md), [acceptance record](docs/verification/acceptance.md), [CLI contract record](docs/verification/upstream-contract.md), and [MIT license](LICENSE) provide implementation context.
