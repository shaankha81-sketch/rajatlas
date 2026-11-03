"""Build the Rajasthan boundary layers for the site (Phase 1: Census 2011 districts).

Input : data/raw/datameet-census2011/2011_Dist.*   (DataMeet, CC BY 2.5 India)
        data/curated/district_names.json            (display names in en/hi/ur)
        data/curated/districts_current.json         (today's 41-district list; run ingest_current_districts.py first)
Output: site/assets/data/districts-2011.geojson     (33 districts, simplified for the screen)
        site/assets/data/context-states.geojson     (the 5 neighbouring states, same simplification)
        site/assets/data/manifest.json              (sources, licence, versions, checks)

Measurements (area, perimeter, adjacency, border lengths) are taken from the ORIGINAL, unsimplified
geometry. Only the drawn shapes are simplified. Run:  .venv/Scripts/python tools/build_boundaries.py
"""
import datetime
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pyproj
import shapefile
import shapely
from shapely.geometry import box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'datameet-census2011' / '2011_Dist'
NAMES = ROOT / 'data' / 'curated' / 'district_names.json'
CURRENT = ROOT / 'data' / 'curated' / 'districts_current.json'
OUT = ROOT / 'site' / 'assets' / 'data'

STATE = 'Rajasthan'
NEIGHBOUR_STATES = ['Punjab', 'Haryana', 'Uttar Pradesh', 'Madhya Pradesh', 'Gujarat']
SIMPLIFY_DEG = 0.006        # about 650 m; keeps shared borders identical between districts
SNAP_DEG = 0.003            # two boundaries closer than this (about 330 m) count as the same border
MIN_SHARED_KM = 3.0         # touching at a corner is not "adjacent"
MIN_INTL_STRETCH_KM = 20.0  # shorter leftovers are mismatches between neighbouring outlines, not real borders
DECIMALS = 4                # coordinates rounded to about 11 m
CONTEXT_MARGIN_DEG = 0.8    # neighbouring states are kept only this far (degrees) beyond Rajasthan's extent

GEOD = pyproj.Geod(ellps='WGS84')
ALBERS = pyproj.CRS.from_proj4('+proj=aea +lat_1=24 +lat_2=30 +lat_0=27 +lon_0=74 +datum=WGS84 +units=m')
TO_M = pyproj.Transformer.from_crs('EPSG:4326', ALBERS, always_xy=True)
TO_DEG = pyproj.Transformer.from_crs(ALBERS, 'EPSG:4326', always_xy=True)


def area_km2(g):
    return abs(GEOD.geometry_area_perimeter(g)[0]) / 1e6


def perimeter_km(g):
    return GEOD.geometry_area_perimeter(g)[1] / 1e3


def length_km(g):
    return 0.0 if g.is_empty else GEOD.geometry_length(g) / 1e3


def centroid_equal_area(g):
    """Centroid computed in an equal-area projection, returned as lon/lat."""
    projected = shapely.transform(g, lambda xy: np.column_stack(TO_M.transform(xy[:, 0], xy[:, 1])))
    c = projected.centroid
    lon, lat = TO_DEG.transform(c.x, c.y)
    return [round(lon, DECIMALS), round(lat, DECIMALS)]


def round_coords(g):
    return shapely.set_precision(g, 10 ** -DECIMALS)


def sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    names = json.loads(NAMES.read_text(encoding='utf-8'))
    dist_names, state_names = names['districts'], names['context_states']

    current = json.loads(CURRENT.read_text(encoding='utf-8'))
    today = {d['id']: d for d in current['districts']}
    missing_today = [v['id'] for v in dist_names.values() if v['id'] not in today]
    assert not missing_today, f'districts missing from the current list: {missing_today}'

    reader = shapefile.Reader(str(RAW))
    by_state, raj = {}, {}
    for sr in reader.shapeRecords():
        rec = sr.record.as_dict()
        geom = shape(sr.shape.__geo_interface__)
        by_state.setdefault(rec['ST_NM'], []).append(geom)
        if rec['ST_NM'] == STATE:
            raj[rec['DISTRICT']] = (rec, geom)

    missing = set(raj) - set(dist_names)
    extra = set(dist_names) - set(raj)
    assert not missing and not extra, f'name table mismatch: missing={missing} extra={extra}'
    assert len(raj) == 33, f'expected 33 districts, found {len(raj)}'

    raj_union = unary_union([g for _, g in raj.values()])
    frame = box(*raj_union.bounds).buffer(CONTEXT_MARGIN_DEG, join_style='mitre')
    # only the five states that touch Rajasthan matter, and only the part near it
    state_union = {s: unary_union(by_state[s]).intersection(frame) for s in NEIGHBOUR_STATES}
    other_states = unary_union(list(state_union.values()))

    # the part of Rajasthan's outline that no other Indian state shares = the international (Pakistan) border
    outer = raj_union.boundary
    leftover = shapely.line_merge(outer.difference(other_states.buffer(SNAP_DEG)))
    pieces = list(leftover.geoms) if hasattr(leftover, 'geoms') else [leftover]
    intl_line = unary_union([x for x in pieces if length_km(x) >= MIN_INTL_STRETCH_KM])
    intl_total_km = length_km(intl_line)
    intl_zone = intl_line.buffer(SNAP_DEG)
    district_zone = {k: raj[k][1].buffer(SNAP_DEG) for k in raj}          # buffered once, reused for every pair
    state_zone = {s: state_union[s].buffer(SNAP_DEG) for s in NEIGHBOUR_STATES}

    order = sorted(raj, key=lambda k: dist_names[k]['en'])
    meta = {}
    for key in order:
        rec, g = raj[key]
        bnd = g.boundary
        neighbours = []
        for other in order:
            if other == key:
                continue
            shared = length_km(bnd.intersection(district_zone[other]))
            if shared >= MIN_SHARED_KM:
                neighbours.append(dist_names[other]['id'])
        border_states = []
        for s in NEIGHBOUR_STATES:
            km = length_km(bnd.intersection(state_zone[s]))
            if km >= MIN_SHARED_KM:
                border_states.append({'state': state_names[s]['id'], 'km': round(km)})
        a, p = area_km2(g), perimeter_km(g)
        meta[key] = {
            'area_km2': round(a, 1),
            'perimeter_km': round(p, 1),
            'compactness': round(4 * math.pi * a / (p * p), 3),     # Polsby-Popper: 1 = circle
            'centroid': centroid_equal_area(g),
            'neighbours': sorted(neighbours),
            'border_states': sorted(border_states, key=lambda x: -x['km']),
            'intl_border_km': round(length_km(bnd.intersection(intl_zone))),
            'parts': len(g.geoms) if hasattr(g, 'geoms') else 1,
        }

    # simplify districts and the neighbouring states together, so every shared edge stays shared
    coverage = [raj[k][1] for k in order] + [state_union[s] for s in NEIGHBOUR_STATES]
    coverage_ok = bool(shapely.coverage_is_valid(coverage))
    # known quality of the SOURCE: overlaps or gaps between neighbouring polygons (reported, not hidden)
    bad_edges = shapely.coverage_invalid_edges(coverage[:len(order)])
    invalid_edge_km = round(sum(length_km(e) for e in bad_edges), 1)
    simple = shapely.coverage_simplify(coverage, SIMPLIFY_DEG)
    simple = [round_coords(g) for g in simple]
    d_simple, s_simple = simple[:len(order)], simple[len(order):]

    features = []
    for key, g in zip(order, d_simple):
        rec = raj[key][0]
        n = dist_names[key]
        pt = shapely.point_on_surface(g)
        props = {
            'id': n['id'],
            'name': {'en': n['en'], 'hi': n['hi'], 'ur': n['ur']},
            'census_district_code': rec['DT_CEN_CD'],
            'source_name': key,
            'division': today[n['id']]['division_id'],              # division in today's list (a district id)
            'label_point': [round(pt.x, DECIMALS), round(pt.y, DECIMALS)],
            'bbox': [round(v, DECIMALS) for v in g.bounds],
            **meta[key],
        }
        features.append({'type': 'Feature', 'properties': props, 'geometry': mapping(g)})

    context = []
    view = box(*raj_union.bounds).buffer(0.3, join_style='mitre')            # the window the map actually shows
    for s, g in zip(NEIGHBOUR_STATES, s_simple):
        n = state_names[s]
        lp = shapely.point_on_surface(g.intersection(view))
        context.append({'type': 'Feature',
                        'properties': {'id': n['id'], 'name': {'en': n['en'], 'hi': n['hi'], 'ur': n['ur']},
                                       'label_point': [round(lp.x, DECIMALS), round(lp.y, DECIMALS)]},
                        'geometry': mapping(g)})

    OUT.mkdir(parents=True, exist_ok=True)
    dump = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    (OUT / 'districts-2011.geojson').write_text(dump({'type': 'FeatureCollection', 'features': features}), encoding='utf-8')
    (OUT / 'context-states.geojson').write_text(dump({'type': 'FeatureCollection', 'features': context}), encoding='utf-8')

    total_orig = sum(area_km2(raj[k][1]) for k in order)
    total_simple = sum(area_km2(g) for g in d_simple)
    manifest = {
        'built_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'names_reviewed_by_owner': bool(names.get('_reviewed')),
        'tools': {'shapely': shapely.__version__, 'pyproj': pyproj.__version__, 'pyshp': shapefile.__version__},
        'layers': {
            'districts-2011': {
                'description': 'Rajasthan districts as in Census 2011 (33 districts)',
                'features': len(features),
                'source': 'DataMeet India community, Districts/Census_2011/2011_Dist.shp',
                'source_url': 'https://github.com/datameet/maps/tree/master/Districts/Census_2011',
                'licence': 'Creative Commons Attribution 2.5 India',
                'source_sha256': sha256(RAW.with_suffix('.shp')),
            },
            'context-states': {
                'description': 'Neighbouring states (Punjab, Haryana, Uttar Pradesh, Madhya Pradesh, Gujarat), drawn for context only',
                'features': len(context),
                'source': 'same file as above, districts dissolved into states',
            },
        },
        'processing': {
            'simplify_degrees': SIMPLIFY_DEG, 'coordinate_decimals': DECIMALS,
            'adjacency_snap_degrees': SNAP_DEG, 'min_shared_border_km': MIN_SHARED_KM,
            'min_international_stretch_km': MIN_INTL_STRETCH_KM,
            'measurements_from': 'original unsimplified geometry (WGS84 geodesic)',
        },
        'checks': {
            'source_is_clean_tiling': coverage_ok,
            'source_invalid_edge_km_districts': invalid_edge_km,
            'source_note': 'DataMeet polygons overlap slightly in places (largest: Alwar/Dausa, about 5.5 km2 of 342,469); no gaps. Edges that are not shared exactly are left unsimplified.',
            'total_area_km2_original': round(total_orig),
            'total_area_km2_simplified': round(total_simple),
            'simplification_area_change_percent': round(100 * (total_simple - total_orig) / total_orig, 3),
            'international_border_km_computed': round(intl_total_km),
            'all_simplified_geometries_valid': all(g.is_valid for g in d_simple + s_simple),
        },
        'current_list': {
            'source': current['source'],
            'counts': current['counts'],
            'divisions': current['divisions'],
            'new_districts': [{'id': d['id'], 'name': d['name'], 'division_id': d['division_id']} for d in current['districts'] if d['status'] == 'new_since_2011'],
            'data_quality': current['data_quality'],
            'trust': current['trust'],
        },
        'size_bytes': {f: (OUT / f).stat().st_size for f in ('districts-2011.geojson', 'context-states.geojson')},
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(manifest['checks'], indent=2))
    print(json.dumps(manifest['size_bytes'], indent=2))


if __name__ == '__main__':
    main()
