#!/usr/bin/env python3
"""Incremental TCGdex -> GitHub Pages JSON snapshot. No paid API or credentials."""
import concurrent.futures, datetime, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
SETS=DATA/'sets'
BASE='https://api.tcgdex.net/v2/en'
HEADERS={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/json'}
WORKERS=10
REPAIR_LIMIT=int(os.environ.get('REPAIR_LIMIT','8'))
ASSETS=ROOT/'assets'/'sets'
def fetch(url, attempts=4):
    for attempt in range(attempts):
        try:
            request=urllib.request.Request(url,headers=HEADERS)
            with urllib.request.urlopen(request,timeout=35) as response:
                return json.load(response)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError) as error:
            if attempt==attempts-1: raise
            time.sleep(min(20,2**attempt))
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    temp.replace(path)
def image_url(value):
    if not value:return ''
    value=str(value).rstrip('/')
    return value if re.search(r'\.(webp|png|jpe?g)$',value,re.I) else value+'/low.webp'
def logo_url(value):
    if not value:return ''
    value=str(value).rstrip('/')
    return value if re.search(r'\.(webp|png|jpe?g)$',value,re.I) else value+'.webp'
def download_asset(url, destination):
    if not url:return False
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists() and destination.stat().st_size>1000:return True
    try:
        req=urllib.request.Request(url,headers=HEADERS)
        with urllib.request.urlopen(req,timeout=18) as response:
            body=response.read(900000)
            content_type=response.headers.get('Content-Type','')
        if not content_type.startswith('image/') or len(body)<1000:return False
        temp=destination.with_suffix('.tmp')
        temp.write_bytes(body)
        temp.replace(destination)
        return True
    except (OSError,urllib.error.URLError,TimeoutError):
        return False
def asset_candidates(base, kind):
    if not base:return []
    base=str(base).rstrip('/')
    if re.search(r'\\.(webp|png|jpe?g)
    source=card.get('variants') or {}
    values=['Base']
    if source.get('reverse') is True:values.append('Reverse holo')
    # Do not invent ball variants: only explicitly supplied API variant data.
    serialized=json.dumps(source,ensure_ascii=False).lower()
    if 'pokeball' in serialized or 'poké ball' in serialized or 'poke ball' in serialized:values.append('Poké Ball')
    if 'masterball' in serialized or 'master ball' in serialized:values.append('Master Ball')
    return values
def card_summary(c):
    return {'id':c.get('id',''),'name':c.get('name',''),'number':c.get('localId',''),
        'supertype':c.get('category',''),'subtypes':[c['stage']] if c.get('stage') else [],
        'types':c.get('types') or [],'rarity':c.get('rarity',''),
        'images':{'small':image_url(c.get('image'))},'availableVariants':variants(c)}
def set_info(item,detail):
    count=detail.get('cardCount') or {}
    return {'id':item['id'],'name':detail.get('name') or item.get('name',''),
        'series':(detail.get('serie') or {}).get('name',''),
        'releaseDate':detail.get('releaseDate') or '',
        'printedTotal':count.get('official') or count.get('total') or 0,
        'total':count.get('total') or 0,
        'images':{'logo':logo_url(detail.get('logo') or '')},'_source':'central'}
def build_set(item, archive=True):
    sid=item['id']
    detail=fetch(BASE+'/sets/'+urllib.parse.quote(sid,safe=''))
    summaries=detail.get('cards') or []
    if not summaries:raise ValueError('Empty card list for '+sid)
    def one(x):
        try:
            c=fetch(BASE+'/cards/'+urllib.parse.quote(x['id'],safe=''))
            result=card_summary(c)
            if not result['images']['small']:
                result['images']['small']=image_url(x.get('image'))
            return result
        except Exception as error:
            # Do not invent image URLs or variants when detail is unavailable.
            print('Card detail unavailable:',x['id'],error,flush=True)
            return card_summary(x)
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        cards=list(pool.map(one,summaries))
    info=set_info(item,detail)
    serie_id=(detail.get('serie') or {}).get('id','')
    if re.fullmatch(r'[A-Za-z0-9_.-]+',serie_id):
        base='https://assets.tcgdex.net/en/'+serie_id+'/'+sid
        if not info['images']['logo']:info['images']['logo']=base+'/logo.webp'
        for c in cards:
            if not c['images']['small'] and re.fullmatch(r'[A-Za-z0-9_.-]+',str(c['number'])):
                c['images']['small']=base+'/'+str(c['number'])+'/low.webp'
    payload={'set':info,'cards':cards,'updated':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    path=SETS/(sid+'.json')
    if path.exists():
        try:
            old=json.loads(path.read_text())
            if not payload['set']['images']['logo']:
                payload['set']['images']['logo']=old.get('set',{}).get('images',{}).get('logo','')
            old_cards={c['id']:c for c in old.get('cards',[])}
            for c in payload['cards']:
                if not c['images']['small']:
                    c['images']['small']=old_cards.get(c['id'],{}).get('images',{}).get('small','')
        except (OSError,ValueError,KeyError):pass
    if archive:
        payload['set']['images']['logo']=store_asset(info['images']['logo'],sid,'logo','logo') or payload['set']['images']['logo']
        for c in payload['cards']:
            base=(c.get('images') or {}).get('small','')
            if base.startswith('./assets/'):continue
            name=re.sub(r'[^A-Za-z0-9_.-]','_',c.get('number') or c['id'])
            local=store_asset(base,sid,name,'card')
            if local:c['images']['small']=local
    write(path,payload)
    print('Updated:',sid,len(cards),flush=True)
    return info
def main():
    DATA.mkdir(exist_ok=True)
    old_path=DATA/'sets.json'
    old=json.loads(old_path.read_text()) if old_path.exists() else {'sets':[]}
    previous={s['id']:s for s in old.get('sets',[])}
    listing=fetch(BASE+'/sets')
    if not isinstance(listing,list) or len(listing)<10:raise RuntimeError('Source returned incomplete set list')
    today=datetime.date.today()
    results={}
    errors=[]
    repairs=0
    # Existing snapshot remains available if a remote request fails.
    for item in listing:
        sid=item.get('id','')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',sid):continue
        path=SETS/(sid+'.json')
        existing=previous.get(sid)
        recent=bool(existing and existing.get('releaseDate') and
                    (today-datetime.date.fromisoformat(existing['releaseDate'])).days<45)
        missing=False
        if path.exists():
            try:
                snapshot=json.loads(path.read_text())
                missing=not str(snapshot.get('set',{}).get('images',{}).get('logo','')).startswith('./assets/') or any(
                    not str(c.get('images',{}).get('small','')).startswith('./assets/') for c in snapshot.get('cards',[]))
            except (OSError,ValueError):pass
        needs_repair=missing and repairs<REPAIR_LIMIT
        if needs_repair:repairs+=1
        if path.exists() and not recent and not needs_repair and os.environ.get('FORCE_REFRESH')!='1':
            try:
                results[sid]=json.loads(path.read_text())['set']
                continue
            except (OSError,ValueError,KeyError):pass
        try:results[sid]=build_set(item,archive=needs_repair or not path.exists())
        except Exception as error:
            errors.append((sid,str(error)))
            if existing and path.exists():results[sid]=existing
            print('Failed:',sid,error,flush=True)
    # Preserve old sets during transient upstream listing omissions.
    for sid,info in previous.items():
        if sid not in results and (SETS/(sid+'.json')).exists():results[sid]=info
    if not results:raise RuntimeError('No usable sets; old manifest retained')
    ordered=sorted(results.values(),key=lambda s:(s.get('releaseDate') or '',s['name']),reverse=True)
    write(old_path,{'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sets':ordered})
    print('Total:',len(ordered),'Repaired:',repairs,'Failures:',len(errors),flush=True)
    if errors:print('Failures:',errors,flush=True)
if __name__=='__main__':main()
,base,re.I):return [base]
    if kind=='logo':return [base+'.webp',base+'.png']
    return [base+'/low.webp',base+'/low.png']
def store_asset(base, set_id, name, kind):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',set_id):return ''
    target=ASSETS/set_id/(name+'.webp')
    if target.exists() and target.stat().st_size>1000:return './assets/sets/'+set_id+'/'+name+'.webp'
    for candidate in asset_candidates(base,kind):
        if download_asset(candidate,target):
            return './assets/sets/'+set_id+'/'+name+'.webp'
    return ''
def variants(card):
    source=card.get('variants') or {}
    values=['Base']
    if source.get('reverse') is True:values.append('Reverse holo')
    # Do not invent ball variants: only explicitly supplied API variant data.
    serialized=json.dumps(source,ensure_ascii=False).lower()
    if 'pokeball' in serialized or 'poké ball' in serialized or 'poke ball' in serialized:values.append('Poké Ball')
    if 'masterball' in serialized or 'master ball' in serialized:values.append('Master Ball')
    return values
def card_summary(c):
    return {'id':c.get('id',''),'name':c.get('name',''),'number':c.get('localId',''),
        'supertype':c.get('category',''),'subtypes':[c['stage']] if c.get('stage') else [],
        'types':c.get('types') or [],'rarity':c.get('rarity',''),
        'images':{'small':image_url(c.get('image'))},'availableVariants':variants(c)}
def set_info(item,detail):
    count=detail.get('cardCount') or {}
    return {'id':item['id'],'name':detail.get('name') or item.get('name',''),
        'series':(detail.get('serie') or {}).get('name',''),
        'releaseDate':detail.get('releaseDate') or '',
        'printedTotal':count.get('official') or count.get('total') or 0,
        'total':count.get('total') or 0,
        'images':{'logo':logo_url(detail.get('logo') or '')},'_source':'central'}
def build_set(item):
    sid=item['id']
    detail=fetch(BASE+'/sets/'+urllib.parse.quote(sid,safe=''))
    summaries=detail.get('cards') or []
    if not summaries:raise ValueError('Empty card list for '+sid)
    def one(x):
        try:
            c=fetch(BASE+'/cards/'+urllib.parse.quote(x['id'],safe=''))
            result=card_summary(c)
            if not result['images']['small']:
                result['images']['small']=image_url(x.get('image'))
            return result
        except Exception as error:
            # Do not invent image URLs or variants when detail is unavailable.
            print('Card detail unavailable:',x['id'],error,flush=True)
            return card_summary(x)
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        cards=list(pool.map(one,summaries))
    info=set_info(item,detail)
    payload={'set':info,'cards':cards,'updated':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    path=SETS/(sid+'.json')
    if path.exists():
        try:
            old=json.loads(path.read_text())
            if not payload['set']['images']['logo']:
                payload['set']['images']['logo']=old.get('set',{}).get('images',{}).get('logo','')
            old_cards={c['id']:c for c in old.get('cards',[])}
            for c in payload['cards']:
                if not c['images']['small']:
                    c['images']['small']=old_cards.get(c['id'],{}).get('images',{}).get('small','')
        except (OSError,ValueError,KeyError):pass
    write(path,payload)
    print('Updated:',sid,len(cards),flush=True)
    return info
def main():
    DATA.mkdir(exist_ok=True)
    old_path=DATA/'sets.json'
    old=json.loads(old_path.read_text()) if old_path.exists() else {'sets':[]}
    previous={s['id']:s for s in old.get('sets',[])}
    listing=fetch(BASE+'/sets')
    if not isinstance(listing,list) or len(listing)<10:raise RuntimeError('Source returned incomplete set list')
    today=datetime.date.today()
    results={}
    errors=[]
    # Existing snapshot remains available if a remote request fails.
    for item in listing:
        sid=item.get('id','')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',sid):continue
        path=SETS/(sid+'.json')
        existing=previous.get(sid)
        recent=bool(existing and existing.get('releaseDate') and
                    (today-datetime.date.fromisoformat(existing['releaseDate'])).days<45)
        missing=False
        if path.exists():
            try:
                snapshot=json.loads(path.read_text())
                missing=not snapshot.get('set',{}).get('images',{}).get('logo') or any(
                    not c.get('images',{}).get('small') for c in snapshot.get('cards',[]))
            except (OSError,ValueError):pass
        if path.exists() and not recent and not missing and os.environ.get('FORCE_REFRESH')!='1':
            try:
                results[sid]=json.loads(path.read_text())['set']
                continue
            except (OSError,ValueError,KeyError):pass
        try:results[sid]=build_set(item)
        except Exception as error:
            errors.append((sid,str(error)))
            if existing and path.exists():results[sid]=existing
            print('Failed:',sid,error,flush=True)
    # Preserve old sets during transient upstream listing omissions.
    for sid,info in previous.items():
        if sid not in results and (SETS/(sid+'.json')).exists():results[sid]=info
    if not results:raise RuntimeError('No usable sets; old manifest retained')
    ordered=sorted(results.values(),key=lambda s:(s.get('releaseDate') or '',s['name']),reverse=True)
    write(old_path,{'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sets':ordered})
    print('Total:',len(ordered),'Failures:',len(errors),flush=True)
    if errors:print('Failures:',errors,flush=True)
if __name__=='__main__':main()
