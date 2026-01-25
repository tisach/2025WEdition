import zmq
import time
import random
import os

def main():
    id = os.environ.get("HOSTNAME", "Rentier") # Docker Hostname nutzen
    context = zmq.Context()
    # REQ Socket: Blockiert nach send(), bis reply empfangen wird
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://santa:5555")

    while True:
        # Urlaub simulieren
        sleep_time = random.uniform(5, 10)
        time.sleep(sleep_time)

        print(f"[{id}] Zurück aus dem Urlaub. Melde mich bei Santa...")
        socket.send_string("RENTIER_DA")

        # Warten auf Antwort (blockiert, bis Santa "GO_FLY" sendet)
        msg = socket.recv()
        print(f"[{id}] Santa sagt: {msg.decode()}. Fliege los!")
        
        # Schlittenfahrt ist implizit vorbei, wenn der Loop neu startet

if __name__ == "__main__":
    main()