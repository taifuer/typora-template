#!/usr/bin/env python3
"""Package the two templates with examples and their actual Word previews."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / 'README.md', ROOT / 'docs/validation.md']
for folder in ('templates', 'examples', 'previews', 'scripts'):
    files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
output = ROOT / 'dist/typora-word-styles.zip'
output.parent.mkdir(exist_ok=True)
with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(ROOT))
with ZipFile(output) as archive:
    assert archive.testzip() is None
    assert len([n for n in archive.namelist() if n.startswith('templates/')]) == 2
print(f'{output.relative_to(ROOT)}: {len(files)} files, {output.stat().st_size:,} bytes')
