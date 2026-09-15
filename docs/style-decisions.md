# 排版与字体说明

评估日期：2026-09-15。适用场景是 Windows Typora 导出的常规报告和技术文章。

## 图片与表格为什么默认居中

居中能让较窄的图表与正文形成清楚的区分，也与当前模板居中的题注保持一致，因此本项目采用这一默认值。它是项目的设计选择，不代表通用投稿标准。专业模板有各自的要求，例如 IEEE IAS 将图题放在图片下方居中、表题放在表格上方居中，并明确具体会议要求优先。[IEEE IAS 排版说明](https://ewh.ieee.org/soc/ias/pub-dept/style.html)

需要区分两种对齐：

| 对象 | 默认做法 | 理由 |
|---|---|---|
| 独立图片、整张表格 | 在正文区域居中 | 窄图表与题注位置一致；满宽表格的视觉变化很小 |
| 表格中的说明文字 | 默认左对齐，尊重 Markdown 设置 | 多行说明容易从同一起点阅读 |
| 数值列 | 示例使用右对齐 | 方便按位比较；需要小数点对齐时可在 Word 中进一步设置 |
| 简短标签列 | 按需居中 | 标签长度较短时容易扫描 |
| 图题、表题 | 居中，保持整段；图下、表上 | 避免题注自身跨页；图与下方题注、表题与下方表格保持相邻 |
| 正文、行内图片 | 左对齐，行内图片随文字 | 保持连续阅读的起点 |

文字左对齐、数字右对齐，以及列标题与列内容保持一致，参考了澳大利亚政府 Style Manual。它也建议统一表格的字体、边线和配色，并以线条或隔行底色帮助阅读长表。[Style Manual：Tables](https://www.stylemanual.gov.au/structuring-content/tables)

标准版继续使用细网格表格；技术版保留较少的竖线、浅色表头和隔行底色。两者分别服务于常规文档和技术文章，没有统一改成论文式三线表。

## 图片识别的边界

参考 DOCX 控制命名样式，不能根据段落是否含图片来改变正文样式。Pandoc 的 `implicit_figures` 会把独占一段、带说明文字的图片变为带题注的图；空说明图片不属于这一规则。[Pandoc：图片与题注](https://pandoc.org/MANUAL.html#extension-implicit_figures)

在本次 Pandoc 2.18 验证中，前者使用 `CaptionedFigure`，后者使用 `BodyText`。所以模板保留 `Figure` / `CaptionedFigure` 居中，并提供可选的 `filters/center-images.lua`，将独立的普通图片段落映射到已有的 `Figure` 样式。文字、图片尺寸、链接和题注内容保持不变。该配置同时支持本次测试的 Markdown 和 native AST 输入；不处理表格单元格、紧凑列表中的 Plain 内容或显式设置了 `custom-style` 的容器。

这是导出前的样式映射，导出的 DOCX 不需要宏，也不需要再运行后处理脚本。Lua 由 Pandoc 内置运行。[Pandoc：自定义样式](https://pandoc.org/MANUAL.html#custom-styles)、[Lua filters](https://pandoc.org/lua-filters.html)

### 可选：无题注图片自动居中

日常使用直接选择 DOCX 模板即可。若希望无题注的 `![](flow.png)` 也自动居中，可进行一次性配置：

1. 将 [center-images.lua](../filters/center-images.lua) 复制到模板所在的固定目录。
2. 在 Typora 的 Word 导出设置中，为附加参数添加以下内容，并换成实际的绝对路径：

   ```text
   --lua-filter="C:\Users\你的用户名\Documents\Typora-Word\center-images.lua"
   ```

Pandoc 自带 Lua，无需单独安装。该配置只对 Word 导出生效；与文字同行的图片、表格单元格和显式指定段落样式的内容保留原有对齐。也可不配置，导出后直接在 Word 中将图片所在段落居中。

## 代码、目录与导出范围

技术版代码块标注 `python`、`javascript`、`json` 等语言后使用语法配色，未标注语言的代码保留等宽排版。长代码允许自然跨页和视觉换行，不插入额外源码换行；相邻示例间加一句说明可分隔连续的浅色区域。

需要目录时，可在 Word 导出项的附加参数中设置 `--toc --toc-depth=3`；导出后在 Word 中右键目录，选择“更新域/更新整个目录”。模板不会自动插入目录或给标题编号。

样式参考控制字体、颜色和版面，内容结构由 Typora/Pandoc 转换。超宽表格可能需要在 Word 中调整列宽；Mermaid、复杂 HTML、特殊提示块和公式编号不属于纯样式模板的能力。[Typora 导出说明](https://support.typora.io/Export/)、[Pandoc 样式参考](https://pandoc.org/MANUAL.html#option--reference-doc)

## 为什么保留 Consolas

Consolas 是微软为编程和等宽文本设计的字体，随 Windows Vista 至 Windows 11 的多个版本提供，Windows 11 字体清单列出了常规、粗体、斜体和粗斜体。因此，面向 Windows 用户时，没有必要因担心额外安装而更换。[Consolas 官方说明](https://learn.microsoft.com/en-us/typography/font-list/consolas)、[Windows 11 字体清单](https://learn.microsoft.com/en-us/typography/fonts/windows_11_font_list)

| 候选 | 本项目的取舍 |
|---|---|
| Consolas | 保留为代码字体。等宽、面向代码设计，已在本机 Word PDF 中验证实际使用。 |
| Courier New | Windows 11 也提供这一等宽字体，但更换它不能消除中文字体和跨系统分页差异；当前没有足够收益。 |
| Times New Roman / Arial | 适合普通文字；比例字宽不适合依靠等宽字符保持代码缩进和列对齐。 |

普通英文继续使用 Times New Roman。代码中文注释仍使用微软雅黑，公式保留数学字体。模板不嵌入或分发字体。对缺少字体的阅读环境，优先提供已经渲染好的 PDF，而不是承诺 DOCX 在所有系统上完全一致。

## 其他样式检查

- 保留正文与标题的纯黑色，以及技术版克制的代码高亮。
- 保留标题与后文同页、正文孤行控制、代码自然跨页和长表重复表头。
- 为题注补上段内不分页，避免长题注被截成两页；不将整篇代码或整张长表强制锁在一页。
- 保留现有字号、行距和 A4 页边距；本次 Word 渲染中三份样例仍为 2、3、4 页。
