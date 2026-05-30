# sdm-hotspot-effort-correction

> **Coverage-based rarefaction and extrapolation: standardizing samples by completeness rather than size** — replication study.
>
> Reference paper: [10.1890/11-1952.1](https://doi.org/10.1890/11-1952.1)

This repository is a self-contained replication of the headline claim from the reference paper above. It produces:

- A reproducible computational pipeline (Snakefile + notebooks).
- A FORRT-tagged nanopublication chain on the [Science Live platform](https://platform.sciencelive4all.org), documenting the claim, the replication design, and the outcome with full provenance.
- A Zenodo-archived release (source + container image) with a citable DOI.

## Quick start

```bash
git clone https://github.com/annefou/sdm-hotspot-effort-correction.git
cd sdm-hotspot-effort-correction
pixi install
pixi run snakemake --cores 1
```

Or with Docker:

```bash
docker run --rm ghcr.io/annefou/sdm-hotspot-effort-correction:latest
```

## Structure

- `paper/` — the source paper PDF (drop yours in there).
- `notebooks/` — jupytext `.py` notebooks that drive the pipeline.
- `data/` — downloaded by `notebooks/01_data_download.py`, never committed.
- `nanopubs/` — drafts of the FORRT chain field-by-field, plus the published-URI registry.
- `docs/` — operating manuals (FORRT form fields, chain decision tree, claim-type vocabulary).
- `figures/` — curated figures used in the Jupyter Book.

## Nanopublication chain

The replication's findings are published as a six-step FORRT nanopublication
chain on the Science Live platform. The **apex citation** is the natural
browsing entry point — it links the Outcome to the prior `sdm-scale-replication`
chain via `cito:extends` (this work reinforces and extends the sibling's
observer-effort finding) and to the methods paper via `cito:usesMethodIn`:

- **CiTO apex (entry point)** — [`RACYbb_IxZNnBcxI7uPqc-df2oRaMr4bqHJTOJe-BNmkc`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RACYbb_IxZNnBcxI7uPqc-df2oRaMr4bqHJTOJe-BNmkc)
- **Replication Outcome** (Contradicted / HighConfidence — coverage correction does not restore agreement) — [`RAsPjEImfZaXsIri0ny4j_s_k_6wyOlC6tkocl6w2y7f4`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RAsPjEImfZaXsIri0ny4j_s_k_6wyOlC6tkocl6w2y7f4)
- **Replication Study** (design) — [`RAONIKJjrrndTWX_f7emVpeKFOrdDtKuaXD6lJk4z6fKI`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RAONIKJjrrndTWX_f7emVpeKFOrdDtKuaXD6lJk4z6fKI)
- **FORRT Claim** (descriptive pattern) — [`RAgF6PfpfyFAkyT514Yj0f97coEFOktoHvdZ6gCV84c4Q`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RAgF6PfpfyFAkyT514Yj0f97coEFOktoHvdZ6gCV84c4Q)
- **AIDA sentence** — [`RAuP2z6scqdWkG6A7RFK4kBSlbHjoDHEbXhoUS5BendEo`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RAuP2z6scqdWkG6A7RFK4kBSlbHjoDHEbXhoUS5BendEo)
- **Quote** (verbatim from Chao & Jost 2012) — [`RArxpQJ98cPc7V3uAWhjJQtriT7qjV40Ml-ciSREJSh3s`](https://platform.sciencelive4all.org/np/?uri=https://w3id.org/sciencelive/np/RArxpQJ98cPc7V3uAWhjJQtriT7qjV40Ml-ciSREJSh3s)

The full URI registry (chain + Zenodo source DOI + GHCR Docker image) lives in
[`nanopubs/PUBLISHED.md`](nanopubs/PUBLISHED.md). The chain's internal and
external consistency was verified via the `/verify-chain` skill on 2026-05-30.

## Headline result

Coverage-based rarefaction (Chao & Jost 2012) **does not** restore agreement
between modern GBIF occurrence-derived bird-richness hotspots and the EU Article
12 expert-rangemap gold standard for Iberian birds. At the Hurlbert & Jetz
reference scale (HEALPix Nside 256 ≈ 25 km, top-5 % hotspots, vs Article 12),
the best coverage-corrected misidentification is **87.4 %** (all-observations)
and **96.6 %** (museum), versus uncorrected baselines of 88.7 % and 94.2 % — a
change of +1.3 and −2.4 percentage points respectively. Neither value reaches
the Hurlbert & Jetz 47.8–68.6 % reference range. See the published Replication
Outcome for full evidence and limitations.

## Citation

If you use this work, please cite both:

- This software: [`CITATION.cff`](CITATION.cff) → DOI [10.5281/zenodo.20451519](https://doi.org/10.5281/zenodo.20451519).
- The original paper: [10.1890/11-1952.1](https://doi.org/10.1890/11-1952.1).
