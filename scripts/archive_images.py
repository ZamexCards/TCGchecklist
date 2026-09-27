#!/usr/bin/env python3
"""Incrementally archive verified TCGdex images without changing card metadata."""
import json, pathlib, re, urllib.request, urllib.error, os, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
SETS=ROOT/'data'/'sets'
MANIFEST=ROOT/'data'/'sets.json'
LIMIT=int(os.getenv('IMAGE_REPAIR_LIMIT','200'))
OVERRIDES=ROOT/'data'/'image_sources.json'
def overrides():
    if not OVERRIDES.exists():return {}
    return json.loads(OVERRIDES.read_text(encoding='utf-8'))
SOURCE_OVERRIDES=overrides()
CACHE_PATH=ROOT/'data'/'image_failed_sources.json'
try:
    FAILURE_CACHE=json.loads(CACHE_PATH.read_text(encoding='utf-8'))
except (OSError,ValueError):
    FAILURE_CACHE={}
TODAY=datetime.date.today()
SKIPPED=0
def eligible(url):
    global SKIPPED
    previous=FAILURE_CACHE.get(url,'')
    try:
        if previous and (TODAY-datetime.date.fromisoformat(previous)).days<30:
            SKIPPED+=1
            return False
    except ValueError:
        pass
    return True

def override(sid,number='',kind='card'):
    entry=SOURCE_OVERRIDES.get(sid,{})
    return entry.get('logo','') if kind=='logo' else entry.get('cards',{}).get(str(number),'')
HEADERS={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'image/webp,image/png,image/*'}
def candidates(url,kind):
    if not url or url.startswith('./'):return []
    url=url.rstrip('/')
    if re.search(r'\.(webp|png|jpe?g)(?:\?.*)?$',url,re.I):return [url]
    return [url+'.webp',url+'.png'] if kind=='logo' else [url+'/low.webp',url+'/low.png',url+'/high.webp',url+'/high.png']
MAX_IMAGE_BYTES=8_000_000

def valid_image(data,mime):
    if mime=='image/png':return data.startswith(b'\x89PNG\r\n\x1a\n')
    if mime=='image/jpeg':return data.startswith(b'\xff\xd8\xff')
    if mime=='image/webp':return data[:4]==b'RIFF' and data[8:12]==b'WEBP'
    return False

def archive(url,sid,name,kind):
    folder=ROOT/'assets'/'sets'/sid
    for ext in ('webp','png','jpg'):
        existing=folder/(name+'.'+ext)
        if existing.exists() and existing.stat().st_size>1000:
            return './assets/sets/'+sid+'/'+existing.name
    for source in candidates(url,kind):
        if not eligible(source):continue
        try:
            with urllib.request.urlopen(urllib.request.Request(source,headers=HEADERS),timeout=12) as response:
                mime=response.headers.get('Content-Type','').split(';')[0].lower()
                if mime not in ('image/webp','image/png','image/jpeg'):continue
                data=response.read(MAX_IMAGE_BYTES+1)
            if len(data)<1000 or len(data)>MAX_IMAGE_BYTES or not valid_image(data,mime):
                FAILURE_CACHE[source]=TODAY.isoformat()
                continue
            ext={'image/webp':'webp','image/png':'png','image/jpeg':'jpg'}[mime]
            folder.mkdir(parents=True,exist_ok=True)
            (folder/(name+'.'+ext)).write_bytes(data)
            FAILURE_CACHE.pop(source,None)
            return './assets/sets/'+sid+'/'+name+'.'+ext
        except urllib.error.HTTPError as error:
            # Cache only permanent missing assets, not outages or throttling.
            if error.code in (404,410):
                FAILURE_CACHE[source]=TODAY.isoformat()
            continue
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
    '2014xy':'mcd14',
}
def supplemental(sid,number='',kind='card'):
    explicit=override(sid,number,kind)
    if explicit:return explicit
    other=FALLBACK_SETS.get(sid)
    if not other:return ''
    if kind=='logo':return 'https://images.pokemontcg.io/'+other+'/logo.png'
    # Exact printed local ID, not fuzzy name matching. Do not guess for other sets.
    number=str(number or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',number):return ''
    return 'https://images.pokemontcg.io/'+other+'/'+number+'.png'

# Pocket B2a is a separate game: require matching set, printed number AND name.
# The public dataset documents cards-by-set/B2a/<number>.webp.
POCKET_META='https://raw.githubusercontent.com/flibustier/pokemon-tcg-pocket-database/main/dist/cards/B2a.json'
POCKET_IMAGE='https://raw.githubusercontent.com/flibustier/pokemon-tcg-exchange/main/public/images/cards-by-set/B2a/{}.webp'
def pocket_cards():
    try:
        with urllib.request.urlopen(urllib.request.Request(POCKET_META,headers={'User-Agent':'ZamexCardsChecklist/1.0'}),timeout=15) as response:
            rows=json.load(response)
        if isinstance(rows,dict):rows=rows.get('cards',[])
        return {str(row['number']):row for row in rows if isinstance(row,dict) and row.get('set','B2a').lower()=='b2a'}
    except (ValueError,KeyError,TypeError,urllib.error.URLError,OSError,TimeoutError) as error:
        print('Pocket source unavailable:',error,flush=True)
        return {}
def pocket_source(sid,card,known):
    if sid.lower()!='b2a':return ''
    number=str(card.get('number','')).strip()
    if not number.isdigit():return ''
    row=known.get(str(int(number)))
    if not row:return ''
    normal=lambda name:re.sub(r'[^a-z0-9]','',str(name).lower())
    if normal(row.get('name'))!=normal(card.get('name')):return ''
    return POCKET_IMAGE.format(int(number))

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    attempted=0; saved=0; changed=0
    pocket=pocket_cards()
    cursor=ROOT/'data'/'image_repair_cursor.txt'
    # Rank only repairable source links; unresolvable sets remain in the diagnosis report.
    audit_path=ROOT/'data'/'image_audit.json'
    priority={}
    if audit_path.exists():
        audit=json.loads(audit_path.read_text(encoding='utf-8'))
        for row in audit.get('sets',[]):
            priority[row['id']]=(row.get('logo_status')!='local',len(row.get('missing_cards',[]))+len(row.get('external_unverified_cards',[])))
    # Only rank sets with a source URL or an explicitly mapped secondary source.
    # Previously, missing-logo-only sets without any source consumed the repair budget.
    paths=[]
    for p in SETS.glob('*.json'):
        payload=json.loads(p.read_text(encoding='utf-8'))
        sid=p.stem
        logo=payload['set'].get('images',{}).get('logo','')
        cards=payload.get('cards',[])
        logo_action=not logo.startswith('./assets/') and bool(logo or supplemental(sid,kind='logo'))
        card_actions=sum(bool((c.get('images',{}).get('small','') or supplemental(sid,c.get('number')) or pocket_source(sid,c,pocket)) and not c.get('images',{}).get('small','').startswith('./assets/')) for c in cards)
        if logo_action or card_actions:
            paths.append((p,logo_action,card_actions))
    paths=[p for p,_,_ in sorted(paths,key=lambda row:(-row[2],-int(row[1]),row[0].stem))]
    start=0
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
        actionable=(bool(logo) or bool(supplemental(sid,kind='logo'))) and not logo.startswith('./assets/') or any((c.get('images',{}).get('small','') or supplemental(sid,c.get('number')) or pocket_source(sid,c,pocket)) and not c.get('images',{}).get('small','').startswith('./assets/') for c in cards)
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
            pocket_url=pocket_source(sid,card,pocket)
            # The same verified Pocket card number may be stored zero-padded in image repositories.
            pocket_padded=(POCKET_IMAGE.format(str(int(card['number'])).zfill(3)) if pocket_url and str(card.get('number','')).isdigit() else '')
            new=archive(current,sid,number,'card') or archive(supplemental(sid,card.get('number')),sid,number,'card') or archive(pocket_url,sid,number,'card') or archive(pocket_padded,sid,number,'card')
            if new:card['images']['small']=new;saved+=1
        if json.dumps(payload,ensure_ascii=False,sort_keys=True)!=original:
            path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            changed+=1
            if sid in by_id:by_id[sid]['images']=info['images']
        print('Image audit:',sid,'logo:',bool(info['images'].get('logo')),'cards archived:',sum(c.get('images',{}).get('small','').startswith('./assets/') for c in cards),'/',len(cards),flush=True)
    # Keep the previous cursor file for compatibility, but priority is recalculated each run.
    CACHE_PATH.write_text(json.dumps(FAILURE_CACHE,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if changed:MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Image archive: attempted sets:',attempted,'saved assets:',saved,'updated sets:',changed,'cached source skips:',SKIPPED,flush=True)
if __name__=='__main__':main()
