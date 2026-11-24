const form = document.querySelector("#analysis-form");
const input = document.querySelector("#image-files");
const button = document.querySelector("#analyze-button");
const selectedFiles = document.querySelector("#selected-files");
const message = document.querySelector("#form-message");
const results = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");

const sliders = [
  ["hue-min", "hue-min-value", value => value],
  ["hue-max", "hue-max-value", value => value],
  ["saturation-min", "saturation-value", value => value],
  ["value-min", "value-value", value => value],
  ["min-area-ratio", "area-value", value => `${value}%`],
];

sliders.forEach(([inputId, outputId, format]) => {
  const control = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  control.addEventListener("input", () => {
    output.value = format(control.value);
    output.textContent = format(control.value);
  });
});

input.addEventListener("change", () => {
  const names = Array.from(input.files, file => file.name);
  selectedFiles.textContent = names.length
    ? `${names.length} archivo(s): ${names.join(", ")}`
    : "Todavia no seleccionaste imagenes";
});

document.querySelector("#dropzone").addEventListener("dragover", event => {
  event.preventDefault();
  event.currentTarget.classList.add("dragging");
});

document.querySelector("#dropzone").addEventListener("dragleave", event => {
  event.currentTarget.classList.remove("dragging");
});

document.querySelector("#dropzone").addEventListener("drop", event => {
  event.preventDefault();
  event.currentTarget.classList.remove("dragging");
  if (event.dataTransfer.files.length) {
    input.files = event.dataTransfer.files;
    input.dispatchEvent(new Event("change"));
  }
});

async function checkServer() {
  // Actualiza el indicador de disponibilidad de la API.
  const status = document.querySelector("#server-status");
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("Backend no disponible");
    status.textContent = "Backend conectado";
    status.dataset.state = "ok";
  } catch (error) {
    status.textContent = "No se pudo conectar con el backend";
    status.dataset.state = "error";
  }
}

function createResultCard(item) {
  // Construye la tarjeta con medidas, etapas o error de una imagen.
  const card = document.createElement("article");
  card.className = "result-card";
  const heading = document.createElement("div");
  heading.className = "result-card-heading";
  const title = document.createElement("h3");
  title.textContent = item.filename;
  heading.append(title);
  card.append(heading);

  if (item.status !== "ok") {
    const error = document.createElement("p");
    error.className = "error-message";
    error.textContent = item.error;
    card.append(error);
    return card;
  }

  const metrics = document.createElement("dl");
  metrics.className = "metrics";
  const data = item.measurements;
  [
    ["Area", `${data.area_px.toLocaleString("es-AR")} px²`],
    ["Perimetro", `${data.perimeter_px.toLocaleString("es-AR")} px`],
    ["Ancho × alto", `${data.width_px} × ${data.height_px} px`],
    ["Proporcion", data.aspect_ratio.toFixed(3)],
  ].forEach(([label, value]) => {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    wrapper.append(term, description);
    metrics.append(wrapper);
  });
  card.append(metrics);

  const stages = document.createElement("div");
  stages.className = "stage-grid";
  item.stages.forEach(stage => {
    const figure = document.createElement("figure");
    const image = document.createElement("img");
    const caption = document.createElement("figcaption");
    const download = document.createElement("a");
    image.src = stage.image;
    image.alt = stage.label;
    caption.textContent = stage.label;
    download.href = stage.image;
    download.download = stage.filename;
    download.textContent = "Guardar PNG";
    figure.append(image, caption, download);
    stages.append(figure);
  });
  card.append(stages);
  return card;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  if (!input.files.length) {
    message.textContent = "Selecciona al menos una imagen.";
    return;
  }
  const formData = new FormData(form);
  Array.from(input.files).forEach(file => formData.append("files", file));
  formData.delete("image-files");
  formData.set(
    "min_area_ratio",
    String(Number(document.querySelector("#min-area-ratio").value) / 100),
  );

  button.disabled = true;
  button.textContent = "Analizando...";
  message.textContent = "";
  results.replaceChildren();
  try {
    const response = await fetch("/api/analyze", { method: "POST", body: formData });
    const body = await response.json();
    if (!response.ok) {
      const detail = body.detail;
      const errorText = Array.isArray(detail)
        ? detail.map(issue => issue.msg).join(", ")
        : typeof detail === "string" ? detail : "No se pudo procesar la solicitud.";
      throw new Error(errorText);
    }
    body.results.forEach(item => results.append(createResultCard(item)));
    const successes = body.results.filter(item => item.status === "ok").length;
    resultCount.textContent = `${successes} de ${body.results.length} imagen(es) detectadas`;
    if (!successes) message.textContent = "No se detectaron hojas. Proba ajustar HSV o usar un fondo contrastante.";
  } catch (error) {
    message.textContent = error.message || "Ocurrio un error al analizar las imagenes.";
  } finally {
    button.disabled = false;
    button.innerHTML = 'Analizar imagenes <span aria-hidden="true">→</span>';
  }
});

checkServer();
