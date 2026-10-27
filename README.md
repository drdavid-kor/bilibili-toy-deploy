# bilibili-toy-deploy

把 GitHub 上的静态网页项目接入哔哩哔哩 Toy。这个仓库提供 GitHub Action、纯 HTML 与 Vite 起点、已有项目接入示例，以及帮助编程助手完成适配的 `toy-github` Skill。它调用 B 站官方 `toy` CLI；B 站接受提审后仍需等待平台审核。

**测试版范围：**纯 HTML/CSS/JS 和 Vite（含 React、Vue），一个仓库对应一个 Toy。示例工作流固定引用 `drdavid-kor/bilibili-toy-deploy@v0.1.0-beta.1`。请先确认该标签已经公开发布；标签不存在时，示例不能在其他仓库运行。托管 Runner 的认证和真实 Toy 发布验收状态以[验证记录](docs/verification/upstream-contract.md)及 GitHub Actions 运行结果为准，不以源码存在代替验证。

## 选择上手路径

| 你的起点 | 从这里开始 | 得到什么 |
| --- | --- | --- |
| 想新建一个 Toy 网页 | [从零创建指南](docs/quickstart-new.md) | 一个纯 HTML 或 Vite 最小项目、配置文件和发布工作流 |
| 已有网页前端项目 | [已有项目接入指南](docs/quickstart-existing.md) | 保留现有项目，适配 Toy 子路径并接入发布工作流 |

已经有 Toy 的开发者可填入其 ID；若没有 ID，Action 会在当前 B 站账号下完整查询 slug，唯一匹配时自动接管。查询失败或结果不唯一时停止，不直接创建第二个 Toy。[配置规则](docs/configuration.md)

## 从零创建：最短路径

先从 GitHub Releases 下载已发布的 `v0.1.0-beta.1` 源码并解压。在解压目录运行下面的命令，把目录、slug 和标题换成自己的；脚手架会复制与该版本匹配的工作流：

```bash
python3 scripts/scaffold.py --template html --destination ./my-toy --slug my-toy --title "My Toy"
```

Vite 项目把 `html` 改为 `vite`。之后在 GitHub 建空仓库，在本机完成 `toy login` 和 `gh auth login`，再从下载的本项目目录运行 `python3 scripts/set_secret.py --repo OWNER/REPOSITORY`。它把本机 Toy 会话设置为该仓库的 Actions Secret `TOY_SESSION_TOKEN`，不会打印会话值。[认证配置与更新](docs/authentication.md)

推送新项目的主分支后，到 Actions 页打开预览。检查真实页面，再为**同一提交**发布 GitHub Release；工作流会复用该预览包并提交审核。只推送 tag 不会提审。完整的建仓、推送和页面检查步骤在[从零创建指南](docs/quickstart-new.md)。

## 已有项目：接入方式

从同一已发布版本复制 `examples/workflows/toy.yml` 到项目的 `.github/workflows/`，按项目现有命令修改构建步骤，并填写仓库根目录的 `toy.config.json`。纯 HTML 产物必须有根目录 `index.html`；Vite 项目可参考 [`examples/react`](examples/react/README.md) 和 [`examples/vue`](examples/vue/README.md)。Toy 页面位于 `/toy/<slug>/`，请检查资源路径和路由。Action 接收已构建目录，不替项目猜构建命令。[已有项目接入指南](docs/quickstart-existing.md)

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

公开仓库及标签可访问后，使用以下命令安装；首次公开发布时还需验证目标编程助手能发现该 Skill：

```bash
npx skills add drdavid-kor/bilibili-toy-deploy --skill toy-github
```

可对编程助手说：“用 `toy-github` 在空目录创建一个 Vite Toy 项目并接入 GitHub 发布”，或“用 `toy-github` 检查并适配当前项目，保留原有部署流程”。Skill 会处理常规代码与工作流修改；涉及后端迁移、登录替换或存储重做时会先说明影响，待你决定。它不能代替你的 Toy 发布资格和真实页面验收。[Skill 入口](skills/toy-github/SKILL.md)

## 开发与来源

本项目使用 Python 标准库实现 Action 逻辑，发布时下载并校验固定版本的官方 CLI。运行本地测试：

```bash
python3 -m unittest discover -s tests -v
```

[开发方案](docs/development-plan.md)记录了需求与验收标准；[上游 CLI 契约记录](docs/verification/upstream-contract.md)列出已核对的版本和仍需真实运行验证的行为；[原始调研](docs/references/bili-toys-publish.original.md)仅作背景。仓库代码使用 [MIT 许可](LICENSE)，随附的官方预检脚本归属及来源见 `vendor/`。

## English

Connect a static GitHub web project to Bilibili Toy with an Action, HTML and Vite starters, React/Vue examples, and a `toy-github` onboarding skill. The Action wraps the official `toy` CLI. “Submitted for review” means Bilibili accepted the request; it does not mean the version is live.

The beta supports plain HTML/CSS/JavaScript and Vite, including React and Vue, with one Toy per repository. The example workflow pins `drdavid-kor/bilibili-toy-deploy@v0.1.0-beta.1`. **Check that this tag is publicly available before using the example in another repository.** Current verification evidence is in the [upstream contract record](docs/verification/upstream-contract.md); source code alone does not establish hosted-runner or live Toy acceptance.

### Choose a path

| Starting point | Guide | Result |
| --- | --- | --- |
| New Toy site | [Start a new project](docs/quickstart-new.md) | Minimal HTML or Vite site, config, and workflow |
| Existing frontend | [Adapt an existing project](docs/quickstart-existing.md) | Toy-compatible paths and a publishing workflow without replacing the application |

For a new site, download the published `v0.1.0-beta.1` source archive and run this from its extracted directory:

```bash
python3 scripts/scaffold.py --template html --destination ./my-toy --slug my-toy --title "My Toy"
```

Choose `--template vite` for a Vite starter. Create an empty GitHub repository, run the official `toy login` and `gh auth login` locally, then run `python3 scripts/set_secret.py --repo OWNER/REPOSITORY` from this release checkout. It stores the Toy session in the repository's `TOY_SESSION_TOKEN` Actions Secret without printing the value. See [authentication](docs/authentication.md) for expiry and replacement.

Push the new project's default branch and inspect the Actions preview. Publish a GitHub Release pointing to **that same commit** to submit the previewed package for review. A tag push alone does not submit. For an existing site, copy the matching `examples/workflows/toy.yml`, set an explicit build command and output directory in `toy.config.json`, and follow the [adaptation guide](docs/quickstart-existing.md). The Action does not auto-detect a build system.

PRs only build and check. Default-branch pushes generate previews. Published Releases reuse the matching preview artifact and submit it. Manual operations are `preview`, `submit`, `override`, `sync-metadata`, and `resolve-unknown`. An override rebuilds the selected Release commit and submits directly after precheck. Unknown write outcomes require inspection on Bilibili before manual reconciliation; they are never retried automatically. See [configuration](docs/configuration.md) and [troubleshooting](docs/troubleshooting.md).

The Action's `expose-preview` input defaults to `false` and withholds the preview URL. The example workflow explicitly sets it to `true` for a clickable job-summary link. In a public repository, readers may obtain that link and the site package from workflow artifacts. Do not include secrets or unshared material in the package.

After the public release and installation check, install the onboarding skill with:

```bash
npx skills add drdavid-kor/bilibili-toy-deploy --skill toy-github
```

Ask your coding assistant to “use `toy-github` to create a Vite Toy project and connect the GitHub Action” or “adapt this existing frontend for Toy while keeping its other deployment.” The skill can make ordinary code and workflow changes. It pauses for your decision when backend, login, or storage behavior must change. [Skill entrypoint](skills/toy-github/SKILL.md)

Run local tests with `python3 -m unittest discover -s tests -v`. The [plan](docs/development-plan.md), [CLI contract record](docs/verification/upstream-contract.md), and [MIT license](LICENSE) provide implementation context.
