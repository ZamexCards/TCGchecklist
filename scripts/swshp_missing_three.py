#!/usr/bin/env python3
"""Archive the three missing SWSH Black Star Promo card images."""
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/swshp.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


payload = json.loads(DATA.read_text())
results = []
for card in payload['cards']:
    if card['number'] not in ('SWSH299', 'SWSH300', 'SWSH301'):
        continue
    number, name = card['number'], card['name']
    slug = name.lower().replace(' ', '-')
    page = f'https://pkmncards.com/card/{slug}-sword-shield-promos-{number.lower()}/'
    result = {'number': number, 'name': name, 'page': page}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(match.group(1)) if match else ''
        if not all(token in title.lower() for token in (name.lower(), 'promos', f'#{number.lower()}')):
            raise ValueError(f'Card identity mismatch: {title}')
        candidates = list(dict.fromkeys(re.findall(
            r'https://pkmncards\.com/wp-content/uploads/[^"\s<>]+\.jpg', body, re.I,
        )))
        sources = [url for url in candidates if (
            f'swshbsp_en_{number[-3:]}_std.jpg' in url.lower()
            or f'promo_swsh-{number.lower()}-' in url.lower()
        )]
        if not sources:
            raise ValueError('Numbered source image missing on card page')
        source = sources[0]
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size != (733, 1024):
                raise ValueError(f'Unexpected source dimensions: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(mask)
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/swshp/{number}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format='PNG', optimize=True)
        card['images']['small'] = './' + str(target.relative_to(ROOT))
        result.update(status='saved', source=source, output=str(target.relative_to(ROOT)))
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    results.append(result)

DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
(ROOT / 'data/swshp_missing_three_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
if len(results) != 3 or any(x['status'] != 'saved' for x in results):
    raise SystemExit(1)
