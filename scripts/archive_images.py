#!/usr/bin/env python3
"""Incrementally archive verified card images without changing card metadata."""
import json, pathlib, re, urllib.request, urllib.error, urllib.parse, os, datetime
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
        if previous and (TODAY-datetime.date.fromisoformat(previous)).days<7:
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
    if '/wiki/Special:FilePath/' in url or '/wiki/Special:Redirect/file/' in url:return [url]
    if re.search(r'\.(webp|png|jpe?g)(?:\?.*)?$',url,re.I):return [url]
    return [url+'.webp',url+'.png'] if kind=='logo' else [url+'/low.webp',url+'/low.png',url+'/low.jpg',url+'/high.webp',url+'/high.png',url+'/high.jpg']
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
    sources=candidates(url,kind)
    # PokemonTCG's high-resolution image can exist when the small CDN file is absent.
    if kind=='card' and url and url.startswith('https://images.pokemontcg.io/') and re.fullmatch('[A-Za-z0-9_-]+/[A-Za-z0-9_-]+[.]png',url.split('images.pokemontcg.io/',1)[1]):
        sources.append(url[:-4]+'_hires.png')
    for source in sources:
        if not eligible(source):
            if sid=='mep':print('MEP source cached:',name,source,flush=True)
            continue
        try:
            with urllib.request.urlopen(urllib.request.Request(source,headers=HEADERS),timeout=12) as response:
                mime=response.headers.get('Content-Type','').split(';')[0].lower()
                if mime not in ('image/webp','image/png','image/jpeg'):
                    if sid=='mep':print('MEP wrong MIME:',name,mime,source,flush=True)
                    continue
                data=response.read(MAX_IMAGE_BYTES+1)
            if len(data)<1000 or len(data)>MAX_IMAGE_BYTES or not valid_image(data,mime):
                FAILURE_CACHE[source]=TODAY.isoformat()
                if sid=='mep':print('MEP invalid image:',name,mime,len(data),source,flush=True)
                continue
            ext={'image/webp':'webp','image/png':'png','image/jpeg':'jpg'}[mime]
            folder.mkdir(parents=True,exist_ok=True)
            (folder/(name+'.'+ext)).write_bytes(data)
            FAILURE_CACHE.pop(source,None)
            if sid=='mep':print('MEP saved:',name,source,flush=True)
            return './assets/sets/'+sid+'/'+name+'.'+ext
        except urllib.error.HTTPError as error:
            if sid=='mep':print('MEP HTTP:',name,error.code,source,flush=True)
            # Cache only permanent missing assets, not outages or throttling.
            if error.code in (404,410):
                FAILURE_CACHE[source]=TODAY.isoformat()
            continue
        except (urllib.error.URLError,OSError,TimeoutError) as error:
            if sid=='mep':print('MEP network:',name,type(error).__name__,source,flush=True)
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
    'ecard2':'ecard2','ecard3':'ecard3','pop6':'pop6',
    '2011bw':'mcd11','2012bw':'mcd12','2014xy':'mcd14',
    '2015xy':'mcd15','2016xy':'mcd16','2017sm':'mcd17',
    '2018sm':'mcd18','2019sm':'mcd19','2021swsh':'mcd21',
    'tk-bw-e':'tk5e','tk-bw-z':'tk5z',
    'tk-ex-latia':'tk1a','tk-ex-latio':'tk1b',
    'tk-ex-p':'tk2a','tk-ex-m':'tk2b',
    '2022swsh':'mcd22','2023sv':'mcd23','2024sv':'mcd24',
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
    # Preserve printed suffixes and holographic H-numbers in the source identity.
    return 'https://images.pokemontcg.io/'+other+'/'+number+'.png'

# Pocket B2a is a separate game: require matching set, printed number AND name.
# The public dataset documents cards-by-set/B2a/<number>.webp.
POCKET_META='https://raw.githubusercontent.com/flibustier/pokemon-tcg-pocket-database/main/dist/cards/{}.json'
POCKET_IMAGE='https://raw.githubusercontent.com/flibustier/pokemon-tcg-exchange/main/public/images/cards-by-set/{}/{}.webp'
POCKET_SETS=('B1a','B2a','PROMO-A','PROMO-B')
POCKET_ALTERNATE='https://raw.githubusercontent.com/Vociferix/ptcgp-images/master/cards/{}/{}.png'
def pocket_cards():
    known={}
    for sid in POCKET_SETS:
        try:
            with urllib.request.urlopen(urllib.request.Request(POCKET_META.format(sid),headers={'User-Agent':'ZamexCardsChecklist/1.0'}),timeout=15) as response:
                rows=json.load(response)
            if isinstance(rows,dict):rows=rows.get('cards',[])
            known[sid.lower()]={str(int(row['number'])):row for row in rows if isinstance(row,dict) and str(row.get('set',sid)).lower()==sid.lower() and str(row.get('number','')).isdigit()}
        except (ValueError,KeyError,TypeError,urllib.error.URLError,OSError,TimeoutError) as error:
            print('Pocket source unavailable:',sid,error,flush=True)
    return known
def pocket_source(sid,card,known):
    source_sid={'p-a':'promo-a','p-b':'promo-b'}.get(sid.lower(),sid.lower())
    if source_sid not in known:return ''
    number=str(card.get('number','')).strip()
    if not number.isdigit():return ''
    row=known[source_sid].get(str(int(number)))
    if not row:return ''
    normal=lambda name:re.sub(r'[^a-z0-9]','',str(name).lower())
    source_name=normal(row.get('name'))
    checklist_name=normal(card.get('name'))
    if source_name!=checklist_name and source_name!=checklist_name+'ex':return ''
    return POCKET_IMAGE.format({'p-a':'PROMO-A','p-b':'PROMO-B'}.get(sid.lower(),sid),int(number))

def bulbagarden_mep_cards():
    """Read independent GitHub MEP catalog, avoiding the blocked Bulbagarden API."""
    result={}
    base='https://api.github.com/repos/willregelmann/database-of-things/contents/collections/trading-cards/pokemon-tcg/mega-evolution-series/promos'
    try:
        with urllib.request.urlopen(urllib.request.Request(base,headers={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/vnd.github+json'}),timeout=20) as response:
            rows=json.load(response)
        for row in rows:
            match=re.fullmatch(r'mep([0-9]+)-(.+)[.]yaml',row.get('name',''),re.I)
            if not match:continue
            number=int(match.group(1))
            result.setdefault(number,[]).append((match.group(2),row.get('download_url','')))
    except (ValueError,KeyError,urllib.error.URLError,OSError,TimeoutError) as error:
        print('GitHub MEP catalog unavailable:',error,flush=True)
    return result

def bulbagarden_mep_source(sid,card,known):
    if sid!='mep':return ''
    number=str(card.get('number','')).strip()
    if not number.isdigit():return ''
    normalize=lambda x:re.sub(r'[^a-z0-9]','',str(x).lower())
    name=normalize(card.get('name',''))
    for filename_name,metadata_url in known.get(int(number),[]):
        if normalize(filename_name)!=name:continue
        try:
            with urllib.request.urlopen(urllib.request.Request(metadata_url,headers={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'text/plain'}),timeout=12) as response:
                metadata=response.read(10000).decode('utf-8')
            match=re.search(r'^image:\s*(https://archives[.]bulbagarden[.]net/wiki/Special:FilePath/[^\s]+)',metadata,re.M)
            if match:return match.group(1)
        except (urllib.error.URLError,OSError,TimeoutError,UnicodeError):continue
    return ''

# Independent Trainer Kit scans: resolve exact PkmnCards card page and verify its title.
TRAINER_KIT_CODES={'tk-bw-e':'tk5e','tk-bw-z':'tk5z'}
def trainer_kit_scan(sid,card):
    code=TRAINER_KIT_CODES.get(sid)
    if not code:return ''
    number=str(card.get('number','')).strip()
    if not number.isdigit():return ''
    name=str(card.get('name','')).strip()
    slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
    label='black-white-trainer-kit-'+('excadrill' if sid=='tk-bw-e' else 'zoroark')
    url='https://pkmncards.com/card/'+slug+'-'+label+'-'+code+'-'+str(int(number))+'/'
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; ZamexCardsChecklist/1.0)','Accept':'text/html'}),timeout=12) as response:
            html=response.read(250000).decode('utf-8','replace')
        title=re.search(r'<title[^>]*>(.*?)</title>',html,re.I|re.S)
        if not title or code.upper() not in title.group(1).upper() or not re.search(r'#'+str(int(number))+r'\\b',title.group(1)):return ''
        if re.sub(r'[^a-z0-9]','',name.lower()) not in re.sub(r'[^a-z0-9]','',title.group(1).lower()):return ''
        tag=re.search(r'<meta[^>]+og:image[^>]*>',html,re.I)
        image=re.search(r'content="([^"]+)"',tag.group(0),re.I) if tag else None
        if tag and not image:image=re.search("content='([^']+)'",tag.group(0),re.I)
        return image.group(1).replace('&amp;','&') if image and image.group(1).startswith('https://') else ''
    except (urllib.error.URLError,OSError,TimeoutError):return ''

def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    attempted=0; saved=0; changed=0
    pocket=pocket_cards()
    mep_scans=bulbagarden_mep_cards()
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
    focus=os.getenv('IMAGE_FOCUS_SET','').strip().lower()
    for p in SETS.glob('*.json'):
        if focus and p.stem.lower()!=focus:continue
        payload=json.loads(p.read_text(encoding='utf-8'))
        sid=p.stem
        logo=payload['set'].get('images',{}).get('logo','')
        cards=payload.get('cards',[])
        logo_action=not logo.startswith('./assets/') and bool(logo or supplemental(sid,kind='logo'))
        card_actions=sum(bool((c.get('images',{}).get('small','') or supplemental(sid,c.get('number')) or pocket_source(sid,c,pocket) or bulbagarden_mep_source(sid,c,mep_scans) or sid in TRAINER_KIT_CODES) and not c.get('images',{}).get('small','').startswith('./assets/')) for c in cards)
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
        actionable=(bool(logo) or bool(supplemental(sid,kind='logo'))) and not logo.startswith('./assets/') or any((c.get('images',{}).get('small','') or supplemental(sid,c.get('number')) or pocket_source(sid,c,pocket) or bulbagarden_mep_source(sid,c,mep_scans)) and not c.get('images',{}).get('small','').startswith('./assets/') for c in cards)
        if not actionable:continue
        attempted+=1
        original=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        if not logo.startswith('./assets/'):
            new=archive(logo,sid,'logo','logo') or archive(supplemental(sid,kind='logo'),sid,'logo','logo')
            if new:info['images']['logo']=new;saved+=1
        pilot=int(os.getenv('IMAGE_PILOT_CARDS','0'))
        for card in cards:
            if pilot and sid=='mep' and (not str(card.get('number','')).isdigit() or int(card['number'])>pilot):continue
            current=card.get('images',{}).get('small','')
            if current.startswith('./assets/'):continue
            number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or card['id']))
            pocket_url=pocket_source(sid,card,pocket)
            # The same verified Pocket card number may be stored zero-padded in image repositories.
            pocket_padded=(POCKET_IMAGE.format({'p-a':'PROMO-A','p-b':'PROMO-B'}.get(sid.lower(),sid),str(int(card['number'])).zfill(3)) if pocket_url and str(card.get('number','')).isdigit() else '')
            pocket_set={'p-a':'P-A','p-b':'P-B'}.get(sid.lower(),sid)
            alternate=(POCKET_ALTERNATE.format(pocket_set,str(int(card['number'])).zfill(3)) if pocket_url and str(card.get('number','')).isdigit() else '')
            new=archive(current,sid,number,'card') or archive(supplemental(sid,card.get('number')),sid,number,'card') or archive(pocket_url,sid,number,'card') or archive(pocket_padded,sid,number,'card') or archive(alternate,sid,number,'card') or archive(bulbagarden_mep_source(sid,card,mep_scans),sid,number,'card') or archive(trainer_kit_scan(sid,card),sid,number,'card')
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
