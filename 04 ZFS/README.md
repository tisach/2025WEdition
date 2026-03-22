# Betriebssysteme – Übungsblatt 3: ZFS

---

## Überblick

Dieses Repository enthält die Implementierungen und Experimente zu Übungsblatt 3 der Vorlesung Betriebssysteme.

| Aufgabe | Beschreibung | Datei |
|---------|-------------|-------|
| 1 | Datensicherung und -archivierung mit ZFS-Snapshots | `src/aufgabe1_zfs_backup.py` |
| 2 | Datei-Inkonsistenzen trotz ZFS-Snapshots | `src/aufgabe2_inconsistency_experiment.py` |
| 3 | Datensicherheit mit RAID-Z | `src/aufgabe3_raidz_experiment.py` |
| 4 | Zugriffsperformanz ZFS vs. ext4 | `src/aufgabe4_benchmark.py` |

## Voraussetzungen

- Ubuntu Server 24.04 LTS (VirtualBox VM)
- Python 3.10+
- ZFS: `sudo apt install zfsutils-linux`
- Root-Rechte für ZFS-Operationen
- Mindestens 5 zusätzliche virtuelle Festplatten (je 1 GB)

## VM-Einrichtung

ZFS und Python installieren:

```bash
sudo apt update && sudo apt install zfsutils-linux python3 -y
```

ZFS-Pool und Dataset erstellen (für Aufgabe 1 + 2):

```bash
sudo zpool create mypool /dev/sdb
sudo zfs create mypool/daten
```

Testdaten anlegen:

```bash
sudo mkdir -p /mypool/daten/projekt
echo "Hello World" | sudo tee /mypool/daten/projekt/test1.txt
echo "Wichtige Daten" | sudo tee /mypool/daten/projekt/test2.txt
sudo cp -r /etc/apt /mypool/daten/projekt/config_backup
sudo mkdir -p /mnt/backups
```

## Aufgaben ausführen

```bash
# Aufgabe 1: Backup-Programm
sudo python3 src/aufgabe1_zfs_backup.py --source mypool/daten --dest /mnt/backups --max-backups 3

# Aufgabe 2: Inkonsistenz-Experiment
sudo python3 src/aufgabe2_inconsistency_experiment.py

# Aufgabe 3: RAID-Z Experiment (nutzt /dev/sdc, /dev/sdd, /dev/sde)
sudo python3 src/aufgabe3_raidz_experiment.py

# Aufgabe 4: Performance-Benchmark (nutzt /dev/sdb für ZFS, /dev/sdf für ext4)
sudo python3 src/aufgabe4_benchmark.py
```

## Aufgabe 1: Datensicherung

Das Backup-Programm nutzt ZFS-Snapshots (`zfs snapshot -r`) und `zfs send`/`receive` um einen konfigurierbaren Ordner zu sichern. Es unterstützt:

- Vollständige und inkrementelle Backups (`zfs send -i`)
- Konfigurierbare Retention (FIFO-basiert)
- JSON-Konfigurationsdatei oder CLI-Parameter
- Automatische Intervall-Ausführung

```bash
# Mit Konfigurationsdatei
sudo python3 src/aufgabe1_zfs_backup.py --config config/backup_config.json

# Mit Intervall (alle 60 Sekunden)
sudo python3 src/aufgabe1_zfs_backup.py --source mypool/daten --dest /mnt/backups --max-backups 5 --interval 60

# Beispiel-Konfiguration erzeugen
python3 src/aufgabe1_zfs_backup.py --generate-config config/my_config.json
```

## Aufgabe 2: Inkonsistenz-Experiment

Demonstriert, dass Dateien im ZFS-Snapshot inkonsistent sein können, wenn sie während des Snapshots geschrieben werden. Das Skript führt zwei Experimente durch:

1. **Inkonsistenz:** Writer-Thread schreibt ohne `fsync()` → Snapshot ist leer/unvollständig
2. **Konsistenz:** Writer mit `fsync()` + `sync` vor Snapshot → Snapshot ist vollständig

## Aufgabe 3: RAID-Z Experiment

Erstellt einen RAID-Z1-Pool aus 3 Platten, simuliert einen Plattenausfall und zeigt, dass laufende IO-Operationen ohne Unterbrechung weiterarbeiten. Prüft Datenintegrität per SHA256-Prüfsummen.

## Aufgabe 4: Performance-Benchmark

Vergleicht ZFS und ext4 in fünf Testszenarien:

- Sequentielles Lesen/Schreiben (256 MB Datei)
- Zufälliges Lesen/Schreiben (500 × 4 KB Dateien)
- Metadaten-Performance (1000 Dateien erstellen/löschen)

## Projektstruktur

```
.
├── README.md
├── Ergebnisbericht_UB3.pdf
├── config/
│   └── backup_config.json
└── src/
    ├── aufgabe1_backup.py
    ├── aufgabe2_inkonsistenz.py
    ├── aufgabe3_raidz.py
    └── aufgabe4_benchmark.py
```

## Testumgebung

- **Host:** Windows 11 Home + VirtualBox
- **VM:** Ubuntu Server 24.04.4 LTS (Kernel 6.8.0)
- **Hardware:** 4 GB RAM, 2 CPUs, 6 virtuelle Festplatten
- **ZFS:** zfsutils-linux (OpenZFS)