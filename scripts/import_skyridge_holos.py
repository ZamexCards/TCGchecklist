"""Import the first nine Skyridge holo scans from PkmnCards."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/ecard3.json"
data = json.loads(set_path.read_text())
cards = [c for c in data["cards"] if c["number"] in {f"H{i:02d}" for i in range(1, 10)}]
assert [c["name"] for c in cards] == ["Alakazam", "Arcanine", "Articuno", "Beedrill", "Crobat", "Dewgong", "Flareon", "Forretress", "Gengar"]

def fetch(card):
    number = card["number"]
    url = f"https://pkmncards.com/wp-content/uploads/h{int(number[1:]):02d}.jpg"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return card, url, urllib.request.urlopen(req, timeout=40).read()

with ThreadPoolExecutor(max_workers=5) as pool:
    downloads = list(pool.map(fetch, cards))

target = ROOT / "assets/sets/ecard3"
target.mkdir(parents=True, exist_ok=True)
report = []
for card, url, raw in downloads:
    source = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = source.size
    assert w >= 600 and h >= 825, (card["number"], source.size)
    mask = Image.new("L", (w, h))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=17, fill=255)
    source.putalpha(ImageChops.multiply(source.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(source, (18, 18))
    buf = io.BytesIO()
    canvas.save(buf, "PNG", optimize=True)
    Image.open(io.BytesIO(buf.getvalue())).load()
    path = target / f"{card['number']}.png"
    path.write_bytes(buf.getvalue())
    Image.open(path).load()
    card["images"]["small"] = f"./assets/sets/ecard3/{card['number']}.png"
    report.append({"number": card["number"], "name": card["name"], "source": url,
                   "source_size": [w, h], "path": str(path.relative_to(ROOT))})

set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/ecard3-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
