"""Import clean McDonald's Collection 2018 scans from Pokemonkaart.nl."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "data/sets/2018sm.json"
data = json.loads(SET_PATH.read_text())
assert len(data["cards"]) == 12
page_url = "https://www.pokemonkaart.nl/set/mcdonalds-collection-2018"
page = urllib.request.urlopen(page_url, timeout=30).read().decode()
entries = re.findall(r'<a href="/kaart/[^" ]+" class="card-tile">(.*?)</a>', page, re.S)
sources = []
for entry in entries:
    name = re.search(r'<div class="card-name">([^<]+)</div>', entry)
    number = re.search(r'<span class="card-number">(\d+)/12</span>', entry)
    image = re.search(r'<img src="([^"]+)" alt=', entry)
    if name and number and image:
        sources.append((int(number[1]), name[1], "https://www.pokemonkaart.nl" + image[1]))
sources.sort()
assert len(sources) == 12
for card, (number, name, _) in zip(data["cards"], sources):
    assert int(card["number"]) == number and card["name"] == name

target = ROOT / "assets/sets/2018sm"
target.mkdir(parents=True, exist_ok=True)

def download_card(entry):
    number, name, url = entry
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return number, name, url, urllib.request.urlopen(request, timeout=30).read()

with ThreadPoolExecutor(max_workers=8) as pool:
    downloads = list(pool.map(download_card, sources))

report = []
for number, name, url, content in downloads:
    source = Image.open(io.BytesIO(content)).convert("RGBA")
    w, h = source.size
    if w < 300 or h < 420:
        raise ValueError((number, source.size))
    mask = Image.new("L", source.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=10, fill=255)
    source.putalpha(ImageChops.multiply(source.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(source, (18, 18))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    output = buffer.getvalue()
    Image.open(io.BytesIO(output)).load()
    filename = f"{number:03d}.png"
    (target / filename).write_bytes(output)
    Image.open(target / filename).load()
    report.append({"number": str(number), "name": name, "source": url,
                   "source_size": [w, h], "path": f"assets/sets/2018sm/{filename}"})

for card in data["cards"]:
    card["images"]["small"] = f"./assets/sets/2018sm/{int(card['number']):03d}.png"
SET_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/2018sm-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
