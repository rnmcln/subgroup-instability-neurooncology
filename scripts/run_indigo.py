#!/usr/bin/env python3
"""
Run the full INDIGO reconstruction pipeline.

Usage:
    python scripts/run_indigo.py --pdf <path_to_NEJMoa2304194.pdf> --out data/extracted/indigo
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.extract_indigo import run_indigo_extraction
from src.reconstruct import (
    run_feasible_set, bootstrap_hr_uncertainty, fit_piecewise_factor,
    factor_metrics, fit_metrics, extract_subgroup_curves,
    fit_weibull_shared, fit_rp_shared, synthetic_identifiability_demo,
)
from src.utils import interp_survival, common_time_grid
from src.plotting import (
    plot_digitised_curves, plot_fit_comparison, plot_feasible_envelopes,
    plot_synthetic_demo, plot_envelope_summary_table, save_figure,
)


INDIGO_CONFIG = {
    "render_dpi": 200,
    "page_index_fig2": 7,
    "page_index_fig3": 9,
    "fig2_upper_crop": [110, 150, 1500, 900],
    "fig2_lower_crop": [110, 960, 1500, 1710],
    "panelA_plot_crop": [130, 70, 1085, 520],
    "panelB_plot_crop": [130, 60, 1085, 500],
    "x_max_months": 30.0,
}

INDIGO_FACTORS_PFS = {
    "Chromosome 1p/19q codeletion status": ["Codeleted", "Non-codeleted"],
    "Location of tumor at initial diagnosis": ["Frontal lobe", "Nonfrontal lobe"],
    "Longest diameter of tumor at baseline": ["<2 cm", "\u22652 cm"],
    "No. of previous surgeries": ["1", "\u22652"],
}

INDIGO_FACTORS_TNI = {
    "Chromosome 1p/19q codeletion status": ["Codeleted", "Non-codeleted"],
    "Location of tumor at initial diagnosis": ["Frontal", "Nonfrontal"],
    "Longest diameter of tumor at baseline": ["<2 cm", "\u22652 cm"],
    "No. of previous surgeries": ["1", "\u22652"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="Path to NEJMoa2304194.pdf")
    ap.add_argument("--out", default="data/extracted/indigo", help="Output directory for extracted data")
    ap.add_argument("--results", default="outputs", help="Directory for analysis results")
    ap.add_argument("--figures", default="figures", help="Directory for figures")
    args = ap.parse_args()

    out = Path(args.out)
    results = Path(args.results)
    figures = Path(args.figures)
    out.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    print("=== INDIGO: Data extraction ===")
    extraction = run_indigo_extraction(args.pdf, INDIGO_CONFIG, str(out))
    print(f"  Extracted KM PFS: {extraction['km_pfs']}")
    print(f"  Extracted KM TTNI: {extraction['km_tni']}")
    print(f"  Anchors: {extraction['anchors']}")

    # Load extracted data
    km_pfs = pd.read_csv(out / "km_digitised_pfs.csv")
    km_tni_path = out / "km_digitised_tni_anchored.csv"
    if km_tni_path.exists():
        km_tni = pd.read_csv(km_tni_path)
    else:
        km_tni = pd.read_csv(out / "km_digitised_tni.csv")
    fp_pfs = pd.read_csv(out / "forestplot_pfs.csv")
    fp_tni = pd.read_csv(out / "forestplot_tni.csv")

    forest_pfs = fp_pfs[fp_pfs["hr"].notna()].copy()
    forest_tni = fp_tni[fp_tni["hr"].notna()].copy()

    arm_names = ("vorasidenib", "placebo")

    # QA plots
    print("=== INDIGO: QA plots ===")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    plot_digitised_curves(km_pfs, "PFS", ax=axes[0])
    plot_digitised_curves(km_tni, "TTNI", ax=axes[1])
    fig.tight_layout()
    save_figure(fig, figures / "qa_digitised_indigo")

    # === PFS Feasible-set reconstruction ===
    print("=== INDIGO PFS: Feasible-set reconstruction ===")
    all_solutions_pfs = []
    all_summaries_pfs = []

    for factor_name, sublabels in INDIGO_FACTORS_PFS.items():
        print(f"  Factor: {factor_name}")
        # Proportional hazards
        sols, summ = run_feasible_set(
            km_pfs, forest_pfs, factor_name, sublabels,
            arm_names=arm_names, tolerance_pct=0.30, tau_rmst=24.0,
        )
        if not sols.empty:
            all_solutions_pfs.append(sols)
            all_summaries_pfs.append(summ)
            sols.to_csv(results / f"pfs_{factor_name.replace(' ', '_').replace('/', '_')}_solutions.csv", index=False)

        # Time-varying HR sensitivity (for selected factors)
        if factor_name in ["Chromosome 1p/19q codeletion status", "Longest diameter of tumor at baseline"]:
            sols_tv, summ_tv = run_feasible_set(
                km_pfs, forest_pfs, factor_name, sublabels,
                arm_names=arm_names, allow_timevarying_hr=True,
                tolerance_pct=0.30, tau_rmst=24.0,
            )
            if not sols_tv.empty:
                sols_tv.to_csv(results / f"pfs_tvhr_{factor_name.replace(' ', '_').replace('/', '_')}_solutions.csv", index=False)
                all_solutions_pfs.append(sols_tv)

    if all_summaries_pfs:
        combined_summ_pfs = pd.concat(all_summaries_pfs, ignore_index=True)
        combined_summ_pfs.to_csv(results / "pfs_envelope_summaries_all.csv", index=False)
        plot_envelope_summary_table(combined_summ_pfs, figures / "Figure2_pfs_envelopes")
    if all_solutions_pfs:
        all_sols_pfs = pd.concat(all_solutions_pfs, ignore_index=True)
        all_sols_pfs.to_csv(results / "pfs_all_feasible_solutions.csv", index=False)

    # Tolerance sensitivity (20%, 40%)
    print("=== INDIGO PFS: Tolerance sensitivity ===")
    tol_results = []
    for tol in [0.20, 0.30, 0.40]:
        for factor_name, sublabels in INDIGO_FACTORS_PFS.items():
            sols, summ = run_feasible_set(
                km_pfs, forest_pfs, factor_name, sublabels,
                arm_names=arm_names, tolerance_pct=tol, tau_rmst=24.0,
            )
            if not summ.empty:
                summ["tolerance"] = tol
                tol_results.append(summ)
    if tol_results:
        pd.concat(tol_results, ignore_index=True).to_csv(results / "pfs_tolerance_sensitivity.csv", index=False)

    # HR uncertainty bootstrap (for selected factor)
    print("=== INDIGO PFS: HR uncertainty bootstrap ===")
    for factor_name, sublabels in list(INDIGO_FACTORS_PFS.items())[:2]:
        factor_df = forest_pfs[
            (forest_pfs["group"] == factor_name) & (forest_pfs["subgroup"].isin(sublabels))
        ].copy()
        if len(factor_df) == 2 and factor_df["hr"].notna().all():
            factor_df = factor_df.set_index("subgroup").loc[sublabels].reset_index()
            boot = bootstrap_hr_uncertainty(
                km_pfs, factor_df, arm_names=arm_names, n_boot=50, seed=42,
            )
            if not boot.empty:
                boot.to_csv(results / f"pfs_bootstrap_{factor_name.replace(' ', '_').replace('/', '_')}.csv", index=False)

    # Parametric-family sensitivity
    print("=== INDIGO PFS: Parametric-family sensitivity ===")
    model_sens = []
    for factor_name, sublabels in list(INDIGO_FACTORS_PFS.items())[:2]:
        factor_df = forest_pfs[
            (forest_pfs["group"] == factor_name) & (forest_pfs["subgroup"].isin(sublabels))
        ].copy()
        if len(factor_df) != 2 or factor_df["hr"].isna().any():
            continue
        factor_df = factor_df.set_index("subgroup").loc[sublabels].reset_index()

        for model_name in ["piecewise", "weibull", "rp"]:
            try:
                if model_name == "piecewise":
                    res, tg, A = fit_piecewise_factor(
                        km_pfs, factor_df, breaks=(0, 12, 24, 30),
                        arm_names=arm_names, maxiter=300,
                    )
                    m, Smc, Smt = factor_metrics(res, tg, A, factor_df, (0, 12, 24, 30))
                elif model_name == "weibull":
                    res_w, t_w = fit_weibull_shared(km_pfs, factor_df, arm_names=arm_names)
                    # Simplified metrics extraction for weibull
                    m = pd.DataFrame({"subgroup": sublabels, "model": model_name})
                elif model_name == "rp":
                    res_rp, t_rp, knots = fit_rp_shared(km_pfs, factor_df, arm_names=arm_names)
                    m = pd.DataFrame({"subgroup": sublabels, "model": model_name})

                m["factor"] = factor_name
                m["model"] = model_name
                model_sens.append(m)
            except Exception:
                continue

    if model_sens:
        pd.concat(model_sens, ignore_index=True).to_csv(results / "pfs_model_sensitivity.csv", index=False)

    # === TTNI Feasible-set reconstruction ===
    print("=== INDIGO TTNI: Feasible-set reconstruction ===")
    all_solutions_tni = []
    all_summaries_tni = []

    for factor_name, sublabels in INDIGO_FACTORS_TNI.items():
        print(f"  Factor: {factor_name}")
        sols, summ = run_feasible_set(
            km_tni, forest_tni, factor_name, sublabels,
            arm_names=arm_names, tolerance_pct=0.30, tau_rmst=24.0,
        )
        if not sols.empty:
            all_solutions_tni.append(sols)
            all_summaries_tni.append(summ)

    if all_summaries_tni:
        combined_summ_tni = pd.concat(all_summaries_tni, ignore_index=True)
        combined_summ_tni.to_csv(results / "tni_envelope_summaries_all.csv", index=False)
        plot_envelope_summary_table(combined_summ_tni, figures / "Figure3_tni_envelopes")
    if all_solutions_tni:
        pd.concat(all_solutions_tni, ignore_index=True).to_csv(results / "tni_all_feasible_solutions.csv", index=False)

    # === Fit diagnostics (Figure 1) ===
    print("=== INDIGO: Fit diagnostic plots ===")
    factor_name_demo = "Chromosome 1p/19q codeletion status"
    sublabels_demo = INDIGO_FACTORS_PFS[factor_name_demo]
    factor_df_demo = forest_pfs[
        (forest_pfs["group"] == factor_name_demo) & (forest_pfs["subgroup"].isin(sublabels_demo))
    ].copy()
    if len(factor_df_demo) == 2:
        factor_df_demo = factor_df_demo.set_index("subgroup").loc[sublabels_demo].reset_index()
        res_d, tg_d, A_d = fit_piecewise_factor(
            km_pfs, factor_df_demo, breaks=(0, 12, 24, 30),
            arm_names=arm_names, maxiter=300,
        )
        curves_d, Smc_d, Smt_d = extract_subgroup_curves(
            res_d, tg_d, A_d, factor_df_demo, (0, 12, 24, 30),
        )
        S_ctrl = interp_survival(km_pfs, "placebo", tg_d)
        S_trt = interp_survival(km_pfs, "vorasidenib", tg_d)

        fig, ax = plt.subplots(figsize=(5, 3.5))
        plot_fit_comparison(tg_d, S_ctrl, S_trt, Smc_d, Smt_d,
                           arm_labels=("placebo", "vorasidenib"), ax=ax)
        save_figure(fig, figures / "Figure1_fit_diagnostic")

    # Synthetic identifiability demo
    print("=== Synthetic identifiability demo ===")
    demo = synthetic_identifiability_demo()
    plot_synthetic_demo(demo, figures / "SupplementFigureS1_synthetic_demo")
    pd.DataFrame({
        "quantity": ["mixture_max_abs_diff", "dRMST24_A_sub1", "dRMST24_A_sub2", "dRMST24_B_sub1", "dRMST24_B_sub2"],
        "value": [demo["mixture_max_abs_diff"]] + demo["dRMST24_A"] + demo["dRMST24_B"],
    }).to_csv(results / "synthetic_demo_summary.csv", index=False)

    # === Results summary JSON ===
    print("=== INDIGO: Generating results summary ===")
    summary = {
        "trial": "INDIGO",
        "pdf": args.pdf,
        "anchors": extraction["anchors"],
        "n_factors_pfs": len(INDIGO_FACTORS_PFS),
        "n_factors_tni": len(INDIGO_FACTORS_TNI),
    }
    if all_summaries_pfs:
        for _, row in combined_summ_pfs.iterrows():
            key = f"pfs_{row['factor']}_{row['subgroup']}"
            key = key.replace(" ", "_").replace("/", "_")
            summary[f"{key}_dRMST24_med"] = round(float(row["dRMST24_med"]), 3)
            summary[f"{key}_dRMST24_range"] = f"[{row['dRMST24_min']:.3f}, {row['dRMST24_max']:.3f}]"

    with open(results / "results_summary_indigo.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=== INDIGO pipeline complete ===")
    return summary


if __name__ == "__main__":
    main()
