# Skills ledger

Purpose: show exactly what this project uses, so claims on a resume or portfolio are backed by files someone can open. Only things already built are listed as used. Update this file at the end of each phase.

## Used so far (Phase 1)

| Skill from your profile | Where it is used | Evidence |
|---|---|---|
| Geography: map projections (conical, equal-area) | The map is drawn in an Albers equal-area conic projection; the build uses the same projection for centroids | `site/assets/js/map.js` (`makeAlbers`), `site/tests.html` (area-preservation test) |
| Geography: choropleth maps | Five-class quantile choropleth, sequential colour ramp, categorical border layer | `site/assets/js/app.js` (`applyLayer`), `map.js` (`quantileClasses`) |
| Geography: map reading and map furniture | Latitude and longitude graticule, scale bar, borders and adjacency worked out from outlines | `map.js` (`drawGraticule`), `tools/build_boundaries.py` |
| Geography of Rajasthan | Districts, divisions, borders with Pakistan and five states, the changing district list | `site/`, `docs/DATA_SOURCES.md` |
| Mathematics and statistics | Geodesic area on the WGS84 ellipsoid, quantile classes, Polsby-Popper shape index, relative-error checks against a known total | `tools/build_boundaries.py`, `map.js`, `tests.html` |
| Social research methods (source criticism) | Recorded which source figures can be trusted and which contradict each other | `tools/ingest_current_districts.py`, `docs/DATA_SOURCES.md` |
| English, Hindi, Urdu | Whole interface in three languages including right-to-left layout; trilingual district names | `site/assets/js/i18n.js`, `data/curated/district_names.json` |
| AI-training habits: check each step, write down errors | 17 pipeline checks, 15 maths tests, 44 browser checks. Anomalies were traced before moving on (for example 1–5 km "international border" slivers on inland districts, and output files overwritten by a stale background run). The limits are written on the page. | `tools/validate_boundaries.py`, `site/tests.html`, `site/tests-e2e.html` |
| Programming: JavaScript | Canvas map renderer, hit-testing, i18n, accessible list and keyboard path, no libraries | `site/assets/js/` |
| Programming: Python | Shapefile reading, geodesic measurement, polygon simplification, data ingestion and validation | `tools/` (pyshp, shapely, pyproj) |
| Reproducibility | Pinned source revision, checksum check, one command per pipeline step | `tools/fetch_raw.py`, `README.md` |

## Not yet used (do not claim these)

* Databases, server code, authentication.
* Remote sensing and satellite data.
* Machine learning. (The AI-training side enters in phase 10 with the GeoQA benchmark.)
* Physics. Your resume mentions force and torque in robot reviews; nothing in this project uses them.

## Facts to keep straight

* Your profile is a final-year B.A. student. There is no Master's degree in it. If you have one, tell the assistant and this ledger will be updated.
* Hindi and Urdu wording is a draft until you review it.
* The AI-assisted parts of this work (code and draft text) should be described honestly if asked.
