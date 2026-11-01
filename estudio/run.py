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

sys.path.insert(0, str(Path(__file__).parent))

from eventos import EVENTOS  # noqa: E402

from quantkit import events, style  # noqa: E402
from quantkit.data import load_prices  # noqa: E402

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
        rows.append({"Fecha": e.dia0, "País": e.pais, "Evento": e.nombre,
                     "Argentina CAR": a["car"], "Argentina t": a["t"],
                     "Brasil CAR": b["car"], "Brasil t": b["t"]})
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


# ============================================================================ main

def pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def main() -> None:
    style.apply()
    p, r = load()
    tab = event_table(r)
    attr, fit = attribution(r, EST)
    robust = pd.DataFrame({f"{a} a {b}": attribution(r, (a, b))[0] for a, b in [EST] + EST_ALT}).T
    cs = lula_cross_section(r)

    fig_trajectory(p)
    fig_events(tab)
    fig_cross_section(cs)
    rb = fig_rolling_beta(r)
    fig_waterfall(attr)

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
                        **{c: tab[c].round(1) for c in ["Argentina t", "Brasil t"]}).to_markdown(index=False), "",
             "## Atribución de la caída desde el 15/7/2026 (puntos log)", "",
             f"Betas: {fit.betas.round(2).to_dict()}, R² {fit.r2:.2f}, {fit.n} ruedas.", "",
             (robust.rename(columns=FACTOR_NAMES) * 100).round(1).to_markdown(), "",
             "## Reelección de Lula: corte transversal", "",
             cs.assign(ret_lula=cs["ret_lula"].map(pct), beta_brasil=cs["beta_brasil"].round(2))
             .sort_values("beta_brasil").to_markdown(), "",
             f"Beta rodante a Brasil: promedio 2025 {rb.loc['2025'].mean():.2f}, septiembre 2026 "
             f"{rb.loc['2026-09'].mean():.2f}, último {rb.iloc[-1]:.2f}.", ""]
    (HERE / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
