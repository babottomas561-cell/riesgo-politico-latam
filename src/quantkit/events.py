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


def fit_factor_model(y: pd.Series, X: pd.DataFrame) -> FactorFit:
    """OLS of y on X with intercept; rows with any NaN are dropped."""
    df = pd.concat([y.rename("_y"), X], axis=1).dropna()
    A = np.column_stack([np.ones(len(df)), df[X.columns].to_numpy()])
    coef, *_ = np.linalg.lstsq(A, df["_y"].to_numpy(), rcond=None)
    resid = df["_y"].to_numpy() - A @ coef
    dof = len(df) - A.shape[1]
    ss_tot = ((df["_y"] - df["_y"].mean()) ** 2).sum()
    return FactorFit(alpha=coef[0], betas=pd.Series(coef[1:], index=X.columns),
                     resid_std=float(np.sqrt(resid @ resid / dof)),
                     r2=float(1 - resid @ resid / ss_tot), n=len(df))


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
    with a t-statistic from the estimation-window residual volatility (Brown & Warner, 1985)."""
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
    return {"raw": float(y.loc[days].sum()), "expected": float(expected.sum()), "car": car,
            "t": t, "p": float(2 * stats.norm.sf(abs(t))), "days": n}


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


def rolling_beta(y: pd.Series, x: pd.Series, controls: pd.DataFrame | None, window: int = 120) -> pd.Series:
    """Rolling beta of y on x, holding ``controls`` fixed in the same regression."""
    X = x.to_frame("x") if controls is None else pd.concat([x.rename("x"), controls], axis=1)
    df = pd.concat([y.rename("_y"), X], axis=1).dropna()
    out = {}
    for end in range(window, len(df) + 1):
        w = df.iloc[end - window:end]
        out[w.index[-1]] = fit_factor_model(w["_y"], w[X.columns]).betas["x"]
    return pd.Series(out)
