#!/usr/bin/env python3
"""Archive reviewed English PRE images and import the complete enriched set.

Frozen inputs preserve identities and image checksums. Missing variant images
remain explicit research records; no fabricated pattern images enter the DB.
"""
import concurrent.futures,datetime,gzip,hashlib,io,json,pathlib,re,time,urllib.request
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
SID='sv08.5'
PREFIX='./assets/sets/'+SID+'/'
MAX_BYTES=10_000_000

def read_input(name):
    return json.loads(gzip.decompress((ROOT/'data/imports'/name).read_bytes()))
def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');tmp.replace(path)
def main():
    payload=read_input('prismatic-evolutions.json.gz')
    sources=read_input('prismatic-evolutions-images.json.gz')
    assert payload['set']['id']==SID and payload['set']['name']=='Prismatic Evolutions'
    cards=payload['cards'];assert len(cards)==180
    assert {c['number']for c in cards}=={f'{n:03}'for n in range(1,181)}
    assert len({c['id']for c in cards})==180
    by_number={c['number']:c for c in cards}
    assets=sources['assets'];names=set()
    for a in assets:
        filename=a['filename']
        assert re.fullmatch(r'[A-Za-z0-9_.-]+',filename) and not filename.startswith('.'),filename
        assert filename not in names;names.add(filename)
        if a['kind']!='logo':
            c=by_number[a['number']];assert a['id']==c['id'] and a['name']==c['name']
        assert a['source'].startswith('https://')
        assert re.fullmatch(r'[a-f0-9]{64}',a['sha256'])
    for c in cards:
        assert c['id']=='sv08.5-'+c['number']
        assert c['images']['small']==PREFIX+c['number']+'.webp'
        assert len({p['key']for p in c['printings']})==len(c['printings'])
        for p in c['printings']:
            image=p['images'].get('small','')
            if image:assert image.startswith(PREFIX) and image[len(PREFIX):]in names
            else:assert p['imageStatus']=='needs_additional_sources'
    destination=ROOT/'assets/sets'/SID;destination.mkdir(parents=True,exist_ok=True)
    def download(a):
        path=destination/a['filename'];error=''
        if path.is_file()and hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256']:return a['filename'],'preserved'
        for attempt in range(3):
            try:
                req=urllib.request.Request(a['source'],headers={'User-Agent':'ZamexCardsChecklist/1.0'})
                with urllib.request.urlopen(req,timeout=35)as r:raw=r.read(MAX_BYTES+1)
                assert 1000<len(raw)<=MAX_BYTES,'image size'
                assert hashlib.sha256(raw).hexdigest()==a['sha256'],'source changed since review'
                with Image.open(io.BytesIO(raw))as image:
                    image.load();assert image.size==(a['width'],a['height'])
                tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(path)
                return a['filename'],'saved'
            except Exception as exc:error=str(exc);time.sleep(attempt+1)
        return a['filename'],'FAILED: '+error
    with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:results=list(pool.map(download,assets))
    failures=[r for r in results if r[1].startswith('FAILED')]
    if failures:raise RuntimeError('Incomplete image import; catalogue not changed: '+repr(failures))
    payload['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_json(ROOT/'data/sets'/f'{SID}.json',payload)
    manifest_path=ROOT/'data/sets.json';manifest=json.loads(manifest_path.read_text())
    manifest['sets']=[s for s in manifest['sets']if s['id']!=SID]+[payload['set']]
    manifest['sets'].sort(key=lambda s:(s.get('releaseDate',''),s['name']),reverse=True)
    manifest['updated']=payload['updated'];write_json(manifest_path,manifest)
    write_json(ROOT/'data/prismatic-evolutions-image-sources.json',sources)
    write_json(ROOT/'data/prismatic-evolutions-research.json',{'set':SID,'checked':payload['updated'],'open':payload['research']})
    report={'set':SID,'language':'en',**payload['summary'],'filesArchived':len(assets),'missingDownloads':0,'checked':payload['updated']}
    write_json(ROOT/'data/prismatic-evolutions-import-report.json',report)
    for name,state in results:print(name,state,flush=True)
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
