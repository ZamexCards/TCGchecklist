#!/usr/bin/env python3
"""Archive individually reviewed English variant scans; retain stable printing keys."""
import hashlib,json,pathlib
import enrich_catalogue as m
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 m.ROOT=ROOT
 reviews=m.read(ROOT/'data/imports/reviewed-variant-images.json')
 count=0
 for rule in reviews['images']:
  sid=m.safe(rule['setId']);path=ROOT/'data/sets'/(sid+'.json');payload=m.read(path)
  assert payload['set']['id']==sid and rule['language']=='en'
  cards=[c for c in payload['cards']if c['id']==rule['cardId']];assert len(cards)==1,rule['cardId'];c=cards[0]
  assert m.norm(c['name'])==m.norm(rule['name'])and m.num(c['number'])==m.num(rule['number'])
  ps=[p for p in c['printings']if p['key']==rule['variantKey']];assert len(ps)==1,rule['variantKey'];p=ps[0]
  original=p.get('_reviewedSourceFields')or p
  for key,value in rule.get('expected',{}).items():assert original.get(key)==value,(c['id'],key,original.get(key),value)
  name=m.file_number(c['number'])+'-reviewed-'+hashlib.sha256(p['key'].encode()).hexdigest()[:12]+'.webp'
  previous=p.get('imageAsset')or{}
  if previous.get('path')and m.local(previous['path']):assert hashlib.sha256(m.local(previous['path']).read_bytes()).hexdigest()==previous['sha256']
  asset=m.archive(rule['sourceUrl'],sid,name,'variant',{'cardId':c['id'],'number':c['number'],'name':c['name'],'language':'en','variantKey':p['key'],'sourcePage':rule['sourcePage'],'visualEvidence':rule['visualEvidence']},expected_source_sha=rule['sourceSha256'])
  assert asset and not asset.get('error'),asset
  p.setdefault('_reviewedSourceFields',{k:p.get(k)for k in ('type','foil','stamp','size','label')})
  overrides=rule.get('overrides',{});assert set(overrides)<=set(['stamp','label','foil','subtype','size','type'])
  if overrides:p['_reviewedOverrides']=overrides;p.update(overrides)
  p.update(images={'small':asset['path']},imageAsset=asset,imageStatus='catalogue_image',verification=rule['verification'],independentlyVisuallyReviewed=True,imagePresentation={'mode':'catalogue_image','referenceImage':c['images']['small'],'simulatedEffect':False})
  c['availableVariants']=[v['label']for v in c['printings']]
  c['dataQuality'].update(m.image_quality(c))
  rp=ROOT/'data/research/sets'/(sid+'.json');research=m.read(rp)
  research['issues']=[i for i in research['issues']if not(i.get('cardId')==c['id']and i.get('type')=='variant_image'and i.get('variantKey')==p['key'])]
  c['dataQuality']['openResearch']=sum(i.get('cardId')==c['id']for i in research['issues'])
  if 'research'in payload:payload['research']=[i for i in payload['research']if not(i.get('id')==c['id']and i.get('key')==p['key'])]
  if 'summary'in payload:
   payload['summary'].update(actualImages=sum(m.valid_image(v.get('images',{}).get('small',''))for x in payload['cards']for v in x['printings']),openImageResearch=sum(i.get('type')=='variant_image'for i in research['issues']))
  m.write(path,payload);m.write(rp,research);count+=1
  print('REVIEWED IMAGE',c['id'],p['label'],asset['path'],flush=True)
 m.exports(m.read(ROOT/'data/sets.json'))
 print('Reviewed English variant images applied:',count,flush=True)
if __name__=='__main__':main()
