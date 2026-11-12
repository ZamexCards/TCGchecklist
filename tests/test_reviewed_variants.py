import hashlib,importlib.util,io,pathlib,sys,tempfile,unittest
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'scripts'))
import enrich_catalogue as m
import import_reviewed_variants as importer
class FrozenSourceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=pathlib.Path(self.temp.name)
  self.addCleanup(patch.stopall);patch.object(m,'ROOT',self.root).start()
  b=io.BytesIO();Image.effect_noise((250,350),35).convert('RGB').save(b,'PNG');self.body=b.getvalue();self.sha=hashlib.sha256(self.body).hexdigest()
  self.path=self.root/'assets/reviewed-sources/card.png';self.path.parent.mkdir(parents=True);self.path.write_bytes(self.body)
  self.rule={'sourcePath':'./assets/reviewed-sources/card.png','sourceSha256':self.sha}
 def test_offline_import_uses_frozen_bytes(self):
  with patch.object(m,'get',side_effect=AssertionError('network forbidden')):
   a=m.archive('https://example.com/card','test','card.webp','variant',{},expected_source_sha=self.sha,source_bytes=importer.frozen_source(self.rule))
  self.assertNotIn('error',a);self.assertEqual(a['sourceSha256'],self.sha);self.assertTrue(m.valid_image(a['path']))
 def test_changed_source_is_rejected(self):
  self.path.write_bytes(self.body+b'changed')
  with self.assertRaisesRegex(ValueError,'reviewed_source_image_changed'):importer.frozen_source(self.rule)
 def test_missing_source_cannot_fall_back_to_network(self):
  self.path.unlink()
  with self.assertRaisesRegex(ValueError,'missing_reviewed_source'):importer.frozen_source(self.rule)
 def test_source_cannot_escape_asset_directory(self):
  with self.assertRaisesRegex(ValueError,'missing_reviewed_source'):importer.frozen_source({**self.rule,'sourcePath':'./assets/../../outside.png'})
 def test_archive_checks_supplied_hash_even_when_resuming(self):
  m.archive('https://example.com/card','test','card.webp','variant',{},expected_source_sha=self.sha,source_bytes=self.body)
  a=m.archive('https://example.com/card','test','card.webp','variant',{},expected_source_sha=self.sha,source_bytes=self.body+b'changed')
  self.assertIn('reviewed_source_image_changed',a['error'])
if __name__=='__main__':unittest.main()
