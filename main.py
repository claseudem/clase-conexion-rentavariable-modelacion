import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats


def fetch_returns(ticker: str, period: str) -> pd.Series:
    data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if data.empty:
        print(f"ERROR: No se encontraron datos para '{ticker}'. Verifica el ticker.")
        sys.exit(1)
    returns = data["Close"].squeeze().pct_change().dropna()
    return returns


def risk_color(sigma1: float, sigma2: float) -> tuple[str, str]:
    """Devuelve colores: rojo para la más riesgosa, verde para la menos riesgosa."""
    if sigma1 >= sigma2:
        return "#e74c3c", "#2ecc71"
    return "#2ecc71", "#e74c3c"


def plot_histogram(ax, returns: pd.Series, ticker: str, color: str, es_mas_riesgosa: bool):
    mu = returns.mean()
    sigma = returns.std()
    var_95 = np.percentile(returns, 5)
    cvar_95 = returns[returns <= var_95].mean()

    # Histograma de retornos
    ax.hist(
        returns,
        bins=60,
        density=True,
        alpha=0.55,
        color=color,
        edgecolor="white",
        linewidth=0.4,
        label="Retornos diarios",
    )

    # Ajuste normal sobre los datos
    x = np.linspace(returns.min(), returns.max(), 400)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), color="black", lw=1.8, linestyle="-", label="Dist. Normal")

    # KDE real (distribución empírica)
    kde = stats.gaussian_kde(returns)
    ax.plot(x, kde(x), color=color, lw=2, linestyle="--", alpha=0.9, label="KDE (real)")

    # Líneas de referencia
    ax.axvline(var_95, color="#e67e22", lw=1.8, linestyle=":", label=f"VaR 95%: {var_95:.2%}")
    ax.axvline(cvar_95, color="#8e44ad", lw=1.8, linestyle=":", label=f"CVaR 95%: {cvar_95:.2%}")
    ax.axvline(mu, color="navy", lw=1.5, linestyle="-.", alpha=0.8, label=f"Media: {mu:.2%}")
    ax.axvline(0, color="gray", lw=0.8, linestyle="-", alpha=0.5)

    etiqueta = " ⚠ MÁS RIESGOSA" if es_mas_riesgosa else " ✓ MENOS RIESGOSA"
    titulo_color = "#c0392b" if es_mas_riesgosa else "#27ae60"
    ax.set_title(
        f"{ticker}{etiqueta}\nσ diaria={sigma:.2%}  |  Skew={returns.skew():.2f}  |  Kurt={returns.kurtosis():.2f}",
        fontsize=11,
        fontweight="bold",
        color=titulo_color,
    )
    ax.set_xlabel("Retorno diario", fontsize=10)
    ax.set_ylabel("Densidad de probabilidad", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", alpha=0.3)


def print_tabla(ticker1: str, ticker2: str, r1: pd.Series, r2: pd.Series):
    sigma1_anual = r1.std() * np.sqrt(252)
    sigma2_anual = r2.std() * np.sqrt(252)
    sharpe1 = (r1.mean() / r1.std()) * np.sqrt(252)
    sharpe2 = (r2.mean() / r2.std()) * np.sqrt(252)

    print(f"\n{'═'*55}")
    print(f"  {'MÉTRICA':<28} {ticker1:>10} {ticker2:>10}")
    print(f"{'═'*55}")
    print(f"  {'Volatilidad anual (σ)':<28} {sigma1_anual:>10.2%} {sigma2_anual:>10.2%}")
    print(f"  {'VaR 95% diario':<28} {np.percentile(r1,5):>10.2%} {np.percentile(r2,5):>10.2%}")
    print(f"  {'CVaR 95% diario':<28} {r1[r1<=np.percentile(r1,5)].mean():>10.2%} {r2[r2<=np.percentile(r2,5)].mean():>10.2%}")
    print(f"  {'Retorno medio anual':<28} {r1.mean()*252:>10.2%} {r2.mean()*252:>10.2%}")
    print(f"  {'Skewness':<28} {r1.skew():>10.2f} {r2.skew():>10.2f}")
    print(f"  {'Kurtosis (exceso)':<28} {r1.kurtosis():>10.2f} {r2.kurtosis():>10.2f}")
    print(f"  {'Sharpe ratio (aprox)':<28} {sharpe1:>10.2f} {sharpe2:>10.2f}")
    print(f"  {'Obs. (días)':<28} {len(r1):>10} {len(r2):>10}")
    print(f"{'═'*55}")

    mas_riesgosa = ticker1 if r1.std() > r2.std() else ticker2
    menos_riesgosa = ticker2 if mas_riesgosa == ticker1 else ticker1
    print(f"\n  ⚠  Acción MÁS RIESGOSA   → {mas_riesgosa}")
    print(f"  ✓  Acción MENOS RIESGOSA → {menos_riesgosa}\n")


def comparar(ticker1: str, ticker2: str, period: str):
    print(f"\nDescargando datos: {ticker1} y {ticker2} | Período: {period}")
    r1 = fetch_returns(ticker1, period)
    r2 = fetch_returns(ticker2, period)

    sigma1 = r1.std()
    sigma2 = r2.std()
    color1, color2 = risk_color(sigma1, sigma2)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(
        f"Comparador de Riesgo — {ticker1} vs {ticker2}  ({period})",
        fontsize=14,
        fontweight="bold",
        y=1.01,
    )

    plot_histogram(axes[0], r1, ticker1, color1, es_mas_riesgosa=(sigma1 >= sigma2))
    plot_histogram(axes[1], r2, ticker2, color2, es_mas_riesgosa=(sigma2 > sigma1))

    plt.tight_layout()
    output = f"comparador_{ticker1}_{ticker2}.png"
    plt.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Gráfico guardado: {output}")
    plt.show()

    print_tabla(ticker1, ticker2, r1, r2)


def main():
    parser = argparse.ArgumentParser(
        description="Compara el riesgo cuantitativo entre 2 acciones usando retornos diarios."
    )
    parser.add_argument("ticker1", help="Primer ticker (ej: AAPL)")
    parser.add_argument("ticker2", help="Segundo ticker (ej: TSLA)")
    parser.add_argument(
        "--period",
        default="1y",
        choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        help="Período histórico (default: 1y)",
    )
    args = parser.parse_args()
    comparar(args.ticker1, args.ticker2, args.period)


if __name__ == "__main__":
    main()
