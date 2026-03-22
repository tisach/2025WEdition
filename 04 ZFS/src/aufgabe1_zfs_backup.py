#!/usr/bin/env python3
"""

Voraussetzungen:
  - Ubuntu Linux mit installiertem ZFS: sudo apt install zfsutils-linux
  - Root-Rechte (sudo) für ZFS-Operationen
  - Ein ZFS-Pool muss bereits existieren (z.B. "mypool")

Verwendung:
  sudo python3 zfs_backup.py                     # Einmaliges Backup
  sudo python3 zfs_backup.py --interval 3600      # Backup jede Stunde
  sudo python3 zfs_backup.py --config backup.json  # Mit Konfigurationsdatei

"""

import subprocess
import sys
import os
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path


# Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("zfs_backup")



# Standardkonfiguration
DEFAULT_CONFIG = {
    "source_dataset": "mypool/daten",      # ZFS-Dataset das gesichert wird
    "backup_location": "/mnt/backups",      # Zielordner für Backup-Dateien
    "max_backups": 5,                       # Maximale Anzahl aufbewahrter Backups
    "interval_seconds": 0,                  # 0 = einmaliger Lauf, >0 = Intervall
    "use_incremental": True,                # Inkrementelle Backups verwenden
}


# Hilfsfunktionen für ZFS-Kommandos

#Führt einen Shell-Befehl aus und gibt das Ergebnis zurück
def run_cmd(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    #Führt einen Shell-Befehl aus und gibt das Ergebnis zurück
    log.debug("Ausführen: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=capture, text=True, check=False)
    if check and result.returncode != 0:
        log.error("Befehl fehlgeschlagen: %s\nStderr: %s", " ".join(cmd), result.stderr.strip())
        raise RuntimeError(f"Befehl fehlgeschlagen: {' '.join(cmd)}")
    return result

#Prüft, ob ein ZFS-Dataset existiert
def dataset_exists(dataset: str) -> bool:
    result = run_cmd(["zfs", "list", "-H", "-o", "name", dataset], check=False)
    return result.returncode == 0


def create_snapshot(dataset: str, snap_name: str) -> str:
    full_name = f"{dataset}@{snap_name}"
    log.info("Erstelle Snapshot: %s", full_name)
    run_cmd(["zfs", "snapshot", "-r", full_name])
    return full_name


def list_snapshots(dataset: str, prefix: str = "backup_") -> list[str]:
    result = run_cmd(
        ["zfs", "list", "-H", "-o", "name", "-t", "snapshot", "-s", "creation", dataset],
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []

    snapshots = []
    for line in result.stdout.strip().splitlines():
        # Format: dataset@snap_name
        if "@" in line:
            snap_part = line.split("@", 1)[1]
            if snap_part.startswith(prefix):
                snapshots.append(line)
    return snapshots


def send_snapshot_to_file(snapshot: str, dest_file: Path, base_snapshot: str | None = None):
    """
    Sendet einen ZFS-Snapshot als Datei an den Zielort

    Verwendet 'zfs send' mit optionalem inkrementellen Modus:
      - Vollbackup:        zfs send snapshot > datei
      - Inkrementell:      zfs send -i base_snapshot snapshot > datei

    Args:
        snapshot:      Vollständiger Snapshot-Name (z.B. mypool/daten@backup_20250101)
        dest_file:     Ziel-Dateipfad
        base_snapshot: Vorheriger Snapshot für inkrementelles Backup (optional)
    """
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["zfs", "send"]
    if base_snapshot:
        log.info("Inkrementelles Backup: %s -> %s", base_snapshot, snapshot)
        cmd.extend(["-i", base_snapshot])
    else:
        log.info("Vollbackup: %s", snapshot)

    cmd.append(snapshot)

    log.info("Schreibe Backup nach: %s", dest_file)
    with open(dest_file, "wb") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=False, check=False)
    if proc.returncode != 0:
        log.error("zfs send fehlgeschlagen: %s", proc.stderr.decode().strip())
        # Unvollständige Datei entfernen
        dest_file.unlink(missing_ok=True)
        raise RuntimeError("zfs send fehlgeschlagen")

    size_mb = dest_file.stat().st_size / (1024 * 1024)
    log.info("Backup geschrieben: %.2f MB", size_mb)


def destroy_snapshot(snapshot: str):
    log.info("Lösche Snapshot: %s", snapshot)
    run_cmd(["zfs", "destroy", snapshot])



# Retention: Überzählige Backups entfernen
def apply_retention(dataset: str, backup_dir: Path, max_backups: int):

    snapshots = list_snapshots(dataset)
    backup_files = sorted(backup_dir.glob("backup_*.zfs"))

    # Snapshots bereinigen
    while len(snapshots) > max_backups:
        oldest = snapshots.pop(0)
        log.info("Retention: Lösche ältesten Snapshot %s", oldest)
        try:
            destroy_snapshot(oldest)
        except RuntimeError:
            log.warning("Konnte Snapshot %s nicht löschen", oldest)

    # Backup-Dateien bereinigen
    while len(backup_files) > max_backups:
        oldest_file = backup_files.pop(0)
        log.info("Retention: Lösche älteste Backup-Datei %s", oldest_file)
        oldest_file.unlink(missing_ok=True)


# Backup durchführen
def perform_backup(config: dict):

    dataset = config["source_dataset"]
    backup_dir = Path(config["backup_location"])
    max_backups = config["max_backups"]
    use_incremental = config.get("use_incremental", True)

    # Prüfen, ob Dataset existiert
    if not dataset_exists(dataset):
        log.error("Dataset '%s' existiert nicht!", dataset)
        log.info("Erstellen Sie es z.B. mit: sudo zfs create %s", dataset)
        sys.exit(1)

    # Zielordner erstellen
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Zeitstempel für den Snapshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_name = f"backup_{timestamp}"

    # 1. Snapshot erstellen
    full_snapshot = create_snapshot(dataset, snap_name)

    # 2. Vorherige Snapshots ermitteln (für inkrementelles Backup)
    existing_snapshots = list_snapshots(dataset)
    base_snapshot = None
    if use_incremental and len(existing_snapshots) >= 2:
        # Der vorletzte Snapshot ist die Basis (der letzte ist der gerade erstellte)
        base_snapshot = existing_snapshots[-2]

    # 3. Backup-Datei erstellen
    if base_snapshot:
        dest_file = backup_dir / f"{snap_name}_incr.zfs"
    else:
        dest_file = backup_dir / f"{snap_name}_full.zfs"

    try:
        send_snapshot_to_file(full_snapshot, dest_file, base_snapshot)
    except RuntimeError:
        log.error("Backup fehlgeschlagen – Snapshot wird beibehalten für nächsten Versuch")
        return False

    # 4. Retention anwenden
    apply_retention(dataset, backup_dir, max_backups)

    log.info("=== Backup erfolgreich abgeschlossen ===")
    return True


# Konfiguration laden
def load_config(config_path: str | None) -> dict:
    """Lädt Konfiguration aus JSON-Datei oder verwendet Standardwerte."""
    config = DEFAULT_CONFIG.copy()

    if config_path and Path(config_path).exists():
        log.info("Lade Konfiguration aus: %s", config_path)
        with open(config_path, "r") as f:
            user_config = json.load(f)
        config.update(user_config)
    elif config_path:
        log.warning("Konfigurationsdatei '%s' nicht gefunden – verwende Standardwerte", config_path)

    return config


# Beispiel-Konfigurationsdatei erzeugen
def generate_example_config(path: str):
    """Erzeugt eine Beispiel-Konfigurationsdatei."""
    with open(path, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    log.info("Beispiel-Konfiguration geschrieben nach: %s", path)


# CLI
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ZFS Backup & Archivierung – Betriebssysteme Übungsblatt 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Beispiele:
  sudo python3 zfs_backup.py                          # Einmaliges Backup
  sudo python3 zfs_backup.py --interval 3600           # Jede Stunde
  sudo python3 zfs_backup.py --config backup.json      # Mit Konfiguration
  sudo python3 zfs_backup.py --generate-config cfg.json # Beispiel-Config erzeugen

Setup (einmalig):
  sudo zpool create mypool /dev/sdX
  sudo zfs create mypool/daten
  # Daten nach /mypool/daten kopieren
        """,
    )
    parser.add_argument(
        "--config", "-c", type=str, default=None,
        help="Pfad zur JSON-Konfigurationsdatei",
    )
    parser.add_argument(
        "--source", "-s", type=str, default=None,
        help="Quell-Dataset (überschreibt Konfiguration)",
    )
    parser.add_argument(
        "--dest", "-d", type=str, default=None,
        help="Zielordner für Backups (überschreibt Konfiguration)",
    )
    parser.add_argument(
        "--max-backups", "-m", type=int, default=None,
        help="Maximale Anzahl aufbewahrter Backups",
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=None,
        help="Intervall in Sekunden (0 = einmalig)",
    )
    parser.add_argument(
        "--no-incremental", action="store_true",
        help="Immer Vollbackups erstellen (kein inkrementelles Backup)",
    )
    parser.add_argument(
        "--generate-config", type=str, default=None,
        metavar="PATH",
        help="Erzeugt eine Beispiel-Konfigurationsdatei und beendet sich",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Ausführliche Ausgabe",
    )
    return parser.parse_args()


# Hauptprogramm
def main():
    args = parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Beispiel-Config erzeugen
    if args.generate_config:
        generate_example_config(args.generate_config)
        return

    # Root-Rechte prüfen
    if os.geteuid() != 0:
        log.error("Dieses Programm benötigt Root-Rechte. Bitte mit 'sudo' ausführen.")
        sys.exit(1)

    # Konfiguration laden und CLI-Argumente anwenden
    config = load_config(args.config)

    if args.source:
        config["source_dataset"] = args.source
    if args.dest:
        config["backup_location"] = args.dest
    if args.max_backups is not None:
        config["max_backups"] = args.max_backups
    if args.interval is not None:
        config["interval_seconds"] = args.interval
    if args.no_incremental:
        config["use_incremental"] = False

    log.info("=== ZFS Backup-Programm gestartet ===")
    log.info("Quell-Dataset:   %s", config["source_dataset"])
    log.info("Backup-Ziel:     %s", config["backup_location"])
    log.info("Max. Backups:    %d", config["max_backups"])
    log.info("Inkrementell:    %s", config["use_incremental"])

    interval = config["interval_seconds"]

    if interval > 0:
        log.info("Intervall-Modus: alle %d Sekunden", interval)
        try:
            while True:
                perform_backup(config)
                log.info("Nächstes Backup in %d Sekunden...", interval)
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("\nProgramm durch Benutzer beendet.")
    else:
        log.info("Einmaliger Backup-Lauf")
        success = perform_backup(config)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
