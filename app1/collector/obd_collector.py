import os
import time

import random
from datetime import datetime, timezone

import requests
import obd  # pip install obd

# =============================
# CONFIG (ENV)
# =============================
API_URL = os.getenv("OBD_API_URL", "http://127.0.0.1:8000/api/obd/ingest/")
INGEST_KEY = os.getenv("OBD_INGEST_API_KEY", "")
# VEHICLE_CODE = os.getenv("OBD_VEHICLE_CODE", "DEMO-000")
# vehicle_code debe ser la placa real del vehiculo registrado
VEHICLE_CODE = os.getenv("OBD_VEHICLE_CODE", "").strip().upper()
OBD_PORT = os.getenv(
    "OBD_PORT", None
)  # o un puerto específico como "COM3" o "/dev/ttyUSB0"
INTERVAL_SECONDS = float(os.getenv("OBD_INTERVAL_SECONDS", "5.0"))

FIXED_TIMESTAMP = os.getenv("OBD_FIXED_TIMESTAMP", "").strip()
SEND_ONCE = os.getenv("OBD_SEND_ONCE", "0") == "1"
DRY_RUN = os.getenv("OBD_DRY_RUN", "0") == "1"


# =============================
# BUILD DEMO PAYLOAD
# =============================
def build_demo_payload() -> dict:
    ts = FIXED_TIMESTAMP or datetime.now(timezone.utc).isoformat()

    return {
        "timestamp": ts,
        "vehicle_code": VEHICLE_CODE,
        "engine_rpm": round(random.uniform(700, 3200), 2),
        "vehicle_speed_kph": round(random.uniform(0, 110), 2),
        "engine_temp_c": round(random.uniform(70, 105), 2),
        "oil_pressure_psi": round(random.uniform(18, 65), 2),
        "battery_voltage_v": round(random.uniform(12.0, 14.6), 2),
        "fuel_level_percent": round(random.uniform(5, 95), 2),
        "engine_failure_imminent": False,
    }


# =============================
# POST TO DJANGO INGEST
# =============================
# def post_payload(payload: dict):
#     headers = {"Content-Type": "application/json"}

#     if INGEST_KEY:
#         headers["X-INGEST-KEY"] = INGEST_KEY

#     # If you are sending historical/fixed timestamps, mark as demo so backend can relax skew checks in DEBUG.
#     if FIXED_TIMESTAMP:
#         headers["X-DEMO"] = "1"

#     if DRY_RUN:
#         return {"dry_run": True, "payload": payload}

#     resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
#     resp.raise_for_status()

#     # On error, raise with response body included (very helpful for 400 validation errors)
#     if resp.status_code >= 400:
#         raise requests.HTTPError(
#             f"{resp.status_code} {resp.reason} for url: {resp.url} | body: {resp.text}",
#             response=resp,
#         )

#     try:
#         return resp.json()
#     except Exception:
#         return {"status_code": resp.status_code, "text": resp.text}


# =============================
# MAIN LOOP
# =============================
# def main():
#     print(
#         f"[collector] Sending to {API_URL} every {INTERVAL_SECONDS}s (vehicle={VEHICLE_CODE})"
#     )

#     if not INGEST_KEY:
#         print(
#             "[collector] WARNING: OBD_INGEST_API_KEY not set (backend may return 401)."
#         )

#     if FIXED_TIMESTAMP:
#         print(f"[collector] Using fixed timestamp: {FIXED_TIMESTAMP}")

#     if DRY_RUN:
#         print("[collector] DRY_RUN=1 (no POST will be sent)")

#     if SEND_ONCE:
#         print("[collector] SEND_ONCE=1 (will send one reading and exit)")

#     if not VEHICLE_CODE:
#         print(
#             "[collector] ERROR: OBD_VEHICLE_CODE no definido. Debe ser la placa real del vehículo."
#         )
#         return

#     while True:
#         payload = build_demo_payload()
#         try:
#             result = post_payload(payload)
#             print(f"[collector] OK -> {result}")
#         except Exception as e:
#             print(f"[collector] ERROR -> {e}")

#         if SEND_ONCE:
#             break

#         time.sleep(INTERVAL_SECONDS)


# -----------------------------
# PENDIENTE: conexión real OBDLink MX+ (Wi-Fi)
# -----------------------------
# Idea general (cuando tengas vehículo):
# 1) Conectar tu laptop al Wi‑Fi del adaptador (o a la red donde esté el adaptador)
# 2) Detectar IP/puerto del adaptador (común: 192.168.x.x y puerto 35000 o 23)
# 3) Probar conectividad:
#      nc -vz $OBD_WIFI_HOST $OBD_WIFI_PORT
# 4) Implementar handshake ELM327 por TCP:
#      ATZ, ATE0, ATL0, ATS0, ATH0, ATSP0
# 5) Consultar PIDs y mapear a tu payload:
#      010C (RPM), 010D (Speed), 0105 (Coolant temp), 0111 (Throttle), etc.
# 6) Reusar `post_payload(payload)` para enviar a /api/obd/ingest/

# Variables (cuando se active):
#   export OBD_WIFI_HOST="192.168.0.10"
#   export OBD_WIFI_PORT="35000"

# Variables (cuando se active):
#   export OBD_WIFI_HOST="192.168.0.10"
#   export OBD_WIFI_PORT="35000"

# def main_obdlink_wifi_loop():
#     """Pendiente: loop real leyendo PIDs -> armando payload -> post_payload."""
#     while True:
#         payload = read_obdlink_wifi_payload()
#         post_payload(payload)
#         time.sleep(INTERVAL_SECONDS)

# if __name__ == "__main__":
#     main()


# =============================
# bluetooth OBDLink MX+ conexion
# =============================
def get_iso_timestamp():
    return datetime.now(timezone.utc).astimezone().isoformat()


def safe_obd_value(connection, command, unit=None):
    """
    Lee un comando OBD y devuelve un valor numerico simple o None.
    """
    try:
        response = connection.query(command)
        if response.is_null():
            return None

        value = response.value

        if unit is not None:
            value = value.to(
                unit
            ).magnitude  # convertir a la unidad deseada y obtener el valor numérico
        elif hasattr(value, "magnitude"):
            value = value.magnitude  # obtener valor numérico si tiene magnitud
        # else:
        #     # para valores sin unidad o ya numericos
        #     if hasattr(value, "magnitude"):
        #         value = value.magnitude  # obtener valor numérico si tiene magnitud

        return float(value)
    except Exception as e:
        print(f"[WARN] Error leyendo {command.name}: {e}")
        return None


def build_payload(connection):
    payload = {
        "timestamp": get_iso_timestamp(),
        "vehicle_code": VEHICLE_CODE,
        "engine_rpm": safe_obd_value(connection, obd.commands.RPM),
        "vehicle_speed_kph": safe_obd_value(connection, obd.commands.SPEED, "kph"),
        "engine_temp_c": safe_obd_value(
            connection, obd.commands.COOLANT_TEMP, "celsius"
        ),
        "oil_pressure_psi": safe_obd_value(
            connection, obd.commands.OIL_PRESSURE, "psi"
        ),
        "battery_voltage_v": safe_obd_value(
            connection, obd.commands.ELM_VOLTAGE, "volt"
        ),
        "fuel_level_percent": safe_obd_value(
            connection, obd.commands.FUEL_LEVEL, "percent"
        ),
        # "engine_failure_imminent": False,  # Pendiente: lógica para determinar esto
    }
    return payload


def post_payload(payload):
    headers = {
        "Content-Type": "application/json",
        "X-INGEST-KEY": INGEST_KEY,
    }
    # response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
    try:
        # print(f"[INFO] POST {response.status_code}: {response.text}")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        print(f"[INFO] POST {response.status_code}: {response.text}")
        # response.raise_for_status()
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Fallo enviando a Django: {e}")
        raise


def connect_obd():
    """
    intenta conectar al adaptador OBD.
    Si OBD_PORT es None, python-OBD intentará autodetectar el puerto.
    """
    print(f"[INFO] Conectando a OBD. Puerto={OBD_PORT}")

    try:
        ports = obd.scan_serial()
        print(f"[INFO] Puertos OBD detectados: {ports}")
    except Exception as e:
        print(f"[ERROR] No se pudieron escanear puertos: {e}")

    # connection = obd.OBD(portstr=OBD_PORT, fast=False, baudrate=115200, timeout=10)
    connection = obd.OBD(portstr=OBD_PORT, fast=False, timeout=10)

    if not connection.is_connected():
        raise RuntimeError(
            "No se pudo conectar al OBDLink MX+."
            "En macOS esto suele pasar cuando el dispositivo no se expone como puerto serial utilizable."
        )

    print("[OK] Conexion OBD establecida.")
    return connection


def main():

    if DRY_RUN:
        # print("[DRY] Payload no enviado", payload)
        print("[DRY] DRY_RUN=1 activado. No se enviarán datos.")
        return

    connection = connect_obd()

    while True:
        try:
            payload = build_payload(connection)
            print("[DATA]", payload)
            post_payload(payload)
        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
