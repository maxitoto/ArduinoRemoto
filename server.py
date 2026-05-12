import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# 1. Importación directa (ya no es "from web.motor")
from motor import procesar_archivos_arduino 

# 2. El static_folder es la carpeta actual ('.')
app = Flask(__name__, static_folder='.', static_url_path='')

CORS(app) 

@app.route('/')
def servir_frontend():
    # 3. Llamamos al index.html directamente
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def procesar_archivos_light():
    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No se recibieron archivos."}), 400
    
    archivos = request.files.getlist('files')
    print(f"\n📦 Delegando {len(archivos)} archivo(s) al motor de Arduino...")
    
    resultado_motor = procesar_archivos_arduino(archivos)

    print("✅ Respuesta del motor recibida.")

    estado_final = "success" if resultado_motor["exito_total"] else "error"

    return jsonify({
        "status": estado_final, 
        "message": "Proceso de hardware finalizado.",
        "detalles": resultado_motor 
    })

if __name__ == '__main__':
    app.run(port=5000)