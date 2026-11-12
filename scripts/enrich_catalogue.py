#!/usr/bin/env python3
"""Persist English card details and genuine artwork with identity-checked provenance.

No synthesized foil/pattern images are stored. Reviewed local printings win over
incomplete upstream flags. Source gaps are reported, never silently invented.
"""
import argparse, concurrent.futures, copy, datetime as dt, gzip, hashlib, io, json, os, pathlib, re, threading, time, unicodedata, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageOps
ROOT=pathlib.Path(__file__).resolve().parents[1]
API='https://api.tcgdex.net/v2/en'
PUBLIC='https://zamexcards.github.io/TCGchecklist/'
LEGACY='https://raw.githubusercontent.com/PokemonTCG/pokemon-tcg-data/master/'
HEADERS={'User-Agent':'ZamexCardsCatalogue/2.0 (English archival import)','Accept':'application/json'}
SCHEMA='2.0'; MAX_IMAGE=12_000_000
LOCK=threading.Lock()

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def norm(s):return re.sub(r'[^\w♀♂]','',unicodedata.normalize('NFKC',str(s)).casefold())
def num(s):return re.sub(r'^0+(?=\d)','',str(s))
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');tmp.replace(path)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def get(url,attempts=3,image=False):
 for attempt in range(attempts):
  try:
   req=urllib.request.Request(url,headers={**HEADERS,'Accept':'image/*' if image else 'application/json'})
   with urllib.request.urlopen(req,timeout=22)as response:
    if image:
     body=response.read(MAX_IMAGE+1)
     if len(body)>MAX_IMAGE:raise ValueError('image_too_large')
     return body
    return json.load(response)
  except urllib.error.HTTPError as e:
   if e.code in (400,404,410):raise
   if attempt==attempts-1:raise
   time.sleep(min(10,2**attempt))
  except (OSError,ValueError,TimeoutError):
   if attempt==attempts-1:raise
   time.sleep(min(5,2**attempt))
def safe(s):
 if not re.fullmatch(r'[A-Za-z0-9_.-]+',str(s))or str(s).startswith('.'):raise ValueError('unsafe_identifier')
 return str(s)
def file_number(value):
 s=str(value)
 return s if re.fullmatch(r'[A-Za-z0-9_.-]+',s)and not s.startswith('.')else re.sub(r'[^A-Za-z0-9_-]','_',s)+'-'+hashlib.sha256(s.encode()).hexdigest()[:8]
def local(path):
 if not isinstance(path,str)or not path.startswith('./assets/'):return None
 p=(ROOT/path[2:]).resolve()
 return p if p.is_relative_to((ROOT/'assets').resolve())and p.is_file() else None
def valid_image(path):
 p=local(path)
 if not p:return False
 try:
  with Image.open(p)as im:im.verify()
  return p.stat().st_size>500
 except (OSError,ValueError):return False
def identity(old,detail,sid):
 if detail.get('id')!=old['id']or detail.get('set',{}).get('id')!=sid or num(detail.get('localId'))!=num(old['number'])or norm(detail.get('name'))!=norm(old['name']):raise ValueError('identity_mismatch')
def label(v):
 s={'normal':'Normal','holo':'Holo','reverse':'Reverse holo','base':'Basiskaart'}.get(v.get('type'),v.get('type','Uitvoering'))
 if v.get('foil')in('pokeball','masterball'):s={'pokeball':'Poké Ball','masterball':'Master Ball'}[v['foil']]
 elif v.get('foil'):s+=' · '+v['foil'].title()
 if v.get('subtype'):s+=' · '+{'unlimited':'Unlimited','shadowless':'Shadowless','1999-2000-copyright':'1999–2000 copyright'}.get(v['subtype'],v['subtype'])
 stamps=v.get('stamp')or[];stamps=[stamps]if isinstance(stamps,str)else stamps
 if stamps:s+=' · '+', '.join({'1st-edition':'1st Edition','set-logo':'setlogo','snowflake':'sneeuwvlok','horizons':'Horizons'}.get(x,x)for x in stamps)
 if v.get('firstEdition')and '1st-edition'not in stamps:s+=' · 1st Edition'
 if v.get('size')and v['size']!='standard':s+=' · '+v['size'].title()
 return s
def signature(v):
 return tuple(json.dumps(v.get(k),sort_keys=True)for k in ('type','foil','subtype','stamp','size','firstEdition'))
def is_ordinary(v):return v.get('type')not in('reverse',)and not v.get('stamp')and not v.get('firstEdition')and v.get('size','standard')=='standard'and v.get('subtype','unlimited')=='unlimited'and v.get('foil')not in('pokeball','masterball','cosmos')
def printings(old,d):
 raw=copy.deepcopy(d.get('variants_detailed')or[])
 if not raw:
  raw=[{'type':k,'size':'standard'}for k in ('normal','holo','reverse')if (d.get('variants')or{}).get(k)is True]
  if not raw:raw=[{'type':'base','size':'standard','verification':'incomplete_source_variants'}]
 primary=next((v for v in raw if is_ordinary(v)),None)
 if primary is None:primary=next((v for v in raw if v.get('type')!='reverse'),raw[0])
 result=[]
 for i,v in enumerate(raw):
  v['key']=v.get('variantId')or 'source-'+hashlib.sha256(repr(signature(v)).encode()).hexdigest()[:16]
  v['_baseReference']=v is primary;v['label']=label(v);v['images']={'small':old.get('images',{}).get('small','')if v is primary else ''}
  v['source']=API+'/cards/'+old['id'];v['verification']=v.get('verification','source_record')
  v['imageStatus']='reference_image'if v['images']['small']else'needs_additional_sources'
  result.append(v)
 # Previously reviewed image assignments and explicitly checked variants survive.
 previous=old.get('printings')or[]
 reviewed=bool(old.get('_variantSource')or old.get('_enrichedSource'))
 for p in previous:
  match=next((v for v in result if signature(v)==signature(p)or(v.get('variantId')and v.get('variantId')==p.get('variantId'))or v['label'].casefold()==p.get('label','').casefold()),None)
  if match:
   if reviewed:
    for k in ('key','label','verification'): 
     if p.get(k):match[k]=p[k]
    if p.get('images',{}).get('small'):match['images']=copy.deepcopy(p['images']);match['imageStatus']=p.get('imageStatus','catalogue_image')
  elif reviewed:result.append(copy.deepcopy(p))
 if reviewed and not previous:
  for name in old.get('availableVariants',[]):
   if name=='Base':continue
   if not any(p['label'].casefold()==name.casefold()for p in result):
    t='reverse'if'reverse'in name.casefold()else'holo'if'holo'in name.casefold()else'normal'
    result.append({'key':name.casefold().replace(' ','-'),'label':name,'type':t,'size':'standard','images':{'small':''},'source':old['_variantSource'],'verification':'reviewed_local','imageStatus':'needs_additional_sources'})
 # No duplicated keys even if upstream reuses a variantId.
 keys=set()
 for i,p in enumerate(result):
  key=p.get('key')or p.get('variantId')or str(i)
  if key in keys:key+='-'+str(i)
  keys.add(key);p['key']=key
 return result

def merge(old,d,sid):
 identity(old,d,sid);out=copy.deepcopy(old)
 out.update({k:copy.deepcopy(v)for k,v in d.items()if k not in('id','name','localId','set','image','variants_detailed')})
 out.update(language='en',setId=sid,number=old['number'],supertype=d.get('category')or old.get('supertype',''),subtypes=[d['stage']]if d.get('stage')else old.get('subtypes',[]))
 out['images']=copy.deepcopy(old.get('images',{}));out['printings']=printings(old,d);out['availableVariants']=[p['label']for p in out['printings']]
 out['baseVariant']=next((p['label']for p in out['printings']if p.get('images',{}).get('small')==out['images'].get('small')and out['images'].get('small')),out['printings'][0]['label'])
 out['_enrichedSource']=API+'/cards/'+old['id'];out['_schemaVersion']=SCHEMA
 out['provenance']={**old.get('provenance',{}),'primary':{'provider':'TCGdex','url':out['_enrichedSource'],'language':'en','fetchedAt':now(),'sourceUpdatedAt':d.get('updated'),'identityChecked':['id','setId','number','name']}}
 return out

def archive(url,sid,filename,kind,evidence):
 if not url or not url.startswith('https://'):return None
 safe(sid);safe(filename);target=ROOT/'assets/sets'/sid/filename
 try:
  # Resumable imports never need to redownload archived source files.
  if target.is_file():
   with Image.open(target)as im:im.load();w,h=im.size
  else:
   body=get(url,attempts=2,image=True)
   with Image.open(io.BytesIO(body))as source:
    source.load();w,h=source.size
    if kind!='logo'and (w<200 or h<280):raise ValueError('not_a_card_image')
    if w*h>20_000_000:raise ValueError('oversized_image')
    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix('.tmp.webp')
    image=ImageOps.exif_transpose(source).convert('RGBA'if source.mode=='RGBA'else'RGB')
    image.save(tmp,'WEBP',quality=90,method=4);tmp.replace(target)
  raw=target.read_bytes()
  return {'path':'./'+str(target.relative_to(ROOT)),'sourceUrl':url,'sha256':hashlib.sha256(raw).hexdigest(),'width':w,'height':h,'bytes':len(raw),'kind':kind,'identityEvidence':evidence,'archivedAt':now()}
 except (OSError,ValueError,urllib.error.URLError,TimeoutError)as e:return {'error':type(e).__name__+': '+str(e),'sourceUrl':url}

def secondary_set(info,rows):
 # IDs differ between providers (e.g. sv08.5 vs sv8pt5). A name alias alone is
 # insufficient: a matching printed count is required as an independent check.
 aliases={'baseset':'base','151':'151'}
 name=aliases.get(norm(info['name']),norm(info['name']))
 matches=[s for s in rows if aliases.get(norm(s['name']),norm(s['name']))==name and int(s.get('printedTotal',0))==int(info.get('printedTotal',-1))]
 return matches[0]if len(matches)==1 else None

def supplement(card,other,source):
 if num(other.get('number'))!=num(card['number'])or norm(other.get('name'))!=norm(card['name']):return card
 fields=[]
 mapping={'artist':'illustrator','flavorText':'description','nationalPokedexNumbers':'dexId','evolvesFrom':'evolveFrom','evolvesTo':'evolveTo','regulationMark':'regulationMark','hp':'hp','types':'types','weaknesses':'weaknesses','resistances':'resistances'}
 for k,dst in mapping.items():
  if not card.get(dst)and other.get(k)is not None:card[dst]=copy.deepcopy(other[k]);fields.append(dst)
 for k in ('attacks','abilities'):
  if not card.get(k)and other.get(k):card[k]=[{**a,'effect':a.get('text','')}for a in other[k]];fields.append(k)
 if card.get('retreat')is None and other.get('convertedRetreatCost')is not None:card['retreat']=other['convertedRetreatCost'];fields.append('retreat')
 # Historical compatibility facts remain clearly attributed, especially legality.
 if not isinstance(card.get('thirdParty'),dict):card['thirdParty']={}
 card['thirdParty']['pokemonTcg']=other['id']
 card['supplemental']={'pokemonTcg':{k:copy.deepcopy(other[k])for k in ('id','subtypes','rules','ancientTrait','legalities','evolvesTo','level','images')if k in other}}
 if not card.get('effect')and other.get('rules'):card['effect']='\n'.join(other['rules']);fields.append('effect')
 card.setdefault('provenance',{})['secondary']={'provider':'PokemonTCG legacy dataset','url':source,'language':'en','fetchedAt':now(),'identityChecked':['setName','setPrintedTotal','number','name'],'fieldsFilled':fields,'historicalCompatibilitySource':True}
 return card

def process_card(old,info,secondary,secondary_url,refresh=False):
 sid=info['id'];issues=[];card=copy.deepcopy(old);detail=None
 cached=card.get('_schemaVersion')==SCHEMA and card.get('provenance',{}).get('primary',{}).get('fetchedAt','')> (dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=7)).isoformat()
 try:
  if cached and not refresh:detail={'image':card.get('imageSourceBase','')}
  else:
   detail=get(API+'/cards/'+urllib.parse.quote(old['id'],safe=''));card=merge(old,detail,sid)
   if detail.get('image'):card['imageSourceBase']=detail['image']
 except Exception as e:issues.append({'type':'card_detail','reason':str(e),'source':API+'/cards/'+old['id']})
 other=secondary.get((num(card['number']),norm(card['name'])))
 if other:card=supplement(card,other,secondary_url)
 card.update(language='en',setId=sid)
 card.setdefault('images',{})
 # Base artwork: preserve existing verified files; consult a second catalogue if
 # the primary source supplies no image. Never derive an ID from a similar name.
 if not valid_image(card['images'].get('small','')):
  candidates=[]
  if detail and detail.get('image'):candidates.append(detail['image']+'/high.webp')
  old_url=card['images'].get('small','')
  if old_url.startswith('https://'):candidates.append(old_url)
  if other:
   candidates.extend([other.get('images',{}).get('large',''),other.get('images',{}).get('small','')])
  for url in dict.fromkeys(candidates):
   a=archive(url,sid,file_number(card['number'])+'-archived.webp','base',{'cardId':card['id'],'number':card['number'],'name':card['name'],'language':'en'})
   if a and not a.get('error'):
    card['images']['small']=a['path'];card.setdefault('imageAssets',{})['base']=a;break
  if not valid_image(card['images'].get('small','')):issues.append({'type':'base_image','reason':'No independently matched English image could be archived.','sourcesTried':[x for x in candidates if x]})
 # Keep a source high-resolution URL distinct from the actually archived file.
 if card.get('imageSourceBase'):card['images']['sourceLarge']=card['imageSourceBase']+'/high.webp'
 if not card.get('printings'):
  card['printings']=[{'key':'base','type':'base','label':'Basiskaart','images':{'small':card['images'].get('small','')},'verification':'summary_only','imageStatus':'reference_image'}]
 base_assigned=False
 for p in card['printings']:
  p.setdefault('images',{})
  if p['images'].get('small')==old.get('images',{}).get('small')and p['images'].get('small'):
   p['images']['small']=card['images'].get('small','');base_assigned=True
  if not p['images'].get('small')and (p.get('_baseReference')or is_ordinary(p))and not base_assigned:
   p['images']['small']=card['images'].get('small','');base_assigned=True
  # Ball patterns have explicit separate product IDs. Do not apply generic
  # marketplace images to first editions, shadowless, stamps or Jumbo formats.
  pid=(p.get('thirdParty')or{}).get('tcgplayer')
  if not valid_image(p['images'].get('small',''))and p.get('foil')in('pokeball','masterball')and pid and not p.get('stamp')and p.get('size','standard')=='standard':
   url='https://tcgplayer-cdn.tcgplayer.com/product/'+str(int(pid))+'_in_1000x1000.jpg'
   a=archive(url,sid,file_number(card['number'])+'-'+p['foil']+'.webp','variant',{'cardId':card['id'],'variantId':p.get('variantId'),'productId':pid,'foil':p['foil'],'language':'en'})
   if a and not a.get('error'):p['images']['small']=a['path'];p['imageAsset']=a;p['verification']='source_product_matched'
  p.pop('_baseReference',None)
  p['imageStatus']='catalogue_image'if valid_image(p['images'].get('small',''))else'needs_additional_sources'
  if p['imageStatus']=='needs_additional_sources':issues.append({'type':'variant_image','variantKey':p['key'],'variant':p['label'],'reason':'Separate English scan not verified; no simulated scan stored.','source':p.get('source')or card.get('_variantSource')or API+'/cards/'+card['id']})
 if not card.get('illustrator'):issues.append({'type':'illustrator','reason':'Artist not supplied by the matched sources.'})
 if card.get('supertype')=='Pokemon'and not card.get('hp'):issues.append({'type':'hp','reason':'HP not supplied by the matched sources.'})
 if card.get('supertype')=='Pokemon'and not any(card.get(k)for k in ('attacks','abilities','effect')):issues.append({'type':'card_text','reason':'No attacks, ability or effect supplied by the matched sources.'})
 card['availableVariants']=[p['label']for p in card['printings']]
 card['dataQuality']={'detailsArchived':bool(card.get('_enrichedSource')),'baseImageArchived':valid_image(card['images'].get('small','')),'printings':len(card['printings']),'variantImagesArchived':sum(valid_image(p['images'].get('small',''))for p in card['printings']),'openResearch':len(issues),'notApplicable':['regulationMark']if not card.get('regulationMark')and (info.get('releaseDate','')<'2017-01-01')else[]}
 return card,[{'setId':sid,'cardId':card['id'],'number':card['number'],'name':card['name'],**x}for x in issues]

def exports(manifest):
 issues=[];allcards=[];series={};totals={'sets':0,'cards':0,'detailsArchived':0,'baseImagesArchived':0,'printings':0,'variantImagesArchived':0,'openResearch':0};assets={};byset=[]
 for s in manifest['sets']:
  data=read(ROOT/'data/sets'/(s['id']+'.json'));cards=data['cards'];totals['sets']+=1
  row={k:0 for k in ('cards','detailsArchived','baseImagesArchived','printings','variantImagesArchived','openResearch')}
  for c in cards:
   q=c.get('dataQuality',{});row['cards']+=1
   for target,key in [('detailsArchived','detailsArchived'),('baseImagesArchived','baseImageArchived'),('printings','printings'),('variantImagesArchived','variantImagesArchived'),('openResearch','openResearch')]:row[target]+=int(q.get(key,0))
   allcards.append(c)
   for path in [c.get('images',{}).get('small','')]+[p.get('images',{}).get('small','')for p in c.get('printings',[])]:
    if path and path not in assets:
     f=local(path)
     if f:
      try:
       with Image.open(f)as im:w,h=im.size
       assets[path]={'url':PUBLIC+path[2:],'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'width':w,'height':h,'bytes':f.stat().st_size,'sourceStatus':'source_metadata_in_card'if c.get('imageAssets')else'previously_archived'}
      except (OSError,ValueError):pass
  byset.append({'id':s['id'],'name':s['name'],**row})
  for k,v in row.items():totals[k]+=v
  rp=ROOT/'data/research/sets'/(s['id']+'.json')
  if rp.exists():issues.extend(read(rp).get('issues',[]))
  series.setdefault(s.get('series')or'Other',[]).append(s['id'])
 checked=now();write(ROOT/'data/catalogue-quality.json',{'schemaVersion':SCHEMA,'checked':checked,'totals':totals,'sets':byset,'scope':'All stored English sets; digital Pocket collections remain explicitly separate.','complete':totals['openResearch']==0})
 write(ROOT/'data/research/open.json',{'checked':checked,'total':len(issues),'issues':issues})
 write(ROOT/'data/series.json',{'schemaVersion':SCHEMA,'language':'en','series':[{'id':re.sub(r'[^a-z0-9]+','-',n.casefold()).strip('-'),'name':n,'sets':ids}for n,ids in series.items()]})
 write(ROOT/'data/cards-index.json',{'schemaVersion':SCHEMA,'language':'en','cards':[{'id':c['id'],'name':c['name'],'number':c['number'],'setId':c.get('setId'),'setDataUrl':PUBLIC+'data/sets/'+c.get('setId','')+'.json','images':c.get('images',{})}for c in allcards]})
 write(ROOT/'data/image-assets.json',{'schemaVersion':SCHEMA,'checked':checked,'assets':assets})
 out=ROOT/'data/exports';out.mkdir(exist_ok=True)
 with gzip.GzipFile(filename=str(out/'pokemon-en.json.gz'),mode='wb',mtime=0)as f:f.write(json.dumps({'schemaVersion':SCHEMA,'language':'en','updated':checked,'sets':manifest['sets'],'cards':allcards},ensure_ascii=False,separators=(',',':')).encode())
 write(ROOT/'data/catalogue.json',{'schemaVersion':SCHEMA,'language':'en','baseUrl':PUBLIC,'updated':checked,'endpoints':{'sets':'data/sets.json','series':'data/series.json','cardIndex':'data/cards-index.json','set':'data/sets/{setId}.json','bulk':'data/exports/pokemon-en.json.gz','images':'data/image-assets.json','quality':'data/catalogue-quality.json','research':'data/research/open.json'},'totals':totals,'imagePolicy':'Only genuine source images are archived. A reverse shine overlay is a UI effect, not a scan. Source image rights remain with their respective rights holders.'})
 print('CATALOGUE TOTALS '+json.dumps(totals),flush=True)
 return totals

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--sets',nargs='*');parser.add_argument('--refresh',action='store_true');parser.add_argument('--exports-only',action='store_true');args=parser.parse_args()
 manifest=read(ROOT/'data/sets.json')
 try:secondary_rows=get(LEGACY+'sets/en.json')
 except Exception as e:print('Secondary listing unavailable:',e,flush=True);secondary_rows=[]
 if not args.exports_only:
  for info in manifest['sets']:
   sid=safe(info['id'])
   if args.sets and sid not in args.sets:continue
   path=ROOT/'data/sets'/(sid+'.json');payload=read(path)
   if payload['set']['id']!=sid:raise ValueError('Set identity mismatch')
   secondary={};matched=secondary_set(info,secondary_rows);secondary_url=''
   if matched:
    secondary_url=LEGACY+'cards/en/'+matched['id']+'.json'
    try:
     for c in get(secondary_url):
      key=(num(c['number']),norm(c['name']))
      if key in secondary:secondary[key]=None
      else:secondary[key]=c
     secondary={k:v for k,v in secondary.items()if v is not None}
    except Exception as e:print('Secondary set unavailable:',sid,e,flush=True)
    for k in ('ptcgoCode','legalities'):
     if matched.get(k)and not payload['set'].get(k):payload['set'][k]=matched[k]
   cards=[];research=[]
   with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get('CATALOGUE_WORKERS','10')))as pool:
    for c,issues in pool.map(lambda old:process_card(old,info,secondary,secondary_url,args.refresh),payload['cards']):cards.append(c);research.extend(issues)
   assert len(cards)==len(payload['cards'])and len({c['id']for c in cards})==len(cards)
   payload.update(cards=cards,updated=now(),schemaVersion=SCHEMA,language='en')
   payload['set']['game']='pokemon-tcg-pocket'if'Pocket'in info.get('series','')else'pokemon-tcg';payload['set']['language']='en'
   # Preserve set metadata changes in the shared manifest too.
   info.update(payload['set'])
   write(path,payload);write(ROOT/'data/research/sets'/(sid+'.json'),{'setId':sid,'checked':now(),'issues':research})
   print('ENRICHED',sid,len(cards),'details',sum(bool(c.get('_enrichedSource'))for c in cards),'research',len(research),flush=True)
  manifest['updated']=now();manifest['schemaVersion']=SCHEMA;write(ROOT/'data/sets.json',manifest)
 exports(manifest)
if __name__=='__main__':main()
