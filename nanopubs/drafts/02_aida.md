# 02 — AIDA Sentence

> Pre-flight (per `docs/forrt-form-fields.md` § AIDA): fields in form order are
> (1) AIDA sentence [required], (2) Select related topics/tags [optional],
> (3) Relates to this nanopublication [required], (4) Supported by datasets
> [optional, repeatable], (5) Supported by other publications [optional,
> repeatable]. Enumerated below in order.

**Form heading:** *"AIDA Sentence — Make structured scientific claims following the AIDA model"*

## Field-by-field draft

### AIDA sentence (textarea, required)

Atomic, Independent, Declarative, Absolute. One claim under test. Ends with a
full stop. States the *hypothesis* (no result — the result lives in the
Outcome, step 05).

```
Standardising per-cell species richness to a common sample coverage by coverage-based rarefaction restores agreement between modern GBIF occurrence-derived bird-richness hotspots and expert-rangemap hotspots in the Iberian peninsula.
```

*(Atomic check: one finding — "coverage standardisation restores hotspot
agreement". No "and" joining two distinct findings.)*

### Select related topics/tags (dropdown, optional)

Predefined vocabulary — open the dropdown and pick whichever of these labels
exist; skip any that aren't offered:

```
biodiversity; species richness; sampling bias; rarefaction; species distribution
```

### Relates to this nanopublication (text input, required)

Paper-rooted chain → the Quote-with-comment URI (step 01).

```
<PENDING — paste the step-01 Quote-with-comment RA… URI from nanopubs/PUBLISHED.md>
```

### Supported by datasets (repeatable group, optional)

The GBIF download DOIs (reused per D6) + the Article 12 gold-standard layer.

- `https://doi.org/10.15468/dl.r8pcat`  *(GBIF museum strategy)*
- `https://doi.org/10.15468/dl.e9xv7p`  *(GBIF all-observations strategy)*
- `https://sdi.eea.europa.eu/data/e2face16-f352-4aff-9e4f-0ad1306f89b5`  *(EU Article 12 distribution polygons, EEA 2013–2018, CC-BY 4.0)*

### Supported by other publications (repeatable group, optional)

*(skip — optional.)* The methods paper (Chao & Jost 2012) is already cited via
the Quote this AIDA relates to. Leaving this empty also avoids the known
platform bug where populating **both** *Supported by datasets* and *Supported
by other publications* has caused publishing to fail (see
`docs/forrt-form-fields.md` § AIDA). If publishing still fails with only
datasets populated, fall back to Nanodash (URI namespace `w3id.org/np/…`).

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 02.
