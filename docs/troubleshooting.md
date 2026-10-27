# 故障排查

先区分失败发生在构建、静态预检、Toy 预览、提审，还是 GitHub 记录保存。工作流 Summary 和 CLI 错误会指出阶段；同一个提示不能套用所有重试方法。

| 现象 | 应先检查什么 | 恢复方式 |
| --- | --- | --- |
| PR 构建失败 | 原项目的依赖锁文件、构建命令和环境变量 | 在本地复现并修复构建；PR 不需要 Toy Secret |
| 静态预检 ERROR | 入口文件、资源路径、包体硬限制和配置 | 修复错误后重新构建；WARN 会显示但不阻断 |
| 新 Toy 预览成功，但创建提审被拒 | `create.poster`、`create.icon` 是否填写且文件存在，图片规格与平台返回原因 | 先用模板提供的封面、图标补齐并重新预览；如果仍被拒，按平台实际错误继续排查，不假定缺图是唯一原因 |
| Toy 页面白屏或 404 | 构建产物内的 `/` 根路径、Vite base、路由刷新和文件名大小写 | 修正项目并重新预览；不能只凭上传成功判定页面正常 |
| 未找到 Release 对应预览包 | tag 指向的 SHA、产物保留期和预览运行是否成功 | 为该提交重新预览；必要时使用明确标记的手动覆盖 |
| 同名 slug 有多个匹配或查询失败 | 当前账号、slug 与 CLI 返回的完整列表 | 先核对目标，必要时显式填写 Toy ID；不要直接重试创建 |
| `v0.1.0-beta.1` 在刚创建的 Toy 审核期间报 `Toy listing contains unverifiable ownership or slug` | 平台列表项可能已有正确归属，却暂时没有可核对 slug 的 URL；[首次失败运行](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/1)在预览前停止，没有发送 Toy 写请求 | 先到 B 站确认目标 Toy 与审核状态；待列表出现可核对的 URL 后，可重跑原预览（[同一运行第 2 次尝试已成功](https://github.com/drdavid-kor/bilibili-toy-existing-example/actions/runs/40543593753/attempts/2)）。也可升级到修复版 `v0.1.0-beta.2` 后重新预览。不要改 slug 或直接发布 Release 来绕过核对 |
| 会话过期或身份不符 | GitHub Secret 和预期 B 站账号 | 按[认证说明](authentication.md)更新会话后重试；不要粘贴会话到 Issue 或聊天 |
| 提审被平台明确拒绝 | CLI 返回的业务原因、元信息和内容 | 修复原因后重新触发；此前提审仍有记录 |
| 提审结果待核实 | 原提交、包摘要、Toy ID/slug、B 站后台状态，以及运行 Summary 中的 Deployment ID | 先在 B 站核实**这一次请求**；然后在手动工作流选择 `resolve-unknown`，填写 `deployment-id` 和 `resolution=accepted` 或 `not-accepted`。该操作不重提 Toy |
| 提审成功但关联保存失败 | Summary 中的 Toy ID、Deployment 权限和 GitHub API 错误 | 修复权限、显式补填 ID 或恢复记录；不要因记录失败再次提审 |

`v0.1.0-beta.2` 的审核中作品处理逻辑：若仓库已有经核对的 binding（账号、Toy ID 与 slug），即使平台列表暂未给该作品 URL，也可用该绑定继续识别目标。修复已通过本地回归、CI 和外部 React 项目的普通更新；尚未在平台再次出现审核中缺 URL 时做同场景重测。若没有可信绑定，而列表中任一作品缺 URL，Action 仍停止自动创建或接管。显式 `toy_id` 也不能绕过缺 URL 时的归属与 slug 核对。首次创建已被平台接受、但 GitHub 关联保存失败且 URL 暂缺时，应保留已返回的 Toy ID 和 Deployment 记录，等能核实 URL 后恢复关联；不要把已接受的请求标为 `not-accepted`，也不要重新创建。

对静态包，Toy 运行于 `/toy/<slug>/`，首页引用 `/assets/...` 容易指向站点根路径。Vite 可配置合适的 base，React/Vue 的 history 路由需要在静态环境下实际验证；示例采用 hash 路由。外部 API、第三方登录和浏览器存储不会因静态预检通过而自动兼容。

“已提交审核”只表示平台接受申请。查看页面是否可用以及审核是否通过，请到 B 站平台核对。Action 第一版不自动回传最终审核结果。

独立 Action 的 `expose-preview` 默认是 `false`，因此运行 Summary 不显示预览 URL。示例工作流把它改为 `true`；公开仓库的 Summary 与 Artifact 可能让其他人取得预览内容。不要把凭据或未准备公开的内容放进网页包。
