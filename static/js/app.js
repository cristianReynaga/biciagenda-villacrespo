// BiciAgenda Villa Crespo - Frontend Controller
let map;
let cicloviasLayer;
let stationsData = [];
let placesData = [];
let selectedStops = []; // IDs de paradas intermedias
let routePolylineLayer = null;

// Centro de Villa Crespo
const VILLA_CRESPO_CENTER = [-34.5985, -58.4410];

document.addEventListener("DOMContentLoaded", async () => {
  initMap();
  setupEventListeners();
  await loadWeather();
  await loadCiclovias();
  await loadStations();
  await loadPlaces();

  // Seleccionar 2 paradas por defecto iniciales (1 cultural, 1 café)
  if (placesData.length >= 2) {
    addStopToState(1); // Ruth Benzacar
    addStopToState(8); // Cuervo Café
  }
});

function initMap() {
  map = L.map("map", {
    zoomControl: false
  }).setView(VILLA_CRESPO_CENTER, 15);

  L.control.zoom({ position: "topright" }).addTo(map);

  // CartoDB Dark Matter / Positron
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> & OpenStreetMap',
    maxZoom: 19
  }).addTo(map);
}

function setupEventListeners() {
  // Sliders tiempo ida y vuelta
  const sliderIda = document.getElementById("tiempoIda");
  const valIda = document.getElementById("valTiempoIda");
  sliderIda.addEventListener("input", (e) => {
    valIda.textContent = `${e.target.value} min`;
  });

  const sliderVuelta = document.getElementById("tiempoVuelta");
  const valVuelta = document.getElementById("valTiempoVuelta");
  sliderVuelta.addEventListener("input", (e) => {
    valVuelta.textContent = `${e.target.value} min`;
  });

  // Modal paradas
  const btnAddStop = document.getElementById("btnAddStop");
  const stopModal = document.getElementById("stopModal");
  const btnModalClose = document.getElementById("btnModalClose");

  btnAddStop.addEventListener("click", () => {
    renderModalPlaces("all");
    stopModal.style.display = "flex";
  });

  btnModalClose.addEventListener("click", () => {
    stopModal.style.display = "none";
  });

  // Filtros del modal
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      renderModalPlaces(e.target.dataset.filter);
    });
  });

  // Cerrar resultado AI
  document.getElementById("btnCloseResult").addEventListener("click", () => {
    document.getElementById("aiResultCard").style.display = "none";
  });

  // Form submit
  document.getElementById("routeForm").addEventListener("submit", handleFormSubmit);
}

// 1. CARGA DE CLIMA Y HORARIOS
async function loadWeather() {
  try {
    const res = await fetch("/api/clima");
    const data = await res.json();

    document.getElementById("wTemp").textContent = Math.round(data.temperatura);
    document.getElementById("wFeel").textContent = `Sensación ${Math.round(data.sensacion)}°C`;
    
    const statusIcon = data.lluvia_actual_mm > 0 ? "fa-cloud-showers-heavy" : "fa-sun";
    document.getElementById("wStatus").innerHTML = `<i class="fa-solid ${statusIcon}"></i> ${data.lluvia_actual_mm > 0 ? "Lluvia" : "Despejado"}`;

    document.getElementById("wLimitText").innerHTML = `<strong>Hasta qué hora salir:</strong> ${data.hora_limite_salida}`;
    document.getElementById("wTipText").innerHTML = `<strong>Confort y Sombra:</strong> ${data.alerta_calor}`;
  } catch (err) {
    console.error("Error cargando clima:", err);
  }
}

// 2. CARGA DE CICLOVÍAS EN MAPA
async function loadCiclovias() {
  try {
    const res = await fetch("/api/ciclovias");
    const geojsonData = await res.json();

    cicloviasLayer = L.geoJSON(geojsonData, {
      style: {
        color: "#10b981",
        weight: 3.5,
        opacity: 0.85
      },
      onEachFeature: (feature, layer) => {
        const nom = feature.properties.nombre || "Ciclovía";
        layer.bindTooltip(`🚲 Ciclovía: ${nom}`, { sticky: true });
      }
    }).addTo(map);
  } catch (err) {
    console.error("Error cargando ciclovías:", err);
  }
}

// 3. CARGA DE ESTACIONES ECOBICI
async function loadStations() {
  try {
    const res = await fetch("/api/ecobicis");
    stationsData = await res.json();

    const select = document.getElementById("originStation");
    select.innerHTML = "";

    stationsData.forEach(st => {
      // Poblar Select
      const opt = document.createElement("option");
      opt.value = st.station_id;
      opt.textContent = `${st.nombre} (${st.bicis_disponibles} bicis / ${st.anclajes_libres} anclajes)`;
      select.appendChild(opt);

      // Marcador en Mapa
      const marker = L.circleMarker([st.lat, st.lon], {
        radius: 7,
        fillColor: "#f59e0b",
        color: "#ffffff",
        weight: 2,
        fillOpacity: 0.95
      }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: inherit; font-size: 13px;">
          <strong style="color: #d97706;">🚲 ${st.nombre}</strong><br>
          <small>${st.direccion}</small><br>
          <div style="margin-top: 6px; display: flex; gap: 8px;">
            <span style="background: #ecfdf5; color: #047857; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
              ${st.bicis_disponibles} bicis libres
            </span>
            <span style="background: #eff6ff; color: #1d4ed8; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
              ${st.anclajes_libres} anclajes
            </span>
          </div>
        </div>
      `);
    });

    if (stationsData.length > 0) {
      document.getElementById("originStatusText").textContent = 
        `🟢 ${stationsData.length} estaciones monitoreadas en tiempo real`;
    }
  } catch (err) {
    console.error("Error cargando estaciones:", err);
  }
}

// 4. CARGA DE LUGARES CULTURALES / CAFÉS
async function loadPlaces() {
  try {
    const res = await fetch("/api/lugares");
    placesData = await res.json();

    placesData.forEach(p => {
      let color = "#8b5cf6"; // Cultura
      let icon = "🎨";
      if (p.tipo.includes("cafe")) {
        color = "#f97316";
        icon = "☕";
      } else if (p.tipo.includes("plaza")) {
        color = "#22c55e";
        icon = "🌳";
      }

      const marker = L.circleMarker([p.lat, p.lon], {
        radius: 8,
        fillColor: color,
        color: "#ffffff",
        weight: 2,
        fillOpacity: 0.95
      }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: inherit; font-size: 13px; max-width: 220px;">
          <strong>${icon} ${p.nombre}</strong><br>
          <span style="font-size: 11px; color: #64748b;">${p.direccion}</span><br>
          <p style="margin: 6px 0; font-size: 12px;">${p.descripcion}</p>
          ${p.tiene_sombra ? '<small style="color: #16a34a; font-weight: 600;">🌿 Cuenta con buena sombra / reparo</small>' : ''}
          <div style="margin-top: 8px;">
            <button onclick="addStopFromMap(${p.id})" style="background: #6366f1; color: white; border: none; padding: 4px 8px; border-radius: 6px; font-size: 11px; cursor: pointer;">
              + Agregar al recorrido
            </button>
          </div>
        </div>
      `);
    });
  } catch (err) {
    console.error("Error cargando lugares:", err);
  }
}

// GESTIÓN DE PARADAS DINÁMICAS
function addStopFromMap(id) {
  addStopToState(id);
  map.closePopup();
}

function addStopToState(id) {
  if (selectedStops.includes(id)) {
    alert("Este lugar ya está agregado al recorrido.");
    return;
  }
  selectedStops.push(id);
  renderStopsList();
}

function removeStop(id) {
  selectedStops = selectedStops.filter(sId => sId !== id);
  renderStopsList();
}

function renderStopsList() {
  const container = document.getElementById("stopsContainer");
  container.innerHTML = "";

  if (selectedStops.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: #94a3b8; text-align: center; padding: 8px;">No hay paradas seleccionadas. Hacé clic en "Agregar Parada" o en el mapa.</div>`;
    return;
  }

  selectedStops.forEach((id, idx) => {
    const place = placesData.find(p => p.id === id);
    if (!place) return;

    const div = document.createElement("div");
    div.className = "stop-item";
    div.innerHTML = `
      <div class="stop-item-left">
        <span class="stop-badge-idx">${idx + 1}</span>
        <div>
          <div class="stop-title">${place.nombre}</div>
          <div class="stop-sub">${place.direccion} • ${place.tiene_sombra ? '🌿 Sombra' : '☀️ Sol directo'}</div>
        </div>
      </div>
      <button type="button" class="btn-remove-stop" onclick="removeStop(${id})">
        <i class="fa-solid fa-trash-can"></i>
      </button>
    `;
    container.appendChild(div);
  });
}

function renderModalPlaces(filter) {
  const list = document.getElementById("modalPlacesList");
  list.innerHTML = "";

  const filtered = placesData.filter(p => {
    if (filter === "cafe") return p.tipo.includes("cafe");
    if (filter === "cultura") return p.tipo.includes("arte") || p.tipo.includes("cultural") || p.tipo.includes("teatro") || p.tipo.includes("museo");
    if (filter === "sombra") return p.tiene_sombra && p.tipo.includes("plaza");
    return true;
  });

  filtered.forEach(p => {
    const card = document.createElement("div");
    card.className = "place-card-select";
    card.innerHTML = `
      <div class="place-card-title">
        <span>${p.nombre}</span>
        <span class="place-badge-type">${p.tipo.replace('_', ' ')}</span>
      </div>
      <div class="place-card-desc">${p.descripcion}</div>
      ${p.tiene_sombra ? '<div class="place-card-shade"><i class="fa-solid fa-leaf"></i> Arbolado y sombra asegurada</div>' : ''}
    `;
    card.addEventListener("click", () => {
      addStopToState(p.id);
      document.getElementById("stopModal").style.display = "none";
    });
    list.appendChild(card);
  });
}

// 5. SUBMIT Y SÍNTESIS DE RUTA
async function handleFormSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById("btnSubmit");
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Calculando con IA...`;
  btn.disabled = true;

  const payload = {
    origen_station_id: document.getElementById("originStation").value,
    tiempo_ida_min: parseFloat(document.getElementById("tiempoIda").value),
    paradas_ids: selectedStops,
    tiempo_vuelta_min: parseFloat(document.getElementById("tiempoVuelta").value),
    groq_api_key: document.getElementById("groqKey").value.trim() || null
  };

  try {
    const res = await fetch("/api/planificar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStringify(payload)
    });
    const result = await res.json();
    displayResults(result);
  } catch (err) {
    console.error("Error al planificar:", err);
    alert("Hubo un error calculando el itinerario.");
  } finally {
    btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Planificar con IA`;
    btn.disabled = false;
  }
}

function displayResults(data) {
  const resultCard = document.getElementById("aiResultCard");
  const content = document.getElementById("aiContent");
  const metrics = document.getElementById("routeMetrics");
  const badge = document.getElementById("aiBadge");

  badge.textContent = data.sintesis_ia.fuente;
  content.innerHTML = window.marked ? marked.parse(data.sintesis_ia.contenido) : data.sintesis_ia.contenido;

  metrics.innerHTML = `
    <div class="metric-box">
      <div class="metric-val">${data.itinerario.distancia_total_km} km</div>
      <div class="metric-lbl">Distancia total</div>
    </div>
    <div class="metric-box">
      <div class="metric-val">${data.itinerario.tiempo_total_pedaleo_min} min</div>
      <div class="metric-lbl">Pedaleo neto</div>
    </div>
    <div class="metric-box">
      <div class="metric-val">${data.itinerario.porcentaje_confort_sombra}%</div>
      <div class="metric-lbl">Confort sombra</div>
    </div>
    <div class="metric-box">
      <div class="metric-val">${data.itinerario.retorno.anclajes_libres} anclajes</div>
      <div class="metric-lbl">Retorno asegurado</div>
    </div>
  `;

  resultCard.style.display = "block";

  // Dibujar Polilínea en Mapa
  if (routePolylineLayer) {
    map.removeLayer(routePolylineLayer);
  }

  const routeCoords = [];
  data.itinerario.tramos.forEach(tramo => {
    routeCoords.push(tramo.coordenadas[0]);
    routeCoords.push(tramo.coordenadas[1]);
  });

  routePolylineLayer = L.polyline(routeCoords, {
    color: "#6366f1",
    weight: 5,
    dashArray: "8, 8",
    opacity: 0.9
  }).addTo(map);

  map.fitBounds(routePolylineLayer.getBounds(), { padding: [50, 50] });
}

function jsonStringify(obj) {
  return JSON.stringify(obj);
}
