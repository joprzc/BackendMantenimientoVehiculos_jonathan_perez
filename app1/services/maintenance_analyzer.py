from datetime import timedelta

from django.db.models import Max, Min
from django.utils import timezone

from app1.models import obddata, RecomendacionMantenimiento, Vehiculo

# constantes alineadas con choices del modelo
ESTADO_PENDIENTE = "pendiente"
ESTADO_ATENDIDO = "atendido"
SEVERIDAD_INFO = "info"
SEVERIDAD_WARNING = "warning"
SEVERIDAD_CRITICAL = "critical"


def _get_obd_queryset_for_vehicle(vehiculo: Vehiculo):
    """
    Prioriza datos ligados por FK; si no hay, usa vehicle_code = placa.
    """
    qs = obddata.objects.filter(vehiculo=vehiculo)
    if qs.exists():
        return qs
    if vehiculo.placa:
        return obddata.objects.filter(vehicle_code__iexact=vehiculo.placa)
    return obddata.objects.none()


def _obtener_registros_recientes(vehiculo, max_registros=500, ventana_horas=24):
    """
    Limita por ventana temporal y cantidad máxima.
    """
    desde = timezone.now() - timedelta(hours=ventana_horas)
    return (
        _get_obd_queryset_for_vehicle(vehiculo)
        .filter(timestamp__gte=desde)
        .order_by("-timestamp")[:max_registros]
    )


def _crear_recomendacion_unica(vehiculo, codigo, titulo, mensaje, severidad):
    """
    Evita duplicados pendientes por código.
    """
    existe = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo, codigo=codigo, estado=ESTADO_PENDIENTE
    ).exists()
    if existe:
        return None

    return RecomendacionMantenimiento.objects.create(
        vehiculo=vehiculo,
        codigo=codigo,
        titulo=titulo,
        mensaje=mensaje,
        severidad=severidad,
        estado=ESTADO_PENDIENTE,
    )


def _evaluar_registros(registros):
    """
    Devuelve una lista de dicts con recomendaciones basadas en las métricas.
    """
    recomendaciones = []

    max_temp = registros.aggregate(Max("engine_temp_c"))["engine_temp_c__max"]
    if max_temp is not None and max_temp >= 100:
        recomendaciones.append(
            {
                "codigo": "TEMP_ALTA",
                "titulo": "Temperatura del motor elevada",
                "mensaje": (
                    f"Se detectó temperatura máxima de {max_temp:.1f} °C. "
                    "Revisar refrigerante, radiador y ventiladores."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    min_oil = registros.aggregate(Min("oil_pressure_psi"))["oil_pressure_psi__min"]
    if min_oil is not None and min_oil < 30:
        recomendaciones.append(
            {
                "codigo": "ACEITE_BAJO",
                "titulo": "Presión de aceite baja",
                "mensaje": (
                    f"Presión mínima registrada: {min_oil:.1f} psi. "
                    "Verificar nivel/calidad de aceite y posibles fugas."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    min_volt = registros.aggregate(Min("battery_voltage_v"))["battery_voltage_v__min"]
    if min_volt is not None and min_volt < 12.0:
        recomendaciones.append(
            {
                "codigo": "BATERIA_BAJA",
                "titulo": "Voltaje de batería bajo",
                "mensaje": (
                    f"Voltaje mínimo registrado: {min_volt:.1f} V. "
                    "Revisar batería y sistema de carga."
                ),
                "severidad": SEVERIDAD_WARNING,
            }
        )

    # if registros.filter(engine_failure_imminent=True).exists():
    if any(r.engine_failure_imminent for r in registros):
        recomendaciones.append(
            {
                "codigo": "FALLO_INMINENTE",
                "titulo": "Alerta de fallo inminente",
                "mensaje": (
                    "El módulo OBD reportó un posible fallo inminente. "
                    "Realizar diagnóstico completo del motor."
                ),
                "severidad": SEVERIDAD_CRITICAL,
            }
        )

    return recomendaciones


def analizar_vehiculo(vehiculo, max_registros=500, ventana_horas=24):
    """
    Devuelve recomendaciones (no guarda). Útil para mostrar en dashboard.
    """
    registros = _obtener_registros_recientes(
        vehiculo, max_registros=max_registros, ventana_horas=ventana_horas
    )
    if not registros.exists():
        return []
    return _evaluar_registros(registros)


def analizar_vehiculo_y_guardar(vehiculo, max_registros=500, ventana_horas=24):
    """
    Genera y guarda recomendaciones nuevas. Devuelve solo las recién creadas.
    """
    registros = _obtener_registros_recientes(
        vehiculo, max_registros=max_registros, ventana_horas=ventana_horas
    )
    if not registros.exists():
        return []

    nuevas = []
    for rec in _evaluar_registros(registros):
        creada = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo=rec["codigo"],
            titulo=rec["titulo"],
            mensaje=rec["mensaje"],
            severidad=rec["severidad"],
        )
        if creada:
            nuevas.append(creada)
    return nuevas


# probar en shell:
# from app1.models import Vehiculo
# from app1.services.maintenance_analyzer import analizar_vehiculo_y_guardar
# vehiculo = Vehiculo.objects.first()
# analizar_vehiculo_y_guardar(vehiculo)

# verificar persistencia
# vehiculo.recomendaciones.all()


# 4 Obtener registros recientes (función privada)
# funcion privada con "_"
# una sola responsabilidad
# def _obtener_registros_recientes(vehiculo, max_registros, ventana_horas):
#     """Obtiene los registros OBD-II recientes del vehículo."""
#     desde = timezone.now() - timedelta(hours=ventana_horas)

#     return obddata.objects.filter(
#         vehiculo=vehiculo,
#         timestamp__gte=desde,  # __gte significa "Greater Than or Equal" (>=)
#     ).order_by("-timestamp")[:max_registros]


# 5 Estructura de salida (opcional pero recomendable)
# esto sirve para api, dashboards, historico, etc.
# def analizar_vehiculo_detallado(vehiculo):
#     """Analiza el vehículo y devuelve un informe detallado."""

#     recomendaciones = analizar_vehiculo(vehiculo)

#     return {
#         "vehiculo_id": vehiculo.id,
#         "total_recomendaciones": len(recomendaciones),
#         "recomendaciones": recomendaciones,
#     }


# 6 Instrucciones para probar el servicio

# vehiculo = Vehiculo.objects.first()
# analizar_vehiculo(vehiculo)
