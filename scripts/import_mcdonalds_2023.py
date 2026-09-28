"""Import McDonald's Match Battle 2023 card scans from PkmnCards."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "data/sets/2023sv.json"
data = json.loads(SET_PATH.read_text())
assert len(data["cards"]) == 15
target = ROOT / "assets/sets/2023sv"
target.mkdir(parents=True, exist_ok=True)

def download_card(card):
    number = int(card["number"])
    url = f"https://pkmncards.com/wp-content/uploads/m23_en_{number:03d}_std.png"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return card, url, urllib.request.urlopen(request, timeout=30).read()

def import_card(download):
    card, url, image_data = download
    number = int(card["number"])
    source = Image.open(io.BytesIO(image_data)).convert("RGBA")
    if source.size != (733, 1024):
        raise ValueError((number, source.size))
    scan = source.resize((728, 1016), Image.Resampling.LANCZOS)
    mask = Image.new("L", scan.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
    scan.putalpha(ImageChops.multiply(scan.getchannel("A"), mask))
    canvas = Image.new("RGBA", (764, 1052))
    canvas.alpha_composite(scan, (18, 18))
    filename = f"{number:03d}.png"
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    content = buffer.getvalue()
    Image.open(io.BytesIO(content)).load()
    (target / filename).write_bytes(content)
    Image.open(target / filename).load()
    return {"number": card["number"], "name": card["name"], "source": url,
            "path": f"assets/sets/2023sv/{filename}"}

with ThreadPoolExecutor(max_workers=8) as pool:
    downloads = list(pool.map(download_card, data["cards"]))
report = [import_card(download) for download in downloads]
for card in data["cards"]:
    card["images"]["small"] = f"./assets/sets/2023sv/{int(card['number']):03d}.png"
SET_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/2023sv-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
