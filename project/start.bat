@echo off
TITLE Laboratorio Remoto TDF - Windows

echo ---------------------------------------------------
echo 🚀 INICIANDO SERVIDORES DEL LABORATORIO (Windows)
echo ---------------------------------------------------

:: 1. Activación del Entorno Virtual
if exist .venv (
    call .venv\Scripts\activate
) else (
    echo ❌ Error: No se detecto el entorno virtual (.venv).
    echo Revisa las instrucciones de instalacion en el README.md.
    pause
    exit /b
)

:: 2. Detección de Hardware (Buscamos puertos COM)
echo 🔍 Buscando Arduino fisico...
for /f "tokens=*" %%i in ('powershell -Command "Get-PnpDevice -PresentOnly | Where-Object { $_.FriendlyName -match 'Arduino' -or $_.FriendlyName -match 'USB Serial Device' } | Select-Object -ExpandProperty DeviceID | ForEach-Object { Get-ItemProperty -Path \"HKLM:\SYSTEM\CurrentControlSet\Enum\$($_)\Device Parameters\" } | Select-Object -ExpandProperty PortName -ErrorAction SilentlyContinue"') do set PORT_ARDUINO=%%i

if "%PORT_ARDUINO%"=="" (
    echo ⚠️  ATENCION: No se detecto Arduino. El servidor iniciara, pero el hardware podria no responder.
) else (
    echo ✅ Arduino detectado en el puerto: %PORT_ARDUINO%
    set PORT_ARDUINO=%PORT_ARDUINO%
)

:: 3. Inicio del Servidor Flask
echo 🔥 Iniciando Servidor Flask...
:: En Windows usamos 'start /b' para que corra en segundo plano en la misma ventana
start /b python server/server.py

:: 4. Gestión del Túnel (Localtunnel)
echo 🌐 Configurando acceso remoto...
timeout /t 3 > nul

:: Verificamos si existe npx (Node.js)
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo 📥 Node.js no detectado. Por favor, instalalo desde https://nodejs.org/
    pause
    exit /b
)

echo 🔗 Generando URL publica...
npx -y localtunnel --port 5000 --subdomain lab-tdf