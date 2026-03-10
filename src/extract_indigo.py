"""
Data extraction from the INDIGO trial PDF (NEJMoa2304194).

Extracts:
- Figure 2 Panel A (PFS KM) and Panel B (TTNI KM) via color-based digitization
- Figure 3 (forest plots for PFS and TTNI) via text parsing
- Text-reported anchor probabilities for TTNI
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import pandas as pd
import pdfplumber
import cv2

from .utils import (
    digitize_curve_by_color, px_to_data, enforce_monotone_nonincreasing,
    find_plot_region, digitise_panel,
)


def render_page_to_png(pdf_path: Path, page_index: int, dpi: int, out_path: Path) -> Path:
    """Render a single PDF page to PNG."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[page_index]
        im = page.to_image(resolution=dpi).original
        im.save(str(out_path))
    return out_path


def extract_km_curves(pdf_path: Path, config: dict, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract PFS and TTNI KM curves from Figure 2."""
    fig2_png = out_dir / "page_fig2.png"
    render_page_to_png(pdf_path, config["page_index_fig2"], config["render_dpi"], fig2_png)

    img2 = cv2.imread(str(fig2_png))

    # Crop upper (PFS) and lower (TTNI) panels
    x1, y1, x2, y2 = config["fig2_upper_crop"]
    upper = img2[y1:y2, x1:x2].copy()
    x1, y1, x2, y2 = config["fig2_lower_crop"]
    lower = img2[y1:y2, x1:x2].copy()

    # Find plot rectangles
    ru = find_plot_region(upper)
    rl = find_plot_region(lower)
    pu = upper[ru[1]:ru[1]+ru[3], ru[0]:ru[0]+ru[2]]
    pl = lower[rl[1]:rl[1]+rl[3], rl[0]:rl[0]+rl[2]]

    # Panel-specific plot area crops
    x1, y1, x2, y2 = config["panelA_plot_crop"]
    panelA = pu[y1:y2, x1:x2].copy()
    x1, y1, x2, y2 = config["panelB_plot_crop"]
    panelB = pl[y1:y2, x1:x2].copy()

    arm_colors = [("vorasidenib", "red"), ("placebo", "blue")]
    km_pfs = digitise_panel(panelA, x_max_months=config["x_max_months"], arm_colors=arm_colors)
    km_tni = digitise_panel(panelB, x_max_months=config["x_max_months"], arm_colors=arm_colors)

    return km_pfs, km_tni


def parse_forestplot_table(pdf_path: Path, page_index: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse Figure 3 forest plot text for PFS and TTNI subgroup data."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        txt = pdf.pages[page_index].extract_text() or ""
    lines = [l.strip() for l in txt.splitlines() if l.strip()]

    # Find panel boundaries
    a_start = None
    b_start = None
    for i, l in enumerate(lines):
        if "Progression-free Survival" in l and a_start is None:
            a_start = i
        if "Receipt of Next Intervention" in l:
            b_start = i

    if a_start is None or b_start is None:
        raise RuntimeError("Could not find forest plot panel headers")

    a_lines = lines[a_start+3:b_start]
    b_lines = lines[b_start+3:]

    group_names = {
        "Age", "Sex", "Geographic region",
        "Location of tumor at initial diagnosis",
        "Time from last surgery to randomization",
        "No. of previous surgeries",
        "Chromosome 1p/19q codeletion status",
        "Longest diameter of tumor at baseline",
    }

    def parse_panel(panel_lines):
        out = []
        current_group = None
        for l in panel_lines:
            if l in group_names:
                current_group = l
                continue
            m = re.match(
                r"^(.*)\s+(\d+)/(\d+)\s+\(([^)]+)\)\s+(NE|[\d.]+)\s+\(([^)]+)\)$", l
            )
            if not m:
                continue
            name, ev, n, pct, hr, ci = m.groups()
            if hr == "NE":
                hr_val = lo = hi = None
            else:
                hr_val = float(hr)
                ci = ci.replace("\u2013", "-").replace("\u2014", "-")
                parts = [x.strip() for x in ci.split("-")]
                lo = float(parts[0]) if parts[0] != "NE" else None
                hi = float(parts[1]) if len(parts) > 1 and parts[1] != "NE" else None
            out.append({
                "group": current_group if current_group else "Overall",
                "subgroup": name.strip(),
                "events": int(ev),
                "n": int(n),
                "pct": float(pct) if pct != "NE" else None,
                "hr": hr_val,
                "ci_low": lo,
                "ci_high": hi,
            })
        return pd.DataFrame(out)

    df_a = parse_panel(a_lines)
    df_b = parse_panel(b_lines)
    return df_a, df_b


def extract_tni_anchors(pdf_path: Path, page_index: int = 6) -> dict:
    """Extract text-reported TTNI probabilities for anchoring."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        txt = (pdf.pages[page_index].extract_text() or "")
    txt_clean = " ".join(txt.split()).replace("likeli- hood", "likelihood")
    txt_clean = txt_clean.replace("\u2014", "-").replace("\u2013", "-")

    anchors = {}
    m1 = re.search(r"by 18 months was\s+(\d+\.\d)%", txt_clean, re.IGNORECASE)
    m2 = re.search(r"as compared with\s+(\d+\.\d)%", txt_clean, re.IGNORECASE)
    m3 = re.search(r"by 24 months,.*?was\s+(\d+\.\d)%", txt_clean, re.IGNORECASE)

    if m1:
        anchors["vorasidenib_18m"] = float(m1.group(1)) / 100.0
    if m2:
        anchors["placebo_18m"] = float(m2.group(1)) / 100.0
    if m3:
        anchors["vorasidenib_24m"] = float(m3.group(1)) / 100.0

    return anchors


def anchor_tni_curves(
    km_tni: pd.DataFrame, v18: float, p18: float, v24: float,
    hr_overall: float = 0.26,
) -> pd.DataFrame:
    """
    Anchor TTNI curves to text-reported probabilities.

    If vorasidenib arm has fewer than 10 digitized points (common because
    the curve is very flat near 1.0 and hard to detect by color), construct
    it from the placebo arm using S_v(t) = S_p(t)^HR plus anchor corrections.
    """
    placebo_df = km_tni[km_tni["arm"] == "placebo"].sort_values("month")
    vora_df = km_tni[km_tni["arm"] == "vorasidenib"].sort_values("month")

    t_p = placebo_df["month"].values
    s_p = placebo_df["survival"].values
    if t_p[0] != 0.0:
        t_p = np.insert(t_p, 0, 0.0)
        s_p = np.insert(s_p, 0, 1.0)

    # Anchor placebo to p18
    s18_p = float(np.interp(18.0, t_p, s_p))
    corr_p = np.interp(t_p, [0.0, 18.0], [0.0, p18 - s18_p], left=0.0, right=p18 - s18_p)
    s_p_adj = np.clip(s_p + corr_p, 0, 1)
    s_p_adj = np.minimum.accumulate(s_p_adj)

    # Vorasidenib: construct from PH if digitization failed
    if len(vora_df) < 10:
        # Construct from placebo + HR
        s_v_ph = np.power(np.clip(s_p, 1e-10, 1.0), hr_overall)
        # Anchor corrections
        s18_v = float(np.interp(18.0, t_p, s_v_ph))
        s24_v = float(np.interp(24.0, t_p, s_v_ph))
        corr_t = [0.0, 18.0, 24.0, 30.0]
        corr_v = [0.0, v18 - s18_v, v24 - s24_v, v24 - s24_v]
        corr = np.interp(t_p, corr_t, corr_v, left=0.0, right=corr_v[-1])
        s_v_adj = np.clip(s_v_ph + corr, 0, 1)
        s_v_adj = np.minimum.accumulate(s_v_adj)
        t_v = t_p
    else:
        t_v = vora_df["month"].values
        s_v = vora_df["survival"].values
        if t_v[0] != 0.0:
            t_v = np.insert(t_v, 0, 0.0)
            s_v = np.insert(s_v, 0, 1.0)
        s18_v = float(np.interp(18.0, t_v, s_v))
        s24_v = float(np.interp(24.0, t_v, s_v))
        corr_t = [0.0, 18.0, 24.0]
        corr_v = [0.0, v18 - s18_v, v24 - s24_v]
        corr = np.interp(t_v, corr_t, corr_v, left=0.0, right=corr_v[-1])
        s_v_adj = np.clip(s_v + corr, 0, 1)
        s_v_adj = np.minimum.accumulate(s_v_adj)

    plac_out = pd.DataFrame({"arm": "placebo", "month": t_p, "survival": s_p_adj})
    vora_out = pd.DataFrame({"arm": "vorasidenib", "month": t_v, "survival": s_v_adj})
    return pd.concat([vora_out, plac_out], ignore_index=True)


def run_indigo_extraction(pdf_path: str, config: dict, out_dir: str) -> dict:
    """Run the full INDIGO extraction pipeline. Returns paths to output files."""
    pdf = Path(pdf_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # KM curves
    km_pfs, km_tni = extract_km_curves(pdf, config, out)
    km_pfs.to_csv(out / "km_digitised_pfs.csv", index=False)
    km_tni.to_csv(out / "km_digitised_tni.csv", index=False)

    # Forest plots
    fp_pfs, fp_tni = parse_forestplot_table(pdf, config["page_index_fig3"])
    fp_pfs.to_csv(out / "forestplot_pfs.csv", index=False)
    fp_tni.to_csv(out / "forestplot_tni.csv", index=False)

    # TTNI anchors
    anchors = extract_tni_anchors(pdf)
    if all(k in anchors for k in ["vorasidenib_18m", "placebo_18m", "vorasidenib_24m"]):
        km_tni_a = anchor_tni_curves(
            km_tni,
            v18=anchors["vorasidenib_18m"],
            p18=anchors["placebo_18m"],
            v24=anchors["vorasidenib_24m"],
        )
        km_tni_a.to_csv(out / "km_digitised_tni_anchored.csv", index=False)
    else:
        km_tni_a = km_tni

    # Save anchors metadata
    pd.DataFrame([anchors]).to_csv(out / "tni_anchors.csv", index=False)

    return {
        "km_pfs": str(out / "km_digitised_pfs.csv"),
        "km_tni": str(out / "km_digitised_tni.csv"),
        "km_tni_anchored": str(out / "km_digitised_tni_anchored.csv"),
        "forestplot_pfs": str(out / "forestplot_pfs.csv"),
        "forestplot_tni": str(out / "forestplot_tni.csv"),
        "anchors": anchors,
    }
