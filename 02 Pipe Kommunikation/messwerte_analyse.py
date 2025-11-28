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
    """
    try:
        df = pd.read_csv(pfad)
        if "latenz_ns" not in df.columns:
            raise ValueError("Spalte 'latenz_ns' nicht gefunden")
        return df["latenz_ns"].values
    except FileNotFoundError:
        print(f"Fehler: Datei '{pfad}' nicht gefunden.")
        sys.exit(1)
    except Exception as e:
        print(f"Fehler beim Laden der Datei: {e}")
        sys.exit(1)


def berechne_statistik(daten: np.ndarray) -> None:
    """
    Berechnet und gibt grundlegende statistische Größen aus.
    """
    n = len(daten)
    if n == 0:
        print("Keine Daten vorhanden.")
        return

    daten_min = float(np.min(daten))
    daten_max = float(np.max(daten))
    mean = float(np.mean(daten))
    median = float(np.median(daten))
    std = float(np.std(daten, ddof=1))  # Stichproben-Standardabweichung

    # Perzentile
    p95 = float(np.percentile(daten, 95))
    p99 = float(np.percentile(daten, 99))

    # 95%-Konfidenzintervall für den Mittelwert
    z = 1.96
    halbweite = z * std / math.sqrt(n)
    ci_unten = mean - halbweite
    ci_oben = mean + halbweite

    print("=" * 60)
    print("Statistik für die Pipe-Verweildauer (Einweg)")
    print("=" * 60)
    print(f"Anzahl Messwerte       : {n}")
    print(f"Minimum                : {daten_min:.2f} ns")
    print(f"Maximum                : {daten_max:.2f} ns")
    print(f"Mittelwert             : {mean:.2f} ns")
    print(f"Median                 : {median:.2f} ns")
    print(f"Standardabweichung     : {std:.2f} ns")
    print(f"95. Perzentil          : {p95:.2f} ns")
    print(f"99. Perzentil          : {p99:.2f} ns")
    print(f"95% Konfidenzintervall : [{ci_unten:.2f}, {ci_oben:.2f}] ns")
    print("=" * 60)


def zeichne_histogramm(daten: np.ndarray, dateiname: str) -> None:
    """
    Zeichnet ein Histogramm der Latenzen und speichert es als PNG.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(daten, bins=50, edgecolor='black', linewidth=0.5, alpha=0.7)
    plt.xlabel("Verweildauer in der Pipe (ns)", fontsize=12)
    plt.ylabel("Häufigkeit", fontsize=12)
    plt.title("Histogramm der Pipe-Verweildauer (Einweg)", fontsize=14, fontweight='bold')
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_histogramm_log(daten: np.ndarray, dateiname: str) -> None:
    """
    Histogramm mit logarithmischer y-Achse, um Ausreißer besser zu sehen.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(daten, bins=50, edgecolor='black', linewidth=0.5, alpha=0.7)
    plt.yscale("log")
    plt.xlabel("Verweildauer in der Pipe (ns)", fontsize=12)
    plt.ylabel("Häufigkeit (log-Skala)", fontsize=12)
    plt.title("Histogramm (log-Skala) der Pipe-Verweildauer (Einweg)", fontsize=14, fontweight='bold')
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_boxplot(daten: np.ndarray, dateiname: str) -> None:
    """
    Zeichnet einen Boxplot zur Verteilung der Latenzen.
    """
    plt.figure(figsize=(8, 6))
    bp = plt.boxplot(daten, vert=True, showfliers=True, patch_artist=True)

    # Boxplot einfärben
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')

    plt.ylabel("Verweildauer in der Pipe (ns)", fontsize=12)
    plt.title("Boxplot der Pipe-Verweildauer (Einweg)", fontsize=14, fontweight='bold')
    plt.grid(True, axis='y', linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_zeitreihe(daten: np.ndarray, dateiname: str) -> None:
    """
    Zeigt Latenz über Zeit - deckt Trends/Scheduler-Effekte auf.
    """
    plt.figure(figsize=(12, 5))
    plt.plot(daten, linewidth=0.5, alpha=0.7, color='steelblue')
    plt.xlabel("Messung Nr.", fontsize=12)
    plt.ylabel("Verweildauer (ns)", fontsize=12)
    plt.title("Pipe-Latenz über Zeit", fontsize=14, fontweight='bold')
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_zeitreihe_rolling_mean(daten: np.ndarray, fenster: int, dateiname: str) -> None:
    """
    Zeichnet gleitenden Mittelwert der Latenz über die Zeit.
    Hilfreich, um langfristige Trends und Laständerungen zu erkennen.
    """
    plt.figure(figsize=(12, 5))
    plt.plot(daten, linewidth=0.3, alpha=0.3, label="Einzelmessungen")

    # Gleitender Mittelwert
    if fenster > 1:
        roll = pd.Series(daten).rolling(window=fenster).mean()
        plt.plot(roll, linewidth=1.0, color="red", label=f"Gleitender Mittelwert (Fenster={fenster})")

    plt.xlabel("Messung Nr.", fontsize=12)
    plt.ylabel("Verweildauer (ns)", fontsize=12)
    plt.title("Pipe-Latenz – gleitender Mittelwert", fontsize=14, fontweight='bold')
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_cdf(daten: np.ndarray, dateiname: str) -> None:
    """
    Zeichnet die empirische Verteilungsfunktion (CDF) der Latenz.
    Zeigt, wie schnell die Verteilung ansteigt und wie viele Werte
    unterhalb eines bestimmten Schwellenwerts liegen.
    """
    sortiert = np.sort(daten)
    n = len(sortiert)
    y = np.arange(1, n + 1) / n  # Werte von (1/n) bis 1

    plt.figure(figsize=(10, 6))
    plt.plot(sortiert, y, linewidth=1.0)
    plt.xlabel("Verweildauer in der Pipe (ns)", fontsize=12)
    plt.ylabel("Kumulative Wahrscheinlichkeit", fontsize=12)
    plt.title("Empirische Verteilungsfunktion (CDF) der Pipe-Verweildauer", fontsize=14, fontweight='bold')
    plt.grid(True, linewidth=0.3, alpha=0.5)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")

def zeichne_scatter(daten, dateiname):
    """
    Scatterplot: Messwert gegen Messindex.
    Zeigt direkt die Ausreißer-Positionen (Scheduler-Interferenzen).
    """
    plt.figure(figsize=(12, 5))
    plt.scatter(range(len(daten)), daten, s=2, alpha=0.6)
    plt.xlabel("Messung Nr.")
    plt.ylabel("Verweildauer (ns)")
    plt.title("Pipe-Verweildauer – Scatterplot (Timing-Jitter sichtbar)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")


def zeichne_autokorrelation(daten, dateiname, max_lag=200):
    """
    Autokorrelation: Wie stark hängen Messwerte zeitlich zusammen?
    Erkennt Scheduling-Cluster oder Lastphasen.
    """
    daten_norm = (daten - np.mean(daten)) / np.std(daten)
    autocorr = [np.correlate(daten_norm[:-lag], daten_norm[lag:])[0] 
                for lag in range(1, max_lag)]

    plt.figure(figsize=(10, 6))
    plt.stem(range(1, max_lag), autocorr, use_line_collection=True)
    plt.xlabel("Lag (Versatz)")
    plt.ylabel("Autokorrelation")
    plt.title("Autokorrelation der Pipe-Verweildauer")
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.close()
    print(f"  ✓ {dateiname}")



def main():
    if len(sys.argv) < 2:
        print("Verwendung: python3 messwerte_analyse.py results/pipe_latenz.csv")
        sys.exit(1)

    pfad = sys.argv[1]
    daten = lade_csv(pfad)

    if len(daten) == 0:
        print("Keine gültigen Messwerte gefunden.")
        sys.exit(1)

    # 1. Statistik auf der Konsole ausgeben
    berechne_statistik(daten)
    print()

    # 2. Plots erzeugen
    print("Erzeuge Grafiken...")
    zeichne_histogramm(daten, "results/pipe_latenz_histogramm.png")
    zeichne_histogramm_log(daten, "results/pipe_latenz_histogramm_log.png")
    zeichne_boxplot(daten, "results/pipe_latenz_boxplot.png")
    zeichne_zeitreihe(daten, "results/pipe_latenz_zeitreihe.png")
    zeichne_zeitreihe_rolling_mean(daten, fenster=1000, dateiname="results/pipe_latenz_rolling_mean.png")
    zeichne_cdf(daten, "results/pipe_latenz_cdf.png")
    zeichne_scatter(daten, "results/pipe_latenz_scatter.png")
    zeichne_autokorrelation(daten, "results/pipe_latenz_autocorr.png")


    print("\n✅ Analyse abgeschlossen!")


if __name__ == "__main__":
    main()
