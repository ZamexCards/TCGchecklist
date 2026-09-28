#!/usr/bin/env python3
"""Archive the five MEP cards following the approved Meganium 001 example."""
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/mep.json'
CARDS = json.loads(DATA.read_text())
REPORT = []

for card in CARDS['cards'][1:6]:
    number, name = card['number'], card['name']
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    page = f'https://pkmncards.com/card/{slug}-mega-evolution-promos-mep-{number}/'
    source = f'https://pkmncards.com/wp-content/uploads/mebsp_en_{number}_std.jpg'
    entry = {'number': number, 'name': name, 'page': page, 'source': source}
    try:
        request = urllib.request.Request(page, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode('utf-8', 'replace')
        title = html.unescape(re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S).group(1))
        if not all(x in title.lower() for x in (name.lower(), 'mep', number)) or source not in body:
            raise ValueError('Card identity or source image differs from expected page')
        request = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
        with Image.open(io.BytesIO(raw)) as original:
            if original.size != (733, 1024):
                raise ValueError(f'Unexpected source dimensions: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        # Same card bounds, padding and corner radius as the approved 001.png.
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(mask)
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/mep/{number}.png'
        canvas.save(target, format='PNG', optimize=True)
        card['images']['small'] = f'./assets/sets/mep/{number}.png'
        entry.update(status='saved', output=str(target.relative_to(ROOT)), size=list(canvas.size))
    except Exception as exc:
        entry.update(status='failed', error=str(exc))
    REPORT.append(entry)

DATA.write_text(json.dumps(CARDS, ensure_ascii=False, separators=(',', ':')))
(ROOT / 'data/mep_five_card_report.json').write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(REPORT, ensure_ascii=False, indent=2))
if any(x['status'] != 'saved' for x in REPORT):
    raise SystemExit(1)
