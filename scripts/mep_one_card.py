#!/usr/bin/env python3
"""Verify and archive exactly Meganium MEP 001 from its independent card page."""
import json, re, html, urllib.request, urllib.error, urllib.parse
from html.parser import HTMLParser
from archive_images import ROOT, archive

PAGE = 'https://pkmncards.com/card/meganium-mega-evolution-promos-mep-001/'
report = {'card':'mep-001','page':PAGE,'status':'not_started'}

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('property','').lower() in ('og:image','twitter:image'):
            self.urls.append(('meta', a.get('content','')))
        if tag in ('img','source'):
            for key in ('data-src','data-lazy-src','src','srcset','data-srcset'):
                value = a.get(key,'')
                if value:
                    self.urls.append((key, value.split(',')[0].strip().split(' ')[0]))
        if tag == 'a':
            value = a.get('href','')
            if value.lower().split('?')[0].endswith(('.png','.jpg','.jpeg','.webp')):
                self.urls.append(('link',value))

try:
    request=urllib.request.Request(PAGE,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
    with urllib.request.urlopen(request,timeout=20) as response:
        body=response.read(500000).decode('utf-8','replace')
    title=re.search('<title[^>]*>(.*?)</title>',body,re.I|re.S)
    label=html.unescape(title.group(1)) if title else ''
    report['title']=label
    if not all(word in label.lower() for word in ('meganium','mep','001')):
        report['status']='card_identity_mismatch'
    else:
        parser=Images()
        parser.feed(body)
        options=[]
        for kind,value in parser.urls:
            url=urllib.parse.urljoin(PAGE,html.unescape(value))
            parsed=urllib.parse.urlparse(url)
            if parsed.scheme!='https' or parsed.hostname not in ('pkmncards.com','www.pkmncards.com'):
                continue
            if not parsed.path.lower().endswith(('.png','.jpg','.jpeg','.webp')):
                continue
            if not any(word in url.lower() for word in ('meganium','mep-001','mep_001','mep001','mebsp-001')):
                continue
            if url not in options:options.append(url)
        report['candidates']=options[:12]
        report['candidate_count']=len(options)
        for source in options[:6]:
            result=archive(source,'mep','001','card')
            if result:
                target=ROOT/'data/sets/mep.json'
                payload=json.loads(target.read_text())
                card=next(c for c in payload['cards'] if c['number']=='001' and c['name']=='Meganium')
                card['images']['small']=result
                target.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
                report.update(status='saved',source=source,local_path=result)
                break
        else:
            report['status']='download_or_validation_failed' if options else 'no_matching_image_in_html'
except urllib.error.HTTPError as exc:
    report['status']='page_http_'+str(exc.code)
except Exception as exc:
    report['status']='error_'+type(exc).__name__
    report['detail']=str(exc)[:200]
(ROOT/'data/mep_one_card_report.json').write_text(json.dumps(report,indent=2)+'\n')
print('MEP ONE CARD:',json.dumps(report),flush=True)
