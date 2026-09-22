# 🚲 BiciAgenda Villa Crespo

Planificador inteligente de microrrutas en Ecobici que combina **agenda cultural**, **cafeterías de especialidad**, **estaciones en tiempo real (GBFS)**, **monitoreo climático (Open-Meteo)** y síntesis contextual con **Groq (Llama-3.3-70B)**.

Desarrollado para la cátedra **K576 - Sistemas Generativos e IA para Diseño** (Universidad de San Andrés).

---

## 🎯 Características Principales

* **Foco Territorial:** Recorte urbano especializado en **Villa Crespo**, Buenos Aires.
* **Control de Tiempos Asimétricos:** Permite definir de forma independiente el tiempo presupuestado de ida (5 a 35 min) y el de vuelta.
* **Itinerarios Multi-Parada Flexibles:** Podés agregar una, dos o múltiples paradas intermedias (galerías de arte, cafés de especialidad, teatros independientes o plazas con sombra).
* **Ecobicis en Tiempo Real:** Conexión directa al feed GBFS oficial con monitoreo de bicicletas libres en el origen y **anclajes garantizados en la estación de retorno**.
* **Inteligencia Climática y Térmica (Open-Meteo):**
  * Predicción de **hasta qué hora salir a pedalear** antes de precipitaciones o picos de radiación UV.
  * Alertas de estrés térmico, sugerencia de hidratación y priorización de corredores con sombra (calles Gurruchaga, Padilla y Loyola).
* **Curaduría Generativa con Groq:** Síntesis narrativa del recorrido mediante Llama-3.3-70B (con fallback heurístico si no se provee API Key).
* **Visualizador Espacial (Leaflet):** Mapa con capas de ciclovías de Villa Crespo, estaciones de Ecobici y trazado dinámico de la ruta.

---

## 🛠️ Stack Tecnológico

* **Backend:** FastAPI (Python 3.11) asíncrono.
* **APIs:** Open-Meteo (Clima sin API Key) + GBFS v3.0 (Ecobicis GCBA/Tembici) + Groq Cloud API.
* **Frontend:** Vanilla JS / HTML5 / CSS3 moderno con Leaflet Maps y CartoDB Voyager Tiles.
* **Despliegue:** Docker y Docker Compose (puerto `8095`).

---

## 🚀 Despliegue Rápido con Docker

```bash
# 1. Clonar el repositorio
git clone https://github.com/cristianReynaga/biciagenda-villacrespo.git
cd biciagenda-villacrespo

# 2. Configurar variable de Groq (opcional)
cp .env.example .env
# Editar .env con tu GROQ_API_KEY si deseas síntesis con Llama-3

# 3. Levantar con Docker Compose
docker compose up -d --build
```

La aplicación quedará disponible en: `http://localhost:8095` (o en tu servidor local: `http://192.168.1.100:8095`).

---

## 🏛️ Dataset Cultural y Espacial
El dataset curado de Villa Crespo incluye referencias icónicas como:
* **Galerías y Centros:** Ruth Benzacar Galería de Arte, Centro Cultural Osvaldo Pugliese, Club Cultural Matienzo, El Gato Viejo (Taller Regazzoni), Espacio Moebius.
* **Cafés de Especialidad y Bares Notables:** Cuervo Café, LAB Tostadores, Café San Bernardo ("Sanber"), Malvón Bakery, Café Crespín, Falena Librería & Café.
* **Pulmones Verdes y Sombra:** Plaza Benito Nazar, Plaza 24 de Septiembre, Plazoleta San Bernardo y perímetro de Parque Centenario.
