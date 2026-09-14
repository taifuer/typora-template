#!/usr/bin/env python3
"""Validate real exports: style inheritance, content preservation and OOXML parts."""
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
Q = '{' + W + '}'


def read(path):
    with ZipFile(path) as z:
        assert z.testzip() is None, f'Invalid ZIP: {path}'
        parts = {n: z.read(n) for n in z.namelist()}
    for name, data in parts.items():
        if name.endswith(('.xml', '.rels')):
            ET.fromstring(data)
    return parts


def styles(parts):
    return {n.get(Q + 'styleId'): n for n in ET.fromstring(parts['word/styles.xml']).findall('w:style', NS)}


def text(element):
    result = []
    for node in element.iter():
        if node.tag == Q + 't':
            result.append(node.text or '')
        elif node.tag == Q + 'br':
            result.append('\n')
        elif node.tag == Q + 'tab':
            result.append('\t')
    return ''.join(result)


def validate_export(path, reference):
    parts = read(path)
    ss = styles(parts)
    doc = ET.fromstring(parts['word/document.xml'])
    for sid in ['Normal', 'BodyText', 'FirstParagraph', 'SourceCode', 'VerbatimChar', 'Table', 'BlockText', 'Footer', 'CommentTok', 'KeywordTok', 'NormalTok']:
        assert sid in ss, f'Missing style: {sid}'
        # Pandoc may change document language; compare the actual typography only.
        for tag in ('w:color', 'w:rFonts', 'w:sz', 'w:shd'):
            actual = ss[sid].find('w:rPr/' + tag, NS)
            expected = reference[sid].find('w:rPr/' + tag, NS)
            assert (actual.attrib if actual is not None else None) == (expected.attrib if expected is not None else None), (sid, tag)
    for level in range(1, 10):
        assert ss[f'Heading{level}'].find('w:pPr/w:keepNext', NS) is not None
    assert doc.find('.//w:sectPr/w:pgSz', NS).get(Q + 'w') == '11906'
    assert doc.find('.//w:sectPr/w:footerReference', NS) is not None
    footers = [data for name, data in parts.items() if re.match(r'word/footer[^/]*\.xml$', name)]
    assert footers and any(b'PAGE' in data for data in footers)
    assert not any('vbaProject' in name for name in parts)
    assert not any(name.endswith(('.ttf', '.odttf', '.ttc')) for name in parts), 'Do not redistribute fonts'

    source = path.with_suffix('.md')
    if source.exists():
        expected = re.findall(r'^```[^\n]*\n(.*?)\n```', source.read_text(), re.M | re.S)
        actual = [text(p) for p in doc.findall('.//w:p', NS) if (p.find('w:pPr/w:pStyle', NS) is not None and p.find('w:pPr/w:pStyle', NS).get(Q + 'val') == 'SourceCode')]
        assert actual == expected, f'Code content changed in {path.name}'
        assert '本页仅用于介绍模板' not in text(doc), 'Reference prose leaked into export'

    if path.stem != 'standard':
        assert doc.find('.//m:oMath', NS) is not None, 'Missing editable math'
        assert any(name.startswith('word/media/') for name in parts), 'Missing embedded figure'
    else:
        assert all(node.get(Q + 'val') == '000000' for s in ss.values() for node in s.findall('.//w:color', NS)), 'Standard text must be black'
    assert doc.find('.//w:footnoteReference', NS) is not None
    for table in doc.findall('.//w:tbl', NS):
        first = table.find('w:tr', NS)
        assert first.find('w:trPr/w:tblHeader', NS) is not None, 'Missing repeating header'
    print(f'PASS {path.relative_to(ROOT)}: styles, code text, semantic structure, header rows, page field')


def main():
    reference = styles(read(ROOT / 'templates/tech.docx'))
    for name in ('technical-blog', 'style-coverage'):
        validate_export(ROOT / f'examples/{name}.docx', reference)
    standard = styles(read(ROOT / 'templates/standard.docx'))
    validate_export(ROOT / 'examples/standard.docx', standard)


if __name__ == '__main__':
    main()
