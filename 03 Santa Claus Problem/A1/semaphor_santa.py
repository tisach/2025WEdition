import threading
import time
import random

# --- Konfiguration ---
ANZ_RENTIERE = 9      # r = Gesamtanzahl Rentiere
ANZ_ELFEN = 10        # e = Gesamtanzahl Elfen
ELFEN_GRUPPE = 3      # p = Mindestanzahl für Hilfe

# --- Globale Counter ---
elfen_counter = 0
rentier_counter = 0

# --- Semaphoren zur Synchronisation  ---
# Mutex für den Zugriff auf die Zähler
elf_tex = threading.Semaphore(1)
rentier_tex = threading.Semaphore(1)

# Signale für den Weihnachtsmann
santa_sem = threading.Semaphore(0)

# Warteschlangen für Elfen und Rentiere
elf_wait = threading.Semaphore(0)
rentier_wait = threading.Semaphore(0)

# Mutex, um sicherzustellen, dass immer nur eine Gruppe Elfen hilft und keine neuen Elfen dazwischenfunken, während Santa hilft.
elf_mutex = threading.Semaphore(1) 

def weihnachtsmann():
    global rentier_counter, elfen_counter
    print("[Santa] Der Weihnachtsmann schläft und wartet auf Arbeit...")
    
    while True:
        # Santa wartet, bis er geweckt wird (Signal von Elfen oder Rentieren)
        santa_sem.acquire()
        
        # Kritischen Bereich für Rentiere prüfen
        rentier_tex.acquire()
        if rentier_counter >= ANZ_RENTIERE:
            # Fall 1: Rentiere sind bereit
            print(f"[Santa] Alle {ANZ_RENTIERE} Rentiere sind da! Zeit für Geschenke!")
            
            # Rentiere aufwecken
            for _ in range(ANZ_RENTIERE):
                rentier_wait.release()
            
            rentier_counter = 0 # Reset für nächstes Jahr
            rentier_tex.release()
            
            # Simulation der Auslieferung
            time.sleep(2) 
            print("[Santa] Auslieferung beendet. Rentiere machen Urlaub.")
            
        else:
            # Fall 2: Elfen brauchen Hilfe
            rentier_tex.release() # Rentier-Lock freigeben, da Rentiere nicht dran sind
            
            print(f"[Santa] Helfe den {ELFEN_GRUPPE} wartenden Elfen beim Spielzeugbau.")
            
            # Elfen aufwecken
            for _ in range(ELFEN_GRUPPE):
                elf_wait.release()
            
            # Simulation der Hilfe
            time.sleep(1)
            print("[Santa] Elfen-Probleme gelöst. Gehe wieder schlafen.")

def elf(id):
    global elfen_counter
    while True:
        # Elfen arbeiten
        time.sleep(random.uniform(1, 5))
        
        # Elf hat ein Problem. Versucht Zugang zur Gruppe zu bekommen.
        elf_mutex.acquire()
        elf_tex.acquire()
        elfen_counter += 1
        print(f"[Elf {id}] Hat ein Problem. Wartende Elfen: {elfen_counter}")
        
        if elfen_counter == ELFEN_GRUPPE:
            print(f"[Elf {id}] Wir sind genug ({ELFEN_GRUPPE}). Wecke Weihnachtsmann!")
            elf_tex.release() # Mutex freigeben
            santa_sem.release() # Santa wecken
        else:
            elf_tex.release() # Mutex freigeben
            elf_mutex.release() # Nächsten Elf erlauben, sich anzustellen
            
        # Warten auf Hilfe vom Weihnachtsmann
        elf_wait.acquire()
        
        print(f"[Elf {id}] Wird vom Weihnachtsmann beraten.")
        
        #Gruppe verkleinern
        elf_tex.acquire()
        elfen_counter -= 1
        if elfen_counter == 0:
            print(f"[Elf {id}] Letzter Elf der Gruppe fertig. Mache Platz für neue.")
            elf_tex.release()
            elf_mutex.release() # Gruppe ist fertig, erst jetzt darf eine neue Gruppe entstehen
        else:
            elf_tex.release()

def rentier(id):
    global rentier_counter
    while True:
        # Rentiere sind im Urlaub
        time.sleep(random.uniform(5, 10))
        
        # Rückkehr zum Nordpol
        rentier_tex.acquire()
        rentier_counter += 1
        print(f"[Rentier {id}] Zurück am Nordpol. Rentiere da: {rentier_counter}")
        
        if rentier_counter == ANZ_RENTIERE:
            print(f"[Rentier {id}] Letztes Rentier! Wecke Weihnachtsmann.")
            santa_sem.release()
        
        rentier_tex.release()
        
        # Warten auf das Anspannen (Weihnachtsmann gibt Signal)
        rentier_wait.acquire()
        print(f"[Rentier {id}] Angespannt und bereit zum Abflug!")
        # Warten bis Schlittenfahrt vorbei

# --- Main: Starten der Threads ---
if __name__ == "__main__":
    threads = []
    
    # Santa als Daemon
    t_santa = threading.Thread(target=weihnachtsmann, daemon=True)
    t_santa.start()
    threads.append(t_santa)
    
    # Elfen als Daemons
    for i in range(ANZ_ELFEN):
        t = threading.Thread(target=elf, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        
    # Rentiere als Daemons
    for i in range(ANZ_RENTIERE):
        t = threading.Thread(target=rentier, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        
    # WICHTIG: Das Hauptprogramm muss nun am Leben bleiben, damit die Daemons laufen.
    # Wir fangen hier Strg+C ab.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSimulation abgebrochen (Strg+C). Programm beendet.")