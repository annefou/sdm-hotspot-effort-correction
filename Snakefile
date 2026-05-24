# Snakefile — orchestrates the coverage-correction replication pipeline.
#
# Four notebooks, four rules (each wraps a jupytext .py executed in place, so
# the notebook stays the source of truth and Snakemake just sequences them):
#
#   01_data_download -> data/gbif/birds_iberia_{museum,allbor}.zip
#                       + data/external/art12/ART12_...gpkg  (real or synthetic)
#                       + data/raw/sources.json
#   02_data_clean    -> data/clean/richness_{museum,allbor}.nc
#                       + atlas_freq_{museum,allbor}.parquet   (NEW: coverage input)
#                       + species_index_{museum,allbor}.parquet
#                       + species_eoo_polygons.parquet + clean_report.json
#   03_analysis      -> results/coverage_correction.parquet (Ĉ sweep, both
#                       strategies, vs rangemap + vs Article 12)
#                       + results/headline.json (D9 verdict inputs)
#   04_figures       -> figures/main_result.{png,pdf}
#
# Usage:
#   pixi run snakemake --cores 1            # run everything
#   pixi run snakemake --cores 1 -n         # dry run
#   pixi run snakemake --cores 1 clean      # 01 + 02
#   pixi run snakemake --cores 1 analysis   # 01 + 02 + 03

NOTEBOOKS = "notebooks"
DATA = "data"
RESULTS = "results"
FIGURES = "figures"


rule all:
    input:
        f"{FIGURES}/main_result.png",
        f"{RESULTS}/coverage_correction.parquet",
        f"{RESULTS}/headline.json",


# ---------- 01: Data download ----------
# Self-contained: two strategy GBIF zips (museum vs allbor) reusing the sibling
# chain's download DOIs (D6), plus the EU Article 12 expert-rangemap GPKG.
# Three modes: pre-minted GBIF keys; GBIF_USER/PWD/EMAIL -> mint via API; or a
# deterministic per-strategy synthetic demo fallback so a fresh checkout runs.
rule download:
    output:
        f"{DATA}/raw/sources.json",
        f"{DATA}/gbif/birds_iberia_museum.zip",
        f"{DATA}/gbif/birds_iberia_allbor.zip",
        f"{DATA}/external/art12/ART12_3035_distribution_data_without_sensitive.gpkg",
    log:
        f"{RESULTS}/logs/01_data_download.log",
    shell:
        "mkdir -p $(dirname {log}) && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 01_data_download.py && "
        "jupyter execute --inplace 01_data_download.ipynb 2>&1 | tee ../{log}"


# ---------- 02: Data clean ----------
# Bin both strategies onto HEALPix NESTED (Nside 16..512); year-split at 2000.
# Emits per-cell richness (atlas + rangemap) AND the per-cell atlas
# species-frequency tables the coverage estimator in 03 needs.
rule clean:
    input:
        f"{DATA}/gbif/birds_iberia_museum.zip",
        f"{DATA}/gbif/birds_iberia_allbor.zip",
    output:
        museum_nc = f"{DATA}/clean/richness_museum.nc",
        allbor_nc = f"{DATA}/clean/richness_allbor.nc",
        museum_freq = f"{DATA}/clean/atlas_freq_museum.parquet",
        allbor_freq = f"{DATA}/clean/atlas_freq_allbor.parquet",
        report = f"{DATA}/clean/clean_report.json",
    log:
        f"{RESULTS}/logs/02_data_clean.log",
    shell:
        "mkdir -p $(dirname {log}) {DATA}/clean && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 02_data_clean.py && "
        "jupyter execute --inplace 02_data_clean.ipynb 2>&1 | tee ../{log}"


# ---------- 03: Analysis (coverage correction) ----------
# Per (strategy, Nside, target coverage C*): coverage-based rarefaction of
# per-cell atlas richness (Chao & Jost 2012), then top-5% hotspot
# misidentification vs the EOO-hull rangemap and vs the Article 12 gold
# standard. Sweeps C* (D7); both strategies (D8); reports reduction + H&J-range
# reach (D9).
rule analysis:
    input:
        museum_nc = f"{DATA}/clean/richness_museum.nc",
        allbor_nc = f"{DATA}/clean/richness_allbor.nc",
        museum_freq = f"{DATA}/clean/atlas_freq_museum.parquet",
        allbor_freq = f"{DATA}/clean/atlas_freq_allbor.parquet",
        art12 = f"{DATA}/external/art12/ART12_3035_distribution_data_without_sensitive.gpkg",
    output:
        coverage = f"{RESULTS}/coverage_correction.parquet",
        headline = f"{RESULTS}/headline.json",
    log:
        f"{RESULTS}/logs/03_analysis.log",
    shell:
        "mkdir -p $(dirname {log}) " + RESULTS + " && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 03_analysis.py && "
        "jupyter execute --inplace 03_analysis.ipynb 2>&1 | tee ../{log}"


# ---------- 04: Figures ----------
# main_result: corrected misidentification vs target coverage C* at Nside 256,
# one line per strategy, with the uncorrected baseline + H&J reference band.
rule figures:
    input:
        coverage = f"{RESULTS}/coverage_correction.parquet",
        headline = f"{RESULTS}/headline.json",
    output:
        main_png = f"{FIGURES}/main_result.png",
        main_pdf = f"{FIGURES}/main_result.pdf",
    log:
        f"{RESULTS}/logs/04_figures.log",
    shell:
        "mkdir -p $(dirname {log}) " + FIGURES + " && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 04_figures.py && "
        "jupyter execute --inplace 04_figures.ipynb 2>&1 | tee ../{log}"
