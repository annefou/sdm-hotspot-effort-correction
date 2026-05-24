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
# # 02 — Data clean (Iberian birds, HEALPix-NESTED ladder, two BoR strategies)
#
# Ported from the sibling `sdm-scale-replication` chain, **plus one addition
# this replication needs**: per-cell *species-frequency* tables for the atlas
# layer. The sibling only kept per-cell *richness* (distinct-species count);
# coverage-based rarefaction (Chao & Jost 2012) needs the per-species record
# counts within each cell to estimate sample coverage. So we keep both.
#
# Bins each of the two BoR-strategy GBIF zips from `01_data_download.py` onto a
# HEALPix **NESTED** ladder of Nside in {16, 32, 64, 128, 256, 512}, with a
# year-stage split at 2000:
#
# - `year >= 2000` -> **modern** = "atlas-equivalent". Per-cell species
#   richness = number of distinct species observed in the cell. **Also**: the
#   per-(cell, species) record count (the abundance/frequency data).
# - `year < 2000`  -> **historical** = "range-map-equivalent". Per species,
#   convex hull (Shapely); per Nside, the hull's NESTED cell coverage via
#   `healpix_geo.nested.polygon_coverage`; per-cell richness = number of species
#   whose hull covers the cell.
#
# Outputs (`data/clean/`):
#
# - `richness_<strategy>.nc` — one NetCDF per strategy, one group per Nside,
#   each holding `richness_atlas` + `richness_rangemap` on the `cell` dim
#   (unchanged from the sibling, so 03's overlap re-use is drop-in).
# - `atlas_freq_<strategy>.parquet` — **NEW**. Long-form per-cell atlas
#   species-frequency: columns (nside, cell, species_id, count). This is the
#   sample-abundance input to the coverage estimator in `03_analysis.py`.
# - `species_index_<strategy>.parquet` — **NEW**. (species_id, species) map so
#   the Article 12 species match in 03 can resolve atlas species names.
# - `species_eoo_polygons.parquet` — per-species convex-hull WKT + counts.
# - `clean_report.json` — per-strategy record/species counts + synthetic flag.
#
# **Domain conventions enforced** (`DOMAIN.md`): HEALPix always NESTED via
# `healpix-geo` (never `healpy`); intermediate arrays as NetCDF + Parquet
# (never `.npz`); per-strategy synthetic flag honoured and propagated.

# %%
import json
import zipfile
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from healpix_geo import nested as hp_nested
from shapely.geometry import MultiPoint, Polygon

# %% [markdown]
# ## Constants

# %%
STRATEGIES = ["museum", "allbor"]
NSIDES = [16, 32, 64, 128, 256, 512]
DEPTHS = {n: int(np.log2(n)) for n in NSIDES}

ELLIPSOID = "WGS84"
YEAR_SPLIT = 2000  # year >= 2000 -> modern (atlas), year < 2000 -> historical

IBERIA_LON_MIN, IBERIA_LAT_MIN = -10.0, 35.0
IBERIA_LON_MAX, IBERIA_LAT_MAX = 4.0, 44.0

ROOT = Path("..").resolve()
DATA = ROOT / "data"
GBIF_DIR = DATA / "gbif"
RAW_DIR = DATA / "raw"
CLEAN_DIR = DATA / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

STRATEGY_ZIPS = {s: GBIF_DIR / f"birds_iberia_{s}.zip" for s in STRATEGIES}
STRATEGY_SYNTH_FLAGS = {
    s: RAW_DIR / f"USING_SYNTHETIC_DEMO_DATA_{s}.txt" for s in STRATEGIES
}
STRATEGY_RICHNESS_NC = {s: CLEAN_DIR / f"richness_{s}.nc" for s in STRATEGIES}
STRATEGY_FREQ_PARQUET = {s: CLEAN_DIR / f"atlas_freq_{s}.parquet" for s in STRATEGIES}
STRATEGY_SPIDX_PARQUET = {s: CLEAN_DIR / f"species_index_{s}.parquet" for s in STRATEGIES}

EOO_PARQUET = CLEAN_DIR / "species_eoo_polygons.parquet"
CLEAN_REPORT = CLEAN_DIR / "clean_report.json"

SYNTHETIC = {s: STRATEGY_SYNTH_FLAGS[s].exists() for s in STRATEGIES}
print(f"ROOT       = {ROOT}")
print(f"STRATEGIES = {STRATEGIES}")
print(f"NSIDES     = {NSIDES}")
print(f"YEAR_SPLIT = {YEAR_SPLIT} (>= modern, < historical)")
print(f"SYNTHETIC  = {SYNTHETIC}")

report: dict = {
    "written_on": date.today().isoformat(),
    "strategies": STRATEGIES,
    "year_split": YEAR_SPLIT,
    "synthetic_per_strategy": SYNTHETIC,
    "nsides": NSIDES,
    "iberia_bbox": {
        "lon": [IBERIA_LON_MIN, IBERIA_LON_MAX],
        "lat": [IBERIA_LAT_MIN, IBERIA_LAT_MAX],
    },
    "per_strategy": {},
}


# %% [markdown]
# ## Iberian HEALPix-NESTED cell sets at each Nside

# %%
def iberian_pix(depth: int, nside: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """All NESTED cells at `depth` whose centre lies in the Iberia bbox.

    Returns (pix, lon, lat) — each shape (n_cells,)."""
    pix_all = np.arange(12 * nside * nside, dtype=np.uint64)
    lon, lat = hp_nested.healpix_to_lonlat(pix_all, depth, ELLIPSOID)
    lon = np.where(lon > 180.0, lon - 360.0, lon)
    mask = (
        (lon >= IBERIA_LON_MIN) & (lon <= IBERIA_LON_MAX)
        & (lat >= IBERIA_LAT_MIN) & (lat <= IBERIA_LAT_MAX)
    )
    return (pix_all[mask].astype(np.int64),
            lon[mask].astype(np.float32),
            lat[mask].astype(np.float32))


IBERIA_PIX: dict[int, np.ndarray] = {}
IBERIA_LON: dict[int, np.ndarray] = {}
IBERIA_LAT: dict[int, np.ndarray] = {}
for nside in NSIDES:
    pix, lon, lat = iberian_pix(DEPTHS[nside], nside)
    IBERIA_PIX[nside] = pix
    IBERIA_LON[nside] = lon
    IBERIA_LAT[nside] = lat
    print(f"  nside={nside:>4}  (depth={DEPTHS[nside]}): "
          f"{len(pix):>7,} cells in Iberia bbox")

report["n_cells_per_nside"] = {n: int(len(IBERIA_PIX[n])) for n in NSIDES}


# %% [markdown]
# ## GBIF zip streaming reader
#
# Streams the SIMPLE_CSV inside a GBIF download zip (tab-separated) in 1 M-row
# chunks, NA-dropped on essentials and bbox-filtered, so the all-BoR allbor
# download (~50–65 M rows) never materialises in full.

# %%
GBIF_CHUNKSIZE = 1_000_000


def iter_gbif_chunks(zip_path: Path,
                     chunksize: int = GBIF_CHUNKSIZE) -> Iterator[pd.DataFrame]:
    """Yield NA-dropped, bbox-filtered chunks of a GBIF SIMPLE_CSV zip."""
    if not zip_path.exists():
        raise FileNotFoundError(
            f"Expected GBIF zip at {zip_path} — re-run "
            f"notebooks/01_data_download.py to populate it."
        )
    with zipfile.ZipFile(zip_path) as zf:
        candidates = [n for n in zf.namelist() if n.endswith(".csv")]
        if not candidates:
            raise RuntimeError(f"No CSV inside {zip_path}")
        with zf.open(candidates[0]) as src:
            reader = pd.read_csv(
                src, sep="\t",
                usecols=lambda c: c in {
                    "gbifID", "species", "decimalLatitude",
                    "decimalLongitude", "year", "basisOfRecord",
                    "countryCode",
                },
                dtype={"gbifID": "Int64", "year": "Int64",
                       "countryCode": "string"},
                chunksize=chunksize, on_bad_lines="skip",
            )
            for raw in reader:
                df = raw.dropna(
                    subset=["species", "decimalLatitude",
                            "decimalLongitude", "year"]
                )
                if df.empty:
                    continue
                lon = df["decimalLongitude"].astype(float)
                lat = df["decimalLatitude"].astype(float)
                in_bbox = (
                    (lon >= IBERIA_LON_MIN) & (lon <= IBERIA_LON_MAX)
                    & (lat >= IBERIA_LAT_MIN) & (lat <= IBERIA_LAT_MAX)
                )
                df = df.loc[in_bbox]
                if df.empty:
                    continue
                yield df.reset_index(drop=True)


# %% [markdown]
# ## Per-species EOO-hull helpers (historical / rangemap layer)

# %%
def species_hull(points: np.ndarray) -> Polygon:
    """Convex hull of a (lon, lat) point array with n<3 fallbacks."""
    if len(points) >= 3:
        hull = MultiPoint(points).convex_hull
        if hull.geom_type != "Polygon":
            hull = hull.buffer(0.05)
    elif len(points) == 2:
        from shapely.geometry import LineString
        hull = LineString(points).buffer(0.1)
    else:  # 1 point
        from shapely.geometry import Point
        hull = Point(points[0]).buffer(0.2)
    return hull


def hull_to_cells(hull: Polygon, depth: int) -> np.ndarray:
    """NESTED cell IDs covered by `hull` at `depth` via polygon_coverage."""
    exterior = np.asarray(hull.exterior.coords)[:, :2]
    if np.allclose(exterior[0], exterior[-1]):
        exterior = exterior[:-1]
    if len(exterior) < 3:
        return np.empty(0, dtype=np.int64)
    cell_ids, _, _ = hp_nested.polygon_coverage(
        exterior, depth, ellipsoid=ELLIPSOID, flat=True,
    )
    return np.asarray(cell_ids, dtype=np.int64)


def historical_cell_counts(species_hulls: dict[str, Polygon],
                           nside: int,
                           iberian_arr: np.ndarray) -> pd.DataFrame:
    """Per-cell count of species whose EOO hull covers the cell (Iberian only)."""
    depth = DEPTHS[nside]
    counts: dict[int, int] = {}
    for hull in species_hulls.values():
        cells = hull_to_cells(hull, depth)
        cells = cells[np.isin(cells, iberian_arr)]
        for c in cells:
            counts[int(c)] = counts.get(int(c), 0) + 1
    if not counts:
        return pd.DataFrame({"cell": [], "richness": []}, dtype=np.int64)
    return pd.DataFrame(
        {"cell": list(counts.keys()), "richness": list(counts.values())}
    ).astype({"cell": np.int64, "richness": np.int64})


# %% [markdown]
# ## Process each strategy (streaming)
#
# Per chunk, split modern/historical. Modern: per Nside, accumulate
# per-(cell, species_id) **record counts** (chunk-local `unique(..., return_counts)`,
# folded into a running list, summed once at the end). This keeps the
# frequency data the coverage estimator needs while bounding memory by the
# number of unique (cell, species) pairs.

# %%
all_eoo_records: list[dict] = []

for strategy in STRATEGIES:
    print(f"\n{'='*60}")
    print(f"=== Strategy: {strategy}  (synthetic={SYNTHETIC[strategy]}) ===")
    print(f"{'='*60}")
    zip_path = STRATEGY_ZIPS[strategy]
    nc_path = STRATEGY_RICHNESS_NC[strategy]

    # Per-strategy species -> small int ID.
    species_to_id: dict[str, int] = {}

    def _sid(sp: str) -> int:
        sid = species_to_id.get(sp)
        if sid is None:
            sid = len(species_to_id)
            species_to_id[sp] = sid
        return sid

    # Modern accumulator: per Nside, list of per-chunk (cell, sid, count) int64
    # arrays. Summed across chunks at end-of-stream.
    modern_counts: dict[int, list[np.ndarray]] = {n: [] for n in NSIDES}
    # Historical accumulator: per species, list of (lon, lat) point arrays.
    hist_pts: dict[str, list[np.ndarray]] = {}

    n_records_total = n_records_modern = n_records_historical = 0
    species_total: set[str] = set()
    species_modern: set[str] = set()
    species_historical: set[str] = set()
    year_min: int | None = None
    year_max: int | None = None

    for ci, chunk in enumerate(iter_gbif_chunks(zip_path), start=1):
        n_records_total += len(chunk)
        years = chunk["year"].astype(int).values
        cmin, cmax = int(years.min()), int(years.max())
        year_min = cmin if year_min is None else min(year_min, cmin)
        year_max = cmax if year_max is None else max(year_max, cmax)
        species_total.update(chunk["species"].unique().tolist())

        is_modern = years >= YEAR_SPLIT
        modern_chunk = chunk.loc[is_modern]
        hist_chunk = chunk.loc[~is_modern]
        n_records_modern += len(modern_chunk)
        n_records_historical += len(hist_chunk)

        if len(modern_chunk):
            species_modern.update(modern_chunk["species"].unique().tolist())
            mod_lon = modern_chunk["decimalLongitude"].astype(float).values
            mod_lat = modern_chunk["decimalLatitude"].astype(float).values
            mod_sp = modern_chunk["species"].values
            mod_sid = np.fromiter(
                (_sid(s) for s in mod_sp), dtype=np.int64, count=len(mod_sp),
            )
            for nside in NSIDES:
                cells = hp_nested.lonlat_to_healpix(
                    mod_lon, mod_lat, DEPTHS[nside], ELLIPSOID,
                ).astype(np.int64)
                pairs = np.column_stack([cells, mod_sid])
                # Per-chunk (cell, sid) -> record count (NOT deduped: we need
                # the abundance/frequency for coverage estimation).
                uniq, cnt = np.unique(pairs, axis=0, return_counts=True)
                modern_counts[nside].append(
                    np.column_stack([uniq, cnt.astype(np.int64)])
                )

        if len(hist_chunk):
            species_historical.update(hist_chunk["species"].unique().tolist())
            for sp, grp in hist_chunk.groupby("species", sort=False):
                pts = (grp[["decimalLongitude", "decimalLatitude"]]
                       .astype(float).values)
                hist_pts.setdefault(sp, []).append(pts)

        print(f"  chunk {ci:>3}: +{len(chunk):>8,} rows  "
              f"(modern +{len(modern_chunk):>8,}, hist +{len(hist_chunk):>7,})  "
              f"running total: {n_records_total:>11,}")

    print(f"\n  loaded     : {n_records_total:>10,} records, "
          f"{len(species_total)} species  (years {year_min}..{year_max})")
    print(f"  modern     : {n_records_modern:>10,} records, "
          f"{len(species_modern)} species  (>= {YEAR_SPLIT})")
    print(f"  historical : {n_records_historical:>10,} records, "
          f"{len(species_historical)} species  (< {YEAR_SPLIT})")

    strat_report: dict = {
        "synthetic": SYNTHETIC[strategy],
        "n_records_total": int(n_records_total),
        "n_species_total": int(len(species_total)),
        "n_records_modern": int(n_records_modern),
        "n_species_modern": int(len(species_modern)),
        "n_records_historical": int(n_records_historical),
        "n_species_historical": int(len(species_historical)),
        "year_min": int(year_min) if year_min is not None else None,
        "year_max": int(year_max) if year_max is not None else None,
    }

    # --- Per-species EOO hulls (historical) ---
    print(f"\n--- Building per-species EOO hulls (historical, {strategy}) ---")
    species_hulls: dict[str, Polygon] = {}
    n_species_eoo = len(hist_pts)
    for i, sp in enumerate(sorted(hist_pts.keys()), start=1):
        parts = hist_pts.pop(sp)
        pts = np.vstack(parts) if len(parts) > 1 else parts[0]
        hull = species_hull(pts)
        species_hulls[sp] = hull
        all_eoo_records.append({
            "strategy": strategy, "species": sp, "n_points": int(len(pts)),
            "hull_area_sqdeg": float(hull.area), "wkt": hull.wkt,
        })
        if i % 50 == 0 or i == n_species_eoo:
            print(f"  built hull {i:>4}/{n_species_eoo}  ({sp[:32]})")
    strat_report["n_species_with_eoo"] = int(n_species_eoo)

    # --- Persist the species_id -> species name map ---
    spidx_df = (pd.DataFrame(
        {"species_id": list(species_to_id.values()),
         "species": list(species_to_id.keys())})
        .sort_values("species_id").reset_index(drop=True))
    spidx_df.to_parquet(STRATEGY_SPIDX_PARQUET[strategy], index=False)
    print(f"  species index -> {STRATEGY_SPIDX_PARQUET[strategy].name} "
          f"({len(spidx_df)} species)")

    # --- Per-Nside richness NetCDF + per-cell atlas frequency parquet ---
    print(f"\n--- Cross-tabulating richness + frequency per Nside ({strategy}) ---")
    if nc_path.exists():
        nc_path.unlink()
    freq_frames: list[pd.DataFrame] = []
    strat_report["per_nside"] = {}
    for nside in NSIDES:
        iberian_pix_arr = IBERIA_PIX[nside]

        # Atlas: sum (cell, sid) counts across chunks, restrict to Iberian cells.
        parts = modern_counts[nside]
        if parts:
            stacked = np.vstack(parts) if len(parts) > 1 else parts[0]
            # Sum counts over duplicate (cell, sid) rows from different chunks.
            keys = stacked[:, :2]
            cnts = stacked[:, 2]
            uniq_keys, inv = np.unique(keys, axis=0, return_inverse=True)
            inv = np.asarray(inv).ravel()
            summed = np.zeros(len(uniq_keys), dtype=np.int64)
            np.add.at(summed, inv, cnts)
            cell_col, sid_col = uniq_keys[:, 0], uniq_keys[:, 1]
            in_iberia = np.isin(cell_col, iberian_pix_arr)
            cell_col, sid_col, summed = (cell_col[in_iberia],
                                         sid_col[in_iberia], summed[in_iberia])
        else:
            cell_col = np.empty(0, dtype=np.int64)
            sid_col = np.empty(0, dtype=np.int64)
            summed = np.empty(0, dtype=np.int64)
        # Free per-Nside memory.
        modern_counts[nside] = []

        # Frequency table (the sample-abundance input to the coverage estimator).
        freq_frames.append(pd.DataFrame({
            "nside": np.full(len(cell_col), nside, dtype=np.int32),
            "cell": cell_col.astype(np.int64),
            "species_id": sid_col.astype(np.int64),
            "count": summed.astype(np.int64),
        }))

        # Atlas richness = distinct species per cell.
        if len(cell_col):
            uc, rc = np.unique(cell_col, return_counts=True)
            atlas_rich = pd.Series(rc, index=uc)
        else:
            atlas_rich = pd.Series(dtype=np.int64)

        # Rangemap richness from EOO hulls.
        hist = historical_cell_counts(species_hulls, nside, iberian_pix_arr)
        hist_rich = hist.set_index("cell")["richness"] if len(hist) else pd.Series(dtype=np.int64)

        df = pd.DataFrame({"cell": iberian_pix_arr}).set_index("cell")
        df["richness_atlas"] = atlas_rich.reindex(df.index, fill_value=0).astype(np.int32)
        df["richness_rangemap"] = hist_rich.reindex(df.index, fill_value=0).astype(np.int32)
        df["lon"] = IBERIA_LON[nside]
        df["lat"] = IBERIA_LAT[nside]

        n_cells = len(df)
        mean_a = float(df["richness_atlas"].mean())
        mean_r = float(df["richness_rangemap"].mean())
        print(f"  nside={nside:>4}  n_cells={n_cells:>6,}  "
              f"mean richness atlas={mean_a:5.2f}, rangemap={mean_r:5.2f}  "
              f"freq-rows={len(cell_col):>7,}")
        strat_report["per_nside"][nside] = {
            "n_cells": int(n_cells),
            "mean_richness_atlas": round(mean_a, 3),
            "mean_richness_rangemap": round(mean_r, 3),
            "n_freq_rows": int(len(cell_col)),
        }

        ds = xr.Dataset(
            data_vars={
                "richness_atlas": (
                    ("cell",), df["richness_atlas"].values,
                    {"long_name": "Per-cell species richness from modern "
                                  "(year>=2000) GBIF occurrences (atlas-equivalent)",
                     "units": "n_species", "strategy": strategy,
                     "synthetic": str(SYNTHETIC[strategy])}),
                "richness_rangemap": (
                    ("cell",), df["richness_rangemap"].values,
                    {"long_name": "Per-cell species richness from historical "
                                  "(year<2000) EOO convex-hull coverage (range-map-equivalent)",
                     "units": "n_species", "strategy": strategy,
                     "synthetic": str(SYNTHETIC[strategy])}),
            },
            coords={
                "cell": ("cell", df.index.values.astype(np.int64),
                         {"long_name": f"HEALPix NESTED pixel index (nside={nside})"}),
                "lon": ("cell", df["lon"].values, {"units": "degrees_east"}),
                "lat": ("cell", df["lat"].values, {"units": "degrees_north"}),
            },
            attrs={
                "nside": nside, "depth": DEPTHS[nside], "ellipsoid": ELLIPSOID,
                "healpix_ordering": "NESTED", "strategy": strategy,
                "synthetic": str(SYNTHETIC[strategy]), "year_split": YEAR_SPLIT,
            },
        )
        ds.to_netcdf(
            nc_path, mode="a" if nc_path.exists() else "w",
            group=f"nside_{nside}", engine="netcdf4",
            encoding={"richness_atlas": {"zlib": True, "complevel": 4},
                      "richness_rangemap": {"zlib": True, "complevel": 4}},
        )

    # Persist the per-cell atlas frequency table (all Nsides, long-form).
    freq_df = pd.concat(freq_frames, ignore_index=True)
    freq_df.to_parquet(STRATEGY_FREQ_PARQUET[strategy], index=False)
    size_mb = nc_path.stat().st_size / 1e6
    print(f"\n  saved {nc_path}  ({size_mb:.2f} MB)")
    print(f"  saved {STRATEGY_FREQ_PARQUET[strategy].name} "
          f"({len(freq_df):,} (nside,cell,species) rows)")
    strat_report["richness_nc"] = str(nc_path.relative_to(ROOT))
    strat_report["atlas_freq_parquet"] = str(STRATEGY_FREQ_PARQUET[strategy].relative_to(ROOT))
    report["per_strategy"][strategy] = strat_report


# %% [markdown]
# ## Persist per-strategy EOO polygons + clean report

# %%
eoo_df = pd.DataFrame(all_eoo_records)
eoo_df.to_parquet(EOO_PARQUET, index=False)
print(f"\nsaved {EOO_PARQUET} "
      f"({len(eoo_df)} species-rows across "
      f"{eoo_df['strategy'].nunique() if len(eoo_df) else 0} strategies)")

with open(CLEAN_REPORT, "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\n--- Clean report -> {CLEAN_REPORT}")
print(json.dumps(report, indent=2, default=str))
