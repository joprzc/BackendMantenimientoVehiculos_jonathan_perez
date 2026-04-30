from app1.models import obddata, Vehiculo


def _get_queryset_for_vehicle(vehiculo: Vehiculo):
    """
    Devuelve un queryset priorizando FK; si no hay, usa vehicle_code (placa).
    """
    qs = obddata.objects.filter(vehiculo=vehiculo)
    if qs.exists():
        return qs
    if vehiculo.placa:
        return obddata.objects.filter(vehicle_code__iexact=vehiculo.placa)
    return obddata.objects.none()


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
    qs = _get_queryset_for_vehicle(vehiculo)
    latest = qs.order_by("-timestamp", "-id").first()

    if not latest:
        return {
            "ok": False,
            "message": "No hay lecturas OBD para este vehículo",
            "gauges": {},
        }

    rpm = latest.engine_rpm
    temp = latest.engine_temp_c

    # estado dinámico para batería
    battery_voltage = latest.battery_voltage_v

    if battery_voltage is None:
        battery_status = "unknown"
        battery_value = 0

    elif battery_voltage < 12.5 or battery_voltage > 15.0:
        battery_status = "critical"
        battery_value = battery_voltage

    elif battery_voltage < 13.5:
        battery_status = "warning"
        battery_value = battery_voltage

    else:
        battery_status = "ok"
        battery_value = battery_voltage

    # estado dinamico para combustible
    fuel = latest.fuel_level_percent

    fuel_status = "ok"
    if fuel is None:
        fuel_status = "unknown"
    elif fuel <= 10:
        fuel_status = "critical"
    elif fuel <= 20:
        fuel_status = "warning"
    else:
        fuel_status = "ok"

    # estado dinamico para aceite
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
            "value": round(battery_value, 2),
            "min": 10,
            "max": 16,
            "unit": "V",
            "status": battery_status,
            # "title": "Batería",
            # "value": round(battery or 0, 2),
            # "min": 0,
            # "max": 16,
            # "unit": "V",
            # "status": _status_from_ranges(battery, warning_min=12.2, critical_min=11.8),
        },
        "fuel": {
            "title": "Combustible",
            "value": round(fuel or 0, 2),
            "min": 0,  #
            "max": 100,  #
            "unit": "%",  #
            "status": fuel_status,
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
