# 公开测试版验收记录

日期：2026-10-28（Asia/Shanghai）。本页逐项记录当前已观察到的结果；“通过”只覆盖列出的证据范围。工作流运行时间由 GitHub 返回 UTC，下面以运行链接为准。测试使用 `toy` CLI v0.6.4、GitHub 托管 `ubuntu-latest` 和本仓库的演示作品。预览链接和会话令牌不写入本页。

## 当前结论

[`v0.1.0-beta.3`](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.3) 已公开发布：新增安全操作摘要、预览上传前的 GitHub 记录权限检查和有限只读重试。55 个本地测试、该提交的 CI 与本仓库托管预览成功；私有 React 仓库用该标签完成同一包的预览和更新提审。无实现上下文的独立代理仅凭公开文档，在私有仓库完成纯 HTML 首次创建和第二次更新。此前公开版本也已在新建 Vite 与已有 React 仓库验证对应路径。按用户修订后的验收要求，两个不继承实现对话的 sub-agent 仅凭 README 提示词和指定场景，完成新建俄罗斯方块与真实已有项目 `muzzle-device-lab` 的真实预览、同包 Release 提审。[试用快照](prompt-only-trials.json)保留新游戏首次遇阻及恢复过程；这属于代理验证，不称为人类试用。“已提交审核”不等于新版已上线。

旧版内容更新运行曾因 CLI 成功响应不含 ID 而在 Action 中失败；平台实际接受了更新，页面显示 Revision 2，前后元信息快照相同。随后用 `resolve-unknown` 核实并恢复 Deployment，未重复发送 Toy 写请求。修复后的普通 Release 更新已在托管 Runner 成功。外部仓库故意换入无效 Secret 后，手动预览明确失败且没有提审；重新设置有效 Secret 后，后续预览和 Release 更新均成功。公开 Skill 的安装命令已重复运行并成功覆盖同源安装；独立代理按安装版完成新 Vite 项目的本地检查。2026-10-28 用户明确以两个独立 sub-agent 试用替代本人试用，修订后的要求已完成。会话实际寿命以及本地登出是否撤销旧会话尚无结论。

已发布的 beta.1 在刚创建的 Toy 仍在审核、平台列表暂缺 URL 时会安全停止预览；同一运行在列表出现 URL 后重跑成功。beta.2 已加入用可信绑定识别该作品的修复，通过本地回归、CI 与外部 React 项目的后续更新；**审核中列表再次缺 URL 的真实场景尚未重现验证**。beta.1 标签保持不变。

## Copy-Paste Prompt 独立代理试用

按用户指定，两个 sub-agent 均以不继承实现对话的方式启动，只收到 README 中文提示词、场景和相应 GitHub/Toy 操作授权。它们自行从公开 beta.3 读取 Skill、指南和工作流；提示词原文及摘要保存在[脱敏试用快照](prompt-only-trials.json)。维护者随后核对运行、提交、包摘要和仓库变更。

| 场景 | 结果与证据 |
| --- | --- |
| 新建俄罗斯方块 | [公开游戏仓库](https://github.com/drdavid-kor/bilibili-toy-blockfall)，提交 `06b4aa707636950e0d26866a2f5202b2b451f45c`；[预览 40556644747](https://github.com/drdavid-kor/bilibili-toy-blockfall/actions/runs/40556644747)和[提审 40556951838](https://github.com/drdavid-kor/bilibili-toy-blockfall/actions/runs/40556951838)成功。游戏的开始、直落得分、暂存、触屏与暂停已检查；本地 375 px 无横向溢出。Release `v0.1.0` 跳过重建，复用 Artifact `12756359669`，包摘要 `5dffb9b296608258e337d07773a86078b6811e2b6161ea73c880c09bb0892f2b`；Toy ID `48682535749632`，`override=false` |
| 适配已有 muzzle-device-lab | [原私有仓库](https://github.com/drdavid-kor/muzzle-device-lab)，提交 `215cb286a58a3af74e836006edb089d722a58032`；仅增加 Toy 工作流、配置、素材及 README，原应用源码、构建和 Cloudflare 配置未变。[预览 40556055650](https://github.com/drdavid-kor/muzzle-device-lab/actions/runs/40556055650)和[提审 40556335437](https://github.com/drdavid-kor/muzzle-device-lab/actions/runs/40556335437)成功，真实页面的 3D、装置切换、分解视图和对比表正常。Release 跳过重建，复用 Artifact `12757451650`，包摘要 `9b23338060ca11631e7b8f628fd6d853b81dab3c7979f14a71c529b6c250e7d9`；Toy ID `48681562671104`，`override=false`。私有运行日志可能无法由外部读者打开 |

实际卡点：[游戏首次 push 运行 40556350697](https://github.com/drdavid-kor/bilibili-toy-blockfall/actions/runs/40556350697)构建成功，但另一条试用刚提交的 Toy 正在审核、列表缺 URL，导致新仓库不能完整核验 slug，Action 在上传前停止。代理从公开故障排查获知这一限制；等列表出现 URL 后，为原提交手动生成 Action 预览，再发布 Release。中途另做的本机 CLI 预览不算 Action 验收。此卡点的跨项目影响及恢复方式已补入两条上手指南、README 和故障排查；未修改运行逻辑或绕过核对。

两条提审最初均返回 `auditing`。维护者于 **2026-10-27 18:08:39 UTC** 另行通过官方 CLI 查询，两个 Toy 均为 `published`，并返回[游戏正式地址](https://www.bilibili.com/toy/blockfall-drdavid/index.html)和[已有项目正式地址](https://www.bilibili.com/toy/muzzle-device-lab/index.html)。随后在浏览器打开两条正式地址，游戏首页及三维模型页面均可见。这是后续平台状态与页面证据，不改变 Action 仅以“接受提审”为成功边界的规则。

两次均复用本机已有官方登录态，通过随版脚本安全设置 Secret；未声称重新走过交互登录，也未进行人类使用研究。已有项目本次没有单独检查托管手机视口；原项目的手机测试记录不能替代这次实测。

## 关键运行与产物

| 证据 | 当前可证明的范围 |
| --- | --- |
| [托管 Runner P0 运行 40535027750](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40535027750) | CLI 安装、隔离会话认证和 GitHub 记录验证步骤成功；2026-10-27 15:50–15:51 UTC |
| [公开预发布 v0.1.0-beta.1](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.1) | 标签指向 `d6c5ca66935291bffb3fdc987720ef562e087d51`；仓库当前公开可访问。这是 Action 的预发布标签，用户的 Toy 提审流程仍要求普通已发布 Release，而非 prerelease |
| [当前预发布 v0.1.0-beta.3](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.3)、[CI 40548477078](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40548477078)、[本仓库预览 40548477069](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40548477069) | 固定提交 `340331a58a6007dbb78628932600d3ecc37be276`；55 个本地测试对应的 CI 和本仓库托管预览均成功 |
| [已发布 v0.1.0-beta.2](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.2)、[CI 40544882196](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40544882196)、[预览 40544882060](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40544882060) | 固定提交 `cc33f7563e3d2f4223eaebc7da6574e384411c7e`，42 个本地回归测试对应的 CI 与本仓库预览均成功 |
| [同一 Secret 的跨时间观察](session-observation.json) | 仓库 Secret 的创建与最后更新均为 2026-10-27 15:50:44 UTC；成功的 P0 与 beta.3 托管预览开始时间相隔 82 分 18 秒，期间未更换该仓库 Secret。仅证明这一观察窗口，不推断会话固定寿命或登出撤销行为 |
| [标签提交 CI 40541049641](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40541049641)、[预览 40541049657](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40541049657) | `d6c5ca6` 对应的 CI 与主分支预览均成功 |
| [CI 运行 40537312297](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537312297)、[40538443763](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538443763)、[40539031460](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539031460) | 三个相应提交的 CI 运行成功；证明对应版本的自动测试和构建检查通过，不等于真实平台验收 |
| [Toy 预览运行 40537312303](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537312303)、[40538443733](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538443733)、[40539031328](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539031328) | 主分支的计划、构建、预览及对应 Artifact 上传步骤完成；三次为独立托管运行 |
| [首次不带素材的 Release 运行 40537748338](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537748338) | 平台明确拒绝提审，Action 报 `307009`；对应 Deployment 状态为 `failure`，未标为成功 |
| [带素材的首次创建运行 40538681541](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538681541) | `verification-20261028-2` 对应提交的已预览包被提审接受；Toy ID `48653775407104`；提审与关联 Deployment 均为 `success` |
| [内容更新运行 40539309434](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539309434)、[元信息前后快照](metadata-retention.json) | CLI 返回 `{"status":"auditing"}` 但不含 ID；当时 Action 将运行标为失败，平台实际上接受更新，浏览器显示 Revision 2，所列标题、分类、可见性、封面和图标保持一致 |
| [修复后的普通 Release 更新 40540621027](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40540621027) | 发布事件的托管工作流与 Deployment `7364124360` 成功；验证 status-only 更新响应可按已核实的 Toy ID 记录，不推断审核最终结果 |
| [结果恢复运行 40539826963](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539826963) | 核实后将 Deployment `7363929796` 改为 `success`；记录显示没有再次向 Toy 发送写请求 |
| [元信息同步运行 40540219276](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40540219276) | 托管工作流及对应 Deployment `7364066856` 成功；这是提交审核的记录，未单独证明新版已上线 |
| [手动覆盖运行 40540210624](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40540210624) | 托管工作流及对应 Deployment `7364074156` 成功，记录为直接提审覆盖；不推断审核结果 |
| [外部仓库预览 40541670908](https://github.com/drdavid-kor/bilibili-toy-action-example/actions/runs/40541670908)、[首次提审 40542720575](https://github.com/drdavid-kor/bilibili-toy-action-example/actions/runs/40542720575)、[预览截图](consumer-vite-preview.jpg) | 私有测试仓库从公开发行版脚手架生成 Vite 项目；提交 `1ed01663f0a6ea47af8d67019e77ac236b5a2e83` 的预览与 Release 提审均成功，浏览器预览交互从 0 增至 1。Toy ID `48659928451072`；这是独立仓库测试，不是独立人类试用 |
| [外部仓库无效 Secret 运行 40542938062](https://github.com/drdavid-kor/bilibili-toy-action-example/actions/runs/40542938062)、[恢复后预览 40543078704](https://github.com/drdavid-kor/bilibili-toy-action-example/actions/runs/40543078704) | 故意把 Secret 换成无效值后手动预览失败，提示会话失效且无提审；使用已发布工具重新设置有效 Secret 后，新提交的托管预览成功。此项不能证明自然过期时间 |
| [外部仓库第二次更新 40543278017](https://github.com/drdavid-kor/bilibili-toy-action-example/actions/runs/40543278017) | `verification-v2` 对提交 `3cec8c72824397a8b8b4f21ef35d329442ff9d6a` 更新同一 Toy ID `48659928451072`；工作流与提审 Deployment `7364512372` 成功，未证明最终上线 |
| [已有 Vite React 项目首次提审 40543437543](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543437543) | 独立私有仓库从已有项目适配，提交 `9c62541f51ce91730e9d0bc5a073b0bd444030bd` 使用公开 Action 标签完成首次创建提审；Toy ID `48661048331264`。这是代理执行的外部仓库测试，不是用户本人试用 |
| [已有 React 项目 beta.2 预览 40545113514](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40545113514)、[更新提审 40545337475](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40545337475)、[脱敏快照](existing-project-runs.json) | 提交 `16bb32e24ed6d3fc97a19d2ef36dbf9f48a8780b` 的预览显示 Revision 2；`verification-v2` 跳过重建，复用 Artifact `12753200622` 提审同一 Toy `48661048331264`，状态为受理/审核中，尚未证明上线 |
| [已有 React 项目 beta.3 预览 40548819419](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40548819419)、[更新提审 40549023286](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40549023286)、[脱敏快照](beta3-regression.json) | 仅升级工作流 Action 引用；提交 `1dc6b280d09dc61ed1e0a25273609bc0208483a4` 的预览 Deployment `7365323491` 从 `in_progress` 变为 `success`。普通 Release `verification-v3` 跳过构建，复用 Artifact `12753379094`，提审 Deployment `7365351037` 成功；同一 Toy `48661048331264`、同一包摘要。所选预览和提审 Summary 含核对字段，观察到的内容没有令牌或原始 CLI 响应；这是维护者代理在私有仓库的测试，未证明最终上线 |
| [纯 HTML 文档独立代理试用](html-document-trial.json)：[首次预览 40549620460](https://github.com/drdavid-kor/bilibili-toy-html-example/actions/runs/40549620460)、[首次创建 40549961991](https://github.com/drdavid-kor/bilibili-toy-html-example/actions/runs/40549961991)、[第二次预览 40550110700](https://github.com/drdavid-kor/bilibili-toy-html-example/actions/runs/40550110700)、[更新 40550289758](https://github.com/drdavid-kor/bilibili-toy-html-example/actions/runs/40550289758) | 无实现上下文的代理仅读公开 beta.3 的 README、从零指南和认证说明，从纯 HTML 模板在私有仓库完成首次创建 Toy `48671274043392` 及第二次更新。两次 Release 均跳过重建、复用各自相同提交的预览包；桌面和手机宽度显示、初始计数交互均已核对。首次创建后的只读观察已见 `published` 和 URL，未遇审核中缺 URL；这不是人类试用，提审成功也不证明第二版已上线 |
| [隔离仓库唯一 slug 接管 40547187265](https://github.com/drdavid-kor/bilibili-toy-adoption-check/actions/runs/40547187265)、[脱敏快照](slug-adoption.json) | 无 `toy_id` 且无先前 Deployment 的仓库自动接管唯一匹配的原 Toy `48653775407104`，写入关联 `7365081757` 并生成预览 `7365082809`；未重复创建或提审，目标元信息前后相同。这是维护者隔离仓库实测，仓库已归档 |
| [单字段元信息同步 40546627089](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40546627089)、[脱敏快照](metadata-sync.json) | 独立手动 `sync-metadata` 只配置 `metadata.title`；Toy `48661048331264` 的标题变为配置值，分类、可见性、主题、水印与封面/图标 URL 摘要保持相同。Deployment `7365000574` 成功；不推断审核最终结果或审核中同步行为 |
| [beta.1 审核中缺 URL：首次尝试](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/1)、[同一运行第 2 次尝试](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/2) | 提交 `d5ea124fc326c047d046000f3300098c539085b6` 的第 1 次预览在目标核对阶段停止，没有 Toy 写入；后来平台列表有 URL，第 2 次尝试生成预览。GitHub 对该 run 的当前总状态显示成功，需按 attempt 区分 |
| 已验证的公开 Skill 安装和重复安装命令 | `npx --yes skills@latest add drdavid-kor/bilibili-toy-deploy --skill toy-github --agent codex --yes --copy --json` 安装成功；重复运行后覆盖同源安装，`SKILL.md` 字节相同。独立实现代理按安装版完成新 Vite 脚手架、构建、预检与 Toy 子路径 HTTP 200。本项没有真人或远程提审证据 |
| 本地回归测试 | beta.3 有 55 个测试通过，新增操作上下文、预览权限预检及有限只读重试；对应 CI 与外部 React 回归已成功。beta.2 对应 42 个测试通过，覆盖审核中缺 URL 的可信绑定与保守阻断，以及记录失败、分页、过期产物、fork PR 规划等分支；beta.1 为 34 个测试。本地故障注入不表示这些故障都在真实平台发生过 |
| Vue 隔离页面检查 | `examples/vue/` 的副本构建与 Toy doctor 均通过、零发现；本地 Toy 子路径的 HTML/JS/CSS 返回 HTTP 200，Chrome 中英文 hash 路由切换和计数 0→1 成功。此项不是 Toy 平台提审 |
| [预览截图](toy-preview.jpg) | 演示页面在 Toy 预览中可见，截图显示页面及一次按钮交互；截图单独不能证明各版本审核或上线状态 |
| [Skill 现有项目隔离测试](skill-forward-test.md) | 独立实现代理按 Skill 改造 Vite React 样例，本地构建、预检与 Toy 子路径 HTTP 资源请求通过；没有远程发布，也不是独立人类使用测试 |

在本仓库首次成功创建中，预览 Deployment `7363798313` 与提审 Deployment `7363830573` 记录了相同提交 `f1b6cb528caf037f8474786e47a8de690f14ff47`、相同包 SHA-256 `fc308cf8d1d3c3b9bdcaeae6c4dcb0806e3b273b28437c025c561bcbb8319b37`。关联 Deployment `7363831942` 保存了返回的 Toy ID。

外部仓库预览 Deployment `7364281567` 与提审 Deployment `7364429248` 同属提交 `1ed01663f0a6ea47af8d67019e77ac236b5a2e83`，包 SHA-256 均为 `8cb98cf95bb47dac275b4115a84fb066e557ffd3c73ee28dd50c0684849d25e9`；关联 Deployment `7364430370` 保存了 Toy ID。这次独立仓库的首次提审复用了预览包。

外部仓库第二次更新的预览 Deployment `7364488908` 与提审 Deployment `7364512372` 同属提交 `3cec8c72824397a8b8b4f21ef35d329442ff9d6a`，包 SHA-256 均为 `4e6091c1c56fe43f3500688ffaed5ef948e156d60b1962dd30deba1d4d863d82`，并且都指向同一 Toy ID。

已有 Vite React 项目的预览 Deployment `7364500931` 与首次提审 Deployment `7364535382` 同属提交 `9c62541f51ce91730e9d0bc5a073b0bd444030bd`，包 SHA-256 均为 `850e3c841e11fc134ea8ec4c08407f9772ec01faabaefc1fc67d4a84e994631b`；关联 Deployment `7364537020` 保存了新 Toy ID。

该 React 项目的 beta.2 预览 Deployment `7364784697` 与更新提审 Deployment `7364811138` 同属提交 `16bb32e24ed6d3fc97a19d2ef36dbf9f48a8780b`，包 SHA-256 均为 `b9104cf18fb7cfecf89ae7688a2d525c2875c377ab27eeaf83efd9988cf8b227`；实际 ZIP 摘要一致。两份[外部仓库脱敏快照](new-project-runs.json)与[已有项目快照](existing-project-runs.json)是维护者观测记录；对应仓库为私有，外部读者未必能打开运行日志。

beta.3 的 React 回归复用该作品同一包摘要 `b9104cf18fb7cfecf89ae7688a2d525c2875c377ab27eeaf83efd9988cf8b227`；其[脱敏快照](beta3-regression.json)记录了预览产物下载后的摘要核对、所选预览及提审摘要字段。私有仓库的运行日志可能无法由外部读者打开。

## 技术验证门槛

状态含义：**通过**表示本行列出的完整要求已由当前证据覆盖；**部分通过**表示已有直接证据但仍缺验收项；**待验证**表示当前证据不足以证明。

| 门槛 | 状态 | 当前证据与尚缺内容 |
| --- | --- | --- |
| G1 托管 Runner 认证 | 通过 | P0、独立托管预览与提交运行均成功；外部私有仓库也使用公开标签完成预览和首次提审。[同一 Secret 跨时间观察](session-observation.json)的两次成功运行开始相隔 82 分 18 秒。两次[提示词独立代理试用](prompt-only-trials.json)均自行用公开版 `set_secret.py` 设置 Secret，并完成托管预览及提审，符合修订后的验收方式。两者复用现成本机登录态，未重新测试交互登录；固定会话寿命不作推断。 |
| G2 失效与更新会话 | 通过 | `scripts/set_secret.py` 的安全传输有本地测试；外部仓库故意设置无效 Secret 后，托管预览明确报会话失效且未提审。重新设置有效 Secret 后，新提交预览及 Release 更新成功。自然过期时间与本地登出是否撤销旧会话仍未知，不作保证。 |
| G3 CLI 创建、预览、更新和接管 | 通过 | 真实预览、创建、内容更新及已有 React 项目的 beta.2、beta.3 更新成功；无 ID、无关联的隔离仓库已按唯一 slug [自动接管原 Toy](slug-adoption.json)，未重复创建。分页、归属验证与冲突停止有本地测试；审核中缺 URL 的可信绑定处理通过回归。**该特定平台形状在修复后尚未真实重现**，不将此额外场景说成已实测。 |
| G4 元信息保持 | 通过 | 真实内容更新的[前后快照](metadata-retention.json)显示标题、分类、可见性、封面和图标相同；已有 React 项目的单字段[手动同步](metadata-sync.json)只改变标题，分类、可见性、主题、水印和封面/图标 URL 摘要均保持。此项证明原计划的常规保留与选中字段同步；该同步前目标为 `published`，未验证审核中同步。 |
| G5 Deployment 关联保存与恢复 | 通过 | 托管临时令牌读写及跨运行读取成功；待核实记录经平台结果核对后恢复且未重提。本地故障注入覆盖关联或状态保存失败后的 ID 保留、停止重复创建与去重恢复；分页第二页和冲突也有本地测试。没有声称真实 GitHub 记录故障已发生。 |
| G6 同一预览包复用 | 通过 | 本仓库、新建 Vite 和已有 React 仓库的首次创建及第二次更新，均有预览与提审记录的相同提交和包摘要；[beta.3 React 回归](beta3-regression.json)还记录所选预览产物 ID、跳过重建及下载后摘要核对。缺少、已删除或过期 Artifact、摘要篡改、跨仓库来源均由本地测试阻断；未声称真实 Artifact 过期已发生。 |
| G7 不确定写入与安全重试 | 通过 | 本地故障注入模拟超时、未知结果与重复提审，均检查不重复写入；真实 status-only 响应曾触发停止，核实后 `resolve-unknown` 未重发 Toy 请求；明确拒绝 `307009` 被标为失败。此结论覆盖原计划的模拟与分类边界，不声称真实网络超时已出现。 |
| G8 权限和链接可见性 | 通过 | 工作流将 PR 限于构建预检，发布 job 不执行不受信任构建；本地测试确认 fork PR 规划只输出 `check`/构建，不访问 Toy、Release 或预览 Artifact。[GitHub 默认权限](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflows-in-forked-repositories)规定 fork PR 不传普通 Secret、`GITHUB_TOKEN` 只读。示例明确 `expose-preview: true` 会使链接及 Artifact 对工作流读者可见。真实 fork PR 未单独运行；私有仓库管理员可[放宽 fork PR 权限](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#enabling-workflows-for-forks-of-private-repositories)，不在此默认配置结论内。 |

CLI 版本与响应形状的来源见[上游契约记录](upstream-contract.md)。[Secret 元数据与跨时间运行记录](session-observation.json)确认同一仓库 Secret 在两次成功运行之间未更新；这只证明观察窗口，不据此计算会话寿命或推断登出撤销效果。

## 两条上手路径

| 路径 | 已验证 | 本次独立提示词试用 |
| --- | --- | --- |
| 新建项目 | HTML、Vite 脚手架可生成配置、封面、图标和工作流；[纯 HTML 文档独立代理试用](html-document-trial.json)完成两次预览、首次创建与同一 Toy 更新；公开安装版 Skill 经独立代理完成 Vite 构建、预检与子路径 HTTP 200，外部 Vite 仓库也完成预览、创建及更新提审 | [俄罗斯方块试用](prompt-only-trials.json)通过：独立公开仓库、可玩游戏、真实 Action 预览、同提交同包提审；曾因另一作品暂缺 URL 停止，按文档恢复。属于用户指定的代理验收 |
| 已有项目 | [独立代理隔离测试](skill-forward-test.md)将合成的现有 Vite React 项目适配 Toy，保留原工作流；私有 React 仓库已用 beta.1 首次提审、beta.2 与 beta.3 更新提审；Vue 示例完成隔离构建、资源与浏览器交互检查；安装版 Skill 的架构迁移停下行为由独立代理验证 | [muzzle-device-lab 试用](prompt-only-trials.json)通过：真实既有私有仓库、原应用及 Cloudflare 配置不变、真实预览和同包提审。可信绑定目标本身缺 URL 的修复仍缺同场景真实重测 |

记录更新原则：每新增一项真实平台或公开发行验证，补充对应运行、提交和观察结果，再提升表中状态。按用户于 2026-10-28 修订的方式，以两条独立代理试用完成上手验收；保留执行者与证据边界，不以 CI 绿灯代替真实路径。
