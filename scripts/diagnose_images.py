#!/usr/bin/env python3
"""Prioritised, reproducible remaining-image investigation from the full audit."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'data/image_audit.json').read_text(encoding='utf-8'))
out=['# Resterende afbeeldingen: gerichte diagnose','','Geen afbeeldingsbron wordt op basis van een gelijkende kaartnaam aangenomen. Een ontbrekende bronlink vereist een gecontroleerde set- en kaart-ID-koppeling.','','| Set | Categorie | Geen bronlink | Extern | Logo | Vervolg |','|---|---|---:|---:|---|---|']
def category(s):
    i=s['id'].lower();n=s['name'].lower()
    if i.startswith('tk-'):return 'Trainer Kit'
    if 'promo' in n or i in ('mep','svp','swshp','smp','xyp','bwp','hgssp','p-a'):return 'Promoties'
    if 'mcdonald' in n:return 'McDonald’s'
    if 'energy' in n:return 'Energy'
    if 'classic collection' in n:return 'Classic Collection'
    if 'battle' in n:return 'Battle-product'
    if 'pocket' in n or i.startswith('b2'):return 'Pocket'
    return 'Overig'
for s in sorted(a['sets'],key=lambda s:(-len(s['missing_cards']),s['id'])):
    missing=len(s['missing_cards']);external=len(s['external_unverified_cards'])
    if not(missing or external or s['logo_status']!='local'):continue
    cat=category(s)
    action='Controleer afzonderlijke set-ID en kaartnummer bij tweede bron' if missing else 'Controleer externe afbeeldingslink'
    if not missing and not external:action='Zoek en verifieer uitsluitend setlogo'
    out.append(f"| {s['id']} – {s['name'].replace('|','/')} | {cat} | {missing} | {external} | {s['logo_status']} | {action} |")
out+=['','## Prioriteit','','1. Sets met veel ontbrekende kaartafbeeldingen eerst; controleer of het een afwijkend product of aparte kaartnummering betreft.','2. Trainer Kits en speciale collecties niet automatisch aan gewone uitbreidingssets koppelen: afbeeldingen kunnen anders verkeerd worden toegewezen.','3. Logo-only sets los afhandelen; dit vereist geen herdownload van kaarten.','4. Externe afbeeldingslinks afzonderlijk controleren voordat ze als lokaal afgerond worden aangemerkt.','','Bron: data/image_audit.json. Dit is een diagnose, geen claim dat de ontbrekende afbeeldingen al beschikbaar zijn.']
p=ROOT/'data/image_diagnosis.md';p.write_text('\n'.join(out)+'\n',encoding='utf-8')
print('Diagnosis:',len(out),'lines, output:',p)

# Export the exact missing-card queue for source-specific recovery.
import csv
queue=ROOT/'data'/'missing_image_queue.csv'
with queue.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['set_id','set_name','card_id','card_number','card_name','status','verified_source_url','review'])
    for row in a['sets']:
        for key,status in [('missing_cards','missing'),('external_unverified_cards','external_unverified')]:
            for c in row[key]:
                w.writerow([row['id'],row['name'],c['id'],c['number'],c['name'],status,'',''])
print('Per-card image queue:',queue)
