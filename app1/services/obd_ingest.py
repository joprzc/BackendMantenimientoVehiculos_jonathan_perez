from django.db import connections, transaction
from django.utils import timezone

OBD_TABLE_NAME = "obd_data"

COLUMNS = [
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


def insert_obd_row(payload: dict) -> dict:
    """Inserta una fila en PostgreSQL (tabla obd_data).

    Retorna un dict con id y timestamp reales para depuración.
    - Si un PID no existe, llega como None y se inserta como NULL.
    """
    data = {k: payload.get(k) for k in COLUMNS}

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
