"""Archive exact numbered HS Trainer Kit Raichu scans."""
import io, json, re, urllib.request, html
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'data/sets/tk-hs-r.json';data=json.loads(path.read_text())
req=urllib.request.Request('https://www.pokemonkaart.nl/set/hgss-trainer-kit-raichu',headers={'User-Agent':'Mozilla/5.0'})
page=urllib.request.urlopen(req,timeout=40).read().decode()
entries=[]
for part in re.findall(r'<a href="/kaart/[^" ]+" class="card-tile">(.*?)</a>',page,re.S):
 n=re.search(r'<span class="card-number">(\d+)/30</span>',part)
 name=re.search(r'<div class="card-name">([^<]+)</div>',part)
 image=re.search(r'<img src="([^"]+)',part)
 if n and name and image:entries.append((int(n[1]),name[1],'https://www.pokemonkaart.nl'+image[1]))
entries.sort()
assert [n for n,_,_ in entries]==list(range(1,31))
cards={int(c['number']):c for c in data['cards']}
assert all(cards[n]['name'].replace('’', "'")==html.unescape(name).replace('’', "'") for n,name,_ in entries)
entries=[(n,cards[n]['name'],url) for n,name,url in entries]
def fetch(item):
 n,name,url=item
 raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
 return n,name,url,raw
with ThreadPoolExecutor(max_workers=6) as pool:scans=list(pool.map(fetch,entries))
target=ROOT/'assets/sets/tk-hs-r';target.mkdir(parents=True,exist_ok=True)
report=[]
for n,name,url,raw in scans:
 im=Image.open(io.BytesIO(raw));im.load()
 assert im.width>=250 and im.height>=350,(n,im.size)
 if im.mode!='RGBA' or im.getpixel((0,0))[3]!=0:
  im=im.convert('RGBA')
  mask=Image.new('L',im.size)
  ImageDraw.Draw(mask).rounded_rectangle((0,0,im.width-1,im.height-1),radius=12,fill=255)
  im.putalpha(mask)
 output=target/f'{n:03d}.png';temporary=output.with_suffix('.tmp.png');im.save(temporary,'PNG');Image.open(temporary).verify();temporary.replace(output)
 cards[n]['images']['small']=f'./assets/sets/tk-hs-r/{n:03d}.png'
 report.append({'number':str(n),'name':name,'source':url,'source_size':list(im.size),'path':str(output.relative_to(ROOT))})
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(ROOT/'data/tk-hs-r-image-sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Archived',len(report),'cards')
