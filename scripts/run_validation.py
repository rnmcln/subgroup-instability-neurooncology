#!/usr/bin/env python3
"""
Simulation validation study for the feasible-set reconstruction framework.

Generates synthetic trials with KNOWN ground-truth subgroup survival curves,
then reconstructs from aggregate KM + subgroup HR to test:
  1. Coverage: do feasible-set envelopes contain the true dRMST24?
  2. Calibration: is envelope width appropriate (not too wide/narrow)?
  3. Robustness: performance under varying signal strengths and sample sizes.

Scenarios:
  A. Well-separated subgroups (easy: large HR difference, large prevalence imbalance)
  B. Moderate separation (mimics INDIGO: realistic HR split, balanced prevalence)
  C. Near-null separation (hard: nearly identical subgroup baselines)
  D. Non-proportional hazards (model misspecification stress test)
  E. Small-sample noise (N=100 per arm, heavy digitization noise)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.reconstruct import run_feasible_set, fit_piecewise_factor, factor_metrics, fit_metrics
from src.utils import rmst


def generate_synthetic_trial(
    lam_ctrl: np.ndarray,  # shape (2,) or (2, J) for PWE
    hr_subgroup: np.ndarray,  # shape (2,) subgroup-specific HRs
    weights: np.ndarray,  # shape (2,) prevalence
    n_per_arm: int = 300,
    tau: float = 30.0,
    censor_rate: float = 0.15,
    seed: int = 42,
    nph_crossover_time: float = None,  # if set, HR flips after this time
):
    """
    Generate synthetic IPD from known piecewise-exponential subgroup model.
    Returns aggregate KM dataframe, forest-plot dataframe, and ground-truth metrics.
    """
    rng = np.random.default_rng(seed)

    # Assign subgroups
    n_total = 2 * n_per_arm
    n_sub = (weights * n_per_arm).astype(int)
    # Ensure sums match
    n_sub[0] = n_per_arm - n_sub[1]

    records = []
    for arm_idx, arm_name in enumerate(["treatment", "control"]):
        for g in range(2):
            n_g = int(n_sub[g])
            for _ in range(n_g):
                # Generate event time from exponential
                lam = lam_ctrl[g]
                if arm_name == "treatment":
                    hr = hr_subgroup[g]
                    if nph_crossover_time is not None:
                        # Non-PH: HR applies before crossover, 1/HR after
                        t_cross = nph_crossover_time
                        u = rng.uniform()
                        # Inverse CDF for piecewise hazard
                        lam_before = lam * hr
                        lam_after = lam * (1.0 / hr)
                        S_cross = np.exp(-lam_before * t_cross)
                        if u > S_cross:
                            # Event before crossover
                            event_time = -np.log(u) / lam_before
                        else:
                            # Event after crossover
                            event_time = t_cross + (-np.log(u) + lam_before * t_cross) / lam_after
                    else:
                        event_time = rng.exponential(1.0 / (lam * hr))
                else:
                    event_time = rng.exponential(1.0 / lam)

                censor_time = rng.exponential(1.0 / censor_rate) if censor_rate > 0 else tau + 10
                obs_time = min(event_time, censor_time, tau)
                event = 1 if event_time <= min(censor_time, tau) else 0

                records.append({
                    "arm": arm_name,
                    "subgroup": g,
                    "time": obs_time,
                    "event": event,
                })

    ipd = pd.DataFrame(records)

    # Compute KM from IPD (Greenwood formula omitted; step function suffices)
    km_rows = []
    for arm_name in ["treatment", "control"]:
        arm_data = ipd[ipd["arm"] == arm_name].sort_values("time")
        times = sorted(arm_data[arm_data["event"] == 1]["time"].unique())
        n_at_risk = len(arm_data)
        surv = 1.0
        km_rows.append({"arm": arm_name, "month": 0.0, "survival": 1.0})
        for t_event in times:
            n_events = len(arm_data[(arm_data["time"] == t_event) & (arm_data["event"] == 1)])
            n_censored_before = len(arm_data[(arm_data["time"] < t_event) & (arm_data["event"] == 0)])
            # Simple KM step
            d = n_events
            surv *= (1 - d / n_at_risk)
            n_at_risk -= d
            # Also remove censored before this time
            n_cens = len(arm_data[(arm_data["time"] <= t_event) & (arm_data["event"] == 0) & (arm_data["time"] > 0)])
            km_rows.append({"arm": arm_name, "month": t_event, "survival": max(surv, 0)})

    # Actually, let's use a proper lifelines-free KM estimator
    km_rows = []
    for arm_name in ["treatment", "control"]:
        arm_data = ipd[ipd["arm"] == arm_name].copy()
        arm_data = arm_data.sort_values("time")
        times_all = arm_data["time"].values
        events_all = arm_data["event"].values

        unique_times = np.sort(np.unique(times_all[events_all == 1]))
        n_total_arm = len(arm_data)

        km_rows.append({"arm": arm_name, "month": 0.0, "survival": 1.0})
        surv = 1.0
        n_at_risk = n_total_arm

        for t_i in unique_times:
            # Count events at this time
            d_i = np.sum((times_all == t_i) & (events_all == 1))
            # Count censored strictly before this time but after previous event time
            c_before = np.sum((times_all < t_i) & (events_all == 0) & (times_all > (km_rows[-1]["month"] if len(km_rows) > 1 else 0)))
            n_at_risk -= c_before
            surv *= (1 - d_i / max(n_at_risk, 1))
            n_at_risk -= d_i
            km_rows.append({"arm": arm_name, "month": float(t_i), "survival": max(surv, 0)})

    km_df = pd.DataFrame(km_rows)

    # Compute subgroup-level Cox-like HR from IPD
    # Simple approximation: observed event rate ratio
    forest_rows = []
    for g in range(2):
        sub_ipd = ipd[ipd["subgroup"] == g]
        trt_sub = sub_ipd[sub_ipd["arm"] == "treatment"]
        ctrl_sub = sub_ipd[sub_ipd["arm"] == "control"]

        # Log-rank style HR estimate
        d_trt = trt_sub["event"].sum()
        d_ctrl = ctrl_sub["event"].sum()
        py_trt = trt_sub["time"].sum()
        py_ctrl = ctrl_sub["time"].sum()

        rate_trt = d_trt / max(py_trt, 1)
        rate_ctrl = d_ctrl / max(py_ctrl, 1)
        hr_est = rate_trt / max(rate_ctrl, 1e-6)

        forest_rows.append({
            "group": "test_factor",
            "subgroup": f"subgroup_{g}",
            "n": len(sub_ipd) // 2,  # per arm
            "hr": hr_est,
            "ci_low": hr_est * 0.7,  # placeholder
            "ci_high": hr_est / 0.7,
        })

    forest_df = pd.DataFrame(forest_rows)

    # Ground-truth subgroup metrics from analytical model
    t_grid = np.linspace(0, 24, 500)
    truth = {}
    for g in range(2):
        lam_c = lam_ctrl[g]
        if nph_crossover_time is not None:
            # NPH treatment curve
            hr = hr_subgroup[g]
            S_trt = np.zeros_like(t_grid)
            for i, t in enumerate(t_grid):
                if t <= nph_crossover_time:
                    S_trt[i] = np.exp(-lam_c * hr * t)
                else:
                    S_at_cross = np.exp(-lam_c * hr * nph_crossover_time)
                    S_trt[i] = S_at_cross * np.exp(-lam_c * (1.0/hr) * (t - nph_crossover_time))
        else:
            S_trt = np.exp(-lam_ctrl[g] * hr_subgroup[g] * t_grid)

        S_ctrl = np.exp(-lam_ctrl[g] * t_grid)

        rmst_trt = rmst(t_grid, S_trt, 24.0)
        rmst_ctrl = rmst(t_grid, S_ctrl, 24.0)

        truth[f"subgroup_{g}"] = {
            "dRMST24": rmst_trt - rmst_ctrl,
            "RMST24_trt": rmst_trt,
            "RMST24_ctrl": rmst_ctrl,
            "S24_trt": S_trt[np.argmin(np.abs(t_grid - 24.0))],
            "S24_ctrl": S_ctrl[np.argmin(np.abs(t_grid - 24.0))],
        }

    return km_df, forest_df, truth, ipd


def run_single_scenario(
    name, lam_ctrl, hr_subgroup, weights, n_per_arm=300,
    censor_rate=0.15, nph_crossover_time=None, seed=42,
    tolerance_pct=0.30,
):
    """Run one validation scenario and return coverage/calibration metrics."""
    km_df, forest_df, truth, ipd = generate_synthetic_trial(
        lam_ctrl=lam_ctrl,
        hr_subgroup=hr_subgroup,
        weights=weights,
        n_per_arm=n_per_arm,
        censor_rate=censor_rate,
        seed=seed,
        nph_crossover_time=nph_crossover_time,
    )

    # Run feasible-set reconstruction
    solutions, summary = run_feasible_set(
        km_df=km_df,
        forest_df=forest_df,
        factor_name="test_factor",
        sublabels=["subgroup_0", "subgroup_1"],
        arm_names=("treatment", "control"),
        tolerance_pct=tolerance_pct,
    )

    results = []
    for g in range(2):
        sub_name = f"subgroup_{g}"
        true_drmst = truth[sub_name]["dRMST24"]

        if summary.empty or sub_name not in summary["subgroup"].values:
            results.append({
                "scenario": name,
                "subgroup": sub_name,
                "true_dRMST24": true_drmst,
                "env_min": np.nan,
                "env_max": np.nan,
                "env_med": np.nan,
                "env_width": np.nan,
                "covered": False,
                "n_solutions": 0,
            })
            continue

        row = summary[summary["subgroup"] == sub_name].iloc[0]
        env_min = row["dRMST24_min"]
        env_max = row["dRMST24_max"]
        env_med = row["dRMST24_med"]
        covered = env_min <= true_drmst <= env_max

        results.append({
            "scenario": name,
            "subgroup": sub_name,
            "true_dRMST24": round(true_drmst, 4),
            "env_min": round(env_min, 4),
            "env_max": round(env_max, 4),
            "env_med": round(env_med, 4),
            "env_width": round(env_max - env_min, 4),
            "bias": round(env_med - true_drmst, 4),
            "covered": covered,
            "n_solutions": int(row["n_solutions"]),
        })

    return results


def main():
    print("=" * 70)
    print("SIMULATION VALIDATION STUDY")
    print("=" * 70)

    all_results = []

    # Run each scenario with multiple seeds for stability
    scenarios = [
        {
            "name": "A_well_separated",
            "lam_ctrl": np.array([0.02, 0.10]),
            "hr_subgroup": np.array([0.4, 0.7]),
            "weights": np.array([0.6, 0.4]),
            "n_per_arm": 300,
            "description": "Well-separated subgroups, strong HR differential",
        },
        {
            "name": "B_moderate_indigo_like",
            "lam_ctrl": np.array([0.03, 0.06]),
            "hr_subgroup": np.array([0.35, 0.50]),
            "weights": np.array([0.52, 0.48]),
            "n_per_arm": 165,
            "description": "INDIGO-like: moderate separation, balanced prevalence",
        },
        {
            "name": "C_near_null",
            "lam_ctrl": np.array([0.045, 0.055]),
            "hr_subgroup": np.array([0.50, 0.50]),
            "weights": np.array([0.50, 0.50]),
            "n_per_arm": 300,
            "description": "Near-null: identical HRs, similar baselines",
        },
        {
            "name": "D_non_proportional_hazards",
            "lam_ctrl": np.array([0.03, 0.08]),
            "hr_subgroup": np.array([0.4, 0.6]),
            "weights": np.array([0.55, 0.45]),
            "n_per_arm": 300,
            "nph_crossover_time": 12.0,
            "description": "Non-PH: HR crosses over at 12 months (model misspecification)",
        },
        {
            "name": "E_small_sample",
            "lam_ctrl": np.array([0.03, 0.07]),
            "hr_subgroup": np.array([0.4, 0.6]),
            "weights": np.array([0.55, 0.45]),
            "n_per_arm": 80,
            "censor_rate": 0.20,
            "description": "Small sample (N=80/arm) with heavy censoring",
        },
    ]

    n_replicates = 50

    for sc in scenarios:
        print(f"\nScenario {sc['name']}: {sc['description']}")
        scenario_results = []

        for rep in range(n_replicates):
            try:
                results = run_single_scenario(
                    name=sc["name"],
                    lam_ctrl=sc["lam_ctrl"],
                    hr_subgroup=sc["hr_subgroup"],
                    weights=sc["weights"],
                    n_per_arm=sc.get("n_per_arm", 300),
                    censor_rate=sc.get("censor_rate", 0.15),
                    nph_crossover_time=sc.get("nph_crossover_time", None),
                    seed=42 + rep * 137,  # coprime stride avoids seed collisions
                )
                for r in results:
                    r["replicate"] = rep
                scenario_results.extend(results)
            except Exception as e:
                print(f"  Replicate {rep} failed: {e}")

        if scenario_results:
            df = pd.DataFrame(scenario_results)
            coverage = df["covered"].mean()
            mean_width = df["env_width"].mean()
            mean_bias = df["bias"].abs().mean() if "bias" in df.columns else np.nan
            print(f"  Coverage: {coverage:.0%} ({df['covered'].sum()}/{len(df)})")
            print(f"  Mean envelope width: {mean_width:.3f} months")
            print(f"  Mean |bias|: {mean_bias:.3f} months")
            all_results.extend(scenario_results)

    # Save results
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(out_dir, 'validation_simulation_results.csv'), index=False)

    # Summary table
    summary = (
        results_df.groupby("scenario")
        .agg(
            n_tests=("covered", "count"),
            coverage=("covered", "mean"),
            mean_width=("env_width", "mean"),
            mean_abs_bias=("bias", lambda x: x.abs().mean()),
            median_abs_bias=("bias", lambda x: x.abs().median()),
        )
        .reset_index()
    )
    summary.to_csv(os.path.join(out_dir, 'validation_summary.csv'), index=False)

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(summary.to_string(index=False))
    print(f"\nResults saved to {out_dir}/validation_simulation_results.csv")
    print(f"Summary saved to {out_dir}/validation_summary.csv")

    return results_df, summary


if __name__ == "__main__":
    results_df, summary = main()
