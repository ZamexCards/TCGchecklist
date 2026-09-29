"""Import the missing Tropical Tidal Wave promo scan."""
import io
import json
import urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/hgssp.json"
data = json.loads(set_path.read_text())
missing = [c for c in data["cards"] if not c["images"]["small"]]
assert [(c["number"], c["name"]) for c in missing] == [("HGSS18", "Tropical Tidal Wave")]
url = "https://www.pokemonkaart.nl/wp-content/uploads/HeartGold-SoulSilver-Promos_Tropical-Tidal-Wave.png"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(request, timeout=40).read()
image = Image.open(io.BytesIO(raw)).convert("RGBA")
assert image.size == (734, 1024)
assert image.getpixel((0, 0))[3] == 0
target = ROOT / "assets/sets/hgssp/HGSS18.png"
target.parent.mkdir(parents=True, exist_ok=True)
image.save(target, "PNG", optimize=True)
Image.open(target).load()
missing[0]["images"]["small"] = "./assets/sets/hgssp/HGSS18.png"
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/hgssp-hgss18-image-source.json").write_text(json.dumps({
    "number": "HGSS18", "name": "Tropical Tidal Wave", "source": url,
    "source_size": list(image.size), "path": "assets/sets/hgssp/HGSS18.png"
}, ensure_ascii=False, indent=2) + "\n")
