#!/usr/bin/env python3
"""Archive the eight Mega Evolution Energy cards from verified Limitless pages."""
import concurrent.futures
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/mee.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


def process(card):
    number, name = card['number'], card['name']
    page = f'https://limitlesstcg.com/cards/en/MEE/{int(number)}'
    source = f'https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/tpci/MEE/MEE_{number}_R_EN.png'
    result = {'number': number, 'name': name, 'page': page, 'source': source}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(match.group(1)) if match else ''
        if not all(token in title.lower() for token in (name.lower(), 'mee', f'#{int(number)}')):
            raise ValueError(f'Card identity mismatch: {title}')
        if f'MEE_{number}_R_EN.png' not in body:
            raise ValueError('Numbered source image not present on card page')
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size != (736, 1024):
                raise ValueError(f'Unexpected image size: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/mee/{number}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', output=str(target.relative_to(ROOT)))
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    return result


payload = json.loads(DATA.read_text())
cards = payload['cards']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(process, cards))
for card, result in zip(cards, results):
    if result['status'] == 'saved':
        card['images']['small'] = './' + result['output']
DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
(ROOT / 'data/mee_energy_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
if len(results) != 8 or any(x['status'] != 'saved' for x in results):
    raise SystemExit(1)
