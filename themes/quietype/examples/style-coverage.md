---
title: 样式覆盖检查
subtitle: 集中检查阅读与编辑元素
lang: zh-CN
toc-title: 目录
---

# 标题与正文

这是标题后的首段。中文正文与 English、数字 12345 混排时，应保持一致的阅读节奏。**粗体强调**、*斜体 emphasis*、~~删除内容~~、上标 $x^2$ 和行内代码 `render_markdown()` 都应能辨认。

这是普通正文段落。首段与后续段落都不使用首行缩进；段落之间靠适度留白区分。链接示例：[Typora 官方导出说明](https://support.typora.io/Export/)。[^note]

## 二级标题

用于组织章节内的主要观点。

### 三级标题

用于解释一个具体步骤。

#### 四级标题

仍保留完整的段前间距和标题语义。

##### 五级标题

通过字重与间距区分正文。

###### 六级标题

不使用难以阅读的极小字号。

# 列表与引用

- 第一层项目。
  - 第二层项目，检查缩进与符号。
    - 第三层项目，检查中英文 mixed content。
- 返回第一层。列表后的正文不应继承缩进。

1. 第一步，准备数据。
2. 第二步，处理数据。
   1. 检查输入。
   2. 记录结果。
3. 第三步，结束操作。

- [x] 已完成的任务。
- [ ] 尚未完成的任务。

> 这是引用段落。左侧标线用于提示这段内容来自另一个上下文。中文引用保持正体。
>
> 引用中可以出现**强调**、`inline_code` 和第二个段落。

引用结束后的正文应该恢复正常宽度和颜色。

# 代码的五种情况

## 标记语言的代码

```javascript
// 中文注释与 English comment 都应该清晰。
const options = { timeout: 1000, retries: 3 };

async function fetchConfig(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error("请求失败");
  return response.json();
}
```

```json
{
  "name": "中文配置",
  "enabled": true,
  "retry_count": 3,
  "labels": ["docs", "export"]
}
```

```sql
-- 统计每种状态的请求数量
SELECT status, COUNT(*) AS total
FROM requests
WHERE created_at >= '2026-01-01'
GROUP BY status;
```

## 未标注语言与空行

```
plain text  0123456789

    四个空格缩进，保留空行与中文。
```

## 长行与特殊字符

长行允许视觉换行，不能为了排版而插入额外的源码换行。下面的两行分别检查长标识符与符号转义。

```text
very_long_identifier_abcdefghijklmnopqrstuvwxyz_0123456789_abcdefghijklmnopqrstuvwxyz_0123456789_abcdefghijklmnopqrstuvwxyz_0123456789
<tag key="value"> & symbols: { } [ ] ( ) => != <= >= ; # $ % / \
```

# 表格、图片与公式

| 类型 | 左对齐文本 | 数值 |
|:--|:--|--:|
| 中文 | 普通正文，检查表格内边距 | 123.45 |
| 代码 | `some_value` | 7 |
| 强调 | **必须保留**，允许换行的较长说明文字 | 999 |

![插图和说明应留在相邻位置。](assets/retry-flow.png)

行内公式 $E = mc^2$ 与独立公式：

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

分隔线前的段落。

---

分隔线后的段落。

[^note]: 脚注文字使用较小字号；引用标记应上标显示。脚注编号需要保持可编辑。
