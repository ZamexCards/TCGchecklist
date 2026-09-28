#!/usr/bin/env python3
"""Archive verified Best of Game cards, retaining the full printed borders."""
import concurrent.futures
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/bog.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


def process(card):
    number, name = card['number'], card['name']
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower().replace('’', '')).strip('-')
    page = f'https://pkmncards.com/card/{slug}-best-of-game-{number}/'
    result = {'number': number, 'name': name, 'page': page}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(match.group(1)) if match else ''
        norm = lambda s: s.lower().replace('’', "'")
        if not all(token in norm(title) for token in (norm(name), 'best of game', f'#{number}')):
            raise ValueError(f'Card identity mismatch: {title}')
        sources = list(dict.fromkeys(re.findall(
            rf'https://pkmncards\.com/wp-content/uploads/[^"\s<>]*best-of-game[^"\s<>]*-{number}\.jpg',
            body, re.I,
        )))
        if not sources:
            raise ValueError('Numbered scan not found on card page')
        source = sources[0]
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size != (600, 825):
                raise ValueError(f'Unexpected image size: {original.size}')
            # Maintain the original card aspect ratio and complete yellow border.
            image = original.convert('RGBA').resize((728, 1001), Image.Resampling.LANCZOS)
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1000), radius=25, fill=255)
        image.putalpha(mask)
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 25))
        target = ROOT / f'assets/sets/bog/{number}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', source=source, output=str(target.relative_to(ROOT)),
                      printed_variant='Winner' if 'winner' in source else 'Standard')
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    return result


payload = json.loads(DATA.read_text())
cards = [c for c in payload['cards'] if not c['images'].get('small')]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(process, cards))
for card, result in zip(cards, results):
    if result['status'] == 'saved':
        card['images']['small'] = './' + result['output']
DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
(ROOT / 'data/bog_missing_images_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
if any(x['status'] != 'saved' for x in results):
    raise SystemExit(1)
