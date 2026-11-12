import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'scripts'))
import plan_research_batches as planner


class ResearchBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.patch = patch.object(planner, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.write('data/sets.json', {'sets': [{'id': 'sv10.5b', 'name': 'Black Bolt'}]})
        cards = [{'id': cid, 'printings': [{'key': 'same-print-key', 'type': 'reverse',
                                          'foil': 'masterball', 'size': 'standard'}]}
                 for cid in ['card-a', 'card-b', 'card-c']]
        self.write('data/sets/sv10.5b.json', {'cards': cards})
        self.issues = [{'setId': 'sv10.5b', 'cardId': c['id'], 'number': str(i),
                        'name': c['id'], 'type': 'variant_image', 'variantKey': 'same-print-key'}
                       for i, c in enumerate(cards)]
        self.write('data/research/open.json', {'issues': self.issues})
        self.write('data/research/completed/part-004.json', {
            'part': 4, 'checked': '2026-11-12', 'items': [
                {'cardId': 'card-a', 'variantKey': 'same-print-key',
                 'outcome': 'searched_no_verified_image',
                 'retryPolicy': 'on_user_request_or_new_source', 'reason': 'Only shop logo'},
                {'cardId': 'card-b', 'variantKey': 'same-print-key',
                 'outcome': 'verified_image_found'}]})

    def write(self, path, value):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(value))

    def result(self):
        planner.main()
        return json.loads((self.root / 'data/research/batches.json').read_text())

    def test_unavailable_stays_missing_but_does_not_repeat_in_fresh_queue(self):
        result = self.result()
        self.assertEqual(result['variantImagesRemaining'], 3)
        self.assertEqual(result['variantImagesToSearch'], 2)
        self.assertEqual(result['reviewedUnavailableImages'], 1)
        self.assertEqual({i['cardId'] for b in result['batches'] for i in b['items']},
                         {'card-b', 'card-c'})
        self.assertEqual(json.loads((self.root / 'data/research/open.json').read_text())['issues'],
                         self.issues)

    def test_resolved_issue_ignores_old_unavailable_record(self):
        self.write('data/research/open.json', {'issues': self.issues[1:]})
        result = self.result()
        self.assertEqual(result['variantImagesRemaining'], 2)
        self.assertEqual(result['reviewedUnavailableImages'], 0)
        self.assertEqual(result['variantImagesToSearch'], 2)


if __name__ == '__main__':
    unittest.main()
