"""Archive individually numbered XY Trainer Kit Latias energy card photos."""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    1: "https://i.ebayimg.com/images/g/ujYAAeSwl~pqtYni/s-l1600.jpg",
    2: "https://i.ebayimg.com/images/g/T4kAAeSwMeVqfkl4/s-l1600.jpg",
    3: "https://i.ebayimg.com/images/g/2sMAAeSwGdhqsKSN/s-l1600.jpg",
    5: "https://i.ebayimg.com/images/g/ejQAAeSw2G9qhS47/s-l1600.jpg",
    8: "https://i.ebayimg.com/images/g/EvQAAeSwUkpqhS3A/s-l1600.jpg",
    9: "https://i.ebayimg.com/images/g/xXIAAeSwfDJqf-CF/s-l1600.jpg",
    10: "https://i.ebayimg.com/images/g/hVQAAeSwG~dquuQ5/s-l1600.jpg",
    17: "https://i.ebayimg.com/images/g/a-sAAeSwd3dqfkl3/s-l1600.jpg",
    19: "https://i.ebayimg.com/images/g/g58AAeSw3ehqTSNb/s-l1600.jpg",
    22: "https://i.ebayimg.com/images/g/Ug8AAeSwGAhqtYni/s-l1600.jpg",
    28: "https://i.ebayimg.com/images/g/VqQAAeSw5UJqfki3/s-l1600.jpg",
}

report_path = ROOT / "data/tk-xy-latia-image-sources.json"
report = json.loads(report_path.read_text())
by_number = {int(entry["number"]): entry for entry in report}

for number, url in SOURCES.items():
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(request, timeout=45).read()
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    pixels = np.asarray(image)
    red, green, blue = [pixels[:, :, i].astype("int16") for i in range(3)]
    yellow = ((red > 145) & (green > 110) & (blue < 160)
              & (red > blue * 1.5) & (green > blue * 1.35))
    ys, xs = np.where(yellow)
    assert len(xs) > image.width * image.height * .02, (number, image.size)
    box = (max(0, int(xs.min()) - 6), max(0, int(ys.min()) - 6),
           min(image.width, int(xs.max()) + 7),
           min(image.height, int(ys.max()) + 7))
    card = image.crop(box).convert("RGBA")
    width, height = card.size
    assert .65 < width / height < .85 and width >= 500 and height >= 700, (number, box)
    mask = Image.new("L", card.size)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, width - 1, height - 1), radius=max(10, width // 25), fill=255)
    card.putalpha(mask)
    canvas = Image.new("RGBA", (width + 30, height + 30))
    canvas.alpha_composite(card, (15, 15))
    output = ROOT / f"assets/sets/tk-xy-latia/{number:03d}.png"
    temporary = output.with_suffix(".tmp.png")
    canvas.save(temporary, "PNG")
    Image.open(temporary).verify()
    temporary.replace(output)
    by_number[number]["source"] = url
    by_number[number]["source_size"] = list(image.size)
    by_number[number]["crop_box"] = list(box)

report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print("Archived", len(SOURCES), "numbered energy photos")
