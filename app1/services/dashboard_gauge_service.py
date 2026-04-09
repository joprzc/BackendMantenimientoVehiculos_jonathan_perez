from app1.models import obddata


def _status_from_ranges(
    value, warning_min=None, warning_max=None, critical_min=None, critical_max=None
):
    if value is None:
        return "unknown"

    if critical_min is not None and value <= critical_min:
        return "critical"
    if critical_max is not None and value >= critical_max:
        return "critical"
    if warning_min is not None and value <= warning_min:
        return "warning"
    if warning_max is not None and value >= warning_max:
        return "warning"

    return "ok"


def get_vehicle_gauge_data(vehiculo):
    latest = (
        obddata.objects.filter(vehiculo_id=vehiculo.id).order_by("-timestamp").first()
    )

    if not latest:
        return {
            "ok": False,
            "message": "No hay lecturas OBD para este vehículo",
            "gauges": {},
        }

    rpm = latest.engine_rpm
    temp = latest.engine_temp_c
    battery = latest.battery_voltage_v
    fuel = latest.fuel_level_percent
    oil = latest.oil_pressure_psi

    gauges = {
        "rpm": {
            "title": "RPM",
            "value": round(rpm or 0, 2),
            "min": 0,
            "max": 8000,
            "unit": "RPM",
            "status": _status_from_ranges(rpm, warning_max=4500, critical_max=6000),
        },
        "temperature": {
            "title": "Temperatura",
            "value": round(temp or 0, 2),
            "min": 0,
            "max": 140,
            "unit": "°C",
            "status": _status_from_ranges(temp, warning_max=95, critical_max=105),
        },
        "battery": {
            "title": "Batería",
            "value": round(battery or 0, 2),
            "min": 0,
            "max": 16,
            "unit": "V",
            "status": _status_from_ranges(battery, warning_min=12.2, critical_min=11.8),
        },
        "fuel": {
            "title": "Combustible",
            "value": round(fuel or 0, 2),
            "min": 0,
            "max": 100,
            "unit": "%",
            "status": _status_from_ranges(fuel, warning_min=25, critical_min=10),
        },
        "oil_pressure": {
            "title": "Presión aceite",
            "value": round(oil or 0, 2),
            "min": 0,
            "max": 120,
            "unit": "psi",
            "status": _status_from_ranges(oil, warning_min=20, critical_min=10),
        },
    }

    return {
        "ok": True,
        "timestamp": latest.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "gauges": gauges,
    }
