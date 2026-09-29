"""Archive the 30 numbered SM Trainer Kit (Alolan Raichu) scans."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
data_path = ROOT / 'data/sets/tk-sm-r.json'
data = json.loads(data_path.read_text())
page = urllib.request.urlopen('https://www.pokemonkaart.nl/set/sm-trainer-kit-alolan-raichu', timeout=40).read().decode()
entries = []
for part in re.findall(r'<a href="/kaart/[^" ]+" class="card-tile">(.*?)</a>', page, re.S):
    number = re.search(r'<span class="card-number">(\d+)/30</span>', part)
    name = re.search(r'<div class="card-name">([^<]+)</div>', part)
    image = re.search(r'<img src="([^"]+)', part)
    if number and name and image:
        entries.append((int(number[1]), name[1], 'https://www.pokemonkaart.nl' + image[1]))
entries.sort()
assert [n for n, _, _ in entries] == list(range(1, 31))
cards = {int(c['number']): c for c in data['cards']}
assert all(cards[n]['name'] == name for n, name, _ in entries)

def fetch(item):
    n, name, url = item
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return n, name, url, urllib.request.urlopen(req, timeout=60).read()

with ThreadPoolExecutor(max_workers=6) as pool:
    downloads = list(pool.map(fetch, entries))
target = ROOT / 'assets/sets/tk-sm-r'
target.mkdir(parents=True, exist_ok=True)
report = []
for n, name, url, raw in downloads:
    im = Image.open(io.BytesIO(raw))
    im.load()
    assert im.width >= 250 and im.height >= 350, (n, im.size)
    if n == 25 and im.mode == 'RGB':
        im = im.convert('RGBA')
        mask = Image.new('L', im.size)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=14, fill=255)
        im.putalpha(mask)
    else:
        assert im.mode == 'RGBA' and im.getpixel((0, 0))[3] == 0, (n, im.mode)
    path = target / f'{n:03d}.png'
    if im.format != 'PNG':
        im.save(path, 'PNG', optimize=True)
    else:
        path.write_bytes(raw)
    cards[n]['images']['small'] = f'./assets/sets/tk-sm-r/{n:03d}.png'
    report.append({'number': str(n), 'name': name, 'source': url, 'source_size': [im.width, im.height], 'path': str(path.relative_to(ROOT))})
data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'data/tk-sm-r-image-sources.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('Archived', len(report), 'scans')
