# GitHub Actions 的 Toy 登录配置

Toy CLI 使用浏览器完成 B 站 OAuth 登录。公开安装说明只介绍 `toy login` 和会话过期后重新登录；本项目使用本地会话令牌在 GitHub 托管 Runner 中登录，属于实验性兼容路径。功能发布前须在干净的托管 Runner 上验证，不能把“本机能用”当作已经通过。[官方安装与登录说明](https://github.com/bilibili/toy/blob/main/skills/toy/references/installation.md)

## 前提

你需要有 Toy 发布资格、能管理目标 GitHub 仓库的 Actions Secret，并在本机安装官方 `toy` CLI 与 GitHub CLI `gh`。发布工作流使用 `TOY_SESSION_TOKEN` Secret；该值相当于能操作你的 Toy 的登录凭据。请只给受信任的发布工作流使用。PR 工作流不会读取该 Secret。

## 初次配置

1. 本机执行 `toy login`，在浏览器完成 B 站授权。
2. 执行 `toy whoami --json` 核对当前账号。此命令只显示账号信息，不应显示会话令牌。
3. 执行 `gh auth status`，确认 GitHub CLI 登录的是可以管理目标仓库的账号。
4. 从本项目仓库运行以下命令，其中 `OWNER/REPO` 是**你的网页项目仓库**：

   ```bash
   python3 scripts/set_secret.py --repo OWNER/REPO
   ```

   脚本默认读取本机 `~/.toy/session.json` 的 `session_token`，通过标准输入交给 `gh secret set`，不把令牌放入命令行参数、日志或项目文件。会话文件在其他位置时，添加 `--session-file /absolute/path/session.json`。脚本只接受含有 `session_token` 字符串字段的 JSON。

5. 在 GitHub 仓库的 Actions Secret 列表确认存在 `TOY_SESSION_TOKEN`。GitHub 不允许回读其明文，也不需要把它复制到 issue、聊天或 README。
6. 运行一次手动预览，核对工作流显示的账号和 Toy 目标。随后再使用主分支预览或 Release 提审。

如果脚本报告找不到文件，先确定本机 CLI 的会话位置；不要直接把完整会话文件上传到 GitHub。若当前 CLI 的会话格式没有 `session_token` 字段，停止并查看当前版本的认证说明，不要猜测或粘贴未知字段。

## 过期与更换

工作流报告会话失效时，在本机重新执行 `toy login`，确认账号仍是目标 Toy 的所有者，再运行同一条 `set_secret.py` 命令覆盖旧 Secret。然后手动重试原操作。会话寿命和本地重新登录对旧会话的影响目前尚未获得官方保证，需要按实际验证记录维护。

提交结果为“待核实”时，先到 B 站检查 Toy 是否已接受请求，不要只因为工作流失败就再次提审。若身份已切换，应先核对目标 Toy 的归属和仓库保存的关联记录，不能用新账号继续更新旧账号的 Toy。

## 安全边界

Secret 只提供给 Toy 查询、预览和提交步骤。构建依赖与项目代码运行时不注入它；来自 fork 的 PR 只做构建与预检。不要在工作流中打印环境变量、调用 `set -x` 或把整个 CLI 响应无筛选地写到日志、Summary、Artifact、Deployment。GitHub 自动遮罩并不能保证所有变形后的令牌都被隐藏。[GitHub Actions 安全参考](https://docs.github.com/en/actions/reference/security/secure-use)

本机不要把 `~/.toy/session.json`、`TOY_SESSION_TOKEN` 或复制的 `.env` 文件加入项目版本控制。若令牌疑似泄露，在 B 站重新登录或登出以更换会话，并立即更新或删除 GitHub Secret；旧令牌的失效行为应以平台实际结果为准。
