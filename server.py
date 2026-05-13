import os
import time
import threading
import queue
import uuid # Para generar tickets únicos
from flask import Flask, request, jsonify
from flask_cors import CORS
from motor import procesar_archivos_arduino

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

cola_trabajos = queue.Queue()
pizarra_estados = {} # Acá guardamos cómo va cada ticket

def trabajador_hardware():
    print("🤖 Trabajador de hardware iniciado y esperando en las sombras...", flush=True)
    while True:
        # Ahora la cola nos da el TICKET y los ARCHIVOS
        ticket, archivos = cola_trabajos.get() 
        
        print(f"\n⚙️ Procesando trabajo {ticket}. Quedan {cola_trabajos.qsize()} en cola.", flush=True)
        pizarra_estados[ticket]["estado"] = "procesando"
        
        try:
            resultado = procesar_archivos_arduino(archivos)
            pizarra_estados[ticket]["detalles"] = resultado
            
            if resultado.get("exito_total"):
                print("✅ Hardware flasheado. Iniciando ventana de tiempo de 60 segundos...", flush=True)
                pizarra_estados[ticket]["estado"] = "exito" # Le avisamos a la web que ya está
                time.sleep(60) 
                print("⏳ Tiempo terminado. Listo para el siguiente trabajo.", flush=True)
            else:
                print("❌ El trabajo falló al compilar/subir.", flush=True)
                pizarra_estados[ticket]["estado"] = "error"
        except Exception as e:
            print(f"🔥 Error catastrófico: {e}", flush=True)
            pizarra_estados[ticket]["estado"] = "error"
            pizarra_estados[ticket]["detalles"] = {"error_critico": str(e)}
            
        cola_trabajos.task_done()

hilo_motor = threading.Thread(target=trabajador_hardware, daemon=True)
hilo_motor.start()

# --- RUTAS DE FLASK ---

@app.route('/')
def servir_frontend():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def procesar_archivos_light():
    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No se recibieron archivos."}), 400
    
    archivos_en_memoria = []
    for f in request.files.getlist('files'):
        archivos_en_memoria.append({
            "filename": f.filename,
            "content": f.read() 
        })
    
    # 1. Generamos un ticket único para este alumno
    ticket = str(uuid.uuid4())
    posicion = cola_trabajos.qsize() + 1
    
    # 2. Anotamos en la pizarra que está en cola
    pizarra_estados[ticket] = {
        "estado": "en_cola",
        "posicion": posicion,
        "detalles": None
    }
    
    # 3. Mandamos a la cola la dupla (ticket, archivos)
    cola_trabajos.put((ticket, archivos_en_memoria))

    return jsonify({
        "status": "queued", 
        "ticket": ticket,
        "posicion": posicion
    })

# NUEVA RUTA: El frontend consulta por acá cómo va su ticket
@app.route('/status/<ticket>', methods=['GET'])
def consultar_estado(ticket):
    estado_actual = pizarra_estados.get(ticket)
    if not estado_actual:
        return jsonify({"estado": "no_encontrado"}), 404
    return jsonify(estado_actual)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)