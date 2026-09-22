import math
from services.places_service import get_villa_crespo_places
from services.ecobici_service import get_villa_crespo_ecobici_stations

VELOCIDAD_BICI_KMH = 13.0  # Velocidad promedio urbana en Ecobici
VELOCIDAD_METROS_MINUTO = (VELOCIDAD_BICI_KMH * 1000.0) / 60.0  # ~216.6 m/min
FACTOR_CUADRICULA_CABA = 1.25  # Factor para convertir distancia recta en distancia Manhattan real

def haversine_dist(lat1, lon1, lat2, lon2):
    """Calcula distancia en metros entre dos coordenadas geográficas."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calcular_tiempo_pedaleo(dist_metros):
    """Calcula minutos de pedaleo considerando la cuadrícula de calles porteñas."""
    dist_real = dist_metros * FACTOR_CUADRICULA_CABA
    minutos = dist_real / VELOCIDAD_METROS_MINUTO
    return round(minutos, 1), round(dist_real, 0)

def planificar_itinerario(origen_station_id, tiempo_ida_min, paradas_ids, tiempo_vuelta_min, destino_station_id=None):
    """
    Planifica un itinerario multi-parada en Villa Crespo:
    1. Origen: Estación Ecobici de salida.
    2. N Paradas intermedias: Espacios culturales, cafés o plazas.
    3. Retorno: Estación Ecobici de destino (con anclajes libres).
    """
    estaciones = get_villa_crespo_ecobici_stations()
    lugares = {p["id"]: p for p in get_villa_crespo_places()}

    # Encontrar estación origen
    st_origen = next((s for s in estaciones if str(s["station_id"]) == str(origen_station_id)), None)
    if not st_origen and estaciones:
        st_origen = estaciones[0]

    # Resolver paradas intermedias
    puntos_paradas = []
    for pid in paradas_ids:
        try:
            pid_int = int(pid)
            if pid_int in lugares:
                puntos_paradas.append(lugares[pid_int])
        except Exception:
            continue

    # Si no envió paradas, seleccionar 2 por defecto (1 cultural + 1 café)
    if not puntos_paradas:
        cult = next((l for l in lugares.values() if "arte" in l["tipo"] or "cultural" in l["tipo"]), None)
        cafe = next((l for l in lugares.values() if "cafe" in l["tipo"]), None)
        if cult: puntos_paradas.append(cult)
        if cafe: puntos_paradas.append(cafe)

    # Estación de retorno
    st_retorno = None
    if destino_station_id:
        st_retorno = next((s for s in estaciones if str(s["station_id"]) == str(destino_station_id)), None)
    
    # Si no se especificó o es la misma, buscar la más cercana a la última parada con anclajes libres
    ultima_parada = puntos_paradas[-1] if puntos_paradas else st_origen
    if not st_retorno:
        # Ordenar estaciones por cercanía a la última parada que tengan al menos 2 anclajes libres
        candidatas = sorted(
            estaciones,
            key=lambda s: haversine_dist(ultima_parada["lat"], ultima_parada["lon"], s["lat"], s["lon"])
        )
        st_retorno = next((s for s in candidatas if s.get("anclajes_libres", 0) >= 2), candidatas[0])

    # Calcular tramos (Legs)
    tramos = []
    tiempo_total_pedaleo = 0.0
    distancia_total_metros = 0.0

    # Tramo 1: Origen -> Primer parada
    primera_parada = puntos_paradas[0]
    d1 = haversine_dist(st_origen["lat"], st_origen["lon"], primera_parada["lat"], primera_parada["lon"])
    t1_min, d1_real = calcular_tiempo_pedaleo(d1)
    tramos.append({
        "tipo_tramo": "ida",
        "desde": f"Ecobici: {st_origen['nombre']}",
        "hasta": primera_parada["nombre"],
        "distancia_m": d1_real,
        "tiempo_pedaleo_min": t1_min,
        "tiempo_presupuestado_min": tiempo_ida_min,
        "coordenadas": [[st_origen["lat"], st_origen["lon"]], [primera_parada["lat"], primera_parada["lon"]]],
        "alerta_tiempo": "Tiempo holgado" if t1_min <= tiempo_ida_min else f"Excede ida por {round(t1_min - tiempo_ida_min, 1)} min"
    })
    tiempo_total_pedaleo += t1_min
    distancia_total_metros += d1_real

    # Tramos intermedios entre paradas
    for i in range(len(puntos_paradas) - 1):
        p_desde = puntos_paradas[i]
        p_hasta = puntos_paradas[i+1]
        dm = haversine_dist(p_desde["lat"], p_desde["lon"], p_hasta["lat"], p_hasta["lon"])
        tm_min, dm_real = calcular_tiempo_pedaleo(dm)
        tramos.append({
            "tipo_tramo": "intermedio",
            "desde": p_desde["nombre"],
            "hasta": p_hasta["nombre"],
            "distancia_m": dm_real,
            "tiempo_pedaleo_min": tm_min,
            "tiempo_presupuestado_min": 10.0,
            "coordenadas": [[p_desde["lat"], p_desde["lon"]], [p_hasta["lat"], p_hasta["lon"]]],
            "alerta_tiempo": "Conexión corta entre actividades"
        })
        tiempo_total_pedaleo += tm_min
        distancia_total_metros += dm_real

    # Tramo final: Última parada -> Estación Ecobici de retorno
    dfinal = haversine_dist(ultima_parada["lat"], ultima_parada["lon"], st_retorno["lat"], st_retorno["lon"])
    tfinal_min, dfinal_real = calcular_tiempo_pedaleo(dfinal)
    tramos.append({
        "tipo_tramo": "vuelta",
        "desde": ultima_parada["nombre"],
        "hasta": f"Ecobici: {st_retorno['nombre']} ({st_retorno['anclajes_libres']} anclajes libres)",
        "distancia_m": dfinal_real,
        "tiempo_pedaleo_min": tfinal_min,
        "tiempo_presupuestado_min": tiempo_vuelta_min,
        "coordenadas": [[ultima_parada["lat"], ultima_parada["lon"]], [st_retorno["lat"], st_retorno["lon"]]],
        "alerta_tiempo": "Tiempo de retorno óptimo" if tfinal_min <= tiempo_vuelta_min else f"Excede retorno por {round(tfinal_min - tiempo_vuelta_min, 1)} min"
    })
    tiempo_total_pedaleo += tfinal_min
    distancia_total_metros += dfinal_real

    # Score de confort del itinerario
    sombra_count = sum(1 for p in puntos_paradas if p.get("tiene_sombra"))
    porcentaje_sombra = round((sombra_count / len(puntos_paradas)) * 100, 0) if puntos_paradas else 50

    return {
        "origen": st_origen,
        "retorno": st_retorno,
        "paradas": puntos_paradas,
        "tramos": tramos,
        "tiempo_total_pedaleo_min": round(tiempo_total_pedaleo, 1),
        "distancia_total_km": round(distancia_total_metros / 1000.0, 2),
        "porcentaje_confort_sombra": porcentaje_sombra,
        "anclajes_garantizados_retorno": st_retorno.get("anclajes_libres", 0) >= 1
    }
