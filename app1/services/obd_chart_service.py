from app1.models import obddata


def _apply_date_filters(qs, fecha_inicio=None, fecha_fin=None):
    """Aplica filtros por fecha sobre timestamp (por día) de forma segura."""
    if fecha_inicio:
        qs = qs.filter(timestamp__date__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(timestamp__date__lte=fecha_fin)
    return qs


def get_obd_chart_data(vehiculo, fecha_inicio=None, fecha_fin=None):
    """Devuelve múltiples series crudas (no agregadas) para gráficos."""
    qs = obddata.objects.filter(vehiculo_id=vehiculo.id)
    qs = _apply_date_filters(qs, fecha_inicio, fecha_fin).order_by("timestamp")

    return {
        "labels": [o.timestamp.strftime("%Y-%m-%d %H:%M:%S") for o in qs],
        "rpm": [o.engine_rpm for o in qs],
        "temp": [o.engine_temp_c for o in qs],
        "fuel": [o.fuel_level_percent for o in qs],
        "volt": [o.battery_voltage_v for o in qs],
        # NUEVO: presión de aceite (asegúrate de que el modelo tenga este campo)
        "oilpressure": [getattr(o, "oil_pressure_psi", None) for o in qs],
        "alerts": [1 if o.engine_failure_imminent else 0 for o in qs],
    }


def get_obd_series_labels_values(
    vehiculo, field_name, fecha_inicio=None, fecha_fin=None
):
    """Devuelve el formato esperado por fetchSeries(): {labels:[], values:[]}.

    field_name: nombre del campo en el modelo obddata (ej: 'engine_rpm', 'oil_pressure_psi')
    """
    qs = obddata.objects.filter(vehiculo_id=vehiculo.id)
    qs = _apply_date_filters(qs, fecha_inicio, fecha_fin).order_by("timestamp")

    labels = []
    values = []

    for o in qs:
        labels.append(o.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        values.append(getattr(o, field_name, None))

    return {"labels": labels, "values": values}
