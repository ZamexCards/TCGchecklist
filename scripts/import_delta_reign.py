#!/usr/bin/env python3
"""Import reviewed English Delta Reign artwork without cross-set substitutions.

Sources are pinned to the SHA-256 bytes reviewed in November 2026. A changed
remote file is rejected rather than silently importing a different printing.
"""
import concurrent.futures
import datetime
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / 'data/me06-english-image-sources.json'
SET_PATH = ROOT / 'data/sets/me06.json'
HEADERS = {'User-Agent': 'ZamexCardsChecklist/1.0', 'Referer': 'https://cardtracker.nl/'}
MAX_BYTES = 8_000_000

def main():
    sources = json.loads(SOURCE_PATH.read_text())
    payload = json.loads(SET_PATH.read_text())
    assert payload['set']['id'] == 'me06' and payload['set']['name'] == 'Delta Reign'
    cards = {c['number']: c for c in payload['cards']}
    rows = sources['cards']
    assert len(rows) == 141 and len({r['number'] for r in rows}) == 141
    assert set(cards) == {r['number'] for r in rows}
    # Validate every identity before writing any files.
    for row in rows:
        card = cards[row['number']]
        assert row['id'] == card['id'] and row['name'] == card['name'], row
        assert row['language'] == 'en' and row['setCode'] == 'DLR'
        assert row['source'].startswith('https://images.scrydex.com/pokemon/me6-')
        assert int(row['source'].split('/me6-')[1].split('/')[0]) == int(row['number'])
    def download(row):
        number = row['number']
        card = cards[number]
        local = card.get('images', {}).get('small', '')
        if local.startswith('./assets/'):
            existing = ROOT / local[2:]
            if existing.is_file():
                with Image.open(existing) as image: image.verify()
                return number, local, 'preserved'
        error = ''
        for attempt in range(3):
            try:
                request = urllib.request.Request(row['source'], headers=HEADERS)
                with urllib.request.urlopen(request, timeout=35) as response:
                    raw = response.read(MAX_BYTES + 1)
                assert 1000 < len(raw) <= MAX_BYTES, 'image size'
                assert hashlib.sha256(raw).hexdigest() == row['sha256'], 'source changed since English review'
                with Image.open(io.BytesIO(raw)) as image:
                    image.load()
                    assert image.size == (row['width'], row['height'])
                    assert image.width >= 245 and image.height >= 342
                    destination = ROOT / 'assets/sets/me06' / (number + '.png')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary = destination.with_suffix('.tmp.png')
                    image.save(temporary, format='PNG')
                with Image.open(temporary) as check: check.verify()
                temporary.replace(destination)
                return number, './assets/sets/me06/' + number + '.png', 'saved'
            except Exception as exc:
                error = str(exc)
                time.sleep(attempt + 1)
        return number, '', error
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(download, rows))
    # Fail closed: leave the catalogue untouched if any reviewed image fails.
    failed = [(n, status) for n, local, status in results if not local]
    if failed:
        raise RuntimeError('Delta Reign import incomplete: ' + repr(failed))
    for number, local, status in results:
        cards[number].setdefault('images', {})['small'] = local
        print(number, cards[number]['name'], status, flush=True)
    payload['updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    SET_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    report = {'set': 'me06', 'language': 'en', 'cards': len(results),
              'saved': sum(s == 'saved' for _, _, s in results),
              'preserved': sum(s == 'preserved' for _, _, s in results),
              'missing': 0, 'checked': payload['updated'],
              'sourceManifest': str(SOURCE_PATH.relative_to(ROOT))}
    (ROOT / 'data/me06-english-import-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)

if __name__ == '__main__':
    main()
