# Quietype 开发与验证

## 验证方式

日常样式调整优先用浏览器模拟，无需启动 Typora 窗口：脚本把 Markdown 转换为对应的元素结构，加载本机 Typora 的基础 CSS、CodeMirror、Mermaid、MathJax 和 Quietype，生成预览并测量布局。涉及编辑交互、应用导出流程或 Typora 版本变化时，再补充实机检查。

浏览器检查包括：

- 420、860、1920px 窗口下的文章与元素布局，以及 1360px 下的四张预览；页面无横向溢出，图片加载正常，图表对齐保留。
- 实际 CodeMirror 的 Python、JavaScript、JSON、SQL 和纯文本渲染；插入并撤销后，代码内容与空行保持一致。
- Mermaid 流程图与时序图；自定义节点及默认节点的 `classDef` 配色得到保留。
- MathJax 行内公式、分式、上下标、对齐公式、矩阵和较宽公式；没有数学语法错误。
- Markdown 标记的展开与隐藏、源码模式标题和粗体、代码换行开关、宽表格滚动及字号偏好。
- 17px、20px 两种字号，编辑与导出两种页面状态，屏幕与打印两种媒体下的 8 组脚注和表格检查：脚注字号一致、随正文缩放，实际显示颜色的对比度至少为 4.5:1；屏幕宽表可滚动，打印时滚动规则不再覆盖打印规则。
- Chromium 模拟的 6 页 PDF：检查 80 行代码与超长代码行、六列跨页表格、2 张 Mermaid、4 个公式及脚注；文本完整、表头重复正常，并逐页查看了渲染结果。这项检查不经过 Typora 原生导出流程。
- HTML 图注与表注：经过本机 Typora HTML 过滤器后，在 420、860px 窗口和 17px、20px 字号下检查编辑/导出结构，共 8 组；标题字号与颜色一致、居中且无横向溢出，普通 Markdown 说明仍保持正文样式。

实机已在 Windows Typora 1.12.4 中查看正文、标题、行内代码、Python/JavaScript 代码、引用、Mermaid 流程图与时序图、行内和块公式，并修正了中文代码字体回退问题；普通表格进入编辑状态后，工具条能完整显示。README 的两张主预览来自实机，正文背景为纯白。

模拟不能替代中文输入法组合输入、原生表格行列操作、专注模式的光标跟随和 Typora 原生 PDF 导出检查，这些项目尚未完成专项验证。打印规则检查也不代表任意宽表都能缩入纸张；过长且不可换行的内容仍需要调整。不同 Typora 版本的解析及图形布局可能略有差异。

## 生成预览

在仓库的 `themes/quietype/` 目录运行以下命令重新生成预览，需要 Pandoc、Chromium/Chrome，以及本机 Typora 的 `resources` 目录：

```bash
python3 scripts/render_theme_preview.py \
  --pandoc /path/to/pandoc \
  --browser /path/to/chromium \
  --typora-resources /path/to/Typora/resources
```

在 WSL 中可额外传 `--font-dir /mnt/c/Windows/Fonts`，用本机微软雅黑与 Consolas 渲染预览。四张组件 PNG 写入 `previews/`，本地 HTML、渲染器副本与测量记录写入忽略的 `build/theme-preview/`。该脚本不会生成实机截图。Typora 自带的 CSS、字体和 JavaScript 只从本机读取，不打包分发；预览脚本目前适配本机 1.12.4 的资源布局。

## 脚注与打印回归检查

在 Linux 或 WSL 中运行，需要 Python 3、Chromium/Chrome 和本机 Typora 的资源目录，不需要额外 Python 包：

```bash
python3 scripts/check_theme_details.py \
  --browser /path/to/chromium \
  --typora-resources /path/to/Typora/resources
```

该检查通过浏览器调试协议实际切换屏幕和打印媒体，不用手工覆盖 CSS 来模拟打印。结果写入 `build/theme-details/check.json`；可传 `--theme /path/to/older.css` 比较旧样式。本次修改前有 36 项断言失败，修改后 8 组检查全部通过。

## 设计约定

Quietype 的全部主题样式写在 `quietype.css` 中，不导入其他主题 CSS，不引用外部字体或图片。预览仅加载 Typora 核心编辑器 CSS、渲染组件和 Quietype；脚本会拒绝主题中的 CSS 导入或外部资源引用。主题接口与文件命名参考 [Typora 主题开发文档](https://theme.typora.io/doc/Write-Custom-Theme/)。

图表标题按需添加，见[写法示例](../examples/quietype-captions.md)。主题为标准 HTML `figcaption` 和 `caption` 提供样式；不从图片 `alt` 自动生成图注，也不将相邻斜体段落识别为标题。这样可以保留普通 Markdown 的含义，同时避免依赖 Typora 编辑预览会过滤的自定义类名。相关限制见 [Typora HTML 说明](https://support.typora.io/HTML/)。

排版参考我们自己的 [Quietype WordPress 主题](https://github.com/taifuer/quietype)与[技术文章实例](https://taifua.com/libvirt-event-handler-two.html)：使用清楚的标题层级、克制的行内代码与引用样式。Typora 版保留纯白背景和更紧凑的间距。
