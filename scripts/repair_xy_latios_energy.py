"""Use individually numbered Energy scans for XY Trainer Kit Latios."""
import io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
  2: "https://static.tcgcollector.com/content/images/0d/4c/06/0d4c06c3ba3835ad87f21bf2ee7e5be5ee8e7c2ab33b92d96a229662ff1baf67.jpg",
  3: "https://static.tcgcollector.com/content/images/50/48/b5/5048b53cc7436c1ff7602ce2b22abbf8502e1fc467ed64b40056f1e275745a94.jpg",
  5: "https://static.tcgcollector.com/content/images/27/7e/75/277e754f572501fdd9d9e798463752f8da7ea5753cede5ec318f7ba9cc4545fb.jpg",
  6: "https://static.tcgcollector.com/content/images/ae/84/9d/ae849da55f7c2a754c00dfa6e0755b4391ad5c4ebc63cfd3560a2711cc53e6e5.jpg",
  7: "https://static.tcgcollector.com/content/images/c0/94/37/c09437c8fbd41dfef7020afe764cc17c4a64c44153418b12b52ed0c8095ed967.jpg",
  8: "https://static.tcgcollector.com/content/images/93/fd/83/93fd83893dc85f5f9c402e259c5600784052ed4c9ae3de20cdc2102fea6e787b.jpg",
  9: "https://static.tcgcollector.com/content/images/d5/4f/9d/d54f9dad068a741a06127562006ce2db4f023b8a5d70e375acb67183f6d25b96.jpg",
  10: "https://static.tcgcollector.com/content/images/d1/f5/8f/d1f58fa6f2fa023cc615a4ddc0379884dd58dc9416bec35a32f8916fdd81800b.jpg",
  16: "https://static.tcgcollector.com/content/images/3b/44/b5/3b44b535c9b4ff181ed4790a2bbd2ab417e0880e1235501986531b32d9d11f94.jpg",
  17: "https://static.tcgcollector.com/content/images/04/7c/91/047c913c2b874072d91647503654e23ac76bdf02b9a9ee27636d4be9db5fe4c5.jpg",
  18: "https://static.tcgcollector.com/content/images/48/5f/8f/485f8fdbfd9799085af9030adbbde09db6393804f3dc33416563486858674376.jpg",
  29: "https://static.tcgcollector.com/content/images/69/55/dc/6955dc7e9e02987dd65e8053314e749ce5b0b1505b463103433dc8fea99783ed.jpg"
}
def fetch(item):
 n,url=item
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read()
 return n,url,raw
with ThreadPoolExecutor(max_workers=5) as pool:scans=list(pool.map(fetch,SOURCES.items()))
report_path=ROOT/'data/tk-xy-latio-image-sources.json';report=json.loads(report_path.read_text());by_number={int(e['number']):e for e in report}
for n,url,raw in scans:
 im=Image.open(io.BytesIO(raw)).convert('RGBA')
 w,h=im.size
 assert w>=250 and h>=350,(n,im.size)
 mask=Image.new('L',(w,h))
 ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=7,fill=255)
 im.putalpha(mask)
 canvas=Image.new('RGBA',(w+36,h+36));canvas.alpha_composite(im,(18,18))
 canvas.save(ROOT/f'assets/sets/tk-xy-latio/{n:03d}.png','PNG',optimize=True)
 by_number[n]['source']=url
 by_number[n]['source_size']=[w,h]
 by_number[n]['name']=by_number[n]['name'].replace('Fightning Energy','Fighting Energy')
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Unique energy scans',len(scans))
