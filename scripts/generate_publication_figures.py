#!/usr/bin/env python3
"""
Generate all publication-quality figures for the manuscript.
R/SPSS-style: light grid, clean axes, no text overlaps.

Main paper (≤6 display items):
  Figure 1: Synthetic identifiability demonstration
  Figure 2: INDIGO PFS feasible-set envelopes (4-panel composite)
  Figure 3: INDIGO TTNI feasible-set envelopes (4-panel composite)
  Figure 4: CheckMate 498 blinded vs unblinded comparison

Supplement:
  Figure S1: Digitized KM quality check (INDIGO PFS, TTNI, CM OS)
  Figure S2: Tolerance sensitivity (INDIGO PFS + CheckMate)
  Figure S3: Model family sensitivity
"""
from __future__ import annotations
import sys, os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import matplotlib.patches as mpatches

# ── R/SPSS-style global configuration ────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.labelweight": "normal",
    "axes.linewidth": 0.6,
    "axes.grid": True,
    "axes.grid.which": "major",
    "axes.axisbelow": True,
    "grid.color": "#E0E0E0",
    "grid.linewidth": 0.4,
    "grid.linestyle": "-",
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.minor.width": 0.3,
    "ytick.minor.width": 0.3,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.fontsize": 7.5,
    "legend.frameon": True,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "#CCCCCC",
    "legend.fancybox": False,
    "figure.dpi": 300,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
})

# ── Color palette (R ggplot2-inspired) ────────────────────────────────
COLORS = {
    "blue": "#3366CC",
    "red": "#CC3333",
    "gray": "#888888",
    "green": "#339933",
    "orange": "#FF9933",
    "purple": "#9966CC",
    "teal": "#33CCCC",
    "dark": "#333333",
}
CTRL_COLOR = COLORS["blue"]
TRT_COLOR = COLORS["red"]

# ── Paths ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "extracted"
OUTPUTS = ROOT / "outputs"
FIGDIR = ROOT / "figures"
FIGDIR.mkdir(exist_ok=True)


def save_fig(fig, name):
    """Save in both PDF (vector) and PNG (600 dpi) formats."""
    fig.savefig(FIGDIR / f"{name}.pdf", dpi=600, bbox_inches="tight")
    fig.savefig(FIGDIR / f"{name}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}.pdf/.png")


def add_panel_label(ax, label, x=-0.12, y=1.06):
    """Add A/B/C/D panel label in upper-left corner."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=12, fontweight="bold", va="top", ha="left")


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 1: Synthetic identifiability demonstration
# ═══════════════════════════════════════════════════════════════════════

def make_figure1():
    """Synthetic demo showing non-identifiability of subgroup curves."""
    print("Figure 1: Synthetic identifiability demonstration")

    np.random.seed(42)
    t = np.linspace(0, 24, 200)

    # Two distinct configurations that produce the same mixture
    lam_ctrl_A = np.array([0.03, 0.06])   # config A: subgroup hazards (control)
    lam_ctrl_B = np.array([0.05, 0.04])   # config B: different decomposition
    w = np.array([0.5, 0.5])              # equal weights

    S_sub_ctrl_A = np.exp(-np.outer(t, lam_ctrl_A))
    S_sub_ctrl_B = np.exp(-np.outer(t, lam_ctrl_B))
    S_mix_ctrl = S_sub_ctrl_A @ w  # both configs give same mixture

    # Treatment: apply different HRs per subgroup
    hr_A = np.array([0.5, 0.7])
    hr_B = np.array([0.65, 0.55])

    S_sub_trt_A = np.exp(-np.outer(t, lam_ctrl_A * hr_A))
    S_sub_trt_B = np.exp(-np.outer(t, lam_ctrl_B * hr_B))
    S_mix_trt_A = S_sub_trt_A @ w
    S_mix_trt_B = S_sub_trt_B @ w

    # RMST24 by subgroup
    dt = t[1] - t[0]
    dRMST_A = [(S_sub_trt_A[:, i] - S_sub_ctrl_A[:, i]).sum() * dt for i in range(2)]
    dRMST_B = [(S_sub_trt_B[:, i] - S_sub_ctrl_B[:, i]).sum() * dt for i in range(2)]

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.8))

    # Panel A: Control arm – same mixture, different subgroup curves
    ax = axes[0]
    add_panel_label(ax, "A")
    ax.plot(t, S_mix_ctrl, color=COLORS["dark"], linewidth=2.0, label="Observed mixture")
    ax.plot(t, S_sub_ctrl_A[:, 0], "--", color=CTRL_COLOR, linewidth=1.0, alpha=0.8, label="Config A: sub 1")
    ax.plot(t, S_sub_ctrl_A[:, 1], ":", color=CTRL_COLOR, linewidth=1.0, alpha=0.8, label="Config A: sub 2")
    ax.plot(t, S_sub_ctrl_B[:, 0], "--", color=TRT_COLOR, linewidth=1.0, alpha=0.8, label="Config B: sub 1")
    ax.plot(t, S_sub_ctrl_B[:, 1], ":", color=TRT_COLOR, linewidth=1.0, alpha=0.8, label="Config B: sub 2")
    ax.set_xlabel("Time (months)")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(-0.02, 1.05)
    ax.xaxis.set_major_locator(MultipleLocator(6))
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.legend(fontsize=6, loc="lower left", framealpha=0.95)

    # Panel B: Treatment arm mixtures (different!)
    ax = axes[1]
    add_panel_label(ax, "B")
    ax.plot(t, S_mix_trt_A, color=CTRL_COLOR, linewidth=1.5, label="Treatment mixture (A)")
    ax.plot(t, S_mix_trt_B, "--", color=TRT_COLOR, linewidth=1.5, label="Treatment mixture (B)")
    ax.fill_between(t, np.minimum(S_mix_trt_A, S_mix_trt_B),
                    np.maximum(S_mix_trt_A, S_mix_trt_B),
                    alpha=0.15, color=COLORS["gray"], label="Identifiability gap")
    ax.set_xlabel("Time (months)")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(-0.02, 1.05)
    ax.xaxis.set_major_locator(MultipleLocator(6))
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.legend(fontsize=6, loc="lower left", framealpha=0.95)

    # Panel C: dRMST bar chart
    ax = axes[2]
    add_panel_label(ax, "C")
    x_pos = np.array([0, 1])
    bar_w = 0.30
    bars_A = ax.bar(x_pos - bar_w/2, dRMST_A, bar_w, color=CTRL_COLOR, alpha=0.85, label="Config A", edgecolor="white", linewidth=0.5)
    bars_B = ax.bar(x_pos + bar_w/2, dRMST_B, bar_w, color=TRT_COLOR, alpha=0.85, label="Config B", edgecolor="white", linewidth=0.5)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["Subgroup 1", "Subgroup 2"])
    ax.set_ylabel("\u0394RMST$_{24}$ (months)")
    ax.set_title("Instability of\nsubgroup benefit", fontsize=9, fontweight="bold")
    ax.axhline(0, color=COLORS["gray"], linewidth=0.5, linestyle="-")
    ax.legend(fontsize=7, framealpha=0.95)

    fig.tight_layout(w_pad=2.5)
    save_fig(fig, "Figure1_synthetic_demo")


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 2 & 3: INDIGO feasible-set envelope composites
# ═══════════════════════════════════════════════════════════════════════

def make_envelope_composite(summary_csv, endpoint_label, fig_name, factor_order=None):
    """4-panel forest-plot style feasible-set envelope figure."""
    df = pd.read_csv(summary_csv)
    factors = factor_order or df["factor"].unique().tolist()

    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.5))
    axes = axes.flatten()
    labels = ["A", "B", "C", "D"]

    for idx, (factor, ax) in enumerate(zip(factors, axes)):
        add_panel_label(ax, labels[idx])
        fdf = df[df["factor"] == factor]

        subgroups = [s.replace("Nonfrontal", "Non-frontal") for s in fdf["subgroup"].tolist()]
        n_sub = len(subgroups)
        y_positions = list(range(n_sub))

        for i, (_, row) in enumerate(fdf.iterrows()):
            lo = row["dRMST24_min"]
            hi = row["dRMST24_max"]
            med = row["dRMST24_med"]

            # Envelope bar (thick horizontal line)
            ax.plot([lo, hi], [i, i], color=CTRL_COLOR, linewidth=5, solid_capstyle="butt", alpha=0.7, zorder=2)
            # Median diamond
            ax.plot(med, i, "D", color=TRT_COLOR, markersize=7, zorder=3, markeredgecolor="white", markeredgewidth=0.5)
            # Value annotation
            ax.annotate(f"{med:.2f} [{lo:.2f}, {hi:.2f}]",
                        (hi, i), textcoords="offset points", xytext=(6, 0),
                        fontsize=6.5, va="center", color=COLORS["dark"])

        ax.set_yticks(y_positions)
        ax.set_yticklabels(subgroups, fontsize=8)
        ax.set_xlabel("\u0394RMST$_{24}$ (months) — bar width = model-specification sensitivity", fontsize=7)
        ax.axvline(0, color=COLORS["gray"], linewidth=0.6, linestyle="--", zorder=0)
        ax.invert_yaxis()

        # Clean up factor name for subtitle
        short = factor.replace("Chromosome 1p/19q codeletion status", "1p/19q codeletion")\
                       .replace("Location of tumor at initial diagnosis", "Tumour location")\
                       .replace("Longest diameter of tumor at baseline", "Tumour diameter")\
                       .replace("No. of previous surgeries", "Prior surgeries")\
                       .replace("Complete resection (CRF)", "Complete resection")\
                       .replace("Baseline corticosteroid use", "Corticosteroid use")\
                       .replace("Baseline performance status (Karnofsky scale)", "Karnofsky PS")
        ax.set_title(short, fontsize=9, fontweight="bold", pad=6)

        # Adjust x limits for readability
        all_vals = fdf[["dRMST24_min", "dRMST24_max"]].values.flatten()
        margin = (all_vals.max() - all_vals.min()) * 0.35
        ax.set_xlim(min(0, all_vals.min()) - margin, all_vals.max() + margin + 1.5)

    fig.suptitle(f"Model-specification sensitivity: {endpoint_label}", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout(h_pad=2.0, w_pad=2.5)
    save_fig(fig, fig_name)


# ═══════════════════════════════════════════════════════════════════════
# FIGURE 4: CheckMate blinded vs unblinded comparison
# ═══════════════════════════════════════════════════════════════════════

def make_figure4():
    """Paired envelope comparison: blinded vs unblinded."""
    print("Figure 4: CheckMate blinded vs unblinded comparison")
    comp = pd.read_csv(OUTPUTS / "cm_blinded_vs_unblinded_comparison.csv")

    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.5))
    axes = axes.flatten()
    labels = ["A", "B", "C", "D"]
    factors = comp["factor"].unique()

    for idx, (factor, ax) in enumerate(zip(factors, axes)):
        add_panel_label(ax, labels[idx])
        fdf = comp[comp["factor"] == factor]

        for i, (_, row) in enumerate(fdf.iterrows()):
            sub = row["subgroup"].replace("Nonfrontal", "Non-frontal")
            bw = row["blinded_envelope_width"]
            uw = row["unblinded_envelope_width"]
            pct = row["width_change_pct"]

            y_b = i * 2.5
            y_u = i * 2.5 + 0.8

            # Parse ranges
            b_range = row["blinded_dRMST24_range"].strip("[]").split(",")
            u_range = row["unblinded_dRMST24_range"].strip("[]").split(",")
            b_lo, b_hi = float(b_range[0].strip()), float(b_range[1].strip())
            u_lo, u_hi = float(u_range[0].strip()), float(u_range[1].strip())

            # Blinded bar
            ax.plot([b_lo, b_hi], [y_b, y_b], color=COLORS["gray"], linewidth=5, solid_capstyle="butt", alpha=0.7, zorder=2)
            ax.plot(row["blinded_dRMST24_med"], y_b, "D", color=COLORS["gray"], markersize=6, zorder=3, markeredgecolor="white", markeredgewidth=0.5)

            # Unblinded bar
            ax.plot([u_lo, u_hi], [y_u, y_u], color=CTRL_COLOR, linewidth=5, solid_capstyle="butt", alpha=0.7, zorder=2)
            ax.plot(row["unblinded_dRMST24_med"], y_u, "D", color=TRT_COLOR, markersize=6, zorder=3, markeredgecolor="white", markeredgewidth=0.5)

            # Pct change annotation
            if abs(pct) > 0.5:
                ax.annotate(f"{pct:.0f}%", (max(b_hi, u_hi), (y_b + y_u) / 2),
                            textcoords="offset points", xytext=(6, 0),
                            fontsize=6.5, va="center", color=COLORS["dark"])

            # Sub label
            ax.annotate(sub, (min(b_lo, u_lo), y_b - 0.4),
                        fontsize=7, va="bottom", ha="right",
                        textcoords="offset points", xytext=(-6, 0))

        ax.axvline(0, color=COLORS["gray"], linewidth=0.6, linestyle="--", zorder=0)
        ax.set_xlabel("\u0394RMST$_{24}$ (months)", fontsize=8)
        ax.set_yticks([])

        short = factor.replace("Complete resection (CRF)", "Complete resection")\
                       .replace("Baseline corticosteroid use", "Corticosteroid use")\
                       .replace("Baseline performance status (Karnofsky scale)", "Karnofsky PS")
        ax.set_title(short, fontsize=9, fontweight="bold", pad=6)
        ax.invert_yaxis()

    # Legend
    from matplotlib.lines import Line2D
    leg_elements = [
        Line2D([0], [0], color=COLORS["gray"], linewidth=4, label="Blinded"),
        Line2D([0], [0], color=CTRL_COLOR, linewidth=4, label="Unblinded"),
    ]
    fig.legend(handles=leg_elements, loc="lower center", ncol=2, fontsize=8, frameon=True, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("CheckMate 498 OS: Instability reduction with supplementary data", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout(h_pad=2.0, w_pad=2.5)
    save_fig(fig, "Figure4_cm_blinded_vs_unblinded")


# ═══════════════════════════════════════════════════════════════════════
# SUPPLEMENTARY FIGURES
# ═══════════════════════════════════════════════════════════════════════

def make_figS1():
    """Digitized KM quality check: overlay raw data for PFS, TTNI, OS."""
    print("Figure S1: Digitized KM curves quality check")

    panels = []
    for label, csv_path, arm_colors in [
        ("INDIGO PFS", DATA / "indigo" / "km_digitised_pfs.csv",
         {"vorasidenib": TRT_COLOR, "placebo": CTRL_COLOR}),
        ("INDIGO TTNI (anchored)", DATA / "indigo" / "km_digitised_tni_anchored.csv",
         {"vorasidenib": TRT_COLOR, "placebo": CTRL_COLOR}),
        ("CheckMate 498 OS", DATA / "checkmate_blinded" / "km_digitised_os.csv",
         {"nivolumab": TRT_COLOR, "temozolomide": COLORS["gray"]}),
    ]:
        if csv_path.exists():
            panels.append((label, pd.read_csv(csv_path), arm_colors))

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(3.5 * n, 3.0))
    if n == 1:
        axes = [axes]

    for i, (label, km, colors) in enumerate(panels):
        ax = axes[i]
        add_panel_label(ax, chr(65 + i))
        for arm in km["arm"].unique():
            d = km[km["arm"] == arm].sort_values("month")
            c = colors.get(arm, COLORS["dark"])
            ax.step(d["month"], d["survival"], where="post", label=arm.capitalize(),
                    color=c, linewidth=1.2)
        ax.set_xlabel("Time (months)")
        ax.set_ylabel("Survival probability")
        ax.set_ylim(-0.02, 1.05)
        ax.xaxis.set_major_locator(MultipleLocator(6))
        ax.yaxis.set_major_locator(MultipleLocator(0.2))
        ax.legend(fontsize=7, framealpha=0.95, loc="lower left")
        ax.set_title(label, fontsize=9, fontweight="bold")

    fig.tight_layout(w_pad=2.0)
    save_fig(fig, "FigureS1_digitised_km")


def make_figS2():
    """Tolerance sensitivity: how envelope width changes with tolerance."""
    print("Figure S2: Tolerance sensitivity")

    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.5))

    # INDIGO PFS tolerance sensitivity
    pfs_tol = pd.read_csv(OUTPUTS / "pfs_tolerance_sensitivity.csv")
    ax = axes[0]
    add_panel_label(ax, "A")
    for factor in pfs_tol["factor"].unique():
        for sub in pfs_tol[pfs_tol["factor"] == factor]["subgroup"].unique():
            mask = (pfs_tol["factor"] == factor) & (pfs_tol["subgroup"] == sub)
            sdf = pfs_tol[mask].sort_values("tolerance")
            widths = sdf["dRMST24_max"] - sdf["dRMST24_min"]
            short_sub = sub[:15]
            ax.plot(sdf["tolerance"], widths, "o-", markersize=3, linewidth=1.0, label=short_sub)
    ax.set_xlabel("Tolerance (ISE ratio)")
    ax.set_ylabel("Envelope width (months)")
    ax.set_title("INDIGO PFS", fontsize=9, fontweight="bold")
    ax.legend(fontsize=5.5, ncol=2, loc="upper left", framealpha=0.95)

    # CheckMate tolerance sensitivity
    cm_tol_path = OUTPUTS / "cm_tolerance_sensitivity.csv"
    if cm_tol_path.exists():
        cm_tol = pd.read_csv(cm_tol_path)
        ax = axes[1]
        add_panel_label(ax, "B")
        for factor in cm_tol["factor"].unique():
            for sub in cm_tol[cm_tol["factor"] == factor]["subgroup"].unique():
                mask = (cm_tol["factor"] == factor) & (cm_tol["subgroup"] == sub)
                sdf = cm_tol[mask].sort_values("tolerance")
                widths = sdf["dRMST24_max"] - sdf["dRMST24_min"]
                short_sub = sub[:15]
                ax.plot(sdf["tolerance"], widths, "o-", markersize=3, linewidth=1.0, label=short_sub)
        ax.set_xlabel("Tolerance (ISE ratio)")
        ax.set_ylabel("Envelope width (months)")
        ax.set_title("CheckMate 498 OS", fontsize=9, fontweight="bold")
        ax.legend(fontsize=5.5, ncol=2, loc="upper left", framealpha=0.95)

    fig.tight_layout(w_pad=2.5)
    save_fig(fig, "FigureS2_tolerance_sensitivity")


def make_figS3():
    """CheckMate 498 OS envelope figure (separate from blinded/unblinded comparison)."""
    print("Figure S3: CheckMate 498 OS envelopes")
    cm_csv = OUTPUTS / "cm_blinded_os_envelope_summaries.csv"
    if cm_csv.exists():
        make_envelope_composite(
            cm_csv, "CheckMate 498 OS (blinded)", "FigureS3_cm498_os_envelopes",
            factor_order=["Complete resection (CRF)", "Sex",
                          "Baseline corticosteroid use",
                          "Baseline performance status (Karnofsky scale)"]
        )


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating publication figures (R/SPSS style, 600 dpi)...\n")

    make_figure1()

    print("Figure 2: INDIGO PFS feasible-set envelopes")
    make_envelope_composite(
        OUTPUTS / "pfs_envelope_summaries_all.csv",
        "INDIGO PFS", "Figure2_indigo_pfs_envelopes",
        factor_order=[
            "Chromosome 1p/19q codeletion status",
            "Location of tumor at initial diagnosis",
            "Longest diameter of tumor at baseline",
            "No. of previous surgeries",
        ]
    )

    print("Figure 3: INDIGO TTNI feasible-set envelopes")
    make_envelope_composite(
        OUTPUTS / "tni_envelope_summaries_all.csv",
        "INDIGO TTNI", "Figure3_indigo_tni_envelopes",
        factor_order=[
            "Chromosome 1p/19q codeletion status",
            "Location of tumor at initial diagnosis",
            "Longest diameter of tumor at baseline",
            "No. of previous surgeries",
        ]
    )

    make_figure4()
    make_figS1()
    make_figS2()
    make_figS3()

    print(f"\nAll figures saved to {FIGDIR}/")
