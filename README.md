# IMakerStudioCN 资源簿

一个无需服务器、可直接部署到 GitHub Pages 的静态资源导航。

## 修改内容

- 站点名称和介绍：编辑 `index.html`
- 资源数据：编辑 `resources.json`
- 投稿地址：修改 `resources.json` 中的 `submitUrl`，当前使用飞书公开表单
- 颜色与排版：编辑 `styles.css`

`submitUrl` 建议配置为组织仓库的 GitHub Issue 表单地址。资源变更提交到默认分支后，GitHub Pages 会自动更新。

## GitHub Pages

本项目面向 `IMakerStudioCN` 组织根站，仓库应命名为：

```text
IMakerStudioCN.github.io
```

对应地址：

```text
https://imakerstudiocn.github.io/
```

如以后改用其他仓库名称，例如 `resources`，对应地址为：

```text
https://imakerstudiocn.github.io/resources/
```

本项目使用相对路径，两种部署方式均可正常工作。

仓库创建后，将本项目推送到 `main` 分支。GitHub Pages 的内置工作流会自动发布站点。
