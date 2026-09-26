#!/usr/bin/env python3
"""Incrementally archive verified TCGdex images without changing card metadata."""
import json, pathlib, re, urllib.request, urllib.error, os
ROOT=pathlib.Path(__file__).resolve().parents[1]
SETS=ROOT/'data'/'sets'
MANIFEST=ROOT/'data'/'sets.json'
LIMIT=int(os.getenv('IMAGE_REPAIR_LIMIT','8'))
HEADERS={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'image/webp,image/png,image/*'}
def candidates(url,kind):
    if not url or url.startswith('./'):return []
    url=url.rstrip('/')
    if re.search(r'\.(webp|png|jpe?g)$',url,re.I):return [url]
    return [url+'.webp',url+'.png'] if kind=='logo' else [url+'/low.webp',url+'/low.png']
def archive(url,sid,name,kind):
    folder=ROOT/'assets'/'sets'/sid
    for ext in ('webp','png','jpg'):
        existing=folder/(name+'.'+ext)
        if existing.exists() and existing.stat().st_size>1000:
            return './assets/sets/'+sid+'/'+existing.name
    for source in candidates(url,kind):
        try:
            with urllib.request.urlopen(urllib.request.Request(source,headers=HEADERS),timeout=12) as response:
                mime=response.headers.get('Content-Type','').split(';')[0].lower()
                if mime not in ('image/webp','image/png','image/jpeg'):continue
                data=response.read(1000001)
            if len(data)<1000 or len(data)>1000000:continue
            ext={'image/webp':'webp','image/png':'png','image/jpeg':'jpg'}[mime]
            folder.mkdir(parents=True,exist_ok=True)
            (folder/(name+'.'+ext)).write_bytes(data)
            return './assets/sets/'+sid+'/'+name+'.'+ext
        except (urllib.error.URLError,OSError,TimeoutError):
            continue
    return ''
def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    attempted=0; saved=0; changed=0
    for path in sorted(SETS.glob('*.json')):
        sid=path.stem
        if not re.fullmatch(r'[A-Za-z0-9_-]+',sid):continue
        payload=json.loads(path.read_text(encoding='utf-8'))
        info=payload['set']
        logo=info.get('images',{}).get('logo','')
        cards=payload.get('cards',[])
        pending=not logo.startswith('./assets/') or any(not c.get('images',{}).get('small','').startswith('./assets/') for c in cards)
        if not pending:continue
        if attempted>=LIMIT:break
        attempted+=1
        original=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        if not logo.startswith('./assets/'):
            new=archive(logo,sid,'logo','logo')
            if new:info['images']['logo']=new;saved+=1
        for card in cards:
            current=card.get('images',{}).get('small','')
            if current.startswith('./assets/'):continue
            number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or card['id']))
            new=archive(current,sid,number,'card')
            if new:card['images']['small']=new;saved+=1
        if json.dumps(payload,ensure_ascii=False,sort_keys=True)!=original:
            path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            changed+=1
            if sid in by_id:by_id[sid]['images']=info['images']
        print('Image audit:',sid,'logo:',bool(info['images'].get('logo')),'cards archived:',sum(c.get('images',{}).get('small','').startswith('./assets/') for c in cards),'/',len(cards),flush=True)
    if changed:MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Image archive: attempted sets:',attempted,'saved assets:',saved,'updated sets:',changed,flush=True)
if __name__=='__main__':main()
