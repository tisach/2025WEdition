````markdown
# Pipe Kommunikation – Latenzmessung

Dieses Programm misst die Nachrichtenlatenz (Verweildauer) einer Nachricht in einer Pipe zwischen zwei Prozessen unter Linux.  
Ein Parent-Prozess sendet ein Byte an den Child-Prozess, dieser sendet es zurück. Die Round-Trip-Zeit wird gemessen und halbiert, um die Einweg-Latenz zu bestimmen.

---

## Kompilieren

```bash
cd "02 Pipe Kommunikation"
make
````

Dies erzeugt das Programm `Pipe_latenz`.

---

## Ausführen der Messung

```bash
./Pipe_latenz 100000 > pipe_latenz.csv
```

* Der Parameter `100000` bestimmt die Anzahl der Messdurchläufe und kann beliebig angepasst werden
* Die Messergebnisse werden in die Datei **pipe_latenz.csv** geschrieben

---

## Analyse der Messwerte

Zur statistischen Auswertung und Visualisierung:

```bash
python3 messwerte_analyse.py results/pipe_latenz.csv
```

Dabei entstehen:

* `pipe_latenz_histogramm.png` (Histogramm)
* `pipe_latenz_boxplot.png` (Boxplot)

Zusätzlich werden statistische Kennzahlen im Terminal ausgegeben (Mittelwert, Min/Max, Standardabweichung, Konfidenzintervall).

---