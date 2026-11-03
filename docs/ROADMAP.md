# Roadmap: bringing the 10 modules into one project

Each phase ends with something that works and is checked. Modules are numbered as in the earlier recommendation list. Effort is a rough guide for part-time work.

| Phase | Module | What gets built | Needs | Main risk |
|---|---|---|---|---|
| **1 done** | 1 RajAtlas (core) | Boundary map, district profiles from geometry, divisions, trilingual UI | DataMeet, Wikipedia list | none open |
| **2** | 1 RajAtlas (data) | Census 2011 population and demographics per district; profile cards | Census 2011 Primary Census Abstract (official tables) | finding a clean, licensed district table |
| **3** | 3 Districts Through Time | 33 → 50 → 41 history; crosswalk from old to new districts; re-expressed 2011 figures | official notifications, village or tehsil boundaries (DataMeet village layer is ODbL) | parent districts are not in any source I have; needs official notifications |
| **4** | 2 RajPath | Place gazetteer, great-circle distance, five definitions of state-to-state distance, then road matrix, rail links, airports | OpenStreetMap (ODbL), datameet/railways (CC0), airport list | no open timetables; show connections, not schedules |
| **5** | 4 Climate and agro-zones | IMD rainfall and temperature per district, Köppen and Thornthwaite, 10 agro-climatic zones, crop statistics | IMD gridded data, Ministry crop data, district-to-zone mapping | zone mapping source not yet found |
| **6** | 5 Development index | Composite indicators, weights, clusters, Moran's I | Census 2011 tables from phase 2 | 2011 data is old and must be labelled |
| **7** | 6 Heritage and circuits | Sourced database of sites and fairs, trip planner over RajPath distances | curated, cited content | content research is the work |
| **8** | 8 Accessibility | Distance to stations and airports per district, gap maps | phase 4 network | overlaps phase 4; keep it analytical |
| **9** | 9 Water and desertification | Rainfall and vegetation trends, traditional water structures | satellite or reanalysis data, groundwater data (availability unchecked) | a new processing pipeline to learn |
| **10** | 7 GeoQA and 10 RajSurvey | Verified fact base and benchmark (reuses GeoTrace checker); offline field-survey tool | all earlier fact tables | RajSurvey needs the geolocation header changed on purpose and a privacy plan |

## Rules for every phase

1. Every number on screen traces to a named source in [DATA_SOURCES.md](DATA_SOURCES.md), with its year.
2. Every pipeline step has an independent check; a check that cannot fail does not count.
3. Known limits are written on the page, not hidden.
4. New text is written in English, Hindi and Urdu; drafts are marked until the owner reviews them.
5. Only the project's own scripts run on the site (the Content-Security-Policy in `site/_headers`).

## Immediate next steps

* Owner review of Hindi and Urdu district names, then set `_reviewed` to true.
* Phase 2: choose the Census 2011 table, check its licence, and add it to the pipeline.
* Put the site on its own GitHub repository and Cloudflare project (see README, "Deploy").
