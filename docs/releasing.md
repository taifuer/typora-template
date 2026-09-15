# 文件布局与发布

## 目录职责

| 目录 | 内容 | 是否纳入 Git |
|---|---|---|
| `templates/` | 两份可直接使用的参考 DOCX，是项目的主要交付物 | 是 |
| `filters/` | 可选图片居中配置 | 是 |
| `examples/` | Markdown 原文、插图，以及三份已验证的 Word 样例 | 是 |
| `previews/` | 三份 Word PDF，以及 README 使用的四张 Markdown / Word 对照图 | 是 |
| `scripts/`、`docs/` | 构建、验证、打包脚本与说明 | 是 |
| `build/` | 分页检查、对齐检查与临时实验结果 | 否 |
| `dist/` | 本地生成的版本压缩包与 SHA-256 校验文件 | 否 |

模板和少量效果样例留在仓库，便于直接下载、查看和核对。ZIP 与这些文件重复，统一作为 GitHub Release 附件分发。GitHub 官方也将 Releases 作为打包软件、发布说明和二进制文件的分发入口。[GitHub Releases 说明](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## 准备发布文件

先按 [验证记录](validation.md) 重建模板和 Word 样例、重新渲染 PDF，并完成内容、对齐和分页检查。再按其中的预览命令运行 `scripts/render_previews.py`，更新 README 的四张对照图。模板、样例、PDF 和预览图应在同一次修改中更新。

例如准备版本 `0.1.0` 时，在仓库根目录执行：

```bash
python3 scripts/package.py --version 0.1.0
```

生成：

```text
dist/typora-word-styles-0.1.0.zip
dist/typora-word-styles-0.1.0.zip.sha256
```

不传版本时生成 `dev` 包，供本地检查。`--version v0.1.0` 与 `--version 0.1.0` 等效。打包采用明确的文件清单，缺少输入会报错，避免把 Word 锁文件、缓存或实验文件带入发布包。包内含同名顶层目录，解压后保留相对链接。

ZIP 的时间戳和权限固定：输入文件字节相同时，重复打包的 SHA-256 相同。重建 DOCX 或重新渲染 PDF 仍可能改变文件内部时间戳，因此不承诺整个 Word 构建流程逐字节可重现。

在 `dist/` 中核对下载完整性：

```bash
sha256sum -c typora-word-styles-0.1.0.zip.sha256
```

Windows PowerShell 可用 `Get-FileHash .\typora-word-styles-0.1.0.zip -Algorithm SHA256`，与 `.sha256` 文件第一列比较。

## 创建 GitHub Release

版本标签使用 `v主版本.次版本.修订号`，例如 `v0.1.0`。发布前将已验证的模板、样例和文档提交到该版本对应的提交；Git 作者与 Codex 署名遵循仓库 `AGENTS.md`。

在 GitHub 的 [Releases](https://github.com/taifuer/typora-template/releases) 页面创建 Release，选择对应标签，填写中文版本说明，并上传：

- `templates/standard.docx`
- `templates/tech.docx`
- `dist/typora-word-styles-版本号.zip`
- `dist/typora-word-styles-版本号.zip.sha256`

版本说明写明样式变化、适用的 Typora/Pandoc 环境、验证结果，以及无题注图片的可选配置。仓库自动提供的 Source code ZIP 是源码快照；命名为 `typora-word-styles-版本号.zip` 的附件是整理后的使用包。

发布后的相同版本附件保持固定。修复模板或更新 PDF 时使用新版本号。打包脚本只生成本地文件，不会创建标签、推送代码或发布 Release。
