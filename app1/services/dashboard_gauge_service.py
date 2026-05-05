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

    # estado dinámico para kilometraje
    # odometer = latest.odometer_reading

    # if odometer is None:
    #     odometer_status = "unknown"
    #     odometer_value = 0
    # else:
    #     odometer_status = "ok"
    #     odometer_value = odometer
    odometer = latest.odometer_reading

    if odometer is None:
        odometer_value = 0
        odometer_status = "unknown"
    else:
        odometer_value = odometer / 1000

        if odometer >= 200000:
            odometer_status = "critical"
        elif odometer >= 100000:
            odometer_status = "warning"
        else:
            odometer_status = "ok"

    # RMP
    rpm = latest.engine_rpm

    # Temperatura del motor
    engine_temp_c = latest.engine_temp_c

    engine_temp_status = "ok"

    if engine_temp_c is None:
        engine_temp_status = "unknown"

    elif engine_temp_c >= 115:
        engine_temp_status = "critical"

    elif engine_temp_c >= 105:
        engine_temp_status = "warning"

    else:
        engine_temp_status = "ok"

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
    oil_pressure_psi = latest.oil_pressure_psi

    if oil_pressure_psi is None:
        oil_status = "unknown"
        oil_value = 0

    elif oil_pressure_psi < 10:
        oil_status = "critical"
        oil_value = oil_pressure_psi

    elif oil_pressure_psi < 20:
        oil_status = "warning"
        oil_value = oil_pressure_psi

    else:
        oil_status = "ok"
        oil_value = oil_pressure_psi

    # normalizamos rpm a miles para mejor visualización
    rpm_value = (rpm or 0) / 1000

    # construimos el dict de gauges con valores y estados
    gauges = {
        "rpm": {
            "title": "RPM",
            "value": round(rpm_value, 2),
            "min": 0,
            "max": 8,
            "unit": "x1000 RPM",
            "status": _status_from_ranges(rpm, warning_max=3000, critical_max=4500),
        },
        "temperature": {
            "title": "Temperatura",
            "value": round(engine_temp_c or 0, 2),
            "unit": "°C",
            "status": engine_temp_status,
            "min": 0,
            "max": 120,
        },
        "battery": {
            "title": "Batería",
            "value": round(battery_value, 2),
            "min": 10,
            "max": 16,
            "unit": "V",
            "status": battery_status,
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
            "title": "Presión Aceite",
            "value": round(oil_value, 2),
            "min": 0,
            "max": 80,
            "unit": "PSI",
            "status": oil_status,
        },
        "odometer": {
            "title": "Kilometraje",
            "value": round(odometer_value, 1),
            "min": 0,
            "max": 260,
            "unit": "mil km",
            "status": odometer_status,
        },
    }

    return {
        "ok": True,
        "timestamp": latest.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "gauges": gauges,
    }
