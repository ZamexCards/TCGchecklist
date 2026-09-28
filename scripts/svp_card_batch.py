#!/usr/bin/env python3
"""Archive verified SVP promo images with the approved transparent card treatment."""
import argparse
import concurrent.futures
import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/svp.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=35) as response:
        return response.read()


def process(card):
    number, name = card['number'], card['name']
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    page = f'https://pkmncards.com/card/{slug}-scarlet-violet-promos-svp-{number}/'
    result = {'number': number, 'name': name, 'page': page}
    try:
        body = fetch(page).decode('utf-8', 'replace')
        title_match = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
        title = html.unescape(title_match.group(1)) if title_match else ''
        normalized = title.lower().replace('’', "'")
        if not all(token in normalized for token in (name.lower(), 'svp', f'#{number}')):
            raise ValueError(f'Card identity mismatch: {title}')
        sources = re.findall(
            rf'https://pkmncards\.com/wp-content/uploads/svbsp_en_{number}_std(?:-\d+)?\.(?:jpg|png)',
            body, re.I,
        )
        sources += re.findall(
            rf'https://pkmncards\.com/wp-content/uploads/SVP_{number}_R_EN\.png', body, re.I,
        )
        sources = list(dict.fromkeys(sources))
        sources.sort(key=lambda url: (not url.lower().endswith('.jpg'), '-1.' in url))
        if not sources:
            raise ValueError('No matching numbered source image')
        source = sources[0]
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size not in ((733, 1024), (734, 1024)):
                raise ValueError(f'Unexpected image size: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/svp/{number}.png'
        target.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', source=source, output=str(target.relative_to(ROOT)), size=list(canvas.size))
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('numbers', nargs='+', help='Exact SVP numbers to process')
    args = parser.parse_args()
    if len(args.numbers) > 20:
        parser.error('Use batches of at most 20')
    payload = json.loads(DATA.read_text())
    by_number = {card['number']: card for card in payload['cards']}
    if any(n not in by_number or by_number[n]['images'].get('small') for n in args.numbers):
        parser.error('Every number must exist and currently lack a local image')
    cards = [by_number[n] for n in args.numbers]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(process, cards))
    for card, result in zip(cards, results):
        if result['status'] == 'saved':
            card['images']['small'] = './' + result['output']
    DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    report = ROOT / f'data/svp_batch_{args.numbers[0]}_{args.numbers[-1]}_report.json'
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(result['status'] != 'saved' for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
