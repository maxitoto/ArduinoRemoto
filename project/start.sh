#!/bin/bash

# =====================================================================
# 🍎 NATIVE MODE - AUTO-INSTALLER & START (macOS ONLY)
# =====================================================================
# Este script automatiza la instalación de arduino-cli, librerías
# de hardware y dependencias de Python directamente en tu macOS.
# =====================================================================

echo "---------------------------------------------------"
echo "🍎 INICIANDO CONFIGURACIÓN NATIVA (macOS)"
echo "---------------------------------------------------"

# 1. Verificar/Instalar Homebrew (Gestor de paquetes de Mac)
if ! command -v brew &> /dev/null; then
    echo "🍺 Homebrew no detectado. Instalándolo ahora..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Instalar herramientas de sistema (Equivalente al apt-get del Docker)
echo "🛠️  Verificando herramientas de sistema (socat)..."
if ! command -v socat &> /dev/null; then
    brew install socat
fi

# 3. Instalar arduino-cli (Equivalente a la línea 8 del Dockerfile)
echo "🤖 Verificando arduino-cli..."
if ! command -v arduino-cli &> /dev/null; then
    echo "📥 Instalando arduino-cli vía Homebrew..."
    brew install arduino-cli
fi

echo "⚙️  Sincronizando núcleos de Arduino..."
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.7

echo "📚 Instalando librerías desde libraries.txt..."
if [ -f "libraries.txt" ]; then
    # Leemos el archivo y quitamos posibles espacios en blanco o saltos de línea raros
    while IFS= read -r linea || [ -n "$linea" ]; do
        # Evitamos líneas vacías
        if [ ! -z "$linea" ]; then
            echo "Installing: $linea"
            arduino-cli lib install "$linea"
        fi
    done < libraries.txt
else
    echo "⚠️  Archivo libraries.txt no encontrado. Saltando paso."
fi 

# 5. Configurar Python y Flask
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual .venv..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "🐍 Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Detección de Hardware y Arranque
echo "🔍 Buscando Arduino físico..."
PUERTO=$(python3 -c "import glob; ports=glob.glob('/dev/cu.usbmodem*'); print(ports[0] if ports else '')")

if [ -z "$PUERTO" ]; then
    echo "⚠️  ATENCIÓN: No se detectó Arduino. Por favor conéctalo."
else
    echo "✅ Arduino detectado en: $PUERTO"
    export PORT_ARDUINO=$PUERTO
fi

echo "🚀 Iniciando Servidor Flask..."
# Se ejecuta en background (&) para liberar la terminal
python3 server/server.py & 

echo "🔗 Iniciando túnel público..."
sleep 2
# Verificamos si existe npx (viene con Node.js)
if command -v npx &> /dev/null; then
    npx localtunnel --port 5000 --subdomain lab-tdf
else
    echo "❌ Error: Node.js/npm no instalado. No se pudo iniciar localtunnel."
fi