"""Download the raw source data into data/raw/ so the whole pipeline can be rebuilt from nothing.

  DataMeet Census 2011 district shapefile : checked against the SHA-256 recorded in the site manifest
  Wikipedia "List of districts of Rajasthan": pinned to the revision the data was built from, so the result never changes silently
                                              (pass --latest to fetch the newest revision instead, then re-run the ingest and read the diff)

Run:  .venv/Scripts/python tools/fetch_raw.py [--latest] [--out DIR]
Uses only the standard library.
"""
import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED_REVISION = 1381020334                      # revision of 2026-10-19 used for districts_current.json
UA = 'RajAtlas-data-build/0.1 (student project)'
DATAMEET = 'https://raw.githubusercontent.com/datameet/maps/master/Districts/Census_2011/2011_Dist.'


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--latest', action='store_true', help='fetch the newest Wikipedia revision instead of the pinned one')
    ap.add_argument('--out', default=str(ROOT / 'data' / 'raw'))
    a = ap.parse_args()
    out = Path(a.out)

    shp_dir = out / 'datameet-census2011'
    shp_dir.mkdir(parents=True, exist_ok=True)
    for ext in ('shp', 'shx', 'dbf', 'prj'):
        (shp_dir / f'2011_Dist.{ext}').write_bytes(get(DATAMEET + ext))
    digest = hashlib.sha256((shp_dir / '2011_Dist.shp').read_bytes()).hexdigest()
    manifest = ROOT / 'site' / 'assets' / 'data' / 'manifest.json'
    status = 'no manifest to compare with'
    if manifest.exists():
        expected = json.loads(manifest.read_text(encoding='utf-8'))['layers']['districts-2011']['source_sha256']
        status = 'MATCHES the manifest' if digest == expected else 'DIFFERS from the manifest: the upstream file has changed, rebuild and re-validate'
    print(f'shapefile sha256 {digest[:16]}...  {status}')

    q = {'action': 'query', 'prop': 'revisions', 'rvprop': 'ids|timestamp|content', 'rvslots': 'main', 'format': 'json', 'formatversion': '2'}
    if a.latest:
        q['titles'] = 'List_of_districts_of_Rajasthan'
    else:
        q['revids'] = str(PINNED_REVISION)
    wiki_dir = out / 'wikipedia-districts'
    wiki_dir.mkdir(parents=True, exist_ok=True)
    body = get('https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode(q))
    (wiki_dir / 'response.json').write_bytes(body)
    rev = json.loads(body)['query']['pages'][0]['revisions'][0]
    print(f"wikipedia revision {rev['revid']} ({rev['timestamp']}), {len(rev['slots']['main']['content'])} characters")
    return 0


if __name__ == '__main__':
    sys.exit(main())
