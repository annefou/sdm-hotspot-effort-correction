# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 04 — Figures
#
# Main result: hotspot **misidentification vs target sample coverage C\*** at the
# Hurlbert & Jetz reference scale (HEALPix Nside 256 ≈ 25 km), one line per BoR
# strategy. The figure answers the D9 question visually — does coverage-based
# correction (Chao & Jost 2012) pull the misidentification down from the
# uncorrected baseline toward the H&J 47.8–68.6 % reference band?
#
# Uses `results/coverage_correction.parquet` + `results/headline.json` from
# `03_analysis.py`. The y-metric is the Article 12 comparator where available
# (real-data runs), otherwise the EOO-hull rangemap comparator.
#
# **Inline display rule:** every `fig.savefig(...)` is paired with `plt.show()`
# so MyST renders the figure in the Jupyter Book. No `matplotlib.use('Agg')`.

# %%
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")

# %%
RESULTS_DIR = Path("../results")
FIGURES_DIR = Path("../figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

HEADLINE_NSIDE = 256
HJ_RANGE = (47.8, 68.6)          # Hurlbert & Jetz 2007 reference band (0.25°).
HJ_BASELINE = {"museum": 89.9, "allbor": 97.8}  # sibling uncorrected baseline.
STRATEGY_COLORS = {"museum": "#1f77b4", "allbor": "#d62728"}

corr = pd.read_parquet(RESULTS_DIR / "coverage_correction.parquet")
with open(RESULTS_DIR / "headline.json") as f:
    headline = json.load(f)

# Comparator chosen by 03 (Art-12 if present, else rangemap). Use the same here.
any_strat = next(iter(headline["per_strategy"].values()), {})
metric = any_strat.get("comparator", "misidentified_pct_vs_rangemap")
metric_label = ("vs Article 12 expert rangemap"
                if metric.endswith("art12") else "vs EOO-hull rangemap")
print(f"Plotting metric: {metric} ({metric_label})")

# %% [markdown]
# ## Main result figure — misidentification vs target coverage C\*

# %%
ref = corr[(corr["nside"] == HEADLINE_NSIDE)
           & (corr["target_coverage_kind"].isin(["fixed", "cmin"]))]

fig, ax = plt.subplots(figsize=(9, 6))

# H&J reference band + uncorrected baselines.
ax.axhspan(HJ_RANGE[0], HJ_RANGE[1], color="green", alpha=0.12, zorder=0,
           label=f"Hurlbert & Jetz 2007 range ({HJ_RANGE[0]}–{HJ_RANGE[1]} %)")
for strat, base in HJ_BASELINE.items():
    ax.axhline(base, color=STRATEGY_COLORS[strat], lw=1.0, ls=":", alpha=0.7)

for strat in ["museum", "allbor"]:
    sub = ref[ref["strategy"] == strat].sort_values("target_coverage")
    if sub.empty or sub[metric].isna().all():
        continue
    ax.plot(sub["target_coverage"], sub[metric], marker="o", lw=2.3,
            color=STRATEGY_COLORS[strat],
            label=f"{strat} — coverage-corrected")
    # Mark the uncorrected baseline point of this run (raw richness) at right.
    unc = corr[(corr["nside"] == HEADLINE_NSIDE)
               & (corr["strategy"] == strat)
               & (corr["target_coverage_kind"] == "uncorrected")]
    if len(unc) and pd.notna(unc[metric].iloc[0]):
        ax.annotate(
            f"{strat} uncorrected = {unc[metric].iloc[0]:.1f} %",
            xy=(0.995, unc[metric].iloc[0]), xytext=(0.86, unc[metric].iloc[0] + 2),
            fontsize=8, color=STRATEGY_COLORS[strat])

ax.set_xlabel("Target sample coverage  C*  (coverage-based standardisation)")
ax.set_ylabel(f"Hotspot misidentification (%)  —  top-5 % symmetric non-overlap\n{metric_label}")
ax.set_ylim(0, 100)
ax.set_title(
    "Coverage-based effort correction of Iberian-bird richness hotspots\n"
    f"(HEALPix Nside {HEADLINE_NSIDE} ≈ 25 km; Chao & Jost 2012). "
    "Dotted lines: sibling uncorrected baseline.",
    fontsize=11)
ax.legend(loc="lower left", fontsize=8, framealpha=0.92)

synthetic = str(ref["synthetic"].iloc[0]) if len(ref) else "?"
if synthetic.lower() == "true":
    ax.text(0.5, 0.5, "SYNTHETIC DEMO DATA", transform=ax.transAxes,
            fontsize=26, color="grey", alpha=0.25, ha="center", va="center",
            rotation=20, zorder=5)

fig.tight_layout()
fig.savefig(FIGURES_DIR / "main_result.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "main_result.pdf", bbox_inches="tight")
plt.show()  # required for MyST inline display
print(f"saved {FIGURES_DIR / 'main_result.png'} (+ .pdf)")

# %% [markdown]
# ## Headline summary (printed)

# %%
for strat, d in headline["per_strategy"].items():
    print(f"\n{strat}  [comparator: {d['comparator']}, synthetic={d['synthetic']}]")
    print(f"  uncorrected      : {d['uncorrected_misidentified_pct']} %")
    print(f"  best corrected   : {d['best_corrected_misidentified_pct']} % "
          f"at {d['best_corrected_at']}")
    print(f"  reduction        : {d['reduction_pp_vs_uncorrected']} percentage points")
    print(f"  reaches H&J range: {d['reaches_hj_range']}")
