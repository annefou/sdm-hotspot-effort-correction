# Design decisions — sdm-hotspot-effort-correction

Locked decisions for this FORRT replication. Supersedes the scratch `HANDOFF.md`.
Read alongside `00_paper_summary.md` (methods paper) and
`../imported/CHAIN_SUMMARY.md` (prior chain being extended).

## What this replication is

A **Replication Study** that tests whether *correcting* the observer-effort bias
identified by the sibling chain (`sdm-scale-replication`, Hurlbert & Jetz 2007)
restores agreement between GBIF-occurrence "biodiversity hotspots" and the EU
Article 12 expert-rangemap gold standard — by standardising per-cell richness for
survey effort via **coverage-based rarefaction (Chao & Jost 2012)** — in the same
Iberian-birds × HEALPix-NESTED system.

## Locked decisions

| # | Decision | Choice | Source |
|---|---|---|---|
| D1 | Chain root / topology | **Methods-paper-rooted** on Chao & Jost 2012 (DOI `10.1890/11-1952.1`); extends the prior chain. | HANDOFF + `CHAIN_SUMMARY.md` |
| D2 | Design type | **Replication Study** (new method on the same system). | HANDOFF + `00_paper_summary.md` |
| D3 | Correction method | Coverage-based rarefaction / `iNEXT`-style sample-coverage standardisation of per-cell richness, then re-compute top-5% hotspot overlap vs Article 12. (Effort-covariate model was the considered alternative — *not* chosen.) | HANDOFF |
| D4 | CiTO relation + target | **`cito:extends`** → the sibling **Replication Outcome** `https://w3id.org/sciencelive/np/RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI` (the node that localised the bias to observer effort). Do **not** re-cite Hurlbert & Jetz 2007 or the Iberian Bombus/Lizards constellation at this CiTO. | HANDOFF + `CHAIN_SUMMARY.md` |
| D5 | Phase 1 entry point | **B (nanopub-rooted)** import from the sibling CiTO apex `RALjFcv…`, combined with verbatim quote of the Chao & Jost methods paper. | HANDOFF |
| **D6** | **GBIF data window** | **Reuse the sibling's existing download DOIs** — museum `10.15468/dl.r8pcat`, allbor `10.15468/dl.e9xv7p`. Maximum comparability: the correction is the only changed variable. | User, 2026-05-24 |
| **D7** | **Target sample coverage Ĉ** | **Sweep a range of Ĉ** and report hotspot-overlap as a function of Ĉ (rather than a single fixed value). Separates the correction's effect from an arbitrary single-Ĉ choice; mirrors the sibling's top-K sweep. | User, 2026-05-24 |
| **D8** | **Basis-of-record strategies** | **Both museum + allbor** are corrected and re-compared, exactly as the sibling did — shows whether correction works across the effort-bias spectrum (r≈0.48 museum to r≈0.96 allbor at Nside 256). | User, 2026-05-24 |
| **D9** | **"Agreement restored" definition** | **Both criteria reported**: (a) statistically significant reduction in misidentification vs the uncorrected 89.9% (museum) / 97.8% (allbor) baseline, AND (b) whether corrected misidentification reaches the Hurlbert & Jetz 47.8–68.6% reference range. The Outcome verdict is nuanced accordingly. | User, 2026-05-24 |

## Grounding numbers from the sibling (not to be re-derived)

At Nside 256 (≈25 km, the 0.25° H&J reference scale), uncorrected:
- museum misidentification 89.9%; allbor 97.8% (vs H&J 47.8% Australia / 68.6% S. Africa).
- Article 12 gold-standard did NOT close the gap: 94.9% museum / 85.2% allbor (matched species).
- Observer-effort coupling: log-log Pearson r ≈ 0.96 (allbor) / 0.48 (museum).
- Top-25% threshold (vs top-5%): 74.2% museum / 71.6% allbor (inside the H&J range).
- Concave-hull substitute closes 6.3 pp (museum) / 13.5 pp (allbor) — secondary contributor.

Sibling Outcome verdict: **Partially Supported**. Sibling apex CiTO: `cito:qualifies` → H&J 2007.

## Implications for the pipeline (Phase 2)

- **Reuse** the sibling's `01_data_download.py` (same GBIF DOIs, D6) and HEALPix-NESTED
  binning + Article 12 loading wholesale (staged in `_template_from_prior/`).
- **New code** = the coverage-rarefaction layer: per-cell sample-coverage estimation
  (Good–Turing), coverage-based richness standardisation across the Ĉ sweep (D7), for
  both strategies (D8), then top-5% hotspot recomputation and overlap-vs-Article-12 as
  a function of Ĉ.
- **Headline figure** (`figures/main_result.png`): corrected misidentification vs Ĉ,
  with the uncorrected baseline and the H&J reference band marked (serves D9).

## Still open (decide before Phase 5 Outcome draft, not blocking Phase 2)

- AIDA (step 02) atomic wording — lock after Phase 3 produces numbers.
- Whether to publish a separate Research Software nanopub for the coverage-correction
  layer if it becomes a reusable `pip install`-able tool (vs a one-off pipeline).
