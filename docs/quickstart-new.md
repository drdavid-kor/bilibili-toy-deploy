# 从零创建并发布第一个 Toy

这条路径适合已有 Toy 创作者资格、准备新建静态网页项目的开发者。完成后，你的 GitHub 仓库会在主分支生成 Toy 预览，并在发布 GitHub Release 时把同一份构建包提交 B 站审核。审核是否通过仍需到 B 站查看。

## 开始前

- 一个可发布 Toy 的 B 站账号，以及一个可创建仓库、运行 GitHub Actions 的 GitHub 账号。
- 使用 [认证说明](authentication.md)配置会话。认证属于实验性接入，具体取得方式和失效处理以该页及当前发行版为准。不要把会话填进 `toy.config.json`、Issue 或聊天。
- 选择已发布的 Action 标签，并从同一标签取得模板和工作流。不要混用不同版本的模板、配置和 Action。

## 1 建立最小项目

从 [v0.1.0-beta.2 发布页](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.2)下载并解压源码。进入解压后的目录，运行脚手架。下面的路径是示例，请把 `./my-toy`、slug 和标题改成自己的值：

```bash
python3 scripts/scaffold.py --template html --destination ./my-toy --slug my-toy --title "My Toy"
```

脚手架会在**新目录**建立纯 HTML 项目，并复制同版本的 `examples/workflows/toy.yml`。若准备使用 Vite，把 `--template html` 改成 `--template vite`。React 和 Vue 项目的接入参考同版本 `examples/react/`、`examples/vue/`。这个新目录才是你的 Toy 仓库；不要把 Action 的整个开发仓库当作作品发布。示例工作流指向 `drdavid-kor/bilibili-toy-deploy@v0.1.0-beta.2`。

模板提供可访问的首页、相对资源路径、一个能运行的构建命令，以及 `toy.config.json`。它还自带 `toy-assets/poster.png`（1200×900）和 `toy-assets/icon.png`（256×256），配置已经引用这些图片，因此首次上手不用制作素材。正式提审前请换成与作品一致的封面和图标。填写自己的 slug 和标题。首次创建默认 `link-only`。slug 是作品地址的一部分，发布后不能靠普通更新修改；请在首次提审前检查拼写。[配置说明](configuration.md)解释各字段。

脚手架已把同一发行版的示例工作流放进 `.github/workflows/`。检查其中的 Action 标签、构建命令和输出目录：纯 HTML 模板直接使用 `site/`，Vite 模板需要运行 `npm ci` 和 `npm run build` 并使用 `dist/`。工作流不应猜测项目类型。

## 2 配置 GitHub

在 GitHub 新建一个空仓库，不要勾选自动生成 README、`.gitignore` 或许可证。先在本机运行官方 `toy login` 和 `gh auth login`。仍在已下载的本项目发行版目录时，使用随发行版提供的工具设置仓库 Secret；示例中的仓库名需换成自己的：

```bash
python3 scripts/set_secret.py --repo OWNER/REPOSITORY
```

它把本机 CLI 会话写入仓库 Actions Secret `TOY_SESSION_TOKEN`，不应在终端打印会话值。具体前提和失效后更新方法见[认证说明](authentication.md)。确认仓库允许 Actions 运行；示例工作流会向临时 `GITHUB_TOKEN` 申请部署记录写权限，用于自动保存 Toy ID，无需另配长期 GitHub 令牌。

然后在刚才生成的项目目录提交并推送。将示例远端地址换成你的仓库地址：

```bash
cd my-toy
git init -b main
git add .
git commit -m "Start Toy project"
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

推送主分支后，在 GitHub 仓库的 Actions 页打开这次运行。工作流会构建项目、执行 Toy 静态预检并生成预览。主分支 push **只预览，不提审**。查看运行 Summary 中的结果并打开 Toy 页面，检查桌面和手机布局、资源加载和路由。预检通过不能代替实际页面检查。若没有生成预览，先打开失败步骤并按[故障排查](troubleshooting.md)处理，别直接发布 Release。

**公开性请在推送前确认：** 示例工作流把 Action 的 `expose-preview` 明确设为 `true`，预览链接会写进运行 Summary；公开仓库的读者也可能看到该链接和工作流 Artifact 中的网页包。预览链接可让持有者访问尚未提审的内容。只在愿意公开分享这个版本时使用该示例。独立 Action 默认 `false` 会隐藏链接，但也无法从 Summary 打开预览。

## 3 提交审核

在 GitHub 仓库的 Releases 页选择“Draft a new release”，创建版本 tag，确认 tag 指向刚才预览的**同一提交**，再选择“Publish release”。第一版示例只接受已发布的正式 Release，不处理 prerelease。发布 Release 才会触发提审；只推送 tag 不会。返回 Actions 页查看本次运行的目标 SHA、包摘要和平台响应。

默认提审复用该提交的已预览构建包。如果找不到有效包、包已过期或校验失败，工作流停止并提示为该提交重新生成预览。它不会悄悄构建主分支最新代码。你可以在手动工作流中明确选择目标 Release 并启用覆盖：此时重新构建 Release 对应提交、执行预检，再直接提审。覆盖动作和提交摘要会进入记录。

首次提审时，Action 会用当前 B 站账号和 slug 查找是否已有作品：唯一匹配则接管，完整查询确认不存在才创建。成功后自动记录 Toy ID。若查询失败或有多个匹配，它会停下让你处理。不要为了重跑而换一个 slug，以免意外产生第二个 Toy。

运行显示“已提交审核”表示 B 站接受本次申请，**不代表已经上线**。到 B 站查看审核状态和页面；审核结果不会由第一版自动同步到 GitHub。

## 4 验证下一次更新

修改页面后再次推送主分支，打开新预览，然后为该提交发布新的 Release。Action 应更新原 Toy，并保持原有标题、封面、分类和可见性。需要同步这些元信息时，使用独立的手动同步入口，不要把它们顺带写进日常内容更新。

如果任务失败，先查看[故障排查](troubleshooting.md)。尤其注意会话过期、预览包缺失、结果待核实和 Toy 关联保存失败这几类情况，它们需要不同的恢复方法。若要重试一条已有 Release，在 Actions 页手动运行工作流，选择 `submit` 并填写其 `release-tag`；需要直接重建时选择 `override`。不要在未核实“结果待核实”前使用这两个入口。

## 用 Skill 加速

Codex 用户可运行已验证的安装命令：

```bash
npx --yes skills@latest add drdavid-kor/bilibili-toy-deploy --skill toy-github --agent codex --yes --copy --json
```

然后对编程助手说：“用 toy-github 在这个空目录创建纯 HTML Toy 项目，并接入 GitHub 发布。”Skill 会建立最小项目和工作流；你仍需在 GitHub 安全地设置会话，并检查真实预览。只有一个创意时，Skill 不会自动替你完成全部业务功能。本人试用可按[简短试用指南](verification/user-trial.md)记录卡点。
