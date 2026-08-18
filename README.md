# IMakerStudioCN 资源簿

一个由 GitHub Pages 托管、无需服务器的小型链接资源导航。

- 网站：<https://imakerstudiocn.github.io/>
- 在线手册：<https://imakerstudiocn.github.io/maintenance.html>
- 仓库：`IMakerStudioCN/IMakerStudioCN.github.io`
- 发布分支：`main`
- 投稿方式：飞书公开表单

## 管理交接清单

1. 将新维护者加入 GitHub 组织，并确认其对本仓库有写入权限。
2. 共享飞书多维表格，允许新维护者查看投稿并更新审核字段。
3. 确认其能打开网站、仓库、Actions、在线手册和投稿表单。
4. 试改一条测试资源，完成提交、发布和线上检查。
5. 不在仓库中保存密码、令牌、私人联系方式或内部链接。

## 文件配置索引

- `index.html`：首页标题、导航、介绍、资源区标题、维护原则和页脚。
- `resources.json`：更新时间、投稿地址、默认封面和资源数据。
- `app.js`：卡片生成、分类、搜索、计数和数据读取。
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

“推荐资源”读取 `resources.json` 的 `submitUrl`。更换飞书表单时，写入新的公开填写地址。地址应包含 `/share/base/form/`，不要使用内部多维表格地址。

审核流程：

1. 在飞书普通数据视图查看新记录。
2. 检查链接可用性、合法性和重复情况。
3. 统一名称、说明、分类与标签。
4. 把通过记录写入 `resources.json` 并更新日期。
5. 将飞书记录标为“已收录”或“不收录”。

建议保留“审核状态、审核备注、处理日期、处理人”四个管理字段，并设置新增记录通知。原始数据表只向维护者开放。

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
- Pages 失败：查看失败步骤，检查 Pages 来源和重复工作流；部署阶段短暂失败可稍后重试。

## 安全边界

- GitHub Pages 和仓库均公开，不保存秘密或敏感信息。
- 网站没有账号、评论、数据库和权限系统。
- 只分享合法外部链接，不代理文件，不绕过付费或版权限制。
- 新增图片前确认有使用权并压缩文件。
- `github.io` 在中国大陆的访问速度和稳定性无法保证。
