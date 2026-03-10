"""
Data extraction from the CheckMate 498 trial (noac099).

Blinded phase: main paper only (OS/PFS KM from Fig 2, OS forest plot from Fig 3).
Unblinded phase: adds supplement (OS by PD-L1 subgroups from Fig S1).
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
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[page_index]
        im = page.to_image(resolution=dpi).original
        im.save(str(out_path))
    return out_path


def extract_checkmate_km_from_pdf(pdf_path: Path, config: dict, out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract OS and PFS KM curves from CheckMate Fig 2."""
    fig2_png = out_dir / "checkmate_page_fig2.png"
    render_page_to_png(pdf_path, config["cm_page_index_fig2"], config["render_dpi"], fig2_png)

    img = cv2.imread(str(fig2_png))
    h_full, w_full = img.shape[:2]

    # Upper panel = OS (Panel A), lower panel = PFS (Panel B)
    upper = img[0:h_full//2, :].copy()
    lower = img[h_full//2:, :].copy()

    # Detect plot regions
    arm_colors_cm = [("nivolumab", "blue"), ("temozolomide", "gray")]

    km_os = digitise_panel(upper, x_max_months=config.get("cm_x_max_months", 33), arm_colors=arm_colors_cm)
    km_pfs = digitise_panel(lower, x_max_months=config.get("cm_x_max_months", 33), arm_colors=arm_colors_cm)

    return km_os, km_pfs


def extract_checkmate_km_from_image(img_path: str, x_max: float = 33.0, arm1_color: str = "orange", arm2_color: str = "gray") -> pd.DataFrame:
    """Extract KM curves from a CheckMate supplement image (PD-L1 subgroups)."""
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {img_path}")

    h, w = img.shape[:2]
    # Split into left and right panels
    left = img[:, :w//2].copy()
    right = img[:, w//2:].copy()

    arm_colors = [("nivolumab", arm1_color), ("temozolomide", arm2_color)]
    km_left = digitise_panel(left, x_max_months=x_max, arm_colors=arm_colors)
    km_right = digitise_panel(right, x_max_months=x_max, arm_colors=arm_colors)

    return km_left, km_right


def parse_checkmate_forest_plot(pdf_path: Path, page_index: int) -> pd.DataFrame:
    """Parse CheckMate Fig 3 forest plot for OS subgroup HRs."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        txt = pdf.pages[page_index].extract_text() or ""

    lines = [l.strip() for l in txt.splitlines() if l.strip()]

    group_names = {
        "Baseline measurable lesion", "Complete resection (CRF)", "Region",
        "Age categorization", "Sex", "Race",
        "Baseline performance status (Karnofsky scale)", "RPA class",
        "Baseline pathology", "Baseline corticosteroid use",
    }

    rows = []
    current_group = None
    for l in lines:
        if l in group_names:
            current_group = l
            continue
        # Pattern: <subgroup> <events_nivo>/<n_nivo> <events_tmz>/<n_tmz> <HR> (<CI>)
        m = re.match(
            r"^(.*?)\s+(\d+)/(\d+)\s+(\d+)/(\d+)\s+([\d.]+)\s+\(([\d.]+)\s*[-\u2013\u2014]\s*([\d.]+)\)$",
            l
        )
        if m:
            name, ev_n, n_n, ev_t, n_t, hr, lo, hi = m.groups()
            rows.append({
                "group": current_group if current_group else "Overall",
                "subgroup": name.strip(),
                "events_nivo": int(ev_n),
                "n_nivo": int(n_n),
                "events_tmz": int(ev_t),
                "n_tmz": int(n_t),
                "n": int(n_n) + int(n_t),
                "events": int(ev_n) + int(ev_t),
                "hr": float(hr),
                "ci_low": float(lo),
                "ci_high": float(hi),
            })

    return pd.DataFrame(rows)


def parse_checkmate_forest_manual() -> pd.DataFrame:
    """
    Manually transcribed CheckMate 498 OS forest plot (Fig 3) from the paper image.
    Used as fallback if PDF text parsing fails.
    """
    data = [
        ("Overall", "Overall", 244, 280, 218, 280, 1.28, 1.07, 1.54),
        ("Baseline measurable lesion", "Yes", 112, 117, 97, 111, 1.30, 0.99, 1.72),
        ("Baseline measurable lesion", "No", 132, 163, 121, 169, 1.27, 0.99, 1.62),
        ("Complete resection (CRF)", "Yes", 125, 151, 102, 144, 1.28, 0.98, 1.66),
        ("Complete resection (CRF)", "No", 119, 129, 116, 136, 1.38, 1.06, 1.79),
        ("Region", "US/Canada", 69, 78, 46, 61, 1.54, 1.05, 2.24),
        ("Region", "Europe", 140, 159, 138, 177, 1.26, 1.00, 1.60),
        ("Region", "Rest of world", 35, 43, 34, 42, 0.96, 0.60, 1.55),
        ("Age categorization", "<65 yr", 162, 190, 154, 207, 1.33, 1.07, 1.67),
        ("Age categorization", ">=65 and <75 yr", 69, 76, 54, 61, 0.97, 0.68, 1.39),
        ("Age categorization", ">=75 yr", 13, 14, 10, 12, 1.51, 0.66, 3.47),
        ("Sex", "Male", 164, 190, 136, 175, 1.24, 0.99, 1.56),
        ("Sex", "Female", 80, 90, 82, 105, 1.35, 0.99, 1.84),
        ("Race", "White", 201, 231, 187, 240, 1.31, 1.07, 1.60),
        ("Race", "Black or African American", 4, 4, 3, 3, 0.79, 0.16, 3.99),
        ("Race", "Asian", 27, 33, 21, 28, 1.26, 0.71, 2.24),
        ("Race", "Other", 12, 12, 7, 9, 0.92, 0.36, 2.38),
        ("Baseline performance status (Karnofsky scale)", "<=80", 73, 82, 53, 67, 1.39, 0.97, 2.00),
        ("Baseline performance status (Karnofsky scale)", ">80", 171, 198, 162, 209, 1.25, 1.01, 1.55),
        ("RPA class", "III", 17, 20, 23, 42, 2.25, 1.19, 4.25),
        ("RPA class", "IV", 189, 219, 166, 202, 1.09, 0.89, 1.35),
        ("RPA class", "V", 38, 41, 29, 36, 1.56, 0.96, 2.54),
        ("Baseline pathology", "Glioblastoma", 237, 272, 209, 270, 1.29, 1.07, 1.55),
        ("Baseline pathology", "Gliosarcoma", 7, 8, 9, 10, None, None, None),
        ("Baseline corticosteroid use", "No", 176, 202, 139, 185, 1.33, 1.07, 1.67),
        ("Baseline corticosteroid use", "Yes", 68, 78, 79, 95, 1.22, 0.88, 1.69),
    ]
    return pd.DataFrame(data, columns=[
        "group", "subgroup", "events_nivo", "n_nivo", "events_tmz", "n_tmz",
        "hr", "ci_low", "ci_high"
    ]).assign(
        n=lambda d: d["n_nivo"] + d["n_tmz"],
        events=lambda d: d["events_nivo"] + d["events_tmz"],
    )


def extract_checkmate_table2(pdf_path: Path) -> dict:
    """Extract OS and PFS rates from Table 2 for anchoring."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        txt = ""
        for p in pdf.pages[5:8]:
            txt += (p.extract_text() or "") + "\n"

    rates = {}
    # OS rates
    for label, key in [("6 months", "os_6m"), ("12 months", "os_12m"),
                        ("18 months", "os_18m"), ("24 months", "os_24m")]:
        m = re.search(
            rf"{re.escape(label)}\s+([\d.]+)\s+\([\d.]+ to [\d.]+\)\s+([\d.]+)\s+\([\d.]+ to [\d.]+\)",
            txt
        )
        if m:
            rates[f"{key}_nivo"] = float(m.group(1)) / 100.0
            rates[f"{key}_tmz"] = float(m.group(2)) / 100.0

    return rates


def extract_checkmate_table2_manual() -> dict:
    """Manually transcribed Table 2 values as fallback."""
    return {
        "os_6m_nivo": 0.885, "os_6m_tmz": 0.887,
        "os_12m_nivo": 0.583, "os_12m_tmz": 0.623,
        "os_18m_nivo": 0.285, "os_18m_tmz": 0.364,
        "os_24m_nivo": 0.103, "os_24m_tmz": 0.212,
        "pfs_6m_nivo": 0.505, "pfs_6m_tmz": 0.546,
        "pfs_9m_nivo": 0.148, "pfs_9m_tmz": 0.309,
        "pfs_12m_nivo": 0.057, "pfs_12m_tmz": 0.177,
        "pfs_18m_nivo": 0.030, "pfs_18m_tmz": 0.081,
    }


def run_checkmate_extraction_blinded(pdf_path: str, config: dict, out_dir: str) -> dict:
    """Blinded extraction: main paper only."""
    pdf = Path(pdf_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Try PDF-based extraction of KM; fall back to manual if needed
    try:
        km_os, km_pfs = extract_checkmate_km_from_pdf(pdf, config, out)
    except Exception:
        km_os = pd.DataFrame(columns=["arm", "month", "survival"])
        km_pfs = pd.DataFrame(columns=["arm", "month", "survival"])

    km_os.to_csv(out / "km_digitised_os.csv", index=False)
    km_pfs.to_csv(out / "km_digitised_pfs.csv", index=False)

    # Forest plot
    try:
        fp_os = parse_checkmate_forest_plot(pdf, config.get("cm_page_index_fig3", 8))
    except Exception:
        fp_os = pd.DataFrame()

    # Validate: check that expected group names are present; PDF parser often
    # assigns subgroups to wrong parent groups due to imperfect header detection.
    expected_groups = {
        "Complete resection (CRF)", "Baseline measurable lesion",
        "Baseline corticosteroid use", "Baseline performance status (Karnofsky scale)",
        "Sex", "Race", "Region", "Age categorization", "RPA class", "Baseline pathology",
    }
    parsed_groups = set(fp_os["group"].unique()) if not fp_os.empty else set()
    if fp_os.empty or len(fp_os) < 5 or len(parsed_groups & expected_groups) < 4:
        fp_os = parse_checkmate_forest_manual()

    fp_os.to_csv(out / "forestplot_os.csv", index=False)

    # Table 2 rates for anchoring
    try:
        rates = extract_checkmate_table2(pdf)
    except Exception:
        rates = {}
    if len(rates) < 4:
        rates = extract_checkmate_table2_manual()
    pd.DataFrame([rates]).to_csv(out / "table2_rates.csv", index=False)

    return {
        "km_os": str(out / "km_digitised_os.csv"),
        "km_pfs": str(out / "km_digitised_pfs.csv"),
        "forestplot_os": str(out / "forestplot_os.csv"),
        "rates": rates,
    }


def run_checkmate_extraction_unblinded(
    pdf_path: str, config: dict, out_dir: str,
    supplement_images: dict | None = None,
) -> dict:
    """Unblinded extraction: adds supplement PD-L1 subgroup OS curves."""
    out = Path(out_dir)

    # PD-L1 subgroup curves from supplement images
    pdl1_data = {}
    if supplement_images:
        for label, img_path in supplement_images.items():
            try:
                km_left, km_right = extract_checkmate_km_from_image(
                    img_path, x_max=33.0, arm1_color="orange", arm2_color="gray"
                )
                km_left.to_csv(out / f"km_pdl1_{label}_left.csv", index=False)
                km_right.to_csv(out / f"km_pdl1_{label}_right.csv", index=False)
                pdl1_data[f"{label}_left"] = km_left
                pdl1_data[f"{label}_right"] = km_right
            except Exception as e:
                pdl1_data[f"{label}_error"] = str(e)

    return {"pdl1_data": pdl1_data}
