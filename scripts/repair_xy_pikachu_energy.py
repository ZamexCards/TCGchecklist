"""Use individual numbered scans for Pikachu Libre Trainer Kit energies."""
import io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
  2: "https://static.tcgcollector.com/content/images/93/47/f1/9347f10f6ba80667afcdfae7f84337cb955d5ab7cb7f09d6fc8f85ae85cf61bb.jpg",
  3: "https://static.tcgcollector.com/content/images/a2/b3/8d/a2b38d726a2f917e66571d8d82c5fb8e7400e028faed5613c7d9e8587ff42155.jpg",
  5: "https://static.tcgcollector.com/content/images/79/6e/82/796e82496836a45cf196dd7f1166ae9be74b79c6f32857eb2fde7e9c5fb50fa3.jpg",
  6: "https://static.tcgcollector.com/content/images/79/d9/4a/79d94a84464eda956c3b99de9c5910659872a7a535f4a27794834d19f77f0dfb.jpg",
  8: "https://static.tcgcollector.com/content/images/4a/83/34/4a83346c9826b0d8f5845c5d4cd55e0b5ee1d145bd5f52cb3bea40389dbd5801.jpg",
  10: "https://static.tcgcollector.com/content/images/72/28/8f/72288f38c6ef02b6ff4037a93bfcedf01a72bbe97371a292651f3f796afaa5cd.jpg",
  17: "https://static.tcgcollector.com/content/images/dc/fc/1a/dcfc1aaaa106969f83d38c5f707d93bacf8f26c8cfdfedd6857365da898983a1.jpg",
  18: "https://static.tcgcollector.com/content/images/ae/1b/2b/ae1b2b71efbbf2304c1150b90270b5a52cc65eba0c8b1d43aa4aefe09f5221d0.jpg"
}
PHOTOS={9:('https://i.ebayimg.com/images/g/-08AAeSwt5BqPBgG/s-l1600.jpg',(104,93,1122,1502)),29:('https://i.ebayimg.com/images/g/32cAAeSwHgVoogY9/s-l1600.jpg',(82,55,1143,1538))}
def fetch(item):
 n,url=item
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read()
 return n,url,raw
with ThreadPoolExecutor(max_workers=5) as pool:scans=list(pool.map(fetch,list(SOURCES.items())+[(n,u) for n,(u,_) in PHOTOS.items()]))
report_path=ROOT/'data/tk-xy-p-image-sources.json';report=json.loads(report_path.read_text());by_number={int(e['number']):e for e in report}
for n,url,raw in scans:
 im=Image.open(io.BytesIO(raw)).convert('RGBA')
 if n in PHOTOS:
  im=im.crop(PHOTOS[n][1]);radius=45
 else:radius=7
 w,h=im.size
 assert w>=250 and h>=350,(n,im.size)
 mask=Image.new('L',(w,h))
 ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=radius,fill=255)
 im.putalpha(mask)
 canvas=Image.new('RGBA',(w+36,h+36));canvas.alpha_composite(im,(18,18))
 canvas.save(ROOT/f'assets/sets/tk-xy-p/{n:03d}.png','PNG',optimize=True)
 by_number[n]['source']=url
 by_number[n]['source_size']=[w,h]
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Unique energy scans',len(scans))
