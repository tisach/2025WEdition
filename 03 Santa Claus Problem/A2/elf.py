import zmq
import time
import random
import os

def main():
    id = os.environ.get("HOSTNAME", "Elf")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://santa:5555")

    while True:
        # Arbeiten simulieren
        work_time = random.uniform(1, 5)
        time.sleep(work_time)

        print(f"[{id}] Habe ein Problem. Warte auf Gruppe...")
        socket.send_string("ELF_HILFE")

        # Warten auf Antwort (blockiert, bis Santa die 3er Gruppe reinlässt)
        msg = socket.recv()
        print(f"[{id}] Santa sagt: {msg.decode()}. Danke!")

if __name__ == "__main__":
    main()