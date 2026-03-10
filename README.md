# Identifiability-aware reconstruction of subgroup-specific absolute benefit from aggregate trial reporting

Reproducibility package for the identifiability-aware subgroup survival reconstruction framework, applied to the INDIGO trial (vorasidenib vs placebo in IDH-mutant glioma) and CheckMate 498 (nivolumab + RT vs TMZ + RT in unmethylated MGMT GBM).

## Overview

Aggregate trial publications report overall Kaplan-Meier curves and subgroup-level hazard ratios, but not subgroup-specific survival trajectories. This package implements a framework that reconstructs feasible sets of subgroup-specific absolute benefit (RMST, survival probability at landmark times) from these aggregate reports, explicitly acknowledging that point estimates are not identified from the available data.

## Directory structure

```
lets-go-indigo-checkmate/
  src/                     Core Python modules
    utils.py               Digitization, survival utilities
    extract_indigo.py      INDIGO-specific extraction
    extract_checkmate.py   CheckMate-specific extraction
    reconstruct.py         Feasible-set reconstruction framework
    plotting.py            Publication figure generation
  scripts/                 Runner scripts
    run_indigo.py          INDIGO pipeline (PFS + TTNI)
    run_checkmate_blinded.py    CheckMate blinded phase
    run_checkmate_unblinded.py  CheckMate unblinded phase
    run_all.py             Master script (single command)
    generate_figures_tables.py  Publication outputs
    create_manuscript.js   Manuscript docx generation
    create_supplement.js   Supplement docx generation
    create_cover_letter.js Cover letter docx generation
  data/
    extracted/             Raw extracted data (KM, forest plots)
    processed/             Model-ready inputs (generated)
  outputs/                 Analysis results (CSVs, JSONs)
    logs/                  Step-by-step run logs
  figures/                 Publication figures (PDF + PNG)
  tables/                  Formatted tables (CSV)
  manuscript/              manuscript.docx, supplement.docx, cover_letter.docx
```

## Requirements

Python 3.9+ with: numpy, pandas, scipy, matplotlib, pdfplumber, opencv-python (cv2).

Install:
```bash
pip install numpy pandas scipy matplotlib pdfplumber opencv-python-headless
```

For manuscript generation: Node.js with `npm install -g docx`.

## Reproducing all analyses

```bash
python scripts/run_all.py \
  --indigo-pdf /path/to/NEJMoa2304194.pdf \
  --checkmate-pdf /path/to/noac099.pdf \
  --checkmate-s1ab /path/to/Checkmate_Fig_S1_panel_a_left_and_b_right.png \
  --checkmate-s1cd /path/to/Checkmate_Fig_S1_panel_c_left_and_d_right.png
```

This runs extraction, reconstruction, sensitivity analyses, and generates all figures and tables. Total runtime is approximately 5 to 10 minutes.

## Key methodological features

The framework fits piecewise-exponential baseline hazards per subgroup level within a two-level factor partition, subject to a mixture constraint (observed arm-level KM equals the weighted sum of subgroup survival curves). Feasible-set characterization varies knot placements (5 configurations), smoothness penalties (6 levels), and regularization strengths (4 levels), retaining solutions within an ISE tolerance of the baseline fit.

Output quantities (S24, RMST24 and their between-arm differences) are reported as feasible-set envelopes (min, median, max), not point estimates.

Four sources of uncertainty are characterized: digitization error, HR uncertainty (log-normal bootstrap), model family choice (Weibull, Royston-Parmar), and regularization/knot selection.

## Trials

**INDIGO** (Mellinghoff et al., NEJM 2023): vorasidenib vs placebo in residual/recurrent grade 2 IDH-mutant glioma. N=331. Endpoints: PFS (HR 0.39), TTNI (HR 0.26). Four two-level factors analyzed for each endpoint.

**CheckMate 498** (Reardon et al., Neuro-Oncology 2020): nivolumab + RT vs TMZ + RT in newly diagnosed GBM with unmethylated MGMT. N=560. Endpoint: OS (HR 1.28). Four two-level factors analyzed in blinded phase (main paper only) and unblinded phase (with supplement).

## License

This reproducibility package is provided for academic and research purposes.
