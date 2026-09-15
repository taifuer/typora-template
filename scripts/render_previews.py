#!/usr/bin/env python3
"""Render paired Markdown/Word screenshots for the README."""
import argparse
import os
import shutil
import subprocess
import tempfile

from build import ROOT, native_path, run

CSS = '''
html { background: white; }
body { box-sizing: border-box; max-width: 980px; margin: 72px auto;
  padding: 0; color: #24292f; background: white;
  font-family: "WenQuanYi Zen Hei", "Microsoft YaHei", sans-serif;
  font-size: 21px; line-height: 1.5; }
h1, h2, h3 { font-weight: 600; line-height: 1.3; }
h1 { font-size: 34px; margin: 30px 0 18px; padding-bottom: 12px; border-bottom: 1px solid #d8dee4; }
h2 { font-size: 27px; margin: 26px 0 14px; }
h3 { font-size: 23px; margin: 22px 0 12px; }
header { margin-bottom: 34px; text-align: left; }
h1.title { font-size: 40px; border: 0; padding: 0; margin: 0 0 12px; }
p.subtitle { font-size: 25px; margin: 0 0 20px; }
p.author, p.date { color: #57606a; font-size: 18px; margin: 4px 0; }
p { margin: 14px 0; }
ul, ol { padding-left: 32px; margin: 12px 0; }
li { margin: 4px 0; }
li ul, li ol { margin: 4px 0; }
code { font-family: "DejaVu Sans Mono", Consolas, monospace; font-size: 0.88em; }
p code { padding: 2px 5px; background: #f0f2f4; border-radius: 4px; }
div.sourceCode { margin: 22px 0; background: #f6f8fa; border: 1px solid #d8dee4; border-radius: 6px; }
pre { margin: 0; padding: 18px 22px; white-space: pre-wrap; line-height: 1.42; }
pre code { font-size: 18px; }
table { border-collapse: collapse; margin: 20px 0; font-size: 20px; }
th, td { border: 1px solid #d0d7de; padding: 9px 16px; }
th { background: #f6f8fa; }
figure { margin: 22px 0; text-align: center; }
img { max-width: 100%; height: auto; }
figcaption { color: #57606a; font-size: 17px; margin-top: 8px; }
math[display="block"] { margin: 20px 0; }
'''


def markdown_excerpt(name):
    source = (ROOT / f'examples/{name}.md').read_text(encoding='utf-8')
    if name == 'standard':
        return source.split('\n> 引用内容', 1)[0] + '\n'
    start = source.index('# 用代码表达边界')
    end = source.index('\n这个示例没有加入随机抖动')
    return source[start:end] + '\n'


def render_markdown(pandoc, browser, name, folder):
    # Use the real sample content; the preview is HTML, not a simulated editor UI.
    html = run(pandoc, ['-f', 'markdown', '-t', 'html5', '--standalone', '--mathml',
        '--self-contained', '--metadata', f'pagetitle={name}', '--resource-path',
        native_path(ROOT / 'examples', pandoc)], markdown_excerpt(name).encode()).decode('utf-8')
    html = html.replace('</head>', f'<style>{CSS}</style></head>')
    source = folder / f'{name}.html'
    source.write_text(html, encoding='utf-8')
    output = ROOT / f'previews/{name}-markdown.png'
    with tempfile.TemporaryDirectory(prefix='preview-browser-', dir=folder) as profile:
        args = [browser, '--headless', '--disable-gpu', '--hide-scrollbars',
            '--no-first-run', '--disable-background-networking', '--disable-extensions',
            '--allow-file-access-from-files', '--timeout=5000',
            '--window-size=1200,1698', '--force-device-scale-factor=1',
            '--virtual-time-budget=2000', f'--user-data-dir={profile}',
            f'--screenshot={output}', source.as_uri()]
        if hasattr(os, 'geteuid') and os.geteuid() == 0:
            args.insert(1, '--no-sandbox')
        subprocess.run(args, check=True, capture_output=True, timeout=30)
    print(f'{output.relative_to(ROOT)}: Markdown preview')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pandoc', default=shutil.which('pandoc'))
    parser.add_argument('--browser', default=shutil.which('chromium') or shutil.which('google-chrome'))
    args = parser.parse_args()
    if not args.pandoc or not args.browser:
        parser.error('Provide --pandoc and --browser (Chromium/Chrome), or put them on PATH.')
    renderer = shutil.which('pdftoppm')
    if renderer is None:
        raise SystemExit('Install Poppler and put pdftoppm on PATH.')
    folder = ROOT / 'build/previews'
    folder.mkdir(parents=True, exist_ok=True)
    for name, page in [('standard', 1), ('technical-blog', 2)]:
        render_markdown(args.pandoc, args.browser, name, folder)
        source = ROOT / 'previews' / f'{name}.pdf'
        output = source.with_suffix('')
        subprocess.run([renderer, '-f', str(page), '-l', str(page),
            '-scale-to-x', '1200', '-scale-to-y', '-1', '-png', '-singlefile',
            str(source), str(output)], check=True)
        print(f'{output.with_suffix(".png").relative_to(ROOT)}: Word PDF page {page}')


if __name__ == '__main__':
    main()
