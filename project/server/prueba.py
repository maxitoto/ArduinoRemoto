import requests
import concurrent.futures
import os

URL_SERVIDOR = "https://lab-tdf.loca.lt/upload"
CANTIDAD_COMPANEROS = 5

# El nombre del archivo real que tenés en tu carpeta
ARCHIVO_LOCAL = "buzzer.ino" 

# 1. Verificamos que el archivo exista antes de empezar el ataque
if not os.path.exists(ARCHIVO_LOCAL):
    print(f"❌ Error: No se encontró el archivo '{ARCHIVO_LOCAL}' en la misma carpeta que este script.")
    exit(1)

# 2. Leemos el archivo físico una sola vez y lo guardamos en RAM
with open(ARCHIVO_LOCAL, 'rb') as f:
    contenido_ino = f.read()

def enviar_trabajo(id_companero):
    print(f"👨‍💻 Compañero {id_companero} enviando código...")
    
    # 3. Empaquetamos el contenido real del archivo
    archivos = {
        'files': (ARCHIVO_LOCAL, contenido_ino, 'text/plain')
    }
    
    try:
        headers = {"Bypass-Tunnel-Reminder": "true"}
        respuesta = requests.post(URL_SERVIDOR, files=archivos, headers=headers)
        
        datos = respuesta.json()
        if datos.get("status") == "queued":
            print(f"✅ Compañero {id_companero} en cola! Ticket: {datos['ticket'][:8]} | Posición: {datos['posicion']}")
        else:
            print(f"⚠️ Compañero {id_companero} recibió una respuesta rara: {datos}")
            
    except Exception as e:
        print(f"❌ Compañero {id_companero} falló por error de red: {e}")

print(f"🚀 Iniciando envío simultáneo de {CANTIDAD_COMPANEROS} trabajos usando el archivo físico '{ARCHIVO_LOCAL}'...")

# 4. Lanzamos el ataque concurrente
with concurrent.futures.ThreadPoolExecutor(max_workers=CANTIDAD_COMPANEROS) as executor:
    futuros = [executor.submit(enviar_trabajo, i) for i in range(1, CANTIDAD_COMPANEROS + 1)]
    
    for futuro in concurrent.futures.as_completed(futuros):
        pass

print("🎉 Todos los clones terminaron de enviar sus peticiones.")