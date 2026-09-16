#!/usr/bin/env python3
"""Check actual Word PDFs, not just the declared DOCX style properties.

Requires Poppler's pdffonts and pdftotext in PATH.
"""
import re
import subprocess
from xml.etree import ElementTree as ET

from build import ROOT


def command(*args):
    return subprocess.check_output(args, text=True, encoding='utf-8')


def main():
    for name, expected in [('standard', ['SimSun', 'SimHei', 'TimesNewRoman', 'Consolas']), ('technical-blog', ['MicrosoftYaHei', 'TimesNewRoman', 'Consolas']), ('style-coverage', ['Consolas'])]:
        path = ROOT / f'previews/{name}.pdf'
        fonts = command('pdffonts', str(path))
        assert all(font in fonts for font in expected), f'Font fallback in {name}'
        doc = ET.fromstring(command('pdftotext', '-bbox', str(path), '-'))
        for page in doc.findall('.//{*}page'):
            width = float(page.get('width'))
            for word in page.findall('.//{*}word'):
                assert float(word.get('xMin')) >= 18 and float(word.get('xMax')) <= width - 18, (name, word.text, 'outside page')
        if name == 'standard':
            assert 'English' in command('pdftotext', '-layout', str(path), '-'), 'Ordinary English words must stay whole'
        print(f'PASS Word PDF {name}: actual fonts and horizontal bounds')
    for name in ('standard', 'technical'):
        path = ROOT / f'build/pagination/previews/{name}.pdf'
        content = command('pdftotext', '-layout', str(path), '-')
        assert re.findall(r'row-(\d{2})', content) == [f'{i:02}' for i in range(1, 71)]
        assert re.findall(r'ITEM-(\d{2})', content) == [f'{i:02}' for i in range(1, 46)]
        assert 'END-OF-CONTENT' in content
        pages = [p for p in content.split('\f') if p.strip()]
        for page in pages:
            if 'ITEM-' in page:
                assert all(label in page for label in ('编号', '说明', '数量')), 'Missing continuation header'
        print(f'PASS pagination {name}: 70 code lines, 45 rows, repeated headers, final marker; {len(pages)} pages')


if __name__ == '__main__':
    main()
