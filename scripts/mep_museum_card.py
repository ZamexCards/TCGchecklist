#!/usr/bin/env python3
"""Archive the separately numbered Museum jumbo card in the MEP checklist."""
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/mep.json'
SOURCE = ('https://images.stockx.com/images/'
          'Pikachu-at-the-Museum-Pokemon-Natural-History-Museum-Promo-Ungraded.jpg'
          '?bg=FFFFFF&dpr=2&fit=fill&h=1024&q=90&trim=color&w=733')

request = urllib.request.Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read()
with Image.open(io.BytesIO(raw)) as original:
    if original.size != (1466, 2048):
        raise ValueError(f'Unexpected museum card size: {original.size}')
    # Remove the few white background pixels outside the physical card.
    image = original.convert('RGBA').crop((3, 8, 1463, 2040))
    image = image.resize((728, 1016), Image.Resampling.LANCZOS)
mask = Image.new('L', image.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
image.putalpha(mask)
canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
canvas.alpha_composite(image, (18, 18))
path = ROOT / 'assets/sets/mep/Museum.png'
canvas.save(path, format='PNG', optimize=True)
payload = json.loads(DATA.read_text())
card = next(c for c in payload['cards'] if c['number'] == 'Museum' and c['name'] == 'Pikachu at the Museum')
card['images']['small'] = './assets/sets/mep/Museum.png'
DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
report = {'number': 'Museum', 'name': card['name'], 'source': SOURCE,
          'source_size': [1466, 2048], 'output': 'assets/sets/mep/Museum.png',
          'size': [764, 1052], 'status': 'saved'}
(ROOT / 'data/mep_museum_card_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
