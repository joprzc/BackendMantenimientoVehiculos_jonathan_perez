# 1 Crear el módulo de análisis
# 2 importar dependencias
from datetime import timedelta
from django.utils import timezone

from app1.models import obddata
from app1.services.maintenance_rules import evaluar_mantenimiento
from app1.services.recommendation_repository import guardar_recomendacion


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
def analizar_vehiculo_y_guardar(vehiculo):

    recomendaciones = analizar_vehiculo(vehiculo)

    if not recomendaciones:
        return []

    return guardar_recomendacion(vehiculo, recomendaciones)


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
def _obtener_registros_recientes(vehiculo, max_registros, ventana_horas):
    """Obtiene los registros OBD-II recientes del vehículo."""
    desde = timezone.now() - timedelta(hours=ventana_horas)

    return obddata.objects.filter(
        vehiculo=vehiculo,
        timestamp__gte=desde,  # __gte significa "Greater Than or Equal" (>=)
    ).order_by("-timestamp")[:max_registros]


# 5 Estructura de salida (opcional pero recomendable)
# esto sirve para api, dashboards, historico, etc.
def analizar_vehiculo_detallado(vehiculo):
    """Analiza el vehículo y devuelve un informe detallado."""

    recomendaciones = analizar_vehiculo(vehiculo)

    return {
        "vehiculo_id": vehiculo.id,
        "total_recomendaciones": len(recomendaciones),
        "recomendaciones": recomendaciones,
    }


# 6 Instrucciones para probar el servicio
# from app1.models import Vehiculo
# from app1.services.maintenance_analyzer import analizar_vehiculo

# vehiculo = Vehiculo.objects.first()
# analizar_vehiculo(vehiculo)
