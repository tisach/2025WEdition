#!/usr/bin/env python3
"""
Ablauf:
  1. Ein Writer-Prozess schreibt langsam 10 nummerierte Blöcke in eine Datei
  2. Während des Schreibens wird ein Snapshot erstellt
  3. Die Datei im Snapshot wird mit der fertigen Datei verglichen
  → Die Snapshot-Datei ist unvollständig (inkonsistent)

Zusätzlich wird gezeigt, wie man mit fsfreeze das Problem beheben kann.

Voraussetzungen:
  - ZFS-Pool "mypool" mit Dataset "mypool/daten" muss existieren
  - Root-Rechte (sudo)

Verwendung:
  sudo python3 inkonsistenz_experiment.py
"""

import subprocess
import os
import time
import threading
import sys

# Konfiguration
DATASET = "mypool/daten"
MOUNT_POINT = "/mypool/daten"
TEST_FILE = os.path.join(MOUNT_POINT, "inkonsistenz_test.txt")
SNAP_NAME_INCONSISTENT = "inkonsistenz_test"
SNAP_NAME_CONSISTENT = "konsistenz_test"
NUM_BLOCKS = 10
BLOCK_DELAY = 0.5  # Sekunden zwischen den Blöcken


# Hilfsfunktionen
def run_cmd(cmd, check=True):
    """Führt einen Befehl aus und gibt die Ausgabe zurück."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"  FEHLER: {' '.join(cmd)}")
        print(f"  {result.stderr.strip()}")
    return result


def cleanup_snapshot(name):
    """Löscht einen Snapshot falls er existiert."""
    full = f"{DATASET}@{name}"
    run_cmd(["zfs", "destroy", full], check=False)


def create_snapshot(name):
    """Erstellt einen Snapshot."""
    full = f"{DATASET}@{name}"
    run_cmd(["zfs", "snapshot", full])
    return full


def get_snapshot_file(snap_name, file_path):
    # ZFS-Snapshots sind unter .zfs/snapshot/ im Mountpoint erreichbar
    rel_path = os.path.relpath(file_path, MOUNT_POINT)
    return os.path.join(MOUNT_POINT, ".zfs", "snapshot", snap_name, rel_path)


def slow_writer(filepath, num_blocks, delay, start_event, done_event):

    start_event.set()  # Signal: Schreiben hat begonnen
    with open(filepath, "w") as f:
        for i in range(1, num_blocks + 1):
            block = f"Block {i:02d}//{num_blocks:02d}: {'X' * 60}\n"
            f.write(block)
            # WICHTIG: Wir rufen absichtlich KEIN f.flush() oder fsync() auf,
            # um zu zeigen, dass gepufferte Daten im Snapshot fehlen können.
            # Aber selbst mit flush kann der Zustand inkonsistent sein,
            # wenn der Snapshot mitten im Schreibvorgang erstellt wird.
            print(f"  Writer: Block {i}/{num_blocks} geschrieben")
            time.sleep(delay)
        f.flush()
        os.fsync(f.fileno())
    done_event.set()
    print(f"  Writer: Alle {num_blocks} Blöcke fertig geschrieben")


# Experiment 1: Inkonsistenz zeigen
def experiment_inkonsistenz():

    print("=" * 65)
    print("EXPERIMENT 1: Inkonsistenz durch gleichzeitiges Schreiben")
    print("=" * 65)

    # Aufräumen
    cleanup_snapshot(SNAP_NAME_INCONSISTENT)
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

    # Events für Synchronisation
    start_event = threading.Event()
    done_event = threading.Event()

    # Writer-Thread starten (schreibt langsam 10 Blöcke)
    print(f"\n1. Starte Writer-Prozess ({NUM_BLOCKS} Blöcke, {BLOCK_DELAY}s Verzögerung)...")
    writer = threading.Thread(
        target=slow_writer,
        args=(TEST_FILE, NUM_BLOCKS, BLOCK_DELAY, start_event, done_event),
    )
    writer.start()

    # Warten bis der Writer angefangen hat
    start_event.wait()

    # Nach der Hälfte der Blöcke den Snapshot erstellen
    wait_time = BLOCK_DELAY * (NUM_BLOCKS // 2)
    print(f"\n2. Warte {wait_time}s (bis ca. Hälfte geschrieben)...")
    time.sleep(wait_time)

    print("\n3. Erstelle Snapshot WÄHREND des Schreibvorgangs...")
    snap_full = create_snapshot(SNAP_NAME_INCONSISTENT)
    print(f"   Snapshot erstellt: {snap_full}")

    # Warten bis Writer fertig ist
    print("\n4. Warte bis Writer fertig ist...")
    done_event.wait()
    writer.join()

    # Vergleich: Originaldatei vs Snapshot-Datei
    print("\n5. Vergleiche Original mit Snapshot:")
    print("-" * 50)

    # Originaldatei lesen (vollständig)
    with open(TEST_FILE, "r") as f:
        original = f.read()
    original_lines = [l for l in original.strip().split("\n") if l]

    # Snapshot-Datei lesen (möglicherweise unvollständig)
    snap_file = get_snapshot_file(SNAP_NAME_INCONSISTENT, TEST_FILE)

    if not os.path.exists(snap_file):
        print("   Snapshot-Datei existiert NICHT → Datei war noch nicht auf Disk")
        snap_lines = []
    else:
        with open(snap_file, "r") as f:
            snap_content = f.read()
        snap_lines = [l for l in snap_content.strip().split("\n") if l]

    print(f"   Original:  {len(original_lines)} Blöcke (vollständig)")
    print(f"   Snapshot:  {len(snap_lines)} Blöcke", end="")

    if len(snap_lines) < len(original_lines):
        print(f" → INKONSISTENT! Es fehlen {len(original_lines) - len(snap_lines)} Blöcke")
    elif len(snap_lines) == 0:
        print(" → INKONSISTENT! Datei ist leer im Snapshot")
    else:
        print(" → Vollständig (Timing war zu langsam, nochmal versuchen)")

    print(f"\n   Inhalt im Snapshot:")
    if snap_lines:
        for line in snap_lines:
            print(f"   | {line}")
    else:
        print("   | (leer oder nicht vorhanden)")

    print(f"\n   Inhalt im Original:")
    for line in original_lines:
        print(f"   | {line}")

    return len(snap_lines) < len(original_lines) or len(snap_lines) == 0


# Experiment 2: Konsistenz mit fsfreeze / sync
def experiment_konsistenz():

    print("\n")
    print("=" * 65)
    print("EXPERIMENT 2: Konsistenz durch sync/fsfreeze")
    print("=" * 65)

    # Aufräumen
    cleanup_snapshot(SNAP_NAME_CONSISTENT)
    test_file_2 = os.path.join(MOUNT_POINT, "konsistenz_test.txt")
    if os.path.exists(test_file_2):
        os.remove(test_file_2)

    # Datei schreiben MIT fsync nach jedem Block
    print("\n1. Schreibe Datei mit fsync() nach jedem Block...")
    with open(test_file_2, "w") as f:
        for i in range(1, NUM_BLOCKS + 1):
            block = f"Block {i:02d}/{NUM_BLOCKS:02d}: {'Y' * 60}\n"
            f.write(block)
            f.flush()
            os.fsync(f.fileno())
            print(f"  Writer: Block {i}/{NUM_BLOCKS} geschrieben + fsync")

    # sync aufrufen (alle Dateisystem-Puffer auf Disk schreiben)
    print("\n2. Rufe 'sync' auf um alle Puffer zu leeren...")
    run_cmd(["sync"])

    # Jetzt Snapshot erstellen
    print("\n3. Erstelle Snapshot NACH sync...")
    snap_full = create_snapshot(SNAP_NAME_CONSISTENT)
    print(f"   Snapshot erstellt: {snap_full}")

    # Vergleich
    print("\n4. Vergleiche Original mit Snapshot:")
    print("-" * 50)

    with open(test_file_2, "r") as f:
        original = f.read()
    original_lines = [l for l in original.strip().split("\n") if l]

    snap_file = get_snapshot_file(SNAP_NAME_CONSISTENT, test_file_2)
    with open(snap_file, "r") as f:
        snap_content = f.read()
    snap_lines = [l for l in snap_content.strip().split("\n") if l]

    print(f"   Original:  {len(original_lines)} Blöcke")
    print(f"   Snapshot:  {len(snap_lines)} Blöcke", end="")

    if len(snap_lines) == len(original_lines):
        print(" → KONSISTENT! Alle Blöcke vorhanden")
    else:
        print(f" → Noch inkonsistent ({len(snap_lines)} von {len(original_lines)})")

    

# Hauptprogramm
def main():
    if os.geteuid() != 0:
        print("Bitte mit sudo ausführen: sudo python3 inkonsistenz_experiment.py")
        sys.exit(1)

    print("ZFS Inkonsistenz-Experiment")
    print("Betriebssysteme, Übungsblatt 3 – Aufgabe 2\n")

    # Experiment 1: Inkonsistenz zeigen
    inkonsistent = experiment_inkonsistenz()

    # Experiment 2: Lösung zeigen
    experiment_konsistenz()

    # Aufräumen
    print("\nAufräumen...")
    cleanup_snapshot(SNAP_NAME_INCONSISTENT)
    cleanup_snapshot(SNAP_NAME_CONSISTENT)
    for f in [TEST_FILE, os.path.join(MOUNT_POINT, "konsistenz_test.txt")]:
        if os.path.exists(f):
            os.remove(f)

    print("\nExperiment abgeschlossen!")
    if inkonsistent:
        print("→ Inkonsistenz wurde erfolgreich demonstriert.")
    else:
        print("→ Inkonsistenz konnte nicht gezeigt werden (Timing). Nochmal versuchen!")


if __name__ == "__main__":
    main()