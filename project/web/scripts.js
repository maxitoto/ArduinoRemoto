const inputArchivo = document.getElementById("inputArchivo");
const btnAccion = document.getElementById("btnAccion"); 
const consola = document.getElementById("consola");

let ticketGlobal = null; 
let ejecutandoStream = false; 
let controladorStream = null;

// --- GESTIÓN DE INTERFAZ Y CONSOLA ---
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

function setBotonEstado(modo) {
  const icono = document.getElementById("btnIcono");
  const texto = document.getElementById("btnTexto");

  if (modo === "enviar") {
    btnAccion.style.background = "var(--primary)";
    icono.textContent = "bolt";
    texto.textContent = "EJECUTAR EN HARDWARE";
    ejecutandoStream = false;
  } else if (modo === "cancelar") {
    btnAccion.style.background = "var(--error)";
    icono.textContent = "cancel";
    texto.textContent = "DETENER EJECUCIÓN";
    btnAccion.disabled = false; 
    ejecutandoStream = true;
  }
}

function toggleAccion() {
  if (!ejecutandoStream) {
    ejecutarProceso();
  } else {
    abortarProceso();
  }
}

// --- EVENTOS ---
inputArchivo.addEventListener("change", (e) => {
  const archivos = e.target.files;

  setPaso(1, ""); setPaso(2, ""); setPaso(3, "");
  consola.innerHTML = "";

  if (archivos.length > 0) {
    const nombre = archivos.length === 1 ? archivos[0].name : `${archivos.length} archivos`;
    document.getElementById("hud-archivo").textContent = nombre;
    document.getElementById("hud-estado").textContent = "LISTO";
    btnAccion.disabled = false;
    log(`Archivos listos: ${nombre}`);
  } else {
    btnAccion.disabled = true;
    document.getElementById("hud-archivo").textContent = "NINGUNO";
  }
});

// --- LÓGICA DE RED Y FLUJO ---
async function ejecutarProceso() {
  const archivos = inputArchivo.files;
  if (archivos.length === 0) return;

  btnAccion.disabled = true;
  consola.innerHTML = "";
  log("Iniciando sesión de laboratorio remoto...");

  const formData = new FormData();
  for (let i = 0; i < archivos.length; i++) {
    formData.append("files", archivos[i]);
  }

  try {
    setPaso(1, "activo");
    document.getElementById("hud-estado").textContent = "ENVIANDO...";

    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
      headers: { "Bypass-Tunnel-Reminder": "true" }
    });

    const data = await response.json();

    if (data.status === "queued") {
      setPaso(1, "exito");
      ticketGlobal = data.ticket; 
      log(`Ticket asignado: ${ticketGlobal.substring(0,8)}`, "#007acc");
      monitorearTicket(ticketGlobal);
    }
  } catch (error) {
    setPaso(1, "fallo");
    log(`Error de conexión al enviar.`, "#e74c3c");
    btnAccion.disabled = false;
  }
}

async function monitorearTicket(ticket) {
  try {
    const response = await fetch(`/status/${ticket}`, { headers: { "Bypass-Tunnel-Reminder": "true" } });
    const data = await response.json();

    if (data.estado === "en_cola") {
      document.getElementById("hud-estado").textContent = "EN ESPERA";
      setTimeout(() => monitorearTicket(ticket), 3000);
    } else if (data.estado === "procesando") {
      document.getElementById("hud-estado").textContent = "EJECUTANDO";
      setPaso(2, "activo");
      setTimeout(() => monitorearTicket(ticket), 2000);
    } else if (data.estado === "exito" || data.estado === "error") {
      mostrarFeedbackCompleto(data, ticket);
    }
  } catch (error) {
    setTimeout(() => monitorearTicket(ticket), 5000);
  }
}

function mostrarFeedbackCompleto(data, ticket) {
  const detalles = data.detalles;
  
  if (detalles) {
    // ---> AGREGAR ESTAS 3 LÍNEAS NUEVAS <---
    if (detalles.etapa_preparacion && detalles.etapa_preparacion.estado === "error") {
        detalles.etapa_preparacion.logs.forEach(msg => log(msg, "#e74c3c"));
    }
    // ----------------------------------------
    if (detalles.etapa_compilacion && detalles.etapa_compilacion.estado === "error") {
        detalles.etapa_compilacion.logs.forEach(msg => log(msg, "#e74c3c"));
    }
    if (detalles.etapa_subida && detalles.etapa_subida.estado === "error") {
        detalles.etapa_subida.logs.forEach(msg => log(msg, "#e74c3c"));
    }
  }

  if (data.estado === "exito") {
    document.getElementById("hud-estado").textContent = "SISTEMA ONLINE";
    setPaso(2, "exito"); setPaso(3, "exito");
    log("------------------------------------------", "#555");
    log("📡 SINTONIZANDO MONITOR SERIE EN VIVO...", "#007acc");
    iniciarStreamSerial(ticket);
  } else {
    document.getElementById("hud-estado").textContent = "FALLO TÉCNICO";
    // Pintamos los pasos según dónde falló
    setPaso(2, detalles.etapa_compilacion?.estado === "error" ? "fallo" : "exito");
    setPaso(3, detalles.etapa_subida?.estado === "error" ? "fallo" : "");
    btnAccion.disabled = false;
  }
}

async function iniciarStreamSerial(ticket) {
  try {
    setBotonEstado("cancelar"); 
    controladorStream = new AbortController();

    const response = await fetch(`/stream/${ticket}`, {
      headers: { "Bypass-Tunnel-Reminder": "true" },
      signal: controladorStream.signal
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lineas = buffer.split('\n\n'); 
      buffer = lineas.pop(); 

      for (let bloque of lineas) {
        const partes = bloque.split('\n');
        for (let linea of partes) {
          if (linea.startsWith("data: ")) {
            const dato = linea.substring(6);
            
            if (dato === "EOF") {
              log("🛑 EJECUCIÓN TERMINADA. PLACA LIBERADA.", "#e74c3c");
              document.getElementById("hud-estado").textContent = "IDLE";
              setBotonEstado("enviar"); 
              return;
            } else if (dato.trim() !== "") {
              log(`[ARDUINO]: ${dato}`, "#f1c40f");
            }
          }
        }
      }
    }
  } catch (err) {
    // NUEVO: Detectamos si el error fue porque nosotros mismos lo matamos
    if (err.name === 'AbortError') {
      log("🛑 LECTURA CERRADA POR EL USUARIO.", "#e74c3c");
    } else {
      log("⚠️ Conexión de red interrumpida.", "#e74c3c");
    }
    setBotonEstado("enviar");
  }
}

async function abortarProceso() {
  if (!ticketGlobal) return;
  log("🛑 Deteniendo proceso...", "#e74c3c");

  // 1. Matamos la conexión del navegador al instante (esto dispara el AbortError de arriba)
  if (controladorStream) {
    controladorStream.abort();
    controladorStream = null;
  }

  // 2. Reseteamos la interfaz manualmente para que quede lista para un nuevo envío
  document.getElementById("hud-estado").textContent = "IDLE";
  setBotonEstado("enviar");
  btnAccion.disabled = false; // Habilitamos el botón de nuevo por las dudas

  // 3. Le avisamos al servidor que suelte el Arduino (en segundo plano)
  try {
    await fetch(`/abort/${ticketGlobal}`, {
      method: "POST",
      headers: { "Bypass-Tunnel-Reminder": "true" }
    });
  } catch (err) {
    console.warn("No se pudo notificar al servidor, pero la interfaz fue liberada.");
  }
}