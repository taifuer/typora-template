#!/usr/bin/env python3
"""Check the standalone theme with local Typora renderers and core editor CSS."""
import argparse
from html import escape, unescape
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import os

from typora_preview_assets import prepare_runtime

ROOT = Path(__file__).resolve().parents[1]


def run(pandoc, args, data=None):
    result = subprocess.run([pandoc, *args], input=data, capture_output=True, check=True)
    if result.stderr:
        print(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def native_path(path, pandoc):
    path = str(Path(path).resolve())
    if os.name != 'nt' and pandoc.lower().endswith('.exe'):
        return subprocess.check_output(['wslpath', '-w', path], text=True, encoding='utf-8').strip()
    return path


MEASURE = r'''
window.addEventListener('load', async () => {
    const runtime = await window.quietypeReady;
    await document.fonts.ready;
    const write = document.querySelector('#write');
    const rect = el => el.getBoundingClientRect();
    const centered = (el, parent) => Math.abs(
        (rect(el).left + rect(el).right) / 2 -
        (rect(parent).left + rect(parent).right) / 2) < 2;
    const colors = [...document.querySelectorAll('.cm-s-inner [class^="cm-"]')]
        .map(el => ({color: getComputedStyle(el).color,
            background: getComputedStyle(el.closest('.md-fences')).backgroundColor}));
    const data = {
        width: window.innerWidth,
        writeWidth: rect(write).width,
        height: Math.ceil(rect(write.lastElementChild).bottom + window.scrollY +
            parseFloat(getComputedStyle(write).paddingBottom)),
        overflow: document.documentElement.scrollWidth > window.innerWidth,
        font: getComputedStyle(write).fontFamily,
        lineHeight: getComputedStyle(write).lineHeight,
        headingSpace: [...write.querySelectorAll('h1,h2,h3')].slice(0,4).map(el => ({
            heading: el.tagName, before: getComputedStyle(el).marginTop,
            after: getComputedStyle(el).marginBottom})),
        runtime,
        diagrams: write.querySelectorAll('[lang="mermaid"] svg').length,
        diagramNotes: [...write.querySelectorAll('[lang="mermaid"] .noteText tspan')]
            .filter(el => el.textContent.trim()).map(el => ({color: getComputedStyle(el).fill,
                background: getComputedStyle(el.closest('svg').querySelector('rect.note')).fill})),
        math: write.querySelectorAll('mjx-container').length,
        mathErrors: write.querySelectorAll('[data-mml-node="merror"]').length,
        images: [...write.querySelectorAll('img')].map(el => ({
            loaded: el.complete && el.naturalWidth > 0,
            fits: rect(el).width <= rect(write).width,
            centered: centered(el, el.closest('figure') || el.parentElement)
        })),
        tables: [...write.querySelectorAll('table')].map(el => ({
            scrollable: el.parentElement.scrollWidth > el.parentElement.clientWidth,
            centered: centered(el, el.parentElement),
            alignmentPreserved: [...el.querySelectorAll('[style*="text-align"]')]
                .every(cell => getComputedStyle(cell).textAlign === cell.style.textAlign)
        })),
        colors,
        fontErrors: [...document.fonts].filter(font => font.status === 'error').length
    };
    const output = document.createElement('script');
    output.id = 'preview-metrics';
    output.type = 'application/json';
    output.textContent = JSON.stringify(data);
    document.body.append(output);
});
'''


def fragment(pandoc, source):
    html = run(pandoc, ['-f', 'markdown-implicit_figures', '-t', 'html5', '--mathjax', '--no-highlight', '--wrap=none',
        '--resource-path', native_path(ROOT / 'examples', pandoc)], source.encode()).decode()
    diagram_count = 0

    def code(match):
        nonlocal diagram_count
        attrs, content = match.groups()
        language = re.search(r'class="([^"]+)"', attrs)
        language = language[1] if language else ''
        diagram_count += language == 'mermaid'
        return f'<pre class="md-fences mock-cm" lang="{escape(language)}" data-diagram-id="{diagram_count}">{content}</pre>'

    html = re.sub(r'<pre([^>]*)><code[^>]*>(.*?)</code></pre>', code, html, flags=re.S)
    html = re.sub(r'<p><span class="math display">(.*?)</span></p>',
        r'<div class="md-math-block"><div class="md-math-container"><div class="md-mathjax-preview">\1</div></div></div>', html, flags=re.S)
    html = html.replace('class="math inline"', 'class="md-inline-math"')
    # Normalize Typora extensions that Pandoc 2.18 does not render natively.
    html = re.sub(r'<p>(.*?)</p>', lambda m: '<p>' + re.sub(
        r'(?<![=\w])==([^=\n<>]+)==(?![=\w])', r'<mark>\1</mark>', m[1]) + '</p>', html, flags=re.S)

    def alert(match):
        kind, body = match.groups()
        name = kind.lower()
        return f'<div class="md-alert md-alert-{name}"><p class="md-alert-text md-alert-text-{name}">{kind.title()}</p><p>{body}</div>'

    html = re.sub(r'<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*?)</blockquote>', alert, html, flags=re.S)
    html = re.sub(r'<table(\s[^>]*)?>', r'<figure class="table-figure"><table\1>', html)
    html = html.replace('</table>', '</table></figure>')
    html = html.replace('src="assets/', f'src="{(ROOT / "examples/assets").as_uri()}/')
    # Typora exports preserve whitespace inside lists. Pandoc's HTML indentation
    # is structural, so remove it rather than displaying it as extra empty lines.
    html = re.sub(r'\s*(</?(?:ul|ol|li)(?:\s[^>]*)?>)\s*', r'\1', html)
    html = re.sub(r'<li><input([^>]*)>\s*',
        r'<li class="task-list-item md-task-list-item"><input\1>', html)
    html = html.replace(' disabled=""', '')
    return html


def document(content, resources, font_dir, runtime):
    styles = [resources / 'style/base.css', resources / 'style/base-control.css', resources / 'style/codemirror.css']
    theme_file = ROOT / 'quietype.css'
    missing = [str(path) for path in [*styles, theme_file] if not path.is_file()]
    if missing:
        raise SystemExit('Missing CSS: ' + ', '.join(missing))
    links = ''.join(f'<link rel="stylesheet" href="{path.as_uri()}">' for path in styles)
    renderers = ''.join(f'<script src="{(runtime / name).as_uri()}"></script>' for name in (
        'codemirror/core.js', 'codemirror/mode.min.js', 'diagram/mermaid.min.js'))
    mathjax = (runtime / 'MathJax3/es5/tex-svg-full.js').as_uri()
    runner = (ROOT / 'scripts/theme_preview_runtime.js').as_uri()
    # Only the editor's core CSS is loaded; no installed theme supplies styles.
    theme = theme_file.read_text(encoding='utf-8')
    css = re.sub(r'/\*.*?\*/', '', theme, flags=re.S)
    if re.search(r'@import\b|@include-when-export\b|url\s*\(', css, flags=re.I):
        raise SystemExit('Quietype must be standalone: no CSS imports or external assets.')
    fonts = ''
    if font_dir:
        for family, filename, weight in [('Microsoft YaHei', 'msyh.ttc', 400),
                ('Microsoft YaHei', 'msyhbd.ttc', 600), ('Consolas', 'consola.ttf', 400)]:
            path = font_dir / filename
            if not path.is_file():
                raise SystemExit(f'Missing preview font: {path}')
            fonts += (f'@font-face {{ font-family: "{family}"; font-weight: {weight}; '
                f'src: url("{path.as_uri()}"); }}\n')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quietype · 阅读预览</title>{links}<style>{theme}</style><style>{fonts}</style></head>
<body class="typora-export"><div id="write">{content}</div>
<script>window.quietypeLoadErrors=[];window.addEventListener('error',e=>window.quietypeLoadErrors.push(e.message||'Renderer failed to load'));</script>
{renderers}
<script>window.MathJax={{startup:{{typeset:false}},options:{{enableMenu:false}},svg:{{fontCache:'local'}}}};</script>
<script src="{mathjax}"></script><script src="{runner}"></script>
<script>{MEASURE}</script></body></html>'''


def browser_run(browser, source, folder, width, height=1000, screenshot=None):
    with tempfile.TemporaryDirectory(prefix='browser-', dir=folder) as profile:
        args = [browser, '--headless', '--disable-gpu', '--hide-scrollbars',
            '--no-first-run', '--disable-background-networking', '--disable-extensions',
            '--allow-file-access-from-files', '--timeout=5000',
            f'--window-size={width},{height}', '--force-device-scale-factor=1',
            '--virtual-time-budget=6000', f'--user-data-dir={profile}', '--dump-dom']
        if hasattr(os, 'geteuid') and os.geteuid() == 0:
            args.insert(1, '--no-sandbox')
        if screenshot:
            args.append(f'--screenshot={screenshot}')
        result = subprocess.run([*args, source.as_uri()], check=True,
            capture_output=True, text=True, encoding='utf-8', timeout=30)
    match = re.search(r'<script id="preview-metrics" type="application/json">(.*?)</script>', result.stdout)
    if not match:
        raise RuntimeError('Browser did not finish measuring the preview. ' + result.stderr[-1500:])
    return json.loads(unescape(match[1]))


def contrast(foreground, background):
    def luminance(color):
        values = [int(v) / 255 for v in re.findall(r'\d+', color)[:3]]
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, (.2126, .7152, .0722)))
    values = sorted([luminance(foreground), luminance(background)])
    return (values[1] + .05) / (values[0] + .05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pandoc', default=shutil.which('pandoc'))
    parser.add_argument('--browser', default=shutil.which('chromium') or shutil.which('google-chrome'))
    parser.add_argument('--typora-resources', required=True, type=Path)
    parser.add_argument('--font-dir', type=Path, help='Optional local Windows fonts for the browser preview only')
    args = parser.parse_args()
    if not args.pandoc or not args.browser:
        parser.error('Provide --pandoc and --browser, or put them on PATH.')
    resources = args.typora_resources.resolve()
    font_dir = args.font_dir.resolve() if args.font_dir else None
    folder = ROOT / 'build/theme-preview'
    folder.mkdir(parents=True, exist_ok=True)
    runtime = prepare_runtime(resources, folder / 'runtime')
    (ROOT / 'previews').mkdir(exist_ok=True)
    source = (ROOT / 'examples/quietype.md').read_text(encoding='utf-8')
    intro, code = source.split('## 用代码表达边界', 1)
    code = '## 用代码表达边界' + code.split('## 指数退避的直觉', 1)[0]
    elements = (ROOT / 'examples/quietype-elements.md').read_text(encoding='utf-8')
    diagrams, markers = elements.split('## 引用与提示', 1)
    note = elements[elements.index('[^note]:'):]
    diagrams += '\n' + note
    markers = markers[:markers.index('[^note]:')]
    variants = {'article': source, 'reading': intro, 'code': code,
        'diagrams': diagrams, 'markers': '## 引用与提示' + markers,
        'coverage': (ROOT / 'examples/style-coverage.md').read_text(encoding='utf-8')}
    reports = {}
    for name, markdown in variants.items():
        path = folder / f'{name}.html'
        path.write_text(document(fragment(args.pandoc, markdown), resources, font_dir, runtime), encoding='utf-8')
        widths = ((420, 860, 1920) if name in ('article', 'coverage')
            else (420, 1360) if name in ('diagrams', 'markers') else (1360,))
        for width in widths:
            report = browser_run(args.browser, path, folder, width)
            assert not report['overflow'], (name, width, 'page overflow')
            assert report['writeWidth'] <= 1180, (name, width, 'line length')
            assert not report['runtime']['errors'], (name, report['runtime']['errors'])
            assert all(e['preserved'] for e in report['runtime']['editors']), (name, 'code source changed')
            assert not report['mathErrors'], (name, 'math syntax error')
            if name == 'diagrams':
                assert report['diagrams'] == 2 and report['math'] >= 4, report
                assert report['diagramNotes'] and all(contrast(note['color'], note['background']) >= 4.5
                    for note in report['diagramNotes']), (name, 'diagram note contrast')
            assert report['fontErrors'] == 0, (name, width, 'preview font failed')
            assert all(i['loaded'] and i['fits'] and i['centered'] for i in report['images']), (name, width, 'image')
            assert all(t['alignmentPreserved'] and (t['scrollable'] or t['centered'])
                for t in report['tables']), (name, width, 'table alignment')
            report['minCodeContrast'] = round(min((contrast(c['color'], c['background'])
                for c in report.pop('colors')), default=21), 2)
            assert report['minCodeContrast'] >= 4.5, (name, width, 'code contrast')
            if name in ('reading', 'code', 'diagrams', 'markers') and width == 1360:
                output = ROOT / f'previews/quietype-{name}.png'
                browser_run(args.browser, path, folder, width, report['height'], output)
                print(output.relative_to(ROOT))
            reports[f'{name}-{width}'] = report
    (folder / 'metrics.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(reports)} browser layouts checked; local HTML and metrics in {folder.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
