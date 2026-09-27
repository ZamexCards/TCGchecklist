#!/usr/bin/env python3
"""Targeted, resumable repair of individual missing checklist cards.

Only exact TCGdex card IDs with matching printed number and normalized name are accepted.
No fuzzy cross-set substitution; results and failed lookups are recorded per card.
"""
import datetime
import json
import os
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from archive_images import ROOT, SETS, MANIFEST, archive, supplemental, CACHE_PATH, FAILURE_CACHE, FALLBACK_SETS

REPORT=ROOT/'data'/'targeted_image_repair.json'
LIMIT=int(os.getenv('TARGETED_REPAIR_LIMIT','120'))
TODAY=datetime.date.today()
try:
    history=json.loads(REPORT.read_text(encoding='utf-8'))
except (OSError,ValueError):
    history={}
if not isinstance(history,dict):history={}
def norm(value):
    return re.sub(r'[^a-z0-9]', '',str(value or '').casefold())
def request_card(cid):
    url='https://api.tcgdex.net/v2/en/cards/'+urllib.parse.quote(cid,safe='')
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/json'}),timeout=15) as response:
            return json.load(response),'ok'
    except urllib.error.HTTPError as exc:
        return None,'http_'+str(exc.code)
    except (urllib.error.URLError,TimeoutError,ValueError,OSError):
        return None,'temporary_error'
def secondary_card(sid,number,name):
    """Query a second catalogue by exact mapped set ID and printed card number."""
    mapped=FALLBACK_SETS.get(sid)
    if not mapped:return None,'unmapped'
    identifier=mapped+'-'+str(number)
    url='https://api.pokemontcg.io/v2/cards/'+urllib.parse.quote(identifier,safe='')
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/json'}),timeout=12) as response:
            row=json.load(response).get('data') or {}
        if str(row.get('number',''))!=str(number) or norm(row.get('name'))!=norm(name):
            return None,'secondary_mismatch'
        images=row.get('images') or {}
        return images.get('small') or images.get('large') or None,'secondary_verified'
    except urllib.error.HTTPError as exc:
        return None,'secondary_http_'+str(exc.code)
    except (urllib.error.URLError,TimeoutError,ValueError,OSError):
        return None,'secondary_temporary_error'
def search_by_identity(set_name,number,name):
    """Search by exact set title, printed number and card name."""
    q='name:"'+str(name).replace('"','')+'" AND number:"'+str(number).replace('"','')+'"'
    url='https://api.pokemontcg.io/v2/cards?'+urllib.parse.urlencode({'q':q,'pageSize':50,'select':'id,name,number,set,images'})
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ZamexCardsChecklist/1.0','Accept':'application/json'}),timeout=15) as response:
            rows=json.load(response).get('data',[])
        matches=[row for row in rows if norm(row.get('name'))==norm(name)
                 and str(row.get('number','')).lstrip('0')==str(number).lstrip('0')
                 and norm((row.get('set') or {}).get('name'))==norm(set_name)]
        if len(matches)!=1:return None,'identity_ambiguous' if matches else 'identity_not_found'
        images=matches[0].get('images') or {}
        return images.get('small') or images.get('large') or None,'identity_verified'
    except urllib.error.HTTPError as exc:return None,'identity_http_'+str(exc.code)
    except (urllib.error.URLError,TimeoutError,ValueError,OSError):return None,'identity_temporary_error'
def eligible(entry):
    date=entry.get('checked','')
    if entry.get('strategy')!='identity_v2':return True
    if entry.get('status') not in ('no_source','http_404','http_410','image_unavailable','mismatch','secondary_http_404','secondary_mismatch','secondary_image_unavailable'):
        return True
    try:return (TODAY-datetime.date.fromisoformat(date)).days>=30
    except ValueError:return True
def main():
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    by_id={s['id']:s for s in manifest['sets']}
    examined=0; saved=0; skipped=0; changed=0
    for path in sorted(SETS.glob('*.json')):
        if examined>=LIMIT:break
        payload=json.loads(path.read_text(encoding='utf-8'))
        sid=path.stem
        dirty=False
        for card in payload.get('cards',[]):
            if examined>=LIMIT:break
            if card.get('images',{}).get('small','').startswith('./assets/'):continue
            cid=str(card.get('id',''))
            if not re.fullmatch(r'[A-Za-z0-9_-]+',cid):continue
            key=sid+'/'+cid
            if not eligible(history.get(key,{})):
                skipped+=1
                continue
            examined+=1
            result,status=request_card(cid)
            if result:
                if str(result.get('localId',''))!=str(card.get('number','')) or norm(result.get('name'))!=norm(card.get('name')):
                    status='mismatch'
                else:
                    source=result.get('image','')
                    number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or cid))
                    local=archive(source,sid,number,'card') if source else ''
                    if not local:
                        local=archive(supplemental(sid,card.get('number')),sid,number,'card')
                    if local:
                        card.setdefault('images',{})['small']=local
                        saved+=1;dirty=True;status='saved'
                    else:status='image_unavailable' if source else 'no_source'
            if status!='saved':
                alternate,alternate_status=secondary_card(sid,card.get('number',''),card.get('name',''))
                if alternate:
                    number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or cid))
                    local=archive(alternate,sid,number,'card')
                    if local:
                        card.setdefault('images',{})['small']=local
                        saved+=1;dirty=True;status='saved_secondary'
                    else:status='secondary_image_unavailable'
                elif alternate_status!='unmapped':
                    status=alternate_status
            if status not in ('saved','saved_secondary'):
                identity,identity_status=search_by_identity(payload['set'].get('name',''),card.get('number',''),card.get('name',''))
                if identity:
                    number=re.sub(r'[^A-Za-z0-9_-]','_',str(card.get('number') or cid))
                    local=archive(identity,sid,number,'card')
                    if local:
                        card.setdefault('images',{})['small']=local
                        saved+=1;dirty=True;status='saved_identity'
                    else:status='identity_image_unavailable'
                else:status=identity_status
            history[key]={'strategy':'identity_v2','status':status,'checked':TODAY.isoformat(),'card_number':card.get('number',''),'card_name':card.get('name','')}
            print('Targeted:',key,status,flush=True)
        if dirty:
            path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            changed+=1
    REPORT.write_text(json.dumps(history,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    CACHE_PATH.write_text(json.dumps(FAILURE_CACHE,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Targeted repair: checked:',examined,'saved:',saved,'updated sets:',changed,'recent failed checks skipped:',skipped,flush=True)
if __name__=='__main__':main()
