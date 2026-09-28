"""Import McDonald's Collection 2024 card scans from Pooka."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "data/sets/2024sv.json"
data = json.loads(SET_PATH.read_text())
assert len(data["cards"]) == 15
target = ROOT / "assets/sets/2024sv"
target.mkdir(parents=True, exist_ok=True)

def download_card(card):
    url = f"https://cdn.pooka.app/card/en-mcd24-{int(card['number'])}.png?size=large"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return card, url, urllib.request.urlopen(request, timeout=30).read()

def import_card(download):
    card, url, content = download
    original = Image.open(io.BytesIO(content)).convert("RGBA")
    if original.size != (750, 1049):
        raise ValueError((card["number"], original.size))
    scan = original.resize((728, 1016), Image.Resampling.LANCZOS)
    mask = Image.new("L", scan.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
    scan.putalpha(ImageChops.multiply(scan.getchannel("A"), mask))
    canvas = Image.new("RGBA", (764, 1052))
    canvas.alpha_composite(scan, (18, 18))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    output = buffer.getvalue()
    Image.open(io.BytesIO(output)).load()
    filename = f"{int(card['number']):03d}.png"
    (target / filename).write_bytes(output)
    Image.open(target / filename).load()
    return {"number": card["number"], "name": card["name"], "source": url,
            "path": f"assets/sets/2024sv/{filename}"}

with ThreadPoolExecutor(max_workers=8) as pool:
    downloads = list(pool.map(download_card, data["cards"]))
report = [import_card(item) for item in downloads]
for card in data["cards"]:
    card["images"]["small"] = f"./assets/sets/2024sv/{int(card['number']):03d}.png"
SET_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/2024sv-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
