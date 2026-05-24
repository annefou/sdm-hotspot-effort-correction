# 06 — CiTO Citation

> Pre-flight (per `docs/forrt-form-fields.md` § Citation with CiTO): fields in
> form order are (1) Identifier for the citing creative work [required],
> (2) List citations [repeatable, ≥1], each with ↳ Citation Type [dropdown] +
> ↳ DOI/URL of the cited work. Enumerated below in order.
>
> Available CiTO types: confirms, qualifies, disputes, **extends**, usesMethodIn,
> citesAsAuthority, obtainsBackgroundFrom, discusses, citesAsDataSource,
> containsAssertionFrom, includesQuotationFrom, reviews, critiques, credits.
> (`replicates` is NOT available.)

**Description:** *"Declare citations between papers or other works, using Citation Typing Ontology"*

## Field-by-field draft

### Identifier for the citing creative work (text input, required)

URI of the Outcome published in step 05.

```
<PENDING — paste the step-05 Outcome RA… URI from nanopubs/PUBLISHED.md>
```

### List citations (repeatable group, required ≥1)

#### Citation 1 — extends the prior chain (PRIMARY, per design decision D4)

##### Citation Type (dropdown)

`extends`. **Override the default mapping.** The Outcome's validation status is
`Contradicted` *for the correction hypothesis*, whose default mapping is
`disputes`. But the citation target here is **not** the methods paper or this
chain's own claim — it is the sibling chain's Replication Outcome, and this
negative result *reinforces and extends* that prior finding (the observer-effort
bias is real and survives a standard completeness correction). So the relation
to the cited work is `extends`, not `disputes`. See `05_outcome.md` § Validation
status and `nanopubs/imported/CHAIN_SUMMARY.md`.

```
extends
```

##### DOI or other URL of the cited work (text input)

The sibling chain's Replication Outcome nanopub (the node localising the bias to
the observer-effort/atlas axis).

```
https://w3id.org/sciencelive/np/RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI
```

#### Citation 2 — uses the method of Chao & Jost 2012 (OPTIONAL)

A second entry making the method provenance machine-explicit. The methods paper
is already quoted at step 01; this adds the typed method-use relation. Include
it if you want the method link in the CiTO graph, or skip (the Quote already
carries it).

##### Citation Type (dropdown)

```
usesMethodIn
```

##### DOI or other URL of the cited work (text input)

```
https://doi.org/10.1890/11-1952.1
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.

This completes the six-step FORRT chain (Quote → AIDA → Claim → Study → Outcome
→ CiTO). Optional next layers:

- **Research Software** (`drafts/07_research_software.md`) — only if this repo
  *produces* a reusable, `pip install`-able artefact. This repo is a one-off
  replication pipeline, not a reusable tool, so per `docs/forrt-form-fields.md`
  § Research Software the honest answer is to **skip** it (the reusable upstream
  artefacts are GBIF, healpix-geo, and the Chao & Jost method, not this repo).
- **Research Synthesis** (`drafts/08_synthesis.md`) — only if this chain is one
  of several testing facets of a shared property. Currently it is a single
  chain extending one sibling; **skip** unless a third chain joins them.
