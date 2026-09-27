#!/usr/bin/env python3
"""Archive verified user-provided logos locally, then repair missing logos by exact set name.

Runs independently of the card repair and records every unresolved set.
"""
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from archive_images import ROOT, SETS, MANIFEST, archive, supplemental, override, CACHE_PATH, FAILURE_CACHE

REPORT=ROOT/'data'/'targeted_logo_repair.json'
HEADERS={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/json'}
def norm(value):
    return re.sub(r'[^a-z0-9]','',str(value or '').casefold())
def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=15) as response:
            return json.load(response)
    except (urllib.error.URLError,TimeoutError,ValueError,OSError):
        return None
def exact_catalogue_logo(name):
    query='name:"'+str(name).replace('"','')+'"'
    url='https://api.pokemontcg.io/v2/sets?'+urllib.parse.urlencode({'q':query,'pageSize':100})
    payload=fetch(url) or {}
    rows=payload.get('data',[])
    matches=[row for row in rows if norm(row.get('name'))==norm(name)]
    if len(matches)!=1:return '', 'ambiguous' if matches else 'not_found'
    return (matches[0].get('images') or {}).get('logo',''),'exact_set_name'
def tcgdex_set_logo(sid,name):
    """Independent set endpoint; only accept exact ID and name."""
    for lang in ('en','fr'):
        url='https://api.tcgdex.net/v2/'+lang+'/sets/'+urllib.parse.quote(sid,safe='')
        payload=fetch(url) or {}
        if str(payload.get('id','')).lower()!=sid.lower():continue
        if lang=='en' and norm(payload.get('name'))!=norm(name):continue
        logo=payload.get('logo','')
        if logo:return logo,'tcgdex_'+lang
    return '','tcgdex_not_found'
def historical_set_logos():
    """Independently archived catalogue, downloaded once per execution."""
    url='https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/sets/en.json'
    rows=fetch(url)
    return rows if isinstance(rows,list) else []
def historical_logo(sid,name,rows):
    """Require unique exact historical name, or exact ID plus name."""
    matches=[row for row in rows if norm(row.get('name'))==norm(name)]
    exact=[row for row in matches if str(row.get('id','')).lower()==sid.lower()]
    selected=exact if len(exact)==1 else matches if len(matches)==1 else []
    if len(selected)!=1:return '','historical_ambiguous' if matches else 'historical_not_found'
    return (selected[0].get('images') or {}).get('logo',''),'historical_verified'
def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    results={}
    historical=historical_set_logos()
    saved=0
    for path in sorted(SETS.glob('*.json')):
        payload=json.loads(path.read_text(encoding='utf-8'))
        info=payload['set'];sid=path.stem
        # User-uploaded artwork is authoritative when already present locally.
        folder=ROOT/'assets'/'sets'/sid
        uploaded=next((folder/('logo.'+ext) for ext in ('webp','png','jpg')
                       if (folder/('logo.'+ext)).exists()
                       and (folder/('logo.'+ext)).stat().st_size>1000),None)
        if uploaded:
            local='./assets/sets/'+sid+'/'+uploaded.name
            info.setdefault('images',{})['logo']=local
            path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            if sid in by_id:by_id[sid]['images']=info['images']
            saved+=1
            results[sid]={'name':info.get('name',''),'status':'saved_user_uploaded'}
            print('Logo repair:',sid,'saved_user_uploaded',flush=True)
            continue
        if info.get('images',{}).get('logo','').startswith('./assets/'):continue
        name=info.get('name','')
        candidates=[('user_verified',override(sid,kind='logo')),
                    ('existing',info.get('images',{}).get('logo','')),
                    ('mapped',supplemental(sid,kind='logo'))]
        external,reason=exact_catalogue_logo(name)
        if external:candidates.append((reason,external))
        tcglogo,tcgreason=tcgdex_set_logo(sid,name)
        if tcglogo:candidates.append((tcgreason,tcglogo))
        oldlogo,oldreason=historical_logo(sid,name,historical)
        if oldlogo:candidates.append((oldreason,oldlogo))
        outcome='not_found'
        for source,url in candidates:
            if not url:continue
            local=archive(url,sid,'logo','logo')
            if local:
                info.setdefault('images',{})['logo']=local
                path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
                if sid in by_id:by_id[sid]['images']=info['images']
                saved+=1;outcome='saved_'+source
                break
        if outcome=='not_found':outcome=reason+'; '+tcgreason+'; '+oldreason
        results[sid]={'name':name,'status':outcome}
        print('Logo repair:',sid,name,outcome,flush=True)
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    REPORT.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    CACHE_PATH.write_text(json.dumps(FAILURE_CACHE,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Targeted logo repair: checked:',len(results),'saved:',saved,'still missing:',len(results)-saved,flush=True)
if __name__=='__main__':main()
