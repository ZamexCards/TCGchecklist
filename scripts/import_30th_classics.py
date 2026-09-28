"""Import the 30th Celebration Classic Collection card scans from Serebii."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SET_PATH = ROOT / "data/sets/30th-c.json"
set_data = json.loads(SET_PATH.read_text())

# The Serebii H image numbers follow the printed vintage numbers rather than
# the synthetic 001–030 checklist order. H16/H17 are the LEGEND halves.
source_numbers = [2, 8, 11, 20, 3, 9, 5, 25, 22, 13, 14, 27, 24, 1, 4,
                  19, 23, 15, 16, 17, 18, 12, 21, 6, 10, 28, 29, 26, 7, 30]
assert len(set_data["cards"]) == len(source_numbers) == 30
target_dir = ROOT / "assets/sets/30th-c"
target_dir.mkdir(parents=True, exist_ok=True)

def import_card(pair):
    card, source_number = pair
    url = f"https://www.serebii.net/card/30thcelebration/h{source_number}.jpg"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    source = Image.open(io.BytesIO(urllib.request.urlopen(request, timeout=30).read())).convert("RGBA")
    if source.size != (660, 920):
        raise ValueError((card["number"], source.size))
    scan = source.resize((728, 1016), Image.Resampling.LANCZOS)
    mask = Image.new("L", scan.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
    scan.putalpha(ImageChops.multiply(scan.getchannel("A"), mask))
    canvas = Image.new("RGBA", (764, 1052))
    canvas.alpha_composite(scan, (18, 18))
    path = target_dir / (card["number"] + ".png")
    canvas.save(path, optimize=True)
    return {"number": card["number"], "name": card["name"], "source": url,
            "path": str(path.relative_to(ROOT))}

with ThreadPoolExecutor(max_workers=8) as pool:
    report = list(pool.map(import_card, zip(set_data["cards"], source_numbers)))

for card in set_data["cards"]:
    card["images"]["small"] = f"./assets/sets/30th-c/{card['number']}.png"
SET_PATH.write_text(json.dumps(set_data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/30th-c-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
