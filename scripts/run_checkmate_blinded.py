#!/usr/bin/env python3
"""
Run CheckMate 498 reconstruction -- blinded phase (main paper only).
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")

from src.extract_checkmate import run_checkmate_extraction_blinded, parse_checkmate_forest_manual
from src.reconstruct import run_feasible_set, bootstrap_hr_uncertainty
from src.plotting import plot_digitised_curves, plot_envelope_summary_table, save_figure


CM_CONFIG = {
    "render_dpi": 200,
    "cm_page_index_fig2": 7,
    "cm_page_index_fig3": 8,
    "cm_x_max_months": 33,
}

# Two-level factor partitions from CheckMate Fig 3
CM_FACTORS_OS = {
    "Complete resection (CRF)": ["Yes", "No"],
    "Sex": ["Male", "Female"],
    "Baseline corticosteroid use": ["No", "Yes"],
    "Baseline performance status (Karnofsky scale)": ["<=80", ">80"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Path to noac099.pdf")
    ap.add_argument("--out", default="data/extracted/checkmate_blinded")
    ap.add_argument("--results", default="outputs")
    ap.add_argument("--figures", default="figures")
    args = ap.parse_args()

    out = Path(args.out); results = Path(args.results); figures = Path(args.figures)
    out.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    print("=== CheckMate BLINDED: Data extraction ===")
    extraction = run_checkmate_extraction_blinded(args.pdf, CM_CONFIG, str(out))

    km_os = pd.read_csv(out / "km_digitised_os.csv")
    fp_os = pd.read_csv(out / "forestplot_os.csv")
    forest_os = fp_os[fp_os["hr"].notna()].copy()

    arm_names = ("nivolumab", "temozolomide")

    # QA plot
    if not km_os.empty:
        fig, ax = plot_digitised_curves(km_os, "OS")
        save_figure(fig, figures / "qa_digitised_checkmate_os")

    # Feasible-set reconstruction for OS
    print("=== CheckMate BLINDED: OS feasible-set reconstruction ===")
    all_solutions = []
    all_summaries = []

    for factor_name, sublabels in CM_FACTORS_OS.items():
        print(f"  Factor: {factor_name}")
        if km_os.empty:
            print("    Skipped: no digitized OS KM curves available")
            continue
        sols, summ = run_feasible_set(
            km_os, forest_os, factor_name, sublabels,
            arm_names=arm_names, tolerance_pct=0.30, tau_rmst=24.0,
        )
        if not sols.empty:
            all_solutions.append(sols)
            all_summaries.append(summ)
            sols.to_csv(results / f"cm_blinded_os_{factor_name.replace(' ', '_').replace('/', '_')}_solutions.csv", index=False)

    if all_summaries:
        combined = pd.concat(all_summaries, ignore_index=True)
        combined.to_csv(results / "cm_blinded_os_envelope_summaries.csv", index=False)
        plot_envelope_summary_table(combined, figures / "Figure4_checkmate_blinded_envelopes")

    summary = {
        "trial": "CheckMate 498",
        "phase": "blinded",
        "n_factors": len(CM_FACTORS_OS),
        "n_solutions_total": sum(len(s) for s in all_solutions) if all_solutions else 0,
        "km_os_digitized": not km_os.empty,
    }
    with open(results / "results_summary_checkmate_blinded.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=== CheckMate BLINDED pipeline complete ===")
    return summary


if __name__ == "__main__":
    main()
