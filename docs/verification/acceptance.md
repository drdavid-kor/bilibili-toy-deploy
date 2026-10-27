# 公开测试版验收记录

日期：2026-10-28（Asia/Shanghai）。本页逐项记录当前已观察到的结果；“通过”只覆盖列出的证据范围。工作流运行时间由 GitHub 返回 UTC，下面以运行链接为准。测试使用 `toy` CLI v0.6.4、GitHub 托管 `ubuntu-latest` 和本仓库的演示作品。预览链接和会话令牌不写入本页。

## 当前结论

托管 Runner 已完成认证、Toy 预览、GitHub Deployment 记录写入、带封面和图标的**首次创建提审**、一次内容更新、一次元信息同步及一次手动覆盖提审。首次创建返回 Toy ID `48653775407104`；提审成功不等于新版已上线。先前一次不带素材的提审被平台以 `307009` 拒绝；补齐素材后创建成功，但这两次结果不能单独证明 `307009` 的唯一成因。

内容更新运行曾因 CLI 成功响应不含 ID 而在 Action 中失败；平台实际接受了更新，页面显示 Revision 2，前后元信息快照相同。随后用 `resolve-unknown` 核实并恢复 Deployment，未重复发送 Toy 写请求。公开标签的外部仓库安装、会话失效恢复、完整异常边界，以及由非项目成员按文档独立完成的两条上手路径仍待验证。

## 关键运行与产物

| 证据 | 当前可证明的范围 |
| --- | --- |
| [托管 Runner P0 运行 40535027750](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40535027750) | CLI 安装、隔离会话认证和 GitHub 记录验证步骤成功；2026-10-27 15:50–15:51 UTC |
| [CI 运行 40537312297](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537312297)、[40538443763](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538443763)、[40539031460](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539031460) | 三个相应提交的 CI 运行成功；证明对应版本的自动测试和构建检查通过，不等于真实平台验收 |
| [Toy 预览运行 40537312303](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537312303)、[40538443733](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538443733)、[40539031328](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539031328) | 主分支的计划、构建、预览及对应 Artifact 上传步骤完成；三次为独立托管运行 |
| [首次不带素材的 Release 运行 40537748338](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40537748338) | 平台明确拒绝提审，Action 报 `307009`；对应 Deployment 状态为 `failure`，未标为成功 |
| [带素材的首次创建运行 40538681541](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40538681541) | `verification-20261028-2` 对应提交的已预览包被提审接受；Toy ID `48653775407104`；提审与关联 Deployment 均为 `success` |
| [内容更新运行 40539309434](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539309434)、[元信息前后快照](metadata-retention.json) | CLI 返回 `{"status":"auditing"}` 但不含 ID；当时 Action 将运行标为失败，平台实际上接受更新，浏览器显示 Revision 2，所列标题、分类、可见性、封面和图标保持一致 |
| [结果恢复运行 40539826963](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40539826963) | 核实后将 Deployment `7363929796` 改为 `success`；记录显示没有再次向 Toy 发送写请求 |
| [元信息同步运行 40540219276](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40540219276) | 托管工作流及对应 Deployment `7364066856` 成功；这是提交审核的记录，未单独证明新版已上线 |
| [手动覆盖运行 40540210624](https://github.com/drdavid-kor/bilibili-toy-deploy/actions/runs/40540210624) | 托管工作流及对应 Deployment `7364074156` 成功，记录为直接提审覆盖；不推断审核结果 |
| [预览截图](toy-preview.jpg) | 演示页面在 Toy 预览中可见，截图显示页面及一次按钮交互；截图单独不能证明各版本审核或上线状态 |
| [Skill 现有项目隔离测试](skill-forward-test.md) | 独立实现代理按 Skill 改造 Vite React 样例，本地构建、预检与 Toy 子路径 HTTP 资源请求通过；没有远程发布，也不是独立人类使用测试 |

在首次成功创建中，预览 Deployment `7363798313` 与提审 Deployment `7363830573` 记录了相同提交 `f1b6cb528caf037f8474786e47a8de690f14ff47`、相同包 SHA-256 `fc308cf8d1d3c3b9bdcaeae6c4dcb0806e3b273b28437c025c561bcbb8319b37`。关联 Deployment `7363831942` 保存了返回的 Toy ID。此组记录支持“提审使用该提交对应的预览包”；后续还需在公开标签的外部仓库重复该路径。

## 技术验证门槛

状态含义：**通过**表示本行列出的完整要求已由当前证据覆盖；**部分通过**表示已有直接证据但仍缺验收项；**待验证**表示当前证据不足以证明。

| 门槛 | 状态 | 当前证据与尚缺内容 |
| --- | --- | --- |
| G1 托管 Runner 认证 | 部分通过 | P0、三次预览和一次创建分属全新托管运行，并完成需要 Toy 会话的操作。尚未证明普通外部用户可按 README 配置成功，也不推断固定会话寿命。 |
| G2 失效与更新会话 | 待验证 | `scripts/set_secret.py` 有本地测试；尚未完成真实会话过期、重新登录和 Secret 更新后的托管恢复。 |
| G3 CLI 创建、预览、更新和接管 | 部分通过 | 真实预览、首次创建与内容更新已发生。v0.6.4 更新成功响应只有 `status`，不重复返回 ID；当前代码从写入前已核实的目标 ID 关联结果。现有 Toy 自动接管和异常分页仍需验收。 |
| G4 元信息保持 | 部分通过 | 一次真实内容更新的[前后快照](metadata-retention.json)显示标题、分类、可见性、封面和图标相同；元信息同步提交成功。更多 Toy 和平台版本、同步后字段结果仍需观察。 |
| G5 Deployment 关联保存与恢复 | 部分通过 | P0 读写成功；首次创建后的 Toy ID 关联跨运行可查询；一次待核实 Deployment 经平台结果核对后恢复。删除记录、冲突、账号切换和保存失败恢复尚未做真实端到端测试。 |
| G6 同一预览包复用 | 部分通过 | 首次创建的预览与提审记录的 SHA 和包摘要一致，Release 提审成功；手动覆盖也完成直接提审。包篡改和跨仓库来源拒绝有本地测试，实际产物过期与公开标签外部仓库路径尚待验证。 |
| G7 不确定写入与安全重试 | 部分通过 | 真实状态响应缺 ID 时旧版 Action 停止；核实平台已接受后，`resolve-unknown` 恢复记录且未重复写入。新版解析已按该响应修正并有本地测试；真实超时、重复触发和 `not-accepted` 分支仍待验收。`307009` 是明确拒绝，不等同于结果未知。 |
| G8 权限和链接可见性 | 部分通过 | PR 仅检查、发布 job 使用单独权限已由代码与运行结构支持；示例明确 `expose-preview: true`，公开仓库的预览链接与 Artifact 视为可访问内容。外部 fork PR 无凭据验证及完整公开可见性检查仍待完成。 |

多次托管运行跨越 2026-10-27 15:50–16:13 UTC 约 23 分钟，但没有核对期间 Secret 是否被更新，因此这里**不宣称会话存活了 23 分钟**，更不推断其有效期。CLI 版本与响应形状的来源见[上游契约记录](upstream-contract.md)。

## 两条上手路径

| 路径 | 已验证 | 尚需完成 |
| --- | --- | --- |
| 新建项目 | HTML、Vite 脚手架在隔离目录生成正确配置、封面、图标和同版本工作流；本仓库演示作品完成托管预览、首次创建和一次真实更新 | 在**另一仓库**用公开标签和 README 独立完成配置、预览、首次创建、第二次更新；由非项目成员执行一次文档上手 |
| 已有项目 | [独立代理隔离测试](skill-forward-test.md)将现有 Vite React 项目的根路径改为相对基路径，保留原工作流，本地构建、预检及 Toy 子路径资源请求通过；React、Vue 示例由 CI 构建 | 在真实已有项目仓库验证 Action、预览、提审；由非项目成员执行一次文档上手，并检查需要架构迁移时 Skill 的停下行为 |

记录更新原则：每新增一项真实平台或公开发行验证，补充对应运行、提交和观察结果，再提升表中状态。独立代理测试与独立人类试用保持分开记录；不以当前 CI 绿灯代替第一版全部验收。
