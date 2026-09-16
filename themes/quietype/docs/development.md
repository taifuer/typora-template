# Quietype 开发与验证

浏览器检查包括：

- 420、860、1920px 窗口下的文章与元素布局，以及 1360px 下的四张预览；页面无横向溢出，图片加载正常，图表对齐保留。
- 实际 CodeMirror 的 Python、JavaScript、JSON、SQL 和纯文本渲染；插入并撤销后，代码内容与空行保持一致。
- Mermaid 流程图与时序图；自定义节点及默认节点的 `classDef` 配色得到保留。
- MathJax 行内公式、分式、上下标、对齐公式、矩阵和较宽公式；没有数学语法错误。
- Markdown 标记的展开与隐藏、源码模式标题和粗体、代码换行开关、宽表格滚动及字号偏好。

另外已在 Windows 的 Typora 1.12.4 窗口中逐项查看正文、标题、行内代码、Python/JavaScript 代码、引用、Mermaid 流程图与时序图、行内和块公式，并修正了实机出现的中文代码字体回退问题。截图中的正文背景为纯白。输入法、表格工具条、专注模式及原生 PDF 导出尚未专项验证；不同 Typora 版本的图形布局也可能略有差异。

在仓库的 `themes/quietype/` 目录运行以下命令重新生成预览，需要 Pandoc、Chromium/Chrome，以及本机 Typora 的 `resources` 目录：

```bash
python3 scripts/render_theme_preview.py \
  --pandoc /path/to/pandoc \
  --browser /path/to/chromium \
  --typora-resources /path/to/Typora/resources
```

在 WSL 中可额外传 `--font-dir /mnt/c/Windows/Fonts`，用本机微软雅黑与 Consolas 渲染预览。四张组件 PNG 写入 `previews/`，本地 HTML、渲染器副本与测量记录写入忽略的 `build/theme-preview/`。该脚本不会生成实机截图。Typora 自带的 CSS、字体和 JavaScript 只从本机读取，不打包分发；预览脚本目前适配本机 1.12.4 的资源布局。

Quietype 的全部主题样式写在 `quietype.css` 中，不导入其他主题 CSS，不引用外部字体或图片。预览仅加载 Typora 核心编辑器 CSS、渲染组件和 Quietype；脚本会拒绝主题中的 CSS 导入或外部资源引用。主题接口与文件命名参考 [Typora 主题开发文档](https://theme.typora.io/doc/Write-Custom-Theme/)。

排版参考我们自己的 [Quietype WordPress 主题](https://github.com/taifuer/quietype)与[技术文章实例](https://taifua.com/libvirt-event-handler-two.html)：使用清楚的标题层级、克制的行内代码与引用样式。Typora 版保留纯白背景和更紧凑的间距。
