# Santa Claus Problem - Übungsblatt 2

Dieses Repository enthält die Lösungen für das Santa Claus Synchronisationsproblem.

## Projektstruktur

### Aufgabe 1: Semaphor-basierte Lösung (Lokal)
* `semaphor_rentier.py`

### Aufgabe 2: Verteilte Lösung (Docker & ZeroMQ)
Der Code ist hier auf mehrere Dateien aufgeteilt:
* `santa.py` (Server/Router)
* `rentier.py` (Client)
* `elf.py` (Client)
* `Dockerfile` (Bauplan für die Container)
* `docker-compose.yml` (Orchestrierung)


## 🚀 Starten der Anwendung

### Zu Aufgabe 2 (Docker)
Startet die Container-Umgebung (1 Santa, 9 Rentiere, 10 Elfen):

```bash
docker compose up --build --scale rentier=9 --scale elf=10