## Inicio
1. **Requisitos**: Tener Docker Desktop instalado.
2. **Configuración**: 
   - Abrir `docker-compose.yml`.
   - En la sección `devices`, cambiar `/dev/ttyACM0` por el puerto donde esté su Arduino.
3. **Ejecución**:
   - Abrir una terminal en la carpeta.
   - Ejecutar: `docker-compose up --build`
4. **Acceso**:
   - El túnel se creará automáticamente en: https://lab-arduino-tdf.localtunnel.me
  
## Cómo encuentrar el puerto rápidamente

 ###  Si usa Windows:
1. Que conecte el Arduino por USB.
2. Que presione la tecla Windows, escriba Administrador de dispositivos y presione Enter.
3. Que busque en la lista la sección que dice Puertos (COM y LPT) y la expanda.
4. Ahí va a ver su placa listada claramente, por ejemplo: Arduino Mega 2560 (COM3) o USB Serial Device (COM4).

### Si usa Mac:

1. Que conecte el Arduino.
2. Que abra su terminal nativa y ejecute: ls /dev/cu.*
3. Le saldrá el puerto clásico: /dev/cu.usbmodem...

### Si usa Linux:

1. Que conecte el Arduino.
2. Que abra su terminal y ejecute: ls /dev/ttyACM* o ls /dev/ttyUSB*.