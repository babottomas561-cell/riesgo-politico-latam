"""¿Argentina, Brasil o el mundo? Qué explica la caída de los activos argentinos en 2026.

Reproduce todas las figuras y tablas del informe (README.md en la raíz del repo):
    uv run python estudio/run.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))

from eventos import EVENTOS  # noqa: E402

from quantkit import events, style  # noqa: E402
from quantkit.data import load_data912, load_prices  # noqa: E402

HERE = Path(__file__).parent
FIG = HERE / "figures"

# Fijado antes de mirar la atribución (ver README, sección Método).
AR = ["GGAL", "BMA", "BBAR", "SUPV", "YPF", "PAM", "TGS", "CEPU", "EDN", "TEO", "CRESY", "LOMA", "IRS"]
BR_STOCKS = ["ITUB", "NU", "PBR"]
GLOBAL = ["SPY", "BZ=F", "^TNX"]
FACTOR_NAMES = {"SPY": "Acciones globales (S&P 500)", "BZ=F": "Petróleo (Brent)", "^TNX": "Tasa a 10 años EEUU",
                "Brasil": "Brasil (propio)", "idiosincrático": "Argentina (propio)"}
START, END = "2022-06-01", "2026-10-31"
MILEI = "2023-12-08"                         # último cierre antes de la asunción
CAIDA = ("2026-07-15", "2026-10-30")         # desde el mínimo del riesgo país hasta hoy
EST = ("2025-11-03", "2026-07-14")           # betas: desde las legislativas hasta antes de la caída
EST_ALT = [("2024-01-02", "2026-07-14"), ("2025-07-15", "2026-07-14"), ("2026-01-02", "2026-07-14")]
CAMPANA_BR = ("2026-08-16", "2026-10-25")    # campaña oficial en Brasil
WINDOW = (0, 1)                              # día 0 y día +1: el FX de Yahoo llega con un día de desfase
LULA = "2026-10-26"
PRIMERA_VUELTA_BR = "2026-10-05"
SECTORES = {"Bancos": ["GGAL", "BMA", "BBAR", "SUPV"], "Energía": ["YPF", "PAM", "CEPU", "TGS"],
            "Servicios": ["EDN", "TEO"], "Agro e inmuebles": ["CRESY", "IRS", "LOMA"]}
BONOS = ["GD30D", "GD35D", "GD41D"]          # Globales en dólares MEP: corto, medio, largo (data912/BYMA)
PARES = {"EWW": "México", "ECH": "Chile", "EPU": "Perú", "COLO": "Colombia", "EEM": "Emergentes"}
SHOCK_BR = 2.5                               # un "día grande" de Brasil: |shock propio| > 2,5 desvíos
C_AR, C_BR, C_US = style.BLUE, style.AQUA, style.ORANGE


# ============================================================================ datos

def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    tickers = AR + BR_STOCKS + ["MELI", "EWZ", "BRL=X"] + GLOBAL
    p = load_prices(tickers, start=START, end=END, how="all")
    # Ruedas de Wall Street (donde cotizan los ADRs); un activo sin precio ese día (feriado
    # propio) arrastra su último cierre, así el retorno del día siguiente no se pierde.
    p = p[p["SPY"].notna()].ffill()
    r = np.log(p).diff()
    r["^TNX"] = p["^TNX"].diff() / 100      # cambio de rendimiento, en decimales
    r["AR"] = r[AR].mean(axis=1)            # canasta equiponderada de ADRs argentinos
    return p, r.iloc[1:]


def load_extra(p: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    """Bonos soberanos y pares de LatAm, en el mismo calendario que ``load``.

    Se cargan aparte para no cambiar el panel congelado del estudio original. Los bonos
    pagan cupón y amortización el 9/1 y el 9/7: el precio cae en la fecha ex, sin que
    cambie el riesgo. Esas semanas se excluyen (ninguna cae en el período de la caída)."""
    peers = load_prices(list(PARES) + ["SPY"], start=START, end=END, how="all").drop(columns="SPY")
    ext = pd.concat([peers, load_data912(BONOS)], axis=1).reindex(p.index).ffill()
    rx = np.log(ext).diff().reindex(r.index)
    ex = rx.index.month.isin([1, 7]) & (rx.index.day >= 5) & (rx.index.day <= 12)
    rx.loc[ex, BONOS] = np.nan
    rx["Bonos"] = rx[BONOS].mean(axis=1, skipna=False)
    rx["LatAm sin Brasil"] = rx[["EWW", "ECH", "EPU", "COLO"]].mean(axis=1)
    return pd.concat([r, rx], axis=1)


def brazil_factor(r: pd.DataFrame, est: tuple[str, str]) -> pd.Series:
    """Retorno de EWZ que no explican los factores globales: el shock propio de Brasil."""
    idx = r.loc[est[0]:est[1]].index
    fit = events.fit_factor_model(r["EWZ"].loc[idx], r[GLOBAL].loc[idx])
    return (r["EWZ"] - fit.alpha - r[GLOBAL] @ fit.betas).rename("Brasil")


def factors(r: pd.DataFrame, est: tuple[str, str]) -> pd.DataFrame:
    return pd.concat([r[GLOBAL], brazil_factor(r, est)], axis=1)


# ============================================================================ análisis

def event_table(r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for e in EVENTOS:
        a = events.event_car(r["AR"], r[GLOBAL], e.dia0, WINDOW)
        b = events.event_car(r["EWZ"], r[GLOBAL], e.dia0, WINDOW)
        row = {"Fecha": e.dia0, "País": e.pais, "Evento": e.nombre,
               "Argentina CAR": a["car"], "Argentina t": a["t"], "Argentina p emp": a["p_emp"],
               "Brasil CAR": b["car"], "Brasil t": b["t"], "Brasil p emp": b["p_emp"]}
        if "Bonos" in r:
            c = events.event_car(r["Bonos"], r[GLOBAL], e.dia0, WINDOW)
            row.update({"Bonos CAR": c["car"], "Bonos t": c["t"], "Bonos p emp": c["p_emp"]})
        rows.append(row)
    return pd.DataFrame(rows)


def attribution(r: pd.DataFrame, est: tuple[str, str]) -> tuple[pd.Series, events.FactorFit]:
    X = factors(r, est)
    idx = r.loc[est[0]:est[1]].index
    fit = events.fit_factor_model(r["AR"].loc[idx], X.loc[idx])
    period = r.loc[CAIDA[0]:CAIDA[1]].index
    return events.attribute(r["AR"], X, fit, period), fit


def lula_cross_section(r: pd.DataFrame) -> pd.DataFrame:
    """Beta de cada acción al shock propio de Brasil (estimado antes de la elección) vs su
    caída el día de la reelección. Si el contagio va por exposición a Brasil, la relación
    debería ser negativa y fuerte."""
    est = ("2025-11-03", "2026-09-20")
    X = factors(r, est)
    idx = r.loc[est[0]:est[1]].index
    rows = []
    for t in AR + ["MELI"] + BR_STOCKS:
        fit = events.fit_factor_model(r[t].loc[idx], X.loc[idx])
        rows.append({"ticker": t, "beta_brasil": fit.betas["Brasil"],
                     "ret_lula": np.expm1(r.loc[LULA, t]),
                     "grupo": "Brasil" if t in BR_STOCKS else ("MELI" if t == "MELI" else "Argentina")})
    return pd.DataFrame(rows).set_index("ticker")


def attribution_of(r: pd.DataFrame, y: str, extra: list[str] | None = None) -> tuple[pd.Series, events.FactorFit]:
    """Atribución de cualquier serie con los betas de la ventana base (opcionalmente con factores extra)."""
    X = factors(r, EST) if not extra else pd.concat([factors(r, EST), r[extra]], axis=1)
    idx = r.loc[EST[0]:EST[1]].index
    fit = events.fit_factor_model(r[y].loc[idx], X.loc[idx])
    return events.attribute(r[y], X, fit, r.loc[CAIDA[0]:CAIDA[1]].index), fit


def placebo(r: pd.DataFrame) -> pd.DataFrame:
    """El mismo método aplicado a otros países. Si también les diera un componente propio
    grande y negativo, el resultado argentino sería un artefacto del método."""
    rows = {}
    for t, name in {"AR": "Argentina (ADRs)", "Bonos": "Argentina (bonos)", **PARES}.items():
        a, fit = attribution_of(r, t)
        rows[name] = {"Mundo": a[GLOBAL].sum(), "Brasil": a["Brasil"], "Propio": a["idiosincrático"],
                      "total": a["total"], "beta Brasil": fit.betas["Brasil"], "R²": fit.r2}
    return pd.DataFrame(rows).T


def bootstrap_bands(r: pd.DataFrame) -> pd.DataFrame:
    """Intervalos de 95% re-estimando también el factor Brasil (bootstrap por bloques)."""
    est, period = r.loc[EST[0]:EST[1]].index, r.loc[CAIDA[0]:CAIDA[1]].index
    out = {}
    for y in ["AR", "Bonos"]:
        b = events.two_stage_bootstrap(r[y], r["EWZ"], r[GLOBAL], est, period, n_boot=5000)
        out[y] = b.quantile([0.025, 0.5, 0.975]).T.assign(
            **{"P(propio < 50%)": [np.nan, np.nan, float((b["propio"] > b.sum(axis=1) / 2).mean())]})
    return pd.concat(out)


def concentration(r: pd.DataFrame) -> dict:
    """¿El componente argentino vino de pocos días o fue un goteo?"""
    X = factors(r, EST)
    idx, period = r.loc[EST[0]:EST[1]].index, r.loc[CAIDA[0]:CAIDA[1]].index
    fit = events.fit_factor_model(r["AR"].loc[idx], X.loc[idx])
    d = (r["AR"] - X @ fit.betas).loc[period].sort_values()   # el alfa queda adentro, como en attribute
    return {"total": d.sum(), "peores5": d[:5].sum(), "peores10": d[:10].sum(), "mejores10": d[-10:].sum(),
            "peor": d.iloc[0], "peor_dia": d.index[0], "sd": fit.resid_std,
            "dias_2sd": int((d < -2 * fit.resid_std).sum()), "neg": float((d < 0).mean()), "n": len(d)}


def passthrough_by_size(r: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Traspaso de Brasil a Argentina según el tamaño del shock brasileño, y la interacción
    de ``big_brazil_days`` con distintos umbrales."""
    br = brazil_factor(r, EST)
    sd = br.loc[EST[0]:EST[1]].std()
    sample = r.index.difference(r.loc[LULA:].index[:2])
    g = events.fit_factor_model(r["AR"].loc[sample], r[GLOBAL].loc[sample])
    ar_abn = (r["AR"] - g.alpha - r[GLOBAL] @ g.betas).loc[sample]
    size = (br.loc[sample].abs() / sd)
    bins = pd.cut(size, [0, 1, 2, 3, np.inf], labels=["< 1", "1 a 2", "2 a 3", "> 3"], right=False)
    rows = {}
    for b in bins.cat.categories:
        x, y = br.loc[sample][bins == b], ar_abn[bins == b]
        beta = float(x @ y / (x @ x))
        se = float(np.sqrt(((y - beta * x) ** 2).sum() / (len(x) - 1) / (x @ x)))
        rows[b] = {"días": len(x), "traspaso": beta, "ee": se}
    by_size = pd.DataFrame(rows).T
    thr = {}
    for k in [2.0, 2.5, 3.0]:
        big = (br.abs() > k * sd).astype(float)
        X = pd.concat([r[GLOBAL], br, (br * big).rename("int")], axis=1)
        f = events.fit_factor_model(r["AR"].loc[sample], X.loc[sample])
        se = np.sqrt(np.diag(f.cov))[-1]
        thr[f"{k} desvíos"] = {"días grandes": int(big.loc[sample].sum()), "beta normal": f.betas["Brasil"],
                               "diferencia": f.betas["int"], "t": f.betas["int"] / se}
    return by_size, pd.DataFrame(thr).T


def sector_attribution(r: pd.DataFrame) -> pd.DataFrame:
    """La misma atribución, por sector: ¿la caída argentina fue de todos o de algunos?"""
    X = factors(r, EST)
    idx, period = r.loc[EST[0]:EST[1]].index, r.loc[CAIDA[0]:CAIDA[1]].index
    rows = {}
    for name, tickers in SECTORES.items():
        y = r[tickers].mean(axis=1)
        a = events.attribute(y, X, events.fit_factor_model(y.loc[idx], X.loc[idx]), period)
        rows[name] = {"Mundo": a[GLOBAL].sum(), "Brasil": a["Brasil"], "Argentina": a["idiosincrático"],
                      "total": a["total"]}
    return pd.DataFrame(rows).T


def lula_passthrough(cs: pd.DataFrame, r: pd.DataFrame) -> pd.DataFrame:
    """Qué parte de la caída que predecía el beta a Brasil se materializó el 26/10, por grupo."""
    shock = brazil_factor(r, ("2025-11-03", "2026-09-20")).loc[LULA]
    d = cs.assign(pred=cs["beta_brasil"] * shock, real=np.log1p(cs["ret_lula"]))
    out = d.groupby("grupo")[["pred", "real"]].mean()
    out["traspaso"] = out["real"] / out["pred"]
    return out


def big_brazil_days(r: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """¿Argentina siempre reacciona menos en los días grandes de Brasil, o solo con Lula?

    Si el traspaso es menor en todos los días grandes, el 26/10 no fue especial: es que los
    shocks grandes de Brasil son brasileños. Se excluyen el 26 y 27/10 para no medir a Lula
    con Lula."""
    br = brazil_factor(r, EST)
    big = (br.abs() > SHOCK_BR * br.loc[EST[0]:EST[1]].std()).astype(float)
    X = pd.concat([r[GLOBAL], br, (br * big).rename("Brasil x día grande")], axis=1)
    sample = X.index.difference(r.loc[LULA:].index[:2])
    fit = events.fit_factor_model(r["AR"].loc[sample], X.loc[sample])
    se = pd.Series(np.sqrt(np.diag(fit.cov)), index=X.columns)
    coefs = pd.DataFrame({"beta": fit.betas, "t": fit.betas / se}).loc[["Brasil", "Brasil x día grande"]]
    # Los días más grandes, uno por uno: retorno anormal de AR (neto de mundo) vs shock de Brasil.
    g = events.fit_factor_model(r["AR"].loc[sample], r[GLOBAL].loc[sample])
    ar_abn = r["AR"] - g.alpha - r[GLOBAL] @ g.betas
    top = br.abs().sort_values(ascending=False).index[:10].sort_values()
    days = pd.DataFrame({"Brasil": br.loc[top], "Argentina": ar_abn.loc[top]})
    days["traspaso"] = days["Argentina"] / days["Brasil"]
    return coefs, days


# ============================================================================ figuras

def fig_trajectory(p: pd.DataFrame) -> None:
    base = p.loc[MILEI:].ffill()
    ar = np.exp(np.log(base[AR]).diff().mean(axis=1).fillna(0).cumsum()) * 100
    series = {"ADRs argentinos (promedio)": (ar, C_AR), "Brasil (EWZ)": (base["EWZ"] / base["EWZ"].iloc[0] * 100, C_BR),
              "S&P 500": (base["SPY"] / base["SPY"].iloc[0] * 100, C_US)}
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for name, (s, c) in series.items():
        ax.plot(s, color=c, lw=2, label=f"{name}: {s.iloc[-1] - 100:+.0f}%")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.yaxis.set_minor_formatter(mtick.NullFormatter())
    ax.set_yticks([50, 75, 100, 150, 200, 300])
    ax.axhline(100, color=style.BASELINE, lw=1)
    for i, e in enumerate(EVENTOS, 1):
        d = pd.Timestamp(e.dia0)
        if d < base.index[0]:
            continue
        y = ar.loc[ar.index[ar.index.get_indexer([d], method="bfill")[0]]]
        ax.annotate(str(i), xy=(d, y), xytext=(-12 if i == 1 else 0, 14 if e.pais != "BR" else -16), textcoords="offset points",
                    ha="center", va="center", fontsize=8.5, fontweight="bold", color=style.SURFACE,
                    bbox=dict(boxstyle="circle,pad=0.25", fc=C_BR if e.pais == "BR" else style.INK_2, ec="none"))
    ax.set_ylabel("Valor en USD, base 100 = asunción de Milei (escala log)")
    ax.legend(loc="upper left")
    ax.set_title("Dos años de rally y cuatro meses de caída", pad=26)
    style.subtitle(ax, "Números: eventos del catálogo (gris = Argentina o global, verde = Brasil). Ver tabla de eventos")
    style.source(fig, "Canasta equiponderada de 13 ADRs argentinos, rebalanceo diario. Fuente: Yahoo Finance.")
    style.save(fig, FIG / "01_trayectoria.png")


def fig_events(tab: pd.DataFrame) -> None:
    tab = tab.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(tab))
    fig, ax = plt.subplots(figsize=(11, 6.4))
    h = 0.38
    ax.barh(y + h / 2, tab["Argentina CAR"] * 100, h, color=C_AR, label="ADRs argentinos")
    ax.barh(y - h / 2, tab["Brasil CAR"] * 100, h, color=C_BR, label="Brasil (EWZ)")
    for yi, (car, t) in zip(y + h / 2, zip(tab["Argentina CAR"], tab["Argentina t"])):
        ax.text(car * 100 + (0.6 if car >= 0 else -0.6), yi, f"{car * 100:+.1f}" + (" *" if abs(t) > 1.96 else ""),
                va="center", ha="left" if car >= 0 else "right", fontsize=9, color=style.INK_2)
    for yi, (car, t) in zip(y - h / 2, zip(tab["Brasil CAR"], tab["Brasil t"])):
        ax.text(car * 100 + (0.6 if car >= 0 else -0.6), yi, f"{car * 100:+.1f}" + (" *" if abs(t) > 1.96 else ""),
                va="center", ha="left" if car >= 0 else "right", fontsize=9, color=style.INK_2)
    n = len(tab)
    ax.set_yticks(y, [f"{n - i}. {pd.Timestamp(f):%d/%m/%y}  {ev}" for i, (f, ev) in enumerate(zip(tab["Fecha"], tab["Evento"]))])
    ax.axvline(0, color=style.BASELINE, lw=1)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.set_xlim(-30, 38)
    ax.set_xlabel("Retorno anormal acumulado, día 0 y +1 (descontado S&P 500, petróleo y tasas)")
    ax.legend(loc="lower right")
    ax.grid(axis="y", visible=False)
    ax.set_title("Lo que mueve a la Argentina es la política argentina", pad=26)
    style.subtitle(ax, "Las elecciones propias movieron los ADRs 20-31%. Lula, 8%. * = significativo al 5%")
    style.save(fig, FIG / "02_eventos.png")


def fig_cross_section(cs: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 6))
    colors = {"Argentina": C_AR, "MELI": style.VIOLET, "Brasil": C_BR}
    for g, d in cs.groupby("grupo"):
        ax.scatter(d["beta_brasil"], d["ret_lula"] * 100, s=60, color=colors[g], edgecolor=style.SURFACE, lw=1.5,
                   label={"Argentina": "ADRs argentinos", "MELI": "Mercado Libre", "Brasil": "Acciones brasileñas"}[g],
                   zorder=3)
    nudge = {"CRESY": (-36, -12), "EDN": (5, 6), "BMA": (5, -10), "GGAL": (-30, -10)}
    for t, row in cs.iterrows():
        ax.annotate(t, (row["beta_brasil"], row["ret_lula"] * 100), xytext=nudge.get(t, (5, 4)),
                    textcoords="offset points", fontsize=8.5, color=style.INK_2)
    ar = cs[cs["grupo"] == "Argentina"]
    b, a = np.polyfit(ar["beta_brasil"], ar["ret_lula"] * 100, 1)
    corr = ar[["beta_brasil", "ret_lula"]].corr().iloc[0, 1]
    xs = np.linspace(ar["beta_brasil"].min(), ar["beta_brasil"].max(), 10)
    ax.plot(xs, a + b * xs, color=C_AR, lw=1.2, ls="--")
    ax.axhline(0, color=style.BASELINE, lw=1)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Sensibilidad al shock propio de Brasil (beta, estimada antes de la elección)")
    ax.set_ylabel("Retorno el 26/10/2026")
    ax.legend(loc="lower left")
    ax.set_title("El día de Lula cayó más quien más dependía de Brasil", pad=26)
    style.subtitle(ax, f"Entre los ADRs argentinos, correlación beta vs caída: {corr:.2f}. los bancos cayeron más, la energía menos")
    style.save(fig, FIG / "03_lula_corte_transversal.png")


def fig_rolling_beta(r: pd.DataFrame) -> pd.Series:
    br = brazil_factor(r, EST)
    rb = events.rolling_beta(r["AR"], br, r[GLOBAL], window=120)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axvspan(pd.Timestamp(CAMPANA_BR[0]), pd.Timestamp(CAMPANA_BR[1]), color=C_BR, alpha=0.12, lw=0)
    ax.text(pd.Timestamp(CAMPANA_BR[0]), 1.08, " Campaña en Brasil", fontsize=9.5, color=style.INK_2, va="top")
    ax.plot(rb, color=C_AR, lw=2)
    ax.axhline(0, color=style.BASELINE, lw=1)
    ax.set_ylim(-0.1, 1.1)
    ax.set_ylabel("Beta de los ADRs argentinos\nal shock propio de Brasil (120 ruedas)")
    ax.set_title("Argentina se volvió más sensible a Brasil justo antes de su elección", pad=26)
    style.subtitle(ax, f"Beta de {rb.loc['2025'].mean():.2f} en promedio en 2025; {rb.loc['2026-09'].mean():.2f} en "
                       f"septiembre 2026. Controla por S&P 500, petróleo y tasas")
    style.save(fig, FIG / "04_beta_brasil.png")
    return rb


def fig_waterfall(attr: pd.Series) -> None:
    order = ["SPY", "^TNX", "BZ=F", "Brasil", "idiosincrático"]
    vals = attr[order] * 100
    fig, ax = plt.subplots(figsize=(10, 5.4))
    cum = 0.0
    colors = {"SPY": C_US, "^TNX": C_US, "BZ=F": C_US, "Brasil": C_BR, "idiosincrático": C_AR}
    for i, k in enumerate(order):
        v = vals[k]
        ax.bar(i, v, bottom=cum, color=colors[k], width=0.62)
        top, bottom = max(cum, cum + v), min(cum, cum + v)
        ax.text(i, top + 0.5 if v >= 0 else bottom - 0.5, f"{v:+.1f}", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=10.5, color=style.INK)
        ax.plot([i + 0.31, i + 0.69], [cum + v] * 2, color=style.MUTED, lw=0.8)
        cum += v
    total = attr["total"] * 100
    ax.bar(len(order), total, color=style.INK_2, width=0.62)
    ax.text(len(order), total - 0.5, f"{total:+.1f}", ha="center", va="top", fontsize=10.5, fontweight="bold")
    ax.axhline(0, color=style.BASELINE, lw=1)
    ax.set_ylim(min(cum, total) - 4, max(0, vals.clip(lower=0).sum()) + 3)
    short = {"SPY": "Acciones\nglobales", "^TNX": "Tasas\nEEUU", "BZ=F": "Petróleo", "Brasil": "Brasil\n(propio)",
             "idiosincrático": "Argentina\n(propio)"}
    ax.set_xticks(range(len(order) + 1), [short[k] for k in order] + ["Total"])
    ax.set_ylabel("Contribución (puntos de retorno logarítmico)")
    ax.grid(axis="x", visible=False)
    simple = np.expm1(attr["total"]) * 100
    share = attr["idiosincrático"] / attr["total"] * 100
    ax.set_title("¿Quién tiró abajo a los ADRs argentinos desde julio?", pad=26)
    style.subtitle(ax, f"15/7 al 30/10/2026: {simple:.0f}% en dólares. El {share:.0f}% de la caída no lo explican "
                       f"ni Brasil ni el mundo")
    style.source(fig, "Betas estimados del 3/11/2025 al 14/7/2026, fuera del período explicado. Factor Brasil = EWZ "
                      "neto de S&P 500, petróleo y tasas.")
    style.save(fig, FIG / "05_atribucion.png")


def fig_path(path: pd.DataFrame) -> None:
    lines = {"Argentina (propio)": (path["idiosincrático"], C_AR, 2.4),
             "Brasil (propio)": (path["Brasil"], C_BR, 2),
             "Mundo": (path[GLOBAL].sum(axis=1), C_US, 2)}
    fig, ax = plt.subplots(figsize=(11, 5.4))
    for name, (s_, c, lw) in lines.items():
        ax.plot(s_ * 100, color=c, lw=lw)
        ax.annotate(f"{name}  {s_.iloc[-1] * 100:+.0f}", (s_.index[-1], s_.iloc[-1] * 100), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=10, color=style.INK)
    for d, lab in [(PRIMERA_VUELTA_BR, "1ª vuelta\nBrasil"), (LULA, "Lula\nreelecto")]:
        ax.axvline(pd.Timestamp(d), color=style.MUTED, lw=0.8, ls=":")
        ax.text(pd.Timestamp(d), 0.45, f" {lab}", transform=ax.get_xaxis_transform(), fontsize=8.5, color=style.INK_2,
                ha="left", va="bottom")
    ax.axhline(0, color=style.BASELINE, lw=1)
    ax.set_xlim(path.index[0], path.index[-1] + pd.Timedelta(days=22))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{pd.Timestamp.fromordinal(int(v)):%d/%m}"))
    ax.set_ylabel("Contribución acumulada (puntos log)")
    pre = path["idiosincrático"].loc[:pd.Timestamp(PRIMERA_VUELTA_BR) - pd.Timedelta(days=1)].iloc[-1]
    br_pre = path["Brasil"].loc[:pd.Timestamp(LULA) - pd.Timedelta(days=1)].iloc[-1]
    ax.set_title("La caída argentina estaba completa antes de que Brasil votara", pad=26)
    style.subtitle(ax, f"Al 2/10 el componente argentino ya sumaba {pre * 100:.0f} puntos. Brasil empujó a favor "
                       f"({br_pre * 100:+.0f}) hasta el balotaje")
    style.source(fig, "Betas estimados del 3/11/2025 al 14/7/2026. Mundo = S&P 500, petróleo y tasas.")
    style.save(fig, FIG / "06_atribucion_diaria.png")


def fig_sectors(sec: pd.DataFrame) -> None:
    sec = sec.sort_values("total")
    comps = [("Mundo", C_US), ("Brasil", C_BR), ("Argentina", C_AR)]
    y = np.arange(len(sec))
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for i, name in enumerate(sec.index):
        neg, pos = 0.0, 0.0
        for comp, c in comps:
            v = sec.loc[name, comp] * 100
            left = pos if v >= 0 else neg + v
            ax.barh(i, abs(v), left=left, color=c, height=0.6, label=comp if i == 0 else None)
            pos, neg = (pos + v, neg) if v >= 0 else (pos, neg + v)
        ax.text(neg - 0.8, i, f"{sec.loc[name, 'total'] * 100:+.0f}", va="center", ha="right", fontsize=10,
                fontweight="bold")
    ax.set_yticks(y, sec.index)
    ax.axvline(0, color=style.BASELINE, lw=1)
    ax.set_xlim(sec[["Brasil", "Argentina"]].clip(upper=0).sum(axis=1).min() * 100 - 8, 10)
    ax.set_xlabel("Contribución a la caída del 15/7 al 30/10/2026 (puntos log)")
    ax.legend(loc="upper left", ncols=3)
    ax.grid(axis="y", visible=False)
    worst = sec["Argentina"].idxmin()
    ax.set_title("El riesgo argentino se concentró en bancos y servicios regulados", pad=26)
    style.subtitle(ax, f"Componente propio: {worst.lower()} {sec.loc[worst, 'Argentina'] * 100:+.0f}, agro e inmuebles "
                       f"{sec.loc['Agro e inmuebles', 'Argentina'] * 100:+.0f}. Número = caída total del sector")
    style.save(fig, FIG / "07_sectores.png")


def fig_placebo(pl: pd.DataFrame) -> None:
    pl = pl.sort_values("Propio")
    y = np.arange(len(pl))
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [C_AR if n.startswith("Argentina") else style.MUTED for n in pl.index]
    ax.barh(y, pl["Propio"] * 100, color=colors, height=0.62)
    for yi, v in zip(y, pl["Propio"] * 100):
        ax.text(v + (0.6 if v >= 0 else -0.6), yi, f"{v:+.0f}", va="center", ha="left" if v >= 0 else "right",
                fontsize=10)
    ax.set_yticks(y, pl.index)
    ax.axvline(0, color=style.BASELINE, lw=1)
    ax.set_xlim(-28, 18)
    ax.set_xlabel("Componente propio del 15/7 al 30/10/2026 (puntos log, neto de mundo y Brasil)")
    ax.grid(axis="y", visible=False)
    ax.set_title("El mismo método, aplicado a los vecinos, no encuentra nada parecido", pad=26)
    style.subtitle(ax, "Solo Argentina tiene un componente propio grande y negativo, en acciones y en bonos")
    style.source(fig, "Bonos: GD30D, GD35D y GD41D en dólares MEP (data912/BYMA). Pares: ETFs MSCI de cada país.")
    style.save(fig, FIG / "08_placebo.png")


def fig_passthrough(by_size: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(by_size))
    ax.bar(x, by_size["traspaso"], color=C_BR, width=0.6)
    ax.errorbar(x, by_size["traspaso"], yerr=1.96 * by_size["ee"], fmt="none", ecolor=style.INK_2, capsize=4, lw=1)
    for xi, (v, n) in enumerate(zip(by_size["traspaso"], by_size["días"])):
        ax.text(xi, 0.03, f"{v:.2f}\n{int(n)} días", ha="center", va="bottom", fontsize=9.5, color=style.SURFACE,
                fontweight="bold")
    ax.set_xticks(x, [f"{b} desvíos" for b in by_size.index])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Tamaño del shock propio de Brasil ese día")
    ax.set_ylabel("Traspaso a los ADRs argentinos")
    ax.grid(axis="x", visible=False)
    ax.set_title("Con shocks más grandes de Brasil, Argentina acompaña algo menos", pad=26)
    style.subtitle(ax, "Tendencia, no prueba: los intervalos de 95% se superponen. Pendiente de los ADRs (netos del "
                       "mundo) sobre el shock de Brasil")
    style.save(fig, FIG / "09_traspaso_por_tamano.png")


# ============================================================================ main

def pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def main() -> None:
    style.apply()
    p, r = load()
    r = load_extra(p, r)
    tab = event_table(r)
    attr, fit = attribution(r, EST)
    robust = pd.DataFrame({f"{a} a {b}": attribution(r, (a, b))[0] for a, b in [EST] + EST_ALT}).T
    cs = lula_cross_section(r)
    period = r.loc[CAIDA[0]:CAIDA[1]].index
    X = factors(r, EST)
    band = events.attribution_band(X, fit, period)
    # P(componente argentino < 50% de la caída): el componente tendría que ser menos negativo que total/2.
    share_p = stats.norm.sf((0.5 * attr["total"] - attr["idiosincrático"]) / band["sd_betas"])
    # ¿Qué tan raro es un residuo así? Todas las ventanas de igual largo desde 2023, con los mismos betas.
    resid = r["AR"] - fit.alpha - X @ fit.betas
    roll = resid.loc["2023-01-01":CAIDA[0]].rolling(len(period)).sum().dropna()
    freq = float((roll <= attr["idiosincrático"]).mean())
    path = events.attribute_path(r["AR"], X, fit, period)
    sec = sector_attribution(r)
    ar_cs = cs[cs["grupo"] == "Argentina"]
    rho, rho_p = stats.pearsonr(ar_cs["beta_brasil"], ar_cs["ret_lula"])
    pt = lula_passthrough(cs, r)
    big_coefs, big_days = big_brazil_days(r)
    pl = placebo(r)
    bands = bootstrap_bands(r)
    conc = concentration(r)
    by_size, thr = passthrough_by_size(r)
    bond_attr = pd.DataFrame({t: attribution_of(r, t)[0] for t in ["Bonos"] + BONOS}).T
    robust_f = pd.DataFrame({"Base": attribution_of(r, "AR")[0],
                             "+ Emergentes (EEM)": attribution_of(r, "AR", ["EEM"])[0],
                             "+ LatAm sin Brasil": attribution_of(r, "AR", ["LatAm sin Brasil"])[0]}).T

    fig_trajectory(p)
    fig_events(tab)
    fig_cross_section(cs)
    rb = fig_rolling_beta(r)
    fig_waterfall(attr)
    fig_path(path)
    fig_sectors(sec)
    fig_placebo(pl)
    fig_passthrough(by_size)

    cum = lambda cols, a, b: np.expm1(r.loc[a:b, cols].sum())  # noqa: E731
    lines = ["# Resultados (generado por estudio/run.py)", "",
             f"Datos: {r.index[0].date()} a {r.index[-1].date()}.", "",
             "## Retorno acumulado en USD", "",
             pd.DataFrame({"Desde asunción de Milei": cum(["AR", "EWZ", "SPY", "MELI"],
                                                          pd.Timestamp(MILEI) + pd.Timedelta(days=1), END),
                           "Desde 15/7/2026": cum(["AR", "EWZ", "SPY", "MELI"], CAIDA[0], END)})
             .map(pct).to_markdown(), "",
             "## Eventos: retorno anormal acumulado [0, +1]", "",
             tab.assign(**{c: tab[c].map(pct) for c in ["Argentina CAR", "Brasil CAR"]},
                        **{c: tab[c].map(pct) for c in ["Bonos CAR"]},
                        **{c: tab[c].round(1) for c in ["Argentina t", "Brasil t", "Bonos t"]},
                        **{c: tab[c].round(3) for c in ["Argentina p emp", "Brasil p emp", "Bonos p emp"]})
             .to_markdown(index=False),
             "", "p emp = fracción de ventanas de 2 días de la ventana de estimación con un residuo al menos igual.", "",
             "## Atribución de la caída desde el 15/7/2026 (puntos log)", "",
             f"Betas: {fit.betas.round(2).to_dict()}, R² {fit.r2:.2f}, {fit.n} ruedas.", "",
             (robust.rename(columns=FACTOR_NAMES) * 100).round(1).to_markdown(), "",
             f"Incertidumbre (ventana base): desvío por estimación de betas {band['sd_betas'] * 100:.1f} pts; "
             f"intervalo 95% del componente argentino {(attr['idiosincrático'] - 1.96 * band['sd_betas']) * 100:.1f} a "
             f"{(attr['idiosincrático'] + 1.96 * band['sd_betas']) * 100:.1f}. P(componente argentino < 50% de la "
             f"caída) = {share_p:.3f}. Contra ruido normal ({band['sd_noise'] * 100:.1f} pts en {len(period)} ruedas): "
             f"z = {attr['idiosincrático'] / band['sd_noise']:.1f}. Ventanas de {len(period)} ruedas desde 2023 con un componente "
             f"argentino igual o peor: {freq:.1%} (peor: {roll.min() * 100:.1f}, el {roll.idxmin().date()}).", "",
             "### Bootstrap en dos etapas (re-estima también el factor Brasil; 5000 réplicas, bloques de 10)", "",
             (bands * 100).round(1).rename(columns={"P(propio < 50%)": "P(propio < 50%) x100"}).to_markdown(), "",
             "### Robustez a factores adicionales (AR)", "",
             (robust_f * 100).round(1).to_markdown(), "",
             "### Concentración del componente argentino", "",
             f"Total {conc['total'] * 100:.1f}; 5 peores días {conc['peores5'] * 100:.1f}; 10 peores "
             f"{conc['peores10'] * 100:.1f}; 10 mejores {conc['mejores10'] * 100:+.1f}. Peor día "
             f"{conc['peor'] * 100:.1f}% ({conc['peor_dia'].date()}). Días por debajo de -2 desvíos "
             f"({2 * conc['sd'] * 100:.1f}%): {conc['dias_2sd']} de {conc['n']}. Días negativos: {conc['neg']:.0%}.", "",
             "### Trayectoria del componente argentino", "",
             f"Acumulado al 2/10 (antes de la 1ª vuelta brasileña): "
             f"{path['idiosincrático'].loc[:'2026-10-02'].iloc[-1] * 100:.1f} pts; al 23/10 (antes del balotaje): "
             f"{path['idiosincrático'].loc[:'2026-10-23'].iloc[-1] * 100:.1f}; final: "
             f"{path['idiosincrático'].iloc[-1] * 100:.1f}. Brasil al 23/10: {path['Brasil'].loc[:'2026-10-23'].iloc[-1] * 100:.1f}; "
             f"final {path['Brasil'].iloc[-1] * 100:.1f}.", "",
             "### Por sector (puntos log)", "",
             (sec * 100).round(1).to_markdown(), "",
             "## Bonos soberanos (puntos log)", "",
             (bond_attr * 100).round(1).to_markdown(), "",
             "## Placebo: el mismo método en otros países (puntos log)", "",
             pl.assign(**{c: pl[c] * 100 for c in ["Mundo", "Brasil", "Propio", "total"]}).round(2).to_markdown(), "",
             "## Reelección de Lula: corte transversal", "",
             cs.assign(ret_lula=cs["ret_lula"].map(pct), beta_brasil=cs["beta_brasil"].round(2))
             .sort_values("beta_brasil").to_markdown(), "",
             f"Correlación beta vs caída (ADRs argentinos, n={len(ar_cs)}): {rho:.2f}, p = {rho_p:.3f}.", "",
             "Traspaso: caída real / caída predicha por el beta a Brasil (log, promedio por grupo).", "",
             pt.round(3).to_markdown(), "",
             "## ¿Los días grandes de Brasil traspasan menos?", "",
             f"Regresión de AR sobre mundo + Brasil + Brasil x (|shock| > {SHOCK_BR} desvíos), toda la muestra "
             "sin el 26-27/10/2026.", "",
             big_coefs.round(2).to_markdown(), "",
             "Por umbral:", "", thr.round(2).to_markdown(), "",
             "Traspaso por tamaño del shock (pendiente sin constante):", "", by_size.round(3).to_markdown(), "",
             "Los 10 días con mayor shock propio de Brasil (log):", "",
             big_days.assign(Brasil=big_days["Brasil"].map(pct), Argentina=big_days["Argentina"].map(pct),
                             traspaso=big_days["traspaso"].round(2)).to_markdown(), "",
             f"Beta rodante a Brasil: promedio 2025 {rb.loc['2025'].mean():.2f}, septiembre 2026 "
             f"{rb.loc['2026-09'].mean():.2f}, último {rb.iloc[-1]:.2f}.", ""]
    (HERE / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
