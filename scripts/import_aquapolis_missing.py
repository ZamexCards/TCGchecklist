"""Add the missing Aquapolis holo and e-Reader variants with source provenance."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/ecard2.json"
data = json.loads(set_path.read_text())
cards = [c for c in data["cards"] if not c["images"]["small"]]
assert len(cards) == 17

page = urllib.request.urlopen("https://pkmncards.com/set/aquapolis/", timeout=40).read().decode()
holo_urls = {}
for article in re.findall(r"<article\b.*?</article>", page, re.S):
    match = re.search(r'title="([^\"]+) · Aquapolis \(AQ\) #(H[1-9])"[^>]*class="card-image-link"><img[^>]*src="([^\"]+)', article)
    if match:
        name, number, url = match.groups()
        holo_urls[f"H{int(number[1:]):02d}"] = (name, url)
assert len(holo_urls) == 9

variant_urls = {
    "50a": "https://images.wikidexcdn.net/mwuploads/wikidex/e/e9/latest/20220918151232/Golduck_%28Aquapolis_TCG%29.png",
    "50b": "https://images.wikidexcdn.net/mwuploads/wikidex/9/94/latest/20260710144335/Golduck_%28Aquapolis_50b_TCG%29.png",
    "74a": "https://images.wikidexcdn.net/mwuploads/wikidex/a/a0/latest/20260703133632/Drowzee_%28Aquapolis_74a_TCG%29.png",
    "74b": "https://images.wikidexcdn.net/mwuploads/wikidex/1/11/latest/20260703133721/Drowzee_%28Aquapolis_74b_TCG%29.png",
    "95a": "https://images.wikidexcdn.net/mwuploads/wikidex/9/9c/latest/20260711213833/Mr._Mime_%28Aquapolis_95a_TCG%29.png",
    "95b": "https://images.wikidexcdn.net/mwuploads/wikidex/d/d6/latest/20260711213855/Mr._Mime_%28Aquapolis_95b_TCG%29.png",
    "103a": "https://images.wikidexcdn.net/mwuploads/wikidex/6/66/latest/20260614142916/Porygon_%28Aquapolis_103a_TCG%29.png",
    "103b": "https://d1rv4ufwpgk2kk.cloudfront.net/88307.jpg",
}

def fetch(card):
    number = card["number"]
    if number.startswith("H"):
        name, url = holo_urls[number]
        assert name == card["name"]
    else:
        url = variant_urls[number]
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return card, url, urllib.request.urlopen(req, timeout=60).read()

with ThreadPoolExecutor(max_workers=5) as pool:
    downloads = list(pool.map(fetch, cards))

target = ROOT / "assets/sets/ecard2"
target.mkdir(parents=True, exist_ok=True)
report = []
for card, url, raw in downloads:
    source = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = source.size
    assert w >= 200 and h >= 280, (card["number"], source.size)
    mask = Image.new("L", (w, h))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=max(8, round(w * .027)), fill=255)
    source.putalpha(ImageChops.multiply(source.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(source, (18, 18))
    buf = io.BytesIO()
    canvas.save(buf, "PNG", optimize=True)
    Image.open(io.BytesIO(buf.getvalue())).load()
    path = target / f"{card['number']}.png"
    path.write_bytes(buf.getvalue())
    Image.open(path).load()
    card["images"]["small"] = f"./assets/sets/ecard2/{card['number']}.png"
    report.append({"number": card["number"], "name": card["name"], "source": url,
                   "source_size": [w, h], "path": str(path.relative_to(ROOT))})

assert all(c["images"]["small"] for c in data["cards"])
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/ecard2-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
