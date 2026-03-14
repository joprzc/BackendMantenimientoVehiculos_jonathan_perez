from __future__ import annotations
from typing import Any, Dict, Optional

from django.utils import timezone
from django.db import connections, transaction
from app1.models import Vehiculo

from django.conf import settings

# ======================== PRODUCCION ==================================
OBD_TABLE_NAME = "obd_data"

COLUMNS = [
    "vehiculo_id",
    "timestamp",
    "vehicle_code",
    "engine_rpm",
    "vehicle_speed_kph",
    "engine_temp_c",
    "oil_pressure_psi",
    "battery_voltage_v",
    "fuel_level_percent",
    "engine_failure_imminent",
]


# En el endpoint, guardar vehiculo_id si existe obd_code
def resolve_vehiculo_id(vehicle_code: str):
    if not vehicle_code:
        return None
    v = Vehiculo.objects.filter(obd_code=vehicle_code).only("id").first()
    return v.id if v else None


def insert_obd_row(payload: dict) -> dict:
    """Inserta una fila en PostgreSQL (tabla obd_data).

    Retorna un dict con id y timestamp reales para depuración.
    - Si un PID no existe, llega como None y se inserta como NULL.
    """
    # Si está habilitado el modo DEMO, rellena métricas faltantes (None) con defaults
    # Esto NO afecta producción si OBD_DEMO_FILL_MISSING=False
    payload = apply_demo_defaults_if_enabled(dict(payload))

    # ---- flujo ----
    # collector → endpoint → service → resolve_vehiculo_id → insert SQL con vehiculo_id
    data = {k: payload.get(k) for k in COLUMNS}

    # Resolver vehiculo_id automáticamente según vehicle_code
    vehiculo_id = resolve_vehiculo_id(payload.get("vehicle_code"))
    data["vehiculo_id"] = vehiculo_id

    # normalización mínima: si timestamp llega vacío, now()
    if not data.get("timestamp"):
        data["timestamp"] = timezone.now()

    cols_sql = ", ".join(COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    values = [data[c] for c in COLUMNS]

    # Importante: RETURNING requiere PostgreSQL (tu caso)
    sql = (
        f"INSERT INTO {OBD_TABLE_NAME} ({cols_sql}) "
        f"VALUES ({placeholders}) RETURNING id, timestamp"
    )

    with transaction.atomic():
        with connections["default"].cursor() as cursor:
            cursor.execute(sql, values)
            row = cursor.fetchone()  # (id, timestamp)

    return {"id": row[0] if row else None, "timestamp": row[1] if row else None}


# ======================= DEMO (rellenar nulls) ==================================
DEMO_DEFAULTS = {
    "engine_rpm": 900.0,
    "engine_temp_c": 85.0,
    "fuel_level_percent": 50.0,
    "battery_voltage_v": 13.6,
    "engine_failure_imminent": False,
    "vehicle_speed_kph": 0.0,
    "coolant_temp_c": 80.0,
    "oil_pressure_psi": 45.0,
}


def apply_demo_defaults_if_enabled(payload: dict) -> dict:
    if not getattr(settings, "OBD_DEMO_FILL_MISSING", False):
        return payload
    for k, v in DEMO_DEFAULTS.items():
        if payload.get(k) is None:
            payload[k] = v
    return payload
