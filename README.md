Aquí tenés el `README.md` reescrito desde cero. Quedó estructurado como un manual profesional, separando claramente los dos caminos (Nativo vs. Docker) y detallando paso a paso todo lo que sacamos del script de arranque.

```markdown
# 🛠️ Laboratorio Remoto TDF - Arquitectura Distribuida

Este repositorio contiene la infraestructura necesaria para desplegar el laboratorio remoto de hardware. Para garantizar el acceso directo a los dispositivos físicos, el sistema utiliza **ejecución nativa en macOS** y **contenedores aislados en Linux**.

---

## 🚀 Cómo Empezar

Dependiendo de tu sistema operativo, sigue las instrucciones correspondientes:

### 🍎 Usuarios de macOS (Modo Nativo)

Dado que macOS gestiona de forma estricta el acceso a los puertos USB físicos, la ejecución se realiza de manera local.

**Paso 1: Instalación de Dependencias (Solo la primera vez)**
Abre tu terminal en la carpeta del proyecto y ejecuta los siguientes comandos para configurar el compilador, las librerías de hardware y el entorno de Python:

```bash
# 1. Instalar compilador y Python
brew install arduino-cli python@3.12

# 2. Descargar núcleos de Arduino
arduino-cli core update-index
arduino-cli core install arduino:avr@1.8.7

# 3. Instalar librerías de sensores (desde libraries.txt)
cat libraries.txt | xargs -I {} arduino-cli lib install "{}"

# 4. Crear entorno virtual y dependencias de servidor
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

**Paso 2: Ejecución del Laboratorio (Uso diario)**
Conecta tu Arduino por USB y arranca el servidor mediante el script automatizado:

```bash
chmod +x start.sh
./start.sh

```

*El script levantará el servidor, activará el entorno y te proporcionará la URL pública (https://lab-tdf.loca.lt).*

---

### 🐧 Usuarios de Linux (Modo Docker)

La infraestructura en Linux está completamente paquetizada. Solo necesitas inyectar la variable del puerto físico hacia adentro del contenedor.

**Paso 1: Detectar el Puerto Físico**
Conecta el Arduino por USB, abre una terminal y ejecuta:

```bash
ls /dev/ttyACM* 2>/dev/null || ls /dev/ttyUSB* 2>/dev/null

```

*Anota el resultado (por ejemplo: `/dev/ttyACM0`).*

**Paso 2: Ejecución del Laboratorio**
Exporta la variable con el puerto que encontraste y levanta los contenedores:

```bash
export PORT_ARDUINO=/dev/ttyACM0
docker compose up --build

```

*(Nota: Asegúrate de que tu usuario de Linux pertenezca al grupo `dialout` para evitar errores de permisos sobre el puerto).*

---

## 🔍 Guía Rápida: ¿No encuentras tu Arduino?

Si el sistema no detecta la placa, puedes forzar la búsqueda de esta manera:

* **En Mac:** Abre la terminal y ejecuta `ls /dev/cu.*`. Busca en la lista un dispositivo que se llame `/dev/cu.usbmodem...`
* **En Linux:** Revisa los mensajes del sistema para ver qué dispositivo se asignó al conectar el cable ejecutando `dmesg | grep tty`.

```

```