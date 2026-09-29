"""Import the eleven DP Trainer Kit (Lucario) card scans."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/tk-dp-l.json"
data = json.loads(set_path.read_text())
assert len(data["cards"]) == 11 and all(not c["images"]["small"] for c in data["cards"])
page_url = "https://www.pokemonkaart.nl/set/dp-trainer-kit-lucario"
page = urllib.request.urlopen(page_url, timeout=40).read().decode()
entries = []
for fragment in re.findall(r'<a href="/kaart/[^" ]+" class="card-tile">(.*?)</a>', page, re.S):
    number = re.search(r'<span class="card-number">(\d+)/11</span>', fragment)
    name = re.search(r'<div class="card-name">([^<]+)</div>', fragment)
    image = re.search(r'<img src="([^\"]+)', fragment)
    if number and name and image:
        entries.append((int(number[1]), name[1], "https://www.pokemonkaart.nl" + image[1]))
entries.sort()
assert len(entries) == 11
for card, (number, name, _) in zip(data["cards"], entries):
    assert (int(card["number"]), card["name"]) == (number, name)

def fetch(entry):
    number, name, url = entry
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return number, name, url, urllib.request.urlopen(request, timeout=50).read()

with ThreadPoolExecutor(max_workers=5) as pool:
    downloads = list(pool.map(fetch, entries))

target = ROOT / "assets/sets/tk-dp-l"
target.mkdir(parents=True, exist_ok=True)
report = []
for number, name, url, raw in downloads:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = image.size
    assert w >= 300 and h >= 420, (number, image.size)
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=max(8, round(w * .027)), fill=255)
    image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(image, (18, 18))
    output = target / f"{number:03d}.png"
    buffer = io.BytesIO()
    canvas.save(buffer, "PNG", optimize=True)
    Image.open(io.BytesIO(buffer.getvalue())).load()
    output.write_bytes(buffer.getvalue())
    Image.open(output).load()
    assert Image.open(output).getpixel((0, 0))[3] == 0
    report.append({"number": str(number), "name": name, "source": url,
                   "source_size": [w, h], "path": str(output.relative_to(ROOT))})

for card in data["cards"]:
    card["images"]["small"] = f"./assets/sets/tk-dp-l/{int(card['number']):03d}.png"
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/tk-dp-l-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
