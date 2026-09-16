# 打包与发布

一个 Release 发布两个独立使用包，使用同一个版本号。

| 附件 | 内容 |
|---|---|
| `typora-word-版本号.zip` | 仅包含 `standard.docx` 和 `tech.docx` |
| `quietype-版本号.zip` | 仅包含 `quietype.css` |
| `SHA256SUMS` | 两个 ZIP 的 SHA-256 校验值 |

## 仓库布局

- `word/`：Word 导出模板及相关资料。
- `themes/quietype/`：阅读主题及相关资料。
- `scripts/package.py`：统一打包入口。
- 各目录的 `build/`：本地验证和渲染中间文件，不纳入 Git。
- 根目录 `dist/`：发布附件，不纳入 Git。

两个 ZIP 的根目录直接放置可安装文件。说明、样例、预览、可选图片配置和开发脚本保留在仓库中，不放入下载包。

Quietype 只需安装 `quietype.css`，不导入或依赖其他主题 CSS。Typora 自带的编辑器、代码高亮、公式和图形渲染功能由应用提供，无需额外安装主题、字体或脚本。开发时的浏览器预览会读取本机 Typora 的运行时资源，这些资源不属于主题依赖，也不随包分发。

## 发布前检查

1. 修改 Word 样式时，按 [Word 构建与验证](../word/docs/validation.md)更新模板、样例和预览，并完成内容、字体、对齐和分页检查。
2. 修改主题样式时，按 [Quietype 开发与验证](../themes/quietype/docs/development.md)更新预览，检查真实 Typora 窗口。
3. 更新三个 README 的介绍、演示及使用说明，检查图片和链接；下载包链接使用本次版本号。
4. 准备中文发布说明，写清两部分各自的变化。Git 作者和提交署名遵循 `AGENTS.md`。

只修改文档和打包时，复查链接、包内文件和校验值即可，无需重建已验证的 DOCX、PDF 或主题截图。

## 生成附件

在仓库根目录执行：

```bash
python3 scripts/package.py --version 0.2.1
```

生成：

```text
dist/
├── typora-word-0.2.1.zip
├── quietype-0.2.1.zip
└── SHA256SUMS
```

不传版本号时生成 `dev` 包。每次运行都会重新生成 `SHA256SUMS`，只列出本次版本的两个 ZIP。打包采用明确的文件清单和固定 ZIP 元数据；输入字节相同时，ZIP 的校验值相同。上传时使用下面的明确文件清单，避免带入 `dist/` 中可能存在的旧附件。

在 `dist/` 目录检查：

```bash
sha256sum -c SHA256SUMS
```

Windows 可用 PowerShell 的 `Get-FileHash` 获取 SHA-256，并与 `SHA256SUMS` 中对应文件的记录比较。

## 发布 Release

将最终提交推送后，在 [GitHub Releases](https://github.com/taifuer/typora-template/releases) 创建对应版本，标签指向已验证的提交，上传上面的三个附件。以下以 `v0.2.1` 为例，发布新版本时替换版本号。

也可先创建草稿并上传附件，检查后发布：

```bash
gh release create v0.2.1 --draft --target COMMIT_SHA \
  --title 'v0.2.1 · Quietype 与 Word 导出模板' \
  --notes-file /path/to/release-notes.md \
  dist/typora-word-0.2.1.zip dist/quietype-0.2.1.zip \
  dist/SHA256SUMS
gh release edit v0.2.1 --draft=false --latest
```

发布后下载附件重新校验，并确认版本标签指向预期提交。正式附件保持固定；后续更新使用新版本号。GitHub 自动提供的 Source code 是完整仓库快照，两个命名 ZIP 仅包含各自的可安装文件。

## 版本保留

当前只保留最新的 `v0.2.1` Release。后续新版本发布并完成下载校验后，清理被替代的旧 Release 及附件，保留全部 Git 标签和提交历史。遇到较大的样式或兼容性调整时，可暂时保留上一稳定版，最多保留两个 Release，方便回退。

删除旧 Release 会使其附件下载链接失效，因此先更新 README 下载入口，并确认旧附件已备份。清理时只删除 Release，不使用 `--cleanup-tag`，不移动或删除历史标签。
