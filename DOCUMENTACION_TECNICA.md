# Especificación Técnica: BiciAgenda Villa Crespo
## Arquitectura de Servicios, Endpoints, Flujo de Datos y Reglas de Negocio

Este documento detalla de manera exhaustiva cada servicio del sistema, sus endpoints REST, las fuentes de datos externas e internas, y todas las fórmulas y reglas lógicas empleadas para calcular itinerarios, confort térmico y disponibilidad en tiempo real.

---

## 1. Mapa de Endpoints de la API (FastAPI)

| Método | Endpoint | Descripción | Servicio Responsable |
| :--- | :--- | :--- | :--- |
| **GET** | `/` | Sirve la interfaz web SPA (Leaflet, JS, CSS). | `StaticFiles` (`/static`) |
| **GET** | `/api/clima` | Devuelve clima en vivo, alertas térmicas y hora límite. | `weather_service.py` |
| **GET** | `/api/ecobicis` | Devuelve estaciones de Villa Crespo con bicis y anclajes en tiempo real. | `ecobici_service.py` |
| **GET** | `/api/lugares` | Devuelve el catálogo curado de 18 espacios de Villa Crespo. | `places_service.py` |
| **GET** | `/api/ciclovias` | Devuelve el GeoJSON con los 677 segmentos de ciclovías de la zona. | `data/ciclovias_villacrespo.geojson` |
| **POST** | `/api/planificar` | Procesa el itinerario multi-parada y genera la síntesis con IA. | `routing_service.py` + `groq_service.py` |

---

## 2. Detalle de Servicios y Reglas de Cálculo

### 2.1. Servicio Meteorológico y Confort Térmico (`weather_service.py`)
* **Endpoint / Fuente Externa:** Open-Meteo REST API (gratuita, sin API key).
  ```text
  GET https://api.open-meteo.com/v1/forecast?latitude=-34.6037&longitude=-58.4420
      &current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m
      &hourly=temperature_2m,precipitation_probability,uv_index,weather_code
      &timezone=America/Argentina/Buenos_Aires&forecast_days=1
  ```
* **Coordenadas de Referencia:** Latitud `-34.6037`, Longitud `-58.4420` (Centro neurálgico de Villa Crespo).
* **Datos Extraídos:**
  * Variables instantáneas: Temperatura actual (°C), Sensación térmica (°C), Precipitación actual (mm), Velocidad del viento (km/h), Código de tiempo WMO.
  * Series horarias (24h): Probabilidad de lluvia por hora (%), Índice UV por hora (0-12), Temperatura por hora (°C).

#### Reglas de Inferencia y Cálculo:
1. **Regla de "Hasta qué hora salir":**
   * El algoritmo itera sobre la ventana horaria $[h_{\text{actual}}, h_{\text{actual}} + 6 \text{ horas}]$.
   * Si en alguna hora $h$ la probabilidad de lluvia es $\ge 50\%$, fija la hora límite:
     $$\text{Hora Límite} = \text{"Salir antes de las } h\text{:00 h (probabilidad de lluvia del } P\text{\%)"}$$
2. **Regla de Estrés Térmico y Calor:**
   * Si $T_{\text{actual}} \ge 28.0^\circ\text{C}$ o $T_{\text{aparente}} \ge 30.0^\circ\text{C}$:
     * Activa bandera `sombra_prioritaria = True`.
     * Inyecta advertencia de hidratación cada 15-20 min y recomienda transitar por calles arboladas (Gurruchaga, Padilla y Loyola).
     * Si la hora actual está entre las **11:00 y las 16:00 h**, advierte pico de insolación y aconseja retrasar la salida a después de las 17:00 h.
3. **Regla de Clima Frío:**
   * Si $T_{\text{actual}} \le 12.0^\circ\text{C}$:
     * Sugiere indumentaria cortaviento y advierte posible asfalto húmedo en esquinas de sombra permanente.
4. **Regla de Radiación UV:**
   * Si $\text{UV}_{\text{máx}} \ge 6.0$ y el horario está entre las 10:00 y las 16:00 h, exige protector solar y gafas.
5. **Inyección de Refugios de Sombra:**
   * Adjunta automáticamente los 3 pulmones verdes de sombra densa de Villa Crespo: Plaza Benito Nazar (jacarandás y tipas), Plaza 24 de Septiembre y perímetro de Parque Centenario.

---

### 2.2. Servicio de Ecobicis en Tiempo Real (`ecobici_service.py`)
* **Endpoint / Fuente Externa:** Feed oficial GBFS v3.0 (General Bikeshare Feed Specification) operado por Tembici / PBSC para el Gobierno de la Ciudad:
  * Metadatos de Estaciones: `https://buenosaires.publicbikesystem.net/customer/gbfs/v3.0/station_information`
  * Estado en Tiempo Real: `https://buenosaires.publicbikesystem.net/customer/gbfs/v3.0/station_status`
* **Datos Extraídos:**
  * `station_id`, `name`, `address`, `lat`, `lon`, `capacity`.
  * `num_vehicles_available` (bicis mecánicas y eléctricas disponibles).
  * `num_docks_available` (anclajes libres para devolver la bici).
  * `is_renting`, `is_returning`.

#### Reglas de Inferencia y Filtrado:
1. **Filtro Espacial de Villa Crespo:**
   * Delimita una caja envolvente (*Bounding Box*) que cubre el barrio y sus transiciones inmediatas:
     $$\text{Latitud}: [-34.615, -34.582] \quad\vert\quad \text{Longitud}: [-58.455, -58.423]$$
   * Retiene 33 estaciones activas dentro de este perímetro.
2. **Caché en Memoria (Rate Limiting Resilience):**
   * TTL de **60 segundos**. Si entran múltiples usuarios en simultáneo, se sirve el estado desde memoria RAM para no saturar los servidores del GCBA ni bloquear la respuesta.
3. **Fallback Offline:**
   * Si la red externa de Tembici no responde o arroja timeout (> 4 seg), conmuta automáticamente a un snapshot de 6 estaciones estratégicas de Villa Crespo (Malabia, Fitz Roy, Villarroel, Plaza Benito Nazar, Plaza 24 de Septiembre, Aráoz) para que la aplicación nunca se caiga.

---

### 2.3. Servicio de Lugares y Espacios (`places_service.py`)
* **Fuente de Datos:** CSV local curado (`data/villa_crespo_agenda.csv`).
* **Datos Extraídos:**
  * `id`: Identificador entero único.
  * `nombre`: Denominación del espacio.
  * `tipo`: `galeria_arte`, `centro_cultural`, `museo_taller`, `teatro`, `cafe_notable`, `cafe_especialidad`, `libreria_cafe`, `plaza_arbolada`.
  * `direccion`, `lat`, `lon`.
  * `horario`: Días y franjas de funcionamiento.
  * `descripcion`: Síntesis de la propuesta de valor cultural o gastronómica.
  * `tiene_sombra`: Booleano (`si` / `no`).
  * `recomendacion_calor`: Nota contextual de acondicionamiento térmico (ej. *local climatizado*, *patio con vegetación*, *exposición a cielo abierto*).

---

### 2.4. Servicio de Ruteo Multi-Parada (`routing_service.py`)
* **Entrada del Payload (`PlanRequest`):**
  * `origen_station_id`: ID de la estación Ecobici de salida (ej. `"70"`).
  * `tiempo_ida_min`: Tiempo presupuestado de ida en minutos (ej. `15.0`).
  * `paradas_ids`: Lista de IDs de paradas intermedias en orden (ej. `[1, 8]`).
  * `tiempo_vuelta_min`: Tiempo presupuestado de retorno en minutos (ej. `15.0`).
  * `destino_station_id`: (Opcional) ID de estación de llegada. Si es `null`, se autocalcula.

#### Fórmulas Matemáticas y Reglas de Ruteo:
1. **Distancia Geodésica Base (Fórmula de Haversine):**
   $$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
   $$d_{\text{haversine}} = 2 R \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1-a}\right) \quad (R = 6.371.000\text{ m})$$

2. **Corrección de Cuadrícula Urbana Porteña (Manhattan Factor):**
   * Las bicicletas no vuelan en línea recta sino que siguen la cuadrícula ortogonal de manzanas de Buenos Aires:
     $$D_{\text{real}} = d_{\text{haversine}} \times 1.25$$

3. **Modelo de Velocidad de Pedaleo:**
   * Se fija la velocidad promedio en Ecobici urbana a **$13.0\text{ km/h}$**:
     $$V_{\text{min}} = \frac{13.0 \times 1000}{60} \approx 216.67\text{ metros/minuto}$$
     $$T_{\text{pedaleo}} = \frac{D_{\text{real}}}{V_{\text{min}}}$$

4. **Regla de Estación de Retorno Garantizada:**
   * Si el usuario no selecciona una estación fija de regreso, el sistema toma las coordenadas de la última parada del recorrido ($P_{\text{última}}$).
   * Ordena todas las estaciones de Villa Crespo por distancia euclidiana hacia $P_{\text{última}}$.
   * **Condición de seguridad:** Selecciona la primera estación que cumpla:
     $$\text{anclajes\_libres} \ge 2$$
     *(Evita que el usuario llegue cansado y encuentre la estación 100% llena sin poder devolver la Ecobici).*

5. **Estructuración de Tramos (*Legs*):**
   * **Tramo 1 (Ida):** Estación Origen $\rightarrow$ Parada 1. Evalúa si $T_{\text{pedaleo}} \le \text{tiempo\_ida\_min}$.
   * **Tramos Intermedios:** Parada $i \rightarrow$ Parada $i+1$. Evalúa la conexión corta entre actividades.
   * **Tramo Final (Vuelta):** Última Parada $\rightarrow$ Estación Retorno. Evalúa si $T_{\text{pedaleo}} \le \text{tiempo\_vuelta\_min}$.

6. **Índice de Confort de Sombra del Recorrido:**
   $$\text{Confort Sombra (\%)} = \left(\frac{\sum \text{Paradas con } \text{tiene\_sombra}}{\text{Total de Paradas}}\right) \times 100$$

---

### 2.5. Servicio de Síntesis Generativa y Heurística (`groq_service.py`)

#### Modo A: Con Clave de Groq (Llama-3.3-70B)
* **Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
* **Modelo:** `llama-3.3-70b-versatile`
* **Parámetros:** `temperature: 0.7`, `max_tokens: 550`.
* **Prompt del Sistema:** Especializado en curaduría urbana, ciclismo en Buenos Aires y análisis de confort ambiental.
* **Inyección de Contexto Estructurado:**
  El modelo recibe en el prompt exactamente los valores numéricos calculados por los módulos determinísticos (estación, bicis disponibles, paradas, distancias en km, minutos netos, temperatura, horario límite de lluvia y calles con sombra). El LLM no calcula distancias ni inventa datos; **sintetiza la experiencia humana**.

#### Modo B: Sin Clave de Groq (Motor Heurístico Contextual de Respaldo)
* Si `GROQ_API_KEY` está vacía o si ocurre un fallo en la llamada HTTP a Groq:
* Se ejecuta un motor basado en reglas que construye el informe en Markdown combinando:
  * Resumen de etapas con distancias reales en km y minutos.
  * Inserción de la hora límite calculada por el servicio meteorológico.
  * Inserción condicional de las recomendaciones de calor/frío.
  * Advertencia de calles con arbolado y confirmación de anclajes de retorno garantizados.
* **Resultado:** La interfaz muestra el veredicto inmediatamente sin romperse ni arrojar pantallas de error.

---

## 3. Ejemplo de Payload de Entrada y Salida (`POST /api/planificar`)

### Request:
```json
{
  "origen_station_id": "70",
  "tiempo_ida_min": 15.0,
  "paradas_ids": [1, 8],
  "tiempo_vuelta_min": 15.0,
  "groq_api_key": null
}
```

### Response:
```json
{
  "clima": {
    "temperatura": 10.5,
    "sensacion": 7.9,
    "lluvia_actual_mm": 0.0,
    "viento_kmh": 6.0,
    "alerta_calor": "Clima fresco/frío: 10.5°C. Sensación 7.9°C.",
    "hora_limite_salida": "Podes salir en cualquier momento de las próximas 4 horas.",
    "sombra_prioritaria": false
  },
  "itinerario": {
    "origen": {
      "station_id": "70",
      "nombre": "070 - ARAOZ",
      "bicis_disponibles": 4,
      "anclajes_libres": 16
    },
    "retorno": {
      "station_id": "101",
      "nombre": "101 - Fitz Roy",
      "bicis_disponibles": 8,
      "anclajes_libres": 12
    },
    "paradas": [
      { "id": 1, "nombre": "Ruth Benzacar Galería de Arte", "tipo": "galeria_arte" },
      { "id": 8, "nombre": "Cuervo Café", "tipo": "cafe_especialidad" }
    ],
    "tramos": [
      {
        "tipo_tramo": "ida",
        "desde": "Ecobici: 070 - ARAOZ",
        "hasta": "Ruth Benzacar Galería de Arte",
        "distancia_m": 2043.0,
        "tiempo_pedaleo_min": 9.4,
        "alerta_tiempo": "Tiempo holgado"
      },
      {
        "tipo_tramo": "intermedio",
        "desde": "Ruth Benzacar Galería de Arte",
        "hasta": "Cuervo Café",
        "distancia_m": 1052.0,
        "tiempo_pedaleo_min": 4.9,
        "alerta_tiempo": "Conexión corta entre actividades"
      },
      {
        "tipo_tramo": "vuelta",
        "desde": "Cuervo Café",
        "hasta": "Ecobici: 101 - Fitz Roy (12 anclajes libres)",
        "distancia_m": 1032.0,
        "tiempo_pedaleo_min": 4.8,
        "alerta_tiempo": "Tiempo de retorno óptimo"
      }
    ],
    "tiempo_total_pedaleo_min": 19.1,
    "distancia_total_km": 4.13,
    "porcentaje_confort_sombra": 100.0,
    "anclajes_garantizados_retorno": true
  },
  "sintesis_ia": {
    "fuente": "Motor Heurístico Contextual (Configurá GROQ_API_KEY para Llama-3)",
    "modelo": "Heurístico Local",
    "contenido": "### 🚲 Circuito Villa Crespo: Ruth Benzacar ➔ Cuervo Café..."
  }
}
```
