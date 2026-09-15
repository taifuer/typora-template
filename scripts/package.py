#!/usr/bin/env python3
"""Build separate Word and Quietype release packages with SHA-256 checksums."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
# Explicit inputs keep caches, editor lock files and installed Typora assets out.
WORD_FILES = (
    'README.md', 'docs/validation.md', 'docs/style-decisions.md',
    'templates/standard.docx', 'templates/tech.docx', 'filters/center-images.lua',
    'examples/assets/retry-flow.png',
    *(f'examples/{name}.{ext}' for name in ('standard', 'technical-blog', 'style-coverage') for ext in ('md', 'docx')),
    *(f'previews/{name}.pdf' for name in ('standard', 'technical-blog', 'style-coverage')),
    *(f'previews/{name}{suffix}.png' for name in ('standard', 'technical-blog') for suffix in ('', '-markdown')),
    *(f'scripts/{name}' for name in ('build.py', 'check_layout.py', 'check_pagination.py',
        'make_diagram.py', 'render-word.ps1', 'render_previews.py', 'validate.py', 'validate_render.py')),
)
QUIETYPE_FILES = (
    'README.md', 'quietype.css', 'docs/development.md', 'examples/assets/retry-flow.png',
    *(f'examples/{name}.md' for name in ('quietype', 'quietype-elements', 'style-coverage')),
    *(f'previews/quietype-{name}.png' for name in (
        'reading', 'code', 'diagrams', 'markers', 'typora-reading', 'typora-code')),
    *(f'scripts/{name}' for name in (
        'render_theme_preview.py', 'typora_preview_assets.py', 'theme_preview_runtime.js')),
)
PACKAGES = {
    'typora-word': ('word', WORD_FILES),
    'quietype': ('themes/quietype', QUIETYPE_FILES),
}
STANDALONE = {
    'standard.docx': 'word/templates/standard.docx',
    'tech.docx': 'word/templates/tech.docx',
    'quietype.css': 'themes/quietype/quietype.css',
}


def package(name, version, source, files, output):
    prefix = f'{name}-{version}'
    archive_path = output / f'{prefix}.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
        for relative in sorted(files):
            # Fixed metadata makes identical inputs produce identical archives.
            info = ZipInfo(f'{prefix}/{relative}', date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (source / relative).read_bytes(), compress_type=ZIP_DEFLATED)
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {f'{prefix}/{relative}' for relative in files}
    print(f'{archive_path.relative_to(ROOT)}: {len(files)} files, {archive_path.stat().st_size:,} bytes')
    return archive_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='dev', help='Release version, e.g. 0.2.0 or v0.2.0; defaults to dev')
    args = parser.parse_args()
    version = args.version.removeprefix('v')
    if version != 'dev' and not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?', version):
        parser.error('Use a version such as 0.2.0, v0.2.0 or 0.2.0-rc.1.')
    required = [f'{source}/{name}' for source, files in PACKAGES.values() for name in files]
    required.extend(STANDALONE.values())
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        parser.error('Missing release inputs: ' + ', '.join(sorted(set(missing))))
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    assets = [package(name, version, ROOT / source, files, output)
        for name, (source, files) in PACKAGES.items()]
    for name, source in STANDALONE.items():
        path = output / name
        shutil.copyfile(ROOT / source, path)
        assets.append(path)
        print(path.relative_to(ROOT))
    checksum = output / 'SHA256SUMS'
    checksum.write_text(''.join(
        f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n'
        for path in sorted(assets)), encoding='utf-8')
    print(checksum.relative_to(ROOT))


if __name__ == '__main__':
    main()
