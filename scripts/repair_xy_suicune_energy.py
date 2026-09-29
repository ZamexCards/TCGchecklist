"""Use individually numbered Water Energy scans for XY Trainer Kit Suicune."""
import io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
  1: "https://static.tcgcollector.com/content/images/93/1f/64/931f64b4e3e5ea510662fba5678d250150cf6606070ae87a16b059c8047d2a57.jpg",
  2: "https://static.tcgcollector.com/content/images/10/7d/5b/107d5be2f32beba2a0a565d6d1d70a9a3097b5b0db9b6efd0ee56b73ed20e79c.jpg",
  3: "https://static.tcgcollector.com/content/images/37/8c/a1/378ca1cd5ec9e0291cfc05f951cb90a0358a8f2d6145368fefa7b1717cd24f7c.jpg",
  5: "https://static.tcgcollector.com/content/images/57/29/c0/5729c05c0123d4df69a54cf2daf616c0dcfbe6c8593537d87afe0704963ed829.jpg",
  8: "https://static.tcgcollector.com/content/images/ae/73/04/ae7304f060e9c17a25a7bed881db5f8df3de82b1cb37924f03c50baa33015eb1.jpg",
  9: "https://static.tcgcollector.com/content/images/ae/28/9e/ae289e2d3c0350198507386d46ebc4e5e6b2eebdd6aadc2a82c194eab4408196.jpg",
  10: "https://static.tcgcollector.com/content/images/ca/1f/0b/ca1f0bea9e4f0f8e54535e3aa6466257cb6810ce59b8709c416c3b7e590d1c8d.jpg",
  17: "https://static.tcgcollector.com/content/images/9c/10/d1/9c10d187405f896e9b4712d41e085ae1fc1fc0400753f56ede109c447443dfc6.jpg",
  19: "https://static.tcgcollector.com/content/images/2e/00/49/2e004978b3da478a40c798854fe1db67bb601b69b0bd38bf97bdfd3600bb6350.jpg",
  22: "https://static.tcgcollector.com/content/images/6e/ba/ca/6ebaca5723c93c5ba6152e413631515a0d742bdba7f4f018b5443f4b7bb10233.jpg",
  28: "https://static.tcgcollector.com/content/images/d8/19/9d/d8199dded611fb32febbdd8ee61372eb0b2cff0dedc07ff6ea193f21d84a4509.jpg"
}
def fetch(item):
 n,url=item
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read()
 return n,url,raw
with ThreadPoolExecutor(max_workers=5) as pool:scans=list(pool.map(fetch,SOURCES.items()))
report_path=ROOT/'data/tk-xy-su-image-sources.json';report=json.loads(report_path.read_text());by_number={int(e['number']):e for e in report}
for n,url,raw in scans:
 im=Image.open(io.BytesIO(raw)).convert('RGBA')
 w,h=im.size
 assert w>=250 and h>=350,(n,im.size)
 mask=Image.new('L',(w,h))
 ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=7,fill=255)
 im.putalpha(mask)
 canvas=Image.new('RGBA',(w+36,h+36));canvas.alpha_composite(im,(18,18))
 canvas.save(ROOT/f'assets/sets/tk-xy-su/{n:03d}.png','PNG',optimize=True)
 by_number[n]['source']=url
 by_number[n]['source_size']=[w,h]
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Unique energy scans',len(scans))
