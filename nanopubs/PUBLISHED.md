# Published nanopub chain — URI registry

This file is the canonical registry of published nanopub URIs for this replication. Update it as you publish each step.

## Chain

| Step | Template | URI |
|---|---|---|
| 01 | Quote-with-comment (or PICO / PCC) | https://w3id.org/sciencelive/np/RArxpQJ98cPc7V3uAWhjJQtriT7qjV40Ml-ciSREJSh3s |
| 02 | AIDA Sentence | https://w3id.org/sciencelive/np/RAuP2z6scqdWkG6A7RFK4kBSlbHjoDHEbXhoUS5BendEo | 
| 03 | FORRT Claim | https://w3id.org/sciencelive/np/RAgF6PfpfyFAkyT514Yj0f97coEFOktoHvdZ6gCV84c4Q | 
| 04 | FORRT Replication Study | https://w3id.org/sciencelive/np/RAONIKJjrrndTWX_f7emVpeKFOrdDtKuaXD6lJk4z6fKI | 
| 05 | FORRT Replication Outcome | https://w3id.org/sciencelive/np/RAsPjEImfZaXsIri0ny4j_s_k_6wyOlC6tkocl6w2y7f4 | 
| 06 | CiTO Citation | https://w3id.org/sciencelive/np/RACYbb_IxZNnBcxI7uPqc-df2oRaMr4bqHJTOJe-BNmkc | 

## Software & data archive (Zenodo / GHCR)

| Artefact | DOI / URL | Notes |
|---|---|---|
| Source — concept DOI | [10.5281/zenodo.20451519](https://doi.org/10.5281/zenodo.20451519) | Resolves to the latest version. |
| Source — version DOI (v0.1.0) | [10.5281/zenodo.20451520](https://doi.org/10.5281/zenodo.20451520) | This release (2026-05-29). |
| Docker image | `ghcr.io/annefou/sdm-hotspot-effort-correction:v0.1.0` (also `:latest`) | Pushed by `.github/workflows/docker.yml` on the `v0.1.0` tag (run 26662285331, 3m36s, success). Optional Zenodo archive of the image not configured — `ZENODO_TOKEN` repo secret not set; this is allowed per CLAUDE.md (image archive on Zenodo is "(optionally)"). To enable on a future release, add the secret. |

## Format

URIs from Science Live are of the form `https://w3id.org/sciencelive/np/RA…`. URIs from Nanodash (used as a fallback when the Science Live UI hits a bug) are of the form `https://w3id.org/np/RA…`. Both are valid and citable.

If a URI is not in the Science Live namespace, view it via the Science Live viewer by wrapping the URI:

```
https://platform.sciencelive4all.org/np/?uri=<full-URI>
```

## Cross-references

- Drafts: `nanopubs/drafts/`
- Form structure: `docs/forrt-form-fields.md`
- Chain shape decision: `docs/chain-decision-tree.md`
