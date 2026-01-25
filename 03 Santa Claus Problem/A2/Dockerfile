FROM python:3.9-slim

# ZeroMQ installieren
RUN pip install pyzmq

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Skripte kopieren
COPY santa.py .
COPY rentier.py .
COPY elf.py .

# Standard-Kommando (wird in docker-compose überschrieben)
CMD ["python", "santa.py"]