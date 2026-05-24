# sdm-hotspot-effort-correction v0.1.0

A reproducible pipeline testing whether **coverage-based rarefaction
(Chao & Jost 2012)** corrects observer-effort bias in GBIF "biodiversity
hotspots," restoring agreement with the EU Article 12 expert-rangemap gold
standard, in an Iberian-birds × HEALPix-NESTED system. **Headline result: it
does not.** At the 0.25° reference scale (HEALPix Nside 256), coverage
standardisation leaves top-5% hotspot misidentification at 87–97% (versus an
uncorrected 89–94%) — far from the Hurlbert & Jetz 47.8–68.6% reference range —
across the full target-coverage sweep and both basis-of-record strategies.
Standardising per-cell sample completeness does not remove the spatial
observer-effort distortion of which cells rank as hotspots.

Methods paper: Chao, A. & Jost, L. (2012), *Ecology* 93(12):2533–2547.
https://doi.org/10.1890/11-1952.1

This release contains:

- A four-stage reproducible pipeline (data download → clean →
  coverage-correction analysis → figures), driven by Snakemake + pixi.
- The Chao & Jost sample-coverage estimator and coverage-based
  rarefaction/extrapolation, implemented from the methods paper.
- Dockerfile, continuous-integration, and Jupyter Book workflows.
- A FORRT nanopublication chain (forthcoming) extending the prior
  observer-effort replication.

Extends the prior `sdm-scale-replication` study archived at
https://doi.org/10.5281/zenodo.20363555.

To cite this software, see `CITATION.cff`.
