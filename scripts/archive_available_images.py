#!/usr/bin/env python3
"""Archive upstream artwork by exact card identity, preserving reviewed local images."""
import concurrent.futures,io,json,pathlib,re,urllib.request
from PIL import Image

ROOT=pathlib.Path(__file__).resolve().parents[1]
MAX_BYTES=8_000_000
HEADERS={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'image/*'}

def save_json(path,value):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    tmp.replace(path)

def fetch_image(url,sid,name):
    if not url or url.startswith('./') or not re.fullmatch(r'[A-Za-z0-9_-]+',sid):return ''
    if not url.startswith('https://'):return ''
    name=re.sub(r'[^A-Za-z0-9_-]','_',str(name))
    destination=ROOT/'assets'/'sets'/sid/(name+'.png')
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=25) as response:
            raw=response.read(MAX_BYTES+1)
        if not 1000<=len(raw)<=MAX_BYTES:return ''
        image=Image.open(io.BytesIO(raw));image.load()
        if name!='logo' and (image.width<200 or image.height<280):return ''
        if image.width<20 or image.height<20:return ''
        destination.parent.mkdir(parents=True,exist_ok=True)
        tmp=destination.with_suffix('.tmp.png')
        image.save(tmp,'PNG')
        with Image.open(tmp) as check:check.load()
        tmp.replace(destination)
        return './'+str(destination.relative_to(ROOT))
    except Exception as error:
        print('Image unavailable:',sid,name,type(error).__name__,flush=True)
        return ''

def main():
    manifest_path=ROOT/'data/sets.json'
    manifest=json.loads(manifest_path.read_text())
    by_id={s['id']:s for s in manifest['sets']}
    saved=0
    for path in sorted((ROOT/'data/sets').glob('*.json')):
        data=json.loads(path.read_text());sid=data['set']['id'];jobs=[]
        logo=data['set'].setdefault('images',{})
        if not logo.get('logo','').startswith('./assets/') and logo.get('logo'):
            jobs.append((logo,'logo','logo',logo['logo']))
        for card in data['cards']:
            images=card.setdefault('images',{});url=images.get('small','')
            if url and not url.startswith('./assets/'):
                jobs.append((images,'small',card['number'],url))
        if not jobs:continue
        def one(job):
            obj,key,name,url=job
            return obj,key,fetch_image(url,sid,name)
        changed=False
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for obj,key,new in pool.map(one,jobs):
                if new:obj[key]=new;saved+=1;changed=True
        if changed:
            save_json(path,data)
            if sid in by_id:by_id[sid]['images']=data['set']['images']
    save_json(manifest_path,manifest)
    print('New verified image files:',saved,flush=True)

if __name__=='__main__':main()
