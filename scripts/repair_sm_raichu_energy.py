"""Replace repeated generic energy art with unique numbered card scans."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
  1: "https://static.tcgcollector.com/content/images/be/73/3a/be733aec733f8707d748a0e60536c50fdbfefff115187891f778499c1694eeed.jpg",
  2: "https://static.tcgcollector.com/content/images/fc/a0/07/fca0075a42fed09a4e6bb7122a9a8a7ec50488b158cbaf7a9e01e1216ca3f552.jpg",
  3: "https://static.tcgcollector.com/content/images/41/46/18/41461818a3ae5ea1f194bea08414c22954a2e73c193b01dae114b07e0c226a6f.jpg",
  5: "https://static.tcgcollector.com/content/images/f6/5f/f6/f65ff6c0731b2cb4a406b5d382caa5aac24c5c4b26189e20e2b8d6d45ea19cca.jpg",
  7: "https://static.tcgcollector.com/content/images/72/db/d9/72dbd9ad4693bf25d984de393dc1a8c9c87e606e62a50bef984607adac440b3a.jpg",
  8: "https://static.tcgcollector.com/content/images/28/27/de/2827de4718d608b069983ecf161999df533182c0693e31b061d0bba7affeb96e.jpg",
  9: "https://static.tcgcollector.com/content/images/b3/8c/72/b38c7212036185e7b46d0e004c2c922eccd22159456e8fa6132857d4f4f69f7a.jpg",
  10: "https://static.tcgcollector.com/content/images/d5/ae/cc/d5aecc9d52f6d77dc97893edd552a393f7e5d292ecda4335c48c0e367b446152.jpg",
  12: "https://static.tcgcollector.com/content/images/46/60/79/46607917b4c29d01f23487dde0c98bd01b808591088ce308a13dccb5acdcee0a.jpg",
  20: "https://static.tcgcollector.com/content/images/45/fb/eb/45fbebae5ddc9edb1561a5754ce1f82d74cd3eb9399975ce565d4c304e1078e0.jpg",
  24: "https://static.tcgcollector.com/content/images/76/9b/3d/769b3d2b457594962337e4f7f86128f3aa58fc84c4ea1d23e6378426d947d7e1.jpg",
  27: "https://static.tcgcollector.com/content/images/30/95/62/30956222504563ed2b2e76f7ae911e78241fcb2150cad762315d05ecf327cc57.jpg",
  28: "https://static.tcgcollector.com/content/images/fe/1d/4e/fe1d4e5e86bac0e1526fca19e4345c8cf6d74e8d32be97d182d45d358d7b96b5.jpg"
} 


def fetch(item):
    number, url = item
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return number, url, urllib.request.urlopen(req, timeout=45).read()

with ThreadPoolExecutor(max_workers=5) as pool:
    scans = list(pool.map(fetch, SOURCES.items()))
report_path = ROOT / 'data/tk-sm-r-image-sources.json'
report = json.loads(report_path.read_text())
by_number = {int(e['number']): e for e in report}
for number, url, raw in scans:
    im = Image.open(io.BytesIO(raw)).convert('RGBA')
    w, h = im.size
    assert w >= 250 and h >= 350, (number, im.size)
    mask = Image.new('L', im.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=7, fill=255)
    im.putalpha(mask)
    canvas = Image.new('RGBA', (w + 36, h + 36))
    canvas.alpha_composite(im, (18, 18))
    canvas.save(ROOT / f'assets/sets/tk-sm-r/{number:03d}.png', 'PNG', optimize=True)
    by_number[number]['source'] = url
    by_number[number]['source_size'] = [w, h]
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('Replaced', len(scans), 'numbered energy scans')
