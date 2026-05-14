FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. Instalamos herramientas base (curl para descargar y socat para túneles)
RUN apt-get update && apt-get install -y curl socat && rm -rf /var/lib/apt/lists/*

# 2. Instalamos el compilador arduino-cli
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh

# 3. Instalamos los núcleos (AVR) y las librerías desde el archivo de texto
RUN arduino-cli core update-index && arduino-cli core install arduino:avr@1.8.7
COPY libraries.txt .
RUN xargs -d '\n' arduino-cli lib install < libraries.txt

WORKDIR /app

# 4. Instalamos dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del proyecto
COPY . .

EXPOSE 5000

# Iniciamos el servidor de forma directa
CMD ["python", "-u", "server/server.py"]