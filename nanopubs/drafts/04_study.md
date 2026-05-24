# 04 — FORRT Replication Study

> Pre-flight (per `docs/forrt-form-fields.md` § FORRT Replication Study): fields
> in form order are (1) Short URI suffix for study ID [required], (2) Label/name
> [required], (3) Study type [required], (4) Search for a FORRT claim
> [required], (5) what part is reproduced/replicated [required, = scope],
> (6) how is reproduced/replicated [required, = method], (7) deviations from
> original methodology [optional], (8) Search keywords Wikidata [optional],
> (9) Search discipline Wikidata [optional]. Enumerated below in order.
>
> Method drafted from `notebooks/03_analysis.py` (verified, not inferred).
> Layer discipline (`docs/pico-study-outcome-levels.md`): scope ≠ method ≠
> results. No result numbers below — config values only.

## Field-by-field draft

### Short URI suffix for study ID (text input, required)

```
coverage-correction-iberian-birds-study
```

### Label/name of replication study (text input, required)

```
Coverage-based effort correction of Iberian-bird richness hotspots (HEALPix-NESTED)
```

### Study type (dropdown, required)

D2: a new method (effort correction) applied to the same system as the sibling
chain — different methodology, so a Replication Study.

- [ ] Reproduction Study — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] Reproduction/Replication Study — both.

### Search for a FORRT claim (search/select, required)

URI of the Claim published in step 03.

```
<PENDING — paste the step-03 Claim RA… URI from nanopubs/PUBLISHED.md>
```

### Describe what part of the claim is reproduced/replicated (textarea, required)

**Scope** — which aspect is tested; no method, no results.

```
Scope: whether standardising per-cell sample completeness removes observer-effort distortion of biodiversity-hotspot identity. The study tests whether coverage-standardising modern occurrence-derived per-cell bird richness makes the top-richest-cells ("hotspot") set agree with the hotspot set derived from an expert rangemap, in the same Iberian-bird, equal-area HEALPix system as the prior scale-dependence chain.

In scope: the top-5% richest-cells hotspot definition; the symmetric set non-overlap between the occurrence-derived hotspot set and the expert-rangemap-derived hotspot set; how that non-overlap changes when occurrence richness is coverage-standardised rather than left raw; both basis-of-record strategies (museum-grade specimens/sensors vs all observations including citizen science); the EU Article 12 expert polygons as the gold-standard rangemap comparator, with the historical occurrence-hull rangemap as a secondary comparator.

Out of scope: the scale-dependence-across-resolutions question itself (that is the prior chain's claim, which this study takes as given); non-bird taxa; regions outside the Iberian peninsula; and any correction of the rangemap layer (only the occurrence/atlas layer is corrected).
```

### Describe how the claim is reproduced/replicated (textarea, required)

**Method** in plain prose; configuration values allowed, result numbers not.

```
Iberian bird occurrences (Spain, Portugal, Andorra, Gibraltar) are taken from GBIF under two basis-of-record strategies with the prior chain's existing download DOIs (museum: PRESERVED_SPECIMEN + MACHINE_OBSERVATION, 10.15468/dl.r8pcat; all-observations: additionally HUMAN_OBSERVATION, 10.15468/dl.e9xv7p), and binned onto a HEALPix-NESTED ladder (Nside 16, 32, 64, 128, 256, 512) using the geographic, WGS84-aware healpix-geo library, NESTED ordering throughout. Records are year-split at 2000: post-2000 form the occurrence/atlas layer, pre-2000 the per-species convex-hull rangemap layer.

For each cell, the per-species record-count vector is retained. Coverage-based rarefaction (Chao & Jost 2012) is applied per cell: sample coverage is estimated with the bias-corrected Good–Turing estimator; per-cell richness is then standardised to a common target sample coverage C* by size-based rarefaction (inverting the rarefied-sample coverage curve) where C* is at or below the cell's observed coverage, and by coverage-based extrapolation (Chao1 undetected-species term) where C* exceeds it. Cells with too few records for a stable coverage estimate are censored. The target coverage C* is swept over a grid (0.80, 0.90, 0.95, 0.99) plus the minimum common coverage Cmin, rather than fixed at one value.

At each (strategy, Nside, C*), the top-5% richest cells of the coverage-standardised surface are recomputed and their symmetric set non-overlap ("misidentification") is measured against (a) the EU Birds Directive Article 12 expert distribution polygons (EEA 2013–2018, 10 km grid, reprojected to WGS84, matched to the species intersection) and (b) the pre-2000 occurrence-hull rangemap. The uncorrected raw-richness surface is computed identically as the baseline. The full pipeline is a Snakemake workflow (download → clean → analysis → figures) reproducible from a fresh checkout; the coverage estimators are validated standalone.
```

### Describe any deviations from original methodology (textarea, optional)

```
Chao & Jost (2012) introduce coverage-based rarefaction for comparing whole-community samples by completeness. This study deviates by applying their estimator at a new unit of analysis — the individual HEALPix-NESTED grid cell as a "sample" — to correct a spatial biodiversity-hotspot comparison, an application the methods paper does not itself perform. Relative to the prior sibling chain (Hurlbert & Jetz 2007 scale-dependence replication), this study reuses that chain's GBIF download DOIs, Iberian study system, HEALPix-NESTED substrate, year-split, top-5% hotspot definition, and Article 12 comparator unchanged, and adds the coverage-correction layer plus the target-coverage sweep as the new method. The estimator can only be evaluated on cells with enough records, so effort-poor cells are necessarily censored; the consequence of that censoring for the comparison is reported in the linked Outcome's limitations.
```

### Search keywords (Wikidata) (multi-select, optional)

Provide labels (not QIDs) — pick matches from the Wikidata search:

```
species richness; biodiversity hotspot; rarefaction; sampling bias; GBIF; HEALPix
```

### Search discipline (Wikidata) (search, optional)

```
macroecology; biodiversity informatics; biogeography
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
