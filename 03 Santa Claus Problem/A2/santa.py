import zmq
import time

def main():
    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind("tcp://*:5555")

    print("[Santa] Server gestartet. Warte auf Post...")

    # Warteschlangen (speichern die ID des Absenders)
    waiting_elves = []
    waiting_reindeer = []

    # Konfiguration
    GROUP_ELVES = 3
    TOTAL_REINDEER = 9

    while True:
        # 1. Nachricht empfangen (Multipart: ID, Empty, Message)
        try:
            msg = socket.recv_multipart()
        except KeyboardInterrupt:
            break
            
        sender_id = msg[0]
        content = msg[2].decode('utf-8')

        # 2. Logik verarbeiten
        if content == "RENTIER_DA":
            print(f"[Santa] Rentier angekommen ({len(waiting_reindeer)+1}/{TOTAL_REINDEER})")
            waiting_reindeer.append(sender_id)

        elif content == "ELF_HILFE":
            print(f"[Santa] Elf braucht Hilfe ({len(waiting_elves)+1} wartend)")
            waiting_elves.append(sender_id)

        # 3. Bedingungen prüfen (Priorität: Rentiere!)
        if len(waiting_reindeer) >= TOTAL_REINDEER:
            print(f"[Santa] --- Alle {TOTAL_REINDEER} Rentiere da! ---")
            
            # Allen 9 Rentieren antworten
            for r_id in waiting_reindeer:
                socket.send_multipart([r_id, b"", b"GO_FLY"])
            waiting_reindeer = [] # Liste leeren
            
            # Ausliefern simulieren (Santa blockiert hier)
            time.sleep(2)
            print("[Santa] Auslieferung fertig. Lege mich wieder schlafen.")

        elif len(waiting_elves) >= GROUP_ELVES:
            # Nur helfen, wenn KEINE Rentiere warten (oder Rentiere nicht vollzählig sind)
            
            print(f"[Santa] --- Helfe Gruppe von {GROUP_ELVES} Elfen ---")
            
            # Die ersten 3 Elfen aus der Schlange nehmen
            group = []
            for _ in range(GROUP_ELVES):
                group.append(waiting_elves.pop(0))
            
            # Elfen antworten
            for e_id in group:
                socket.send_multipart([e_id, b"", b"GO_WORK"])
            
            # Helfen simulieren
            time.sleep(1)
            print("[Santa] Hilfe beendet.")

if __name__ == "__main__":
    main()