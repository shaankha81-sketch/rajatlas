"""Independent checks on the published boundary files. Reads ONLY site/assets/data/*, never the build code.
Run:  .venv/Scripts/python tools/validate_boundaries.py     (exit code 1 if any check fails)
"""
import json
import sys
from pathlib import Path

import shapely
from shapely.geometry import shape

DATA = Path(__file__).resolve().parents[1] / 'site' / 'assets' / 'data'
CURATED = Path(__file__).resolve().parents[1] / 'data' / 'curated'

# Rajasthan total area, Census of India 2011 as recalled by the author: verify against the Primary Census Abstract.
EXPECTED_TOTAL_KM2, AREA_TOLERANCE = 342239, 0.005
# Districts that touch Pakistan (stated by the Border Security Force and in standard references).
PAKISTAN_BORDER = {'barmer', 'bikaner', 'jaisalmer', 'sri-ganganagar'}

failures = []


def check(ok, message):
    print(('PASS  ' if ok else 'FAIL  ') + message)
    if not ok:
        failures.append(message)


def main():
    d = json.loads((DATA / 'districts-2011.geojson').read_text(encoding='utf-8'))['features']
    c = json.loads((DATA / 'context-states.geojson').read_text(encoding='utf-8'))['features']
    props = {f['properties']['id']: f['properties'] for f in d}

    check(len(d) == 33, f'33 districts (found {len(d)})')
    check(len(props) == 33, 'district ids are unique')
    check(all(all(p['name'].get(k) for k in ('en', 'hi', 'ur')) for p in props.values()), 'every district has an en, hi and ur name')
    check(all(shape(f['geometry']).is_valid for f in d + c), 'all drawn geometries are valid')

    total = sum(p['area_km2'] for p in props.values())
    off = abs(total - EXPECTED_TOTAL_KM2) / EXPECTED_TOTAL_KM2
    check(off < AREA_TOLERANCE, f'total area {total:,.0f} km2 is within {AREA_TOLERANCE:.1%} of {EXPECTED_TOTAL_KM2:,} (off by {off:.2%})')

    # shapes drawn on screen must still enclose the measured area (simplification must not shrink districts)
    from pyproj import Geod
    geod = Geod(ellps='WGS84')
    worst = max(abs(abs(geod.geometry_area_perimeter(shape(f['geometry']))[0]) / 1e6 - f['properties']['area_km2']) / f['properties']['area_km2'] for f in d)
    check(worst < 0.02, f'drawn shape area is within 2% of the measured area for every district (worst {worst:.2%})')

    asym = [(a, b) for a, p in props.items() for b in p['neighbours'] if a not in props[b]['neighbours']]
    check(not asym, f'neighbour lists are symmetric ({len(asym)} mismatches)')
    check(all(p['neighbours'] for p in props.values()), 'every district has at least one neighbouring district')

    intl = {k for k, p in props.items() if p['intl_border_km'] > 0}
    check(intl == PAKISTAN_BORDER, f'international border only on {sorted(PAKISTAN_BORDER)} (found {sorted(intl)})')
    check(all(0 < p['compactness'] <= 1 for p in props.values()), 'compactness is between 0 and 1')
    check(all(p['bbox'][0] <= p['centroid'][0] <= p['bbox'][2] and p['bbox'][1] <= p['centroid'][1] <= p['bbox'][3] for p in props.values()),
          'every centroid lies within its district bounding box')

    in_box = all(p['bbox'][0] <= p['label_point'][0] <= p['bbox'][2] and p['bbox'][1] <= p['label_point'][1] <= p['bbox'][3] for p in props.values())
    inside = all(shape(f['geometry']).contains(shapely.Point(f['properties']['label_point'])) for f in d)
    check(in_box and inside, 'label points lie inside their own district')

    # --- today's district list (Wikipedia, ingested separately) ---
    man = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    cur = man['current_list']
    divisions = {name.lower().replace(' ', '-') for name in cur['divisions']}      # division names equal district ids once lower-cased
    check(len(divisions) == 7 and cur['counts']['total'] == 41, f"today's list has 7 divisions and 41 districts ({len(divisions)}, {cur['counts']['total']})")
    check(all(p['division'] in divisions and p['division'] in props for p in props.values()), 'every district has a division, and each division is named after a district')
    check(cur['counts']['continuing'] == 33 and len(cur['new_districts']) == cur['counts']['new_since_2011'] == 8, 'the 33 districts of the map plus 8 new ones make the 41')
    check(not ({n['id'] for n in cur['new_districts']} & set(props)), 'new districts are not on the 2011 map')
    check(all(n['division_id'] in divisions for n in cur['new_districts']), 'every new district sits in a known division')

    # warning only: do the list's claimed areas match the areas measured from the boundaries?
    claimed = json.loads((CURATED / 'districts_current.json').read_text(encoding='utf-8'))['districts']
    off = []
    for c in claimed:
        if c['id'] in props and c['area_km2_claimed']:
            rel = (c['area_km2_claimed'] - props[c['id']]['area_km2']) / props[c['id']]['area_km2']
            if abs(rel) > 0.02:
                off.append(f"{c['name']['en']} {rel:+.1%}")
    print(f"INFO  claimed area differs by more than 2% from the measured 2011 area for {len(off)} of 33 districts: {', '.join(off) or 'none'}")

    print(f'\n{len(failures)} failed' if failures else '\nall checks passed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
