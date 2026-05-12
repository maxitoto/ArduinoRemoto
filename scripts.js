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
  paso.className = `paso ${estado}`;
}

inputArchivo.addEventListener("change", (e) => {
  const archivos = e.target.files;

  setPaso(1, "");
  setPaso(2, "");
  setPaso(3, "");
  consola.innerHTML = "";

  if (archivos.length > 0) {
    const nombre =
      archivos.length === 1 ? archivos[0].name : `${archivos.length} archivos`;
    document.getElementById("hud-archivo").textContent = nombre;
    document.getElementById("hud-estado").textContent = "Listo para enviar";
    btnEnviar.disabled = false;
    log(`Archivos cargados: ${nombre}`);
  } else {
    btnEnviar.disabled = true;
    document.getElementById("hud-archivo").textContent = "Ninguno";
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
    // FASES INICIALES VISUALES
    setPaso(1, "activo");
    document.getElementById("hud-estado").textContent = "Enviando...";
    log("Enviando archivos...");

    // LLAMADA A FLASK
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    const motor = data.detalles; // Este es el diccionario gigante de Python

    consola.innerHTML = ""; // Limpiamos consola

    // --- PINTAR LOS LOGS DEL MOTOR ---
    // Leemos etapa 1 (Preparación)
    motor.etapa_preparacion.logs.forEach((l) => log(l, "#aaaaaa"));

    // Leemos etapa 2 (Compilación)
    if (motor.etapa_compilacion.logs.length > 0) {
      motor.etapa_compilacion.logs.forEach((l) =>
        log(
          l,
          motor.etapa_compilacion.estado === "error" ? "#ff4d4d" : "#ffffff",
        ),
      );
    }

    // Leemos etapa 3 (Subida)
    if (motor.etapa_subida.logs.length > 0) {
      motor.etapa_subida.logs.forEach((l) =>
        log(l, motor.etapa_subida.estado === "error" ? "#ff4d4d" : "#a8ffcc"),
      );
    }

    // --- PINTAR LOS CIRCULOS DEL TIMELINE ---
    setPaso(1, motor.etapa_preparacion.estado === "exito" ? "exito" : "fallo");

    if (motor.etapa_preparacion.estado === "exito") {
      setPaso(
        2,
        motor.etapa_compilacion.estado === "exito"
          ? "exito"
          : motor.etapa_compilacion.estado === "error"
            ? "fallo"
            : "",
      );
    }

    if (motor.etapa_compilacion.estado === "exito") {
      setPaso(
        3,
        motor.etapa_subida.estado === "exito"
          ? "exito"
          : motor.etapa_subida.estado === "error"
            ? "fallo"
            : "",
      );
    }

    // --- ESTADO FINAL DEL HUD ---
    if (data.status === "success") {
      document.getElementById("hud-estado").textContent = "¡Placa Programada!";
      log("Proceso exitoso. El Arduino está corriendo tu código.", "#2ecc71");
    } else {
      document.getElementById("hud-estado").textContent = "Error en el Motor";
      log("El proceso se detuvo por errores.", "#e74c3c");
    }
  } catch (error) {
    setPaso(1, "fallo");
    setPaso(2, "fallo");
    setPaso(3, "fallo");
    document.getElementById("hud-estado").textContent = "Fallo de Conexión";
    log("Error Crítico: ¿Se apagó el servidor Python?", "#e74c3c");
    console.error(error);
  } finally {
    btnEnviar.disabled = false;
  }
}
