#!/bin/bash

echo "---------------------------------------------------"
echo "🛠️  INICIANDO LABORATORIO REMOTO TDF  🛠️"
echo "---------------------------------------------------"

echo "🔍 1. Detectando el Sistema Operativo Anfitrión..."
OS_NAME=$(uname -s)
SERVICIO_DOCKER=""

# Evaluamos qué sistema operativo está corriendo el script
if [[ "$OS_NAME" == "Darwin" ]]; then
    echo "🍎 Sistema detectado: macOS"
    SERVICIO_DOCKER="lab-mac"

elif [[ "$OS_NAME" == "Linux" ]]; then
    # Un pequeño truco: Windows con WSL2 se hace pasar por Linux. 
    # Leemos el archivo version para ver si dice "Microsoft" o "WSL".
    if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
        echo "🪟 Sistema detectado: Windows (WSL2)"
        SERVICIO_DOCKER="lab-windows"
    else
        echo "🐧 Sistema detectado: Linux nativo"
        SERVICIO_DOCKER="lab-linux"
    fi
else
    echo "⚠️ Sistema Operativo no reconocido ($OS_NAME). Usando Linux por defecto."
    SERVICIO_DOCKER="lab-linux"
fi

echo "🔍 2. Buscando Arduino físico conectado..."
# Buscamos en las rutas típicas de Mac y Linux/Windows
PUERTO_DETECTADO=$(ls /dev/cu.usbmodem* /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -n 1)

if [ -z "$PUERTO_DETECTADO" ]; then
    echo "❌ Error: No se encontró ningún hardware conectado."
    echo "Por favor, enchufá la placa USB y volvé a ejecutar el script."
    exit 1
fi

echo "✅ Arduino detectado en el puerto: $PUERTO_DETECTADO"

echo "🔗 Abriendo túnel SOCAT en la Mac (Puerto TCP 3333)..."
# Matamos cualquier túnel viejo que haya quedado abierto
killall socat 2>/dev/null

# La Mac agarra el cable físico y lo sirve crudo por el puerto TCP 3333 en segundo plano (&)
socat file:$PUERTO_DETECTADO,rawer tcp:127.0.0.1:3333,retry=15,interval=1 &

echo "🚀 Levantando infraestructura en Docker..."
# Ya no pasamos la variable acá, dejamos que docker-compose se encargue
docker compose up --build lab-mac localtunnel