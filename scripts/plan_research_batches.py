#!/usr/bin/env python3
"""Save bounded, reproducible work lists; ordinary reverses never enter them."""
import collections
import json
from pathlib import Path
import enrich_catalogue as m

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 25

def main():
    manifest = m.read(ROOT / 'data/sets.json')['sets']
    open_issues = m.read(ROOT / 'data/research/open.json')
    names = {s['id']: s['name'] for s in manifest}
    grouped = collections.defaultdict(list)
    excluded_reverse = 0
    seen = set()
    cards = {}
    for s in manifest:
        cards.update({c['id']: c for c in m.read(ROOT / 'data/sets' / (s['id'] + '.json'))['cards']})
    for issue in open_issues['issues']:
        if issue['type'] != 'variant_image':
            continue
        card = cards[issue['cardId']]
        printing = next(p for p in card['printings'] if p['key'] == issue['variantKey'])
        if m.ordinary_reverse(printing):
            excluded_reverse += 1
            continue
        key = (issue['cardId'], issue['variantKey'])
        assert key not in seen, key
        seen.add(key)
        grouped[issue['setId']].append(issue)
    priority = ['sv10.5b', 'sv10.5w', 'sv08.5']
    order = priority + [s['id'] for s in manifest if s['id'] not in priority]
    batches = []
    for sid in order:
        rows = sorted(grouped[sid], key=lambda i: (i['number'].zfill(8), i['variantKey']))
        for start in range(0, len(rows), LIMIT):
            batches.append({'id': f"{sid}-{start // LIMIT + 1:03d}",
                            'setId': sid, 'setName': names[sid],
                            'count': len(rows[start:start + LIMIT]),
                            'items': rows[start:start + LIMIT]})
    assert all(0 < b['count'] <= LIMIT for b in batches)
    assert sum(b['count'] for b in batches) == len(seen)
    metadata_groups = collections.defaultdict(list)
    for issue in open_issues['issues']:
        if issue['type'] != 'variant_image':
            metadata_groups[issue['type']].append(issue)
    metadata_batches = []
    for kind in sorted(metadata_groups):
        rows = sorted(metadata_groups[kind], key=lambda i: (i['setId'], i.get('cardId', '')))
        for start in range(0, len(rows), LIMIT):
            items = rows[start:start + LIMIT]
            metadata_batches.append({'id': f"metadata-{kind}-{start // LIMIT + 1:03d}",
                                     'type': kind, 'count': len(items), 'items': items})
    assert sum(b['count'] for b in metadata_batches) == sum(len(v) for v in metadata_groups.values())
    m.write(ROOT / 'data/research/batches.json', {
        'schemaVersion': '1.0', 'checked': m.now(), 'maxItemsPerBatch': LIMIT,
        'variantImagesRemaining': len(seen), 'batchCount': len(batches),
        'metadataBatchCount': len(metadata_batches),
        'totalPendingBatches': len(batches) + len(metadata_batches),
        'ordinaryReverseExcluded': excluded_reverse,
        'otherResearchByType': dict(collections.Counter(i['type'] for i in open_issues['issues'] if i['type'] != 'variant_image')),
        'completionRule': 'Every item has either a verified matching image committed and published, or an explicit searched-but-unavailable result with sources. Unavailable is not complete data.',
        'batches': batches, 'metadataBatches': metadata_batches})
    print('RESEARCH BATCHES', len(batches), 'groups,', len(seen), 'special images; max', LIMIT, 'per group')

if __name__ == '__main__':
    main()
