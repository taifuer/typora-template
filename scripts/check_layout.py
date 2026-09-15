#!/usr/bin/env python3
"""Check figure/table alignment through Markdown and Typora-style native input."""
import argparse
from xml.etree import ElementTree as ET

from build import ROOT, native_path, run
from validate import NS, Q, read, styles, text, validate_layout_styles


SOURCE = '''---
title: 图片与表格对齐检查
lang: zh-CN
---

普通正文保持左对齐。

![带题注图片，说明应紧跟图片。](retry-flow.png){width=5cm}

![](retry-flow.png){width=5cm}

[![](retry-flow.png){width=5cm}](https://example.com/)

行内图片 ![](retry-flow.png){width=1cm} 跟随正文。

| 文本 | 类别 | 数量 |
|:--|:--:|--:|
| 左对齐 | 居中 | 12.34 |
| 内容 | 简短标签 | 567.89 |

: 表题在表格上方，各列保留各自的对齐方式。

::: {custom-style="Body Text"}
![](retry-flow.png){width=2cm}
:::

普通结尾保持左对齐。
'''


def check(path, filtered):
    parts = read(path)
    ss = styles(parts)
    validate_layout_styles(ss)
    doc = ET.fromstring(parts['word/document.xml'])
    image_paragraphs = [p for p in doc.findall('.//w:p', NS) if p.find('.//w:drawing', NS) is not None]
    expected = ['CaptionedFigure', 'Figure' if filtered else 'BodyText',
                'Figure' if filtered else 'BodyText', 'BodyText', 'BodyText']
    actual = [p.find('w:pPr/w:pStyle', NS).get(Q + 'val') for p in image_paragraphs]
    assert actual == expected, (path, actual)
    assert '行内图片' in text(image_paragraphs[3])
    assert doc.find('.//w:hyperlink', NS) is not None
    assert any(name.startswith('word/media/') for name in parts), 'Missing embedded images'
    for row in doc.findall('.//w:tbl/w:tr', NS):
        alignments = [cell.find('.//w:pPr/w:jc', NS).get(Q + 'val') for cell in row.findall('w:tc', NS)]
        assert alignments == ['left', 'center', 'right'], alignments
    for table in doc.findall('.//w:tbl', NS):
        direct = table.find('w:tblPr/w:jc', NS)
        assert direct is None or direct.get(Q + 'val') == 'center', 'Direct formatting overrides table style'
    print(f'PASS {path.relative_to(ROOT)}: image styles, inline image, explicit style, column alignment')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pandoc', required=True)
    args = parser.parse_args()
    folder = ROOT / 'build/layout'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'layout.md').write_text(SOURCE, encoding='utf-8')
    native = run(args.pandoc, ['-f', 'markdown', '-t', 'native', '-s'], SOURCE.encode())
    for name in ('standard', 'tech'):
        for reader, data in [('markdown', SOURCE.encode()), ('native', native)]:
            for filtered in (False, True):
                extra = ['--lua-filter', native_path(ROOT / 'filters/center-images.lua', args.pandoc)] if filtered else []
                result = run(args.pandoc, ['-f', reader, '-t', 'docx', '--reference-doc',
                    native_path(ROOT / f'templates/{name}.docx', args.pandoc), '--resource-path',
                    native_path(ROOT / 'examples/assets', args.pandoc), *extra, '-o', '-'], data)
                path = folder / f'{name}-{reader}{"-centered" if filtered else ""}.docx'
                path.write_bytes(result)
                check(path, filtered)
    baseline = run(args.pandoc, ['-f', 'markdown', '-t', 'html'], SOURCE.encode())
    filtered = run(args.pandoc, ['-f', 'markdown', '-t', 'html', '--lua-filter',
        native_path(ROOT / 'filters/center-images.lua', args.pandoc)], SOURCE.encode())
    assert baseline == filtered, 'Filter must not change other output formats'


if __name__ == '__main__':
    main()
