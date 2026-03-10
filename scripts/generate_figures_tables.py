#!/usr/bin/env python3
"""
Generate all publication-quality figures and formatted tables.

Figures:
  Figure 1: Synthetic identifiability demonstration
  Figure 2: INDIGO PFS feasible-set envelopes (all factors)
  Figure 3: INDIGO TTNI feasible-set envelopes (all factors)
  Figure 4: CheckMate OS feasible-set envelopes (blinded)
  Figure S1: Fit diagnostics -- digitised vs fitted mixture curves
  Figure S2: Tolerance sensitivity (INDIGO PFS)
  Figure S3: CheckMate tolerance sensitivity

Tables:
  Table 1: INDIGO PFS envelope summaries
  Table 2: INDIGO TTNI envelope summaries
  Table 3: CheckMate blinded OS envelope summaries
  Table 4: CheckMate blinded vs unblinded comparison
  Table S1: INDIGO PFS tolerance sensitivity
  Table S2: INDIGO PFS model sensitivity
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from src.plotting import save_figure

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def make_envelope_figure(summary_path, title_prefix, out_path, metric_pairs=None):
    """Create a publication envelope figure from a summary CSV."""
    df = pd.read_csv(summary_path)
    if df.empty:
        return

    if metric_pairs is None:
        metric_pairs = [("dRMST24", "dRMST (months, 24-month)"),
                        ("dS24", "dS(24) (absolute difference)")]

    factors = df["factor"].unique()
    n_rows = df.shape[0]
    fig, axes = plt.subplots(1, len(metric_pairs),
                              figsize=(5 * len(metric_pairs), 1.5 + 0.55 * n_rows))
    if len(metric_pairs) == 1:
        axes = [axes]

    for col_idx, (metric, xlabel) in enumerate(metric_pairs):
        ax = axes[col_idx]
        y_pos = 0
        yticks, ylabels = [], []
        group_boundaries = []

        for f_idx, f in enumerate(factors):
            fdf = df[df["factor"] == f]
            if f_idx > 0:
                group_boundaries.append(y_pos - 0.25)
            for _, row in fdf.iterrows():
                lo = row[f"{metric}_min"]
                hi = row[f"{metric}_max"]
                med = row[f"{metric}_med"]
                ax.plot([lo, hi], [y_pos, y_pos], color="#4C72B0",
                        linewidth=3, solid_capstyle="round", zorder=2)
                ax.plot(med, y_pos, "D", color="#C44E52", markersize=5, zorder=3)
                yticks.append(y_pos)
                ylabels.append(row["subgroup"])
                y_pos += 1
            y_pos += 0.5

        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, fontsize=7)
        ax.set_xlabel(xlabel)
        ax.axvline(0, color="gray", linewidth=0.5, linestyle="--", zorder=0)
        for gb in group_boundaries:
            ax.axhline(gb, color="#cccccc", linewidth=0.3, zorder=0)
        ax.invert_yaxis()

        # Add factor group labels on left
        if col_idx == 0:
            current_y = 0
            for f in factors:
                n_sub = len(df[df["factor"] == f])
                mid_y = current_y + (n_sub - 1) / 2
                ax.annotate(f, xy=(-0.02, mid_y), xycoords=("axes fraction", "data"),
                           fontsize=6, fontweight="bold", ha="right", va="center",
                           color="#555555")
                current_y += n_sub + 0.5

    fig.tight_layout()
    save_figure(fig, out_path)
    print(f"  Saved: {out_path}")


def make_tolerance_figure(tol_path, out_path, factor_filter=None):
    """Show how envelope width changes with tolerance."""
    df = pd.read_csv(tol_path)
    if df.empty:
        return

    if factor_filter:
        df = df[df["factor"].isin(factor_filter)]

    df["envelope_width"] = df["dRMST24_max"] - df["dRMST24_min"]
    factors = df["factor"].unique()
    n_f = len(factors)
    fig, axes = plt.subplots(1, n_f, figsize=(3.5 * n_f, 3), sharey=True)
    if n_f == 1:
        axes = [axes]

    for i, f in enumerate(factors):
        ax = axes[i]
        fdf = df[df["factor"] == f]
        for sub in fdf["subgroup"].unique():
            sdf = fdf[fdf["subgroup"] == sub].sort_values("tolerance")
            ax.plot(sdf["tolerance"] * 100, sdf["envelope_width"],
                    "o-", markersize=4, label=sub, linewidth=1.2)
        ax.set_xlabel("Tolerance (%)")
        if i == 0:
            ax.set_ylabel("dRMST24 envelope width (months)")
        ax.set_title(f, fontsize=8)
        ax.legend(frameon=False, fontsize=6)

    fig.tight_layout()
    save_figure(fig, out_path)
    print(f"  Saved: {out_path}")


def format_table_csv(df, out_path, float_fmt=".3f"):
    """Save formatted table CSV."""
    for col in df.select_dtypes(include=[np.floating]).columns:
        df[col] = df[col].apply(lambda x: f"{x:{float_fmt}}" if pd.notna(x) else "")
    df.to_csv(out_path, index=False)
    print(f"  Table saved: {out_path}")


def main():
    figures = Path("figures")
    tables = Path("tables")
    figures.mkdir(exist_ok=True)
    tables.mkdir(exist_ok=True)

    print("=== Generating publication figures ===")

    # Figure 1: Synthetic demo (already generated)
    print("  Figure 1 (synthetic demo): already generated")

    # Figure 2: INDIGO PFS envelopes
    pfs_summ = Path("outputs/pfs_envelope_summaries_all.csv")
    if pfs_summ.exists():
        make_envelope_figure(pfs_summ, "INDIGO PFS",
                            figures / "Figure2_indigo_pfs_envelopes")

    # Figure 3: INDIGO TTNI envelopes
    tni_summ = Path("outputs/tni_envelope_summaries_all.csv")
    if tni_summ.exists():
        make_envelope_figure(tni_summ, "INDIGO TTNI",
                            figures / "Figure3_indigo_tni_envelopes")

    # Figure 4: CheckMate blinded envelopes
    cm_summ = Path("outputs/cm_blinded_os_envelope_summaries.csv")
    if cm_summ.exists():
        make_envelope_figure(cm_summ, "CheckMate 498 OS (blinded)",
                            figures / "Figure4_checkmate_blinded_envelopes")

    # Figure S2: Tolerance sensitivity (INDIGO PFS)
    tol_pfs = Path("outputs/pfs_tolerance_sensitivity.csv")
    if tol_pfs.exists():
        make_tolerance_figure(tol_pfs, figures / "FigureS2_tolerance_sensitivity_pfs")

    # Figure S3: CheckMate tolerance sensitivity
    tol_cm = Path("outputs/cm_tolerance_sensitivity.csv")
    if tol_cm.exists():
        make_tolerance_figure(tol_cm, figures / "FigureS3_tolerance_sensitivity_checkmate")

    print("\n=== Generating formatted tables ===")

    # Table 1: INDIGO PFS envelopes
    if pfs_summ.exists():
        df = pd.read_csv(pfs_summ)
        format_table_csv(df.copy(), tables / "Table1_indigo_pfs_envelopes.csv")

    # Table 2: INDIGO TTNI envelopes
    if tni_summ.exists():
        df = pd.read_csv(tni_summ)
        format_table_csv(df.copy(), tables / "Table2_indigo_tni_envelopes.csv")

    # Table 3: CheckMate blinded
    if cm_summ.exists():
        df = pd.read_csv(cm_summ)
        format_table_csv(df.copy(), tables / "Table3_checkmate_blinded_envelopes.csv")

    # Table 4: Comparison
    comp_path = Path("outputs/cm_blinded_vs_unblinded_comparison.csv")
    if comp_path.exists():
        df = pd.read_csv(comp_path)
        format_table_csv(df.copy(), tables / "Table4_checkmate_comparison.csv")

    # Table S1: Tolerance sensitivity
    if tol_pfs.exists():
        df = pd.read_csv(tol_pfs)
        # Pivot to show widths per tolerance
        df["envelope_width_dRMST24"] = df["dRMST24_max"] - df["dRMST24_min"]
        pivot = df.pivot_table(
            index=["factor", "subgroup"],
            columns="tolerance",
            values="envelope_width_dRMST24",
        ).reset_index()
        pivot.columns = [f"tol_{c}" if isinstance(c, float) else c for c in pivot.columns]
        format_table_csv(pivot, tables / "TableS1_tolerance_sensitivity_pfs.csv")

    # Table S2: Model sensitivity
    ms_path = Path("outputs/pfs_model_sensitivity.csv")
    if ms_path.exists():
        df = pd.read_csv(ms_path)
        format_table_csv(df.copy(), tables / "TableS2_model_sensitivity_pfs.csv")

    print("\n=== All figures and tables generated ===")


if __name__ == "__main__":
    main()
