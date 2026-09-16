#!/usr/bin/env python3
"""Exercise long code, tables, and the native-AST input used in Typora's pipeline."""
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from build import ROOT, native_path, run
from validate import NS, Q, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pandoc', required=True)
    args = parser.parse_args()
    folder = ROOT / 'build/pagination'
    folder.mkdir(parents=True, exist_ok=True)
    code = '\n'.join(f'values[{i:02}] = "row-{i:02}"  # 中文注释 {i:02}' for i in range(1, 71))
    rows = '\n'.join(f'| ITEM-{i:02} | 第 {i:02} 条记录，检查跨页与表头 | {i * 7} |' for i in range(1, 46))
    source = f'''---
title: 分页与内容保真检查
lang: zh-CN
---

# 长代码

代码之前的普通段落，不应产生大块空白。

```python
{code}
```

代码之后的普通段落，应该恢复正常排版。

# 跨页表格

| 编号 | 说明 | 数量 |
|:--|:--|--:|
{rows}

# 正常收尾

- 有序列表之前的无序项目。
  - 第二层项目。

1. 第一项。
2. 第二项。

末尾标记：END-OF-CONTENT。
'''
    (folder / 'pagination.md').write_text(source, encoding='utf-8')
    native = run(args.pandoc, ['-f', 'markdown', '-t', 'native', '-s'], source.encode())
    for name, template in [('standard', 'standard'), ('technical', 'tech')]:
        output = run(args.pandoc, ['-f', 'native', '-t', 'docx', '--reference-doc', native_path(ROOT / f'templates/{template}.docx', args.pandoc), '-o', '-'], native)
        path = folder / f'{name}.docx'
        path.write_bytes(output)
        with ZipFile(path) as z:
            doc = ET.fromstring(z.read('word/document.xml'))
        code_paragraphs = [p for p in doc.findall('.//w:p', NS) if p.find('w:pPr/w:pStyle', NS) is not None and p.find('w:pPr/w:pStyle', NS).get(Q + 'val') == 'SourceCode']
        assert len(code_paragraphs) == 1 and text(code_paragraphs[0]) == code
        assert len(doc.findall('.//w:tbl/w:tr', NS)) == 46
        assert 'END-OF-CONTENT' in text(doc)
        assert doc.find('.//w:numPr', NS) is not None
        print(f'PASS native AST -> {path.relative_to(ROOT)}: 70 exact code lines, 45 table rows, native lists')


if __name__ == '__main__':
    main()
