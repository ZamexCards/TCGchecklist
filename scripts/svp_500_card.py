#!/usr/bin/env python3
"""Archive the separately numbered SVP Terapagos & Friends jumbo promo."""
import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/svp.json'
SOURCE = 'https://i.ebayimg.com/images/g/jEoAAOSwzIxnWjK~/s-l1200.jpg'

request = urllib.request.Request(SOURCE, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read()
with Image.open(io.BytesIO(raw)) as original:
    if original.size != (900, 1200):
        raise ValueError(f'Unexpected source dimensions: {original.size}')
    # The photo shows the whole card, almost front-on. Crop only the surroundings.
    image = original.convert('RGBA').crop((98, 95, 817, 1142))
    image = image.resize((728, 1016), Image.Resampling.LANCZOS)
mask = Image.new('L', image.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=42, fill=255)
image.putalpha(mask)
canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
canvas.alpha_composite(image, (18, 18))
path = ROOT / 'assets/sets/svp/500.png'
canvas.save(path, format='PNG', optimize=True)
payload = json.loads(DATA.read_text())
card = next(c for c in payload['cards'] if c['number'] == '500' and c['name'] == 'Terapagos & Friends')
card['images']['small'] = './assets/sets/svp/500.png'
DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
report = {'number': '500', 'name': card['name'], 'source': SOURCE, 'source_type': 'photograph',
          'source_size': [900, 1200], 'output': 'assets/sets/svp/500.png',
          'size': [764, 1052], 'status': 'saved'}
(ROOT / 'data/svp_500_card_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
