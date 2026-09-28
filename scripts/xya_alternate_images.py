#!/usr/bin/env python3
"""Archive the six exact Yellow A Alternate prints."""
import concurrent.futures
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/xya.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}
PAGES = {
    '24a': 'm-manectric-ex-phantom-forces-phf-24a',
    '28a': 'jolteon-ex-generations-gen-28a',
    '54a': 'zygarde-ex-fates-collide-fco-54a',
    '55a': 'm-lucario-ex-furious-fists-ffi-55a',
    '92a': 'trainers-mail-roaring-skies-ros-92a',
    '107a': 'professor-sycamore-breakpoint-bkp-107a',
}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


def process(card):
    number, name = card['number'], card['name']
    page = f'https://pkmncards.com/card/{PAGES[number]}/'
    result = {'number': number, 'name': name, 'page': page}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        title_match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(title_match.group(1)) if title_match else ''
        normalize = lambda s: s.lower().replace('’', "'")
        if not all(token in normalize(title) for token in (normalize(name), f'#{number}')):
            raise ValueError(f'Card identity mismatch: {title}')
        sources = list(dict.fromkeys(re.findall(
            rf'https://pkmncards\.com/wp-content/uploads/[^"\s<>]+-{number}-[^"\s<>]+-yaa\.jpg',
            body, re.I,
        )))
        if len(sources) != 1:
            raise ValueError(f'Expected one exact alternate image, found {len(sources)}')
        source = sources[0]
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size not in ((733, 1024), (734, 1024)):
                raise ValueError(f'Unexpected source size: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(mask)
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/xya/{number}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', source=source, output=str(target.relative_to(ROOT)))
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
(ROOT / 'data/xya_alternate_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
if len(results) != 6 or any(x['status'] != 'saved' for x in results):
    raise SystemExit(1)
