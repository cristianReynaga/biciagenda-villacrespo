import urllib.request
import json
from datetime import datetime

VILLA_CRESPO_LAT = -34.6037
VILLA_CRESPO_LON = -58.4420

def get_villa_crespo_weather():
    """
    Obtiene el clima en tiempo real y pronóstico horario para Villa Crespo
    mediante Open-Meteo (gratuito, sin API key).
    Calcula:
      - Métricas actuales (temperatura, sensación térmica, lluvia, viento, UV).
      - Horario límite recomendado para salir (por lluvia o calor extremo).
      - Recomendaciones térmicas y de sombra.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={VILLA_CRESPO_LAT}&longitude={VILLA_CRESPO_LON}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,precipitation_probability,uv_index,weather_code"
        f"&timezone=America%2FArgentina%2FBuenos_Aires&forecast_days=1"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BiciAgenda/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Fallback offline si falla la conexión
        return {
            "estado": "offline_fallback",
            "temperatura": 21.0,
            "sensacion": 21.0,
            "lluvia_actual_mm": 0.0,
            "viento_kmh": 10.0,
            "uv_max": 4.0,
            "hora_limite_salida": "Sin restricciones inmediatas",
            "alerta_calor": "Clima templado. Condiciones favorables para pedalear.",
            "recomendaciones": ["Llevar hidratación básica.", "Rutas arboladas recomendadas."],
            "sombra_prioritaria": True
        }

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    temp = current.get("temperature_2m", 20.0)
    apparent_temp = current.get("apparent_temperature", temp)
    rain_mm = current.get("precipitation", 0.0)
    wind_kmh = current.get("wind_speed_10m", 8.0)
    weather_code = current.get("weather_code", 0)

    # Análisis del pronóstico para calcular hasta qué hora pedalear
    times = hourly.get("time", [])
    rain_probs = hourly.get("precipitation_probability", [])
    uv_indices = hourly.get("uv_index", [])
    hourly_temps = hourly.get("temperature_2m", [])

    now = datetime.now()
    current_hour = now.hour

    hora_limite = "Podes salir en cualquier momento de las próximas 4 horas."
    alerta_lluvia = None

    # Buscar lluvia en las próximas 6 horas
    for i, t_str in enumerate(times):
        try:
            h = int(t_str.split("T")[1].split(":")[0])
            if h >= current_hour and h <= current_hour + 6:
                prob = rain_probs[i] if i < len(rain_probs) else 0
                if prob >= 50:
                    hora_limite = f"Salir antes de las {h:02d}:00 h (probabilidad de lluvia de {prob}%)."
                    alerta_lluvia = f"Lluvia prevista a partir de las {h:02d}:00 h ({prob}%)."
                    break
        except Exception:
            continue

    # Recomendaciones según calor y radiación UV
    recomendaciones = []
    uv_max = max(uv_indices) if uv_indices else 3.0

    if temp >= 28.0 or apparent_temp >= 30.0:
        alerta_calor = f"ALERTA CALOR: {temp}°C (Sensación {apparent_temp}°C). Alto estrés térmico."
        recomendaciones.append("Pedalear por corredores con arbolado tupido (Calles Gurruchaga, Padilla y Loyola).")
        recomendaciones.append("Hacer paradas obligatorias de hidratación cada 15-20 min.")
        recomendaciones.append("Evitar tramos de asfalto abierto sobre Av. Juan B. Justo o Av. Corrientes en horario central.")
        recomendaciones.append("Paradas con sombra sugeridas: Plaza Benito Nazar y Plaza 24 de Septiembre.")
        sombra_prioritaria = True
        if current_hour >= 11 and current_hour <= 16:
            hora_limite = "Precaución: pico de radiación y calor. Se sugiere retrasar el paseo para después de las 17:00 h."
    elif temp <= 12.0:
        alerta_calor = f"Clima fresco/frío: {temp}°C. Sensación {apparent_temp}°C."
        recomendaciones.append("Llevar abrigo cortaviento y guantes para el pedaleo nocturno/matutino.")
        recomendaciones.append("El asfalto puede estar húmedo en esquinas con sombra prolongada.")
        sombra_prioritaria = False
    else:
        alerta_calor = f"Clima muy agradable: {temp}°C. Condiciones óptimas para bicicleta."
        recomendaciones.append("Clima ideal para paseos combinados con cafeterías o muestras culturales.")
        recomendaciones.append("Llevar agua y candado si dejas la bici en paradas intermedias.")
        sombra_prioritaria = False

    if uv_max >= 6.0 and (10 <= current_hour <= 16):
        recomendaciones.append(f"Índice UV elevado ({uv_max}). Usar protector solar y buscar sombra.")

    return {
        "temperatura": temp,
        "sensacion": apparent_temp,
        "lluvia_actual_mm": rain_mm,
        "viento_kmh": wind_kmh,
        "weather_code": weather_code,
        "uv_max": uv_max,
        "alerta_calor": alerta_calor,
        "alerta_lluvia": alerta_lluvia,
        "hora_limite_salida": hora_limite,
        "recomendaciones": recomendaciones,
        "sombra_prioritaria": sombra_prioritaria,
        "plazas_sombra_villa_crespo": [
            {"nombre": "Plaza Benito Nazar", "beneficio": "Jacarandás y tipas frondosas con bebederos y bancos."},
            {"nombre": "Plaza 24 de Septiembre", "beneficio": "Gran cobertura vegetal, descanso térmico y ciclovía."},
            {"nombre": "Parque Centenario (Perímetro)", "beneficio": "Máxima densidad de sombra del área."}
        ]
    }
