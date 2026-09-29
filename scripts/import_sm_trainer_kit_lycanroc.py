"""Import all 30 numbered SM Trainer Kit (Lycanroc) cards."""
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
set_path = ROOT / "data/sets/tk-sm-l.json"
data = json.loads(set_path.read_text())
assert data["set"]["printedTotal"] == 30
page_url = "https://www.pokemonkaart.nl/set/sm-trainer-kit-lycanroc"
request = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
page = urllib.request.urlopen(request, timeout=40).read().decode()
entries = []
for fragment in re.findall(r'<a href="/kaart/[^" ]+" class="card-tile">(.*?)</a>', page, re.S):
    number = re.search(r'<span class="card-number">(\d+)/30</span>', fragment)
    name = re.search(r'<div class="card-name">([^<]+)</div>', fragment)
    image = re.search(r'<img src="([^\"]+)', fragment)
    if number and name and image:
        entries.append((int(number[1]), name[1], "https://www.pokemonkaart.nl" + image[1]))
entries.sort()
assert len(entries) == 30 and [e[0] for e in entries] == list(range(1, 31))

known = {int(c["number"]): c for c in data["cards"]}
assert len(known) == 18
for number, name, _ in entries:
    if number in known:
        assert known[number]["name"] == name
    else:
        assert name == "Fighting Energy", (number, name)
        known[number] = {
            "id": f"tk-sm-l-{number}", "name": name, "number": str(number),
            "supertype": "Energy", "subtypes": [], "types": [], "rarity": "Common",
            "images": {"small": ""}, "availableVariants": ["Base"]
        }

def fetch(entry):
    number, name, url = entry
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return number, name, url, urllib.request.urlopen(request, timeout=60).read()

with ThreadPoolExecutor(max_workers=6) as pool:
    downloads = list(pool.map(fetch, entries))

target = ROOT / "assets/sets/tk-sm-l"
target.mkdir(parents=True, exist_ok=True)
report = []
for number, name, url, raw in downloads:
    source = Image.open(io.BytesIO(raw))
    source.load()
    assert source.size == (734, 1024), (number, source.size)
    assert source.mode == "RGBA" and source.getpixel((0, 0))[3] == 0
    output = target / f"{number:03d}.png"
    output.write_bytes(raw)
    Image.open(output).load()
    known[number]["images"]["small"] = f"./assets/sets/tk-sm-l/{number:03d}.png"
    report.append({"number": str(number), "name": name, "source": url,
                   "source_size": list(source.size), "path": str(output.relative_to(ROOT))})

data["cards"] = [known[n] for n in range(1, 31)]
assert all(c["images"]["small"] for c in data["cards"])
data["set"]["total"] = 30
set_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
(ROOT / "data/tk-sm-l-image-sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
