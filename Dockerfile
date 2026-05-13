FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Solo instalamos 'curl' porque lo necesitamos para bajar arduino-cli
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Instalar arduino-cli
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Configurar Cores de Arduino
RUN arduino-cli core update-index && \
    arduino-cli core install arduino:avr@1.8.7

# Instalar librerías de hardware
RUN arduino-cli lib install "Adafruit BusIO" && \
    arduino-cli lib install "Adafruit GFX Library" && \
    arduino-cli lib install "Adafruit SSD1306" && \
    arduino-cli lib install "Adafruit Unified Sensor" && \
    arduino-cli lib install "DHT sensor library" && \
    arduino-cli lib install "Servo"

WORKDIR /app

# Instalar Python (Flask)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

EXPOSE 5000

# Iniciamos el servidor directamente con Python
CMD ["python","-u", "server.py"]