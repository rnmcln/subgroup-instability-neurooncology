"""
Identifiability-aware subgroup survival reconstruction.

Core framework:
- Piecewise-exponential baseline hazards per subgroup level
- Treatment effect via proportional (or time-varying) HR within subgroup
- Arm-level mixture constraint: observed S(t) = sum_k w_k S_k(t)
- Feasible-set characterization over knot placements and penalty strengths

Output quantities are model-implied within a feasible set, NOT point-identified.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from dataclasses import dataclass, field

from .utils import interp_survival, common_time_grid, rmst, surv_at, perturb_km


# ---------------------------------------------------------------------------
# Piecewise-exponential model for a two-level factor partition
# ---------------------------------------------------------------------------

def _build_exposure_matrix(t_grid: np.ndarray, breaks: np.ndarray) -> np.ndarray:
    """Build exposure matrix A[i,j] = time in interval j up to t_grid[i]."""
    J = len(breaks) - 1
    A = np.zeros((len(t_grid), J))
    for i, t in enumerate(t_grid):
        for j in range(J):
            A[i, j] = max(0.0, min(t, breaks[j+1]) - breaks[j])
    return A


def fit_piecewise_factor(
    km_df: pd.DataFrame,
    factor_df: pd.DataFrame,
    breaks: tuple,
    arm_names: tuple[str, str] = ("treatment", "control"),
    penalty_smooth: float = 1e-3,
    penalty_reg: float = 1e-4,
    maxiter: int = 280,
    allow_timevarying_hr: bool = False,
    penalty_hrtv: float = 5e-2,
) -> tuple:
    """
    Fit piecewise-exponential subgroup hazards for a single two-level factor.

    Parameters
    ----------
    km_df : DataFrame with columns [arm, month, survival]
    factor_df : DataFrame with exactly 2 rows, columns [subgroup, n, hr]
    breaks : tuple of knot times
    arm_names : (treatment_arm, control_arm)
    penalty_smooth : smoothness penalty on log-hazard differences across intervals
    penalty_reg : L2 regularization on log-hazards
    allow_timevarying_hr : if True, allow piecewise-constant HR(t)
    penalty_hrtv : penalty anchoring time-varying HR to reported Cox HR

    Returns
    -------
    res : scipy OptimizeResult
    t_grid : time grid
    A : exposure matrix
    """
    factor_df = factor_df.reset_index(drop=True)
    K = 2  # two-level partition
    assert len(factor_df) == K

    t_grid = common_time_grid(km_df, max(breaks))
    S_ctrl = interp_survival(km_df, arm_names[1], t_grid)
    S_trt = interp_survival(km_df, arm_names[0], t_grid)

    w = (factor_df["n"] / factor_df["n"].sum()).values
    hr0 = factor_df["hr"].values
    breaks_arr = np.array(breaks, float)
    J = len(breaks_arr) - 1
    A = _build_exposure_matrix(t_grid, breaks_arr)

    if allow_timevarying_hr:
        # Parameters: K*J log-hazards for control + K*J log-HR values
        x0 = np.concatenate([np.full(K*J, -3.5), np.log(np.repeat(hr0, J))])

        def obj(x):
            xl = x[:K*J].reshape(K, J)
            xh = x[K*J:].reshape(K, J)
            lam_c = np.exp(xl)
            hr = np.exp(xh)
            lam_t = hr * lam_c
            Hc = A.dot(lam_c.T)
            Ht = A.dot(lam_t.T)
            Sc = np.exp(-Hc)
            St = np.exp(-Ht)
            Smc = (Sc * w[None, :]).sum(1)
            Smt = (St * w[None, :]).sum(1)
            loss = ((Smc - S_ctrl)**2).mean() + ((Smt - S_trt)**2).mean()
            loss += penalty_smooth * np.square(np.diff(xl, axis=1)).mean()
            loss += penalty_reg * np.square(xl).mean()
            target = np.log(hr0)[:, None]
            loss += penalty_hrtv * np.square(xh - target).mean()
            loss += penalty_smooth * np.square(np.diff(xh, axis=1)).mean()
            return float(loss)

        res = minimize(obj, x0, method="L-BFGS-B", options={"maxiter": maxiter})
    else:
        x0 = np.full(K*J, -3.5)

        def obj(x):
            xl = x.reshape(K, J)
            lam_c = np.exp(xl)
            lam_t = hr0[:, None] * lam_c
            Hc = A.dot(lam_c.T)
            Ht = A.dot(lam_t.T)
            Sc = np.exp(-Hc)
            St = np.exp(-Ht)
            Smc = (Sc * w[None, :]).sum(1)
            Smt = (St * w[None, :]).sum(1)
            loss = ((Smc - S_ctrl)**2).mean() + ((Smt - S_trt)**2).mean()
            loss += penalty_smooth * np.square(np.diff(xl, axis=1)).mean()
            loss += penalty_reg * np.square(x).mean()
            return float(loss)

        res = minimize(obj, x0, method="L-BFGS-B", options={"maxiter": maxiter})

    return res, t_grid, A


def extract_subgroup_curves(
    res, t_grid, A, factor_df, breaks, allow_timevarying_hr=False
):
    """Extract fitted subgroup-level survival curves from optimization result."""
    factor_df = factor_df.reset_index(drop=True)
    K = 2
    J = len(np.array(breaks, float)) - 1
    hr0 = factor_df["hr"].values
    w = (factor_df["n"] / factor_df["n"].sum()).values

    if allow_timevarying_hr:
        xl = res.x[:K*J].reshape(K, J)
        xh = res.x[K*J:].reshape(K, J)
        lam_c = np.exp(xl)
        hr = np.exp(xh)
        lam_t = hr * lam_c
    else:
        xl = res.x.reshape(K, J)
        lam_c = np.exp(xl)
        lam_t = hr0[:, None] * lam_c

    curves = {}
    for k in range(K):
        Sc = np.exp(-A.dot(lam_c[k]))
        St = np.exp(-A.dot(lam_t[k]))
        curves[factor_df["subgroup"].iloc[k]] = {"t": t_grid, "S_ctrl": Sc, "S_trt": St}

    # Mixture curves
    Sc_all = np.column_stack([np.exp(-A.dot(lam_c[k])) for k in range(K)])
    St_all = np.column_stack([np.exp(-A.dot(lam_t[k])) for k in range(K)])
    Smc = (Sc_all * w[None, :]).sum(1)
    Smt = (St_all * w[None, :]).sum(1)

    return curves, Smc, Smt


def factor_metrics(
    res, t_grid, A, factor_df, breaks,
    allow_timevarying_hr=False, tau_rmst=24.0,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Compute subgroup-level metrics (S24, RMST24, absolute effects)."""
    curves, Smc, Smt = extract_subgroup_curves(
        res, t_grid, A, factor_df, breaks, allow_timevarying_hr
    )

    rows = []
    for sub_name, sub_curves in curves.items():
        row = factor_df[factor_df["subgroup"] == sub_name].iloc[0]
        Sc = sub_curves["S_ctrl"]
        St = sub_curves["S_trt"]
        rows.append({
            "subgroup": sub_name,
            "n": int(row["n"]),
            "hr_reported": float(row["hr"]),
            "S24_ctrl": surv_at(t_grid, Sc, tau_rmst),
            "S24_trt": surv_at(t_grid, St, tau_rmst),
            "RMST24_ctrl": rmst(t_grid, Sc, tau_rmst),
            "RMST24_trt": rmst(t_grid, St, tau_rmst),
        })
    df = pd.DataFrame(rows)
    df["dS24"] = df["S24_trt"] - df["S24_ctrl"]
    df["dRMST24"] = df["RMST24_trt"] - df["RMST24_ctrl"]
    return df, Smc, Smt


def fit_metrics(t_grid, Smc, Smt, km_df, arm_names=("treatment", "control")):
    """Compute fit quality metrics (ISE, MAD) for each arm."""
    S_ctrl = interp_survival(km_df, arm_names[1], t_grid)
    S_trt = interp_survival(km_df, arm_names[0], t_grid)
    return {
        "ISE_ctrl": float(np.mean((Smc - S_ctrl)**2)),
        "ISE_trt": float(np.mean((Smt - S_trt)**2)),
        "MAD_ctrl": float(np.max(np.abs(Smc - S_ctrl))),
        "MAD_trt": float(np.max(np.abs(Smt - S_trt))),
    }


# ---------------------------------------------------------------------------
# Weibull shared-shape model
# ---------------------------------------------------------------------------

def fit_weibull_shared(km_df, factor_df, arm_names=("treatment", "control"),
                       tau=30.0, reg=1e-4, maxiter=600):
    """Weibull shared-shape baseline with subgroup-specific scaling."""
    factor_df = factor_df.reset_index(drop=True)
    t = common_time_grid(km_df, tau)
    S_c = interp_survival(km_df, arm_names[1], t)
    S_t = interp_survival(km_df, arm_names[0], t)
    w = (factor_df["n"] / factor_df["n"].sum()).values
    hr = factor_df["hr"].values
    K = len(factor_df)

    def obj(x):
        shape = np.exp(x[0])
        alpha = x[1:]
        H0 = np.clip(t, 1e-6, None) ** shape
        Hc = np.exp(alpha)[None, :] * H0[:, None]
        Ht = (hr[None, :] * np.exp(alpha)[None, :]) * H0[:, None]
        Sc = np.exp(-Hc)
        St = np.exp(-Ht)
        Smc = (Sc * w[None, :]).sum(1)
        Smt = (St * w[None, :]).sum(1)
        loss = ((Smc - S_c)**2).mean() + ((Smt - S_t)**2).mean()
        loss += reg * (x**2).mean()
        return float(loss)

    x0 = np.concatenate([[np.log(1.2)], np.full(K, -4.0)])
    return minimize(obj, x0, method="L-BFGS-B", options={"maxiter": maxiter}), t


# ---------------------------------------------------------------------------
# Royston-Parmar restricted cubic spline model
# ---------------------------------------------------------------------------

def _rcs_basis(z, knots):
    """Restricted cubic spline basis on log-time scale."""
    z = np.asarray(z)
    k = np.asarray(knots)
    K = len(k)
    def d(u, kk):
        return np.maximum(u - kk, 0.0) ** 3
    denom = (k[-1] - k[-2]) if k[-1] != k[-2] else 1.0
    B = [z]
    for j in range(1, K-1):
        bj = (d(z, k[j]) - d(z, k[-2])*(k[-1]-k[j])/denom + d(z, k[-1])*(k[-2]-k[j])/denom)
        B.append(bj)
    return np.column_stack(B)


def fit_rp_shared(km_df, factor_df, arm_names=("treatment", "control"),
                  tau=30.0, reg=1e-4, maxiter=800):
    """Flexible parametric Royston-Parmar-style shared baseline."""
    factor_df = factor_df.reset_index(drop=True)
    t = common_time_grid(km_df, tau)
    S_c = interp_survival(km_df, arm_names[1], t)
    S_t = interp_survival(km_df, arm_names[0], t)
    w = (factor_df["n"] / factor_df["n"].sum()).values
    hr = factor_df["hr"].values
    K = len(factor_df)

    tt = np.clip(t, 1e-4, None)
    z = np.log(tt)
    knots = np.array([np.log(0.5), np.log(3), np.log(12), np.log(tau)])
    X = _rcs_basis(z, knots)
    p = X.shape[1]

    def obj(x):
        eta0 = x[0]
        b = x[1:1+p]
        alpha = x[1+p:]
        H0 = np.exp(eta0 + X.dot(b))
        Hc = np.exp(alpha)[None, :] * H0[:, None]
        Ht = (hr[None, :] * np.exp(alpha)[None, :]) * H0[:, None]
        Sc = np.exp(-Hc)
        St = np.exp(-Ht)
        Smc = (Sc * w[None, :]).sum(1)
        Smt = (St * w[None, :]).sum(1)
        loss = ((Smc - S_c)**2).mean() + ((Smt - S_t)**2).mean()
        loss += reg * (x**2).mean()
        return float(loss)

    x0 = np.concatenate([[np.log(0.05)], np.zeros(p), np.full(K, -4.0)])
    return minimize(obj, x0, method="L-BFGS-B", options={"maxiter": maxiter}), t, knots


# ---------------------------------------------------------------------------
# Feasible-set search
# ---------------------------------------------------------------------------

def run_feasible_set(
    km_df: pd.DataFrame,
    forest_df: pd.DataFrame,
    factor_name: str,
    sublabels: list[str],
    arm_names: tuple[str, str] = ("treatment", "control"),
    allow_timevarying_hr: bool = False,
    tolerance_pct: float = 0.30,
    tau_rmst: float = 24.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run feasible-set search over knot placements and penalty strengths.

    Returns
    -------
    solutions : DataFrame of all accepted solutions
    summary : DataFrame with envelope min/median/max per subgroup
    """
    factor_df = forest_df[
        (forest_df["group"] == factor_name) & (forest_df["subgroup"].isin(sublabels))
    ].copy()
    factor_df = factor_df.set_index("subgroup").loc[sublabels].reset_index()

    if len(factor_df) != 2 or factor_df["hr"].isna().any():
        return pd.DataFrame(), pd.DataFrame()

    knot_sets = [
        (0, 12, 24, 30), (0, 6, 12, 18, 24, 30), (0, 9, 18, 30),
        (0, 8, 16, 24, 30), (0, 10, 20, 30),
    ]
    smooth_list = [5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2]
    reg_list = [1e-5, 5e-5, 1e-4, 5e-4]

    # Baseline fit
    res0, t0, A0 = fit_piecewise_factor(
        km_df, factor_df, breaks=(0, 12, 24, 30),
        arm_names=arm_names,
        penalty_smooth=1e-3, penalty_reg=1e-4,
        allow_timevarying_hr=allow_timevarying_hr, maxiter=300,
    )
    m0, Smc0, Smt0 = factor_metrics(
        res0, t0, A0, factor_df, (0, 12, 24, 30),
        allow_timevarying_hr, tau_rmst,
    )
    fm0 = fit_metrics(t0, Smc0, Smt0, km_df, arm_names)
    eps = (fm0["ISE_ctrl"] + fm0["ISE_trt"]) * (1.0 + tolerance_pct)

    sols = []
    for breaks in knot_sets:
        for ps in smooth_list:
            for pr in reg_list:
                try:
                    res, tg, A = fit_piecewise_factor(
                        km_df, factor_df, breaks=breaks,
                        arm_names=arm_names,
                        penalty_smooth=ps, penalty_reg=pr,
                        allow_timevarying_hr=allow_timevarying_hr,
                        maxiter=300,
                    )
                except Exception:
                    continue
                if not res.success:
                    continue
                m, Smc, Smt = factor_metrics(
                    res, tg, A, factor_df, breaks, allow_timevarying_hr, tau_rmst,
                )
                fm = fit_metrics(tg, Smc, Smt, km_df, arm_names)
                ise = fm["ISE_ctrl"] + fm["ISE_trt"]
                if ise <= eps:
                    for _, row in m.iterrows():
                        sols.append({
                            "factor": factor_name,
                            "subgroup": row["subgroup"],
                            "breaks": ",".join(map(str, breaks)),
                            "pen_smooth": ps, "pen_reg": pr,
                            "timevarying_hr": allow_timevarying_hr,
                            **fm, "ISE_sum": ise,
                            "S24_ctrl": row["S24_ctrl"],
                            "S24_trt": row["S24_trt"],
                            "RMST24_ctrl": row["RMST24_ctrl"],
                            "RMST24_trt": row["RMST24_trt"],
                            "dS24": row["dS24"],
                            "dRMST24": row["dRMST24"],
                        })

    solutions = pd.DataFrame(sols)

    if solutions.empty:
        return solutions, pd.DataFrame()

    summary = (
        solutions.groupby(["factor", "subgroup"])
        .agg(
            n_solutions=("dRMST24", "count"),
            dRMST24_min=("dRMST24", "min"),
            dRMST24_max=("dRMST24", "max"),
            dRMST24_med=("dRMST24", "median"),
            dS24_min=("dS24", "min"),
            dS24_max=("dS24", "max"),
            dS24_med=("dS24", "median"),
            S24_ctrl_med=("S24_ctrl", "median"),
            S24_trt_med=("S24_trt", "median"),
            RMST24_ctrl_med=("RMST24_ctrl", "median"),
            RMST24_trt_med=("RMST24_trt", "median"),
            ISE_sum_med=("ISE_sum", "median"),
        )
        .reset_index()
    )
    return solutions, summary


# ---------------------------------------------------------------------------
# HR uncertainty propagation
# ---------------------------------------------------------------------------

def bootstrap_hr_uncertainty(
    km_df: pd.DataFrame,
    factor_df: pd.DataFrame,
    arm_names: tuple[str, str] = ("treatment", "control"),
    n_boot: int = 50,
    km_sd: float = 0.012,
    seed: int = 42,
    tau_rmst: float = 24.0,
) -> pd.DataFrame:
    """
    Propagate HR uncertainty and digitization noise through reconstruction.
    """
    rng = np.random.default_rng(seed)
    factor_df = factor_df.reset_index(drop=True)
    loghr = np.log(factor_df["hr"].values)
    se = (np.log(factor_df["ci_high"].values) - np.log(factor_df["ci_low"].values)) / (2 * 1.96)

    boot_results = []
    for b in range(n_boot):
        hr_b = np.exp(rng.normal(loghr, se))
        km_b = perturb_km(km_df, sd=km_sd, seed=5000 + b)
        factor_b = factor_df.copy()
        factor_b["hr"] = hr_b

        try:
            res, tg, A = fit_piecewise_factor(
                km_b, factor_b, breaks=(0, 12, 24, 30),
                arm_names=arm_names,
                penalty_smooth=1e-3, penalty_reg=1e-4,
                maxiter=200,
            )
            if not res.success:
                continue
            m, _, _ = factor_metrics(res, tg, A, factor_b, (0, 12, 24, 30), tau_rmst=tau_rmst)
            m["boot"] = b
            boot_results.append(m)
        except Exception:
            continue

    if not boot_results:
        return pd.DataFrame()

    boot = pd.concat(boot_results, ignore_index=True)
    return boot


# ---------------------------------------------------------------------------
# Synthetic identifiability demonstration
# ---------------------------------------------------------------------------

def synthetic_identifiability_demo() -> dict:
    """
    Construct a synthetic example where distinct subgroup baselines yield
    identical mixture survival, demonstrating non-identifiability.

    Two subgroups with weights w1=0.5, w2=0.5.
    Show that different (lam1, lam2) pairs can produce the same S_mix(t).
    """
    t = np.linspace(0, 24, 200)
    w = np.array([0.5, 0.5])

    # Configuration A
    lam_A = np.array([0.02, 0.08])
    S_A = np.column_stack([np.exp(-lam_A[k] * t) for k in range(2)])
    S_mix_A = (S_A * w[None, :]).sum(1)

    # Configuration B: different subgroup hazards, same mixture
    # We cannot get an exact match with exponential, but near-exact
    # Use optimization to find alternative
    from scipy.optimize import minimize

    def obj(x):
        l1, l2 = np.exp(x)
        S1 = np.exp(-l1 * t)
        S2 = np.exp(-l2 * t)
        S_mix = 0.5 * S1 + 0.5 * S2
        return float(np.mean((S_mix - S_mix_A)**2))

    # Start from a different initial point
    res = minimize(obj, [np.log(0.04), np.log(0.06)], method="L-BFGS-B")
    lam_B = np.exp(res.x)

    # Configuration C: with a treatment HR=0.5 applied uniformly
    hr = 0.5
    # Under A
    S_trt_A = np.column_stack([np.exp(-hr * lam_A[k] * t) for k in range(2)])
    S_mix_trt_A = (S_trt_A * w[None, :]).sum(1)

    # Under B
    S_trt_B = np.column_stack([np.exp(-hr * lam_B[k] * t) for k in range(2)])
    S_mix_trt_B = (S_trt_B * w[None, :]).sum(1)

    # Absolute effects differ
    dRMST_A = [rmst(t, S_trt_A[:, k], 24) - rmst(t, S_A[:, k], 24) for k in range(2)]
    dRMST_B = [rmst(t, S_trt_B[:, k], 24) - rmst(t, S_A[:, k], 24) for k in range(2)]

    return {
        "t": t,
        "w": w,
        "lam_A": lam_A, "lam_B": lam_B,
        "S_mix_ctrl": S_mix_A,
        "S_mix_trt_A": S_mix_trt_A,
        "S_mix_trt_B": S_mix_trt_B,
        "mixture_max_abs_diff": float(np.max(np.abs(S_mix_A - (0.5*np.exp(-lam_B[0]*t) + 0.5*np.exp(-lam_B[1]*t))))),
        "S_sub_ctrl_A": S_A,
        "S_sub_ctrl_B": np.column_stack([np.exp(-lam_B[k] * t) for k in range(2)]),
        "S_sub_trt_A": S_trt_A,
        "S_sub_trt_B": S_trt_B,
        "dRMST24_A": dRMST_A,
        "dRMST24_B": dRMST_B,
        "hr": hr,
    }
