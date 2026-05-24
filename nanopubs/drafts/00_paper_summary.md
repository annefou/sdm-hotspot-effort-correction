# Paper summary

> This is a working scratchpad for the paper-analysis phase. The output of this file feeds the Quote / AIDA / Claim drafts. It is not itself a nanopub.

**Reference paper:** Coverage-based rarefaction and extrapolation: standardizing samples by completeness rather than size

**DOI:** 10.1890/11-1952.1

**Authors:** Anne Chao & Lou Jost

**Year:** 2012 — *Ecology* 93(12):2533–2547

> ⚠️ **This is a METHODS paper, not an empirical-claim paper.** The chain is
> methods-paper-rooted: the Quote states the *methodological principle* the
> replication's correction rests on (standardise samples by completeness/coverage
> rather than by size), not an empirical finding about a dataset. The empirical
> claim being tested lives in the *sibling* chain's Outcome (observer-effort bias
> inflates GBIF hotspots), which this chain `extends`.

## Headline claim (methodological principle)

The principle this replication operationalises as a correction:

> **"The solution is to compare samples of equal completeness, not equal size."** (p. 2533)

…formally proposed in the abstract as:

> **"We propose an integrated sampling, rarefaction, and extrapolation methodology to compare species richness of a set of communities based on samples of equal completeness (as measured by sample coverage) instead of equal size."** (p. 2533)

The consequence the replication exploits: coverage-based standardisation
"more efficiently finds the correct ranking of communities according to their
true richnesses" (p. 2533) — and hotspot identification is fundamentally a
*ranking* problem (top-5% richest cells).

> _Verbatim candidates verified against the PDF pp. 2533. Promoted to `01_quote.md`._

## Methodology summary

Chao & Jost (2012) introduce **coverage-based** rarefaction and extrapolation as
an alternative to traditional **size-based** (equal-individuals or equal-samples)
rarefaction for comparing species richness across communities.

- **Core idea / model.** Communities are compared at equal **sample coverage**
  *C* (a Good–Turing measure of sample completeness: the proportion of the
  community's total individuals belonging to species represented in the sample;
  Good 1953). The **coverage deficit** `1 − C` is the probability the next
  sampled individual is a new species, and equals the slope of the species
  accumulation curve (their Eqs. 1–3). The authors derive, for the first time,
  an **unbiased analytic rarefaction formula to estimate richness at a given
  coverage**, plus an analytic **extrapolation** formula to predict richness at a
  higher coverage than observed — unifying interpolation and extrapolation on a
  single coverage axis.
- **Why size-based fails.** Samples standardised to equal size generally have
  *different* completeness (a fixed-size sample fully characterises a low-diversity
  community but under-samples a rich one), so equal-size comparison "systematically
  biases the degree of differences between community richnesses" (abstract). Peet
  (1974): fixed sample sizes compress the ratio of richnesses.
- **Replication principle.** Coverage-standardised richness estimates
  approximately satisfy a *replication principle* (doubling a community's size by
  pooling an identical second community doubles estimated richness) — a property
  fixed-size estimates lack. This is what makes coverage-based ratios/rankings
  "representative of the true relationship" between communities.
- **Adaptive stopping rule.** If sampling stops at a target coverage, samples are
  directly comparable with no rarefaction at all (no data thrown away).
- **Headline methodological result (not a single number).** Coverage-based
  rarefaction yields less compression / less biased comparisons than size-based
  rarefaction, throws away less data, and more efficiently recovers the correct
  **ranking** of communities by true richness. Illustrated with hypothetical
  communities (e.g. Community A vs A+B, a tropical-canopy/understory butterfly
  example) and real datasets, not a single attribution statistic.

## Replication design choice

- [ ] **Reproduction Study** — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] **Reproduction/Replication Study** — both.

**Justification.** We are not reproducing Chao & Jost's own analyses. We *apply*
their method (coverage-based rarefaction, `iNEXT`-style sample-coverage
standardisation) as a **new correction** to the same biodiversity system the
sibling chain studied (Iberian birds × HEALPix-NESTED, two GBIF basis-of-record
strategies). The question — does effort-correcting per-cell richness via
coverage-based rarefaction restore agreement between GBIF-occurrence hotspots and
the EU Article 12 expert-rangemap gold standard? — is a new method on the same
system, i.e. a Replication Study that *extends* the sibling's Replication Outcome.

## Notes for downstream drafts

- **Quote** quotes Chao & Jost (the method), cited DOI `10.1890/11-1952.1`.
- **CiTO** at the chain apex is `cito:extends` → the sibling Replication Outcome
  `RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI` (not Chao & Jost, not Hurlbert
  & Jetz). See `nanopubs/imported/CHAIN_SUMMARY.md`.
- "Sample coverage" in the per-cell context = completeness of each HEALPix cell's
  GBIF occurrence sample. Effort-rich cells (cities) have high coverage; effort-poor
  cells have low coverage. Standardising all cells to a common target coverage *Ĉ*
  is the mechanism by which observer effort is removed — this is the open design
  question (target *Ĉ* choice) flagged in `CHAIN_SUMMARY.md`.
- The AIDA sentence (step 02) must be one atomic methodological statement, e.g.
  "Standardising samples by coverage rather than by size yields less biased
  comparisons of species richness across communities." Lock the AIDA wording only
  after the design questions are settled.
