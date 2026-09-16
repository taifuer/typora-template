# 制作与验证记录

日期：2026-09-15。两套独立的样式参考文件：标准黑白、技术文档。本次补充表格整体居中、题注段内不分页、可选无题注图片居中配置，以及版本发布包规范。

## 验证环境与结果

| 项目 | 实际使用或结果 |
|---|---|
| 制作环境 | WSL Ubuntu 24.04，Python 3.12 标准库 |
| 导出引擎 | Windows 已安装的 Pandoc 2.18 |
| Word 渲染 | Microsoft Word 16.0，Build 16.0.20228 |
| 标准文档预览 | 2 页，实际字体含 SimSun、SimHei、Times New Roman、Consolas |
| 技术文章预览 | 3 页，实际字体含 Microsoft YaHei、Times New Roman、Consolas、Cambria Math |
| 元素覆盖预览 | 4 页，检查各级标题、目录、嵌套列表、任务列表、引用、代码、表格、图片、公式、脚注、链接与分隔线 |
| 分页检查 | 两套各 5 页，70 行代码、45 行表格，表头在续页重复，末尾标记完整 |
| 对齐检查 | 两套 × Markdown/native 输入 × 启用/不启用图片配置，共 8 份导出；图题、空题注图片、带链接图片、行内图片、显式样式和左/中/右列对齐均检查 |
| 内容保真 | 逐块比较 Markdown 与 DOCX 的代码文本，保留空行、缩进、特殊符号和中文 |
| 文件结构 | DOCX ZIP/XML 可解析；图片内嵌；公式为 OMML；脚注与页码域存在；无字体文件或宏 |
| PDF 检查 | 检查实际使用的字体和文字横向边界，普通英文单词不在中间断开 |

已用 Pandoc 的 Markdown 输入和 native AST 输入进行导出测试。后者覆盖 Typora 导出链路使用的输入形式，但不是一次完整的 Typora 界面自动化测试。没有修改 Typora 的偏好设置。可选图片配置另验证了非 DOCX 输出不受影响。

最终 PDF 由本机 Word 生成并检查。两份启用图片配置的 native 对齐样例均为 1 页，窄表与独立图片居中，行内图片跟随正文，显式指定为正文样式的图片保持左对齐。LibreOffice 24.2 用于早期对照，其字体与分页结果不能替代 Word 验证。未验证 WPS、macOS Word 或其他 Pandoc 版本。

## 两套样式的分工

标准版所有命名样式中的文字颜色都是 `000000`，链接保留下划线，代码保留等宽结构但不使用彩色高亮。标题通过字号和字重区分，无蓝色标题或装饰线。正文中文 12 pt 宋体、英文 Times New Roman，标题中文黑体。

技术版正文中文 11 pt 微软雅黑、英文 Times New Roman，代码 9.5 pt Consolas，中文注释使用微软雅黑。代码配色区分关键词、字符串、数字和注释，底色保持浅色。正文、各级标题、列表、表格、题注、脚注和页码均使用纯黑色，仅代码语法高亮与链接保留配色；引用有左侧标线。两套普通英文与数字均为 Times New Roman，代码保留等宽字体，公式保留数学字体。

两套均明确设置 Normal、Body Text、First Paragraph、Compact、Heading 1–9、Source Code、Verbatim Char、表格、脚注、题注、目录等相关样式，避免只改正文而漏掉标题后首段、列表或表格。列表由 Pandoc 输出为 Word 原生编号结构，不转换成手工符号。

## 关键实现依据

Typora 官方提供 Word 的“Style Reference”入口，且允许建立多个导出预设，所以不需要安装 Typora 插件。[Typora 导出文档](https://support.typora.io/Export/)

参考 DOCX 的样式和页面属性会用于新文档，参考文件的正文不会复制进去；编辑器的 CSS 不是 Word 的排版样式。[Pandoc reference-doc](https://pandoc.org/MANUAL.html#option--reference-doc)

代码段落、行内代码和语法标记分别定义样式。配色预先写进参考文件的语法标记字符样式，实测 Pandoc 2.18 会保留这些定义，因此最终每套只分发一个 DOCX，不要求用户配置 `.theme` 文件。[Pandoc DOCX writer 源码](https://github.com/jgm/pandoc/blob/main/src/Text/Pandoc/Writers/Docx.hs)

本机 Word 对照实验发现，文档默认设置会影响实际字体选择，即使字体属性显示为 Consolas，PDF 中仍可能出现替代字体。最终将文档默认值保持中性，把中英文字体显式放到命名样式中，并用 PDF 字体列表验证了结果。该结论来自本机对照实验，不表示所有 Word/Pandoc 版本都会出现同一问题。

正文按单词边界换行，代码允许在字符层面视觉折行。DOCX 中的原始代码文本不变；同时避免将长代码块设置为整段不可分页。[Open XML WordWrap 定义](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.wordwrap)

表格居中设置在 `Table` 样式的 `tblPr/jc` 中，单元格段落的 `jc` 继续由 Markdown 列对齐生成。带题注图片沿用 `CaptionedFigure`，图题使用 `ImageCaption`；空题注图片在 Pandoc 2.18 中使用 `BodyText`，可选 Lua 配置会把独立图片段落映射到 `Figure`。默认样式与可选配置分别验证，避免将可选配置的效果误报为纯 DOCX 模板的能力。专业排版取舍与字体依据见 [排版与字体说明](style-decisions.md)。

## 重现验证

先进入仓库的 `word/` 目录；以下命令和相对路径均以该目录为起点。

```bash
python3 scripts/build.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe
python3 scripts/validate.py
python3 scripts/check_layout.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe
python3 scripts/check_pagination.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe
```

在 Windows PowerShell 中，于 `word/` 目录运行：

```powershell
.\scripts\render-word.ps1 -CheckAlignment
.\scripts\render-word.ps1 -Sources @('build/pagination/standard.docx', 'build/pagination/technical.docx') -OutputDirectory 'build/pagination/previews'
.\scripts\render-word.ps1 -Sources @('build/layout/standard-native-centered.docx', 'build/layout/tech-native-centered.docx') -OutputDirectory 'build/layout/previews' -CheckAlignment
```

然后在 WSL 中检查实际字体、换行和分页结果（需要 Poppler）：

```bash
python3 scripts/validate_render.py
python3 scripts/render_previews.py --pandoc /mnt/c/Users/Administrator/AppData/Local/Pandoc/pandoc.exe --browser /path/to/chromium
```

`-CheckAlignment` 通过 Word 对象模型检查表格与图片/题注段落的实际对齐属性，不只读取 DOCX 中声明的样式。`check_layout.py` 的不启用配置样例保留为对照，不能将其中无题注图片也解释为已居中。

`render_previews.py` 生成 README 的四张对照图，需要 Pandoc、Chromium/Chrome 和 Poppler。将 `--browser` 换成本机浏览器可执行文件路径；Pandoc 和 Chromium 均在 PATH 中时，可省略这两个参数。

- 左侧 `*-markdown.png`：从 `examples/` 中的原文提取对应片段，由 Pandoc 转为 HTML，再用浏览器截图；这是 Markdown 渲染预览，不是 Typora 界面截图。标准版展示开头至“信息记录”表格，技术版展示“用代码表达边界”至指数退避公式。
- 右侧 PNG：由 `pdftoppm` 从已经验证的 Word PDF 中提取标准样例第 1 页、技术样例第 2 页，保留完整页面。Markdown 连续排版与 Word 分页不同，标准表格末行在 Word 第 2 页。

预览图宽 1200 px，保留在仓库中。截图用的 HTML 和浏览器临时文件放在被 Git 忽略的 `build/` 中，浏览器截图不需要额外的 Python 包。

如需生成发布包，在完整仓库根目录运行 `python3 scripts/package.py --version 0.2.1`。两个独立 ZIP 和 `SHA256SUMS` 写入被 Git 忽略的 `dist/`，具体操作见[发布说明](https://github.com/taifuer/typora-template/blob/main/docs/releasing.md)。

模板只负责排版，不承诺将任意 Mermaid、复杂 HTML、特殊提示块或公式交叉引用转换为原生 Word 内容。宽表格仍受列数和内容长度影响。字体缺失或阅读器不同也可能改变分页。
