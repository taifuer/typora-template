# Typora Template：两套完整的 Word 导出样式

面向 Windows Typora 的 Word 导出。每套只需选择一个 `.docx` 样式参考文件，日常使用不需要 Python、Lua 或额外的代码高亮主题。

| 样式 | 文件 | 用途与排版 |
|---|---|---|
| **标准黑白** | [standard.docx](templates/standard.docx) | 常规文档。黑色正文、标题、链接与代码；宋体中文、Times New Roman 英文、黑体标题；规整的列表与细网格表格。 |
| **澄明 · 技术文档** | [tech.docx](templates/tech.docx) | 技术文章、开发说明。微软雅黑中文、Times New Roman 英文；黑色正文与标题；等宽代码、克制的语法配色、浅色代码块与引用标线。 |

两套默认文字均为纯黑色，包括各级标题、列表、表格、题注、脚注和页码；技术版仅代码语法高亮与链接使用配色。普通英文与数字统一为 Times New Roman，行内代码和代码块保留 Consolas 等宽字体，公式保留数学字体。

两套共用完整的文档结构：文档标题、副标题、作者、日期、各级标题、正文、首段、有序/无序/嵌套列表、表格、代码、引用、图片说明、脚注、链接、目录样式和页码。A4 纸张，四周约 22 mm 页边距。正文不自动首行缩进，标题不强制另起一页。

## 在 Windows Typora 中使用

1. 将 `templates` 中的两份文件复制到 Windows 的固定目录，例如“文档\Typora-Word”。
2. 打开 Typora 的 **偏好设置 → 导出 → Word (.docx)**。
3. 在 **样式参考 / Style Reference** 中选择其中一份 `.docx`。
4. 正常执行 **文件 → 导出 → Word (.docx)**。

切换风格时，更换样式参考文件即可。Typora 也支持添加导出预设，可分别建立“Word · 标准黑白”和“Word · 技术文档”两个项目。使用方式依据 [Typora 官方导出说明](https://support.typora.io/Export/#word-docx)。

当前项目位于 WSL。从 Windows 资源管理器可打开：

```text
\\wsl.localhost\Ubuntu-24.04\root\codes\toy\typora-word
```

建议复制到 Windows 本地目录后再打开模板或样例。本机验证时，Word 自动化直接打开 WSL 网络路径曾出现等待，本地文件打开正常。Typora 所使用的 Pandoc 已能导出 Word，无需为使用模板再安装 WSL 版 Pandoc。

## 先看效果

- 标准文档：[Word 样例](examples/standard.docx) · [PDF 预览](previews/standard.pdf) · [Markdown 原文](examples/standard.md)
- 技术文章：[Word 样例](examples/technical-blog.docx) · [PDF 预览](previews/technical-blog.pdf) · [Markdown 原文](examples/technical-blog.md)
- 完整元素检查：[Word 样例](examples/style-coverage.docx) · [PDF 预览](previews/style-coverage.pdf)

PDF 由本机 **Microsoft Word** 渲染，展示 Word 的实际排版。模板文件中自带的介绍文字不会进入你的导出文章。

## 代码和目录

代码块标注语言，例如 `python`、`javascript`、`json`、`sql` 或 `yaml`，技术版就会使用对应的语法配色。没有标注语言的代码仍有等宽字体和代码块排版。标准版保持黑色。所有代码仍是可复制、编辑的文本。

长代码允许自然跨页和视觉换行，模板不会向源码插入额外换行。相邻代码块可能形成连续的浅色区域；不同示例之间加一句说明，阅读会更清楚。

目录样式与目录生成是两件事。需要自动目录时，可在 Word 导出项的附加参数中设置 `--toc --toc-depth=3`；在 Word 中右键目录，选择“更新域/更新整个目录”。模板不会为每篇短文强制插入目录，也不会自动给标题加编号。

## 实际边界

样式参考负责字体、颜色和版面；Markdown 的结构仍由 Typora/Pandoc 转换。表格列宽会根据内容和导出器生成，超宽表格可能需要在 Word 中调整。Mermaid 渲染、复杂 HTML、特殊提示块和公式编号不属于纯样式模板的能力。该分工依据 [Pandoc 的样式参考机制](https://pandoc.org/MANUAL.html#option--reference-doc)。

字体采用常见 Windows 字体，模板不附带字体文件。其他电脑缺少字体时，Word 会替换字体，分页可能随之变化。

## 维护与验证

普通使用者无需执行脚本。维护者可用 Python 标准库和 Pandoc 重新构建两套模板：

```bash
python3 scripts/build.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe
python3 scripts/validate.py
python3 scripts/check_pagination.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe
```

也支持本地 Linux `pandoc` 或 Windows Python + `pandoc.exe`。`scripts/render-word.ps1` 用已安装的 Word 只读打开样例、更新目录并生成 PDF；它只处理传入的样例文件。示例插图已经提供，只有重新绘制插图才需要 Pillow。

实际验证环境与结果见 [验证记录](docs/validation.md)。
