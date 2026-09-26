#!/usr/bin/env python3
"""Audit every checklist snapshot, including missing and broken local assets."""
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
SETS=ROOT/'data'/'sets'
OUT=ROOT/'data'/'image_audit.json'
REPORT=ROOT/'data'/'image_audit.md'

def status(url):
    if not url:
        return 'missing'
    if url.startswith(('https://','http://')):
        return 'external_unverified'
    if url.startswith('./'):
        relative=unquote(urlsplit(url).path[2:])
        target=(ROOT/relative).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            return 'invalid_path'
        return 'local' if target.is_file() and target.stat().st_size>1000 else 'broken_local'
    return 'invalid_path'

def main():
    rows=[]
    totals={'sets':0,'cards':0,'local_cards':0,'missing_cards':0,'external_cards':0,'broken_cards':0,'local_logos':0,'missing_logos':0,'external_logos':0,'broken_logos':0,'complete_sets':0}
    for path in sorted(SETS.glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        info=data.get('set',{})
        cards=data.get('cards',[])
        logo=status(info.get('images',{}).get('logo',''))
        missing=[];external=[];broken=[];local=0
        for card in cards:
            state=status(card.get('images',{}).get('small',''))
            entry={'id':card.get('id',''),'number':card.get('number',''),'name':card.get('name','')}
            if state=='local':local+=1
            elif state=='missing':missing.append(entry)
            elif state=='external_unverified':external.append(entry)
            else:broken.append({**entry,'reason':state})
        row={'id':info.get('id',path.stem),'name':info.get('name',path.stem),'logo_status':logo,'total_cards':len(cards),'local_cards':local,'missing_cards':missing,'external_unverified_cards':external,'broken_cards':broken}
        rows.append(row)
        totals['sets']+=1;totals['cards']+=len(cards);totals['local_cards']+=local
        totals['missing_cards']+=len(missing);totals['external_cards']+=len(external);totals['broken_cards']+=len(broken)
        totals[{'local':'local_logos','missing':'missing_logos','external_unverified':'external_logos'}.get(logo,'broken_logos')]+=1
        if logo=='local' and local==len(cards):totals['complete_sets']+=1
    payload={'note':'External URLs are not downloaded or verified by this audit. Missing means no URL; broken means a local reference is absent, too small or invalid.','totals':totals,'sets':rows}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# ZamexCards – afbeeldingen- en logo-eindcontrole','','Lokale bestanden worden op aanwezigheid en minimale grootte gecontroleerd. Externe links zijn niet op bereikbaarheid gecontroleerd.','','## Totaaloverzicht','']
    lines += [f'- {key}: {value}' for key,value in totals.items()]
    lines += ['','## Per set','','| Set | Logo | Kaarten lokaal | Ontbrekend | Extern (niet geverifieerd) | Lokale fouten |','|---|---|---:|---:|---:|---:|']
    for row in rows:
        name=str(row['name']).replace('|','/')
        lines.append(f"| {row['id']} – {name} | {row['logo_status']} | {row['local_cards']}/{row['total_cards']} | {len(row['missing_cards'])} | {len(row['external_unverified_cards'])} | {len(row['broken_cards'])} |")
    lines+=['','## Ontbrekende of ongeldige setlogo’s','']
    for row in rows:
        if row['logo_status']!='local':lines.append(f"- {row['id']} – {row['name']}: {row['logo_status']}")
    lines+=['','## Kaarten zonder lokale afbeelding (per set)','']
    for row in rows:
        if row['missing_cards'] or row['external_unverified_cards'] or row['broken_cards']:
            lines.append(f"### {row['id']} – {row['name']}")
            for label,key in [('Geen bronlink','missing_cards'),('Externe bronlink (niet geverifieerd)','external_unverified_cards'),('Ongeldig lokaal bestand','broken_cards')]:
                if row[key]:
                    lines.append(f"**{label} ({len(row[key])}):** "+', '.join(str(c['number'] or c['id']) for c in row[key]))
            lines.append('')
    REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('AUDIT TOTALS:',json.dumps(totals),flush=True)
    print('Detailed reports: data/image_audit.md and data/image_audit.json',flush=True)

if __name__=='__main__':main()
