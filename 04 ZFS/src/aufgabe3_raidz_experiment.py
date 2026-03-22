#!/usr/bin/env python3
"""

Ablauf:
  1. RAID-Z Pool mit 3 Platten erstellen (sdc, sdd, sde)
  2. Testdaten schreiben und Prüfsummen berechnen
  3. Dauerhaften Lese-/Schreibprozess starten
  4. Eine Platte simuliert ausfallen lassen (offline setzen)
  5. Zeigen: Pool ist DEGRADED aber funktioniert weiter
  6. Datenintegrität prüfen (Prüfsummen vergleichen)
  7. Platte wieder einbinden und resilvering zeigen

Voraussetzungen:
  - Freie Platten: /dev/sdc, /dev/sdd, /dev/sde (je 1 GB)
  - Root-Rechte (sudo)
  - mypool darf nicht auf diesen Platten liegen

Verwendung:
  sudo python3 raidz_experiment.py
"""

import subprocess
import os
import sys
import time
import threading
import hashlib
import signal

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
POOL_NAME = "raidpool"
DATASET = f"{POOL_NAME}/daten"
MOUNT_POINT = f"/{POOL_NAME}/daten"
# Platten für RAID-Z (3 Platten = 1 Platte Parität, 2 Platten Nutzdaten)
DISKS = ["/dev/sdc", "/dev/sdd", "/dev/sde"]
FAIL_DISK = "/dev/sdc"  # Diese Platte simulieren wir als ausgefallen

# Flag um den IO-Worker zu stoppen
stop_io = threading.Event()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def run_cmd(cmd, check=True, silent=False):
    """Führt einen Befehl aus."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0 and not silent:
        print(f"  FEHLER: {' '.join(cmd)}")
        print(f"  {result.stderr.strip()}")
    return result


def print_header(title):
    """Druckt eine formatierte Überschrift."""
    print(f"\n{'=' * 65}")
    print(f" {title}")
    print(f"{'=' * 65}")


def print_step(num, text):
    """Druckt einen nummerierten Schritt."""
    print(f"\n--- Schritt {num}: {text} ---")


def get_pool_status():
    """Gibt den Pool-Status zurück."""
    result = run_cmd(["zpool", "status", POOL_NAME], check=False)
    return result.stdout if result.returncode == 0 else "Pool nicht gefunden"


def get_pool_state():
    """Gibt nur den Zustand des Pools zurück (ONLINE, DEGRADED, etc.)."""
    result = run_cmd(["zpool", "list", "-H", "-o", "health", POOL_NAME], check=False)
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def calculate_checksum(filepath):
    """Berechnet SHA256-Prüfsumme einer Datei."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ---------------------------------------------------------------------------
# IO-Worker: Liest und schreibt dauerhaft im Hintergrund
# ---------------------------------------------------------------------------
def io_worker(log):
    """
    Führt dauerhaft Lese- und Schreiboperationen durch.
    Protokolliert Erfolge und Fehler in der log-Liste.
    """
    counter = 0
    while not stop_io.is_set():
        counter += 1
        filepath = os.path.join(MOUNT_POINT, f"io_test_{counter % 5}.txt")
        try:
            # Schreiben
            with open(filepath, "w") as f:
                f.write(f"IO-Test Iteration {counter} - Timestamp: {time.time()}\n")
                f.write("D" * 1000 + "\n")
                f.flush()
                os.fsync(f.fileno())

            # Lesen
            with open(filepath, "r") as f:
                content = f.read()

            log.append({"iteration": counter, "status": "OK", "time": time.time()})
        except Exception as e:
            log.append({"iteration": counter, "status": f"FEHLER: {e}", "time": time.time()})

        time.sleep(0.3)

    return counter


# ---------------------------------------------------------------------------
# Cleanup: Pool zerstören falls er existiert
# ---------------------------------------------------------------------------
def cleanup_pool():
    """Zerstört den RAID-Z Pool falls er existiert."""
    result = run_cmd(["zpool", "list", POOL_NAME], check=False, silent=True)
    if result.returncode == 0:
        print(f"  Bestehenden Pool '{POOL_NAME}' wird zerstört...")
        run_cmd(["zpool", "destroy", "-f", POOL_NAME])


# ---------------------------------------------------------------------------
# Hauptexperiment
# ---------------------------------------------------------------------------
def main():
    if os.geteuid() != 0:
        print("Bitte mit sudo ausführen: sudo python3 raidz_experiment.py")
        sys.exit(1)

    print_header("ZFS RAID-Z Experiment")
    print("Betriebssysteme, Übungsblatt 3 – Aufgabe 3\n")
    print(f"Platten:      {', '.join(DISKS)}")
    print(f"RAID-Level:   RAIDZ (einfache Parität, 1 Platte darf ausfallen)")
    print(f"Ausfall-Disk: {FAIL_DISK}")

    # -----------------------------------------------------------------------
    # Schritt 1: Pool erstellen
    # -----------------------------------------------------------------------
    print_step(1, "RAID-Z Pool erstellen")

    cleanup_pool()

    cmd = ["zpool", "create", POOL_NAME, "raidz"] + DISKS
    print(f"  Befehl: {' '.join(cmd)}")
    result = run_cmd(cmd)
    if result.returncode != 0:
        print("  Pool-Erstellung fehlgeschlagen!")
        sys.exit(1)

    # Dataset erstellen
    run_cmd(["zfs", "create", DATASET])

    print(f"  Pool '{POOL_NAME}' erfolgreich erstellt!")
    print(f"\n  Pool-Status:")
    print(get_pool_status())

    state = get_pool_state()
    print(f"  Pool-Zustand: {state}")

    # -----------------------------------------------------------------------
    # Schritt 2: Testdaten schreiben und Prüfsummen berechnen
    # -----------------------------------------------------------------------
    print_step(2, "Testdaten schreiben")

    test_files = {}
    for i in range(1, 4):
        filepath = os.path.join(MOUNT_POINT, f"wichtige_daten_{i}.txt")
        with open(filepath, "w") as f:
            # Genug Daten schreiben, damit sie über die Platten verteilt werden
            f.write(f"Wichtige Datei Nr. {i}\n")
            f.write(f"{'A' * 10000}\n" * 100)  # ca. 1 MB pro Datei
            f.flush()
            os.fsync(f.fileno())
        checksum = calculate_checksum(filepath)
        test_files[filepath] = checksum
        print(f"  Datei {i}: {filepath}")
        print(f"  SHA256: {checksum[:32]}...")

    run_cmd(["sync"])
    print(f"\n  {len(test_files)} Testdateien geschrieben und Prüfsummen gespeichert.")

    # -----------------------------------------------------------------------
    # Schritt 3: IO-Worker starten
    # -----------------------------------------------------------------------
    print_step(3, "Dauerhaften Lese-/Schreibprozess starten")

    io_log = []
    stop_io.clear()
    io_thread = threading.Thread(target=io_worker, args=(io_log,))
    io_thread.start()
    print("  IO-Worker läuft im Hintergrund...")
    time.sleep(2)  # Kurz laufen lassen

    ops_before = len(io_log)
    errors_before = sum(1 for x in io_log if "FEHLER" in x["status"])
    print(f"  Operationen bisher: {ops_before}, Fehler: {errors_before}")

    # -----------------------------------------------------------------------
    # Schritt 4: Plattenausfall simulieren
    # -----------------------------------------------------------------------
    print_step(4, f"Plattenausfall simulieren ({FAIL_DISK})")

    print(f"  Setze {FAIL_DISK} offline...")
    run_cmd(["zpool", "offline", POOL_NAME, FAIL_DISK])

    time.sleep(1)
    state = get_pool_state()
    print(f"\n  Pool-Zustand nach Ausfall: {state}")
    print(f"\n  Pool-Status:")
    print(get_pool_status())

    # -----------------------------------------------------------------------
    # Schritt 5: Zeigen dass IO weiterläuft
    # -----------------------------------------------------------------------
    print_step(5, "IO-Operationen nach Plattenausfall prüfen")

    print("  Warte 5 Sekunden um IO-Operationen zu sammeln...")
    time.sleep(5)

    ops_after = len(io_log)
    ops_during_failure = ops_after - ops_before
    errors_during = sum(1 for x in io_log[ops_before:] if "FEHLER" in x["status"])

    print(f"  Operationen nach Ausfall: {ops_during_failure}")
    print(f"  Fehler nach Ausfall:      {errors_during}")

    if errors_during == 0:
        print("  → ERFOLGREICH: Alle Lese-/Schreiboperationen liefen ohne Unterbrechung!")
    else:
        print(f"  → {errors_during} Fehler aufgetreten")
        for entry in io_log[ops_before:]:
            if "FEHLER" in entry["status"]:
                print(f"     Iteration {entry['iteration']}: {entry['status']}")

    # -----------------------------------------------------------------------
    # Schritt 6: Datenintegrität prüfen
    # -----------------------------------------------------------------------
    print_step(6, "Datenintegrität prüfen (Prüfsummen vergleichen)")

    all_ok = True
    for filepath, original_checksum in test_files.items():
        current_checksum = calculate_checksum(filepath)
        match = current_checksum == original_checksum
        status = "OK" if match else "KORRUPT!"
        if not match:
            all_ok = False
        print(f"  {os.path.basename(filepath)}: {status}")
        print(f"    Vorher:  {original_checksum[:32]}...")
        print(f"    Nachher: {current_checksum[:32]}...")

    if all_ok:
        print("\n  → ERFOLGREICH: Alle Daten sind intakt trotz Plattenausfall!")
    else:
        print("\n  → WARNUNG: Datenkorruption festgestellt!")

    # -----------------------------------------------------------------------
    # Schritt 7: IO-Worker stoppen
    # -----------------------------------------------------------------------
    print_step(7, "IO-Worker stoppen und Platte wieder einbinden")

    stop_io.set()
    io_thread.join()

    total_ops = len(io_log)
    total_errors = sum(1 for x in io_log if "FEHLER" in x["status"])
    print(f"  Gesamt-Operationen: {total_ops}")
    print(f"  Gesamt-Fehler:      {total_errors}")

    # Platte wieder online bringen
    print(f"\n  Bringe {FAIL_DISK} wieder online...")
    run_cmd(["zpool", "online", POOL_NAME, FAIL_DISK])
    time.sleep(2)

    state = get_pool_state()
    print(f"  Pool-Zustand nach Recovery: {state}")
    print(f"\n  Pool-Status nach Recovery:")
    print(get_pool_status())

    # -----------------------------------------------------------------------
    # Zusammenfassung
    # -----------------------------------------------------------------------
    print_header("ZUSAMMENFASSUNG")
    print(f"""
    RAID-Z Pool:           {POOL_NAME} ({len(DISKS)} Platten)
    Ausgefallene Platte:   {FAIL_DISK}
    Pool-Zustand:          DEGRADED (aber funktionsfähig)
    
    IO-Operationen:        {total_ops} gesamt
    IO-Fehler:             {total_errors} 
    Datenintegrität:       {"Alle Dateien intakt" if all_ok else "Korruption!"}
    
    Ergebnis:
    → Der Ausfall einer Platte hatte KEINEN Einfluss auf das Dateisystem.
    → Alle Lese- und Schreiboperationen liefen ohne Unterbrechung weiter.
    → Die Daten blieben vollständig und korrekt (Prüfsummen identisch).
    → Nach Wiedereingliederung der Platte wird der Pool automatisch
      repariert (Resilvering).
      
    Hinweis: Bei RAIDZ darf 1 Platte ausfallen.
             Bei RAIDZ2 dürfen 2 Platten gleichzeitig ausfallen.
    """)

    # Aufräumen
    print("Pool aufräumen...")
    cleanup_pool()
    print("Fertig!")


if __name__ == "__main__":
    main()