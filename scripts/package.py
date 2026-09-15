#!/usr/bin/env python3
"""Build a versioned Release archive and SHA-256 checksum from reviewed files."""
import argparse
import hashlib
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
# Explicit inputs: Word lock files, caches and exploratory exports never ship.
FILES = (
    'README.md', 'docs/validation.md', 'docs/style-decisions.md', 'docs/releasing.md',
    'templates/standard.docx', 'templates/tech.docx', 'filters/center-images.lua',
    'examples/assets/retry-flow.png',
    *(f'examples/{name}.{ext}' for name in ('standard', 'technical-blog', 'style-coverage') for ext in ('md', 'docx')),
    *(f'previews/{name}.pdf' for name in ('standard', 'technical-blog', 'style-coverage')),
    *(f'previews/{name}{suffix}.png' for name in ('standard', 'technical-blog') for suffix in ('', '-markdown')),
    *(f'scripts/{name}' for name in ('build.py', 'check_layout.py', 'check_pagination.py',
        'make_diagram.py', 'package.py', 'render-word.ps1', 'render_previews.py', 'validate.py', 'validate_render.py')),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='dev', help='Release version, e.g. 0.1.0 or v0.1.0; defaults to dev')
    args = parser.parse_args()
    version = args.version.removeprefix('v')
    if version != 'dev' and not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?', version):
        parser.error('Use a version such as 0.1.0, v0.1.0 or 0.1.0-rc.1.')
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        parser.error('Missing release inputs: ' + ', '.join(missing))
    prefix = f'typora-word-styles-{version}'
    output = ROOT / 'dist' / f'{prefix}.zip'
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name in sorted(FILES):
            # Fixed metadata makes identical inputs produce identical archives.
            info = ZipInfo(f'{prefix}/{name}', date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compress_type=ZIP_DEFLATED)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {f'{prefix}/{name}' for name in FILES}
    checksum = output.with_suffix('.zip.sha256')
    checksum.write_text(f'{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}\n', encoding='utf-8')
    print(f'{output.relative_to(ROOT)}: {len(FILES)} files, {output.stat().st_size:,} bytes')
    print(checksum.relative_to(ROOT))


if __name__ == '__main__':
    main()
