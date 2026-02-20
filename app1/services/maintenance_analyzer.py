# 1 Crear el módulo de análisis
# 2 importar dependencias
from django.db.models import Max, Min
from django.utils import timezone
from datetime import timedelta

from app1.models import obddata
from app1.models import obddata, RecomendacionMantenimiento, Vehiculo
from app1.services.maintenance_rules import evaluar_mantenimiento
from app1.services.recommendation_repository import guardar_recomendacion

# variables advertencia
ESTADO_PENDIENTE = "Pendiente"
ESTADO_ATENDIDO = "Atendido"
SEVERIDAD_INFO = "info"
SEVERIDAD_WARNING = "warning"
SEVERIDAD_CRITICAL = "critical"


# nuevas funciones para reglas de mantenimiento
def _get_obd_queryset_for_vehicle(vehiculo: Vehiculo):
    """
    Devolver el queryset OBD para un vehiculo:
    1) busca por FK vehiculo
    2) si no hay datos, busca por vehicle_code == vehiculo.placa
    """
    qs_fk = obddata.objects.filter(vehiculo=vehiculo)
    if qs_fk.exists():
        return qs_fk

    if vehiculo.placa:
        qs_code = obddata.objects.filter(vehicle_code=vehiculo.placa)
        if qs_code.exists():
            return qs_code

    return obddata.objects.none()  # queryset vacío


def _crear_recomendacion_unica(
    vehiculo: Vehiculo, codigo: str, titulo: str, mensaje: str, severidad: str
):
    """
    Crea una recomendación solo si no existe una pendiente con el mismo código para ese vehículo.
    """
    existe = RecomendacionMantenimiento.objects.filter(
        vehiculo=vehiculo, codigo=codigo, estado="Pendiente"
    ).exists()

    if existe:
        return None  # ya existe una recomendación pendiente similar

    rec = RecomendacionMantenimiento.objects.create(
        vehiculo=vehiculo,
        codigo=codigo,
        titulo=titulo,
        mensaje=mensaje,
        severidad=severidad,
        estado="Pendiente",
    )
    return rec


# funciones anteriores(no devuelven recomendaciones, solo indicadores)
# 3 Función principal del servicio
def analizar_vehiculo(vehiculo, max_registros=500, ventana_horas=24):
    """Analiza el estado del vehículo y devuelve recomendaciones de mantenimiento."""

    # Filtrar registros OBD-II recientes
    registros = _obtener_registros_recientes(
        vehiculo,
        # max_registros,
        max_registros=max_registros,
        # ventana_horas
        ventana_horas=ventana_horas,
    )

    if not registros.exists():
        return []

    # return evaluar_mantenimiento(vehiculo)
    return evaluar_mantenimiento(vehiculo, registros)


# Integrar con el servicio de análisis, nueva funcion EXTENDIDA
def analizar_vehiculo_y_guardar(vehiculo: Vehiculo):

    # recomendaciones = analizar_vehiculo(vehiculo)
    # if not recomendaciones:
    #     return []
    # return guardar_recomendacion(vehiculo, recomendaciones)
    """
    Analiza el histórico OBD de un vehículo y guarda recomendaciones
    de mantenimiento si se cumplen ciertas condiciones.
    Devuelve una lista de las recomendaciones NUEVAS creadas.
    """
    qs = _get_obd_queryset_for_vehicle(vehiculo)
    if not qs.exists():
        return []

    nuevas = []

    # 1) temperatura del motor alta
    max_temp = qs.aggregate(max_temp=Max("engine_temp_c"))["max_temp"]
    if max_temp is not None and max_temp >= 100:  # revisar umbral >= 100C es ejemplo
        rec = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo="TEMP_ALTA",
            titulo="Temperatura del motor elevada",
            mensaje=(
                f"Se detectó una temperatura máxima de {max_temp:.1f} °C."
                "Revisar sistema de refrigeración(refrigerante, radiador, ventiladores)."
            ),
            severidad=SEVERIDAD_CRITICAL,
        )
        if rec:
            nuevas.append(rec)

    # 2) presion de aceite baja
    min_oil = qs.aggregate(min_oil=Min("oil_pressure_psi"))["min_oil"]
    if min_oil is not None and min_oil < 30:  # revisar umbrarl < 30 es ejemplo
        rec = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo="ACEITE_BAJO",
            titulo="Presión de aceite baja",
            mensaje=(
                f"La presión mínima de aceite registrada fue {min_oil:.1f} psi."
                "Verificar nivel y calidad del aceite, asi como posibles fugas."
            ),
            severidad=SEVERIDAD_CRITICAL,
        )
        if rec:
            nuevas.append(rec)

    # 3) Batería con voltaje bajo
    min_volt = qs.aggregate(min_volt=Min("battery_voltage_v"))["min_volt"]
    if min_volt is not None and min_volt < 12.0:
        rec = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo="BATERIA_BAJA",
            titulo="Voltaje de batería bajo",
            mensaje=(
                f"Se registró un voltaje mínimo de {min_volt:.1f} V."
                "Revisar estado de la batería y sistema de carga."
            ),
            severidad=SEVERIDAD_WARNING,
        )
        if rec:
            nuevas.append(rec)
    # 4) Flag de fallo inminente reportado por el dispositivo
    if qs.filter(engine_failure_imminent=True).exists():
        rec = _crear_recomendacion_unica(
            vehiculo=vehiculo,
            codigo="FALLO_INMINENTE",
            titulo="Alerta de fallo inminente",
            mensaje=(
                "El módulo OBD reportó un posible fallo inminente del motor. "
                "Se recomienda realizar un diagnóstico completo del sistema."
            ),
            severidad=SEVERIDAD_CRITICAL,
        )
        if rec:
            nuevas.append(rec)

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
