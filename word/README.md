# Typora Word 导出模板

两套面向 Windows Typora 的 Word 样式。选择一个参考 DOCX，即可导出带标题、代码、列表、图表和页码的文档。

| 模板 | 适用场景 | 样式 |
|---|---|---|
| **标准黑白** | 常规文档、报告、打印 | 宋体正文、黑体标题、黑白代码、细网格表格 |
| **技术文档** | 技术文章、开发说明 | 微软雅黑正文、代码高亮、浅色引用与表格 |

## 使用

下载并解压 [Word 模板包](https://github.com/taifuer/typora-template/releases/download/v0.2.2/typora-word-0.2.2.zip)，内含 `standard.docx` 和 `tech.docx` 两份模板。

1. 将选中的 DOCX 放到 Windows 本地固定目录。
2. 在 Typora **偏好设置 → 导出 → Word (.docx) → 样式参考**中选择模板。
3. 执行 **文件 → 导出 → Word (.docx)**。切换风格时更换样式参考即可。

参考文件里的介绍文字不会出现在导出文档中。

### 说明

- **图表**：表格整体和带题注图片默认居中；表内文字遵循 Markdown 列对齐。无题注图片可在 Word 中居中，也可配置[自动居中过滤器](docs/style-decisions.md#可选无题注图片自动居中)。
- **代码**：技术版按代码块语言高亮，标准版保持黑白；代码文本可编辑，空行和缩进得到保留。
- **字体**：普通英文使用 Times New Roman，代码使用 Windows 自带的 Consolas。其他系统缺少字体时，分页可能变化。
- **版面**：A4 纸张，正文不自动首行缩进；可用 PDF 分享固定版式。

图片、目录及字体设置见[排版说明](docs/style-decisions.md)。

## 演示

左侧是 Markdown 渲染预览，右侧是对应的 Word 导出效果。点击图片查看大图。

### 标准黑白

| Markdown | Word · 第 1 页 |
|:---:|:---:|
| [![标准黑白 Markdown 预览](previews/standard-markdown.png)](previews/standard-markdown.png) | [![标准黑白 Word 导出](previews/standard.png)](previews/standard.png) |

### 技术文档

| Markdown | Word · 第 2 页 |
|:---:|:---:|
| [![技术文档 Markdown 预览](previews/technical-blog-markdown.png)](previews/technical-blog-markdown.png) | [![技术文档 Word 导出](previews/technical-blog.png)](previews/technical-blog.png) |

完整样例：

- 标准黑白：[Markdown](examples/standard.md) · [Word](examples/standard.docx) · [PDF](previews/standard.pdf)
- 技术文档：[Markdown](examples/technical-blog.md) · [Word](examples/technical-blog.docx) · [PDF](previews/technical-blog.pdf)
- 元素覆盖：[Markdown](examples/style-coverage.md) · [Word](examples/style-coverage.docx) · [PDF](previews/style-coverage.pdf)

## 开发者

构建脚本位于 `scripts/`，环境和验证步骤见[构建与验证](docs/validation.md)。发布流程见[仓库发布文档](https://github.com/taifuer/typora-template/blob/main/docs/releasing.md)。
