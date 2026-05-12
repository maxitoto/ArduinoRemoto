import os
import shutil
import subprocess

# Configuraciones de tu hardware

# En motor.py
# FQBN = "arduino:avr:uno"  # Descomentar esta para el UNO
FQBN = "arduino:avr:mega"   # Descomentar esta para el MEGA      

PUERTO_USB = "/dev/cu.usbmodem14101" 

def ejecutar_comando_terminal(comando):
    
    resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
    return {
        "exito": resultado.returncode == 0,
        "salida": resultado.stdout,
        "error": resultado.stderr
    }

def procesar_archivos_arduino(archivos_recibidos, directorio_base="/tmp/arduino_workspace"):
    feedback = {
        "etapa_preparacion": {"estado": "pendiente", "logs": []},
        "etapa_compilacion": {"estado": "pendiente", "logs": []},
        "etapa_subida": {"estado": "pendiente", "logs": []},
        "exito_total": False
    }

    try:
        # FASE 1: Preparación
        feedback["etapa_preparacion"]["estado"] = "en_proceso"
        archivo_principal = next((f for f in archivos_recibidos if f.filename.endswith('.ino')), None)
        
        if not archivo_principal:
            feedback["etapa_preparacion"]["estado"] = "error"
            feedback["etapa_preparacion"]["logs"].append("Error: No se encontró archivo .ino.")
            return feedback

        nombre_proyecto = archivo_principal.filename.replace('.ino', '')
        ruta_proyecto = os.path.join(directorio_base, nombre_proyecto)

        if os.path.exists(ruta_proyecto):
            shutil.rmtree(ruta_proyecto)
        os.makedirs(ruta_proyecto)

        # Guardamos todos los archivos en esa carpeta
        nombres_guardados = []
        for archivo in archivos_recibidos:
            ruta_guardado = os.path.join(ruta_proyecto, archivo.filename)
            archivo.seek(0) 
            archivo.save(ruta_guardado)
            nombres_guardados.append(archivo.filename)

        feedback["etapa_preparacion"]["logs"].append(f"Guardado en {ruta_proyecto}: {', '.join(nombres_guardados)}")
        feedback["etapa_preparacion"]["estado"] = "exito"

        # ==========================================
        # ETAPA 1.5: RESOLVER LIBRERÍAS (Auto-install)
        # ==========================================
        feedback["etapa_preparacion"]["logs"].append("Escaneando dependencias externas...")

        # Este comando busca e instala librerías faltantes basadas en los #include del código
        comando_libs = f"arduino-cli lib install --git-url https://github.com/arduino-libraries/Servo.git" # Ejemplo manual
        # O mejor aún, el comando automático:
        comando_auto_libs = f"arduino-cli lib resolve {ruta_proyecto}"

        res_libs = ejecutar_comando_terminal(comando_auto_libs)
        if res_libs["exito"]:
            feedback["etapa_preparacion"]["logs"].append("Librerías sincronizadas correctamente.")
        else:
            # A veces falla si la lib no es oficial, pero igual intentamos compilar
            feedback["etapa_preparacion"]["logs"].append("Aviso: Algunas librerías podrían requerir instalación manual.")
        

        # FASE 2: Compilación
        feedback["etapa_compilacion"]["estado"] = "en_proceso"

        # Agregamos --libraries apuntando a la misma ruta del proyecto
        comando_compilar = f"arduino-cli compile --fqbn {FQBN} --libraries {ruta_proyecto} {ruta_proyecto}"

        feedback["etapa_compilacion"]["logs"].append(f"Compilando con librerías locales en: {ruta_proyecto}")
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
        comando_subir = f"arduino-cli upload -p {PUERTO_USB} --fqbn {FQBN} {ruta_proyecto}"
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