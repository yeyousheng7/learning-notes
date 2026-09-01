# Learning Notes

基于 [MkDocs](https://www.mkdocs.org/) 和 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 构建的个人学习笔记站点。

## 本地预览

```bash
uv sync
uv run mkdocs serve
```

打开终端中显示的本地地址，即可实时预览。修改 `docs/` 中的 Markdown 文件后，页面会自动刷新。

## 构建静态站点

```bash
uv run mkdocs build --strict
```

构建结果位于 `site/` 目录。将该目录中的内容上传到 GitHub Pages、Cloudflare Pages、Netlify 等静态托管服务即可发布。

## GitHub Pages 自动部署

仓库包含 `.github/workflows/deploy-pages.yml`。Pull Request 会执行构建检查；推送到 `main` 分支后会自动：

1. 根据 `.python-version` 安装 Python；
2. 使用 `uv.lock` 同步锁定的依赖；
3. 以严格模式构建 MkDocs；
4. 将 `site/` 发布到 GitHub Pages。

首次使用时，在 GitHub 仓库中进入 **Settings → Pages**，将 **Build and deployment → Source** 设置为 **GitHub Actions**。之后推送到 `main`，或者在 **Actions** 页面手动运行工作流即可部署。

> `uv.lock` 必须提交到仓库；它用于保证本地与 CI 安装相同的依赖版本。

## 添加新笔记

1. 在 `docs/` 下创建 Markdown 文件；
2. 在 `mkdocs.yml` 的 `nav` 中添加对应导航项；
3. 本地预览并检查内容；
4. 使用严格模式构建，确认没有无效配置或链接警告。

## 目录结构

```text
.
├─ docs/                         # 笔记源文件
│  ├─ assets/stylesheets/        # 站点自定义样式
│  ├─ index.md                   # 首页
│  └─ AI Prompts.md              # AI 学习提示词库
├─ mkdocs.yml                    # 站点配置与导航
└─ pyproject.toml                # Python 依赖
```
