"""The event-study tools recover effects planted in synthetic data."""

import numpy as np
import pandas as pd
import pytest

from quantkit import events

RNG = np.random.default_rng(1)
IDX = pd.bdate_range("2020-01-01", periods=600)


def synthetic(beta=(1.2, -0.5), sigma=0.01):
    X = pd.DataFrame(RNG.standard_normal((len(IDX), 2)) * 0.01, index=IDX, columns=["mkt", "oil"])
    y = 0.0002 + X @ np.array(beta) + RNG.standard_normal(len(IDX)) * sigma
    return y, X


def test_factor_model_recovers_betas():
    y, X = synthetic()
    fit = events.fit_factor_model(y, X)
    assert fit.betas["mkt"] == pytest.approx(1.2, abs=0.08)
    assert fit.betas["oil"] == pytest.approx(-0.5, abs=0.08)


def test_estimation_window_ends_before_event_with_gap():
    win = events.estimation_window(IDX, IDX[400], length=250, gap=10)
    assert len(win) == 250 and win[-1] == IDX[389]


def test_planted_shock_is_detected_and_market_move_is_not():
    y, X = synthetic()
    day0 = IDX[500]
    X.loc[day0, "mkt"] = -0.10           # a big market day fully explained by beta
    y.loc[day0] = 1.2 * -0.10
    res = events.event_car(y, X, day0, window=(0, 0))
    assert abs(res["t"]) < 3             # no abnormal return: the factor explains it
    y.loc[day0] -= 0.08                  # now plant an 8% idiosyncratic shock
    res = events.event_car(y, X, day0, window=(0, 0))
    assert res["car"] == pytest.approx(-0.08, abs=0.03)
    assert res["t"] < -4


def test_attribution_adds_up_to_total():
    y, X = synthetic()
    fit = events.fit_factor_model(y.iloc[:400], X.iloc[:400])
    parts = events.attribute(y, X, fit, IDX[400:420])
    assert parts.drop("total").sum() == pytest.approx(parts["total"])


def test_rolling_beta_tracks_a_regime_change():
    x = pd.Series(RNG.standard_normal(len(IDX)) * 0.01, index=IDX)
    b = np.where(np.arange(len(IDX)) < 300, 0.2, 1.0)
    y = b * x + RNG.standard_normal(len(IDX)) * 0.005
    rb = events.rolling_beta(y, x, None, window=120)
    assert rb.iloc[0] == pytest.approx(0.2, abs=0.15)
    assert rb.iloc[-1] == pytest.approx(1.0, abs=0.15)
