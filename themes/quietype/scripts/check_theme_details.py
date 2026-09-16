#!/usr/bin/env python3
"""Check footnote consistency and real print-media table overflow with local Chromium."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import tempfile
import time

from render_theme_preview import ROOT, contrast, document


class Browser:
    """Minimal Chrome DevTools pipe client; no extra Python packages required."""

    def __init__(self, executable, profile):
        # Chromium uses descriptors 3/4 for its protocol. Pass arguments directly
        # through the shell; no paths or user input are interpolated as shell code.
        self.process = subprocess.Popen([
            '/bin/sh', '-c', 'exec 3<&0 4>&1; exec "$@"', 'quietype-check',
            executable, '--headless', '--no-sandbox', '--disable-gpu',
            '--no-first-run', '--disable-background-networking',
            '--allow-file-access-from-files', '--remote-debugging-pipe',
            f'--user-data-dir={profile}',
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.buffer = b''
        self.serial = 0
        self.session = None

    def receive(self, deadline):
        while b'\0' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError('Chromium did not answer within 30 seconds')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('Chromium closed its DevTools pipe')
            self.buffer += chunk
        message, self.buffer = self.buffer.split(b'\0', 1)
        return json.loads(message)

    def call(self, method, **params):
        self.serial += 1
        message = {'id': self.serial, 'method': method, 'params': params}
        if self.session:
            message['sessionId'] = self.session
        self.process.stdin.write(json.dumps(message).encode() + b'\0')
        self.process.stdin.flush()
        deadline = time.monotonic() + 30
        while True:
            response = self.receive(deadline)
            if response.get('id') == self.serial:
                if 'error' in response:
                    raise RuntimeError(response['error'])
                return response['result']

    def evaluate(self, expression):
        response = self.call('Runtime.evaluate', expression=expression,
                             returnByValue=True, awaitPromise=True)
        if 'exceptionDetails' in response:
            raise RuntimeError(response['exceptionDetails'])
        return response['result'].get('value')

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()


FIXTURE = '''<h1>脚注与表格回归检查</h1>
<p class="md-def-footnote"><span class="md-def-name">note</span><span class="md-def-content">编辑态脚注说明。</span></p>
<section class="footnotes"><ol><li><p>组件预览脚注说明。</p></li></ol></section>
<div class="footnotes-area"><div class="footnote-line"><span class="md-fn-count">1</span><span>原生 HTML 导出脚注说明。</span></div></div>
'''

MEASURE = r'''() => {
    const rgba = value => (value.match(/[\d.]+/g) || []).map(Number);
    const over = (front, back) => front.slice(0, 3).map((v, i) =>
        v * (front[3] ?? 1) + back[i] * (1 - (front[3] ?? 1)));
    const footnote = selector => {
        const el = document.querySelector(selector), style = getComputedStyle(el);
        const chain = [];
        for (let node = el; node; node = node.parentElement) chain.unshift(node);
        let opacity = 1, background = [255, 255, 255];
        for (const node of chain) {
            const s = getComputedStyle(node);
            opacity *= Number(s.opacity);
            background = over(rgba(s.backgroundColor), background);
        }
        const foreground = rgba(style.color);
        foreground[3] = (foreground[3] ?? 1) * opacity;
        const rgb = value => `rgb(${value.map(Math.round).join(', ')})`;
        return {selector, fontSize: parseFloat(style.fontSize), opacity,
            foreground: rgb(over(foreground, background)), background: rgb(background)};
    };
    const tables = [...document.querySelectorAll('.table-figure')].map(el => {
        const s = getComputedStyle(el);
        el.scrollLeft = 20;
        return {focused: el.classList.contains('md-focus'),
            overflowX: s.overflowX, overflowY: s.overflowY,
            clientWidth: el.clientWidth, scrollWidth: el.scrollWidth,
            canScroll: el.scrollLeft > 0};
    });
    return {bodyFontSize: parseFloat(getComputedStyle(document.querySelector('#write')).fontSize),
        printMedia: matchMedia('print').matches,
        footnotes: ['.md-def-footnote .md-def-content', '.footnotes p',
            '.footnotes-area .footnote-line'].map(footnote), tables};
}'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', default=shutil.which('chromium') or shutil.which('google-chrome'))
    parser.add_argument('--typora-resources', type=Path, required=True)
    parser.add_argument('--theme', type=Path, default=ROOT / 'quietype.css',
                        help='Optional older CSS file for a negative regression check')
    parser.add_argument('--report', type=Path, default=ROOT / 'build/theme-details/check.json')
    args = parser.parse_args()
    if not args.browser:
        parser.error('Provide --browser, or put Chromium on PATH.')
    folder = ROOT / 'build/theme-details'
    folder.mkdir(parents=True, exist_ok=True)
    theme = args.theme.resolve().read_text(encoding='utf-8')
    # A long unbroken cell makes overflow measurable without fixture CSS that
    # could mask the theme's actual screen/print cascade.
    table = '<table><thead><tr><th>接口</th></tr></thead><tbody><tr><td>' + 'long_api_name_' * 35 + '</td></tr></tbody></table>'
    content = FIXTURE + ''.join(f'<figure class="table-figure{focus}">{table}</figure>'
                                for focus in ('', ' md-focus'))
    html = document(content, args.typora_resources.resolve(), None, folder)
    html = html.replace((ROOT / 'quietype.css').read_text(encoding='utf-8'), theme, 1)
    # This check needs only actual installed editor CSS, not diagram runtimes.
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
    path = folder / 'fixture.html'
    path.write_text(html, encoding='utf-8')
    report = {'theme': str(args.theme.resolve()),
              'sha256': hashlib.sha256(theme.encode()).hexdigest(), 'cases': [], 'errors': []}
    with tempfile.TemporaryDirectory(prefix='browser-', dir=folder) as profile:
        browser = Browser(args.browser, profile)
        try:
            report['browser'] = browser.call('Browser.getVersion')['product']
            target = browser.call('Target.createTarget', url='about:blank')['targetId']
            browser.session = browser.call('Target.attachToTarget', targetId=target, flatten=True)['sessionId']
            browser.call('Emulation.setDeviceMetricsOverride', width=700, height=1000,
                         deviceScaleFactor=1, mobile=False)
            browser.call('Page.enable')
            browser.call('Page.navigate', url=path.as_uri())
            deadline = time.monotonic() + 30
            while browser.receive(deadline).get('method') != 'Page.loadEventFired':
                pass
            browser.evaluate('document.fonts.ready.then(() => true)')
            for size in (17, 20):
                browser.evaluate(f'document.documentElement.style.fontSize = "{size}px"')
                for mode in ('editor', 'export'):
                    browser.evaluate('document.body.className = ' + json.dumps('typora-export' if mode == 'export' else ''))
                    for media in ('screen', 'print'):
                        browser.call('Emulation.setEmulatedMedia', media=media)
                        case = browser.evaluate('(' + MEASURE + ')()')
                        case.update(fontSize=size, mode=mode, media=media)
                        label = f'{size}px {mode} {media}'
                        notes = case['footnotes']
                        for note in notes:
                            note['contrast'] = round(contrast(note['foreground'], note['background']), 2)
                        errors = []
                        if case['printMedia'] != (media == 'print'):
                            errors.append('print media emulation did not take effect')
                        if abs(case['bodyFontSize'] - size) > .01:
                            errors.append('body does not respect the selected font size')
                        if max(n['fontSize'] for n in notes) - min(n['fontSize'] for n in notes) > .05:
                            errors.append('footnote sizes differ between editor/preview/export markup')
                        if any(not .8 <= n['fontSize'] / size <= .95 for n in notes):
                            errors.append('footnotes do not scale to a readable size')
                        if min(n['contrast'] for n in notes) < 4.5:
                            errors.append('composited footnote contrast is below 4.5:1')
                        if max(n['contrast'] for n in notes) - min(n['contrast'] for n in notes) > .1:
                            errors.append('footnote brightness differs between markup variants')
                        for table_result in case['tables']:
                            if media == 'print' and any(table_result[key] != 'visible' for key in ('overflowX', 'overflowY')):
                                errors.append(f'printed table clips content (focused={table_result["focused"]})')
                            if media == 'screen' and not table_result['focused'] and not (
                                    table_result['overflowX'] == 'auto' and table_result['canScroll']):
                                errors.append('unfocused wide table is not scrollable on screen')
                        report['cases'].append(case)
                        report['errors'].extend(f'{label}: {error}' for error in errors)
        finally:
            browser.close()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(report["cases"])} cases; {len(report["errors"])} failures; report: {args.report}')
    for error in report['errors']:
        print(error)
    raise SystemExit(bool(report['errors']))


if __name__ == '__main__':
    main()
