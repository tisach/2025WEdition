```markdown
# 02 – Pipe Kommunikation – Messung der Verweildauer im Kernel

Dieses Projekt untersucht die Latenz der Interprozesskommunikation über Pipes unter Linux. 
Dabei wird ein Parent- und ein Child-Prozess per `fork()` erzeugt und eine Nachricht 
per Ping-Pong über zwei Pipes übertragen. Die Round-Trip-Zeit wird gemessen und 
halbiert, um die Einweg-Verweildauer einer Nachricht im Kernel zu bestimmen.

```

## Ordnerstruktur

```

2025WEdition/
├── 02 Pipe Kommunikation/
│    ├── Pipe_latenz.cpp        # Messprogramm (C++)
│    ├── messwerte_analyse.py   # Analyse & Plotgenerierung (Python)
│    ├── Makefile               # Build-Skript
│    └── results/               # erzeugte CSV + Grafiken

````

Die Dateien im Ordner `results/` werden automatisch erzeugt und analysiert.

## Kompilieren

Im Ordner **02 Pipe Kommunikation**:

```bash
make
```

Das erzeugt ein ausführbares Programm:

```
Pipe_latenz
```

---

## Messung ausführen

```bash
./Pipe_latenz 100000
```

-Parameter = Anzahl der Messwerte
-Ergebnisse werden abgespeichert in:

```
results/pipe_latenz.csv
```

---

## Analyse durchführen

```bash
python3 messwerte_analyse.py results/pipe_latenz.csv
```

Dabei entstehen u. a.:

| Datei                            | Inhalt                                 |
| -------------------------------- | -------------------------------------- |
| `pipe_latenz_histogramm.png`     | Verteilungsanalyse                     |
| `pipe_latenz_histogramm_log.png` | Darstellung seltener Ausreißer         |
| `pipe_latenz_boxplot.png`        | Ausreißeranalyse                       |
| `pipe_latenz_cdf.png`            | Zuverlässigkeitsbewertung              |
| `pipe_latenz_zeitreihe.png`      | Verlauf über die Zeit                  |
| `pipe_latenz_scatter.png`        | Timing-Jitter                          |
| `pipe_latenz_rolling_mean.png`   | Systemtrends                           |
| `pipe_latenz_autocorr.png`       | Clusterbildung / temporale Korrelation |

Zusätzlich werden statistische Kennzahlen in der Konsole ausgegeben:

* Mittelwert
* Minimum / Maximum
* Standardabweichung
* 95 %-Konfidenzintervall
* Perzentile
