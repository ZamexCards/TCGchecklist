#!/usr/bin/env python3
"""Archive a verified numbered batch of MEP promos with the approved 001 treatment."""
import argparse
import concurrent.futures
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/mep.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=35) as response:
        return response.read()


def process(card):
    number, name = card['number'], card['name']
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    page = f'https://pkmncards.com/card/{slug}-mega-evolution-promos-mep-{number}/'
    result = {'number': number, 'name': name, 'page': page}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        title_match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(title_match.group(1)) if title_match else ''
        if not all(token in title.lower() for token in (name.lower(), 'mep', f'#{number}')):
            raise ValueError(f'Card identity mismatch: {title}')
        sources = re.findall(
            rf'https://pkmncards\.com/wp-content/uploads/mebsp_en_{number}_std(?:-\d+)?\.(?:jpg|png)',
            body, re.I,
        )
        sources = list(dict.fromkeys(sources))
        sources.sort(key=lambda url: (not url.lower().endswith('.jpg'), '-1.' in url))
        if not sources:
            raise ValueError('No matching numbered source image on card page')
        source = sources[0]
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size != (733, 1024):
                raise ValueError(f'Unexpected image size: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        mask = Image.new('L', (728, 1016), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(mask)
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/mep/{number}.png'
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', source=source, output=str(target.relative_to(ROOT)), size=list(canvas.size))
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    args = parser.parse_args()
    if args.start < 2 or args.end < args.start or args.end - args.start > 19:
        parser.error('Choose 2–20 consecutive cards starting after 001')
    payload = json.loads(DATA.read_text())
    cards = [c for c in payload['cards'] if c['number'].isdigit() and args.start <= int(c['number']) <= args.end]
    if len(cards) != args.end - args.start + 1:
        parser.error('One or more card numbers are missing from the checklist')
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(process, cards))
    for card, result in zip(cards, results):
        if result['status'] == 'saved':
            card['images']['small'] = './' + result['output']
    DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    report = ROOT / f'data/mep_batch_{args.start:03d}_{args.end:03d}_report.json'
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)
    if any(result['status'] != 'saved' for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
