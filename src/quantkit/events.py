"""Event study and return attribution.

Convention: an event's day 0 is the first trading day on which the market could react
(a Sunday election has day 0 on Monday). Abnormal return = actual return minus what a
factor model, estimated on data that ends before the event, predicted for that day.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class FactorFit:
    alpha: float
    betas: pd.Series
    resid_std: float
    r2: float
    n: int
    cov: np.ndarray | None = None   # covariance of the betas (intercept excluded)


def fit_factor_model(y: pd.Series, X: pd.DataFrame) -> FactorFit:
    """OLS of y on X with intercept; rows with any NaN are dropped."""
    df = pd.concat([y.rename("_y"), X], axis=1).dropna()
    A = np.column_stack([np.ones(len(df)), df[X.columns].to_numpy()])
    coef, *_ = np.linalg.lstsq(A, df["_y"].to_numpy(), rcond=None)
    resid = df["_y"].to_numpy() - A @ coef
    dof = len(df) - A.shape[1]
    ss_tot = ((df["_y"] - df["_y"].mean()) ** 2).sum()
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.inv(A.T @ A)[1:, 1:]
    return FactorFit(alpha=coef[0], betas=pd.Series(coef[1:], index=X.columns),
                     resid_std=float(np.sqrt(s2)), r2=float(1 - resid @ resid / ss_tot), n=len(df), cov=cov)


def estimation_window(index: pd.DatetimeIndex, day0: pd.Timestamp, length: int = 250, gap: int = 10) -> pd.DatetimeIndex:
    """The ``length`` trading days that end ``gap`` days before day 0, so that pre-event
    leakage (polls, rumors) does not contaminate the 'normal' model."""
    pos = index.get_indexer([day0])[0]
    if pos < 0:
        raise KeyError(f"{day0.date()} is not a trading day in the index")
    start, end = pos - gap - length, pos - gap
    if start < 0:
        raise ValueError(f"not enough history before {day0.date()}")
    return index[start:end]


def event_car(y: pd.Series, X: pd.DataFrame, day0: str | pd.Timestamp, window: tuple[int, int] = (0, 1),
              est_length: int = 250, gap: int = 10) -> dict[str, float]:
    """Cumulative abnormal return over trading days [window[0], window[1]] around day 0,
    with a t-statistic from the estimation-window residual volatility (Brown & Warner, 1985).

    ``p_emp`` drops the normality assumption: the share of all same-length windows inside
    the estimation sample whose summed residual is at least as large in absolute value.
    Fat tails (common in Argentine ADRs) make it larger than the normal ``p``."""
    day0 = pd.Timestamp(day0)
    idx = y.dropna().index.intersection(X.dropna().index)
    est = estimation_window(idx, day0, est_length, gap)
    fit = fit_factor_model(y.loc[est], X.loc[est])
    pos = idx.get_indexer([day0])[0]
    days = idx[pos + window[0]: pos + window[1] + 1]
    expected = fit.alpha + X.loc[days] @ fit.betas
    ar = y.loc[days] - expected
    n = len(days)
    car = float(ar.sum())
    t = car / (fit.resid_std * np.sqrt(n))
    resid = y.loc[est] - fit.alpha - X.loc[est] @ fit.betas
    placebo = resid.rolling(n).sum().dropna()
    return {"raw": float(y.loc[days].sum()), "expected": float(expected.sum()), "car": car,
            "t": t, "p": float(2 * stats.norm.sf(abs(t))),
            "p_emp": float((placebo.abs() >= abs(car)).mean()), "days": n}


def attribute(y: pd.Series, X: pd.DataFrame, fit: FactorFit, period: pd.DatetimeIndex) -> pd.Series:
    """Split the cumulative (summed log) return of y over ``period`` into each factor's
    contribution (beta x factor return) and the unexplained remainder.

    The intercept is deliberately left in the remainder: it is the drift of the estimation
    sample, not something the factors explain. ``period`` should lie outside the sample
    the betas were estimated on, or the remainder is zero by construction."""
    contrib = X.loc[period].sum() * fit.betas
    total = float(y.loc[period].sum())
    out = contrib.copy()
    out["idiosincrático"] = total - contrib.sum()
    out["total"] = total
    return out


def attribution_band(X: pd.DataFrame, fit: FactorFit, period: pd.DatetimeIndex) -> dict[str, float]:
    """Two sources of uncertainty in the unexplained remainder of ``attribute``.

    ``sd_betas``: from estimating the betas. Since total is observed, the remainder moves
    one-for-one (with opposite sign) with the explained part, whose variance is
    s' Cov(beta) s for s = summed factor returns. It says how sure we are of the split.
    ``sd_noise``: how large a remainder ordinary residual noise produces over that many
    days (sigma * sqrt(n)). Remainder / sd_noise tests whether it is abnormal at all."""
    s = X.loc[period].sum().to_numpy()
    return {"sd_betas": float(np.sqrt(s @ fit.cov @ s)), "sd_noise": fit.resid_std * np.sqrt(len(period))}


def attribute_path(y: pd.Series, X: pd.DataFrame, fit: FactorFit, period: pd.DatetimeIndex) -> pd.DataFrame:
    """Cumulative version of ``attribute``, day by day: when each contribution built up."""
    contrib = X.loc[period] * fit.betas
    contrib["idiosincrático"] = y.loc[period] - contrib.sum(axis=1)
    return contrib.cumsum()


def rolling_beta(y: pd.Series, x: pd.Series, controls: pd.DataFrame | None, window: int = 120) -> pd.Series:
    """Rolling beta of y on x, holding ``controls`` fixed in the same regression."""
    X = x.to_frame("x") if controls is None else pd.concat([x.rename("x"), controls], axis=1)
    df = pd.concat([y.rename("_y"), X], axis=1).dropna()
    out = {}
    for end in range(window, len(df) + 1):
        w = df.iloc[end - window:end]
        out[w.index[-1]] = fit_factor_model(w["_y"], w[X.columns]).betas["x"]
    return pd.Series(out)
