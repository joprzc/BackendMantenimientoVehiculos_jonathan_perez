import os
import time
import random
import requests
from datetime import datetime, timezone
import hmac
import hashlib
from django.conf import settings

# mandar datos simulados

API_URL = os.getenv("OBD_API_URL", "http://127.0.0.1:8000/api/obd/ingest/")
INGEST_KEY = os.getenv("OBD_INGEST_API_KEY", "")
VEHICLE_CODE = os.getenv("OBD_VEHICLE_CODE", "DEMO-000")
INTERVAL_SECONDS = float(os.getenv("OBD_INTERVAL_SECONDS", "2.0"))
# provided = request.headers.get("X-INGEST-KEY", "")


# --- POST helper for ingest endpoint ---
def post_payload(payload: dict):
    """POST a payload to the ingest endpoint.

    - Uses OBD_INGEST_API_KEY if present.
    - Sends header X-INGEST-KEY (backend expectation) plus extra common conventions.
    """
    headers = {
        "Content-Type": "application/json",
    }

    if INGEST_KEY:
        # Match backend expectation (Postman): X-INGEST-KEY
        headers["X-INGEST-KEY"] = INGEST_KEY
        # Keep extra common conventions for compatibility
        headers["X-API-KEY"] = INGEST_KEY
        headers["Authorization"] = f"Bearer {INGEST_KEY}"

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    # Raise on 4xx/5xx so the loop can log and retry
    # resp.raise_for_status()
    response = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()

    # Try to return JSON; fall back to raw text
    try:
        return resp.json()
    except Exception:
        # return {"status_code": resp.status_code, "text": resp.text}
        return {"status_code": response.status_code}


def build_demo_payload() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vehicle_code": VEHICLE_CODE,
        "engine_rpm": round(random.uniform(700, 3200), 2),
        "vehicle_speed_kph": round(random.uniform(0, 110), 2),
        "engine_temp_c": round(random.uniform(70, 105), 2),
        "oil_pressure_psi": round(random.uniform(18, 65), 2),
        "battery_voltage_v": round(random.uniform(12.0, 14.6), 2),
        "fuel_level_percent": round(random.uniform(5, 95), 2),
        "engine_failure_imminent": False,
    }


def main_demo_loop():
    if not INGEST_KEY:
        print(
            "[collector] WARNING: Falta OBD_INGEST_API_KEY en el entorno. Se enviará SIN key (puede fallar con 401/403)."
        )

    print(
        f"[collector] POST -> {API_URL} vehicle={VEHICLE_CODE} every {INTERVAL_SECONDS}s",
        # Expected key from environment/settings (do NOT hardcode in code)
        expected=(
            os.getenv("OBD_INGEST_API_KEY")
            or getattr(settings, "OBD_INGEST_API_KEY", "")
            or os.getenv("OBD_INGEST_KEY")
            or ""
        ),
    )
    while True:
        payload = build_demo_payload()
        try:
            resp = post_payload(payload)
            print(f"[collector] ok {resp}")
        except Exception as e:
            # reintento sin crashear
            print(f"[collector] error: {e} (reintentando...)")
        time.sleep(INTERVAL_SECONDS)

    # If no key is configured, allow only in DEBUG to avoid blocking local dev.
    if not expected:
        if not getattr(settings, "DEBUG", False):
            return JsonResponse(
                {"ok": False, "error": "Ingest key not configured"}, status=500
            )
    else:
        # Constant-time compare to avoid timing leaks
        if not hmac.compare_digest(str(provided), str(expected)):
            # Safe debug aid (hash only, never print secrets)
            if getattr(settings, "DEBUG", False):
                exp_hash = hashlib.sha256(expected.encode("utf-8")).hexdigest()[:8]
                prov_hash = (
                    hashlib.sha256(provided.encode("utf-8")).hexdigest()[:8]
                    if provided
                    else "(missing)"
                )
                print(
                    f"[ingest] unauthorized: provided={prov_hash} expected={exp_hash}"
                )
            return JsonResponse({"ok": False, "error": "Unauthorized"}, status=401)


def post_payload(payload: dict):
    headers = {"Content-Type": "application/json"}
    if INGEST_KEY:
        headers["X-INGEST-KEY"] = INGEST_KEY

        resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code}


def main():
    print(
        f"[collector] Sending to {API_URL} every {INTERVAL_SECONDS}s (vehicle={VEHICLE_CODE})"
    )
    if not INGEST_KEY:
        print("[collector] WARNING: OBD_INGEST_API_KEY not set.")

    while True:
        payload = build_demo_payload()
        try:
            result = post_payload(payload)
            print(f"[collector] OK -> {result}")
        except Exception as e:
            print(f"[collector] ERROR -> {e}")
        time.sleep(INTERVAL_SECONDS)


# -----------------------------
# PENDIENTE: conexión real OBDLink (Wi-Fi)
# -----------------------------
# Nota técnica:
# Muchos adaptadores ELM327 Wi-Fi exponen TCP (ej: puerto 35000) y se consultan PIDs.
# Una opción es usar un fork/adaptación tipo python-OBD-wifi.
#
# Ejemplo de referencia (NO activar hasta tener vehículo):
#
#   import obd
#   connection = obd.OBD("192.168.0.10", 35000)  # IP/puerto del adaptador
#   rpm = connection.query(obd.commands.RPM).value
#   speed = connection.query(obd.commands.SPEED).value
#
# Cuando tengas el adaptador en Wi-Fi:
# - detectamos IP (gateway o rango 192.168.x.x)
# - probamos conectividad: nc -vz <ip> 35000
# - implementamos loop: leer PIDs -> mapear -> post al endpoint
#
# Por ahora dejamos solo DEMO.

if __name__ == "__main__":
    # main_demo_loop()
    main()
