import os
import urllib.request
import json

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def generar_sintesis_itinerario(itinerario, clima, user_api_key=None):
    """
    Sintetiza la propuesta del itinerario cultural y recomendaciones
    climáticas utilizando Groq con Llama 3.3.
    Si no hay API key disponible, utiliza un motor heurístico inteligente.
    """
    api_key = user_api_key or os.getenv("GROQ_API_KEY", "").strip()

    paradas_nombres = " ➔ ".join([p["nombre"] for p in itinerario["paradas"]])
    origen_nom = itinerario["origen"]["nombre"]
    retorno_nom = itinerario["retorno"]["nombre"]
    dist_km = itinerario["distancia_total_km"]
    tiempo_min = itinerario["tiempo_total_pedaleo_min"]

    # Si hay API Key configurada, llamamos a Groq
    if api_key:
        prompt_sistema = (
            "Sos el asistente experto de 'BiciAgenda Villa Crespo', un curador urbano de recorridos "
            "en bicicleta y actividades culturales/gastronómicas en Buenos Aires. "
            "Tu tarea es redactar un itinerario conciso, atractivo, con recomendaciones precisas sobre "
            "el clima, horarios límites para salir, alertas de calor o hidratación, y consejos para pedalear por sombra. "
            "Mantené un tono fresco, práctico y con identidad porteña de Villa Crespo."
        )

        prompt_usuario = f"""
DATOS DEL RECORRIDO EN VILLA CRESPO:
- Estación de salida: {origen_nom} (Bicis libres: {itinerario['origen'].get('bicis_disponibles', 'Varios')})
- Paradas intermedias: {paradas_nombres}
- Estación de llegada: {retorno_nom} (Anclajes libres: {itinerario['retorno'].get('anclajes_libres', 'Varios')})
- Distancia total pedaleo: {dist_km} km ({tiempo_min} minutos netos)

CONDICIONES CLIMÁTICAS:
- Temperatura actual: {clima.get('temperatura')}°C (Sensación: {clima.get('sensacion')}°C)
- Alerta térmica: {clima.get('alerta_calor')}
- Ventana horaria límite: {clima.get('hora_limite_salida')}
- Recomendaciones de calor/sombra: {", ".join(clima.get('recomendaciones', []))}

Generá:
1. Título con onda del circuito.
2. Síntesis paso a paso de la experiencia (qué hacer en cada parada).
3. Advertencia climática / hasta qué hora salir y calles sugeridas con sombra.
4. Tip de anclaje de Ecobici.
"""

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            "temperature": 0.7,
            "max_tokens": 550
        }

        try:
            req = urllib.request.Request(
                GROQ_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "BiciAgenda/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                texto = result["choices"][0]["message"]["content"]
                return {
                    "fuente": "Groq Llama-3.3-70B",
                    "contenido": texto,
                    "modelo": DEFAULT_MODEL
                }
        except Exception as e:
            print(f"Fallo llamada a Groq: {e}. Activando fallback heurístico.")

    # Fallback heurístico inteligente
    clima_adv = clima.get("hora_limite_salida", "Sin límites inmediatos")
    calor_adv = clima.get("alerta_calor", "")
    recs = clima.get("recomendaciones", ["Pedalear con precaución"])

    texto_fallback = f"""### 🚲 Circuito Villa Crespo: {paradas_nombres}

**Resumen del Recorrido:**
* **Partida:** Desde `{origen_nom}`, desbloqueando tu Ecobici en minutos.
* **Tramos:** {len(itinerario['tramos'])} etapas cubriendo **{dist_km} km** (~{tiempo_min} min pedaleo neto).
* **Paradas:** {paradas_nombres}.
* **Llegada:** Anclaje seguro en `{retorno_nom}` ({itinerario['retorno'].get('anclajes_libres', 0)} anclajes confirmados).

**🌤️ Monitoreo Climático y Horario Sugerido:**
* **Horario límite:** {clima_adv}
* **Condición térmica:** {calor_adv}
* **Calles con sombra recomendadas:** Corredor de ciclovía de calle Gurruchaga, Padilla y Loyola. En caso de necesitar sombra o agua, pasar por Plaza Benito Nazar o Plaza 24 de Septiembre.
* **Consejos:** {recs[0] if recs else 'Llevar caramañola.'}

*(Nota: Podés configurar tu GROQ_API_KEY para síntesis generativa ultra personalizada con Llama-3).*"""

    return {
        "fuente": "Motor Heurístico Contextual (Configurá GROQ_API_KEY para Llama-3)",
        "contenido": texto_fallback,
        "modelo": "Heurístico Local"
    }
