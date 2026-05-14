#!/bin/bash

# =====================================================================
# 🍎 LABORATORIO REMOTO TDF - SCRIPT DE ARRANQUE (macOS)
# =====================================================================
# Este script inicia los servicios necesarios para el laboratorio.
# Nota: La configuración inicial de Python y Arduino se encuentra
# detallada en el archivo README.md.
# =====================================================================

echo "---------------------------------------------------"
echo "🚀 INICIANDO SERVIDORES DEL LABORATORIO (macOS)"
echo "---------------------------------------------------"

# Buscamos el puerto físico para inyectarlo al servidor
echo "🔍 Buscando Arduino físico..."
PUERTO=$(python3 -c "import glob; ports=glob.glob('/dev/cu.usbmodem*'); print(ports[0] if ports else '')")

if [ -z "$PUERTO" ]; then
    echo "⚠️  ATENCIÓN: No se detectó Arduino en /dev/cu.usbmodem*"
    echo "El servidor iniciará, pero las funciones de hardware podrían fallar."
else
    echo "✅ Arduino detectado en: $PUERTO"
    export PORT_ARDUINO=$PUERTO
fi

# 3. Inicio del Servidor Flask
echo "🔥 Iniciando Servidor Flask..."
# Se ejecuta en segundo plano para permitir el inicio del túnel
python3 server/server.py &

# 4. Gestión del Túnel (Localtunnel)
echo "🌐 Configurando acceso remoto..."
sleep 2

# Verificamos si existe npx (dependencia del servidor para el acceso externo)
if ! command -v npx &> /dev/null; then
    echo "📥 Instalando dependencia del servidor (Node.js)..."
    brew install node
fi

echo "🔗 Generando URL pública..."
# Iniciamos el túnel de forma persistente
npx -y localtunnel --port 5000 --subdomain lab-untdf-arduino-srt