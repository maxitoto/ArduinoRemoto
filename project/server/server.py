import os
import time
import threading
import queue
import uuid
import serial
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from ArduinoRemoto.project.server.motor import procesar_archivos_arduino, obtener_puerto_actual

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_web = os.path.abspath(os.path.join(ruta_actual, '..', 'web'))
app = Flask(__name__, static_folder=ruta_web, static_url_path='')
CORS(app)

# Estructuras de datos globales
cola_trabajos = queue.Queue()
pizarra_estados = {} 
flujos_serie = {} 
eventos_cancelacion = {} 

# --- CONFIGURACIÓN DE LIMPIEZA ---
TIEMPO_MAX_INACTIVIDAD = 120
ID_TICKET_LIMPIEZA = "SISTEMA-LIMPIEZA"
ultima_actividad = time.time()
limpieza_ejecutada = False 
hardware_ocupado = False

def actualizar_actividad():
    global ultima_actividad, limpieza_ejecutada
    ultima_actividad = time.time()
    limpieza_ejecutada = False

def trabajador_hardware():
    global hardware_ocupado
    while True:
        ticket, archivos = cola_trabajos.get() 
        hardware_ocupado = True
        if ticket != ID_TICKET_LIMPIEZA:
            actualizar_actividad()  
        pizarra_estados[ticket]["estado"] = "procesando"
        
        evento_abortar = threading.Event()
        eventos_cancelacion[ticket] = evento_abortar
        
        try:
            resultado = procesar_archivos_arduino(archivos, ticket)
            pizarra_estados[ticket]["detalles"] = resultado
            
            if resultado.get("exito_total"):
                
                if ticket == ID_TICKET_LIMPIEZA:
                    pizarra_estados[ticket]["estado"] = "exito"
                    print("✨ Hardware limpio y en estado de reposo.", flush=True)
                else:
                    flujos_serie[ticket] = queue.Queue()
                    pizarra_estados[ticket]["estado"] = "exito" 
                    
                    time.sleep(2) 
                    tiempo_limite = time.time() + 40
                    
                    try:
                        puerto_real = obtener_puerto_actual()
                        with serial.Serial(puerto_real, 9600, timeout=1) as puerto:
                            while time.time() < tiempo_limite and not evento_abortar.is_set():
                                linea = puerto.readline().decode('utf-8', errors='replace').strip()
                                if linea:
                                    flujos_serie[ticket].put(linea)
                    except Exception as e:
                        flujos_serie[ticket].put(f"[ERROR DE HARDWARE: {str(e)}]")
                    
                    flujos_serie[ticket].put("EOF") 
                    print(f"⏳ Trabajo {ticket[:8]} finalizado.", flush=True)
            else:
                pizarra_estados[ticket]["estado"] = "error"
        except Exception as e:
            pizarra_estados[ticket]["estado"] = "error"
            pizarra_estados[ticket]["detalles"] = {"error_critico": str(e)}
            
        if ticket != ID_TICKET_LIMPIEZA:
            actualizar_actividad()
        hardware_ocupado = False
        cola_trabajos.task_done()
        if ticket in eventos_cancelacion: del eventos_cancelacion[ticket]

def vigilante_inactividad():
    global limpieza_ejecutada
    print("⏳ Vigilante de inactividad iniciado...", flush=True)
    
    while True:
        time.sleep(2) 
        if hardware_ocupado:
            continue
        ahora = time.time()
        inactivo = ahora - ultima_actividad
        
        if inactivo > TIEMPO_MAX_INACTIVIDAD and not limpieza_ejecutada:
            if cola_trabajos.empty():
                print("\n🧹 [VIGILANTE] Sistema inactivo. Preparando limpieza...", flush=True)
                
                try:
                    ruta_actual = os.path.abspath(os.path.dirname(__file__))
                    ruta_down = os.path.join(ruta_actual, "down.ino")
                    
                    if os.path.exists(ruta_down):
                        with open(ruta_down, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                        
                        archivos_limpieza = [{"filename": "down.ino", "content": contenido}]
                        pizarra_estados[ID_TICKET_LIMPIEZA] = {"estado": "en_cola", "detalles": None}
                        cola_trabajos.put((ID_TICKET_LIMPIEZA, archivos_limpieza))
                        limpieza_ejecutada = True 
                        print("✅ [VIGILANTE] Ticket de limpieza enviado exitosamente.", flush=True)
                    else:
                        print(f"⚠️ [VIGILANTE] Error: No existe el archivo {ruta_down}", flush=True)
                        limpieza_ejecutada = True 
                
                except Exception as e:
                    print(f"⚠️ [VIGILANTE] Error crítico al cargar limpieza: {e}", flush=True)

# 3. CORRECCIÓN: Los hilos se inician abajo de todo, cuando las funciones ya existen en memoria
threading.Thread(target=trabajador_hardware, daemon=True).start()
threading.Thread(target=vigilante_inactividad, daemon=True).start()


# --- RUTAS ---

@app.route('/')
def servir_frontend():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def procesar_archivos_light():
    global limpieza_ejecutada
    """Recibe los archivos y los encola con un ticket único."""
    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No se subieron archivos"}), 400
    
    # IMPORTANTE: Aquí aplicamos el .decode('utf-8') para que el contenido sea texto y no bytes
    # Esto evita el error 500 que bloquea al navegador
    try:
        archivos_en_memoria = [
            {"filename": f.filename, "content": f.read().decode('utf-8')} 
            for f in request.files.getlist('files')
        ]
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al leer archivos: {str(e)}"}), 400

    ticket = str(uuid.uuid4())
    posicion = cola_trabajos.qsize() + 1
    
    # Registramos en la pizarra
    pizarra_estados[ticket] = {
        "estado": "en_cola", 
        "posicion": posicion, 
        "detalles": None
    }

    actualizar_actividad() 
    limpieza_ejecutada = False 
    
    # Metemos a la cola para el trabajador
    cola_trabajos.put((ticket, archivos_en_memoria))

    # Esta respuesta es la que espera scripts.js para cambiar el botón
    return jsonify({
        "status": "queued", 
        "ticket": ticket, 
        "posicion": posicion
    })

@app.route('/status/<ticket>', methods=['GET'])
def consultar_estado(ticket):
    """Informa al frontend sobre el progreso del ticket."""
    return jsonify(pizarra_estados.get(ticket, {"estado": "no_encontrado"}))

@app.route('/stream/<ticket>')
def stream_serial(ticket):
    """Genera el flujo de datos SSE para el monitor serie."""
    def generar():
        q = flujos_serie.get(ticket)
        if not q: return
        while True:
            linea = q.get()
            yield f"data: {linea}\n\n"
            if linea == "EOF": break
            
    return Response(generar(), mimetype='text/event-stream')

@app.route('/abort/<ticket>', methods=['POST'])
def abortar_trabajo(ticket):
    """Cancela la ejecución actual a petición del usuario."""
    if ticket in eventos_cancelacion:
        eventos_cancelacion[ticket].set()
        return jsonify({"status": "aborted"})
    return jsonify({"status": "error"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)