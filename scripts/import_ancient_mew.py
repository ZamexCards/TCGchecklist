"""Add the international Ancient Mew promo with a transparent surrounding edge."""
import io
import json
import urllib.request
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/miscp.json"
data = json.loads(set_path.read_text())
assert len(data["cards"]) == 1
card = data["cards"][0]
assert (card["number"], card["name"], card["images"]["small"]) == ("001", "Ancient Mew", "")
url = "https://images.wikidexcdn.net/mwuploads/wikidex/b/b0/latest/20200922030709/Ancient_Mew_%28Miscellaneous_Promotional_cards_TCG%29.png"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(request, timeout=40).read()
image = Image.open(io.BytesIO(raw)).convert("RGBA")
assert image.size == (430, 599)
mask = Image.new("L", image.size)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=12, fill=255)
image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
canvas = Image.new("RGBA", (image.width + 36, image.height + 36))
canvas.alpha_composite(image, (18, 18))
target = ROOT / "assets/sets/miscp/001.png"
target.parent.mkdir(parents=True, exist_ok=True)
canvas.save(target, "PNG", optimize=True)
Image.open(target).load()
assert Image.open(target).getpixel((0, 0))[3] == 0
card["images"]["small"] = "./assets/sets/miscp/001.png"
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/miscp-image-source.json").write_text(json.dumps({
    "number": "001", "name": "Ancient Mew", "source": url,
    "source_size": list(image.size), "path": "assets/sets/miscp/001.png"
}, ensure_ascii=False, indent=2) + "\n")
