# 图片与表格标题

图表较多、需要在正文中引用时，标题有助于读者定位；上下文已经说明用途时，可以省略。下面两种写法按需选用。

## 普通 Markdown

图下写说明，表上写标题即可；换主题或导出 Word 时，也能保留这些文字。编号按文章需要手动填写。

![请求失败后，等待一段时间再发起下一次请求](assets/retry-flow.png)

图 1：一次重试的执行过程

**表 1：重试参数**

| 参数 | 含义 |
| --- | --- |
| 最大尝试次数 | 包含第一次请求 |
| 等待时间 | 两次请求之间的间隔 |

这些说明是普通段落，遵循正文排版。

## HTML 标题

需要统一的小字号灰色居中标题时，可使用标准 HTML 标签。图注使用 `figcaption`，表注使用 `caption`；不需要自定义类名。

<figure>
  <img src="assets/retry-flow.png" alt="请求失败后，等待一段时间再发起下一次请求">
  <figcaption>图 1：一次重试的执行过程</figcaption>
</figure>

<table>
  <caption>表 1：重试参数</caption>
  <thead><tr><th>参数</th><th>含义</th></tr></thead>
  <tbody>
    <tr><td>最大尝试次数</td><td>包含第一次请求</td></tr>
    <tr><td>等待时间</td><td>两次请求之间的间隔</td></tr>
  </tbody>
</table>

在源码模式下查看以上 HTML 写法。HTML 块内不混写 Markdown、不插入空行。此写法适合 Typora 阅读及 HTML/PDF 输出；导出 Word 时优先用上面的普通 Markdown 写法，Typora 不保证保留 HTML 结构。详见 [Typora HTML 说明](https://support.typora.io/HTML/)。

## 参考

- [Google：图片与图注](https://developers.google.com/style/images)——图注按需添加；图片替代文字 `alt` 和图注各有用途。
- [Cloudflare：表格标题](https://developers.cloudflare.com/style-guide/style-and-grammar/formatting/structure/tables/#table-captions)——多表相邻时可用编号区分，Markdown 表注写在表格前。
