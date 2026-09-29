"""Replace generic Lycanroc Trainer Kit energy art with numbered card scans."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "2": "https://static.tcgcollector.com/content/images/52/64/b9/5264b9c3397e4fbfc83a0943e2f82da48b9d4d8c0e9d3ff51ae69f7d8f1150fa.jpg",
    "3": "https://static.tcgcollector.com/content/images/87/61/b3/8761b367289c80cd66ef8459ad19ec501b0fba02d39b129a74fb843d415714bb.jpg",
    "5": "https://static.tcgcollector.com/content/images/ba/3a/0e/ba3a0e0c843d2a2eec1a90e3b9ed730a3c2096ea9cd2b249ee09b1fd34721568.jpg",
    "6": "https://static.tcgcollector.com/content/images/54/84/ab/5484ab25b4ee5957dd1df6432e68dc389ef08bbed68907d014b579cd2b971f8a.jpg",
    "7": "https://static.tcgcollector.com/content/images/06/21/81/0621811ac83aac4bc57fef2e60a86cc703cba367213adcc6b00aee0a8e969fb7.jpg",
    "8": "https://static.tcgcollector.com/content/images/48/a0/c3/48a0c394675bf228e9e129bcbf058e74df0c822fc2b18d887c43d0b13b8bd7fb.jpg",
    "9": "https://static.tcgcollector.com/content/images/83/91/bb/8391bb9971ffdae3ea48afde1bac4746a2d94985ce15a9f3741e6e19c4e1687b.jpg",
    "10": "https://static.tcgcollector.com/content/images/ae/7a/42/ae7a425efa10bcdf882a36e768d04dacb88e72a386a389ce1c15f0460c0629ea.jpg",
    "17": "https://static.tcgcollector.com/content/images/1b/00/bd/1b00bda5c82778329695aff805996155672135849b2a4ddfd20ae6d66f37b94c.jpg",
    "20": "https://static.tcgcollector.com/content/images/03/22/60/0322609d46723efcbd882f1a58fa28ad36ab36b7b7a96abb2d5e8f1b1d1ea70f.jpg",
    "24": "https://static.tcgcollector.com/content/images/b2/7a/14/b27a14b540737c75ec171142b6cc91008474a18ed40b803d1505a1fda4e53614.jpg",
    "26": "https://static.tcgcollector.com/content/images/e1/d4/5f/e1d45ff8e3748f6acfc6ba413d975947d6ab6952b042a94735e9f0bacf134999.jpg",
    "28": "https://static.tcgcollector.com/content/images/9f/56/f0/9f56f0abd278bfebd571f6c922aca41f6045ac921d9ac307c14ef4c70b80af14.jpg"
}
SOURCES = {int(k): v for k, v in SOURCES.items()}
assert len(SOURCES) == 13

def fetch(entry):
    number, url = entry
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return number, url, urllib.request.urlopen(request, timeout=50).read()

with ThreadPoolExecutor(max_workers=5) as pool:
    scans = list(pool.map(fetch, SOURCES.items()))

target = ROOT / "assets/sets/tk-sm-l"
source_report = ROOT / "data/tk-sm-l-image-sources.json"
report = json.loads(source_report.read_text())
by_number = {int(e["number"]): e for e in report}
for number, url, raw in scans:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = image.size
    assert w >= 250 and h >= 350, (number, image.size)
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=7, fill=255)
    image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
    canvas = Image.new("RGBA", (w + 36, h + 36))
    canvas.alpha_composite(image, (18, 18))
    output = target / f"{number:03d}.png"
    buffer = io.BytesIO()
    canvas.save(buffer, "PNG", optimize=True)
    Image.open(io.BytesIO(buffer.getvalue())).load()
    output.write_bytes(buffer.getvalue())
    Image.open(output).load()
    by_number[number]["source"] = url
    by_number[number]["source_size"] = [w, h]
source_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
