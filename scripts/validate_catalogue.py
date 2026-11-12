#!/usr/bin/env python3
"""Validate exported contracts and genuine archived files; allow explicit gaps."""
import gzip,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
 manifest=load('data/sets.json');seen=set();total=0;printing_count=0
 for s in manifest['sets']:
  p=load('data/sets/'+s['id']+'.json');assert p['set']['id']==s['id'],s['id']
  assert p['language']=='en'and p['schemaVersion']=='2.0',s['id']
  for c in p['cards']:
   assert c['id']not in seen,c['id'];seen.add(c['id']);total+=1
   assert c['language']=='en'and c['setId']==s['id']and c['name']and str(c['number']),c['id']
   ps=c['printings'];assert ps and len({v['key']for v in ps})==len(ps),c['id'];printing_count+=len(ps)
   assert c['availableVariants']==[v['label']for v in ps],c['id']
   assert c['dataQuality']['printings']==len(ps),c['id']
   if c['dataQuality']['detailsArchived']:assert c.get('_enrichedSource'),c['id']
   for image in [c['images'].get('small','')]+[v['images'].get('small','')for v in ps]:
    if image.startswith('./'):
     path=(ROOT/image[2:]).resolve();assert path.is_relative_to((ROOT/'assets').resolve())and path.is_file(),(c['id'],image)
 quality=load('data/catalogue-quality.json');assert quality['totals']['cards']==total;assert quality['totals']['printings']==printing_count
 issues=load('data/research/open.json');assert issues['total']==len(issues['issues'])==quality['totals']['openResearch']
 index=load('data/cards-index.json');assert {c['id']for c in index['cards']}==seen
 with gzip.open(ROOT/'data/exports/pokemon-en.json.gz','rt',encoding='utf-8')as f:bulk=json.load(f)
 assert {c['id']for c in bulk['cards']}==seen
 assets=load('data/image-assets.json')['assets']
 for path,record in assets.items():
  body=(ROOT/path[2:]).read_bytes();assert len(body)==record['bytes']and hashlib.sha256(body).hexdigest()==record['sha256'],path
 print('VALIDATED',len(manifest['sets']),'sets,',total,'cards,',printing_count,'printings,',len(assets),'archived image files; open source gaps:',issues['total'])
if __name__=='__main__':main()
