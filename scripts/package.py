#!/usr/bin/env python3
"""Build Word and Quietype ZIP packages and their SHA-256 checksum file."""
import argparse
import hashlib
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
# Explicit inputs keep caches, editor lock files and installed Typora assets out.
WORD_FILES = ('standard.docx', 'tech.docx')
QUIETYPE_FILES = ('quietype.css',)
PACKAGES = {
    'typora-word': ('word/templates', WORD_FILES),
    'quietype': ('themes/quietype', QUIETYPE_FILES),
}


def package(name, version, source, files, output):
    prefix = f'{name}-{version}'
    archive_path = output / f'{prefix}.zip'
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
        for relative in sorted(files):
            # Fixed metadata makes identical inputs produce identical archives.
            info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (source / relative).read_bytes(), compress_type=ZIP_DEFLATED)
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(files)
    print(f'{archive_path.relative_to(ROOT)}: {len(files)} files, {archive_path.stat().st_size:,} bytes')
    return archive_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='dev', help='Release version, e.g. 0.2.2 or v0.2.2; defaults to dev')
    args = parser.parse_args()
    version = args.version.removeprefix('v')
    if version != 'dev' and not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?', version):
        parser.error('Use a version such as 0.2.2, v0.2.2 or 0.2.2-rc.1.')
    required = [f'{source}/{name}' for source, files in PACKAGES.values() for name in files]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        parser.error('Missing release inputs: ' + ', '.join(sorted(set(missing))))
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    assets = [package(name, version, ROOT / source, files, output)
        for name, (source, files) in PACKAGES.items()]
    checksum = output / 'SHA256SUMS'
    checksum.write_text(''.join(
        f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n'
        for path in sorted(assets)), encoding='utf-8')
    print(checksum.relative_to(ROOT))


if __name__ == '__main__':
    main()
