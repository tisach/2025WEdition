import sys
import math
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Sicherstellen, dass der results-Ordner existiert
os.makedirs("results", exist_ok=True)


def lade_csv(pfad: str) -> np.ndarray:
    """
    Lädt die Messwerte aus einer CSV-Datei.
    Erwartet eine Spalte 'latenz_ns'.
    Gibt ein NumPy-Array in Nanosekunden zurück.
    """
    try:
        df = pd.read_csv(pfad)
        if "latenz_ns" not in df.columns:
            raise ValueError("Spalte 'latenz_ns' nicht gefunden.")
        return df["latenz_ns"].values.astype(float)
    except FileNotFoundError:
        print(f"Fehler: Datei '{pfad}' nicht gefunden.")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler beim Laden der Datei: {e}")
        sys.exit(1)


def berechne_statistik(daten_ns: np.ndarray) -> None:
    """
    Berechnet und gibt grundlegende statistische Größen aus.
    Arbeitet intern in Mikrosekunden (µs).
    """
    if len(daten_ns) == 0:
        print("Keine Daten vorhanden.")
        return

    daten_us = daten_ns / 1000.0  # von ns -> µs

    n = len(daten_us)
    daten_min = float(np.min(daten_us))
    daten_max = float(np.max(daten_us))
    mean = float(np.mean(daten_us))
    median = float(np.median(daten_us))
    std = float(np.std(daten_us, ddof=1))  # Stichproben-Standardabweichung

    # Quantile
    p90 = float(np.percentile(daten_us, 90))
    p95 = float(np.percentile(daten_us, 95))
    p99 = float(np.percentile(daten_us, 99))

    # 95%-Konfidenzintervall für den Mittelwert
    z = 1.96
    halbweite = z * std / math.sqrt(n)
    ci_unten = mean - halbweite
    ci_oben = mean + halbweite

    print("=" * 70)
    print("Statistik für die Pipe-Verweildauer (Einweg) [µs]")
    print("=" * 70)
    print(f"Anzahl Messwerte       : {n}")
    print(f"Minimum                : {daten_min:.3f} µs")
    print(f"Maximum                : {daten_max:.3f} µs")
    print(f"Mittelwert             : {mean:.3f} µs")
    print(f"Median                 : {median:.3f} µs")
    print(f"Standardabweichung     : {std:.3f} µs")
    print(f"90. Perzentil          : {p90:.3f} µs")
    print(f"95. Perzentil          : {p95:.3f} µs")
    print(f"99. Perzentil          : {p99:.3f} µs")
    print(f"95% Konfidenzintervall : [{ci_unten:.3f}, {ci_oben:.3f}] µs")
    print("=" * 70)


def zeichne_histogramm(daten_ns: np.ndarray, dateiname: str, x_max_us: float | None = None) -> None:
    """
    Zeichnet ein Histogramm der Latenzen (in µs) und speichert es als PNG.
    Optional kann die x-Achse auf x_max_us begrenzt werden.
    """
    daten_us = daten_ns / 1000.0

    plt.figure(figsize=(8, 5))
    plt.hist(daten_us, bins=50, edgecolor="black", linewidth=0.5)
    plt.xlabel("Verweildauer in der Pipe (µs)")
    plt.ylabel("Häufigkeit")
    plt.title("Histogramm der Pipe-Verweildauer (Einweg)")
    if x_max_us is not None:
        plt.xlim(0, x_max_us)
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_histogramm_log(daten_ns: np.ndarray, dateiname: str) -> None:
    """
    Histogramm mit logarithmischer y-Achse (in µs), um seltene Ausreißer sichtbar zu machen.
    """
    daten_us = daten_ns / 1000.0

    plt.figure(figsize=(8, 5))
    plt.hist(daten_us, bins=50, edgecolor="black", linewidth=0.5)
    plt.yscale("log")
    plt.xlabel("Verweildauer in der Pipe (µs)")
    plt.ylabel("Häufigkeit (log-Skala)")
    plt.title("Histogramm der Pipe-Verweildauer (log. Skala)")
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_boxplot(daten_ns: np.ndarray, dateiname: str) -> None:
    """
    Zeichnet einen Boxplot der Latenzen (in µs).
    """
    daten_us = daten_ns / 1000.0

    plt.figure(figsize=(5, 6))
    plt.boxplot(daten_us, vert=True, showfliers=True)
    plt.ylabel("Verweildauer in der Pipe (µs)")
    plt.title("Boxplot der Pipe-Verweildauer (Einweg)")
    plt.grid(True, axis="y", linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_zeitreihe(daten_ns: np.ndarray, dateiname: str, y_max_us: float | None = None) -> None:
    """
    Zeitreihenplot der Latenzen (in µs).
    """
    daten_us = daten_ns / 1000.0

    plt.figure(figsize=(10, 4))
    plt.plot(daten_us, linewidth=0.5)
    plt.xlabel("Messung Nr.")
    plt.ylabel("Verweildauer (µs)")
    plt.title("Pipe-Verweildauer über der Zeit")
    if y_max_us is not None:
        plt.ylim(0, y_max_us)
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_scatter(daten_ns: np.ndarray, dateiname: str, y_max_us: float | None = None) -> None:
    """
    Scatterplot: Messwert vs. Messindex (in µs).
    """
    daten_us = daten_ns / 1000.0

    plt.figure(figsize=(10, 4))
    plt.scatter(range(len(daten_us)), daten_us, s=2, alpha=0.5)
    plt.xlabel("Messung Nr.")
    plt.ylabel("Verweildauer (µs)")
    plt.title("Pipe-Verweildauer – Scatterplot")
    if y_max_us is not None:
        plt.ylim(0, y_max_us)
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_rolling_mean(daten_ns: np.ndarray, dateiname: str, fenster: int = 1000) -> None:
    """
    Zeichnet den gleitenden Mittelwert der Latenzen (in µs).
    """
    daten_us = daten_ns / 1000.0
    s = pd.Series(daten_us)
    roll = s.rolling(window=fenster).mean()

    plt.figure(figsize=(10, 4))
    plt.plot(daten_us, linewidth=0.3, alpha=0.3, label="Einzelmessungen")
    plt.plot(roll, linewidth=1.0, label=f"Gleitender Mittelwert (Fenster={fenster})")
    plt.xlabel("Messung Nr.")
    plt.ylabel("Verweildauer (µs)")
    plt.title("Pipe-Verweildauer – gleitender Mittelwert")
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_cdf(daten_ns: np.ndarray, dateiname: str) -> None:
    """
    Zeichnet die empirische Verteilungsfunktion (CDF) der Latenzen (in µs).
    """
    daten_us = np.sort(daten_ns / 1000.0)
    n = len(daten_us)
    y = np.arange(1, n + 1) / n

    plt.figure(figsize=(8, 5))
    plt.plot(daten_us, y, linewidth=1.0)
    plt.xlabel("Verweildauer in der Pipe (µs)")
    plt.ylabel("Kumulative Wahrscheinlichkeit")
    plt.title("Empirische Verteilungsfunktion (CDF) der Pipe-Verweildauer")
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def zeichne_autokorrelation(daten_ns: np.ndarray, dateiname: str, max_lag: int = 200) -> None:
    """
    Autokorrelation der Latenzen (in µs).
    """
    daten_us = daten_ns / 1000.0
    daten_norm = (daten_us - np.mean(daten_us)) / np.std(daten_us)

    autocorr = []
    for lag in range(1, max_lag):
        v1 = daten_norm[:-lag]
        v2 = daten_norm[lag:]
        autocorr.append(np.correlate(v1, v2)[0] / len(v1))

    plt.figure(figsize=(8, 5))
    plt.stem(range(1, max_lag), autocorr, linefmt='-', markerfmt='o', basefmt=' ')
    plt.xlabel("Lag")
    plt.ylabel("Autokorrelation")
    plt.title("Autokorrelation der Pipe-Verweildauer")
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  {dateiname}")


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python3 messwerte_analyse.py results/pipe_latenz.csv")
        sys.exit(1)

    pfad = sys.argv[1]
    daten_ns = lade_csv(pfad)

    if len(daten_ns) == 0:
        print("Keine gültigen Messwerte gefunden.")
        sys.exit(1)

    # 1. Statistik ausgeben
    berechne_statistik(daten_ns)
    print("\nErzeuge Plots...\n")

    # 2. Plots erzeugen (alle in µs beschriftet)
    zeichne_histogramm(daten_ns, "results/pipe_latenz_histogramm.png", x_max_us=200.0)
    zeichne_histogramm_log(daten_ns, "results/pipe_latenz_histogramm_log.png")
    zeichne_boxplot(daten_ns, "results/pipe_latenz_boxplot.png")
    zeichne_cdf(daten_ns, "results/pipe_latenz_cdf.png")
    zeichne_zeitreihe(daten_ns, "results/pipe_latenz_zeitreihe.png", y_max_us=250.0)
    zeichne_scatter(daten_ns, "results/pipe_latenz_scatter.png", y_max_us=250.0)
    zeichne_rolling_mean(daten_ns, "results/pipe_latenz_rolling_mean.png", fenster=1000)
    zeichne_autokorrelation(daten_ns, "results/pipe_latenz_autocorr.png", max_lag=200)

    print("\nFertig. Plots wurden in 'results/' gespeichert.")


if __name__ == "__main__":
    main()
