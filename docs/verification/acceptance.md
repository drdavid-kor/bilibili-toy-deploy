# 公开测试版验收记录

日期：2026-10-28（Asia/Shanghai）。本页逐项记录当前已观察到的结果；“通过”只覆盖列出的证据范围。工作流运行时间由 GitHub 返回 UTC，下面以运行链接为准。测试使用 `toy` CLI v0.6.4、GitHub 托管 `ubuntu-latest` 和本仓库的演示作品。预览链接和会话令牌不写入本页。

## 当前结论

[`v0.1.0-beta.1`](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.1) 已从提交 `d6c5ca66935291bffb3fdc987720ef562e087d51` 公开发布。托管 Runner 已完成认证、Toy 预览、GitHub Deployment 记录写入、带封面和图标的**首次创建提审**、内容更新、元信息同步及手动覆盖提审。一个私有新建 Vite 仓库使用公开标签完成预览、首次创建提审及同一 Toy 的第二次更新提审；另一个已有 Vite React 仓库已完成首次创建提审。“已提交审核”不等于新版已上线。

旧版内容更新运行曾因 CLI 成功响应不含 ID 而在 Action 中失败；平台实际接受了更新，页面显示 Revision 2，前后元信息快照相同。随后用 `resolve-unknown` 核实并恢复 Deployment，未重复发送 Toy 写请求。修复后的普通 Release 更新已在托管 Runner 成功。外部仓库故意换入无效 Secret 后，手动预览明确失败且没有提审；重新设置有效 Secret 后，后续预览和 Release 更新均成功。公开 Skill 已安装，独立代理按安装版完成新 Vite 项目的本地检查；用户本人已表示愿意试用，**仍待实际反馈**。会话实际寿命以及本地登出是否撤销旧会话尚无结论。

已发布的 beta.1 在刚创建的 Toy 仍在审核、平台列表暂缺 URL 时会安全停止预览；同一运行在列表出现 URL 后重跑成功。beta.2 已加入用可信绑定识别该作品的修复，**仍待 CI 与外部仓库验证**；beta.1 标签保持不变。

## 关键运行与产物

| 证据 | 当前可证明的范围 |
| --- | --- |
| [托管 Runner P0 运行 40535027750](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40535027750) | CLI 安装、隔离会话认证和 GitHub 记录验证步骤成功；2026-10-27 15:50–15:51 UTC |
| [公开预发布 v0.1.0-beta.1](https://github.com/drdavid-kor/bilibili-toy-deploy/releases/tag/v0.1.0-beta.1) | 标签指向 `d6c5ca66935291bffb3fdc987720ef562e087d51`；仓库当前公开可访问。这是 Action 的预发布标签，用户的 Toy 提审流程仍要求普通已发布 Release，而非 prerelease |
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
| [beta.1 审核中缺 URL：首次尝试](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/1)、[同一运行第 2 次尝试](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/2) | 提交 `d5ea124fc326c047d046000f3300098c539085b6` 的第 1 次预览在目标核对阶段停止，没有 Toy 写入；后来平台列表有 URL，第 2 次尝试生成预览。GitHub 对该 run 的当前总状态显示成功，需按 attempt 区分 |
| 已验证的公开 Skill 安装命令 | `npx --yes skills@latest add drdavid-kor/bilibili-toy-deploy --skill toy-github --agent codex --yes --copy --json` 安装成功；独立实现代理按安装版完成新 Vite 脚手架、构建、预检与 Toy 子路径 HTTP 200。本项没有真人或远程提审证据 |
| 本地回归测试 | 当前工作树 42 个测试通过，覆盖审核中缺 URL 的可信绑定与保守阻断，以及记录失败、分页、过期产物、fork PR 规划等分支；已公开的 beta.1 标签对应版本为 34 个测试。本地故障注入不表示这些故障都在真实平台发生过 |
| [预览截图](toy-preview.jpg) | 演示页面在 Toy 预览中可见，截图显示页面及一次按钮交互；截图单独不能证明各版本审核或上线状态 |
| [Skill 现有项目隔离测试](skill-forward-test.md) | 独立实现代理按 Skill 改造 Vite React 样例，本地构建、预检与 Toy 子路径 HTTP 资源请求通过；没有远程发布，也不是独立人类使用测试 |

在本仓库首次成功创建中，预览 Deployment `7363798313` 与提审 Deployment `7363830573` 记录了相同提交 `f1b6cb528caf037f8474786e47a8de690f14ff47`、相同包 SHA-256 `fc308cf8d1d3c3b9bdcaeae6c4dcb0806e3b273b28437c025c561bcbb8319b37`。关联 Deployment `7363831942` 保存了返回的 Toy ID。

外部仓库预览 Deployment `7364281567` 与提审 Deployment `7364429248` 同属提交 `1ed01663f0a6ea47af8d67019e77ac236b5a2e83`，包 SHA-256 均为 `8cb98cf95bb47dac275b4115a84fb066e557ffd3c73ee28dd50c0684849d25e9`；关联 Deployment `7364430370` 保存了 Toy ID。这次独立仓库的首次提审复用了预览包。

外部仓库第二次更新的预览 Deployment `7364488908` 与提审 Deployment `7364512372` 同属提交 `3cec8c72824397a8b8b4f21ef35d329442ff9d6a`，包 SHA-256 均为 `4e6091c1c56fe43f3500688ffaed5ef948e156d60b1962dd30deba1d4d863d82`，并且都指向同一 Toy ID。

已有 Vite React 项目的预览 Deployment `7364500931` 与首次提审 Deployment `7364535382` 同属提交 `9c62541f51ce91730e9d0bc5a073b0bd444030bd`，包 SHA-256 均为 `850e3c841e11fc134ea8ec4c08407f9772ec01faabaefc1fc67d4a84e994631b`；关联 Deployment `7364537020` 保存了新 Toy ID。

## 技术验证门槛

状态含义：**通过**表示本行列出的完整要求已由当前证据覆盖；**部分通过**表示已有直接证据但仍缺验收项；**待验证**表示当前证据不足以证明。

| 门槛 | 状态 | 当前证据与尚缺内容 |
| --- | --- | --- |
| G1 托管 Runner 认证 | 部分通过 | P0、独立托管预览与提交运行均成功；外部私有仓库也使用公开标签完成预览和首次提审。普通用户按文档独立配置仍待本人试用，固定会话寿命不作推断。 |
| G2 失效与更新会话 | 通过 | `scripts/set_secret.py` 的安全传输有本地测试；外部仓库故意设置无效 Secret 后，托管预览明确报会话失效且未提审。重新设置有效 Secret 后，新提交预览及 Release 更新成功。自然过期时间与本地登出是否撤销旧会话仍未知，不作保证。 |
| G3 CLI 创建、预览、更新和接管 | 部分通过 | 真实预览、创建、内容更新与修复后的普通 Release 更新成功；脱敏响应已用于测试。分页、归属验证、唯一 slug 接管与冲突停止有本地测试；beta.2 审核中缺 URL 的可信绑定处理也已通过本地回归，外部仓库仍待验证。 |
| G4 元信息保持 | 部分通过 | 一次真实内容更新的[前后快照](metadata-retention.json)显示标题、分类、可见性、封面和图标相同。随后观察到手动同步所选标题/分类匹配配置，未选的可见性、封面和图标保持；同期还有本地响应探测写入，不能把变化唯一归因于某一次请求。 |
| G5 Deployment 关联保存与恢复 | 通过 | 托管临时令牌读写及跨运行读取成功；待核实记录经平台结果核对后恢复且未重提。本地故障注入覆盖关联或状态保存失败后的 ID 保留、停止重复创建与去重恢复；分页第二页和冲突也有本地测试。没有声称真实 GitHub 记录故障已发生。 |
| G6 同一预览包复用 | 通过 | 本仓库、新建 Vite 和已有 React 仓库的首次创建，以及外部 Vite 第二次更新，均有预览与提审记录的相同提交和包摘要。缺少、已删除或过期 Artifact、摘要篡改、跨仓库来源均由本地测试阻断；未声称真实 Artifact 过期已发生。 |
| G7 不确定写入与安全重试 | 通过 | 本地故障注入模拟超时、未知结果与重复提审，均检查不重复写入；真实 status-only 响应曾触发停止，核实后 `resolve-unknown` 未重发 Toy 请求；明确拒绝 `307009` 被标为失败。此结论覆盖原计划的模拟与分类边界，不声称真实网络超时已出现。 |
| G8 权限和链接可见性 | 部分通过 | 工作流结构将 PR 限于构建预检，发布 job 分离权限与受信任构建；本地测试确认 fork PR 规划只输出 `check`/构建，不访问 Toy、Release 或预览 Artifact。示例公开说明 `expose-preview: true` 的链接和 Artifact 可见性；真实 fork PR 无凭据运行尚未执行。 |

CLI 版本与响应形状的来源见[上游契约记录](upstream-contract.md)。已有跨时间托管运行，但未确认期间 Secret 是否更新，因此不据此计算会话寿命或推断登出撤销效果。

## 两条上手路径

| 路径 | 已验证 | 尚需完成 |
| --- | --- | --- |
| 新建项目 | HTML、Vite 脚手架可生成配置、封面、图标和工作流；公开安装版 Skill 已经独立代理完成 Vite 构建、预检与子路径 HTTP 200；外部仓库使用公开 Action 标签完成预览、首次创建及同一 Toy 的第二次更新提审 | [本人按文档独立试用](user-trial.md)及反馈；不把维护者运行当成人工上手验收 |
| 已有项目 | [独立代理隔离测试](skill-forward-test.md)将现有 Vite React 项目的根路径改为相对基路径，保留原工作流，本地构建、预检及 Toy 子路径资源请求通过；另一个私有 React 项目已用 beta.1 完成首次提审；React、Vue 示例由 CI 构建 | beta.2 对审核中缺 URL 的修复在该仓库完成第二次更新、[本人按文档独立试用](user-trial.md)及反馈，并检查需要架构迁移时 Skill 的停下行为 |

记录更新原则：每新增一项真实平台或公开发行验证，补充对应运行、提交和观察结果，再提升表中状态。独立代理测试与独立人类试用保持分开记录；不以当前 CI 绿灯代替第一版全部验收。
