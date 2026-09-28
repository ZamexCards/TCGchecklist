#!/usr/bin/env python3
"""Fill MEP 055–063 from individually identified Pokedexia card images."""
import concurrent.futures
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/sets/mep.json'
PAGE = 'https://pokedexia.com/en/pokemon-cards/sets/mega-evolution-mep-black-star-promos'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        return response.read()


def process(card, body):
    number, name = card['number'], card['name']
    result = {'number': number, 'name': name, 'page': PAGE}
    try:
        marker = f'title="{name} MEP {number}"'
        index = body.find(marker)
        if index < 0:
            raise ValueError('Exact card name and number missing from set page')
        section = body[index:index + 6500]
        match = re.search(
            rf'https://cdn\.pokedexia\.com/cards/me/MEP/cards/en/mep-{number}-low\.webp',
            section,
        )
        if not match:
            raise ValueError('Expected numbered card image missing from set page')
        source = match.group(0).replace('-low.webp', '-high.webp')
        with Image.open(io.BytesIO(fetch(source))) as original:
            if original.size != (420, 585):
                raise ValueError(f'Unexpected image size: {original.size}')
            image = original.convert('RGBA').resize((728, 1016), Image.Resampling.LANCZOS)
        # Keep the original anti-aliased card silhouette while matching MEP 001 padding.
        mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
        image.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
        canvas = Image.new('RGBA', (764, 1052), (0, 0, 0, 0))
        canvas.alpha_composite(image, (18, 18))
        target = ROOT / f'assets/sets/mep/{number}.png'
        canvas.save(target, format='PNG', optimize=True)
        result.update(status='saved', source=source, source_size=[420, 585], output=str(target.relative_to(ROOT)))
    except Exception as exc:
        result.update(status='failed', error=str(exc))
    return result


def main():
    payload = json.loads(DATA.read_text())
    cards = [card for card in payload['cards'] if card['number'] in {f'{n:03d}' for n in range(55, 64)}]
    body = fetch(PAGE).decode('utf-8', 'replace')
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda card: process(card, body), cards))
    for card, result in zip(cards, results):
        if result['status'] == 'saved':
            card['images']['small'] = './' + result['output']
    DATA.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    (ROOT / 'data/mep_first_partner_fallback_report.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + '\n'
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(result['status'] != 'saved' for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
