#!/usr/bin/env python3
"""Incrementally archive verified TCGdex images without changing card metadata."""
import json, pathlib, re, urllib.request, urllib.error, os
ROOT=pathlib.Path(__file__).resolve().parents[1]
SETS=ROOT/'data'/'sets'
MANIFEST=ROOT/'data'/'sets.json'
LIMIT=int(os.getenv('IMAGE_REPAIR_LIMIT','16'))
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
# Explicit cross-database IDs only: never infer an image from a card name.
# PokemonTCG.io uses different identifiers from TCGdex for these releases.
FALLBACK_SETS={
    'sv05':'sv5','sv10':'sv10','sma':'sma','svp':'svp',
    'swshp':'swshp','smp':'smp','xyp':'xyp','bwp':'bwp','hgssp':'hsp',
    'cel25':'cel25','cel25cc':'cel25c','swsh9tg':'swsh9tg',
    'swsh10tg':'swsh10tg','swsh11tg':'swsh11tg','swsh12tg':'swsh12tg',
    'pl2':'pl2','xy8':'xy8','sm2':'sm2','sm3':'sm3','sm6':'sm6',
    'ecard2':'ecard2','ecard3':'ecard3',
}
def supplemental(sid,number='',kind='card'):
    other=FALLBACK_SETS.get(sid)
    if not other:return ''
    if kind=='logo':return 'https://images.pokemontcg.io/'+other+'/logo.png'
    # Exact printed local ID, not fuzzy name matching. Do not guess for other sets.
    number=str(number or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',number):return ''
    return 'https://images.pokemontcg.io/'+other+'/'+number+'.png'
def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    attempted=0; saved=0; changed=0
    cursor=ROOT/'data'/'image_repair_cursor.txt'
    # Prioritise logo-only sets and the largest image gaps, rather than cycling blindly.
    audit_path=ROOT/'data'/'image_audit.json'
    priority={}
    if audit_path.exists():
        audit=json.loads(audit_path.read_text(encoding='utf-8'))
        for row in audit.get('sets',[]):
            priority[row['id']]=(row.get('logo_status')!='local',len(row.get('missing_cards',[]))+len(row.get('external_unverified_cards',[])))
    paths=sorted(SETS.glob('*.json'),key=lambda p:(-int(priority.get(p.stem,(False,0))[0] and priority.get(p.stem,(False,0))[1]==0),-priority.get(p.stem,(False,0))[1],p.stem))
    start=0  # Re-evaluate priority after every audit; avoid stale cursor ordering.
    visited=0
    for path in paths[start:]+paths[:start]:
        if attempted>=LIMIT:break
        visited+=1
        sid=path.stem
        if not re.fullmatch(r'[A-Za-z0-9_-]+',sid):continue
        payload=json.loads(path.read_text(encoding='utf-8'))
        info=payload['set']
        logo=info.get('images',{}).get('logo','')
        cards=payload.get('cards',[])
        pending=not logo.startswith('./assets/') or any(not c.get('images',{}).get('small','').startswith('./assets/') for c in cards)
        if not pending:continue
        actionable=(bool(logo) or bool(supplemental(sid,kind='logo'))) and not logo.startswith('./assets/') or any((c.get('images',{}).get('small','') or supplemental(sid,c.get('number'))) and not c.get('images',{}).get('small','').startswith('./assets/') for c in cards)
        if not actionable:continue
        attempted+=1
        original=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        if not logo.startswith('./assets/'):
            new=archive(logo,sid,'logo','logo') or archive(supplemental(sid,kind='logo'),sid,'logo','logo')
            if new:info['images']['logo']=new;saved+=1
        for card in cards:
            current=card.get('images',{}).get('small','')
            if current.startswith('./assets/'):continue
            number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or card['id']))
            new=archive(current,sid,number,'card') or archive(supplemental(sid,card.get('number')),sid,number,'card')
            if new:card['images']['small']=new;saved+=1
        if json.dumps(payload,ensure_ascii=False,sort_keys=True)!=original:
            path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            changed+=1
            if sid in by_id:by_id[sid]['images']=info['images']
        print('Image audit:',sid,'logo:',bool(info['images'].get('logo')),'cards archived:',sum(c.get('images',{}).get('small','').startswith('./assets/') for c in cards),'/',len(cards),flush=True)
    # Keep the previous cursor file for compatibility, but priority is recalculated each run.
    if changed:MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Image archive: attempted sets:',attempted,'saved assets:',saved,'updated sets:',changed,flush=True)
if __name__=='__main__':main()
