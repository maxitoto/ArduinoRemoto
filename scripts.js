const inputArchivo = document.getElementById("inputArchivo");
const btnEnviar = document.getElementById("btnEnviar");
const consola = document.getElementById("consola");

function log(mensaje, color = "") {
  const p = document.createElement("p");
  p.textContent = `> ${mensaje}`;
  if (color) p.style.color = color;
  consola.appendChild(p);
  consola.scrollTop = consola.scrollHeight;
}

function setPaso(numero, estado) {
  const paso = document.getElementById(`paso-${numero}`);
  if (paso) paso.className = `paso ${estado}`;
}

inputArchivo.addEventListener("change", (e) => {
  const archivos = e.target.files;
  
  // Limpiamos visuales para nueva carga
  setPaso(1, "");
  setPaso(2, "");
  setPaso(3, "");
  consola.innerHTML = "";

  if (archivos.length > 0) {
    const nombre = archivos.length === 1 ? archivos[0].name : `${archivos.length} archivos`;
    document.getElementById("hud-archivo").textContent = nombre.toUpperCase();
    document.getElementById("hud-estado").textContent = "LISTO";
    btnEnviar.disabled = false;
    log(`Archivos cargados: ${nombre}`);
  }
});

async function ejecutarProceso() {
  const archivos = inputArchivo.files;
  if (archivos.length === 0) return;

  btnEnviar.disabled = true;

  const formData = new FormData();
  for (let i = 0; i < archivos.length; i++) {
    formData.append("files", archivos[i]);
  }

  try {
    setPaso(1, "activo");
    document.getElementById("hud-estado").textContent = "ENVIANDO...";
    log("Subiendo código al servidor de cola...");

    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
      headers: { "Bypass-Tunnel-Reminder": "true" }
    });

    const data = await response.json();

    if (data.status === "queued") {
      setPaso(1, "exito");
      log("------------------------------------------", "#555");
      log(`¡TICKET EMITIDO! Tu posición inicial: ${data.posicion}`, "#007acc");
      
      // Iniciamos la vigilancia del ticket
      monitorearTicket(data.ticket);
    } else {
      throw new Error(data.message || "Error al encolar");
    }
  } catch (error) {
    setPaso(1, "fallo");
    log(`Error Crítico: ${error.message}`, "#e74c3c");
    btnEnviar.disabled = false;
  }
}

// NUEVA FUNCIÓN: Pregunta al servidor cada 3 segundos
async function monitorearTicket(ticket) {
  try {
    const response = await fetch(`/status/${ticket}`, {
      headers: { "Bypass-Tunnel-Reminder": "true" }
    });
    const data = await response.json();

    if (data.estado === "en_cola") {
      document.getElementById("hud-estado").textContent = "EN COLA...";
      setTimeout(() => monitorearTicket(ticket), 3000); // Vuelve a preguntar en 3s
      
    } else if (data.estado === "procesando") {
      document.getElementById("hud-estado").textContent = "PROCESANDO";
      setPaso(2, "activo");
      log("⏳ Tu código está siendo procesado por el hardware...", "#e67e22");
      setTimeout(() => monitorearTicket(ticket), 3000); // Sigue preguntando
      
    } else if (data.estado === "exito") {
      document.getElementById("hud-estado").textContent = "FLASHEADO";
      setPaso(2, "exito");
      setPaso(3, "exito");
      log("------------------------------------------", "#555");
      log("✅ CÓDIGO SUBIDO AL ARDUINO EXITOSAMENTE", "#2ecc71");
      log("El hardware estará ejecutando tu código por 60 segundos.", "#aaaaaa");
      btnEnviar.disabled = false; // Liberamos el botón
      
    } else if (data.estado === "error") {
      document.getElementById("hud-estado").textContent = "ERROR MOTOR";
      setPaso(2, "fallo");
      setPaso(3, "fallo");
      log("❌ Error en la compilación o subida:", "#e74c3c");
      
      // Imprimimos el detalle del motor si existe
      if (data.detalles && data.detalles.etapa_compilacion) {
          data.detalles.etapa_compilacion.logs.forEach(l => log(l, "#e74c3c"));
      }
      btnEnviar.disabled = false;
    }

  } catch (error) {
    log("Error al consultar estado: " + error.message, "#e74c3c");
    setTimeout(() => monitorearTicket(ticket), 5000);
  }
}