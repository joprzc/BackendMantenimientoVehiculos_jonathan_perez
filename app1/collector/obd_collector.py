import os
import time
import random
import requests
from datetime import datetime, timezone

# =============================
# CONFIG (ENV)
# =============================
API_URL = os.getenv("OBD_API_URL", "http://127.0.0.1:8000/api/obd/ingest/")
INGEST_KEY = os.getenv("OBD_INGEST_API_KEY", "")
VEHICLE_CODE = os.getenv("OBD_VEHICLE_CODE", "DEMO-000")
INTERVAL_SECONDS = float(os.getenv("OBD_INTERVAL_SECONDS", "2.0"))

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
def post_payload(payload: dict):
    headers = {"Content-Type": "application/json"}

    if INGEST_KEY:
        headers["X-INGEST-KEY"] = INGEST_KEY

    # If you are sending historical/fixed timestamps, mark as demo so backend can relax skew checks in DEBUG.
    if FIXED_TIMESTAMP:
        headers["X-DEMO"] = "1"

    if DRY_RUN:
        return {"dry_run": True, "payload": payload}

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)

    # On error, raise with response body included (very helpful for 400 validation errors)
    if resp.status_code >= 400:
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} for url: {resp.url} | body: {resp.text}",
            response=resp,
        )

    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code}


# =============================
# MAIN LOOP
# =============================
def main():
    print(
        f"[collector] Sending to {API_URL} every {INTERVAL_SECONDS}s (vehicle={VEHICLE_CODE})"
    )

    if not INGEST_KEY:
        print(
            "[collector] WARNING: OBD_INGEST_API_KEY not set (backend may return 401)."
        )

    if FIXED_TIMESTAMP:
        print(f"[collector] Using fixed timestamp: {FIXED_TIMESTAMP}")

    if DRY_RUN:
        print("[collector] DRY_RUN=1 (no POST will be sent)")

    if SEND_ONCE:
        print("[collector] SEND_ONCE=1 (will send one reading and exit)")

    while True:
        payload = build_demo_payload()
        try:
            result = post_payload(payload)
            print(f"[collector] OK -> {result}")
        except Exception as e:
            print(f"[collector] ERROR -> {e}")

        if SEND_ONCE:
            break

        time.sleep(INTERVAL_SECONDS)


# -----------------------------
# PENDIENTE: conexión real OBDLink (Wi-Fi)
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

if __name__ == "__main__":
    main()
