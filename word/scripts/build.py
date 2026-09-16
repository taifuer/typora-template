#!/usr/bin/env python3
"""Build a self-contained Pandoc reference DOCX. Python standard library only.

The input reference always comes from the selected Pandoc, preserving its package
structure. Exported user documents are never postprocessed by this script.
"""

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
from xml.dom import minidom
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FONT = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Microsoft YaHei" w:cs="Times New Roman"/>'
MONO = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="Microsoft YaHei" w:cs="Consolas" w:hint="default"/>'
LANG = '<w:lang w:val="en-US" w:eastAsia="zh-CN"/>'
INK, LINK = "000000", "215E78"


def fragment(xml):
    return minidom.parseString(f'<root xmlns:w="{W}" xmlns:r="{R}">{xml}</root>')


def children(node, tag):
    return [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE and n.tagName == tag]


def append_xml(doc, node, xml):
    for child in list(fragment(xml).documentElement.childNodes):
        node.appendChild(doc.importNode(child, True))


def replace_child(doc, parent, tag, xml):
    matches = children(parent, tag)
    new = doc.importNode(fragment(xml).documentElement.firstChild, True)
    if matches:
        parent.replaceChild(new, matches[0])
        for duplicate in matches[1:]:
            parent.removeChild(duplicate)
    else:
        parent.appendChild(new)


def run(pandoc, args, data=None):
    p = subprocess.run([pandoc, *args], input=data, capture_output=True, check=True)
    if p.stderr:
        print(p.stderr.decode("utf-8", errors="replace").strip())
    return p.stdout


def native_path(path, pandoc):
    path = str(Path(path).resolve())
    if os.name != "nt" and pandoc.lower().endswith(".exe"):
        return subprocess.check_output(["wslpath", "-w", path], text=True, encoding='utf-8').strip()
    return path


def size(halfpoints):
    return f'<w:sz w:val="{halfpoints}"/><w:szCs w:val="{halfpoints}"/>'


def spacing(before=0, after=120, line=360, rule="atLeast"):
    return f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="{rule}"/>'


def color(value):
    return f'<w:color w:val="{value}"/>'


def make_styles(base, token_names):
    doc = minidom.parseString(base)
    root = doc.documentElement
    # Keep document defaults neutral. Actual typography belongs to named styles.
    # In Word, explicit CJK defaults combined with Pandoc 2.18's global language
    # rewrite can make Latin text use the CJK font despite correct style fonts.
    defaults = f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorEastAsia" w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi"/>{size(22)}</w:rPr></w:rPrDefault><w:pPrDefault/></w:docDefaults>'
    replace_child(doc, root, "w:docDefaults", defaults)

    def style(sid, name, kind="paragraph", based="Normal", p="", r="", tail="", default=False):
        old = next((n for n in children(root, "w:style") if n.getAttribute("w:styleId") == sid), None)
        xml = f'<w:style w:type="{kind}" w:styleId="{sid}"' + (' w:default="1"' if default else '') + '>'
        xml += f'<w:name w:val="{escape(name)}"/>'
        if based:
            xml += f'<w:basedOn w:val="{based}"/>'
        if kind == "paragraph":
            xml += '<w:next w:val="BodyText"/>'
        xml += '<w:qFormat/>'
        if p:
            xml += f'<w:pPr>{p}</w:pPr>'
        if r:
            xml += f'<w:rPr>{r}</w:rPr>'
        xml += tail + '</w:style>'
        new = doc.importNode(fragment(xml).documentElement.firstChild, True)
        if old is not None:
            root.replaceChild(new, old)
        else:
            root.appendChild(new)

    plain = '<w:keepNext w:val="0"/><w:keepLines w:val="0"/><w:widowControl/><w:snapToGrid w:val="0"/>'
    # Do not set a Normal-level indent: lists supply their own numbering indents.
    style("Normal", "Normal", based=None, p=plain + '<w:wordWrap w:val="1"/>' + spacing() + '<w:jc w:val="left"/>', r=FONT + color(INK) + size(22) + LANG, default=True)
    for sid, name in [("BodyText", "Body Text"), ("FirstParagraph", "First Paragraph")]:
        style(sid, name, p=spacing(after=140) + '<w:ind w:firstLine="0"/>')
    style("Compact", "Compact", p=spacing(after=60, line=300))
    style("Title", "Title", p='<w:keepNext/><w:keepLines/>' + spacing(after=180, line=288), r=FONT + '<w:b/><w:bCs/>' + color(INK) + size(50))
    style("Subtitle", "Subtitle", p='<w:keepNext/>' + spacing(after=220, line=300), r=color(INK) + size(24))
    style("Author", "Author", p='<w:keepNext/>' + spacing(after=40, line=276), r=color(INK) + size(19))
    style("Date", "Date", p=spacing(after=280, line=276), r=color(INK) + size(18))
    for level, points in enumerate([36, 29, 25, 23, 22, 22, 22, 22, 22], 1):
        border = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="7" w:color="DCE5EB"/></w:pBdr>' if level == 1 else ''
        p = '<w:keepNext/><w:keepLines/>' + border + spacing(before=360 if level < 3 else 240, after=140, line=288) + f'<w:outlineLvl w:val="{level - 1}"/>'
        style(f"Heading{level}", f"Heading {level}", p=p, r=FONT + '<w:b/><w:bCs/><w:i w:val="0"/>' + color(INK) + size(points))

    code_border = '<w:pBdr>' + ''.join(f'<w:{side} w:val="single" w:sz="4" w:space="7" w:color="DFE5EB"/>' for side in ("top", "left", "bottom", "right")) + '</w:pBdr>'
    code_p = plain + code_border + '<w:shd w:val="clear" w:fill="F3F6F8"/><w:wordWrap w:val="0"/><w:autoSpaceDE w:val="0"/><w:autoSpaceDN w:val="0"/>' + spacing(before=160, after=180, line=280) + '<w:ind w:left="160" w:right="160" w:firstLine="0"/>'
    style("SourceCode", "Source Code", p=code_p, r=MONO + color(INK) + size(19) + '<w:noProof/>' + LANG)
    # No background on VerbatimChar: it is also inherited by code token styles.
    style("VerbatimChar", "Verbatim Char", kind="character", based="DefaultParagraphFont", r=MONO + size(19) + '<w:noProof/>' + LANG)
    palette = {
        "Keyword": "7C3F8C", "ControlFlow": "7C3F8C", "Import": "7C3F8C",
        "DataType": "176681", "Function": "215E78", "BuiltIn": "215E78",
        "String": "276749", "Char": "276749", "SpecialChar": "276749",
        "VerbatimString": "276749", "SpecialString": "276749",
        "DecVal": "9B4D14", "BaseN": "9B4D14", "Float": "9B4D14", "Constant": "9B4D14",
        "Comment": "5B6978", "Documentation": "5B6978", "CommentVar": "5B6978",
        "Annotation": "5B6978", "Information": "5B6978", "Preprocessor": "7C3F8C",
        "Attribute": "176681", "Operator": "465567", "Variable": INK,
        "Error": "A12F39", "Alert": "A12F39", "Warning": "8A541E",
    }
    for token in sorted(set(token_names) | {"Normal"}):
        strong = token in {"Keyword", "ControlFlow", "Error", "Alert"}
        r = MONO + f'<w:b w:val="{int(strong)}"/><w:bCs w:val="{int(strong)}"/><w:i w:val="0"/><w:iCs w:val="0"/>' + color(palette.get(token, INK)) + '<w:shd w:val="clear" w:fill="auto"/>'
        style(token + "Tok", token + "Tok", kind="character", based="VerbatimChar", r=r)

    quote_p = '<w:pBdr><w:left w:val="single" w:sz="18" w:space="9" w:color="81AAB9"/></w:pBdr>' + spacing(before=120, after=160, line=312) + '<w:ind w:left="280" w:right="140" w:firstLine="0"/>'
    style("BlockText", "Block Text", p=quote_p, r=color(INK) + '<w:i w:val="0"/><w:iCs w:val="0"/>')
    style("FootnoteBlockText", "Footnote Block Text", based="BlockText", r=size(18))
    style("FootnoteText", "Footnote Text", p=spacing(after=60, line=288), r=size(18) + color(INK))
    style("FootnoteReference", "Footnote Reference", kind="character", based="DefaultParagraphFont", r=color(INK) + '<w:vertAlign w:val="superscript"/>')
    style("Hyperlink", "Hyperlink", kind="character", based="DefaultParagraphFont", r=color(LINK) + '<w:u w:val="single"/>')
    style("SectionNumber", "Section Number", kind="character", based="DefaultParagraphFont", r=color(INK))
    style("BodyTextChar", "Body Text Char", kind="character", based="DefaultParagraphFont", r=FONT)
    style("DefinitionTerm", "Definition Term", p='<w:keepNext/>' + spacing(before=120, after=60), r='<w:b/><w:bCs/>')
    style("Definition", "Definition", p=spacing(after=140) + '<w:ind w:left="360"/>')
    for sid, name in [("AbstractTitle", "Abstract Title"), ("TOCHeading", "TOC Heading")]:
        style(sid, name, p='<w:keepNext/>' + spacing(before=200, after=120), r=color(INK) + '<w:b/><w:bCs/>' + size(26))
    style("Abstract", "Abstract", p=spacing(after=180), r=color(INK))
    style("Bibliography", "Bibliography", p=spacing(after=100, line=300) + '<w:ind w:left="300" w:hanging="300"/>', r=size(20))
    for sid, name in [("Caption", "Caption"), ("TableCaption", "Table Caption"), ("ImageCaption", "Image Caption")]:
        p = '<w:keepLines/>' + ('<w:keepNext/>' if sid == 'TableCaption' else '') + spacing(before=80, after=140, line=288) + '<w:jc w:val="center"/>'
        style(sid, name, p=p, r=color(INK) + size(18) + '<w:i w:val="0"/>')
    for sid, name in [("Figure", "Figure"), ("CaptionedFigure", "Captioned Figure")]:
        style(sid, name, p=('<w:keepNext/>' if sid == 'CaptionedFigure' else '') + spacing(before=160, after=100) + '<w:jc w:val="center"/>')
    for level in range(1, 10):
        p = spacing(after=60, line=300) + '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9129"/></w:tabs>' + f'<w:ind w:left="{(level - 1) * 240}"/>'
        style(f"TOC{level}", f"toc {level}", p=p, r=size(20) + (color(INK) + '<w:b/>' if level == 1 else color(INK)))
    style("Header", "header", p=spacing(after=0, line=240), r=size(17) + color(INK))
    style("Footer", "footer", p=spacing(after=0, line=240) + '<w:jc w:val="right"/>', r=size(17) + color(INK))

    borders = ''.join(f'<w:{side} w:val="single" w:sz="4" w:color="DFE5EB"/>' for side in ('top', 'left', 'bottom', 'right', 'insideH')) + '<w:insideV w:val="nil"/>'
    margins = ''.join(f'<w:{side} w:w="{value}" w:type="dxa"/>' for side, value in [('top', 100), ('left', 140), ('bottom', 100), ('right', 140)])
    # Center the table as an object; cell paragraphs retain Markdown column alignment.
    table = f'<w:tblPr><w:tblStyleRowBandSize w:val="1"/><w:jc w:val="center"/><w:tblBorders>{borders}</w:tblBorders><w:tblCellMar>{margins}</w:tblCellMar></w:tblPr>'
    table += '<w:trPr><w:cantSplit/></w:trPr><w:tcPr><w:vAlign w:val="center"/></w:tcPr>'
    table += f'<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:bCs/>{color(INK)}</w:rPr><w:tcPr><w:shd w:val="clear" w:fill="E8F0F4"/></w:tcPr></w:tblStylePr>'
    table += '<w:tblStylePr w:type="band1Horz"><w:tcPr><w:shd w:val="clear" w:fill="F7F9FB"/></w:tcPr></w:tblStylePr>'
    style("Table", "Table", kind="table", based=None, p=spacing(after=0, line=288), r=FONT + color(INK) + size(20), tail=table)
    return canonical_styles(doc)


def canonical_styles(doc):
    """Use the OOXML property order rather than relying on viewer recovery."""
    orders = {
        'w:pPr': 'pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange',
        'w:rPr': 'rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath rPrChange',
    }
    for tag, names in orders.items():
        rank = {f'w:{n}': i for i, n in enumerate(names.split())}
        for node in doc.getElementsByTagName(tag):
            elements = [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]
            for element in sorted(elements, key=lambda e: rank.get(e.tagName, 999)):
                node.appendChild(element)
    return doc.toxml(encoding='UTF-8')


def standard_styles(data):
    """The same complete semantic coverage with conventional black typography."""
    doc = minidom.parseString(data)
    serif = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/>'
    heading_font = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/>'
    for node in doc.getElementsByTagName('w:color'):
        node.setAttribute('w:val', '000000')
    for fonts in list(doc.getElementsByTagName('w:rFonts')):
        if fonts.hasAttribute('w:ascii') and fonts.getAttribute('w:ascii') != 'Consolas':
            replace_child(doc, fonts.parentNode, 'w:rFonts', serif)
    for shading in doc.getElementsByTagName('w:shd'):
        fill = shading.getAttribute('w:fill')
        if fill != 'auto':
            shading.setAttribute('w:fill', 'F2F2F2' if fill in ('E8F0F4', 'F3F6F8') else 'FFFFFF')
    for node in doc.getElementsByTagName('*'):
        if node.hasAttribute('w:color'):
            node.setAttribute('w:color', 'B7B7B7')
    defaults = doc.getElementsByTagName('w:rPrDefault')[0].getElementsByTagName('w:rPr')[0]
    replace_child(doc, defaults, 'w:sz', '<w:sz w:val="24"/>')
    replace_child(doc, defaults, 'w:szCs', '<w:szCs w:val="24"/>')
    for style in doc.getElementsByTagName('w:style'):
        sid = style.getAttribute('w:styleId')
        p = children(style, 'w:pPr')
        r = children(style, 'w:rPr')
        if sid == 'Normal':
            replace_child(doc, r[0], 'w:sz', '<w:sz w:val="24"/>')
            replace_child(doc, r[0], 'w:szCs', '<w:szCs w:val="24"/>')
        if sid == 'Title' or sid.startswith('Heading'):
            replace_child(doc, r[0], 'w:rFonts', heading_font)
            if sid == 'Title':
                replace_child(doc, r[0], 'w:sz', '<w:sz w:val="44"/>')
                replace_child(doc, r[0], 'w:szCs', '<w:szCs w:val="44"/>')
            if p:
                for border in children(p[0], 'w:pBdr'):
                    p[0].removeChild(border)
        if sid == 'BlockText' and p:
            for border in children(p[0], 'w:pBdr'):
                p[0].removeChild(border)
        if sid == 'Table':
            for border in style.getElementsByTagName('w:insideV'):
                border.setAttribute('w:val', 'single')
                border.setAttribute('w:sz', '4')
                border.setAttribute('w:color', 'B7B7B7')
    return canonical_styles(doc)


def make_reference(pandoc, standard=False):
    base = run(pandoc, ["--print-default-data-file", "reference.docx"])
    tokens = json.loads(run(pandoc, ["--print-highlight-style", "pygments"]))["text-styles"].keys()
    with ZipFile(io.BytesIO(base)) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    parts['word/styles.xml'] = make_styles(parts['word/styles.xml'], tokens)
    if standard:
        parts['word/styles.xml'] = standard_styles(parts['word/styles.xml'])
    fonts = minidom.parseString(parts['word/fontTable.xml'])
    for name, family, pitch, charset in [('Consolas', 'modern', 'fixed', '00'), ('Microsoft YaHei', 'swiss', 'variable', '86'), ('SimSun', 'roman', 'fixed', '86'), ('SimHei', 'swiss', 'fixed', '86')]:
        if not any(f.getAttribute('w:name') == name for f in fonts.getElementsByTagName('w:font')):
            append_xml(fonts, fonts.documentElement, f'<w:font w:name="{name}"><w:charset w:val="{charset}"/><w:family w:val="{family}"/><w:pitch w:val="{pitch}"/></w:font>')
    parts['word/fontTable.xml'] = fonts.toxml(encoding='UTF-8')

    sect = '<w:sectPr><w:footerReference w:type="default" r:id="rIdClearFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1247" w:right="1247" w:bottom="1247" w:left="1247" w:header="567" w:footer="567" w:gutter="0"/><w:cols w:space="720"/><w:docGrid w:type="default"/></w:sectPr>'
    def paragraph(style, text):
        return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'
    title = '标准黑白 · Standard' if standard else '技术文档'
    subtitle = '规范、清晰的 Word 文档样式' if standard else '中文技术文章的 Word 导出样式'
    body = paragraph('Title', title) + paragraph('Subtitle', subtitle)
    body += paragraph('BodyText', '在 Typora 的偏好设置 → 导出 → Word (.docx) 中，将本文件选为“样式参考 / Style Reference”。随后正常导出即可。')
    body += paragraph('Heading1', '完整的文档样式') + paragraph('BodyText', '本模板覆盖标题、正文、代码、表格、引用、列表、图片说明、脚注、目录与页码。字体与颜色已经内置，无需额外的主题文件。')
    body += paragraph('BlockText', '本页仅用于介绍模板。作为样式参考导出时，这些说明文字不会出现在你的文章中。')
    example = 'standard' if standard else 'technical-blog'
    body += paragraph('Heading2', '查看完整效果') + paragraph('BodyText', f'在线样例：https://github.com/taifuer/typora-template/blob/main/word/examples/{example}.docx。预览与说明：https://github.com/taifuer/typora-template/blob/main/word/README.md。')
    parts['word/document.xml'] = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}{sect}</w:body></w:document>'.encode()
    footer = '<w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr><w:r><w:t xml:space="preserve">第 </w:t></w:r><w:fldSimple w:instr="PAGE"><w:r><w:t>1</w:t></w:r></w:fldSimple><w:r><w:t xml:space="preserve"> 页</w:t></w:r></w:p>'
    parts['word/footer-clear.xml'] = f'<?xml version="1.0" encoding="UTF-8"?><w:ftr xmlns:w="{W}">{footer}</w:ftr>'.encode()
    rels = minidom.parseString(parts['word/_rels/document.xml.rels'])
    rel = rels.createElementNS('http://schemas.openxmlformats.org/package/2006/relationships', 'Relationship')
    for k, v in {'Id': 'rIdClearFooter', 'Type': R + '/footer', 'Target': 'footer-clear.xml'}.items():
        rel.setAttribute(k, v)
    rels.documentElement.appendChild(rel)
    parts['word/_rels/document.xml.rels'] = rels.toxml(encoding='UTF-8')
    ct = minidom.parseString(parts['[Content_Types].xml'])
    override = ct.createElementNS('http://schemas.openxmlformats.org/package/2006/content-types', 'Override')
    override.setAttribute('PartName', '/word/footer-clear.xml')
    override.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml')
    ct.documentElement.appendChild(override)
    parts['[Content_Types].xml'] = ct.toxml(encoding='UTF-8')
    settings = minidom.parseString(parts['word/settings.xml'])
    replace_child(settings, settings.documentElement, 'w:updateFields', '<w:updateFields w:val="true"/>')
    parts['word/settings.xml'] = settings.toxml(encoding='UTF-8')
    # Clear reference metadata; article title and author come from its own input.
    parts['docProps/core.xml'] = f'<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{title}</dc:title><dc:creator>typora-word</dc:creator></cp:coreProperties>'.encode()
    output = ROOT / ('templates/standard.docx' if standard else 'templates/tech.docx')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return output


def export(pandoc, source, output, reference, extra=()):
    args = ['-f', 'markdown', '-t', 'docx', '--reference-doc', native_path(reference, pandoc), '--resource-path', native_path(source.parent, pandoc), *extra, '-o', '-']
    result = run(pandoc, args, source.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pandoc', default=shutil.which('pandoc'), help='Path to pandoc, including a Windows pandoc.exe under WSL')
    args = parser.parse_args()
    if not args.pandoc:
        parser.error('Provide --pandoc or put pandoc on PATH.')
    print(run(args.pandoc, ['--version']).decode().splitlines()[0])
    reference = make_reference(args.pandoc)
    export(args.pandoc, ROOT / 'examples/technical-blog.md', ROOT / 'examples/technical-blog.docx', reference)
    export(args.pandoc, ROOT / 'examples/style-coverage.md', ROOT / 'examples/style-coverage.docx', reference, ['--toc', '--toc-depth=3'])
    standard = make_reference(args.pandoc, standard=True)
    export(args.pandoc, ROOT / 'examples/standard.md', ROOT / 'examples/standard.docx', standard)
    print('Built both reference templates and three examples.')


if __name__ == '__main__':
    main()
