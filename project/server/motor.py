import os
import shutil
import subprocess
import glob

# Configuración del hardware
FQBN = "arduino:avr:mega"   

import os

def obtener_puerto_actual():
    """Detecta el puerto físicamente en la Mac, o usa el entorno si existe."""
    # 1. Si existe la variable de entorno, la usamos
    puerto_env = os.environ.get('PORT_ARDUINO')
    if puerto_env:
        return puerto_env
    
    # 2. Si no hay variable (porque estás corriendo directo en la Mac), buscamos el cable
    import glob
    puertos_mac = glob.glob('/dev/cu.usbmodem*')
    if puertos_mac:
        return puertos_mac[0] # Retorna el primer Arduino que encuentre
        
    return '/dev/ttyUSB0' # Fallback de emergencia

def ejecutar_comando_terminal(comando, max_tiempo=30):
    """Ejecuta comandos en la terminal con un límite de tiempo para evitar bloqueos."""
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=max_tiempo)
        return {
            "exito": resultado.returncode == 0,
            "salida": resultado.stdout,
            "error": resultado.stderr
        }
    except subprocess.TimeoutExpired as e:
        # Extraemos el error crudo que haya quedado en el buffer
        error_crudo = e.stderr if e.stderr else e.stdout
        
        # ---> LA DEFENSA CONTRA BYTES <---
        if isinstance(error_crudo, bytes):
            error_crudo = error_crudo.decode('utf-8', errors='replace')
            
        if not error_crudo or error_crudo.strip() == "":
            error_crudo = "TIMEOUT ERROR: El servidor se saturó y canceló la compilación.\n"
            
        return {"exito": False, "salida": "", "error": error_crudo}

def procesar_archivos_arduino(archivos_recibidos, ticket, directorio_base="/tmp/arduino_workspace"):
    feedback = {
        "etapa_preparacion": {"estado": "pendiente", "logs": []},
        "etapa_compilacion": {"estado": "pendiente", "logs": []},
        "etapa_subida": {"estado": "pendiente", "logs": []},
        "exito_total": False
    }

    try:
        feedback["etapa_preparacion"]["estado"] = "en_proceso"
        archivo_principal = next((f for f in archivos_recibidos if f["filename"].endswith('.ino')), None)
        
        if not archivo_principal:
            feedback["etapa_preparacion"]["estado"] = "error"
            feedback["etapa_preparacion"]["logs"].append("Error: No se encontró archivo .ino principal.")
            return feedback

        nombre_proyecto = archivo_principal["filename"].replace('.ino', '')
        
        # --- LA MEJORA: Ruta única por ticket ---
        # Estructura: /tmp/arduino_workspace/ID_TICKET/NombreProyecto
        ruta_aislada = os.path.join(directorio_base, ticket)
        ruta_proyecto = os.path.join(ruta_aislada, nombre_proyecto)

        # Creamos la carpeta del ticket (limpia)
        if os.path.exists(ruta_aislada):
            shutil.rmtree(ruta_aislada)
        os.makedirs(ruta_proyecto) 

        for archivo in archivos_recibidos:
            ruta_guardado = os.path.join(ruta_proyecto, archivo["filename"])
            with open(ruta_guardado, 'w', encoding='utf-8') as f:
                f.write(archivo["content"])
        
        feedback["etapa_preparacion"]["estado"] = "exito"

        # FASE 2: Compilación (con rutas protegidas por comillas)
        feedback["etapa_compilacion"]["estado"] = "en_proceso"
        comando_compilar = f'arduino-cli compile --fqbn {FQBN} --libraries "{ruta_proyecto}" "{ruta_proyecto}"'
        res_compilacion = ejecutar_comando_terminal(comando_compilar)
        
        if res_compilacion["exito"]:
            feedback["etapa_compilacion"]["estado"] = "exito"
            feedback["etapa_compilacion"]["logs"].append(res_compilacion["salida"])
        else:
            feedback["etapa_compilacion"]["estado"] = "error"
            feedback["etapa_compilacion"]["logs"].append(res_compilacion["error"])
            return feedback

        # FASE 3: Subida
        feedback["etapa_subida"]["estado"] = "en_proceso"
        puerto_real = obtener_puerto_actual()
        comando_subir = f'arduino-cli upload -p {puerto_real} --fqbn {FQBN} "{ruta_proyecto}"'
        res_subida = ejecutar_comando_terminal(comando_subir)
        
        if res_subida["exito"]:
            feedback["etapa_subida"]["estado"] = "exito"
            feedback["etapa_subida"]["logs"].append(res_subida["salida"])
            feedback["exito_total"] = True
        else:
            feedback["etapa_subida"]["estado"] = "error"
            feedback["etapa_subida"]["logs"].append(res_subida["error"])
            return feedback

        return feedback

    except Exception as e:
        feedback["etapa_preparacion"]["estado"] = "error"
        feedback["etapa_preparacion"]["logs"].append(f"Falla crítica: {str(e)}")
        return feedback