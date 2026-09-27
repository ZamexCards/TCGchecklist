#!/usr/bin/env python3
"""Conservative Pikawiz card-art recovery: require exact card page identity and image URL."""
# Trigger first scheduled repair after workflow registration.
import html.parser, json, pathlib, re, urllib.parse, urllib.request, urllib.error
from archive_images import ROOT, SETS, archive
REPORT=ROOT/'data'/'pikawiz_repair.json'
SETS_MAP={'30th-c':'30th-celebration-classic-collection','cel25cc':'celebrationsclassic',
'ecard2':'aquapolis','ecard3':'skyridge','pop6':'popseries6',
'swshp':'swshpromo','svp':'svpromo','2023sv':'mcdonalds2023',
'2024sv':'mcdonalds2024'}
class Images(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.images=[]
 def handle_starttag(self,tag,attrs):
  if tag!='img':return
  a=dict(attrs);self.images.append(a)
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; ZamexCardsChecklist/1.0)'})
 with urllib.request.urlopen(req,timeout=12) as r:return r.read(2000000).decode('utf-8','replace')
def norm(s):return re.sub('[^a-z0-9]','',str(s).casefold())
def printed(s):return str(s).upper().removeprefix('CC').lstrip('0') or '0'
def main():
 report={};saved=0
 for sid,slug in SETS_MAP.items():
  p=SETS/(sid+'.json')
  if not p.exists():continue
  data=json.loads(p.read_text(encoding='utf-8'));items=[]
  for card in data.get('cards',[]):
   if card.get('images',{}).get('small','').startswith('./assets/'):continue
   number=str(card.get('number',''));name=str(card.get('name',''))
   # The source's URL uses printed numeric IDs; do not infer card artwork from listing position.
   if not re.fullmatch(r'[0-9]+|CC[0-9]+',number,re.I):
    items.append({'number':number,'name':name,'status':'unsupported_number'});continue
   slugname=re.sub(r'[^a-z0-9]+','-',name.casefold()).strip('-')
   url='https://www.pikawiz.com/card/'+slug+'/'+urllib.parse.quote(slugname)+'/'+printed(number)
   try:
    page=get(url)
    # Verify the destination itself identifies the expected set, name and printed number.
    title=re.search(r'<title[^>]*>(.*?)</title>',page,re.I|re.S)
    title=re.sub('<[^>]+>',' ',title.group(1)) if title else ''
    if norm(name) not in norm(title) or norm(slug.replace('-','')) not in norm(title):
     items.append({'number':number,'name':name,'status':'identity_not_verified','url':url});continue
    parser=Images();parser.feed(page)
    images=[]
    for im in parser.images:
     src=im.get('data-src') or im.get('src') or ''
     alt=im.get('alt','')
     if not src or not src.startswith(('https://','http://')):continue
     if norm(name) not in norm(alt):continue
     if not re.search(r'\.(?:png|webp|jpe?g)(?:\?|$)',src,re.I):continue
     images.append(src)
    images=list(dict.fromkeys(images))
    if len(images)!=1:
     items.append({'number':number,'name':name,'status':'image_ambiguous_or_missing','candidates':len(images),'url':url});continue
    local=archive(images[0],sid,re.sub('[^A-Za-z0-9_-]','_',number),'card')
    if local:
     card.setdefault('images',{})['small']=local;saved+=1
     items.append({'number':number,'name':name,'status':'saved','local':local})
    else:items.append({'number':number,'name':name,'status':'download_failed','url':url})
   except (urllib.error.URLError,OSError,TimeoutError,ValueError) as e:
    items.append({'number':number,'name':name,'status':'request_failed','error':str(e)[:100]})
  p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
  report[sid]=items
  print('Pikawiz:',sid,'checked:',len(items),'saved:',sum(x['status']=='saved' for x in items),flush=True)
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Pikawiz total saved:',saved,flush=True)
if __name__=='__main__':main()
