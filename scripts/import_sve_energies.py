"""Import all 24 individually numbered Scarlet & Violet Energy scans."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/sve.json"
data = json.loads(set_path.read_text())
assert len(data["cards"]) == 24 and all(not c["images"]["small"] for c in data["cards"])
page_url = "https://pkmncards.com/set/scarlet-violet-energy/"
request = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
page = urllib.request.urlopen(request, timeout=40).read().decode()
type_names = {"G": "Grass", "R": "Fire", "W": "Water", "L": "Lightning",
              "P": "Psychic", "F": "Fighting", "D": "Darkness", "M": "Metal"}
entries = []
for article in re.findall(r"<article\b.*?</article>", page, re.S):
    match = re.search(r'title="Basic \{([A-Z])\} Energy · Scarlet &#038; Violet Energy \(SVE\) #(\d+)"[^>]*class="card-image-link"><img[^>]*src="([^\"]+)', article)
    if match:
        type_code, number, url = match.groups()
        entries.append((number, type_names[type_code] + " Energy", url))
entries.sort()
assert len(entries) == 24 and [number for number, _, _ in entries] == [f"{n:03d}" for n in range(1, 25)]
for card, (number, name, _) in zip(data["cards"], entries):
    assert (card["number"], card["name"]) == (number, name)

def fetch(entry):
    number, name, url = entry
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return number, name, url, urllib.request.urlopen(request, timeout=50).read()

with ThreadPoolExecutor(max_workers=6) as pool:
    downloads = list(pool.map(fetch, entries))

target = ROOT / "assets/sets/sve"
target.mkdir(parents=True, exist_ok=True)
report = []
for number, name, url, raw in downloads:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = image.size
    assert w >= 730 and h == 1024, (number, image.size)
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=28, fill=255)
    image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(image, (18, 18))
    buffer = io.BytesIO()
    canvas.save(buffer, "PNG", optimize=True)
    Image.open(io.BytesIO(buffer.getvalue())).load()
    output = target / f"{number}.png"
    output.write_bytes(buffer.getvalue())
    Image.open(output).load()
    report.append({"number": number, "name": name, "source": url,
                   "source_size": [w, h], "path": str(output.relative_to(ROOT))})

for card in data["cards"]:
    card["images"]["small"] = f"./assets/sets/sve/{card['number']}.png"
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/sve-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
