# 把已有网页项目接入 Toy

这条路径适合已有纯 HTML/CSS/JS 或 Vite 项目的开发者，包括 Vite React、Vue。完成后，现有项目会多一条 Toy 发布流程：PR 做构建与预检，主分支生成预览，GitHub Release 提交审核。

## 1 查清项目的实际构建方式

先确认入口文件、包管理器、构建命令及输出目录，并运行一次现有构建和测试。不要假定所有项目的产物都在 `dist/`。后端或服务端渲染项目需要另行判断；第一版不承诺自动迁移这些功能。

从本项目 GitHub Releases 下载并解压一个已发布版本，将其中 `examples/workflows/toy.yml` 复制到现有项目的 `.github/workflows/`。示例当前指向 `drdavid-kor/bilibili-toy-deploy@v0.1.0-beta.1`，该标签未发布前不能在其他仓库运行。将构建步骤改为项目原有命令，并把 `toy.config.json` 的 `directory` 设置为实际输出目录。保留已经使用的其他部署工作流。Action 接收**构建好的目录**，不会自动识别或修理构建命令。Action 标签、示例工作流和配置 schema 应使用同一发布版本。

## 2 让页面在 Toy 的子路径中运行

Toy 页面位于 `/toy/<slug>/`。检查首页 HTML 中的脚本、样式、图片、字体链接，以及 JavaScript 里的绝对跳转。`/assets/app.js` 这类站点根路径通常无法指向 Toy 包内资源；应使用相对路径，或在 Vite 中设置与 Toy 子路径相符的构建基路径。构建后检查**产物**，不能只查看源码。

若项目使用浏览器路由，直接刷新 `/profile` 这样的 history 路由可能没有对应静态文件。Vite React、Vue 示例展示可在静态环境下工作的 hash 路由。纯页面锚点（如 `#features`）本身应保持，不要误当路由问题删除。多页面项目需逐一检查入口和链接。动态导入、CSS `url()`、字体和 `public/` 资源也要在产物中检查。

项目若依赖自有服务器 API、现有登录系统或存储服务，请核实 Toy 环境中这些接口的访问方式、跨域限制和账号语义。不要通过删除功能或塞入模拟数据让静态检查“变绿”。需要后端迁移、登录替换或存储重做时，先确认方案再动相关代码。

## 3 指定目标 Toy

在 `toy.config.json` 填写本项目的 slug、输出目录和首次创建所需的标题等信息；凭据不写在这个文件里。若此仓库要首次创建 Toy，请同时填写 `create.poster`、`create.icon`，并把对应图片放在项目仓库里。可以先从同版本 `templates/html/toy-assets/` 复制已配置的占位封面与图标，之后换成自己的图片；不必在首次配置前自行制作。现有作品接管后，普通内容更新会保留 B 站上的封面与图标。已有 Toy 可以显式填写 ID。未填 ID 时，Action 会核对当前登录账号并按 slug 完整查询：唯一匹配就接管，零匹配才可能创建。slug 相同意味着本仓库后续会更新那个 Toy，接入前请确认对象正确。[配置说明](configuration.md)

先在本机完成官方 `toy login` 和 `gh auth login`。在下载并解压的同版本项目目录运行 `python3 scripts/set_secret.py --repo OWNER/REPOSITORY`，把示例仓库名换成自己的。工具将会话设置为 GitHub Actions Secret `TOY_SESSION_TOKEN`，不应打印会话值。前提与更新方法见[认证说明](authentication.md)。示例工作流会向临时 `GITHUB_TOKEN` 申请部署记录写权限。会话只注入发布步骤，不注入安装依赖或构建步骤，也不注入 PR 工作流。

## 4 构建、预览、提审

先在本地运行原测试、构建和 Toy 静态预检，修复 ERROR，逐条了解 WARN。检查桌面和移动端的入口、图片、字体、路由与核心交互。然后推送主分支，在 GitHub Actions 页找到本次运行：工作流生成 Toy 预览，但不会提交审核。打开预览进行实际页面检查。示例将 `expose-preview` 设为 `true`，会把可访问的预览链接写进 Summary；公开仓库的读者也可能看到链接和 Artifact 中的网页包。若内容不能公开，先改用私有仓库并确认访问权限，或改用自己的预览交付方式。把该选项改为 `false` 会隐藏链接，也无法从 Summary 打开预览。

在 GitHub Releases 页为**同一提交**发布 Release。默认提审复用预览包，显示“已提交审核”表示 B 站接受申请，不等于已经上线。如果预览包缺失或过期，先为该提交重新预览；确需跳过这一步时，在 Actions 页的手动入口明确指定 Release 并启用覆盖，工具会重新构建、预检并直接提审。

以后发布继续走主分支预览 → Release 提审。日常内容更新保留 B 站现有标题、封面、分类与可见性；单独的手动同步操作才更新仓库配置中显式填写的元信息。

## 用 Skill 加速

公开发行版发布且安装命令验证后，可运行 `npx skills add drdavid-kor/bilibili-toy-deploy --skill toy-github`。然后向编程助手提出：“检查并适配当前 Vite 项目，让它在 Toy 子路径运行，接入发布 Action，保留现有部署流程。”Skill 会检查路由、资源路径和构建产物，直接完成通常的代码修改与工作流接入。若必须迁移后端、替换登录或重做存储，它会说明影响并等待你决定。改造后仍需验证真实页面和工作流结果。

故障恢复见[故障排查](troubleshooting.md)。
