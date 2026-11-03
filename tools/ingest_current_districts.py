"""Ingest the CURRENT district list of Rajasthan from the Wikipedia article "List of districts of Rajasthan".

Input : data/raw/wikipedia-districts/response.json   (MediaWiki API response: wikitext + revision id + timestamp)
        data/curated/district_names.json              (trilingual names of the 2011 districts and of the new ones)
Output: data/curated/districts_current.json

What is trusted and what is not
  * The LIST of districts, their DIVISIONS and the official district websites are used. The page states them twice
    (main table and a separate divisions table), and this script requires the two to agree.
  * The AREA and POPULATION columns are kept only as "claimed": the page does not name a source or year for them and
    contradicts itself (see data_quality). The site does not display them.
Run:  .venv/Scripts/python tools/ingest_current_districts.py     (exit code 1 if a structural check fails)
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'wikipedia-districts' / 'response.json'
NAMES = ROOT / 'data' / 'curated' / 'district_names.json'
OUT = ROOT / 'data' / 'curated' / 'districts_current.json'
PAGE_URL = 'https://en.wikipedia.org/wiki/List_of_districts_of_Rajasthan'

problems = []


def need(ok, message):
    if not ok:
        problems.append(message)
        print('FAIL  ' + message)
    return ok


def link_label(cell):
    """[[Target|Label]] -> Label, [[Label]] -> Label."""
    m = re.search(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', cell)
    return (m.group(2) or m.group(1)).strip() if m else cell.strip()


def to_int(cell):
    digits = re.sub(r'[^\d]', '', cell)
    return int(digits) if digits else None


def parse_main_table(text):
    start = text.index('{| class="wikitable sortable plainrowheaders"')
    table = text[start:text.index('\n|}', start)]
    rows = []
    for chunk in table.split('\n|-\n')[1:]:
        chunk = chunk.replace('||', '\n|')
        cells = [c[1:].strip() for c in chunk.split('\n') if c.startswith('|') and not c.startswith('|-')]
        need(len(cells) == 6, f'main table row has {len(cells)} cells, expected 6: {cells[:2]}')
        if len(cells) != 6:
            continue
        site = re.search(r'\[(https?://\S+)', cells[2])
        rows.append({
            'serial': to_int(cells[0]), 'name': link_label(cells[1]), 'website': site.group(1) if site else None,
            'area_km2_claimed': to_int(cells[3]), 'population_claimed': to_int(cells[4]), 'division': link_label(cells[5]),
        })
    return rows


def parse_division_table(text):
    start = text.index('== Division ==')
    table = text[text.index('{|', start):]
    table = table[:table.index('\n|}')]
    names = [link_label(l[1:]).replace(' Division', '').replace(' division', '') for l in table.split('\n') if l.startswith('![[')]
    body = table[table.index('vertical-align: top;"') :].split('\n', 1)[1]
    columns = re.split(r'\n\|\n', '\n' + body.strip('\n').lstrip('|') if body.startswith('|') else body)
    members = []
    for col in columns:
        members.append([link_label(l[2:]) for l in col.split('\n') if l.startswith('# ')])
    members = [m for m in members if m]
    return dict(zip(names, members)) if need(len(names) == len(members), f'divisions table: {len(names)} headings but {len(members)} columns') else {}


def parse_infobox(text):
    box = {}
    m = re.search(r'\[\[[^\]|]+\|\s*([^\]]+?)\s*\]\]\s*[–-]\s*([\d,]+)\s*\(lowest\)', text)
    if m: box['population_lowest'] = (m.group(1), to_int(m.group(2)))
    m = re.search(r'\[\[[^\]|]+\|\s*([^\]]+?)\s*\]\]\s*[–-]\s*([\d,]+)\s*\(highest\)', text)
    if m: box['population_highest'] = (m.group(1), to_int(m.group(2)))
    for kind in ('smallest', 'largest'):
        m = re.search(r'\[\[[^\]|]+\|\s*([^\]]+?)\s*\]\]\s*[–-]\s*\{\{Convert\|([\d,]+)\|km2[^}]*\}\}\s*\(' + kind + r'\)', text)
        if m: box['area_' + kind] = (m.group(1), to_int(m.group(2)))
    return box


def main():
    api = json.loads(RAW.read_text(encoding='utf-8'))
    rev = api['query']['pages'][0]['revisions'][0]
    text = rev['slots']['main']['content']
    names = json.loads(NAMES.read_text(encoding='utf-8'))
    old = {v.get('source_spelling', k): v for k, v in names['districts'].items()}          # 2011 layer, keyed by the list's spelling
    old_by_en = {v['en']: v for v in names['districts'].values()}
    new = names['new_districts_since_2011']

    rows = parse_main_table(text)
    divisions = parse_division_table(text)
    infobox = parse_infobox(text)

    need(len(rows) == 41, f'41 districts in the main table (found {len(rows)})')
    need([r['serial'] for r in rows] == list(range(1, len(rows) + 1)), 'serial numbers run 1..n without gaps')
    need(len({r['name'] for r in rows}) == len(rows), 'district names are unique')
    need(len(divisions) == 7, f'7 divisions in the divisions table (found {len(divisions)})')
    need(sum(len(v) for v in divisions.values()) == len(rows), 'divisions table lists every district exactly once')

    # the main table and the divisions table must agree
    in_div = {d: div for div, members in divisions.items() for d in members}
    disagree = [(r['name'], r['division'], in_div.get(r['name'])) for r in rows if in_div.get(r['name']) != r['division']]
    need(not disagree, f'division column agrees with the divisions table (disagreements: {disagree})')

    district_names = {r['name'] for r in rows}
    need(set(divisions) <= district_names, f'every division is named after a district (division names: {sorted(divisions)})')

    # which districts continue from the 2011 map and which are new
    out = []
    for r in rows:
        n = r['name']
        if n in old_by_en:
            meta, status = old_by_en[n], 'continuing'
        elif n in old:
            meta, status = old[n], 'continuing'
        elif n in new:
            meta, status = new[n], 'new_since_2011'
        else:
            need(False, f'no trilingual name for "{n}": add it to district_names.json')
            continue
        out.append({'id': meta['id'], 'name': {k: meta[k] for k in ('en', 'hi', 'ur')}, 'status': status,
                    'division_id': old_by_en[r['division']]['id'] if r['division'] in old_by_en else None,
                    'serial': r['serial'], 'district_website': r['website'],
                    'area_km2_claimed': r['area_km2_claimed'], 'population_claimed': r['population_claimed']})
    continuing = {o['id'] for o in out if o['status'] == 'continuing'}
    need(continuing == {v['id'] for v in names['districts'].values()}, 'every district of the 2011 map is in the current list')
    need(all(o['division_id'] for o in out), 'every division resolves to a district of the 2011 map')

    # --- data quality: what the page claims that does not hold together (reported, never hidden) ---
    dq = []
    by_area, by_pop = {}, {}
    for r in rows:
        by_area.setdefault(r['area_km2_claimed'], []).append(r['name'])
        by_pop.setdefault(r['population_claimed'], []).append(r['name'])
    for v, ns in by_area.items():
        if len(ns) > 1: dq.append(f'identical claimed area {v:,} km2 for {" and ".join(ns)}')
    for v, ns in by_pop.items():
        if len(ns) > 1: dq.append(f'identical claimed population {v:,} for {" and ".join(ns)}')
    areas = {r['name']: r['area_km2_claimed'] for r in rows}
    pops = {r['name']: r['population_claimed'] for r in rows}
    for key, fn, table in (('area_smallest', min, areas), ('area_largest', max, areas), ('population_lowest', min, pops), ('population_highest', max, pops)):
        if key in infobox:
            who, val = infobox[key]
            tw = fn(table, key=table.get)
            if tw != who or table.get(who) != val:
                dq.append(f'infobox says {key.replace("_", " ")} is {who} ({val:,}) but the table gives {tw} ({table[tw]:,}) and {who} ({table.get(who, 0):,})')
    dq.append('the page names no source or census year for the area and population columns')

    result = {
        'source': {
            'title': 'List of districts of Rajasthan', 'url': PAGE_URL, 'publisher': 'Wikipedia', 'licence': 'CC BY-SA 4.0',
            'revision_id': rev['revid'], 'revision_timestamp': rev['timestamp'],
            'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'list_date_stated_by_page': '30 December 2024',
            'stated_counts': {'districts': 41, 'divisions': 7},
        },
        'trust': {
            'used': ['district list', 'division of each district', 'official district websites'],
            'kept_but_not_used': ['area_km2_claimed', 'population_claimed'],
            'reason': 'no source or year named; internal contradictions (see data_quality)',
        },
        'data_quality': dq,
        'divisions': {d: sorted(m) for d, m in divisions.items()},
        'districts': out,
        'counts': {'total': len(out), 'continuing': len(continuing), 'new_since_2011': len(out) - len(continuing)},
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{len(out)} districts ({len(continuing)} from the 2011 map, {len(out) - len(continuing)} new), {len(divisions)} divisions")
    print('data_quality:'); [print('  - ' + x) for x in dq]
    print('\nFAILED' if problems else '\nstructural checks passed')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
