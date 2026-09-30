"""Archive the 34 checklist entries using the My First Battle source gallery."""
import hashlib,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'data/sets/mfb.json';data=json.loads(path.read_text())
special={'8':'BasicGrassEnergySVEEnergy1.jpg','16':'BasicFireEnergySVEEnergy2.jpg','24':'BasicLightningEnergySVEEnergy4.jpg','32':'BasicWaterEnergySVEEnergy3.jpg','33':'PotionScarletViolet188.jpg','34':'SwitchScarletViolet194.jpg'}
target=ROOT/'assets/sets/mfb';target.mkdir(parents=True,exist_ok=True)
def fetch(c):
 n=c['number'];filename=special.get(n,c['name'].replace(' ','')+'MyFirstBattle.jpg');h=hashlib.md5(filename.encode()).hexdigest()
 url=f'https://archives.bulbagarden.net/media/upload/{h[0]}/{h[:2]}/{filename}'
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
 im=Image.open(io.BytesIO(raw));im.load();assert im.width>=250 and im.height>=350
 im.thumbnail((734,1024),Image.Resampling.LANCZOS)
 im=im.convert('RGBA');mask=Image.new('L',im.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,im.width-1,im.height-1),radius=round(im.width*.015),fill=255);im.putalpha(mask)
 output=target/f'{int(n):03d}.png';tmp=output.with_suffix('.tmp.png');im.save(tmp,'PNG');Image.open(tmp).verify();tmp.replace(output)
 return {'number':n,'name':c['name'],'source':url,'path':str(output.relative_to(ROOT)),'size':list(im.size)}
with ThreadPoolExecutor(max_workers=6) as pool:report=list(pool.map(fetch,data['cards']))
assert len(report)==34
assert len({hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() for r in report})==34
for c,r in zip(data['cards'],report):c['images']['small']='./'+r['path']
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(ROOT/'data/mfb-image-sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
sheet=Image.new('RGB',(7*180,5*270),'#dce5ee');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(report):
 im=Image.open(ROOT/r['path']);im.load();im.thumbnail((170,240));x=(i%7)*180+5;y=(i//7)*270+20;sheet.paste(im,(x,y),im);draw.text((x,y-16),r['number']+' '+r['name'],fill='black')
sheet.save('/tmp/mfb-montage.jpg');print('Archived 34 distinct images')
