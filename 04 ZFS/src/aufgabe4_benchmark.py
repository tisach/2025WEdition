#!/usr/bin/env python3
"""

Benchmark-Tests:
  1. Sequentielles Schreiben (große Datei)
  2. Sequentielles Lesen (große Datei)
  3. Zufälliges Schreiben (viele kleine Dateien)
  4. Zufälliges Lesen (viele kleine Dateien)
  5. Metadaten-Performance (Dateien erstellen/löschen)

Voraussetzungen:
  - Freie Platten: /dev/sdb (ZFS), /dev/sdf (ext4)
  - mypool auf /dev/sdb muss existieren (oder wird erstellt)
  - Root-Rechte (sudo)

Verwendung:
  sudo python3 aufgabe4_benchmark.py
"""

import subprocess
import os
import sys
import time
import random
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
# ZFS
ZFS_POOL = "mypool"
ZFS_DATASET = f"{ZFS_POOL}/bench"
ZFS_MOUNT = f"/{ZFS_POOL}/bench"
ZFS_DISK = "/dev/sdb"

# ext4
EXT4_DISK = "/dev/sdf"
EXT4_MOUNT = "/mnt/ext4bench"

# Benchmark-Parameter
SEQ_FILE_SIZE_MB = 256       # Größe der sequentiellen Testdatei
SEQ_BLOCK_SIZE_KB = 64       # Blockgröße für seq. Lesen/Schreiben
RANDOM_FILE_COUNT = 500      # Anzahl kleiner Dateien für Random-Test
RANDOM_FILE_SIZE_KB = 4      # Größe der kleinen Dateien
METADATA_FILE_COUNT = 1000   # Anzahl Dateien für Metadaten-Test
REPEAT_COUNT = 3             # Wiederholungen pro Test


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def run_cmd(cmd, check=True, silent=False):
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0 and not silent:
        print(f"  FEHLER: {' '.join(cmd)}")
        print(f"  {result.stderr.strip()}")
    return result


def drop_caches():
    run_cmd(["sync"])
    with open("/proc/sys/vm/drop_caches", "w") as f:
        f.write("3")
    time.sleep(0.5)


def format_speed(mb_per_sec):
    if mb_per_sec >= 1:
        return f"{mb_per_sec:.1f} MB/s"
    else:
        return f"{mb_per_sec * 1024:.1f} KB/s"


def format_ops(ops_per_sec):
    return f"{ops_per_sec:.0f} ops/s"


def print_header(title):
    print(f"\n{'=' * 65}")
    print(f" {title}")
    print(f"{'=' * 65}")


# Setup: Dateisysteme vorbereiten
def setup_filesystems():
    print_header("Setup: Dateisysteme vorbereiten")

    # ZFS Dataset erstellen
    print("\n  ZFS:")
    result = run_cmd(["zfs", "list", ZFS_DATASET], check=False, silent=True)
    if result.returncode == 0:
        # Altes Dataset löschen und neu erstellen
        run_cmd(["zfs", "destroy", "-r", ZFS_DATASET])
    run_cmd(["zfs", "create", ZFS_DATASET])
    print(f"  Dataset {ZFS_DATASET} erstellt → {ZFS_MOUNT}")

    # ext4 formatieren und mounten
    print("\n  ext4:")
    # Sicherstellen dass nicht gemountet
    run_cmd(["umount", EXT4_MOUNT], check=False, silent=True)
    # Formatieren
    print(f"  Formatiere {EXT4_DISK} als ext4...")
    run_cmd(["mkfs.ext4", "-F", "-q", EXT4_DISK])
    # Mounten
    os.makedirs(EXT4_MOUNT, exist_ok=True)
    run_cmd(["mount", EXT4_DISK, EXT4_MOUNT])
    print(f"  {EXT4_DISK} gemountet auf {EXT4_MOUNT}")

    print("\n  Beide Dateisysteme bereit!")


def cleanup_filesystems():
    print("\nAufräumen...")
    run_cmd(["zfs", "destroy", "-r", ZFS_DATASET], check=False, silent=True)
    run_cmd(["umount", EXT4_MOUNT], check=False, silent=True)


# Benchmark-Tests
def bench_sequential_write(mount_point, file_size_mb, block_size_kb):
    filepath = os.path.join(mount_point, "seq_write_test.bin")
    block_size = block_size_kb * 1024
    total_blocks = (file_size_mb * 1024 * 1024) // block_size
    data = os.urandom(block_size)

    drop_caches()
    start = time.perf_counter()

    with open(filepath, "wb") as f:
        for _ in range(total_blocks):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())

    elapsed = time.perf_counter() - start
    mb_per_sec = file_size_mb / elapsed

    # Aufräumen
    os.remove(filepath)
    return mb_per_sec, elapsed


def bench_sequential_read(mount_point, file_size_mb, block_size_kb):
    filepath = os.path.join(mount_point, "seq_read_test.bin")
    block_size = block_size_kb * 1024
    total_blocks = (file_size_mb * 1024 * 1024) // block_size
    data = os.urandom(block_size)

    # Testdatei erstellen
    with open(filepath, "wb") as f:
        for _ in range(total_blocks):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())

    drop_caches()
    start = time.perf_counter()

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break

    elapsed = time.perf_counter() - start
    mb_per_sec = file_size_mb / elapsed

    os.remove(filepath)
    return mb_per_sec, elapsed


def bench_random_write(mount_point, file_count, file_size_kb):

    test_dir = os.path.join(mount_point, "random_write")
    os.makedirs(test_dir, exist_ok=True)
    data = os.urandom(file_size_kb * 1024)

    drop_caches()
    start = time.perf_counter()

    for i in range(file_count):
        filepath = os.path.join(test_dir, f"file_{i:05d}.bin")
        with open(filepath, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

    elapsed = time.perf_counter() - start
    ops_per_sec = file_count / elapsed

    # Aufräumen
    for f in Path(test_dir).iterdir():
        f.unlink()
    os.rmdir(test_dir)

    return ops_per_sec, elapsed


def bench_random_read(mount_point, file_count, file_size_kb):
 
    test_dir = os.path.join(mount_point, "random_read")
    os.makedirs(test_dir, exist_ok=True)
    data = os.urandom(file_size_kb * 1024)

    # Dateien erstellen
    filepaths = []
    for i in range(file_count):
        filepath = os.path.join(test_dir, f"file_{i:05d}.bin")
        with open(filepath, "wb") as f:
            f.write(data)
        filepaths.append(filepath)

    # Zufällige Reihenfolge
    random.shuffle(filepaths)

    drop_caches()
    start = time.perf_counter()

    for fp in filepaths:
        with open(fp, "rb") as f:
            _ = f.read()

    elapsed = time.perf_counter() - start
    ops_per_sec = file_count / elapsed

    # Aufräumen
    for f in Path(test_dir).iterdir():
        f.unlink()
    os.rmdir(test_dir)

    return ops_per_sec, elapsed


def bench_metadata(mount_point, file_count):

    test_dir = os.path.join(mount_point, "metadata_test")
    os.makedirs(test_dir, exist_ok=True)

    drop_caches()

    # Erstellen
    start_create = time.perf_counter()
    for i in range(file_count):
        filepath = os.path.join(test_dir, f"meta_{i:05d}.txt")
        with open(filepath, "w") as f:
            f.write("")
    run_cmd(["sync"])
    elapsed_create = time.perf_counter() - start_create
    create_ops = file_count / elapsed_create

    # Löschen
    start_delete = time.perf_counter()
    for f in Path(test_dir).iterdir():
        f.unlink()
    run_cmd(["sync"])
    elapsed_delete = time.perf_counter() - start_delete
    delete_ops = file_count / elapsed_delete

    os.rmdir(test_dir)

    return create_ops, delete_ops, elapsed_create, elapsed_delete


# Benchmark-Runner
def run_benchmark(name, bench_func, *args):
    results = []
    for i in range(REPEAT_COUNT):
        result = bench_func(*args)
        results.append(result)
    return results


def average(values):
    return sum(values) / len(values)


# Hauptprogramm
def main():
    if os.geteuid() != 0:
        print("Bitte mit sudo ausführen: sudo python3 aufgabe4_benchmark.py")
        sys.exit(1)

    print_header("ZFS vs ext4 Performance-Benchmark")
    print("Betriebssysteme, Übungsblatt 3 – Aufgabe 4\n")
    print(f"Sequentielle Dateigröße:  {SEQ_FILE_SIZE_MB} MB")
    print(f"Blockgröße:               {SEQ_BLOCK_SIZE_KB} KB")
    print(f"Random-Dateien:           {RANDOM_FILE_COUNT} × {RANDOM_FILE_SIZE_KB} KB")
    print(f"Metadaten-Dateien:        {METADATA_FILE_COUNT}")
    print(f"Wiederholungen:           {REPEAT_COUNT}")

    setup_filesystems()

    results = {
        "zfs": {},
        "ext4": {},
    }

    # Test 1: Sequentielles Schreiben
    print_header("Test 1: Sequentielles Schreiben")

    for fs_name, mount in [("zfs", ZFS_MOUNT), ("ext4", EXT4_MOUNT)]:
        print(f"\n  {fs_name.upper()}:")
        runs = run_benchmark("seq_write", bench_sequential_write, mount, SEQ_FILE_SIZE_MB, SEQ_BLOCK_SIZE_KB)
        speeds = [r[0] for r in runs]
        avg_speed = average(speeds)
        results[fs_name]["seq_write"] = avg_speed
        for i, (speed, elapsed) in enumerate(runs):
            print(f"    Lauf {i+1}: {format_speed(speed)} ({elapsed:.2f}s)")
        print(f"    Durchschnitt: {format_speed(avg_speed)}")

    # Test 2: Sequentielles Lesen
    print_header("Test 2: Sequentielles Lesen")

    for fs_name, mount in [("zfs", ZFS_MOUNT), ("ext4", EXT4_MOUNT)]:
        print(f"\n  {fs_name.upper()}:")
        runs = run_benchmark("seq_read", bench_sequential_read, mount, SEQ_FILE_SIZE_MB, SEQ_BLOCK_SIZE_KB)
        speeds = [r[0] for r in runs]
        avg_speed = average(speeds)
        results[fs_name]["seq_read"] = avg_speed
        for i, (speed, elapsed) in enumerate(runs):
            print(f"    Lauf {i+1}: {format_speed(speed)} ({elapsed:.2f}s)")
        print(f"    Durchschnitt: {format_speed(avg_speed)}")

    # Test 3: Zufälliges Schreiben
    print_header("Test 3: Zufälliges Schreiben (viele kleine Dateien)")

    for fs_name, mount in [("zfs", ZFS_MOUNT), ("ext4", EXT4_MOUNT)]:
        print(f"\n  {fs_name.upper()}:")
        runs = run_benchmark("rand_write", bench_random_write, mount, RANDOM_FILE_COUNT, RANDOM_FILE_SIZE_KB)
        ops = [r[0] for r in runs]
        avg_ops = average(ops)
        results[fs_name]["rand_write"] = avg_ops
        for i, (op, elapsed) in enumerate(runs):
            print(f"    Lauf {i+1}: {format_ops(op)} ({elapsed:.2f}s)")
        print(f"    Durchschnitt: {format_ops(avg_ops)}")

    # Test 4: Zufälliges Lesen
    print_header("Test 4: Zufälliges Lesen (viele kleine Dateien)")

    for fs_name, mount in [("zfs", ZFS_MOUNT), ("ext4", EXT4_MOUNT)]:
        print(f"\n  {fs_name.upper()}:")
        runs = run_benchmark("rand_read", bench_random_read, mount, RANDOM_FILE_COUNT, RANDOM_FILE_SIZE_KB)
        ops = [r[0] for r in runs]
        avg_ops = average(ops)
        results[fs_name]["rand_read"] = avg_ops
        for i, (op, elapsed) in enumerate(runs):
            print(f"    Lauf {i+1}: {format_ops(op)} ({elapsed:.2f}s)")
        print(f"    Durchschnitt: {format_ops(avg_ops)}")

    # Test 5: Metadaten-Performance
    print_header("Test 5: Metadaten-Performance (Dateien erstellen/löschen)")

    for fs_name, mount in [("zfs", ZFS_MOUNT), ("ext4", EXT4_MOUNT)]:
        print(f"\n  {fs_name.upper()}:")
        runs = run_benchmark("metadata", bench_metadata, mount, METADATA_FILE_COUNT)
        create_ops = [r[0] for r in runs]
        delete_ops = [r[1] for r in runs]
        avg_create = average(create_ops)
        avg_delete = average(delete_ops)
        results[fs_name]["meta_create"] = avg_create
        results[fs_name]["meta_delete"] = avg_delete
        for i, (cop, dop, ce, de) in enumerate(runs):
            print(f"    Lauf {i+1}: Erstellen {format_ops(cop)}, Löschen {format_ops(dop)}")
        print(f"    Durchschnitt: Erstellen {format_ops(avg_create)}, Löschen {format_ops(avg_delete)}")

    # Ergebnistabelle
    print_header("ERGEBNISÜBERSICHT: ZFS vs ext4")

    print(f"\n  {'Test':<30} {'ZFS':>15} {'ext4':>15} {'Vergleich':>15}")
    print(f"  {'-'*75}")

    comparisons = [
        ("Seq. Schreiben", "seq_write", "MB/s", True),
        ("Seq. Lesen", "seq_read", "MB/s", True),
        ("Random Schreiben", "rand_write", "ops/s", True),
        ("Random Lesen", "rand_read", "ops/s", True),
        ("Metadaten Erstellen", "meta_create", "ops/s", True),
        ("Metadaten Löschen", "meta_delete", "ops/s", True),
    ]

    for label, key, unit, higher_is_better in comparisons:
        zfs_val = results["zfs"][key]
        ext4_val = results["ext4"][key]

        if unit == "MB/s":
            zfs_str = format_speed(zfs_val)
            ext4_str = format_speed(ext4_val)
        else:
            zfs_str = format_ops(zfs_val)
            ext4_str = format_ops(ext4_val)

        if ext4_val > 0:
            ratio = zfs_val / ext4_val
            if ratio > 1:
                comp = f"ZFS {ratio:.1f}x"
            else:
                comp = f"ext4 {1/ratio:.1f}x"
        else:
            comp = "N/A"

        print(f"  {label:<30} {zfs_str:>15} {ext4_str:>15} {comp:>15}")

    print(f"\n  Hinweis: Tests in VirtualBox mit virtuellen Festplatten.")
    print(f"  Die absoluten Werte sind nicht repräsentativ für echte Hardware,")
    print(f"  aber die relativen Unterschiede zwischen ZFS und ext4 sind aussagekräftig.")

    # Ergebnisse als JSON speichern
    results_file = "/home/mim/benchmark_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Ergebnisse gespeichert in: {results_file}")

    cleanup_filesystems()
    print("\nBenchmark abgeschlossen!")


if __name__ == "__main__":
    main()