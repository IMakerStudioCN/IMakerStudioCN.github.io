IMakerStudioCN 资源簿

项目简介

这是一个由 GitHub Pages 托管、无需服务器的小型链接资源导航。

网站：https://imakerstudiocn.github.io/
访客投稿页：https://imakerstudiocn.github.io/submission.html
管理者维护页：https://imakerstudiocn.github.io/admin.html
在线手册：https://imakerstudiocn.github.io/maintenance.html
仓库：https://github.com/IMakerStudioCN/IMakerStudioCN.github.io
发布分支：main
访客投稿：飞书公开表单，无需 GitHub 登录
管理者编辑：Pages CMS 在线编辑器
审核同步：GitHub Actions 创建并自动合并 Pull Request


一、管理交接清单

1. 将新维护者加入 GitHub 组织 IMakerStudioCN。
2. 确认新维护者对 IMakerStudioCN.github.io 仓库有写入权限。
3. 将飞书多维表格共享给新维护者，允许其查看投稿并更新审核字段。
4. 确认新维护者能打开网站、仓库、Actions、在线手册和投稿表单。
5. 让新维护者试改一条测试资源，完整执行提交、发布和线上检查流程。
6. 不要在仓库中保存密码、访问令牌、私人联系方式或内部链接。


二、主要文件

index.html
首页结构，包括浏览器标题、导航、介绍、资源区标题、维护原则和页脚。

submission.html 和 submission.js
访客飞书投稿入口，以及从 resources.json 读取公开表单地址的脚本。

admin.html
管理者在线编辑、投稿审核和发布入口。

resources.json
保存更新时间、投稿地址、默认封面和全部资源数据。日常维护主要编辑这个文件。

app.js
负责读取资源、生成卡片、内容分类、资源类型筛选、关键词搜索和资源计数。

.pages.yml
Pages CMS 管理者编辑器的字段配置。

scripts/sync-feishu-submissions.mjs
读取审核通过的飞书记录并转换为 resources.json 数据。

.github/workflows/sync-feishu-submissions.yml
定时运行同步脚本、创建并自动合并 Pull Request，并回写飞书同步状态。

styles.css
负责颜色、字号、间距、卡片封面透明度和手机布局。

assets/resource-cover.webp
资源卡片使用的默认封面图片。

maintenance.html
网站中的站务手册。

README.md
GitHub 仓库首页显示的 Markdown 版维护说明。

README.txt
当前这份纯文本维护说明。

404.html
无效地址提示页。

.nojekyll
让 GitHub Pages 直接发布静态文件。不要删除。


三、首页标题和文案配置

以下内容在 index.html 中修改。

浏览器标签标题：查找 title 标签中的“资源簿”。
搜索引擎摘要：修改 meta name="description" 的 content。
左上角方形标记：修改 class="brand-mark" 内的“资”。
左上角站名：修改 class="brand" 内的“资源簿”。
导航名称和地址：修改 class="header-actions" 内的文字和 href。
首页小标题：查找“少而精的链接收藏”。
首页主标题：查找“找到值得打开的资源”。
首页简介：修改 class="intro-note" 的文字。
统计标签：修改“项资源”“个分类”“最后整理”。数字和日期由脚本自动填写。
资源区标题：修改“资源索引”和“浏览全部”。
搜索框提示：修改搜索输入框的 placeholder。
空结果提示：修改 class="empty-state" 内的文字。
页脚文字：修改 footer 内的站名、说明和链接。

修改站名后，应搜索旧站名，并同步修改 maintenance.html、404.html、README.md 和 README.txt。


四、添加或修改资源

1. 在 GitHub 仓库中打开 resources.json。
2. 点击铅笔图标进入编辑模式。
3. 复制一条完整的资源记录。
4. 在上一条资源结尾添加英文逗号。
5. 修改新资源的各个字段。
6. 更新文件顶部的 updatedAt。
7. 提交到 main 分支。
8. 等待 GitHub Pages 发布完成。

资源记录示例：

{
  "name": "资源名称",
  "description": "说明它解决什么问题、适合哪些人。",
  "url": "https://example.com/",
  "category": "学习",
  "type": "网站",
  "tags": ["教程", "免费"],
  "cover": "./assets/example-cover.jpg"
}

字段说明：

name
资源卡片标题，建议不超过 24 个中文字符。

description
资源说明，建议 30 至 70 个中文字符。

url
点击卡片后打开的地址，必须保留 https://。

category
内容主题，例如开发、设计、学习、效率。页面第一排筛选按钮会自动读取全部分类。

type
资源载体，例如网站、网盘链接、在线工具、文档、视频、课程平台。页面第二排筛选按钮会自动读取全部类型。

tags
更细的搜索关键词。卡片显示前两个标签，但搜索会读取全部标签。

cover
可选的单条资源封面。省略时使用 defaultCover 指定的默认封面。


五、扩展分类和资源类型

直接在资源记录的 category 或 type 中填写新名称，页面会自动生成筛选按钮，不需要修改 index.html 或 app.js。

category 表示内容主题，例如开发、设计、学习、效率。
type 表示资源载体，例如网站、网盘链接、在线工具、文档、视频、课程平台。

两层筛选可以组合。例如先选择“学习”，再选择“视频”。搜索框也会同时搜索名称、说明、分类、类型和标签。

同一含义必须使用完全相同的名称。不要同时出现“网盘”“网盘资源”和“网盘链接”。重命名时，应搜索并修改所有相关资源，否则页面会生成多个相似按钮。


六、扩展标签

标签写在 tags 数组中，并使用英文双引号和英文逗号。

示例：

"tags": ["教程", "免费", "中文"]

每条资源建议设置 2 至 5 个短标签。
不要把内容分类和资源类型重复写成标签。
标签会参与搜索，但不会生成筛选按钮。
如果需要生成筛选按钮，应使用 category 或 type。


七、网盘链接维护

网盘资源的 type 统一填写“网盘链接”。

description 中应写清文件内容、文件格式和更新时间。
提取码可以写在说明中。
不要收录需要私人账号、个人权限或来源不明的文件。
不要分享侵权、违法或绕过付费限制的资源。
应定期检查网盘链接是否失效，失效后及时删除或替换。


八、封面图片配置

全站默认封面在 resources.json 顶部配置：

"defaultCover": "./assets/resource-cover.webp"

更换默认封面的方法：

1. 准备有使用权的横向 JPG、PNG 或 WebP 图片。
2. 建议图片宽度为 1200 至 2000 像素。
3. 建议文件小于 500 KB。
4. 将图片上传到 assets 文件夹。
5. 修改 defaultCover 的文件路径。

文件路径区分大小写。文件名建议只使用小写英文、数字和连字符。

单条资源需要独立封面时，在该资源记录中增加 cover 字段。

封面透明度在 styles.css 中修改：

.resource-cover 的 opacity 控制默认透明度，当前为 0.16。
.resource-card:hover .resource-cover 的 opacity 控制悬停透明度，当前为 0.23。
.resource-cover 的 object-fit 和 object-position 控制裁切位置。
.resource-card::after 控制文字区域的渐变遮罩。


九、外观配置

styles.css 顶部的颜色变量：

--paper：页面背景色。
--surface：卡片悬停表面色。
--ink：主要文字和深色按钮。
--muted：次要文字。
--line：分隔线。
--accent：强调色。
--accent-soft：聚焦状态浅色。
--radius：圆角基准。

常用样式位置：

.intro h1：首页主标题。
.catalog-head h2：资源区标题。
.resource-card h3：资源卡片标题。
.resource-card：卡片高度和内边距。
.site-header, main, footer：页面最大宽度。
@media (max-width: 760px)：手机端布局。

修改外观后，应同时检查桌面页面和约 375 像素宽的手机页面，确认文字清晰且没有横向溢出。


十、扩展独立页面

如果需要新增说明页、专题页或公告页：

1. 复制一个现有 HTML 页面。
2. 使用小写英文文件名，例如 guide.html。
3. 不要在文件名中使用空格或中文。
4. 修改 title、meta description、正文标题和内容。
5. 保留 ./styles.css 相对路径。
6. 页面需要交互时，再引用独立 JavaScript 文件。
7. 在 index.html 的 header-actions 或页脚增加 ./guide.html 链接。
8. 如果所有页面都需要入口，同步修改 maintenance.html 和 404.html。
9. 发布后访问 https://imakerstudiocn.github.io/guide.html 测试。
10. 同时检查桌面和手机布局。

分类、类型和标签只需要编辑 resources.json。只有内容需要独立正文和独立网址时，才创建新的 HTML 页面。


十一、投稿与审核

网站提供两个独立页面：submission.html 供访客使用飞书公开表单投稿；admin.html 供管理者进入 Pages CMS，并查看投稿审核和发布流程。飞书表单地址来自 resources.json 中的 submitUrl。

更换飞书表单时，将新的公开填写地址写入 submitUrl。公开地址应包含 /share/base/form/。不要使用飞书内部多维表格地址。

调整现有表单的问题、顺序、说明和必填状态通常不会影响网站。删除并重建表单、关闭公开分享或生成新链接后，必须更新 submitUrl。

飞书公开表单字段：资源名称、资源链接、资源简介、内容分类、资源类型、标签，可选封面地址。

飞书管理字段：审核状态和同步状态。审核状态使用“待审核、已通过、不收录”，同步状态初始为空。

审核与自动同步流程：

1. 在飞书多维表格的普通数据视图查看投稿。
2. 检查链接是否可以打开。
3. 检查内容是否合法、是否重复。
4. 统一资源名称、说明、分类、类型和标签。
5. 将审核状态改为“已通过”。
6. GitHub Actions 每两小时读取全部“已通过且同步状态为空”的投稿。
7. 缺少必填字段的记录会被跳过，日志显示记录编号、投稿时间和中文字段名。
8. Actions 更新 resources.json 并创建普通 Pull Request。
9. Actions 将 PR 地址回写到同步状态，然后用专用令牌自动合并 PR 并删除临时分支。
10. GitHub Pages 自动更新网站。

自动合并失败时，PR 和地址会保留。检查令牌权限、分支保护或合并冲突并手动恢复；只有关闭 PR 且需要重新生成时才清空飞书同步状态。

GitHub Secrets：FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_MERGE_TOKEN。FEISHU_MERGE_TOKEN 应是仅授权当前仓库的细粒度 PAT，具有 Contents 和 Pull requests 读写权限。

GitHub Variables：
FEISHU_APP_TOKEN=TDDCbNKFUa1d7QsKX7vcrJinnhe
FEISHU_TABLE_ID=tblyK8zKwJX3F91g
FEISHU_VIEW_ID=vew3HOr4oa
FEISHU_SYNC_MODE=all

飞书自建应用需要多维表格读取和编辑权限，并且必须成为目标多维表格的协作者。

管理者在线编辑：先打开 https://imakerstudiocn.github.io/admin.html，再进入 Pages CMS；使用 GitHub 登录，授权当前仓库，在“资源管理”中修改并保存。

飞书原始数据表只向维护者开放。可以设置新增记录通知，避免漏看投稿。


十二、发布和回退

发布方法：

1. 将修改提交到 main 分支。
2. 打开仓库的 Actions 页面。
3. 查看 pages build and deployment。
4. 绿色对勾表示发布成功。
5. 发布后等待约 1 至 3 分钟。
6. 强制刷新网站。
7. 检查首页、修改过的资源、投稿按钮和站务手册。

项目只使用 GitHub Pages 内置工作流。不要添加第二套 Pages 部署工作流。

需要回退时，对错误提交使用 GitHub 的 Revert 功能生成反向提交。不要删除仓库，也不要强制重置 main 分支。


十三、常见故障

网站仍显示旧内容

先确认 Actions 发布成功，再使用 Ctrl + F5 强制刷新。macOS 使用 Command + Shift + R。

资源列表不显示

检查 resources.json 的英文逗号、英文双引号、大括号和方括号。任何一处 JSON 格式错误都可能导致整个资源列表无法加载。

出现重复分类或类型按钮

检查 category 和 type 是否使用了含义相同但文字不同的名称，并统一修改。

封面不显示

确认图片已提交，路径和文件名大小写一致。单条资源失败时检查 cover，全部失败时检查 defaultCover。

投稿按钮打不开

使用未登录飞书的浏览器测试，确认公开分享仍然开启，并检查 submitUrl 是否为公开填写地址。

Pages 部署失败

打开失败任务查看具体步骤。检查 Pages 来源是否被修改，是否存在重复工作流。构建成功但部署短暂失败时，可以等待后重新触发。


十四、安全边界

GitHub Pages 和仓库内容均为公开内容。
不要保存密码、令牌、内部链接或个人敏感信息。
网站没有账号、评论、数据库和权限系统。
只分享合法外部链接，不代理文件。
不要绕过付费、版权或访问限制。
新增图片前确认拥有使用权并压缩文件。
github.io 在中国大陆的访问速度和稳定性无法保证。
