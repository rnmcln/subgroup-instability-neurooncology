"""
Utility functions for KM curve digitization, survival computations, and data handling.
"""
from __future__ import annotations
import numpy as np
import cv2
import pandas as pd


def digitize_curve_by_color(
    img_bgr: np.ndarray,
    color: str,
    hsv_ranges: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract pixel coordinates (x_px, y_px) of a curve identified by color in a BGR image.

    Parameters
    ----------
    img_bgr : array, shape (H, W, 3)
    color : str, one of 'red', 'blue', 'orange', 'gray'
    hsv_ranges : optional dict overriding default HSV ranges

    Returns
    -------
    xs, ys : 1-d arrays of pixel x, y coordinates (y increases downward)
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    defaults = {
        "red": [((0, 80, 80), (10, 255, 255)), ((160, 80, 80), (179, 255, 255))],
        "blue": [((90, 80, 80), (135, 255, 255))],
        "orange": [((5, 120, 120), (25, 255, 255))],
        "gray": [((0, 0, 80), (180, 50, 180))],
    }
    if hsv_ranges and color in hsv_ranges:
        ranges = hsv_ranges[color]
    else:
        ranges = defaults.get(color)
    if ranges is None:
        raise ValueError(f"Unknown color: {color}")

    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(lo), np.array(hi)))

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    h, w = mask.shape
    xs, ys = [], []
    for x in range(w):
        y_idx = np.where(mask[:, x] > 0)[0]
        if len(y_idx) == 0:
            continue
        y = int(np.median(y_idx))
        xs.append(x)
        ys.append(y)
    return np.asarray(xs), np.asarray(ys)


def px_to_data(
    xs: np.ndarray,
    ys: np.ndarray,
    width: int,
    height: int,
    x_max: float,
    y_min: float = 0.0,
    y_max: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert pixel coordinates to data coordinates."""
    months = xs / max(width - 1, 1) * x_max
    surv = y_max - (ys / max(height - 1, 1)) * (y_max - y_min)
    return months, surv


def enforce_monotone_nonincreasing(
    t: np.ndarray, s: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Sort by time and enforce non-increasing survival."""
    order = np.argsort(t)
    t = t[order]
    s = s[order]
    s = np.minimum.accumulate(s)
    return t, s


def interp_survival(km_df: pd.DataFrame, arm: str, t_grid: np.ndarray) -> np.ndarray:
    """Interpolate digitized KM data onto a common time grid."""
    d = km_df[km_df["arm"] == arm].sort_values("month")
    return np.interp(
        t_grid, d["month"].values, d["survival"].values,
        left=d["survival"].iloc[0], right=d["survival"].iloc[-1],
    )


def common_time_grid(km_df: pd.DataFrame, x_max: float = 30.0) -> np.ndarray:
    """Create union time grid from all arms."""
    t = np.unique(np.concatenate(
        [km_df[km_df["arm"] == a]["month"].values for a in km_df["arm"].unique()]
    ))
    return t[(t >= 0) & (t <= x_max)]


def rmst(t: np.ndarray, S: np.ndarray, tau: float) -> float:
    """Restricted mean survival time up to tau."""
    S_tau = float(np.interp(tau, t, S))
    mask = t < tau
    t2 = np.append(t[mask], tau)
    S2 = np.append(S[mask], S_tau)
    return float(np.trapz(S2, t2))


def surv_at(t: np.ndarray, S: np.ndarray, time_point: float) -> float:
    """Survival probability at a specific time point."""
    return float(np.interp(time_point, t, S))


def find_plot_region(img_bgr: np.ndarray, min_w: int = 200, min_h: int = 200) -> tuple[int, int, int, int]:
    """Detect the largest rectangular plot region in an image."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_area = 0
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area > best_area and w > min_w and h > min_h:
            best = (x, y, w, h)
            best_area = area
    if best is None:
        raise RuntimeError("Could not find plot rectangle")
    return best


def digitise_panel(
    panel_img: np.ndarray,
    x_max_months: float,
    arm_colors: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """Digitise a KM panel image into a tidy DataFrame."""
    if arm_colors is None:
        arm_colors = [("treatment", "red"), ("control", "blue")]

    h, w = panel_img.shape[:2]
    rows = []
    for arm_name, color in arm_colors:
        xs, ys = digitize_curve_by_color(panel_img, color=color)
        if len(xs) == 0:
            continue
        months, surv = px_to_data(xs, ys, width=w, height=h, x_max=x_max_months)
        months, surv = enforce_monotone_nonincreasing(months, surv)
        # Prepend (0, 1) anchor
        months = np.insert(months, 0, 0.0)
        surv = np.insert(surv, 0, 1.0)
        for m, s in zip(months, surv):
            rows.append({"arm": arm_name, "month": float(m), "survival": float(s)})
    return pd.DataFrame(rows).sort_values(["arm", "month"]).reset_index(drop=True)


def perturb_km(
    km_df: pd.DataFrame, sd: float = 0.012, seed: int = 0
) -> pd.DataFrame:
    """Add small Gaussian noise to digitized survival for uncertainty quantification."""
    rng = np.random.default_rng(seed)
    out = []
    for arm, d in km_df.groupby("arm"):
        d = d.sort_values("month").copy()
        s = d["survival"].values.copy()
        noise = rng.normal(0, sd, size=len(s))
        noise[0] = 0.0  # preserve S(0)=1
        s2 = np.clip(s + noise, 0, 1)
        s2 = np.minimum.accumulate(s2)
        out.append(pd.DataFrame({"arm": arm, "month": d["month"].values, "survival": s2}))
    return pd.concat(out, ignore_index=True)
