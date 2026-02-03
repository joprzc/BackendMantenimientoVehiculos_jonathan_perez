from app1.models import obddata


def get_obd_chart_data(vehiculo, fecha_inicio=None, fecha_fin=None):
    qs = obddata.objects.filter(vehiculo_id=vehiculo.id)

    if fecha_inicio:
        qs = qs.filter(timestamp__date__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(timestamp__date__lte=fecha_fin)

    qs = qs.order_by("timestamp")

    return {
        "labels": [o.timestamp.strftime("%Y-%m-%d %H:%M:%S") for o in qs],
        "rpm": [o.engine_rpm for o in qs],
        "temp": [o.engine_temp_c for o in qs],
        "fuel": [o.fuel_level_percent for o in qs],
        "volt": [o.battery_voltage_v for o in qs],
        "alerts": [1 if o.engine_failure_imminent else 0 for o in qs],
    }
