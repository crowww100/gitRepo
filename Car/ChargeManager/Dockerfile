# Basis-Image mit Python
FROM python:3.10-slim

# Optional: Installiere sudo falls benötigt
#RUN apt-get update && \
#    apt-get install -y sudo && \
#    apt-get install -y evcc curl && \
#    apt-get clean

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere alle lokalen Dateien in das Arbeitsverzeichnis des Containers
COPY . .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir requests paho-mqtt

# Deaktiviere Zertifikatprüfung (optional, unsicher!)
ENV PYTHONWARNINGS="ignore:Unverified HTTPS request"

# evcc-Binary ins Image kopieren
#COPY evcc /usr/local/bin/evcc

# ausführbar machen
#RUN chmod +x /usr/local/bin/evcc


# Starte das Python-Programm
CMD ["python", "chargeManager.py"]