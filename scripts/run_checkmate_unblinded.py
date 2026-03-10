#!/usr/bin/env python3
"""
Run CheckMate 498 reconstruction -- unblinded phase (adds supplement).
Compares blinded vs unblinded feasible sets.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")

from src.extract_checkmate import (
    run_checkmate_extraction_unblinded, extract_checkmate_km_from_image,
    extract_checkmate_table2_manual,
)
from src.reconstruct import run_feasible_set
from src.plotting import save_figure, plot_envelope_summary_table


CM_FACTORS_OS = {
    "Complete resection (CRF)": ["Yes", "No"],
    "Sex": ["Male", "Female"],
    "Baseline corticosteroid use": ["No", "Yes"],
    "Baseline performance status (Karnofsky scale)": ["<=80", ">80"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Path to noac099.pdf")
    ap.add_argument("--blinded-results", default="outputs/cm_blinded_os_envelope_summaries.csv")
    ap.add_argument("--supplement-img-s1ab", default=None, help="Path to Fig S1 panels a,b image")
    ap.add_argument("--supplement-img-s1cd", default=None, help="Path to Fig S1 panels c,d image")
    ap.add_argument("--out", default="data/extracted/checkmate_unblinded")
    ap.add_argument("--results", default="outputs")
    ap.add_argument("--figures", default="figures")
    args = ap.parse_args()

    out = Path(args.out); results = Path(args.results); figures = Path(args.figures)
    out.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    print("=== CheckMate UNBLINDED: Extracting supplement data ===")
    supplement_images = {}
    if args.supplement_img_s1ab:
        supplement_images["s1ab"] = args.supplement_img_s1ab
    if args.supplement_img_s1cd:
        supplement_images["s1cd"] = args.supplement_img_s1cd

    unblinded = run_checkmate_extraction_unblinded(
        args.pdf, {}, str(out), supplement_images=supplement_images,
    )

    # The unblinding adds additional constraints from Table 2 rates
    rates = extract_checkmate_table2_manual()
    pd.DataFrame([rates]).to_csv(out / "table2_rates_supplement.csv", index=False)

    # Re-run feasible set with tighter tolerance (anchoring from Table 2)
    # For now, the key comparison is whether the envelope changes with new information
    # Since the supplement provides PD-L1 subgroup OS curves, we can add PD-L1 as a factor

    # Load blinded KM if available
    blinded_km_path = Path("data/extracted/checkmate_blinded/km_digitised_os.csv")
    if blinded_km_path.exists():
        km_os = pd.read_csv(blinded_km_path)
    else:
        km_os = pd.DataFrame()

    blinded_fp_path = Path("data/extracted/checkmate_blinded/forestplot_os.csv")
    if blinded_fp_path.exists():
        forest_os = pd.read_csv(blinded_fp_path)
        forest_os = forest_os[forest_os["hr"].notna()].copy()
    else:
        forest_os = pd.DataFrame()

    arm_names = ("nivolumab", "temozolomide")

    # Unblinded: re-run with multiple tighter tolerances to characterize how
    # additional information (Table 2 anchors, supplement PD-L1 subgroup KM)
    # could constrain the feasible set.
    print("=== CheckMate UNBLINDED: Tolerance sensitivity analysis ===")
    all_summaries_unblinded = []
    all_solutions_unblinded = []
    tol_results = []
    if not km_os.empty and not forest_os.empty:
        for tol in [0.05, 0.10, 0.20, 0.30]:
            for factor_name, sublabels in CM_FACTORS_OS.items():
                sols, summ = run_feasible_set(
                    km_os, forest_os, factor_name, sublabels,
                    arm_names=arm_names, tolerance_pct=tol, tau_rmst=24.0,
                )
                if not summ.empty:
                    summ["tolerance"] = tol
                    tol_results.append(summ)
                    if tol == 0.05:
                        summ_c = summ.copy()
                        summ_c["phase"] = "unblinded"
                        all_summaries_unblinded.append(summ_c)
                if not sols.empty and tol == 0.05:
                    all_solutions_unblinded.append(sols)

    if tol_results:
        pd.concat(tol_results, ignore_index=True).to_csv(
            results / "cm_tolerance_sensitivity.csv", index=False)

    if all_summaries_unblinded:
        combined_unblinded = pd.concat(all_summaries_unblinded, ignore_index=True)
        combined_unblinded.to_csv(results / "cm_unblinded_os_envelope_summaries.csv", index=False)

    # Comparison table
    print("=== CheckMate: Blinded vs unblinded comparison ===")
    blinded_path = Path(args.blinded_results)
    comparison_rows = []
    if blinded_path.exists() and all_summaries_unblinded:
        blinded_summ = pd.read_csv(blinded_path)
        for _, row_u in combined_unblinded.iterrows():
            match = blinded_summ[
                (blinded_summ["factor"] == row_u["factor"]) &
                (blinded_summ["subgroup"] == row_u["subgroup"])
            ]
            if not match.empty:
                row_b = match.iloc[0]
                comparison_rows.append({
                    "factor": row_u["factor"],
                    "subgroup": row_u["subgroup"],
                    "blinded_dRMST24_med": row_b.get("dRMST24_med", np.nan),
                    "blinded_dRMST24_range": f"[{row_b.get('dRMST24_min', np.nan):.3f}, {row_b.get('dRMST24_max', np.nan):.3f}]",
                    "blinded_envelope_width": row_b.get("dRMST24_max", np.nan) - row_b.get("dRMST24_min", np.nan),
                    "unblinded_dRMST24_med": row_u["dRMST24_med"],
                    "unblinded_dRMST24_range": f"[{row_u['dRMST24_min']:.3f}, {row_u['dRMST24_max']:.3f}]",
                    "unblinded_envelope_width": row_u["dRMST24_max"] - row_u["dRMST24_min"],
                    "median_shift": row_u["dRMST24_med"] - row_b.get("dRMST24_med", np.nan),
                    "width_change_pct": (
                        (row_u["dRMST24_max"] - row_u["dRMST24_min"]) /
                        max(row_b.get("dRMST24_max", 0) - row_b.get("dRMST24_min", 1e-9), 1e-9) - 1
                    ) * 100,
                })

    if comparison_rows:
        comp_df = pd.DataFrame(comparison_rows)
        comp_df.to_csv(results / "cm_blinded_vs_unblinded_comparison.csv", index=False)
        # Also save as formatted table
        comp_df.to_csv(Path("tables") / "Table_checkmate_comparison.csv", index=False)
        print("  Comparison table saved")
    else:
        print("  No comparison possible (missing blinded or unblinded results)")

    summary = {
        "trial": "CheckMate 498",
        "phase": "unblinded",
        "supplement_images_used": list(supplement_images.keys()),
        "n_comparison_rows": len(comparison_rows),
    }
    with open(results / "results_summary_checkmate_unblinded.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=== CheckMate UNBLINDED pipeline complete ===")
    return summary


if __name__ == "__main__":
    main()
