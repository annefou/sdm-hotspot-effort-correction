# 05 — FORRT Replication Outcome

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> Numbers below are read directly from `results/headline.json` +
> `results/coverage_correction.parquet` of the **real-data** run (2026-05-24;
> museum ≈ 1.0 M GBIF records / 452 species, allbor ≈ 61.7 M records / 964
> species; synthetic flag = False). The chain-reference field (Study URI) is
> filled in Phase 5 once step 04 is published.

## Field-by-field draft

### Short URI suffix for outcome ID (text input, required)

```
coverage-correction-does-not-restore-hotspot-agreement
```

### Plain-text label for the outcome (text input, required)

```
Coverage-based rarefaction does not restore agreement between GBIF richness hotspots and the EU Article 12 expert-rangemap gold standard (Iberian birds, HEALPix-NESTED)
```

### Search for a FORRT replication study (search/select, required)

URI of the Replication Study published in step 04. Pull from `nanopubs/PUBLISHED.md`.

```
<PENDING — published in Phase 5 as step 04; paste its RA… URI here>
```

### Repository URL (text input, required)

```
https://github.com/annefou/sdm-hotspot-effort-correction
```

### Completion date (date picker, required)

```
2026-05-24
```

### Validation status (dropdown, required)

- [ ] Validated
- [ ] PartiallySupported
- [x] **Contradicted**

The claim under test is the *correction hypothesis* — that coverage-based
rarefaction restores agreement between occurrence-derived hotspots and the
expert-rangemap gold standard. The data contradict it. **Note on the chain
CiTO (step 06):** the template's default Contradicted→`disputes` mapping does
**not** apply here. Per design decision D4 the apex CiTO `cito:extends` the
sibling chain's Replication Outcome (`RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI`):
this negative result *reinforces and extends* the sibling's finding that the
bias lives on the observer-effort/atlas axis, by showing it survives a standard
completeness correction. It disputes the correction hypothesis while extending
the prior bias finding — set the CiTO relation manually to `extends`.

### Confidence level (dropdown, required)

```
HighConfidence
```

Strong evidence against the correction hypothesis: the null effect is robust
across the full target-coverage sweep (C* = 0.80–0.99 and Cmin) and both
basis-of-record strategies, and the uncorrected baselines reproduce the sibling
chain's published numbers (museum 89.9 %, allbor 97.8 % vs the EOO-hull
rangemap), anchoring the comparison.

### Describe the overall conclusion about the original claim (textarea, required)

```
Coverage-based rarefaction (Chao & Jost 2012) does NOT restore agreement between modern GBIF occurrence richness hotspots and the EU Article 12 expert-rangemap gold standard for Iberian birds. At the Hurlbert & Jetz reference scale (HEALPix-NESTED Nside 256, ≈ 25 km), standardising every cell to a common sample coverage leaves the top-5 % hotspot misidentification (symmetric set non-overlap vs the Article 12 expert polygons) at its best 87.4 % for the all-observations strategy and 96.6 % for the museum strategy, versus uncorrected baselines of 88.7 % and 94.2 % — a change of +1.3 and −2.4 percentage points respectively. Neither corrected value comes anywhere near the 47.8–68.6 % Hurlbert & Jetz reference range; the correction moves museum the wrong way. Standardising per-cell sample completeness does not remove the observer-effort distortion of which cells rank as biodiversity hotspots, because that distortion is a spatial sampling-location bias (where observers go versus where birds are biologically densest), not a per-cell completeness artefact that coverage standardisation can rescale away.
```

### Describe the evidence that supports your conclusion (textarea, required)

```
Headline scale, HEALPix-NESTED Nside 256 (≈ 25 km), top-5 % hotspots, symmetric set non-overlap ("misidentification").

Against the EU Article 12 expert-rangemap gold standard (the pre-registered comparator, D9):
- museum:  uncorrected 94.2 %  →  best coverage-corrected 96.6 % (at target coverage C* = 0.80); change −2.4 percentage points (worse). All swept C* (0.80, 0.90, 0.95, 0.99) and Cmin give 96.6–98.0 %.
- allbor:  uncorrected 88.7 %  →  best coverage-corrected 87.4 % (at C* = 0.80); change +1.3 percentage points. Swept values 87.4–90.5 %.
- Neither strategy reaches the Hurlbert & Jetz 47.8–68.6 % reference range at any sweep point.

Against the historical EOO-hull rangemap (secondary comparator; reproduces the sibling baseline):
- museum:  uncorrected 89.9 %  →  corrected 90.6–94.4 % (worse across the sweep).
- allbor:  uncorrected 98.2 %  →  corrected best 92.0 % at C* = 0.80 (a 6.2-percentage-point improvement) but still far above the reference range.

Baseline validation: the uncorrected EOO-hull numbers (museum 89.9 %, allbor 98.2 %) match the sibling chain's published Replication Outcome (89.9 % / 97.8 %), confirming the pipeline reproduces the prior result before the correction is applied.

Coverage-based rarefaction was implemented from Chao & Jost (2012): per-cell sample coverage via the bias-corrected Good–Turing estimator; size-based rarefaction (Hurlbert/Good) inverted to the target coverage; coverage-based extrapolation (Chao1 f0) where the target exceeds a cell's observed coverage. Estimators validated standalone (rarefaction monotone, Ĉ(n) self-consistent with the full-sample estimator). Sweep: target coverage C* ∈ {0.80, 0.90, 0.95, 0.99} plus the minimum common coverage Cmin, both strategies, full Nside ladder 16–512. See notebooks/03_analysis.py and results/coverage_correction.parquet.
```

### Describe what limits the conclusions of the study (textarea, optional)

```
1. Coverage standardisation can only be applied to cells with enough records for a coverage estimate (here, ≥ 5). At Nside 256 this censors 698 of 1849 cells (38 %) for the museum strategy and 489 (26 %) for allbor. The censored cells are predominantly the effort-poor ones — exactly the under-sampled, potentially biologically-rich cells whose absence drives the hotspot mismatch. Coverage-based rarefaction therefore structurally cannot recover the hotspot status of cells it must exclude; this is an intrinsic limitation of the method for this problem, not a tuning choice, and is itself part of why the correction fails.

2. Extrapolating sparse cells up to a high fixed target coverage (e.g. C* = 0.99) relies on the Chao1-based extrapolation, which has wide uncertainty for very incomplete samples; this is why we swept a range of C* and also report the minimum-common-coverage standardisation, rather than committing to a single target. The conclusion (no restoration of agreement) holds across the whole sweep, so it does not depend on the extrapolation regime.

3. The comparison inherits the sibling chain's design choices: HEALPix-NESTED equal-area cells (vs Hurlbert & Jetz's lat-lon graticule), convex-hull EOO as the historical rangemap surrogate, and the top-5 % hotspot-threshold convention. The Article 12 gold-standard comparator removes the rangemap-substitute concern for that metric, and the negative result is consistent across both comparators.

4. The Article 12 comparison is restricted to the species intersection between each GBIF strategy and the Article 12 Iberian breeding set; species in one but not the other are excluded from that metric.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
