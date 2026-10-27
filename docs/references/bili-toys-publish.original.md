# GitHub → 哔哩哔哩 Toy 发布插件

Idealizer · 2026-10-27 · 调研报告 + 实施方案 + 问题清单

## TL;DR

  * **可以做，而且不用逆向。** B站官方已发布 `toy` CLI（Go 写的 cobra 二进制，本机实测为 v0.6.4，2026-10-20 构建），有 `create / update / mylist / stats / history / video` 等命令，支持 `--json`，也能在非交互环境里加 `--yes` 提交审核。GitHub Action 只要包一层这个 CLI 就行。
  * **没有公开的 HTTP 发布 API 文档。** open.bilibili.com 上没有 Toy 上传接口的文档。CLI 背后走的是服务端 OAuth 代理（路径形如 `/oauth/preview`、`/oauth/mylist`）。不要直接调这些内部接口，只调 CLI。
  * **最大的卡点是 CI 里怎么登录。** 官方的登录方式只有 `toy login`，要在浏览器里走 OAuth。不过二进制里有环境变量 `TOY_CLI_SESSION_TOKEN`、`TOY_HOME`、`TOY_CLI_SERVER`、`TOY_NO_UPDATE_CHECK`，很可能可以把 session 注入成 GitHub Secret 来用。但这些都**没有文档** ，session 能活多久也不知道，需要实测，最好再找官方确认。
  * **每次更新都要过审核。** 流程是上传 → preview_url →（加 `--yes`）提交审核 → 安全扫描和内容审核 → 上线。所以只能做到"每次 push 自动提审"，做不到 Cloudflare 那种秒级上线。
  * **平台还在邀请制内测。** 2026 年 6 月开始内测；上线一个多月时 UP 主已上传 300+ 件作品，累计体验 850 万次以上。开发者小站上每天都有新的入驻申请。目标用户是会写代码的 UP 主和 vibe coder，人数不多但在快速增长。
  * **建议：** MVP 做一个 composite GitHub Action，`bilibili-toy-deploy`：装 CLI → 跑 toy_doctor 预检 → `toy update <id> dist --json` → 把 preview_url 写进 PR 评论或 Job Summary → main 分支或 tag 触发时加 `--yes` 提审。工作量大约 2–4 人日。



## 一、调研报告

### 1\. Toy 是什么

  * Toy 是 B 站的互动内容发布平台。它把静态 HTML、小游戏、测试、工具、生成器等发布成站内链接，用户点开就能玩，还能挂到视频、动态和评论区。[bilibili.com/toy/intro](https://www.bilibili.com/toy/intro)
  * 官方介绍的发布流程：在管理端上传文件，填写名称、简介、封面和访问地址，提交后经过安全扫描和内容审核，通过就能拿到链接。平台本身也提供"更新"能力。目前发布权限只对受邀的 UP 主逐步开放。
  * 2026 年 7 月 8 日内测招募：支持"将本地制作的静态HTML及相关代码，快速发布成可访问的B站链接"。[B站动态](https://www.bilibili.com/opus/1210067990129672211)
  * 数据：6 月开始内测，一个多月后 UP 主已上传 300+ 件作品，体验量超过 850 万次；百大 UP 主"火山哥哥"已经做了 30 多款。[观察者网 2026-07-09](https://www.guancha.cn/economy/2026_07_09_823132.shtml)
  * 社区：Toy 开发者小站有 FAQ（更新到 2026-10-23）、赛事和大量入驻申请。[bilibili.com/bubble/home/86](https://www.bilibili.com/bubble/home/86)



### 2\. 官方工具链（重点）

  * **Agent Skill 仓库** [github.com/bilibili/toy](https://github.com/bilibili/toy)（MIT，创建于 2026-07-08）。安装命令是 `npx skills add bilibili/toy`。仓库里有 SKILL.md、installation.md、error-codes.md、content-checklist.md，以及零依赖的预检脚本 `scripts/toy_doctor.py`。
  * **CLI 安装** ：`curl -fsSL https://boss.hdslb.com/toy-cli/toy/install.sh | bash`，Windows 用 install.ps1。可以通过环境变量 `VERSION` 锁版本，用 `BIN_DIR` 指定安装目录；`toy upgrade` 带 sha256 校验。我已在 Linux 上实测安装成功。
  * **命令** （来自 `toy --help-json` 实测）： 
    * `create`，参数有 access-password, activity, category, icon, poster, slug, theme, title, visibility, watermark, yes
    * `update`，参数同上但没有 slug，因为 slug 发布后不能改
    * 其余命令：mylist, stats, history, video (bind/unbind/list/mine), whoami, login, logout, shared-storage, upgrade
    * 全局参数 `--json`：输出 JSON，不做交互确认，要提交必须显式加 `--yes`
  * **两段式发布** ：不加 `--yes` 时只上传并返回 `{"preview_url"}`；加了 `--yes` 才提交审核，返回 `{id,status,preview_url}`。如果只改元信息、不带包体，会直接提审。
  * **硬限制** ： 
    * 入口 index.html 解压后不能超过 1MB，否则报错 307000，预览也会被拦
    * 单个 HTML 达到 12MB 会出 WARN
    * 页面跑在 `/toy/<slug>/` 子路径下，用绝对路径引用资源会白屏或 404
    * 只放行白名单里的扩展名，其他文件会被丢掉（[Pygame Studio 文档](https://pygamestudio.com/platform/bilibili_toy/)）
    * 上传超时 60 秒
    * 云存储和排行榜有共享额度，超限报 307044，阈值不公开
  * **认证** ：服务端 OAuth，session 失效时报 307001 或 307029，要重新 `toy login`。官方没有提供 app key/secret 或 CI token 的方案。
  * **运行时 SDK** （页面内的 `window.toy`，和发布无关）：社区有类型封装 [imba97/bilibili-toy](https://github.com/imba97/bilibili-toy)（npm 包 bilibili-toy）。



### 3\. 类比与参考

  * **Cloudflare** Pages/Workers Git 集成和 wrangler-action：用 API Token 当 Secret，每个 PR 出预览、main 分支直接上线。Toy 能对上"预览 + 上线"这套模型，但**多了一道审核** 。
  * **微信 miniprogram-ci** ：用后台下载的上传密钥加 IP 白名单，upload 之后提审仍要人工操作。和 Toy 最像，差别是 Toy 目前没有官方 CI 密钥。
  * **抖音小游戏** ：有开发者工具 CLI，也是上传加审核。
  * **itch.io butler** ：用 API key 做增量推送，不需要审核。
  * **biliup** （B站视频上传）：用 cookie 或扫码拿到的登录态做无人值守上传，社区长期这么用。可以参考，但它属于非官方登录态，有风险。



### 4\. 用户与市场

  * 核心用户是用 Vite、React 或 AI 做网页小游戏和工具、并且频繁迭代的 UP 主或小团队。还有一类潜在用户是借 Toy 引流的独立开发者，David 就是。
  * 需求信号：官方自己做了 CLI 和 Agent Skill，说明官方鼓励用工具发布；目前没找到现成的 GitHub Action 或 GitHub App，市场是空白。
  * 局限：规模小（几百到几千个开发者），而且还在邀请制阶段；官方也随时可能自己出 CI 方案。它更适合做成开源工具来提升个人影响力，不太适合当商业产品。



## 二、实施方案

### 架构选择

  1. **A. Composite GitHub Action（MVP，推荐）** ：`uses: drdavid-kor/bilibili-toy-deploy@v1`。用户自己的 Runner 装 CLI，session 存在用户自己的 Secret 里，我们不碰任何凭据。
  2. **B. GitHub App + Cloudflare Worker** （类似 Cloudflare 的一键 Git 集成）：Webhook 打到 Worker，Worker 调起构建（CF 没法跑 Go 二进制，要另配 Runner 或 Container），再回写 Check Run。这样要替用户托管 B 站登录态，合规和安全风险都高。**只有官方开放 CI token 或 API 之后再考虑。**
  3. **C. 本地 git hook / npm 脚本** ：最简单，作为文档里的备选方案。



### 流水线（方案 A）
    
    
    on: pull_request / push main / release
    1 checkout → setup-node → build（用户自定义）→ dist/
    2 安装 toy（锁定 VERSION，TOY_NO_UPDATE_CHECK=1，缓存二进制）
    3 python toy_doctor.py dist   # ERROR 就失败，WARN 写进 Summary
    4 注入 session：Secret TOY_SESSION → TOY_CLI_SESSION_TOKEN 或 TOY_HOME（待验证）
    5 PR：toy update $TOY_ID dist --json → preview_url 写进 PR 评论或 Summary
    6 main/tag：toy update $TOY_ID dist --json --yes → {id,status} 写进 Summary 和 Deployment
    7 （可选）定时任务轮询 mylist 的 status，审核通过或驳回时更新 Deployment 状态 / 发通知
    8 遇到 307001/307029 时明确报"session 过期，请本地 toy login 后更新 Secret"
    

  * **Secrets** ：只存在用户仓库的 Secret 里，用 GitHub Environment 加保护规则；绝不 echo，用 `::add-mask::` 遮掉。
  * **版本标记** ：Toy 没有显式版本号，把 commit sha 和 tag 写进 Job Summary；如果要在页面上显示，可以注入 meta 标签或 version.json。
  * **首次创建** ：不做自动 create。首发由用户在本地 `toy create`，slug 定下来之后只用 update，避免误建新的 Toy。



### 分期与工作量

  * **P0 验证（0.5 天）** ：在本地 login 后找到 session 存在哪里，验证 TOY_CLI_SESSION_TOKEN 能不能在干净的 Runner 上用、多久过期。同时在开发者小站或 FAQ 问官方，CI 场景是否允许、怎么做。
  * **P1 MVP（2–3 天）** ：Action、README、示例仓库（Vite），发布到 Marketplace。
  * **P2（2–3 天）** ：审核状态轮询、PR 评论机器人、monorepo 多 Toy 矩阵发布、`toy.config` 元信息同步（标题和封面改动直接提审）。
  * **P3** ：官方开放 API 后再做 GitHub App 和托管面板。



### 风险

  * **认证** ：session 注入没有文档，可能随时失效，也可能违反创作者协议。一定先问官方，不要逆向内部接口。
  * **审核延迟** ：频繁提审可能拖慢审核、被限流，甚至影响账号。所以默认只在 release 或 tag 时提审，push 只出预览。
  * **CLI 变化快** ：Action 要锁版本，参数一律从 `--help-json` 动态校验。
  * **网络** ：GitHub 海外 Runner 访问 B 站的上传接口，可能出现 60 秒超时，需要重试，必要时用 self-hosted 国内 Runner。
  * **官方竞争** ：官方可能自己出 Action。应对是保持轻量，做"官方 CLI 的薄封装"。



## 三、问题清单（grill-me）

逐条回答。回"是"即采纳推荐答案。

  1. **你自己现在有 Toy 发布资格吗？** 有
  2. **做这个的首要目的是什么？** 自用、开源换影响力与潜在官方合作机会
  3. **形态是 GitHub Action 还是 GitHub App？** Action
  4. **CI 登录要不要依赖没文档的 TOY_CLI_SESSION_TOKEN？** 先按依赖作
  5. **要不要直接调 CLI 背后的 /oauth/* 接口？** 优先用 CLI
  6. **什么事件触发提审（--yes）？** 同意推荐：只在 release 或 tag 时提审；push main 和 PR 只出 preview_url。请在 readme 中明确说明使用方法
  7. **PR 预览要不要做成评论机器人？** 不用
  8. **首次 create 要不要由 Action 负责？** 要，这个项目的目的是可以完全接管从github仓库到toy的发布工作
  9. **元信息（标题、封面、分类）用代码管吗？** 允许用代码管理
  10. **预检失败（toy_doctor 报 ERROR）怎么处理？** Job 直接失败；WARN 只写进 Summary。
  11. **toy_doctor.py 怎么拿？** 运行时从 bilibili/toy 仓库拉固定 commit，拉不到则以自己仓库的备份运行。
  12. **CLI 版本策略？** Action 输入 `toy-version`，默认锁一个实测过的版本，并设置 TOY_NO_UPDATE_CHECK=1。
  13. **审核结果要不要回传？** 用 schedule workflow 轮询 mylist 的 status，更新 GitHub Deployment 状态。
  14. **Runner 网络问题怎么办？** 默认用 ubuntu-latest，上传失败时指数退避重试 3 次；文档里写明 self-hosted 方案。
  15. **要不要支持 monorepo 多 Toy？** MVP 只支持单个 Toy。
  16. **要不要做 Cloudflare Worker 中继？** MVP 不做
  17. **仓库叫什么、用什么协议？** `drdavid-kor/bilibili-toy-deploy`，MIT，README 中英双语。


