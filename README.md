# RajAtlas

An interactive, trilingual (English, Hindi, Urdu) geographic atlas of Rajasthan. It is a standalone website, built in phases; the 10 modules agreed for the project are added one at a time. See [docs/ROADMAP.md](docs/ROADMAP.md).

**Status: Phase 1 done.** District boundaries (Census 2011 layout, 33 districts), measured area, boundary length, shape compactness, neighbours, state and Pakistan borders, divisions from today's 41-district list, a searchable district list, light and dark themes, and an interface in three languages.

## Layout

```
site/            the website (plain HTML, CSS and JavaScript, no build step) - this folder is what gets deployed
  assets/data/   boundary files and the build manifest (produced by tools/, do not edit by hand)
  _headers       security headers applied by Cloudflare
  404.html, robots.txt, .assetsignore
wrangler.jsonc   Cloudflare deployment settings
data/curated/    hand-checked inputs: trilingual names, today's district list
data/raw/        downloaded source files (not in git; recreate with tools/fetch_raw.py)
tools/           Python data pipeline and validators
docs/            roadmap, data sources, skills ledger
```

## Run it locally

One-time setup (Windows; built and tested with Python 3.14):

```
python -m venv .venv
.venv\Scripts\python -m pip install pyshp shapely pyproj
```

Rebuild the data and check it:

```
.venv\Scripts\python tools\fetch_raw.py                  # download sources (Wikipedia revision pinned, shapefile hash checked)
.venv\Scripts\python tools\ingest_current_districts.py   # parse today's district list and check it against itself
.venv\Scripts\python tools\build_boundaries.py           # measure and simplify the boundaries
.venv\Scripts\python tools\validate_boundaries.py        # independent checks on the published files
```

View the site (it must be served, not opened as a file, because it loads JSON):

```
cd site
python -m http.server 8765
```

Then open http://127.0.0.1:8765/. In-browser tests: `tests.html` (projection and statistics maths) and `tests-e2e.html` (clicking, searching, layers, languages, themes). Both are kept out of the deployed site by `site/.assetsignore`.

## Deploy (Cloudflare Workers, from GitHub)

1. Create an empty GitHub repository for this project (for example `rajatlas`) and push this folder to its `main` branch.
2. In Cloudflare: Workers & Pages, Create, import the repository.
3. Project name `rajatlas` (it must match `name` in `wrangler.jsonc`), build command empty, deploy command `npx wrangler deploy`, root directory `/`.
4. The site is then at `https://rajatlas.<your-workers-subdomain>.workers.dev/`. Every push to `main` redeploys it.

`wrangler.jsonc` serves the `site/` folder as static files and uses `site/404.html` for unknown addresses. A custom domain can be added later in the Cloudflare project settings.

## What is checked

* `ingest_current_districts.py` requires the list's two tables to agree and records every contradiction found on the source page.
* `validate_boundaries.py` re-reads only the published files: 17 checks including total area against the Census figure, neighbour symmetry, and that exactly the four districts that touch Pakistan show an international border.
* The browser tests (15 maths, 44 interaction) include a check that the map projection really preserves area, which the choropleth depends on, and a check that the site links to no outside page except the Wikipedia credit.

## Licences and attribution

* Boundaries: DataMeet India community, CC BY 2.5 India.
* Today's district list: Wikipedia, CC BY-SA 4.0 (pinned to revision 1381020334).
* Both are credited in the site footer. Details in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
* The project's own code and text have no licence file yet; add one before inviting others to reuse them.

## Known limits

* The map shows the Census 2011 layout. The 8 districts added since then are listed but not drawn.
* Hindi and Urdu wording is a draft awaiting the owner's review. `data/curated/district_names.json` has a `_reviewed` flag; set it to true only after checking.
* No population, farming or climate data yet. The page's claimed areas and populations are deliberately not used because they contradict each other.
