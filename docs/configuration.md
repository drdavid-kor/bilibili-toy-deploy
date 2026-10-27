# 配置与发布规则

项目在仓库根目录使用 `toy.config.json`。该文件保存目标 Toy 和首次创建的非敏感信息，不保存 B 站会话、GitHub 令牌或访问密码。纯 HTML 模板的起始示例如下；Vite 项目把 `directory` 改为 `dist`：

编辑器可以使用[配置 JSON Schema](../schema/toy.config.schema.json)提示字段与取值；实际发布仍由 Action 校验目标路径、账号和平台返回值。

```json
{
  "slug": "my-toy",
  "directory": "site",
  "create": {
    "title": "My Toy",
    "category": "TOOL",
    "visibility": "link-only",
    "poster": "toy-assets/poster.png",
    "icon": "toy-assets/icon.png"
  },
  "metadata": {}
}
```

把 `my-toy` 和标题换成自己的值。第一版配置只接受 `slug`、`directory`、可选 `toy_id`、`create` 和 `metadata` 五类顶层字段。标题、分类、可见性、图标、封面、主题、水印和活动字段应放在 `create` 或 `metadata` 中；`watermark` 必须写 JSON 布尔值 `true` 或 `false`。`toy_id` 是正整数。具体可选字段以所选 Action 发行标签附带的实现和示例为准，以下说明解释字段的用途与优先级。

| 字段 | 用途 | 更新时的行为 |
| --- | --- | --- |
| `slug` | Toy 地址标识；用于首次创建和寻找已有作品 | 不能修改已有 Toy 的 slug；若与保存的关联不符则停止 |
| `toy_id`（可选） | 明确指定现有 Toy，或用于关联恢复 | 先验证当前账号归属与 slug，再更新 |
| `directory` | 用户工作流构建后的静态产物目录 | Action 使用此目录，不自行构建 |
| `create.title` | 首次创建的标题 | 日常更新不覆盖平台现值 |
| `create.category`（可选） | 首次创建的分类 | 日常更新不覆盖平台现值 |
| `create.visibility`（可选） | 首次创建可见性，默认 `link-only` | 日常更新不覆盖平台现值 |
| `create.poster`、`create.icon` | 首次创建使用的封面与图标路径 | 日常更新不覆盖平台现值 |
| `metadata`（可选） | 手动元信息同步时的字段 | 仅手动同步并仅显式填写的字段生效 |

图片字段 `icon`、`poster` 填写仓库内相对路径。模板已提供 `toy-assets/poster.png`（1200×900）和 `toy-assets/icon.png`（256×256）；改造已有项目前可复制这两张占位图，以便完成首次创建。B 站真实提审曾在缺少素材的情况下拒绝创建，即使预览已生成；完整原因仍以当前平台响应为准。为减少这类失败，首次创建路径应提供有效图片。分类可选 `GAME`、`INTERACTIVE_PLAY`、`TOOL`、`TEST`、`GUIDE`、`COLLECTION`、`OTHER`。测试版只接受 `link-only` 和 `public` 两种显式可见性；已有密码访问作品在普通内容更新中保持原配置，但当前不支持通过此配置设置或修改访问密码。配置文件中省略一个元信息字段表示“保持原值”，不能用空字符串代替删除指令。

## 事件与结果

| 触发 | 默认动作 |
| --- | --- |
| PR | 构建与静态预检；不上传 Toy，也不读取 Toy Secret |
| 主分支 push | 构建、预检、生成 Toy 预览并保存对应产物 |
| 发布 GitHub Release | 取同一提交已预览的包，创建或更新 Toy 并提交审核 |
| 推送 tag | 无独立 Toy 操作 |
| 手动预览 | 对选定的受信任提交生成预览 |
| 手动覆盖提审（`override`） | 重新构建指定 Release 的提交并预检，直接提审，记录覆盖事实 |
| 手动元信息同步 | 只更新 `metadata` 中显式字段并提交审核 |
| 手动处理待核实结果（`resolve-unknown`） | 输入失败记录中的 Deployment ID；在 B 站核实后选择 `accepted` 或 `not-accepted`，不再次发送 Toy 写请求 |

示例工作流的手动入口可选 `preview`、`submit`、`override`、`sync-metadata`、`resolve-unknown`。手动 `submit` 和 `override` 必须填现有已发布、非预发行版的 `release-tag`；手动 `preview` 可填处于默认分支历史中的 `source-ref`，留空则使用默认分支。PR 仅检查。工作流成功时应显示“已提交审核”，不能据此判断新版已上线。若前一版尚在审核，新 Release 仍可提交；平台是否接受由 B 站决定。同一 Toy 的写操作串行进行。

示例工作流使用 GitHub [concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)，将同一仓库的 Toy 写操作放进一个组，设置 `cancel-in-progress: false` 与 `queue: max`，以排队而非取消后续运行。GitHub 每组最多保留 100 个待运行任务，超出时会取消新任务。这只控制 GitHub 工作流的并发，不表示等待 B 站完成审核。

独立 Action 的 `expose-preview` 默认为 `false`，不在 Summary 输出预览 URL；示例工作流将它明确设为 `true`，以便从 Actions 页打开预览。预览 URL 含可访问内容的能力链接，公开仓库的运行 Summary 和 Artifact 可被他人看到。只把可以公开分享的网页包放入示例流程；若内容尚需保密，先使用私有仓库并审查访问者，或使用自己的预览交付方式。把选项改成 `false` 会隐藏 URL，也会使本示例无法通过 Summary 打开预览。

## 关联和恢复

Action 优先使用显式 ID，其次核对 GitHub Deployment 中保存的关联；两者都没有时，查询当前 B 站账号下的全部 Toy。唯一 slug 匹配会自动接管；完整查询确认零匹配才创建。查询失败、多项匹配、账号或 slug 冲突都会停止。因网络中断而“结果待核实”时，不能因暂时查不到记录就再提交一次。

Deployment 记录仅用于保存非敏感关联和提交事实。它不是审核通过证明，也不是 Secret 存储。若 Toy 提审成功而保存关联失败，工作流应展示 Toy ID 和恢复方法；下一次可以显式填入 `toy_id`，但恢复记录本身不应重新提审。

运行 Summary 会列出经过筛选的操作上下文：提交、所选预览运行与产物 ID、包摘要、Release 与覆盖状态；元信息同步只列字段名、图片摘要及内容指纹。恢复待核实请求时会重列原请求的上下文和时间，不输出凭据或完整 CLI 响应。预览在上传前先确认 GitHub Deployment 记录可写；权限不足时停止，不产生可复用预览。

预览产物与完整提交 SHA 对应。Release 必须使用同一 SHA 的预览产物；包过期或摘要不一致会停止。手动覆盖是单独的显式操作，并不会自动从失败的常规提审切换过去。
