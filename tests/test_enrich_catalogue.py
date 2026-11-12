import importlib.util, pathlib, unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('enrich',pathlib.Path(__file__).parents[1]/'scripts/enrich_catalogue.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CatalogueTests(unittest.TestCase):
 def setUp(self):
  self.old={'id':'base1-1','name':'Alakazam','number':'1','supertype':'Pokemon','images':{'small':'./assets/sets/base1/1.png'},'availableVariants':['Base']}
  self.d={'id':'base1-1','name':'Alakazam','localId':'1','set':{'id':'base1'},'category':'Pokemon','hp':80,'attacks':[{'name':'Confuse Ray','effect':'Flip a coin.'}],'variants_detailed':[{'type':'holo','subtype':'unlimited','size':'standard'},{'type':'holo','subtype':'shadowless','stamp':['1st-edition'],'size':'standard'}]}
 def test_identity_prevents_cross_set_and_wrong_number(self):
  for bad in ({**self.d,'set':{'id':'base2'}},{**self.d,'localId':'2'},{**self.d,'name':'Alakazam ex'}):
   with self.assertRaisesRegex(ValueError,'identity_mismatch'):m.merge(self.old,bad,'base1')
  self.assertNotEqual(m.norm('Nidoran♀'),m.norm('Nidoran♂'))
 def test_details_and_editions_persist(self):
  c=m.merge(self.old,self.d,'base1');self.assertEqual(c['hp'],80);self.assertEqual(c['attacks'],self.d['attacks']);self.assertEqual(len(c['printings']),2);self.assertNotEqual(c['printings'][0]['key'],c['printings'][1]['key']);self.assertIn('1st Edition',c['printings'][1]['label']);self.assertFalse(c['printings'][1]['images']['small'])
 def test_reviewed_reverse_survives_incomplete_upstream(self):
  o={**self.old,'_variantSource':'reviewed','availableVariants':['Normal','Reverse holo']};d={**self.d,'variants_detailed':[{'type':'normal','size':'standard'}]};c=m.merge(o,d,'base1');self.assertTrue(any(p['type']=='reverse'for p in c['printings']))
 def test_existing_reviewed_picture_survives_refresh(self):
  o={**self.old,'_enrichedSource':'primary','printings':[{'type':'holo','subtype':'shadowless','stamp':['1st-edition'],'size':'standard','key':'my-key','label':'1st Edition reviewed','images':{'small':'./assets/verified.png'},'verification':'reviewed'}]};c=m.merge(o,self.d,'base1');p=next(p for p in c['printings']if p['key']=='my-key');self.assertEqual(p['images']['small'],'./assets/verified.png')
 def test_secondary_requires_matching_set_and_card(self):
  info={'name':'Base Set','printedTotal':102};self.assertIsNotNone(m.secondary_set(info,[{'name':'Base','printedTotal':102,'id':'base1'}]));self.assertIsNone(m.secondary_set(info,[{'name':'Base','printedTotal':130,'id':'base4'}]));c=m.supplement(dict(self.old),{'id':'x','name':'Alakazam','number':'2','artist':'Wrong'},'source');self.assertNotIn('illustrator',c)
 def test_promo_counts_can_grow_with_verified_series_and_id(self):
  a={'id':'svp','name':'SVP Black Star Promos','series':'Scarlet & Violet','printedTotal':500};b={'id':'svp','name':'Scarlet & Violet Black Star Promos','series':'Scarlet & Violet','printedTotal':1};self.assertEqual(m.secondary_set(a,[b]),b)
 def test_punctuation_card_numbers_have_unique_safe_file_names(self):
  self.assertNotEqual(m.file_number('!'),m.file_number('%3F'));m.safe(m.file_number('!'));m.safe(m.file_number('%3F'))
 def test_temporary_source_failure_preserves_complete_verified_snapshot(self):
  old={**self.old,**{k:v for k,v in self.d.items()if k not in ('localId','set')}}
  secondary={('1',m.norm('Alakazam')):{'id':'base1-1','name':'Alakazam','number':'1','hp':'80'}}
  with patch.object(m,'get',side_effect=OSError('HTTP 503')),patch.object(m,'valid_image',side_effect=lambda p:bool(p)):
   c,issues=m.process_card(old,{'id':'base1','releaseDate':'1999-01-09'},secondary,'secondary-source')
  self.assertEqual(c['hp'],80);self.assertEqual(len(c['printings']),2);self.assertTrue(c['dataQuality']['detailsArchived']);self.assertTrue(c['provenance']['primary']['recoveredFromStoredSnapshot']);self.assertFalse(any(i['type']=='card_detail'for i in issues))
 def test_reviewed_stamp_correction_and_image_evidence_survive_refresh(self):
  old={**self.old,'_enrichedSource':'primary','printings':[{'type':'holo','stamp':['pokemon-day-2025'],'size':'standard','variantId':'same-print','key':'stable-old-key','label':'Holo · Pokémon Day 2025','images':{'small':'./assets/reviewed.webp'},'_reviewedOverrides':{'stamp':['pokemon-day-2025'],'label':'Holo · Pokémon Day 2025'},'_reviewedSourceFields':{'stamp':['30th-pokeday']},'imageAsset':{'sha256':'reviewed-hash'},'verification':'identity_and_image_reviewed','independentlyVisuallyReviewed':True}]}
  detail={**self.d,'variants_detailed':[{'type':'holo','stamp':['30th-pokeday'],'size':'standard','variantId':'same-print'}]};c=m.merge(old,detail,'base1');p=next(p for p in c['printings']if p['key']=='stable-old-key');self.assertEqual(p['stamp'],['pokemon-day-2025']);self.assertEqual(p['imageAsset']['sha256'],'reviewed-hash');self.assertTrue(p['independentlyVisuallyReviewed'])
 def test_ordinary_reverse_uses_overlay_without_research_or_extra_download(self):
  d={**self.d,'variants_detailed':[{'type':'normal','size':'standard'},{'type':'reverse','size':'standard'}]}
  with patch.object(m,'get',return_value=d),patch.object(m,'valid_image',side_effect=lambda p:bool(p)),patch.object(m,'archive')as archive:
   c,issues=m.process_card(self.old,{'id':'base1','releaseDate':'1999-01-09'},{},'')
  reverse=next(p for p in c['printings']if p['type']=='reverse');self.assertEqual(reverse['imagePresentation']['mode'],'reverse_overlay');self.assertFalse(any(i['type']=='variant_image'for i in issues));archive.assert_not_called();self.assertEqual(c['dataQuality']['ordinaryReverseOverlays'],1)
 def test_special_reverse_stamps_and_patterns_still_need_their_own_image(self):
  self.assertFalse(m.ordinary_reverse({'type':'reverse','stamp':['set-logo']}));self.assertFalse(m.ordinary_reverse({'type':'reverse','foil':'pokeball'}));self.assertFalse(m.ordinary_reverse({'type':'reverse','size':'jumbo'}))
 def test_no_fabricated_images_for_missing_reverse(self):
  d={**self.d,'variants_detailed':[{'type':'normal','size':'standard'},{'type':'reverse','size':'standard'}]}
  with patch.object(m,'get',return_value=d),patch.object(m,'valid_image',side_effect=lambda p:bool(p)),patch.object(m,'archive')as a:
   c,issues=m.process_card(self.old,{'id':'base1','releaseDate':'1999-01-09'}, {},'');self.assertFalse(c['printings'][1]['images']['small']);self.assertFalse(any(i['type']=='variant_image'for i in issues));a.assert_not_called()
if __name__=='__main__':unittest.main()
