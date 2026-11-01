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


def test_empirical_p_is_small_for_planted_shock_and_large_for_none():
    y, X = synthetic()
    day0 = IDX[500]
    assert events.event_car(y, X, day0, window=(0, 1))["p_emp"] > 0.01
    y.loc[day0] -= 0.10
    assert events.event_car(y, X, day0, window=(0, 1))["p_emp"] < 0.01


def test_beta_covariance_matches_monte_carlo_spread():
    # The analytical sd of the betas should match their spread across fresh samples.
    draws = [events.fit_factor_model(*synthetic()).betas["mkt"] for _ in range(300)]
    sd_analytic = np.sqrt(events.fit_factor_model(*synthetic()).cov[0, 0])
    assert np.std(draws) == pytest.approx(sd_analytic, rel=0.2)


def test_attribution_path_ends_at_attribution():
    y, X = synthetic()
    fit = events.fit_factor_model(y.iloc[:400], X.iloc[:400])
    path = events.attribute_path(y, X, fit, IDX[400:450])
    parts = events.attribute(y, X, fit, IDX[400:450])
    assert path.iloc[-1].to_dict() == pytest.approx(parts.drop("total").to_dict())


def _two_stage_world(rng):
    G = pd.DataFrame(rng.standard_normal((len(IDX), 2)) * 0.01, index=IDX, columns=["mkt", "oil"])
    reg = pd.Series(rng.standard_normal(len(IDX)) * 0.01, index=IDX)        # Brazil's own shock
    z = G @ np.array([1.0, 0.3]) + reg
    y = G @ np.array([1.2, 0.0]) + 0.6 * reg + rng.standard_normal(len(IDX)) * 0.01
    period = IDX[450:530]
    y.loc[period] -= 0.10 / len(period)                                     # plant -10 points of own drift
    truth = float((y - G @ np.array([1.2, 0.0]) - 0.6 * reg).loc[period].sum())
    return y, z, G, period, truth


def test_two_stage_bootstrap_band_covers_the_true_own_component():
    # A 95% band should cover the truth in most worlds (not every one: that is what 95% means).
    rng = np.random.default_rng(7)
    hits = 0
    for _ in range(20):
        y, z, G, period, truth = _two_stage_world(rng)
        lo, hi = events.two_stage_bootstrap(y, z, G, IDX[100:400], period, n_boot=200,
                                            seed=int(rng.integers(1e6)))["propio"].quantile([0.025, 0.975])
        hits += lo < truth < hi
    assert hits >= 16


def test_two_stage_band_is_wider_than_treating_the_factor_as_data():
    y, z, G, period, _ = _two_stage_world(np.random.default_rng(8))
    est = IDX[100:400]
    f1 = events.fit_factor_model(z.loc[est], G.loc[est])
    X = pd.concat([G, (z - f1.alpha - G @ f1.betas).rename("reg")], axis=1)
    one_stage = events.attribution_band(X, events.fit_factor_model(y.loc[est], X.loc[est]), period)
    boot = events.two_stage_bootstrap(y, z, G, est, period, n_boot=400)
    assert boot["propio"].std() > one_stage["sd_betas"]
