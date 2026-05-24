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
# # 03 — Analysis: coverage-based effort correction of richness hotspots
#
# **The new science of this replication.** The sibling chain
# (`sdm-scale-replication`) showed that raw per-cell GBIF richness hotspots are
# inflated by observer effort: effort-rich cells (cities, accessible reserves)
# are sampled to far higher *completeness* than effort-poor cells, so comparing
# raw richness is exactly the equal-*size* comparison Chao & Jost (2012,
# DOI 10.1890/11-1952.1) warn against. Here we standardise every cell to a
# common **sample coverage** Ĉ — coverage-based rarefaction — and re-measure
# how well the corrected hotspots agree with (a) the historical EOO-hull
# rangemap and (b) the EU Article 12 expert-rangemap gold standard.
#
# Per the locked design decisions (`nanopubs/drafts/00_design_decisions.md`):
#
# - **D7** — sweep a *range* of target coverage C*, not a single value, plus the
#   minimum-common-coverage Cmin and an "uncorrected" baseline (raw richness).
# - **D8** — both `museum` and `allbor` basis-of-record strategies.
# - **D9** — report both (a) the reduction in hotspot misidentification vs the
#   uncorrected baseline and (b) whether corrected misidentification reaches the
#   Hurlbert & Jetz 47.8–68.6 % reference range.
#
# ## Estimators (faithful to Chao & Jost 2012 / Chao et al. 2014 iNEXT)
#
# For a cell with abundance vector {X_i} (per-species record counts),
# n = Σ X_i total records, f_k = #species with exactly k records:
#
# - **Sample coverage of the full sample** (bias-corrected Good–Turing; Chao &
#   Jost 2012 Eq. 4a):
#       Ĉ_n = 1 − (f1/n)·A,   A = (n−1)f1 / [(n−1)f1 + 2 f2]   (f2>0)
#   with the f2=0 variant A = (n−1)(f1−1) / [(n−1)(f1−1) + 2].
# - **Size-based rarefaction richness** (Hurlbert 1971 / Good 1953), m ≤ n:
#       Ŝ(m) = Σ_i [ 1 − C(n−X_i, m)/C(n, m) ].
# - **Rarefied-sample coverage curve** (consistent with Ĉ_n at m=n):
#       Ĉ(m) = 1 − Σ_i (X_i/n)·[ C(n−X_i, m−1)/C(n−1, m−1) ].
# - **Coverage-based extrapolation** beyond the observed sample (Chao et al.
#   2014, abundance case), with Chao1 undetected richness
#       f0 = ((n−1)/n)·f1²/(2 f2)   (f2>0)  |  ((n−1)/n)·f1(f1−1)/2  (f2=0):
#       Ŝ(n+m*) = S_obs + f0·[1 − (1 − f1/(n·f0 + f1))^{m*}]
#       Ĉ(n+m*) = 1 − (f1/n)·A^{m*+1}.
#   To hit a target coverage C* > Ĉ_n we invert the coverage equation for m*.
#
# Binomial ratios are computed in log-space via `scipy.special.gammaln` for
# numerical stability.

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.special import gammaln

# %% [markdown]
# ## Constants and paths

# %%
STRATEGIES = ["museum", "allbor"]
NSIDES = [16, 32, 64, 128, 256, 512]
HOTSPOT_FRACTION = 0.05          # H&J 2007: top-5 % richest cells.
HEADLINE_NSIDE = 256             # ≈ 25 km, the 0.25° H&J reference scale.

# Target sample-coverage sweep (D7). Cmin (per strategy×nside) is appended at
# runtime; "uncorrected" (raw richness, no standardisation) is the baseline.
TARGET_COVERAGES = [0.80, 0.90, 0.95, 0.99]

# Uncorrected baselines from the sibling Replication Outcome (Nside 256).
HJ_BASELINE = {"museum": 89.9, "allbor": 97.8}
# Hurlbert & Jetz 2007 reference range (Australia / Southern Africa, 0.25°).
HJ_RANGE = (47.8, 68.6)

# A cell needs a minimum number of records for a meaningful coverage estimate.
MIN_CELL_RECORDS = 5

ROOT = Path("..").resolve()
DATA = ROOT / "data"
CLEAN_DIR = DATA / "clean"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Article 12 GPKG (optional; the vs-Art-12 comparison is skipped if absent).
ART12_GPKG = (DATA / "external" / "art12" /
              "ART12_3035_distribution_data_without_sensitive.gpkg")
ART12_LAYER = "EU_ART12_birds_distribution_2013_2018_without_sensitive_species"
IBERIA_COUNTRIES = {"ES", "PT", "GIB"}
ELLIPSOID = "WGS84"
DEPTHS = {n: int(np.log2(n)) for n in NSIDES}

STRATEGY_RICHNESS_NC = {s: CLEAN_DIR / f"richness_{s}.nc" for s in STRATEGIES}
STRATEGY_FREQ_PARQUET = {s: CLEAN_DIR / f"atlas_freq_{s}.parquet" for s in STRATEGIES}
STRATEGY_SPIDX_PARQUET = {s: CLEAN_DIR / f"species_index_{s}.parquet" for s in STRATEGIES}

OUT_PARQUET = RESULTS_DIR / "coverage_correction.parquet"
OUT_HEADLINE = RESULTS_DIR / "headline.json"

print(f"STRATEGIES        = {STRATEGIES}")
print(f"TARGET_COVERAGES  = {TARGET_COVERAGES} (+ Cmin + uncorrected)")
print(f"HEADLINE_NSIDE    = {HEADLINE_NSIDE}")
print(f"Article 12 GPKG   = {ART12_GPKG}  (exists={ART12_GPKG.exists()})")


# %% [markdown]
# ## Coverage estimator + coverage-based rarefaction / extrapolation

# %%
def _log_binom(a: np.ndarray | float, b: int) -> np.ndarray:
    """log C(a, b) via gammaln; -inf where a < b (i.e. C=0)."""
    a = np.asarray(a, dtype=float)
    out = np.full_like(a, -np.inf)
    ok = a >= b
    out[ok] = (gammaln(a[ok] + 1.0) - gammaln(b + 1.0)
               - gammaln(a[ok] - b + 1.0))
    return out


def sample_coverage(X: np.ndarray) -> float:
    """Bias-corrected Good–Turing full-sample coverage Ĉ_n (Chao & Jost Eq. 4a)."""
    n = int(X.sum())
    if n <= 1:
        return float("nan")
    f1 = int((X == 1).sum())
    f2 = int((X == 2).sum())
    if f1 == 0:
        return 1.0
    if f2 > 0:
        A = (n - 1) * f1 / ((n - 1) * f1 + 2 * f2)
    else:
        A = (n - 1) * (f1 - 1) / ((n - 1) * (f1 - 1) + 2)
    return 1.0 - (f1 / n) * A


def rarefied_richness(X: np.ndarray, m: float) -> float:
    """Expected species in a size-`m` subsample, Ŝ(m) (Hurlbert/Good)."""
    n = int(X.sum())
    if m <= 0:
        return 0.0
    if m >= n:
        return float((X > 0).sum())
    # Ŝ(m) = Σ_i [1 − C(n−X_i, m)/C(n, m)]. Interpolate non-integer m linearly.
    if float(m).is_integer():
        mm = int(m)
        log_ratio = _log_binom(n - X, mm) - _log_binom(n, mm)
        return float(np.sum(1.0 - np.exp(log_ratio)))
    lo, hi = int(np.floor(m)), int(np.ceil(m))
    s_lo = rarefied_richness(X, lo)
    s_hi = rarefied_richness(X, hi)
    return s_lo + (s_hi - s_lo) * (m - lo)


def rarefied_coverage(X: np.ndarray, m: int) -> float:
    """Expected coverage of a size-`m` subsample, Ĉ(m)."""
    n = int(X.sum())
    if m <= 0:
        return 0.0
    if m >= n:
        return sample_coverage(X)
    # Ĉ(m) = 1 − Σ_i (X_i/n)·C(n−X_i, m−1)/C(n−1, m−1).
    log_ratio = _log_binom(n - X, m - 1) - _log_binom(n - 1, m - 1)
    return float(1.0 - np.sum((X / n) * np.exp(log_ratio)))


def _f0_chao1(n: int, f1: int, f2: int) -> float:
    """Chao1 estimate of undetected species f0."""
    if f1 == 0:
        return 0.0
    if f2 > 0:
        return (n - 1) / n * f1 * f1 / (2.0 * f2)
    return (n - 1) / n * f1 * (f1 - 1) / 2.0


def extrapolated_richness_at_coverage(X: np.ndarray, target_C: float) -> float:
    """Coverage-based extrapolation Ŝ at target_C > observed coverage."""
    n = int(X.sum())
    s_obs = int((X > 0).sum())
    f1 = int((X == 1).sum())
    f2 = int((X == 2).sum())
    if f1 == 0:
        return float(s_obs)  # sample already saturated; nothing to extrapolate.
    A = ((n - 1) * f1 / ((n - 1) * f1 + 2 * f2) if f2 > 0
         else (n - 1) * (f1 - 1) / ((n - 1) * (f1 - 1) + 2))
    if A <= 0 or A >= 1:
        return float(s_obs)
    # Invert Ĉ(n+m*) = 1 − (f1/n)·A^{m*+1} for m*.
    rhs = (1.0 - target_C) * n / f1
    if rhs <= 0:
        return float("nan")
    m_star = np.log(rhs) / np.log(A) - 1.0
    if not np.isfinite(m_star) or m_star <= 0:
        return float(s_obs)
    f0 = _f0_chao1(n, f1, f2)
    if f0 <= 0:
        return float(s_obs)
    return float(s_obs + f0 * (1.0 - (1.0 - f1 / (n * f0 + f1)) ** m_star))


def richness_at_coverage(X: np.ndarray, target_C: float) -> float:
    """Coverage-standardised richness at target_C (rarefy or extrapolate)."""
    n = int(X.sum())
    if n < MIN_CELL_RECORDS:
        return float("nan")
    c_n = sample_coverage(X)
    if not np.isfinite(c_n):
        return float("nan")
    if target_C <= c_n:
        # Rarefaction: binary-search integer m bracketing target_C, interpolate.
        lo, hi = 1, n
        c_lo, c_hi = rarefied_coverage(X, lo), rarefied_coverage(X, hi)
        if target_C <= c_lo:
            return rarefied_richness(X, lo)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            c_mid = rarefied_coverage(X, mid)
            if c_mid < target_C:
                lo, c_lo = mid, c_mid
            else:
                hi, c_hi = mid, c_mid
        # Linear interpolation in coverage between m=lo and m=hi.
        if c_hi == c_lo:
            m_star = float(hi)
        else:
            m_star = lo + (target_C - c_lo) / (c_hi - c_lo)
        return rarefied_richness(X, m_star)
    return extrapolated_richness_at_coverage(X, target_C)


# %% [markdown]
# ## Hotspot overlap helper (top-5 % symmetric non-overlap = "misidentification")

# %%
def top_k_set(richness: np.ndarray, fraction: float = HOTSPOT_FRACTION) -> set[int]:
    """Positions of the top-`fraction` cells by richness (NaN-safe)."""
    valid = np.where(np.isfinite(richness))[0]
    if len(valid) == 0:
        return set()
    vals = richness[valid]
    top_k = max(1, int(np.ceil(fraction * len(valid))))
    sel = valid[np.argpartition(vals, -top_k)[-top_k:]]
    return set(int(i) for i in sel)


def misidentified_pct(atlas: np.ndarray, rangemap: np.ndarray) -> float:
    """Symmetric set non-overlap (%) of the top-5 % atlas vs rangemap hotspots."""
    atl = top_k_set(atlas)
    rm = top_k_set(rangemap)
    union = atl | rm
    inter = atl & rm
    if not union:
        return float("nan")
    return (len(union) - len(inter)) / len(union) * 100.0


# %% [markdown]
# ## Build per-cell abundance vectors from the atlas frequency table

# %%
def cell_abundances(freq: pd.DataFrame, nside: int) -> dict[int, np.ndarray]:
    """{cell_id -> per-species record-count vector} for one Nside."""
    sub = freq[freq["nside"] == nside]
    out: dict[int, np.ndarray] = {}
    for cell, grp in sub.groupby("cell", sort=False):
        out[int(cell)] = grp["count"].to_numpy(dtype=np.int64)
    return out


def corrected_atlas_surface(abund: dict[int, np.ndarray],
                            cells: np.ndarray,
                            target_C: float | None) -> np.ndarray:
    """Per-cell coverage-corrected richness aligned to `cells`.

    target_C=None -> uncorrected raw richness (distinct species per cell)."""
    out = np.full(len(cells), np.nan, dtype=float)
    idx = {int(c): i for i, c in enumerate(cells)}
    for cell, X in abund.items():
        i = idx.get(int(cell))
        if i is None:
            continue
        out[i] = float((X > 0).sum()) if target_C is None \
            else richness_at_coverage(X, target_C)
    return out


# %% [markdown]
# ## Optional: Article 12 expert-rangemap per-cell richness
#
# Loaded only if the GPKG is present (real-data runs). On synthetic / fresh
# checkouts the vs-Art-12 columns are NaN and the pipeline still completes.

# %%
def load_art12_richness() -> dict[tuple[str, int], np.ndarray] | None:
    """{(strategy, nside) -> per-cell Art-12 matched-subset richness} or None."""
    if not ART12_GPKG.exists():
        print("Article 12 GPKG absent — vs-Art-12 comparison skipped (NaN).")
        return None
    import pyogrio
    from healpix_geo import nested as hp_nested

    where = f"country IN ({','.join(repr(c) for c in IBERIA_COUNTRIES)})"
    art12 = pyogrio.read_dataframe(ART12_GPKG, layer=ART12_LAYER, where=where)
    art12 = art12.to_crs("EPSG:4326")
    rep = art12.geometry.representative_point()
    art12 = art12.assign(lon=rep.x, lat=rep.y)
    art12_species = set(art12["speciesnameEU"].dropna().unique().tolist())
    print(f"Article 12: {len(art12):,} Iberian cells, "
          f"{len(art12_species)} species.")

    result: dict[tuple[str, int], np.ndarray] = {}
    for s in STRATEGIES:
        spidx = pd.read_parquet(STRATEGY_SPIDX_PARQUET[s])
        atlas_species = set(spidx["species"].tolist())
        matched = atlas_species & art12_species
        sub = art12[art12["speciesnameEU"].isin(matched)]
        lons = sub["lon"].to_numpy(float)
        lats = sub["lat"].to_numpy(float)
        sp = sub["speciesnameEU"].to_numpy()
        sp_id = {name: i for i, name in enumerate(sorted(matched))}
        sid = np.fromiter((sp_id[x] for x in sp), dtype=np.int64, count=len(sp))
        for nside in NSIDES:
            with xr.open_dataset(STRATEGY_RICHNESS_NC[s],
                                 group=f"nside_{nside}") as ds:
                cells = ds["cell"].values.astype(np.int64)
            hp_cells = hp_nested.lonlat_to_healpix(
                lons, lats, DEPTHS[nside], ELLIPSOID).astype(np.int64)
            keep = np.isin(hp_cells, cells)
            rich = pd.Series(0, index=cells, dtype=np.int64)
            if keep.any():
                pairs = np.unique(
                    np.column_stack([hp_cells[keep], sid[keep]]), axis=0)
                uc, cnt = np.unique(pairs[:, 0], return_counts=True)
                rich.loc[uc] = cnt
            result[(s, nside)] = rich.to_numpy()
        print(f"  {s}: {len(matched)} matched species vs Art-12.")
    return result


# %% [markdown]
# ## Main sweep: (strategy × nside × target coverage)

# %%
art12_rich = load_art12_richness()

rows: list[dict] = []
for strategy in STRATEGIES:
    freq = pd.read_parquet(STRATEGY_FREQ_PARQUET[strategy])
    print(f"\n{'='*60}\n=== {strategy} ===\n{'='*60}")
    for nside in NSIDES:
        with xr.open_dataset(STRATEGY_RICHNESS_NC[strategy],
                             group=f"nside_{nside}") as ds:
            cells = ds["cell"].values.astype(np.int64)
            rangemap = ds["richness_rangemap"].values.astype(float)
            synthetic = str(ds.attrs.get("synthetic", "?"))
        abund = cell_abundances(freq, nside)

        # Per-cell observed coverage, to define Cmin for this strategy×nside.
        observed_cov = [sample_coverage(X) for X in abund.values()
                        if X.sum() >= MIN_CELL_RECORDS]
        observed_cov = [c for c in observed_cov if np.isfinite(c)]
        cmin = float(np.min(observed_cov)) if observed_cov else float("nan")

        art12_layer = art12_rich.get((strategy, nside)) if art12_rich else None

        # Sweep: uncorrected baseline, then each target coverage, then Cmin.
        sweep: list[tuple[str, float | None]] = [("uncorrected", None)]
        sweep += [("fixed", c) for c in TARGET_COVERAGES]
        if np.isfinite(cmin):
            sweep.append(("cmin", cmin))

        for kind, target_C in sweep:
            atlas = corrected_atlas_surface(abund, cells, target_C)
            mis_rm = misidentified_pct(atlas, rangemap)
            mis_a12 = (misidentified_pct(atlas, art12_layer.astype(float))
                       if art12_layer is not None else float("nan"))
            n_censored = int(np.isnan(atlas).sum()) if target_C is not None else 0
            rows.append({
                "strategy": strategy, "nside": nside,
                "target_coverage_kind": kind,
                "target_coverage": (round(target_C, 4)
                                    if target_C is not None else np.nan),
                "misidentified_pct_vs_rangemap": (round(mis_rm, 2)
                                                  if np.isfinite(mis_rm) else np.nan),
                "misidentified_pct_vs_art12": (round(mis_a12, 2)
                                               if np.isfinite(mis_a12) else np.nan),
                "n_cells": int(len(cells)),
                "n_cells_censored": n_censored,
                "cmin": round(cmin, 4) if np.isfinite(cmin) else np.nan,
                "synthetic": synthetic,
            })
            mis_a12_str = f"{mis_a12:6.2f}" if np.isfinite(mis_a12) else "   nan"
            label = kind if target_C is None else f"{kind} C*={target_C:.3f}"
            print(f"  nside={nside:>4}  {label:<16}  "
                  f"misid vs rangemap={mis_rm:6.2f}%  "
                  f"vs art12={mis_a12_str}  censored={n_censored}")

corr_df = pd.DataFrame(rows)
corr_df.to_parquet(OUT_PARQUET, index=False)
print(f"\nsaved {OUT_PARQUET}  ({len(corr_df)} rows)")


# %% [markdown]
# ## Headline JSON — D9 verdict inputs at the reference scale (Nside 256)
#
# For each strategy: uncorrected baseline vs best corrected misidentification,
# the reduction (percentage points), and whether the corrected number reaches
# the Hurlbert & Jetz 47.8–68.6 % reference band.

# %%
headline: dict = {
    "headline_nside": HEADLINE_NSIDE,
    "hotspot_fraction": HOTSPOT_FRACTION,
    "hj_reference_range_pct": list(HJ_RANGE),
    "hj_baseline_sibling_pct": HJ_BASELINE,
    "per_strategy": {},
}
ref = corr_df[corr_df["nside"] == HEADLINE_NSIDE]
for strategy in STRATEGIES:
    sub = ref[ref["strategy"] == strategy]
    if sub.empty:
        continue
    base = sub[sub["target_coverage_kind"] == "uncorrected"]
    corrected = sub[sub["target_coverage_kind"] != "uncorrected"]
    # Prefer the Art-12 comparator when available (D9 target); else rangemap.
    metric = "misidentified_pct_vs_rangemap"
    if art12_rich is not None and corrected["misidentified_pct_vs_art12"].notna().any():
        metric = "misidentified_pct_vs_art12"
    base_val = float(base[metric].iloc[0]) if len(base) and pd.notna(base[metric].iloc[0]) else np.nan
    best_idx = corrected[metric].idxmin() if corrected[metric].notna().any() else None
    best = corrected.loc[best_idx] if best_idx is not None else None
    best_val = float(best[metric]) if best is not None else np.nan
    reduction = (base_val - best_val) if np.isfinite(base_val) and np.isfinite(best_val) else np.nan
    reaches = bool(HJ_RANGE[0] <= best_val <= HJ_RANGE[1]) if np.isfinite(best_val) else False
    below_top = bool(best_val <= HJ_RANGE[1]) if np.isfinite(best_val) else False
    headline["per_strategy"][strategy] = {
        "comparator": metric,
        "uncorrected_misidentified_pct": round(base_val, 2) if np.isfinite(base_val) else None,
        "best_corrected_misidentified_pct": round(best_val, 2) if np.isfinite(best_val) else None,
        "best_corrected_at": (None if best is None else {
            "kind": best["target_coverage_kind"],
            "target_coverage": (None if pd.isna(best["target_coverage"])
                                else float(best["target_coverage"]))}),
        "reduction_pp_vs_uncorrected": round(reduction, 2) if np.isfinite(reduction) else None,
        "reaches_hj_range": reaches,
        "at_or_below_hj_upper": below_top,
        "synthetic": str(sub["synthetic"].iloc[0]),
    }

with open(OUT_HEADLINE, "w") as f:
    json.dump(headline, f, indent=2, default=str)
print(f"\nsaved {OUT_HEADLINE}")
print(json.dumps(headline, indent=2, default=str))
