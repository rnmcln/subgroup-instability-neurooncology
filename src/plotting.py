"""
Publication-quality figure generation.

Style: sans-serif font, no embedded titles, clean axis labels,
consistent tick formatting, minimal decoration.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


# Global style
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


def save_figure(fig, path: str | Path, formats=("pdf", "png")):
    """Save figure in multiple formats."""
    p = Path(path)
    for fmt in formats:
        fig.savefig(p.with_suffix(f".{fmt}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_digitised_curves(km_df: pd.DataFrame, endpoint_label: str, ax=None):
    """Plot digitized KM curves for both arms."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 3.5))
    else:
        fig = ax.get_figure()

    colors = {"vorasidenib": "#D62728", "placebo": "#1F77B4",
              "nivolumab": "#D62728", "temozolomide": "#7F7F7F",
              "treatment": "#D62728", "control": "#1F77B4"}

    for arm in km_df["arm"].unique():
        d = km_df[km_df["arm"] == arm].sort_values("month")
        c = colors.get(arm, "#333333")
        ax.step(d["month"], d["survival"], where="post", label=arm, color=c, linewidth=1.2)

    ax.set_xlabel("Months")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(-0.02, 1.05)
    ax.xaxis.set_major_locator(MultipleLocator(6))
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.legend(frameon=False)
    return fig, ax


def plot_fit_comparison(t_grid, S_obs_ctrl, S_obs_trt, S_fit_ctrl, S_fit_trt,
                        arm_labels=("control", "treatment"), ax=None):
    """Plot observed vs fitted mixture curves."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 3.5))
    else:
        fig = ax.get_figure()

    ax.plot(t_grid, S_obs_ctrl, "b-", linewidth=1.2, label=f"Digitized {arm_labels[0]}", alpha=0.8)
    ax.plot(t_grid, S_obs_trt, "r-", linewidth=1.2, label=f"Digitized {arm_labels[1]}", alpha=0.8)
    ax.plot(t_grid, S_fit_ctrl, "b--", linewidth=1.0, label=f"Fitted mixture {arm_labels[0]}", alpha=0.7)
    ax.plot(t_grid, S_fit_trt, "r--", linewidth=1.0, label=f"Fitted mixture {arm_labels[1]}", alpha=0.7)

    ax.set_xlabel("Months")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(-0.02, 1.05)
    ax.xaxis.set_major_locator(MultipleLocator(6))
    ax.legend(frameon=False, fontsize=7)
    return fig, ax


def plot_feasible_envelopes(solutions_df: pd.DataFrame, factor_name: str,
                            metric: str = "dRMST24", out_path: str | None = None):
    """Plot feasible-set envelopes as strip/box for each subgroup."""
    if solutions_df.empty:
        return None

    fdf = solutions_df[solutions_df["factor"] == factor_name].copy()
    if fdf.empty:
        return None

    subs = fdf["subgroup"].unique()
    fig, ax = plt.subplots(figsize=(5, 2.5 + 0.5 * len(subs)))

    for i, sub in enumerate(subs):
        vals = fdf[fdf["subgroup"] == sub][metric].values
        ax.scatter(vals, np.full_like(vals, i), alpha=0.3, s=8, color="#4C72B0", zorder=2)
        ax.plot([vals.min(), vals.max()], [i, i], color="#4C72B0", linewidth=2, zorder=1)
        med = np.median(vals)
        ax.plot(med, i, "D", color="#C44E52", markersize=6, zorder=3)

    ax.set_yticks(range(len(subs)))
    ax.set_yticklabels(subs)
    ax.set_xlabel(metric.replace("_", " "))
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--", zorder=0)

    fig.tight_layout()
    if out_path:
        save_figure(fig, out_path)
    return fig


def plot_synthetic_demo(demo: dict, out_path: str | None = None):
    """Plot the synthetic identifiability demonstration."""
    t = demo["t"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    # Panel 1: control arm mixtures
    ax = axes[0]
    ax.plot(t, demo["S_mix_ctrl"], "k-", linewidth=1.5, label="Mixture (both configs)")
    ax.plot(t, demo["S_sub_ctrl_A"][:, 0], "b--", linewidth=1, label="Config A: subgroup 1", alpha=0.7)
    ax.plot(t, demo["S_sub_ctrl_A"][:, 1], "b:", linewidth=1, label="Config A: subgroup 2", alpha=0.7)
    ax.plot(t, demo["S_sub_ctrl_B"][:, 0], "r--", linewidth=1, label="Config B: subgroup 1", alpha=0.7)
    ax.plot(t, demo["S_sub_ctrl_B"][:, 1], "r:", linewidth=1, label="Config B: subgroup 2", alpha=0.7)
    ax.set_xlabel("Months")
    ax.set_ylabel("Survival probability")
    ax.legend(frameon=False, fontsize=6)
    ax.set_ylim(-0.02, 1.05)

    # Panel 2: treatment arm mixtures
    ax = axes[1]
    ax.plot(t, demo["S_mix_trt_A"], "k-", linewidth=1.5, label="Mixture config A")
    ax.plot(t, demo["S_mix_trt_B"], "k--", linewidth=1.5, label="Mixture config B")
    ax.plot(t, demo["S_sub_trt_A"][:, 0], "b--", linewidth=1, alpha=0.5, label="A: sub1 (trt)")
    ax.plot(t, demo["S_sub_trt_A"][:, 1], "b:", linewidth=1, alpha=0.5, label="A: sub2 (trt)")
    ax.plot(t, demo["S_sub_trt_B"][:, 0], "r--", linewidth=1, alpha=0.5, label="B: sub1 (trt)")
    ax.plot(t, demo["S_sub_trt_B"][:, 1], "r:", linewidth=1, alpha=0.5, label="B: sub2 (trt)")
    ax.set_xlabel("Months")
    ax.set_ylabel("Survival probability")
    ax.legend(frameon=False, fontsize=6)
    ax.set_ylim(-0.02, 1.05)

    # Panel 3: absolute effects
    ax = axes[2]
    x = [0, 1]
    ax.bar([xi - 0.15 for xi in x], demo["dRMST24_A"], width=0.3, color="#4C72B0", label="Config A", alpha=0.8)
    ax.bar([xi + 0.15 for xi in x], demo["dRMST24_B"], width=0.3, color="#C44E52", label="Config B", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Subgroup 1", "Subgroup 2"])
    ax.set_ylabel("dRMST24 (months)")
    ax.legend(frameon=False)

    fig.tight_layout()
    if out_path:
        save_figure(fig, out_path)
    return fig


def plot_envelope_summary_table(summary_df: pd.DataFrame, out_path: str | None = None):
    """Generate a summary visualization of feasible-set envelopes across factors."""
    if summary_df.empty:
        return None

    factors = summary_df["factor"].unique()
    n_factors = len(factors)
    fig, axes = plt.subplots(1, 2, figsize=(10, 1.5 + 0.6 * summary_df.shape[0]))

    for col_idx, metric in enumerate(["dRMST24", "dS24"]):
        ax = axes[col_idx]
        y_pos = 0
        yticks = []
        ylabels = []

        for f in factors:
            fdf = summary_df[summary_df["factor"] == f]
            for _, row in fdf.iterrows():
                lo = row[f"{metric}_min"]
                hi = row[f"{metric}_max"]
                med = row[f"{metric}_med"]
                ax.plot([lo, hi], [y_pos, y_pos], color="#4C72B0", linewidth=3, solid_capstyle="round")
                ax.plot(med, y_pos, "D", color="#C44E52", markersize=5, zorder=3)
                yticks.append(y_pos)
                ylabels.append(f"{row['subgroup']}")
                y_pos += 1
            y_pos += 0.5  # gap between factors

        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, fontsize=7)
        ax.set_xlabel(metric.replace("_", " "))
        ax.axvline(0, color="gray", linewidth=0.5, linestyle="--", zorder=0)
        ax.invert_yaxis()

    fig.tight_layout()
    if out_path:
        save_figure(fig, out_path)
    return fig
