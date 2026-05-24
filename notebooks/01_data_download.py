# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 01 — Data download (Iberian birds + EU Article 12, effort-correction replication)
#
# Fetches every input dataset needed by the coverage-correction pipeline.
# Self-contained: a fresh clone runs this notebook end-to-end without manual
# data preparation.
#
# This is a **sibling-reused** download layer (decision **D6**): the two GBIF
# basis-of-record strategies use the *same download DOIs* as the prior
# `sdm-scale-replication` chain so the only changed variable is the
# coverage-based correction itself.
#
# ## Datasets
#
# 1. **GBIF Strategy A — "museum + sensors"** (`museum`). BoR =
#    `PRESERVED_SPECIMEN + MACHINE_OBSERVATION`. DOI `10.15468/dl.r8pcat`,
#    download key `0008222-260519110011954`.
# 2. **GBIF Strategy B — "all observations incl. citizen-science"** (`allbor`).
#    BoR = `HUMAN_OBSERVATION + PRESERVED_SPECIMEN + MACHINE_OBSERVATION`.
#    DOI `10.15468/dl.e9xv7p`, download key `0008251-260519110011954`.
# 3. **EU Birds Directive Article 12 distribution polygons** (EEA, 2013–2018
#    reporting period, 10 km grid, EPSG:3035, CC-BY 4.0) — the expert-rangemap
#    gold standard the corrected hotspots are re-compared against.
#
# Within each GBIF strategy, `02_data_clean.py` splits records by year
# (`>= 2000` modern/atlas, `< 2000` historical/rangemap). One DOI per strategy
# serves both year windows.
#
# **Credentials.** GBIF zips are fetched from the public occurrence-download
# endpoint by URL once a key is minted — no credentials needed at execution
# time. Set `GBIF_USER` / `GBIF_PWD` / `GBIF_EMAIL` only if you want to mint a
# fresh download (fallback path). The Article 12 GPKG is public CC-BY 4.0.
#
# **Synthetic-demo fallback.** When a real dataset is unavailable (no minted
# key + no credentials, or the EEA file is missing and the network download
# fails), a deterministic synthetic stand-in is written and a
# `data/raw/USING_SYNTHETIC_DEMO_DATA_*.txt` flag is dropped. This is what lets
# the pipeline run on a fresh checkout without the multi-GB real download.

# %%
import json
import os
import time
import zipfile
from datetime import date
from pathlib import Path

import requests

# %% [markdown]
# ## Paths

# %%
ROOT = Path("..").resolve()
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
GBIF_DIR = DATA_DIR / "gbif"
EXTERNAL_DIR = DATA_DIR / "external"
ART12_DIR = EXTERNAL_DIR / "art12"

for d in (RAW_DIR, GBIF_DIR, ART12_DIR):
    d.mkdir(parents=True, exist_ok=True)

print(f"ROOT     = {ROOT}")
print(f"RAW_DIR  = {RAW_DIR}")
print(f"GBIF_DIR = {GBIF_DIR}")
print(f"ART12_DIR= {ART12_DIR}")

SOURCES: list[dict] = []

# Conservative threshold — small enough to detect broken downloads, big
# enough to never false-positive on a real zip.
MIN_ZIP_BYTES = 1_000


# %% [markdown]
# ## GBIF Strategy A — "museum + sensors" (`museum`)
#
# DOI `10.15468/dl.r8pcat`. Predicates (Aves class, ES/PT/AD/GI, coordinates,
# no geospatial issue, BoR `PRESERVED_SPECIMEN + MACHINE_OBSERVATION`, no year
# filter — the year split is a clean-stage operation). Reused from the sibling
# chain per D6.

# %%
GBIF_MUSEUM_DL_KEY = os.environ.get("GBIF_MUSEUM_DL_KEY", "0008222-260519110011954")
GBIF_MUSEUM_DL_DOI = os.environ.get("GBIF_MUSEUM_DL_DOI", "10.15468/dl.r8pcat")

GBIF_MUSEUM_PREDICATES = {
    "taxonKey": 212,
    "taxonKey_resolution": "Aves (class, ACCEPTED)",
    "country": ["ES", "PT", "AD", "GI"],
    "hasCoordinate": True,
    "hasGeospatialIssue": False,
    "basisOfRecord": ["PRESERVED_SPECIMEN", "MACHINE_OBSERVATION"],
}

GBIF_MUSEUM_ZIP = GBIF_DIR / "birds_iberia_museum.zip"
GBIF_MUSEUM_DOI_PATH = GBIF_DIR / "museum_download_doi.txt"
GBIF_MUSEUM_KEY_PATH = GBIF_DIR / "museum_download_key.txt"
GBIF_MUSEUM_META = GBIF_DIR / "birds_iberia_museum_metadata.json"


# %% [markdown]
# ## GBIF Strategy B — "all observations incl. citizen-science" (`allbor`)
#
# DOI `10.15468/dl.e9xv7p`. Same predicates as Strategy A but with
# `HUMAN_OBSERVATION` added to the BoR list. Reused from the sibling chain
# per D6.

# %%
GBIF_ALLBOR_DL_KEY = os.environ.get("GBIF_ALLBOR_DL_KEY", "0008251-260519110011954")
GBIF_ALLBOR_DL_DOI = os.environ.get("GBIF_ALLBOR_DL_DOI", "10.15468/dl.e9xv7p")

GBIF_ALLBOR_PREDICATES = {
    "taxonKey": 212,
    "taxonKey_resolution": "Aves (class, ACCEPTED)",
    "country": ["ES", "PT", "AD", "GI"],
    "hasCoordinate": True,
    "hasGeospatialIssue": False,
    "basisOfRecord": [
        "HUMAN_OBSERVATION", "PRESERVED_SPECIMEN", "MACHINE_OBSERVATION"
    ],
}

GBIF_ALLBOR_ZIP = GBIF_DIR / "birds_iberia_allbor.zip"
GBIF_ALLBOR_DOI_PATH = GBIF_DIR / "allbor_download_doi.txt"
GBIF_ALLBOR_KEY_PATH = GBIF_DIR / "allbor_download_key.txt"
GBIF_ALLBOR_META = GBIF_DIR / "birds_iberia_allbor_metadata.json"


# %% [markdown]
# ## GBIF download helpers
#
# `fetch_gbif_by_key` — pull a pre-minted download zip by its key (public URL,
# no credentials), idempotent. `mint_gbif_download` — fallback that mints a
# fresh download via the API when `GBIF_USER/PWD/EMAIL` are set and the
# hardcoded key is still a `TODO_` placeholder.

# %%
def fetch_gbif_by_key(key: str, zip_path: Path, doi: str, doi_path: Path,
                      key_path: Path, meta_path: Path,
                      predicates: dict) -> dict:
    """Fetch a pre-minted GBIF download zip by URL. No credentials needed."""
    if (zip_path.exists() and zip_path.stat().st_size > MIN_ZIP_BYTES
            and doi_path.exists() and key_path.exists()):
        print(f"  [cached]  key = {key_path.read_text().strip()}, "
              f"doi = {doi_path.read_text().strip()}")
        print(f"            zip = {zip_path} ({zip_path.stat().st_size:,} bytes)")
        return {"key": key_path.read_text().strip(),
                "doi": doi_path.read_text().strip(),
                "zip": str(zip_path)}

    url = f"https://api.gbif.org/v1/occurrence/download/request/{key}.zip"
    print(f"  fetching {url}")
    # The whole fetch — request start AND streamed body — is wrapped, so a
    # mid-stream drop (e.g. ChunkedEncodingError) also falls back to synthetic
    # instead of crashing the notebook. Partial zips are removed.
    try:
        r = requests.get(url, stream=True, timeout=600, allow_redirects=True)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    except requests.RequestException as e:
        print(f"  [fail  ]  GBIF fetch failed: {e}")
        if zip_path.exists():
            zip_path.unlink()  # drop the truncated zip.
        return {"key": None, "doi": None, "zip": None, "skipped": True,
                "reason": f"GBIF fetch of key {key} failed: {e}"}
    print(f"  saved {zip_path} ({zip_path.stat().st_size:,} bytes)")

    doi_path.write_text(doi + "\n")
    key_path.write_text(key + "\n")
    meta_path.write_text(json.dumps({
        "download_key": key, "doi": doi, "doi_url": f"https://doi.org/{doi}",
        "source_url": url, "predicates": predicates,
    }, indent=2))
    return {"key": key, "doi": doi, "zip": str(zip_path)}


def mint_gbif_download(predicates: dict, name: str) -> dict | None:
    """Mint a fresh GBIF download via the API. None if credentials absent / fails."""
    user = os.environ.get("GBIF_USER")
    pwd = os.environ.get("GBIF_PWD")
    email = os.environ.get("GBIF_EMAIL")
    if not (user and pwd and email):
        print(f"  [skip  ]  GBIF_USER/PWD/EMAIL not set — cannot mint '{name}'")
        return None

    json_predicate = {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY",
             "value": str(predicates["taxonKey"])},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
            {"type": "in", "key": "COUNTRY", "values": predicates["country"]},
            {"type": "in", "key": "BASIS_OF_RECORD",
             "values": predicates["basisOfRecord"]},
        ],
    }
    print(f"  [mint  ]  requesting GBIF download for '{name}'")
    api_url = "https://api.gbif.org/v1/occurrence/download/request"
    body = {"creator": user, "notificationAddresses": [email],
            "sendNotification": False, "format": "SIMPLE_CSV",
            "predicate": json_predicate}
    resp = requests.post(api_url, json=body, auth=(user, pwd), timeout=120)
    if not resp.ok:
        print(f"  [fail  ]  mint POST {resp.status_code}: {resp.text[:200]}")
        return None
    key = resp.text.strip()
    print(f"  [mint  ]  download key = {key} — polling ...")
    status_url = f"https://api.gbif.org/v1/occurrence/download/{key}"
    for attempt in range(60):
        s = requests.get(status_url, timeout=30).json()
        status = s.get("status")
        print(f"            attempt {attempt + 1}: status = {status}")
        if status == "SUCCEEDED":
            return {"key": key, "doi": s.get("doi", "")}
        if status in ("FAILED", "CANCELLED", "FILE_ERASED"):
            return None
        time.sleep(30)
    return None


def get_or_mint(name: str, hardcoded_key: str, hardcoded_doi: str,
                zip_path: Path, doi_path: Path, key_path: Path,
                meta_path: Path, predicates: dict) -> dict:
    """If hardcoded key is real, fetch by URL. Else attempt to mint. Else skip.

    Set GBIF_FORCE_SYNTHETIC=1 to skip the (multi-GB) real download entirely and
    use the deterministic synthetic demo data — the default for a fresh-checkout
    / offline / CI end-to-end run."""
    if os.environ.get("GBIF_FORCE_SYNTHETIC"):
        return {"key": None, "doi": None, "zip": None, "skipped": True,
                "reason": "GBIF_FORCE_SYNTHETIC set — using synthetic demo data."}
    if not hardcoded_key.startswith("TODO_"):
        return fetch_gbif_by_key(hardcoded_key, zip_path, hardcoded_doi,
                                 doi_path, key_path, meta_path, predicates)
    minted = mint_gbif_download(predicates, name)
    if minted:
        return fetch_gbif_by_key(minted["key"], zip_path, minted["doi"],
                                 doi_path, key_path, meta_path, predicates)
    return {"key": None, "doi": None, "zip": None, "skipped": True,
            "reason": (f"No pre-minted key for '{name}' and "
                       f"GBIF_USER/PWD/EMAIL not set.")}


# %% [markdown]
# ## Execute the two GBIF strategy downloads

# %%
print("\n--- GBIF Strategy A: museum + sensors ---")
museum_result = get_or_mint(
    name="museum", hardcoded_key=GBIF_MUSEUM_DL_KEY,
    hardcoded_doi=GBIF_MUSEUM_DL_DOI,
    zip_path=GBIF_MUSEUM_ZIP, doi_path=GBIF_MUSEUM_DOI_PATH,
    key_path=GBIF_MUSEUM_KEY_PATH, meta_path=GBIF_MUSEUM_META,
    predicates=GBIF_MUSEUM_PREDICATES,
)
SOURCES.append({
    "strategy": "museum",
    "name": "GBIF Iberian birds — PRESERVED_SPECIMEN + MACHINE_OBSERVATION",
    "role": "Strategy A — museum+sensor provenance (reused from sibling, D6)",
    "doi": museum_result.get("doi"),
    "url": (f"https://doi.org/{museum_result['doi']}"
            if museum_result.get("doi") else None),
    "license": "CC-BY-NC-4.0 (per individual GBIF datasets)",
    "accessed_on": date.today().isoformat(),
    "download_key": museum_result.get("key"),
    "predicates": GBIF_MUSEUM_PREDICATES,
    "local_path": museum_result.get("zip"),
    "skipped": museum_result.get("skipped", False),
    "skip_reason": museum_result.get("reason"),
})

# %%
print("\n--- GBIF Strategy B: all observations (incl. citizen-science) ---")
allbor_result = get_or_mint(
    name="allbor", hardcoded_key=GBIF_ALLBOR_DL_KEY,
    hardcoded_doi=GBIF_ALLBOR_DL_DOI,
    zip_path=GBIF_ALLBOR_ZIP, doi_path=GBIF_ALLBOR_DOI_PATH,
    key_path=GBIF_ALLBOR_KEY_PATH, meta_path=GBIF_ALLBOR_META,
    predicates=GBIF_ALLBOR_PREDICATES,
)
SOURCES.append({
    "strategy": "allbor",
    "name": "GBIF Iberian birds — HUMAN + PRESERVED_SPECIMEN + MACHINE_OBSERVATION",
    "role": "Strategy B — all observations incl. citizen-science (reused, D6)",
    "doi": allbor_result.get("doi"),
    "url": (f"https://doi.org/{allbor_result['doi']}"
            if allbor_result.get("doi") else None),
    "license": "CC-BY-NC-4.0 (per individual GBIF datasets)",
    "accessed_on": date.today().isoformat(),
    "download_key": allbor_result.get("key"),
    "predicates": GBIF_ALLBOR_PREDICATES,
    "local_path": allbor_result.get("zip"),
    "skipped": allbor_result.get("skipped", False),
    "skip_reason": allbor_result.get("reason"),
})


# %% [markdown]
# ## Per-strategy GBIF synthetic fallback
#
# If a strategy's download was skipped, emit a deterministic synthetic Iberian
# bird dataset at that strategy's zip path. **Per-strategy** — Strategy A can
# be real while Strategy B is synthetic. Each strategy writes its own
# `data/raw/USING_SYNTHETIC_DEMO_DATA_<strategy>.txt` flag; downstream
# notebooks key off these flags and tag artefacts with `synthetic_data: true`.
#
# The synthetic generator emits per-record rows (not just presence) so that
# `02_data_clean.py` can build a per-cell **species-frequency table** with
# realistic per-species record counts — the abundance data the Chao & Jost
# coverage estimator needs (singletons f1, doubletons f2).

# %%
def make_synthetic_demo(zip_path: Path, doi_path: Path, key_path: Path,
                        meta_path: Path, strategy: str,
                        flag_path: Path) -> dict:
    """Generate deterministic Iberian bird demo data for a single strategy."""
    import numpy as np

    seed = {"museum": 20260522, "allbor": 20260523}.get(strategy, 20260524)
    rng = np.random.default_rng(seed=seed)

    SPECIES_N = 80
    lon0, lon1 = -10.0, 4.0
    lat0, lat1 = 35.0, 44.0

    centres_lon = rng.uniform(lon0 + 1, lon1 - 1, size=SPECIES_N)
    centres_lat = rng.uniform(lat0 + 1, lat1 - 1, size=SPECIES_N)
    range_radii = rng.uniform(1.0, 4.0, size=SPECIES_N)
    species_names = [f"Synthavis demoensis_{i:03d}" for i in range(SPECIES_N)]

    hotspot_centres = np.array([
        [-3.5, 37.0],   # Sierra Nevada-ish
        [0.0, 42.5],    # Pyrenees-ish
        [-6.5, 39.5],   # Extremadura-ish
    ])

    records: list[dict] = []
    # 1) Historical (pre-2000) — wide spread per species.
    for sp_idx, name in enumerate(species_names):
        n_pts = rng.integers(15, 40)
        lons = rng.normal(centres_lon[sp_idx], range_radii[sp_idx], n_pts)
        lats = rng.normal(centres_lat[sp_idx], range_radii[sp_idx] * 0.6, n_pts)
        years = rng.integers(1950, 2000, n_pts)
        keep = (lons >= lon0) & (lons <= lon1) & (lats >= lat0) & (lats <= lat1)
        for j in np.where(keep)[0]:
            records.append({"species": name, "lat": float(lats[j]),
                            "lon": float(lons[j]), "year": int(years[j]),
                            "bor": "PRESERVED_SPECIMEN"})
    # 2) Modern (2000+) — denser, with hotspot-injected density for half the
    #    species. Effort bias: allbor gets extra repeat visits at hotspots,
    #    inflating per-cell record counts (lower coverage spread to correct).
    effort_boost = 3 if strategy == "allbor" else 1
    for sp_idx, name in enumerate(species_names):
        n_pts = rng.integers(40, 120)
        lons = rng.normal(centres_lon[sp_idx], range_radii[sp_idx] * 0.8, n_pts)
        lats = rng.normal(centres_lat[sp_idx], range_radii[sp_idx] * 0.5, n_pts)
        years = rng.integers(2000, 2025, n_pts)
        if sp_idx % 2 == 0:
            hc = hotspot_centres[sp_idx % 3]
            extra_n = rng.integers(20, 60) * effort_boost
            extra_lons = rng.normal(hc[0], 0.3, extra_n)
            extra_lats = rng.normal(hc[1], 0.3, extra_n)
            extra_years = rng.integers(2010, 2025, extra_n)
            lons = np.concatenate([lons, extra_lons])
            lats = np.concatenate([lats, extra_lats])
            years = np.concatenate([years, extra_years])
        keep = (lons >= lon0) & (lons <= lon1) & (lats >= lat0) & (lats <= lat1)
        for j in np.where(keep)[0]:
            records.append({"species": name, "lat": float(lats[j]),
                            "lon": float(lons[j]), "year": int(years[j]),
                            "bor": "MACHINE_OBSERVATION"})

    cols = ["gbifID", "species", "decimalLatitude", "decimalLongitude",
            "year", "basisOfRecord", "countryCode"]
    lines = ["\t".join(cols)]
    for i, rec in enumerate(records):
        lines.append("\t".join([
            str(i), rec["species"], f"{rec['lat']:.5f}", f"{rec['lon']:.5f}",
            str(rec["year"]), rec["bor"], "ES",
        ]))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("occurrence.csv", "\n".join(lines) + "\n")

    doi_path.write_text(f"SYNTHETIC_DEMO_DATA_NO_DOI_{strategy}\n")
    key_path.write_text(f"SYNTHETIC_DEMO_{strategy}\n")
    meta_path.write_text(json.dumps({
        "synthetic": True, "strategy": strategy, "seed": seed,
        "n_records": len(records), "n_species": SPECIES_N,
    }, indent=2))
    flag_path.write_text(
        f"Strategy '{strategy}' is SYNTHETIC DEMO DATA.\n"
        f"Mint the real GBIF DOI for this strategy and re-run to replace.\n")
    print(f"  [demo  ]  wrote synthetic strategy='{strategy}': "
          f"{len(records):,} records across {SPECIES_N} species")
    return {"n_records": len(records), "n_species": SPECIES_N, "seed": seed}


# %%
SYNTHETIC_FLAG_MUSEUM = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_museum.txt"
SYNTHETIC_FLAG_ALLBOR = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_allbor.txt"

if museum_result.get("skipped"):
    print("\n--- Synthetic demo fallback for Strategy A (museum) ---")
    demo_info = make_synthetic_demo(
        zip_path=GBIF_MUSEUM_ZIP, doi_path=GBIF_MUSEUM_DOI_PATH,
        key_path=GBIF_MUSEUM_KEY_PATH, meta_path=GBIF_MUSEUM_META,
        strategy="museum", flag_path=SYNTHETIC_FLAG_MUSEUM)
    SOURCES.append({
        "strategy": "museum",
        "name": "Synthetic Iberian bird demo data (Strategy A — museum)",
        "role": "demo fallback — used when DOI #1 unavailable",
        "doi": None, "url": None,
        "license": f"n/a (generated locally, seed {demo_info['seed']})",
        "accessed_on": date.today().isoformat(), "synthetic": True})
else:
    if SYNTHETIC_FLAG_MUSEUM.exists():
        SYNTHETIC_FLAG_MUSEUM.unlink()

if allbor_result.get("skipped"):
    print("\n--- Synthetic demo fallback for Strategy B (allbor) ---")
    demo_info = make_synthetic_demo(
        zip_path=GBIF_ALLBOR_ZIP, doi_path=GBIF_ALLBOR_DOI_PATH,
        key_path=GBIF_ALLBOR_KEY_PATH, meta_path=GBIF_ALLBOR_META,
        strategy="allbor", flag_path=SYNTHETIC_FLAG_ALLBOR)
    SOURCES.append({
        "strategy": "allbor",
        "name": "Synthetic Iberian bird demo data (Strategy B — allbor)",
        "role": "demo fallback — used when DOI #2 unavailable",
        "doi": None, "url": None,
        "license": f"n/a (generated locally, seed {demo_info['seed']})",
        "accessed_on": date.today().isoformat(), "synthetic": True})
else:
    if SYNTHETIC_FLAG_ALLBOR.exists():
        SYNTHETIC_FLAG_ALLBOR.unlink()


# %% [markdown]
# ## EU Article 12 expert-rangemap gold standard
#
# EU Birds Directive Article 12 distribution data (EEA, 2013–2018 reporting
# period). The expected on-disk artefact is a GeoPackage at
# `data/external/art12/ART12_3035_distribution_data_without_sensitive.gpkg`
# (layer `EU_ART12_birds_distribution_2013_2018_without_sensitive_species`,
# EPSG:3035, 10 km grid, CC-BY 4.0).
#
# **Acquisition.** The EEA portal serves the file as a ~237 MB bundle behind a
# JS-driven "Download all files" link, not a single stable direct URL, so a
# robust headless download is not guaranteed. The downloader:
#
# 1. Uses the file if it already exists locally (e.g. symlinked from a manual
#    EEA download — see `docs/` or the dataset landing page
#    `https://sdi.eea.europa.eu/data/e2face16-f352-4aff-9e4f-0ad1306f89b5`).
# 2. Otherwise tries `ART12_DOWNLOAD_URL` (env var) if set.
# 3. Otherwise writes a **deterministic synthetic Article 12 GPKG** derived
#    from the GBIF species set, dropping
#    `data/raw/USING_SYNTHETIC_DEMO_DATA_art12.txt`. This keeps `03_analysis`'s
#    Article 12 comparison runnable on a fresh checkout. The synthetic layer
#    matches the real schema (`country`, `speciesnameEU`, `geometry` in 3035).

# %%
ART12_GPKG = ART12_DIR / "ART12_3035_distribution_data_without_sensitive.gpkg"
ART12_LAYER = ("EU_ART12_birds_distribution_2013_2018_without_sensitive_species")
ART12_FLAG = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_art12.txt"
ART12_LANDING = "https://sdi.eea.europa.eu/data/e2face16-f352-4aff-9e4f-0ad1306f89b5"
ART12_DOWNLOAD_URL = os.environ.get("ART12_DOWNLOAD_URL")


def make_synthetic_art12(gpkg_path: Path, layer: str) -> dict:
    """Write a deterministic synthetic Article-12-like GPKG matching the real
    schema, derived from the synthetic GBIF species set so the downstream
    matched-subset comparison has overlapping species."""
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import box

    rng = np.random.default_rng(20260524)
    # Mirror the synthetic GBIF species names so matched-subset overlap > 0.
    SPECIES_N = 80
    species_names = [f"Synthavis demoensis_{i:03d}" for i in range(SPECIES_N)]
    # Iberia bbox in WGS84; build 10 km cells in EPSG:3035 then store as 3035.
    lon0, lon1, lat0, lat1 = -10.0, 4.0, 35.0, 44.0

    # Sample cell centres in lon/lat, reproject to 3035, build 10 km boxes.
    rows = []
    for sp_idx, name in enumerate(species_names):
        # Each species occupies a contiguous-ish block of cells.
        n_cells = int(rng.integers(20, 120))
        clon = rng.uniform(lon0 + 1, lon1 - 1)
        clat = rng.uniform(lat0 + 1, lat1 - 1)
        rad = rng.uniform(1.0, 3.5)
        lons = np.clip(rng.normal(clon, rad, n_cells), lon0, lon1)
        lats = np.clip(rng.normal(clat, rad * 0.6, n_cells), lat0, lat1)
        for lo, la in zip(lons, lats):
            rows.append({"country": "ES", "speciesnameEU": name,
                         "lon": float(lo), "lat": float(la)})
    gdf_pts = gpd.GeoDataFrame(
        rows, geometry=gpd.points_from_xy([r["lon"] for r in rows],
                                          [r["lat"] for r in rows]),
        crs="EPSG:4326").to_crs("EPSG:3035")
    # 10 km square cells centred on each reprojected point.
    half = 5_000.0
    geoms = [box(p.x - half, p.y - half, p.x + half, p.y + half)
             for p in gdf_pts.geometry]
    gdf = gpd.GeoDataFrame(
        {"country": gdf_pts["country"].values,
         "speciesnameEU": gdf_pts["speciesnameEU"].values},
        geometry=geoms, crs="EPSG:3035")
    gpkg_path.parent.mkdir(parents=True, exist_ok=True)
    if gpkg_path.exists():
        gpkg_path.unlink()
    gdf.to_file(gpkg_path, layer=layer, driver="GPKG")
    return {"n_cells": len(gdf), "n_species": gdf["speciesnameEU"].nunique()}


print("\n--- EU Article 12 expert-rangemap gold standard ---")
art12_synthetic = False
if ART12_GPKG.exists() and ART12_GPKG.stat().st_size > MIN_ZIP_BYTES:
    print(f"  [cached]  {ART12_GPKG} ({ART12_GPKG.stat().st_size:,} bytes)")
    if ART12_FLAG.exists():
        ART12_FLAG.unlink()
elif ART12_DOWNLOAD_URL:
    print(f"  fetching {ART12_DOWNLOAD_URL}")
    try:
        r = requests.get(ART12_DOWNLOAD_URL, stream=True, timeout=900,
                         allow_redirects=True)
        r.raise_for_status()
        # Direct-URL downloads may be a zip; if so, extract the gpkg.
        tmp = ART12_DIR / "art12_download.bin"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
        if zipfile.is_zipfile(tmp):
            with zipfile.ZipFile(tmp) as zf:
                gpkg_members = [n for n in zf.namelist() if n.endswith(".gpkg")]
                if gpkg_members:
                    with zf.open(gpkg_members[0]) as src, open(ART12_GPKG, "wb") as dst:
                        dst.write(src.read())
            tmp.unlink()
        else:
            tmp.rename(ART12_GPKG)
        print(f"  saved {ART12_GPKG} ({ART12_GPKG.stat().st_size:,} bytes)")
        if ART12_FLAG.exists():
            ART12_FLAG.unlink()
    except Exception as e:  # noqa: BLE001
        print(f"  [fail  ]  Article 12 download failed: {e} — using synthetic")
        art12_synthetic = True
else:
    print("  [skip  ]  Article 12 GPKG not present and ART12_DOWNLOAD_URL unset")
    art12_synthetic = True

if art12_synthetic:
    print("  [demo  ]  writing synthetic Article 12 layer")
    a12 = make_synthetic_art12(ART12_GPKG, ART12_LAYER)
    ART12_FLAG.write_text(
        "Article 12 layer is SYNTHETIC DEMO DATA.\n"
        f"Download the real EEA dataset from {ART12_LANDING} and place it at\n"
        f"{ART12_GPKG} (or set ART12_DOWNLOAD_URL), then re-run.\n")
    print(f"  [demo  ]  synthetic Art-12: {a12['n_cells']:,} cells, "
          f"{a12['n_species']} species")

SOURCES.append({
    "name": "EU Birds Directive Article 12 distribution polygons (EEA 2013-2018)",
    "role": "Expert-rangemap gold standard for corrected-hotspot comparison",
    "doi": None,
    "url": ART12_LANDING,
    "license": "CC-BY-4.0 (EEA)",
    "accessed_on": date.today().isoformat(),
    "local_path": str(ART12_GPKG.relative_to(ROOT)),
    "layer": ART12_LAYER,
    "crs": "EPSG:3035",
    "synthetic": art12_synthetic,
})


# %% [markdown]
# ## Source registry
#
# Single JSON at `data/raw/sources.json` recording every download's
# strategy/URL/DOI/license/accessed-on + synthetic status. This is the
# provenance contract the Replication Study draft cites.

# %%
SOURCES_JSON = RAW_DIR / "sources.json"
with open(SOURCES_JSON, "w") as f:
    json.dump({
        "sources": SOURCES,
        "strategies": {
            "museum": {
                "synthetic": museum_result.get("skipped", False),
                "doi": museum_result.get("doi"),
                "download_key": museum_result.get("key"),
                "zip": (str(GBIF_MUSEUM_ZIP.relative_to(ROOT))
                        if GBIF_MUSEUM_ZIP.exists() else None)},
            "allbor": {
                "synthetic": allbor_result.get("skipped", False),
                "doi": allbor_result.get("doi"),
                "download_key": allbor_result.get("key"),
                "zip": (str(GBIF_ALLBOR_ZIP.relative_to(ROOT))
                        if GBIF_ALLBOR_ZIP.exists() else None)},
        },
        "art12": {
            "synthetic": art12_synthetic,
            "gpkg": (str(ART12_GPKG.relative_to(ROOT))
                     if ART12_GPKG.exists() else None),
            "layer": ART12_LAYER,
        },
        "written_on": date.today().isoformat(),
    }, f, indent=2)
print(f"\n--- Wrote source registry -> {SOURCES_JSON}")


# %% [markdown]
# ## Summary

# %%
print("\nArtefact inventory:")
artefacts = [
    ("Museum zip",          GBIF_MUSEUM_ZIP),
    ("Museum download DOI",  GBIF_MUSEUM_DOI_PATH),
    ("Museum synth flag",    SYNTHETIC_FLAG_MUSEUM),
    ("Allbor zip",          GBIF_ALLBOR_ZIP),
    ("Allbor download DOI",  GBIF_ALLBOR_DOI_PATH),
    ("Allbor synth flag",    SYNTHETIC_FLAG_ALLBOR),
    ("Article 12 GPKG",      ART12_GPKG),
    ("Article 12 synth flag", ART12_FLAG),
    ("Source registry JSON", SOURCES_JSON),
]
for name, p in artefacts:
    if p.exists():
        size = (p.stat().st_size if p.is_file()
                else sum(f.stat().st_size for f in p.rglob("*") if f.is_file()))
        print(f"  ok    {name:<24} {size:>12,} bytes  {p.relative_to(ROOT)}")
    else:
        print(f"  MISS  {name:<24} {'-':>12}        {p.relative_to(ROOT)}")
