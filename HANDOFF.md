# HANDOFF — sdm-hotspot-effort-correction

> Scratch brief for the first working session in this repo. Not a deliverable;
> delete once `nanopubs/drafts/00_design_decisions.md` + `00_paper_summary.md`
> capture this. Written 2026-05-24 from the parent session that finished the
> sibling chain `sdm-scale-replication`.

## What this replication is

A FORRT replication that **shows how to *solve*** the observer-effort bias
identified by its sibling chain. The sibling (`sdm-scale-replication`,
Hurlbert & Jetz 2007, Iberian birds × HEALPix) concluded that modern GBIF
"biodiversity hotspots" are inflated by survey effort — even a gold-standard
EU Article 12 expert rangemap did **not** close the gap, localising the
problem to the *atlas/effort axis*. This new study tests whether a standard
correction recovers hotspot agreement.

## Locked design decisions (from parent session, 2026-05-24)

- **Headline question / claim under test:** does correcting per-cell richness
  for **survey effort via coverage-based rarefaction** (Chao & Jost 2012)
  restore agreement between GBIF-occurrence hotspots and the EU Article 12
  expert-rangemap gold standard, in the same Iberian-birds × HEALPix-NESTED
  system as the sibling chain?
- **Design type:** Replication Study (new method on the same system).
- **Chain root / topology:** **methods-paper-rooted + extends prior.**
  - Methods paper: **Chao & Jost (2012)**, "Coverage-based rarefaction and
    extrapolation: standardizing samples by completeness rather than size,"
    *Ecology* 93(12):2533–2547. **DOI `10.1890/11-1952.1`** (verified resolves).
  - CiTO step: **`extends`** the sibling chain's Replication Outcome.
- **Correction method:** coverage-based rarefaction / `iNEXT` (sample-coverage
  standardisation of per-cell richness), then re-compute top-5% hotspot overlap
  vs Article 12. (Effort-covariate model was the considered alternative — not chosen.)
- **Phase 1 entry point:** **B (nanopub-rooted)** — run `/import-from-nanopub`
  seeded from the sibling chain apex before/with reading the Chao & Jost PDF.

## Prior-chain URIs to import / cite

- Sibling **CiTO apex** (seed the import here):
  `https://w3id.org/sciencelive/np/RALjFcvPtncy74ZL8QgSiEyRZv_-mOiZj4wvWuq8JK-2s`
- Sibling **Replication Outcome** (the node this chain `extends`):
  `https://w3id.org/sciencelive/np/RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI`
- Full sibling registry: `/Users/annef/Documents/ScienceLive/sdm-scale-replication/nanopubs/PUBLISHED.md`
  (also lists the Iberian Bombus/Lizards constellation + the 8 SDM-resolution
  Quote-with-comment scaffold — do **not** re-cite those at this chain's CiTO).

## Sibling key numbers (for grounding the new claim, not re-deriving)

- Scale-dependence replicated qualitatively (hotspot misidentification rises
  monotonically with grid refinement, Nside 16→512).
- Magnitude inflated: ~89.9% (museum) / ~97.8% (allbor) misidentification at
  Nside 256 (≈0.25°), vs Hurlbert & Jetz 47.8% (Australia) / 68.6% (S. Africa).
- Atlas observer-effort coupling: log-log Pearson r ≈ 0.96 (allbor) / 0.48
  (museum) at Nside 256 — the dominant residual.
- Article 12 gold-standard test did NOT close the gap (94.9% museum / 85.2%
  allbor on matched species) → problem is on the atlas axis, not the rangemap.
- Authoritative sibling doc: `sdm-scale-replication/docs/replication-gap-verification.md`.

## First steps in this repo

1. `git config user.name "Anne Fouilloux"` / `user.email "anne.fouilloux@lifewatch.eu"`.
2. **Phase 0 — `/init-template`**: substitute `{{...}}` tokens. Paper DOI =
   `10.1890/11-1952.1`. Author identity per `USER_PREFERENCES.md` (already
   matches Anne). Drop the Chao & Jost 2012 PDF in `paper/`.
3. **Phase 1 — `/import-from-nanopub`** seeded from the sibling CiTO apex above
   → writes `nanopubs/imported/CHAIN_SUMMARY.md`. Then verify the methods-paper
   verbatim quote from the PDF into `nanopubs/drafts/01_quote.md`.
4. Proceed through the `/replication-study` orchestration (Phases 2–5). Reuse
   the sibling's GBIF download + HEALPix pipeline as the starting point for the
   atlas axis; the new code is the coverage-rarefaction layer + Article 12 re-compare.
