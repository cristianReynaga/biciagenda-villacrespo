import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from services.weather_service import get_villa_crespo_weather
from services.ecobici_service import get_villa_crespo_ecobici_stations
from services.places_service import get_villa_crespo_places
from services.routing_service import planificar_itinerario
from services.groq_service import generar_sintesis_itinerario

BASE_DIR = Path(__file__).resolve().parent
CICLOVIAS_GEOJSON_PATH = BASE_DIR / "data" / "ciclovias_villacrespo.geojson"

app = FastAPI(
    title="BiciAgenda Villa Crespo",
    description="Planificador inteligente de microrrutas en Ecobici con agenda cultural, clima y Groq Llama-3.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanRequest(BaseModel):
    origen_station_id: str
    tiempo_ida_min: float = 15.0
    paradas_ids: List[int] = []
    tiempo_vuelta_min: float = 15.0
    destino_station_id: Optional[str] = None
    groq_api_key: Optional[str] = None

@app.get("/api/clima")
def api_clima():
    """Retorna clima actual, pronóstico de lluvia, radiación UV y alertas de calor."""
    return get_villa_crespo_weather()

@app.get("/api/ecobicis")
def api_ecobicis():
    """Retorna estaciones de Ecobici en Villa Crespo con disponibilidad en tiempo real."""
    return get_villa_crespo_ecobici_stations()

@app.get("/api/lugares")
def api_lugares():
    """Retorna los espacios culturales, galerías, cafés y plazas con sombra de Villa Crespo."""
    return get_villa_crespo_places()

@app.get("/api/ciclovias")
def api_ciclovias():
    """Retorna el GeoJSON de la red de ciclovías de Villa Crespo."""
    if not CICLOVIAS_GEOJSON_PATH.exists():
        raise HTTPException(status_code=404, detail="GeoJSON de ciclovías no encontrado")
    with open(CICLOVIAS_GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/planificar")
def api_planificar(req: PlanRequest):
    """Calcula el itinerario multi-parada y genera la síntesis con IA."""
    clima = get_villa_crespo_weather()
    itinerario = planificar_itinerario(
        origen_station_id=req.origen_station_id,
        tiempo_ida_min=req.tiempo_ida_min,
        paradas_ids=req.paradas_ids,
        tiempo_vuelta_min=req.tiempo_vuelta_min,
        destino_station_id=req.destino_station_id
    )
    sintesis = generar_sintesis_itinerario(
        itinerario=itinerario,
        clima=clima,
        user_api_key=req.groq_api_key
    )
    return {
        "clima": clima,
        "itinerario": itinerario,
        "sintesis_ia": sintesis
    }

# Montar frontend estático
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8095, reload=True)
