#!/usr/bin/env python3
"""Isolated MEP 001 image trial using the independently identified PkmnCards page."""
import json,re,html,urllib.request,urllib.error
from pathlib import Path
from archive_images import ROOT,archive
page='https://pkmncards.com/card/meganium-mega-evolution-promos-mep-001/'
report={'card':'mep-001','page':page,'status':'not_started'}
try:
    req=urllib.request.Request(page,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
    with urllib.request.urlopen(req,timeout=20) as response:
        body=response.read(400000).decode('utf-8','replace')
    title=re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
    label=html.unescape(title.group(1)) if title else ''
    report['title']=label
    if not ('Meganium' in label and 'MEP' in label and '001' in label):
        report['status']='card_identity_mismatch'
    else:
        tag=next((t for t in re.findall(r'<meta\\s+[^>]*>',body,re.I) if re.search(r'(?:og:image|twitter:image)',t,re.I)), '')
        match=re.search(r'content=["\\x27]([^"\\x27]+)',tag,re.I)
        if not match:report['status']='no_image_metadata'
        else:
            source=html.unescape(match.group(1))
            report['source']=source
            result=archive(source,'mep','001','card')
            if result:
                target=ROOT/'data/sets/mep.json'
                payload=json.loads(target.read_text())
                card=next(c for c in payload['cards'] if c['number']=='001' and c['name']=='Meganium')
                card['images']['small']=result
                target.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
                report['status']='saved'
                report['local_path']=result
            else:report['status']='download_or_image_validation_failed'
except urllib.error.HTTPError as exc:report['status']='page_http_'+str(exc.code)
except Exception as exc:report['status']='error_'+type(exc).__name__;report['detail']=str(exc)[:200]
out=ROOT/'data/mep_one_card_report.json'
out.write_text(json.dumps(report,indent=2)+'\\n')
print('MEP ONE CARD:',json.dumps(report),flush=True)
