"""Archive the 28 letter-specific Unseen Forces Unown scans."""
import io,json,urllib.request,hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads(Path('/tmp/unown-entries.json').read_text())
entries=[(n,'https://pokemonplug.com/cdn/shop/products/90187.jpg?v=1660848571' if n=='T' else u) for n,u in entries]
assert {n for n,u in entries}==set('ABCDEFGHIJKLMNOPQRSTUVWXYZ!?')
data=json.loads((ROOT/'data/sets/exu.json').read_text())
target=ROOT/'assets/sets/exu';target.mkdir(parents=True,exist_ok=True)
def fetch(entry):
 n,url=entry
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
 im=Image.open(io.BytesIO(raw));im.load();assert im.width>=250 and im.height>=350
 im=im.convert('RGBA')
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,im.width-1,im.height-1),radius=10,fill=255);im.putalpha(mask)
 filename={'!':'exclamation','?':'question'}.get(n,n)+'.png'
 path=target/filename;tmp=path.with_suffix('.tmp.png');im.save(tmp,'PNG');Image.open(tmp).verify();tmp.replace(path)
 return {'number':n,'source':url,'path':str(path.relative_to(ROOT)),'size':list(im.size)}
with ThreadPoolExecutor(max_workers=6) as pool:report=list(pool.map(fetch,entries))
assert len({hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() for r in report})==28
mapping={r['number']:r for r in report}
for c in data['cards']:c['images']['small']='./'+mapping['?' if c['number']=='%3F' else c['number']]['path']
(ROOT/'data/sets/exu.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(ROOT/'data/exu-image-sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
sheet=Image.new('RGB',(7*180,4*270),'#dce5ee');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(report):
 im=Image.open(ROOT/r['path']);im.thumbnail((170,240));x=(i%7)*180+5;y=(i//7)*270+20;sheet.paste(im,(x,y),im);draw.text((x,y-16),r['number'],fill='black')
sheet.save('/tmp/unown-montage.jpg')
print('Archived 28 unique cards; montage /tmp/unown-montage.jpg')
