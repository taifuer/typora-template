#!/usr/bin/env python3
"""Regenerate the example's simple diagram (optional; requires Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('/mnt/c/Windows/Fonts/msyh.ttc')
if not FONT.exists():
    FONT = Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')

image = Image.new('RGB', (1440, 280), 'white')
draw = ImageDraw.Draw(image)
regular = ImageFont.truetype(str(FONT), 30)
small = ImageFont.truetype(str(FONT), 23)
for x, title, detail in [(25, '执行请求', '调用与超时'), (535, '判断边界', '错误类型 · 剩余次数'), (1045, '等待重试', '退避 · 再次尝试')]:
    draw.rounded_rectangle((x, 40, x + 365, 205), radius=14, fill='#F3F6F8', outline='#C9D9E2', width=2)
    draw.text((x + 182, 86), title, font=regular, fill='#215E78', anchor='mm')
    draw.text((x + 182, 143), detail, font=small, fill='#596779', anchor='mm')
for x, label in [(408, '失败'), (918, '允许')]:
    draw.line((x, 122, x + 103, 122), fill='#81AAB9', width=4)
    draw.polygon([(x + 103, 122), (x + 91, 115), (x + 91, 129)], fill='#81AAB9')
    draw.text((x + 51, 90), label, font=small, fill='#596779', anchor='mm')
path = ROOT / 'examples/assets/retry-flow.png'
path.parent.mkdir(parents=True, exist_ok=True)
image.save(path, dpi=(220, 220))
print(path.relative_to(ROOT))
