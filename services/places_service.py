import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "villa_crespo_agenda.csv"

def get_villa_crespo_places():
    """
    Lee y estructura los lugares culturales, cafes y plazas de Villa Crespo.
    """
    places = []
    if not CSV_PATH.exists():
        return places

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            places.append({
                "id": int(row["id"]),
                "nombre": row["nombre"],
                "tipo": row["tipo"],
                "direccion": row["direccion"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "horario": row["horario"],
                "descripcion": row["descripcion"],
                "tiene_sombra": row["tiene_sombra"].lower() == "si",
                "recomendacion_calor": row["recomendacion_calor"]
            })
    return places
