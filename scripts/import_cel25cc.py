"""Import the 25 Celebrations Classic Collection scans from PkmnCards."""
import html
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PAGE = "https://pkmncards.com/set/celebrations/"
markup = urllib.request.urlopen(PAGE, timeout=30).read().decode()
sources = []
for article in re.findall(r'<article class="type-pkmn_card entry".*?</article>', markup):
    match = re.search(r'<a href="([^"]+)" title="([^"]+)" class="card-image-link"><img[^>]+src="([^"]+)"', article)
    if match and "Ann25thR" in match[3]:
        sources.append({"name": html.unescape(match[2].split(" · ")[0]), "source": match[3].replace(".jpg", ".png")})

set_path = ROOT / "data/sets/cel25cc.json"
set_data = json.loads(set_path.read_text())
assert len(sources) == len(set_data["cards"]) == 25
target_dir = ROOT / "assets/sets/cel25cc"
target_dir.mkdir(parents=True, exist_ok=True)
def import_card(pair):
    card, source = pair
    number = card["number"]
    original = Image.open(io.BytesIO(urllib.request.urlopen(source["source"], timeout=30).read())).convert("RGBA")
    if original.size != (734, 1024):
        raise ValueError((number, original.size))
    scan = original.resize((728, 1016), Image.Resampling.LANCZOS)
    mask = Image.new("L", scan.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 727, 1015), radius=25, fill=255)
    scan.putalpha(ImageChops.multiply(scan.getchannel("A"), mask))
    canvas = Image.new("RGBA", (764, 1052))
    canvas.alpha_composite(scan, (18, 18))
    path = target_dir / f"{number}.png"
    canvas.save(path, optimize=True)
    card["images"]["small"] = f"./assets/sets/cel25cc/{number}.png"
    return {"number": number, "name": card["name"], "source_name": source["name"], "source": source["source"], "path": str(path.relative_to(ROOT))}

with ThreadPoolExecutor(max_workers=8) as pool:
    report = list(pool.map(import_card, zip(set_data["cards"], sources)))

set_path.write_text(json.dumps(set_data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/cel25cc-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
