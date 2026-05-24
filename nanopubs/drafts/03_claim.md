# 03 — FORRT Claim

> Pre-flight (per `docs/forrt-form-fields.md` § FORRT Claim): fields in form
> order are (1) Short URI suffix as claim ID [required], (2) Label of the claim
> [required], (3) Search for an AIDA sentence [required], (4) Type of FORRT
> claim [required], (5) Source URI [optional]. No fields below Source URI except
> the "publish as example" toggle. Enumerated below in order.

**Form heading:** *"FORRT Claim — Declare an original claim according to FORRT, linking it to an AIDA sentence with a specific FORRT type."*

## Field-by-field draft

### Short URI suffix as claim ID (text input, required)

```
coverage-rarefaction-restores-hotspot-agreement
```

### Label of the claim (text input, required)

Descriptive title (not a sentence).

```
Coverage-based rarefaction restores GBIF-vs-expert-rangemap hotspot agreement (Iberian birds, HEALPix-NESTED)
```

### Search for an AIDA sentence (search/select, required)

URI of the AIDA published in step 02.

```
<PENDING — paste the step-02 AIDA RA… URI from nanopubs/PUBLISHED.md>
```

### Type of FORRT claim (dropdown, required)

See `docs/claim-type-vocabulary.md`. The claim asserts an empirical
*relationship* — that applying coverage-based correction yields agreement
between two hotspot surfaces. That is a `descriptive pattern` (an observed
empirical relationship between variables), not a statement about a test
statistic per se.

- [ ] computational performance
- [ ] scalability
- [ ] data quality
- [ ] data governance
- [x] **descriptive pattern**
- [ ] model performance
- [ ] statistical significance

### Source URI (text input, optional)

Full URL form. The methods paper whose technique the claim operationalises.

```
https://doi.org/10.1890/11-1952.1
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 03.
