# IMakerStudioCN 资源簿

一个由 GitHub Pages 托管、无需服务器的小型链接资源导航。

- 网站：<https://imakerstudiocn.github.io/>
- 访客投稿页：<https://imakerstudiocn.github.io/submission.html>
- 管理者维护页：<https://imakerstudiocn.github.io/admin.html>
- 在线手册：<https://imakerstudiocn.github.io/maintenance.html>
- 仓库：`IMakerStudioCN/IMakerStudioCN.github.io`
- 发布分支：`main`
- 访客投稿：飞书公开表单
- 管理者编辑：Pages CMS
- 审核同步：GitHub Actions 创建并自动合并 Pull Request

## 管理交接清单

1. 将新维护者加入 GitHub 组织，并确认其对本仓库有写入权限。
2. 共享飞书多维表格，允许新维护者查看投稿并更新审核字段。
3. 确认其能打开网站、仓库、Actions、在线手册和投稿表单。
4. 试改一条测试资源，完成提交、发布和线上检查。
5. 不在仓库中保存密码、令牌、私人联系方式或内部链接。

## 文件配置索引

- `index.html`：首页标题、导航、介绍、资源区标题、维护原则和页脚。
- `submission.html`、`submission.js`：访客飞书投稿入口及投稿地址读取脚本。
- `admin.html`：管理者在线编辑、投稿审核和发布入口。
- `resources.json`：更新时间、投稿地址、默认封面和资源数据。
- `app.js`：卡片生成、分类、搜索、计数和数据读取。
- `.pages.yml`：Pages CMS 字段配置。
- `scripts/sync-feishu-submissions.mjs`：飞书记录转换脚本。
- `.github/workflows/sync-feishu-submissions.yml`：定时创建并自动合并 PR。
- `styles.css`：颜色、字号、间距、封面透明度和手机布局。
- `assets/resource-cover.webp`：资源卡片默认封面。
- `maintenance.html`：网页维护手册。
- `README.md`：仓库交接手册，应与网页手册同步。
- `404.html`：无效地址页。
- `.nojekyll`：让 Pages 直接发布静态文件，保留即可。

## 标题与文案配置

### 首页 `index.html`

- 浏览器标题：`<title>资源簿</title>`。
- 搜索引擎摘要：`<meta name="description">` 的 `content`。
- 左上角站名：`class="brand"` 内的“资”和“资源簿”。
- 导航名称和地址：`class="header-actions"` 内链接文字与 `href`。
- 首页小标题：“少而精的链接收藏”。
- 首页主标题：“找到值得打开的资源”。
- 首页简介：`class="intro-note"`。
- 统计标签：“项资源”“个分类”“最后整理”；数字和日期自动读取。
- 资源区标题：“资源索引”“浏览全部”。
- 搜索提示：输入框的 `placeholder`。
- 空结果提示：`class="empty-state"` 内文字。
- 页脚：`<footer>` 内站名、说明和链接。

修改站名后，用仓库搜索查找旧站名，并同步修改 `maintenance.html`、`404.html` 和本文件。其他页面的浏览器标题位于各自文件的 `<title>`。

## 资源数据维护

1. 打开 `resources.json` 并点击铅笔图标。
2. 复制一条完整资源对象，在上一条结尾补英文逗号。
3. 修改字段并更新顶部 `updatedAt`。
4. 提交到 `main`，等待 Pages 发布。

```json
{
  "name": "资源名称",
  "description": "说明它解决什么问题、适合哪些人。",
  "url": "https://example.com/",
  "category": "学习",
  "type": "网站",
  "tags": ["教程", "免费"],
  "cover": "./assets/example-cover.jpg"
}
```

- `name`：卡片标题，建议不超过 24 个中文字符。
- `description`：卡片说明，建议 30 至 70 个中文字符。
- `url`：目标地址，保留 `https://`。
- `category`：内容主题；新名称会自动生成第一排筛选按钮。
- `type`：资源载体；新名称会自动生成第二排筛选按钮。
- `tags`：更细的关键词；卡片显示前两个，搜索读取全部。
- `cover`：可选的单条封面；省略则使用 `defaultCover`。

JSON 只能使用英文双引号和英文标点。最后一条资源后不要加逗号。

### 扩展分类和资源类型

- `category` 表示内容主题，例如“开发、设计、学习、效率”。
- `type` 表示资源载体，例如“网站、网盘链接、在线工具、文档、视频、课程平台”。
- 写入新的 `category` 或 `type` 后，页面自动生成筛选按钮，无需修改 HTML 或 JavaScript。
- 同一含义必须使用相同文字。重命名时搜索并修改所有相关资源，避免出现重复按钮。
- 两层筛选可以组合，例如先选“学习”，再选“视频”；搜索同时读取分类、类型和标签。

### 扩展标签

```json
"tags": ["教程", "免费", "中文"]
```

- 建议每条设置 2 至 5 个短标签。
- 不要把分类和资源类型重复写成标签。
- 卡片只展示前两个标签，但搜索读取全部标签。
- 新标签不会生成按钮；需要筛选按钮时使用 `category` 或 `type`。
- 网盘资源的 `type` 统一写成“网盘链接”，说明中写明内容、格式和更新时间，并定期检查是否失效。

## 扩展独立页面

新增说明页、专题页或公告页时：

1. 复制现有 HTML 页面，使用小写英文文件名，例如 `guide.html`。
2. 修改 `<title>`、`meta description`、正文标题和内容。
3. 保留 `./styles.css` 相对路径，需要交互时再引用独立脚本。
4. 在 `index.html` 的 `header-actions` 或页脚增加 `./guide.html` 链接。
5. 如果所有页面都需要入口，同步修改 `maintenance.html` 和 `404.html`。
6. 发布后访问 `https://imakerstudiocn.github.io/guide.html`，检查桌面和手机布局。

分类、类型和标签只需编辑 `resources.json`。只有需要独立正文和独立网址时才创建 HTML 页面。

## 封面图片配置

默认封面在 `resources.json` 顶部：

```json
"defaultCover": "./assets/resource-cover.webp"
```

1. 将有使用权的横向 JPG、PNG 或 WebP 上传到 `assets`。
2. 建议宽度 1200 至 2000 像素、文件小于 500 KB。
3. 修改 `defaultCover`；路径区分大小写。
4. 单条资源需要独立封面时，在该对象中增加 `cover`。

`styles.css` 中的封面设置：

- 默认透明度：`.resource-cover` 的 `opacity: .16`。
- 悬停透明度：`.resource-card:hover .resource-cover` 的 `opacity: .23`。
- 图片裁切：`.resource-cover` 的 `object-fit` 与 `object-position`。
- 文字遮罩：`.resource-card::after` 的渐变。

## 外观配置

`styles.css` 顶部变量控制全站颜色：

```css
--paper: #f4f5f0;       /* 页面背景 */
--surface: #ffffff;     /* 悬停表面 */
--ink: #17201b;         /* 主文字和按钮 */
--muted: #667069;       /* 次要文字 */
--line: #d7dcd5;        /* 分隔线 */
--accent: #126b4b;      /* 强调色 */
--accent-soft: #dcebe3; /* 聚焦浅色 */
--radius: 14px;         /* 圆角 */
```

常用位置：`.intro h1` 控制首页主标题，`.catalog-head h2` 控制资源区标题，`.resource-card h3` 控制卡片标题，`.resource-card` 控制卡片高度与间距，`.site-header, main, footer` 控制页面最大宽度，`@media (max-width: 760px)` 控制手机布局。

修改后同时检查桌面和约 375 像素宽的手机页面，确认没有横向溢出。

## 投稿与审核

### 两个独立入口

- 访客打开 `submission.html`，使用飞书公开表单，无需 GitHub 登录。
- 管理者打开 `admin.html`，进入 Pages CMS 或查看投稿审核与发布说明。

### 飞书数据表字段

公开表单字段：`资源名称`、`资源链接`、`资源简介`、`内容分类`、`资源类型`、`标签`，可选 `封面地址`。

管理字段：

- `审核状态`：单选，选项为待审核、已通过、不收录。
- `同步状态`：单行文本，初始为空，由 Actions 回写 PR 地址；不要设为单选字段。

### 自动审核同步

1. 管理者检查投稿并将 `审核状态` 改为“已通过”。
2. `Sync approved Feishu submissions` 每两小时执行，也支持手动运行。
3. 默认处理全部“已通过”且“同步状态为空”的记录；日志会显示候选数量、资源名称、记录 ID、投稿时间和中文缺失字段名。
4. Actions 更新 `resources.json`，推送临时分支并创建普通 PR。
5. Actions 回写飞书同步状态，然后用专用令牌自动合并 PR 并删除临时分支。
6. 合并到 `main` 后，GitHub Pages 自动发布。

自动合并失败时，PR 和已回写的地址会保留，应根据 Action 日志检查令牌权限、分支保护或合并冲突并手动恢复。只有关闭 PR 且需要重新生成时，才清空对应飞书记录的同步状态。

### 飞书开放平台配置

创建企业自建应用，申请多维表格读取和编辑权限，发布应用并将其添加为目标多维表格协作者。

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

Secrets：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_MERGE_TOKEN`：仅授权当前仓库的细粒度 PAT，需要 Contents 和 Pull requests 读写权限

Variables：

- `FEISHU_APP_TOKEN`：`TDDCbNKFUa1d7QsKX7vcrJinnhe`
- `FEISHU_TABLE_ID`：`tblyK8zKwJX3F91g`
- `FEISHU_VIEW_ID`：`vew3HOr4oa`

默认字段名与上文一致时无需配置映射。字段不同可增加：`FEISHU_FIELD_NAME`、`FEISHU_FIELD_URL`、`FEISHU_FIELD_DESCRIPTION`、`FEISHU_FIELD_CATEGORY`、`FEISHU_FIELD_TYPE`、`FEISHU_FIELD_TAGS`、`FEISHU_FIELD_COVER`、`FEISHU_FIELD_REVIEW`、`FEISHU_FIELD_SYNC`、`FEISHU_FIELD_CREATED_TIME`。同步默认使用 `FEISHU_SYNC_MODE=all`，处理全部“审核状态=已通过且同步状态为空”的投稿；仅需每次处理最新一条时改为 `latest`。

进入 Settings → Actions → General → Workflow permissions，启用 **Allow GitHub Actions to create and approve pull requests**。否则工作流可以推送临时分支，但无法创建审核 PR。

### 管理者在线编辑

1. 打开 <https://imakerstudiocn.github.io/admin.html>，选择“进入 Pages CMS”。
2. 使用 GitHub 登录 Pages CMS。
3. 安装 Pages CMS GitHub App，只授权当前仓库。
4. 选择 `IMakerStudioCN/IMakerStudioCN.github.io`。
5. 在“资源管理”中编辑，保存前更新最后整理日期。
6. 保存后检查 Actions 与线上网站。

`FEISHU_APP_SECRET` 和 `FEISHU_MERGE_TOKEN` 只能保存在 GitHub Secret 中，不能提交到仓库。

## 发布与回退

1. 提交文件到 `main`。
2. 在 Actions 查看 `pages build and deployment`。
3. 绿色对勾后等待约 1 至 3 分钟并强制刷新。
4. 检查首页、修改过的资源、投稿按钮和在线手册。

项目只使用 GitHub Pages 内置工作流。需要回退时，对错误提交使用 Revert 生成反向提交；不要强制重置 `main`。

## 故障排查

- 网站仍是旧内容：确认 Actions 成功后强制刷新。
- 资源列表不显示：检查 `resources.json` 的逗号、双引号和括号。
- 封面不显示：确认图片已提交、路径大小写一致；单条检查 `cover`，全部检查 `defaultCover`。
- 投稿打不开：用未登录飞书的浏览器测试，并检查公开分享及 `submitUrl`。
- 飞书同步失败：检查必需的 Secrets、Variables、应用权限、文档协作者权限和字段名。
- 投稿未生成 PR：确认审核状态为“已通过”、同步状态为空且链接没有重复。
- PR 未自动合并：检查 `FEISHU_MERGE_TOKEN` 是否过期且具有必需权限，再检查 `main` 的分支保护和 PR 合并冲突。
- Pages 失败：查看失败步骤，检查 Pages 来源和重复工作流；部署阶段短暂失败可稍后重试。

## 安全边界

- GitHub Pages 和仓库均公开，不保存秘密或敏感信息。
- 网站没有账号、评论、数据库和权限系统。
- 只分享合法外部链接，不代理文件，不绕过付费或版权限制。
- 新增图片前确认有使用权并压缩文件。
- `github.io` 在中国大陆的访问速度和稳定性无法保证。
