# 01 — Quote-with-comment (paper-rooted chains)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> If this is a question-rooted chain, use `01_pico.md` or `01_pcc.md` instead — see `docs/chain-decision-tree.md`.
>
> **After choosing the chain shape, delete the two step-1 alternates you aren't using.** Once you've decided this chain is paper-rooted and keep `01_quote.md`, run:
> ```bash
> rm nanopubs/drafts/01_pico.md nanopubs/drafts/01_pcc.md
> ```

**Form heading:** *"Annotate a paper quotation — Annotating a paper quotation with personal interpretation"*

## Field-by-field draft

### Cited DOI (text input)

Format: starts with `10.` — bare DOI, **NOT** `https://doi.org/...` form.

```
10.1890/11-1952.1
```

### Quote mode (radio button)

- [x] **Quote whole text (less than 500 characters)**
- [ ] Quote start/end *(use this if the quote exceeds 500 chars)*

### Quoted Text (textarea, required)

Verbatim from the paper PDF in `paper/`. Character-for-character. ≤ 500 chars in whole-text mode.

> _Verified verbatim against the PDF, p. 2533 (abstract). Read pages 2533–2535 directly; not reconstructed from memory._

**PRIMARY** (abstract, p. 2533):

```
We propose an integrated sampling, rarefaction, and extrapolation methodology to compare species richness of a set of communities based on samples of equal completeness (as measured by sample coverage) instead of equal size.
```

Character count: 224 / 500.

#### Alternate quotes (also verbatim — pick one if the primary is rejected)

**ALT-A** — crisp statement of the principle (Introduction, p. 2533):

```
The solution is to compare samples of equal completeness, not equal size.
```

Character count: 73 / 500.

**ALT-B** — ties coverage-standardisation to *ranking* recovery, which is the
hotspot use case (abstract, p. 2533):

```
coverage-based rarefaction throws away less data than traditional size-based rarefaction, and more efficiently finds the correct ranking of communities according to their true richnesses
```

Character count: 186 / 500. *(Verbatim contiguous span; opening lowercase because it is mid-sentence in the source.)*

### Comment (textarea, required)

Subtitle: *"Our interpretation or explanation of why this quotation is relevant."*

Why this quote matters and what the replication tests. Connect the paper's claim to the work this repo does. Don't repeat the quote.

```
A sibling replication showed modern GBIF "biodiversity hotspots" for Iberian birds are inflated by survey effort: richest-ranked cells track where observers go, not where birds are densest, and even an EU Article 12 expert rangemap doesn't close the gap. Effort-rich cells reach higher completeness than effort-poor ones, so comparing raw per-cell richness is exactly the equal-size comparison this paper warns against. This study tests whether coverage-based rarefaction removes that effort bias.
```

Character count: 497 / 500.

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 01.
