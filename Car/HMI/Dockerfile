# --- Basis-Image ---
FROM python:3.11-slim

# --- Arbeitsverzeichnis im Container ---
WORKDIR /app

# --- Systemabhängigkeiten (optional für einige Python-Pakete) ---
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --- Python-Abhängigkeiten ---
# Kopiere zuerst requirements separat, um Docker-Layer-Caching zu nutzen
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# --- Quellcode kopieren ---
COPY . .

# --- Flask App starten ---
EXPOSE 5001

CMD ["python", "HMI.py"]